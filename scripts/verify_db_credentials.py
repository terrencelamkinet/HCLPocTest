#!/usr/bin/env python3
"""Verify every DB credential in backend/.env against all three layers.

Layers that must agree (the 2026-09-15 outage happened because they did not):
  1. backend/.env NEXUS_*_DATABASE_URL      — what the app sends
  2. Postgres role (pg_authid.rolpassword)  — what the direct 5432 path checks
  3. pgbouncer /etc/pgbouncer/userlist.txt  — what the 6432 pool uses for server login

SCRAM verifiers are salted, so equal passwords do NOT imply equal verifier strings;
a rotation must copy pg_authid.rolpassword verbatim into userlist.txt
(use scripts/sync_pgbouncer_userlist.py).

Run: cd backend && ./venv/bin/python ../scripts/verify_db_credentials.py
Read-only. Prints PASS/FAIL and never prints secrets.
"""
import asyncio
import base64
import hashlib
import hmac
import re
import subprocess
import sys
import urllib.parse
from pathlib import Path

ENV = Path(__file__).resolve().parent.parent / "backend" / ".env"
USERLIST = Path("/etc/pgbouncer/userlist.txt")
KEYS = ["NEXUS_DATABASE_URL", "NEXUS_APP_DATABASE_URL",
        "NEXUS_ADMIN_DATABASE_URL", "NEXUS_BRIEFING_DATABASE_URL"]


def env_dsns():
    out = {}
    for line in ENV.read_text().splitlines():
        s = line.strip()
        if s and not s.startswith("#") and "=" in s:
            k, _, v = s.partition("=")
            if k in KEYS:
                out[k] = v
    return out


def verifiers(roles):
    q = "select rolname, rolpassword from pg_authid where rolname in (%s)" % ",".join(
        f"'{r}'" for r in roles)
    r = subprocess.run(["sudo", "-u", "postgres", "psql", "-d", "nexus_crm", "-tAF", "|", "-c", q],
                       capture_output=True, text=True)
    return {ln.split("|")[0]: ln.split("|", 1)[1] for ln in r.stdout.splitlines() if "|" in ln}


def userlist():
    r = subprocess.run(["sudo", "cat", str(USERLIST)], capture_output=True, text=True)
    out = {}
    for line in r.stdout.splitlines():
        m = re.match(r'^"([^"]+)"\s+"(.*)"\s*$', line.strip())
        if m:
            out[m.group(1)] = m.group(2)
    return out


def scram_match(vf, pw):
    if not vf or not vf.startswith("SCRAM-SHA-256$"):
        return False
    try:
        _, params, stored = vf.split("$", 2)
        iters, _, salt_b64 = params.partition(":")
        stored_key = stored.split(":")[0]
        salted = hashlib.pbkdf2_hmac("sha256", pw.encode(), base64.b64decode(salt_b64), int(iters))
        ck = hmac.new(salted, b"Client Key", hashlib.sha256).digest()
        return hmac.compare_digest(
            base64.b64encode(hashlib.sha256(ck).digest()).decode(), stored_key)
    except Exception:  # noqa: BLE001
        return False


async def live_connect(dsn):
    import asyncpg
    u = urllib.parse.urlparse(dsn)
    try:
        c = await asyncpg.connect(host=u.hostname, port=u.port, user=u.username,
                                  password=urllib.parse.unquote(u.password or ""),
                                  database=(u.path or "/").lstrip("/"), timeout=8)
        await c.fetchrow("select 1")
        await c.close()
        return True, "ok"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {str(e)[:80]}"


async def main():
    dsns = env_dsns()
    users = {}
    for k, v in dsns.items():
        u = urllib.parse.urlparse(v)
        users[k] = (u.username, urllib.parse.unquote(u.password or ""), u.port)
    vf = verifiers([u for u, _, _ in users.values()])
    ul = userlist()

    print(f"{'env key':28} {'port':5} {'role':16} {'db-verifier':12} {'pgbouncer':10} {'connect':8}")
    fails = 0
    for key, (user, pw, port) in users.items():
        db_ok = scram_match(vf.get(user, ""), pw)
        if port == 6432:
            ul_ok = scram_match(ul.get(user, ""), pw) and ul.get(user) == vf.get(user)
            ul_txt = "ok" if ul_ok else "MISMATCH"
        else:
            ul_txt = "n/a"
        conn_ok, detail = await live_connect(dsns[key])
        if not (db_ok and conn_ok and ul_txt in ("ok", "n/a")):
            fails += 1
        print(f"{key:28} {port:<5} {user:16} {'ok' if db_ok else 'MISMATCH':12} "
              f"{ul_txt:10} {'ok' if conn_ok else 'FAIL':8}{'' if conn_ok else ' ' + detail}")

    print()
    print("RESULT: " + ("ALL LAYERS AGREE ✅" if fails == 0 else f"{fails} credential(s) BROKEN ❌"))
    if fails:
        print("Fix: scripts/sync_pgbouncer_userlist.py <role> --apply  (after any ALTER ROLE)")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
