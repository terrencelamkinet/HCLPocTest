#!/usr/bin/env python3
"""Sync a Postgres role's SCRAM verifier into pgbouncer's userlist.txt.

Why: pgbouncer (auth_file) authenticates to the backend using the verifier stored in
userlist.txt. When that verifier is NOT the exact one Postgres holds, server login fails
with "password authentication failed" even though the password itself is correct — SCRAM
verifiers are salted, so equal passwords do not imply equal verifier strings.

This copies pg_authid.rolpassword verbatim for the given roles and reloads pgbouncer.

Run: sudo-less, uses `sudo -u postgres psql` / `sudo tee`.
  ./backend/venv/bin/python scripts/sync_pgbouncer_userlist.py gg_fighter [--apply]
"""
import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

USERLIST = Path("/etc/pgbouncer/userlist.txt")
STAMP = dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def db_verifier(role):
    r = subprocess.run(
        ["sudo", "-u", "postgres", "psql", "-d", "nexus_crm", "-tAc",
         f"select rolpassword from pg_authid where rolname='{role}'"],
        capture_output=True, text=True)
    return (r.stdout or "").strip()


def read_userlist():
    r = subprocess.run(["sudo", "cat", str(USERLIST)], capture_output=True, text=True)
    return r.stdout


def parse(text):
    out = []
    for line in text.splitlines():
        if not line.strip():
            continue
        m = re.match(r'^"([^"]+)"\s+"(.*)"\s*$', line.strip())
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("roles", nargs="+")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()

    entries = parse(read_userlist())
    cur = dict(entries)
    new = dict(cur)
    for role in a.roles:
        vf = db_verifier(role)
        if not vf.startswith("SCRAM-SHA-256$"):
            print(f"{role}: no SCRAM verifier in pg_authid — skip")
            continue
        status = "already identical" if cur.get(role) == vf else "DIFFERENT -> will sync"
        print(f"{role}: userlist present={role in cur} {status}")
        new[role] = vf

    if not a.apply:
        print("\nDRY RUN — re-run with --apply to write + reload pgbouncer")
        return 0

    bak = f"/tmp/userlist.txt.bak-{STAMP}"
    subprocess.run(["sudo", "cp", str(USERLIST), bak], check=True)
    body = "".join(f'"{u}" "{p}"\n' for u, p in new.items())
    r = subprocess.run(["sudo", "tee", str(USERLIST)], input=body,
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("write failed:", r.stderr.strip())
        return 1
    subprocess.run(["sudo", "chown", "postgres:postgres", str(USERLIST)], check=True)
    subprocess.run(["sudo", "chmod", "640", str(USERLIST)], check=True)
    print(f"userlist.txt updated (backup {bak})")
    subprocess.run(["sudo", "systemctl", "reload", "pgbouncer"], check=False)
    print("pgbouncer reloaded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
