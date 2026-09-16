#!/usr/bin/env python3
"""[one-off, KB-045] End-to-end proof: resolving a name card no longer writes a touchpoint.

Self-cleaning demo（真 API，唔係 mock）：
  1. 登入 → 記低現有 touchpoint 總數
  2. POST /name-cards        建一張 synthetic pending 卡（parsed_data 假名）
  3. POST /name-cards/{id}/resolve  action=separate → 應開新 contact
  4. GET /touchpoints        斷言：冇新增、冇 type=namecard 嘅 row
  5. 清走自己造嘅嘢（卡片、contact、activity/notification 殘留由 SQL 按 id scoped 清）

憑證：/tmp/.nc_creds.json
用法: ./backend/venv/bin/python scripts/verify_namecard_resolve_no_touchpoint.py
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:8001"
CREDS = Path("/tmp/.nc_creds.json")
PROBE_NAME = "ZZ QA Probe (do not keep)"
PROBE_TAIL = "zz-qa-probe-no-touchpoint@example.invalid"


def call(method: str, path: str, token: str | None = None, body: dict | None = None):
    req = urllib.request.Request(API + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        return e.code, None


def login() -> str:
    d = json.loads(CREDS.read_text(encoding="utf-8"))
    status, payload = call("POST", "/api/v1/auth/login", body={"email": d["email"], "password": d["password"]})
    assert status == 200 and payload and payload.get("access_token"), f"login failed: {status}"
    return payload["access_token"]


def all_touchpoints(token: str) -> list[dict]:
    out, offset = [], 0
    while True:
        status, payload = call("GET", f"/api/v1/crm/touchpoints?limit=100&offset={offset}", token)
        assert status == 200, f"list failed: {status}"
        items = payload.get("items") or payload.get("data") or []
        out += items
        if len(items) < 100:
            return out
        offset += 100


def main() -> int:
    token = login()
    before = all_touchpoints(token)
    before_ids = {str(t["id"]) for t in before}
    print(f"touchpoints before: {len(before)}")

    card_id = contact_id = None
    try:
        status, card = call(
            "POST",
            "/api/v1/crm/name-cards",
            token,
            {"status": "pending", "raw_ocr_text": "QA probe",
             "parsed_data": {"name": PROBE_NAME, "email": PROBE_TAIL, "company": "QA Probe Co"}},
        )
        assert status == 201 and card, f"create card failed: HTTP {status}"
        card_id = card["id"]
        print(f"created probe card: {card_id} (status={card.get('status')})")

        status, resolved = call("POST", f"/api/v1/crm/name-cards/{card_id}/resolve", token, {"action": "separate"})
        assert status == 200 and resolved, f"resolve failed: HTTP {status}"
        contact_id = resolved.get("contact_id")
        print(f"resolved (separate) -> contact: {contact_id}")

        after = all_touchpoints(token)
        new_ids = {str(t["id"]) for t in after} - before_ids
        new_rows = [t for t in after if str(t["id"]) in new_ids]
        namecard_rows = [t for t in after if str(t.get("type") or "") == "namecard"]
        print(f"touchpoints after: {len(after)} | new rows: {len(new_rows)} | type=namecard rows: {len(namecard_rows)}")
        if new_rows:
            for t in new_rows[:5]:
                print(f"  ! new touchpoint {t['id']} type={t.get('type')} title={t.get('title')!r}")
        ok = not new_rows and not namecard_rows
        print(f"RESULT: {'PASS' if ok else 'FAIL'} — resolve 唔再自動寫 touchpoint")
        return 0 if ok else 1
    finally:
        # 清走自己造嘅嘢（只按今次嘅 id，唔碰其他資料）
        if card_id:
            s, _ = call("DELETE", f"/api/v1/crm/name-cards/{card_id}", token)
            print(f"cleanup: delete card -> HTTP {s}")
        if contact_id:
            s, _ = call("DELETE", f"/api/v1/crm/contacts/{contact_id}", token)
            print(f"cleanup: delete contact -> HTTP {s}")


if __name__ == "__main__":
    raise SystemExit(main())
