"""contact_changes v1 — 欄位級聯絡人歷史（2026-09-15 Terrence + P仔 review）。

純邏輯測試（唔需要 DB）：fake session 收集 `db.add()` 出嘅物件，驗證
  ① 每個改動欄位一行 ② no-op（old == new）skip ③ 空字串／None 正規化
  ④ source 白名單 ⑤ manual = verified、card/ai = unverified（P仔：來源＋信心入 schema）
  ⑥ 名片併入情境（old=None 補空白欄位）

DB 層（RLS / tenant 隔離 / 真表）另外用真環境 curl + SQL 驗證。
"""
import asyncio
import uuid

import pytest

from app.routers.crm import CHANGE_SOURCES, _log_contact_changes

TENANT = uuid.uuid4()
CONTACT = uuid.uuid4()
ACTOR = uuid.uuid4()


class FakeDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)


def run(**kw):
    db = FakeDB()
    n = asyncio.run(
        _log_contact_changes(db, tenant_id=TENANT, contact_id=CONTACT, **kw)
    )
    return db, n


def test_one_row_per_changed_field():
    db, n = run(
        changes={"email": ("a@x.com", "b@y.com"), "job_title": ("Sales", "CTO")},
        source="manual",
        actor_id=ACTOR,
    )
    assert n == 2 and len(db.added) == 2
    by_field = {o.field: o for o in db.added}
    assert by_field["email"].old_value == "a@x.com"
    assert by_field["email"].new_value == "b@y.com"
    assert by_field["job_title"].new_value == "CTO"
    assert all(o.tenant_id == TENANT and o.contact_id == CONTACT for o in db.added)
    assert by_field["email"].actor_id == ACTOR


def test_noop_skipped():
    db, n = run(changes={"email": ("a@x.com", "a@x.com")}, source="manual")
    assert n == 0 and db.added == []


def test_blank_and_none_normalised_then_skipped():
    db, n = run(
        changes={"email": (None, ""), "phone": ("", ""), "job_title": (None, "CTO")},
        source="manual",
    )
    assert n == 1
    assert db.added[0].field == "job_title"
    assert db.added[0].old_value is None
    assert db.added[0].new_value == "CTO"


def test_manual_is_verified_others_unverified():
    db, _ = run(changes={"email": ("a", "b")}, source="manual")
    assert db.added[0].verification_status == "verified"
    assert db.added[0].confidence is None

    sid = uuid.uuid4()
    db2, _ = run(
        changes={"email": ("a", "b")}, source="card", source_id=sid, confidence="high"
    )
    assert db2.added[0].verification_status == "unverified"  # 卡 OCR：未經人確認
    assert db2.added[0].source == "card"
    assert db2.added[0].source_id == sid
    assert db2.added[0].confidence == "high"


def test_empty_actor_normalised_to_none():
    db, _ = run(changes={"email": ("a", "b")}, source="manual", actor_id="")
    assert db.added[0].actor_id is None


def test_unknown_source_rejected():
    with pytest.raises(ValueError):
        run(changes={"email": ("a", "b")}, source="gpt")


def test_source_enum_matches_pzai_review():
    assert CHANGE_SOURCES == {"card", "manual", "import", "merge", "ai", "legacy"}


def test_merge_backfill_keeps_none_old():
    """名片併入只補空白欄位 → old_value 必須係 None（唔可以扮「由某值改過來」）。"""
    db, n = run(
        changes={"email": (None, "x@y.com")},
        source="card",
        source_id=uuid.uuid4(),
        confidence="high",
    )
    assert n == 1
    assert db.added[0].old_value is None
    assert db.added[0].new_value == "x@y.com"
