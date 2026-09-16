"""KB-048 回歸測試：T+30 follow-up 嘅產出物只有 touchpoint，冇 task。

背景（2026-09-16 實證）：
- 2026-09-12 `fd66569` 喺 `ask_followup()` 加咗一條 task 生產線
  （`meeting_task.create_task_from_meeting`）→ 一個會議同時生 touchpoint
  （設計意圖）＋ task（後加）⇒ 6 條「跟進會議：」task，全部 auto_suggested、
  其他欄位空，其中 1 條係已取消會議。
- `_touchpoint_exists()` 用 `touchpoints.date`（DATE 欄）同 event timestamptz
  比 ⇒ 永遠 false（同日 touchpoint 睇唔到）⇒「已記錄就唔問」失效。
"""

import re
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import text

from app.db import async_session
from app.services import calendar_followup as cf

T = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER = uuid.UUID("a77d12c5-c02f-4335-88b2-1f293a74fe6f")  # terrence_lam@kinetix.com.hk

_BACKEND = Path(__file__).resolve().parents[1]
SERVICE_SRC = (_BACKEND / "app" / "services" / "calendar_followup.py").read_text(encoding="utf-8")

_TAG = "zz-kb048-regression"


@pytest.fixture(autouse=True)
async def _db_fixture():
    """同 test_meeting_task.py 一樣：每個 test 前後 dispose engine（避免 loop 綁死）。"""
    from app.db import engine

    await engine.dispose()
    yield
    await engine.dispose()


def test_meeting_task_service_is_gone():
    """會議唔可以生 task ⇒ 成個 service 刪咗。"""
    assert not (_BACKEND / "app" / "services" / "meeting_task.py").exists()


def test_followup_engine_creates_no_task():
    # 只 check「真 code」pattern（docstring 提到個名唔算）
    for needle in (
        "from app.services.meeting_task",
        "create_task_from_meeting(",
        "INSERT INTO nexus_crm.tasks",
    ):
        assert needle not in SERVICE_SRC, f"calendar_followup.py 唔准再建 task：{needle}"


def test_scan_has_canceled_guard():
    assert re.search(r"cancel", SERVICE_SRC, re.I), "scan_followups 要 skip 已取消 event"


async def _workspace_id(db) -> uuid.UUID:
    row = (
        await db.execute(
            text("SELECT id FROM nexus_auth.workspaces WHERE tenant_id = :t LIMIT 1"), {"t": T}
        )
    ).first()
    return row[0]


async def _setup(db):
    await db.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(T)})


@pytest.mark.asyncio
async def test_ask_followup_does_not_create_task(monkeypatch):
    """接線驗證：ask_followup 只可以「問」，唔准建立 task。"""

    async def fake_notify(db, tenant_id, user_id, ev, body, title=None):
        return True

    async def fake_channel_enabled(db, tenant_id, user_id, ch):
        return False

    monkeypatch.setattr(cf, "_inapp_notify", fake_notify)
    monkeypatch.setattr(cf, "_channel_enabled", fake_channel_enabled)

    class FakeEvent:
        id = uuid.uuid4()
        title = "接線測試會議（KB-048）"
        project_id = None
        # 2019 年某日：一定冇 touchpoint ⇒ 唔會撞「已記錄」分支
        start = datetime(2019, 1, 2, 4, 0, tzinfo=timezone.utc)
        end = datetime(2019, 1, 2, 5, 0, tzinfo=timezone.utc)

    async with async_session() as db:
        await _setup(db)
        before = (
            await db.execute(
                text(
                    "SELECT count(*) FROM nexus_crm.tasks "
                    "WHERE tenant_id = :t AND auto_suggested = true AND title LIKE '跟進會議%'"
                ),
                {"t": T},
            )
        ).scalar()
        res = await cf.ask_followup(db, T, USER, FakeEvent())
        await db.commit()
        await _setup(db)
        after = (
            await db.execute(
                text(
                    "SELECT count(*) FROM nexus_crm.tasks "
                    "WHERE tenant_id = :t AND auto_suggested = true AND title LIKE '跟進會議%'"
                ),
                {"t": T},
            )
        ).scalar()

    assert res["asked"] is True, res
    assert "task" not in res, f"ask_followup 唔應該再帶 task：{res}"
    assert after == before, f"冇新 task 至啱（before={before}, after={after}）"


@pytest.mark.asyncio
async def test_same_day_touchpoint_counts_as_logged():
    """同日 touchpoint 一定要被 check 到（KB-048 DATE vs timestamptz bug）。"""
    async with async_session() as db:
        await _setup(db)
        ws = await _workspace_id(db)
        await db.execute(
            text(
                "INSERT INTO nexus_crm.touchpoints "
                "(id, tenant_id, workspace_id, company_id, type, title, date, "
                " visibility_scope, version) "
                "VALUES (gen_random_uuid(), :t, :w, NULL, 'meeting', :title, :d, 'workspace', 1)"
            ),
            {"t": T, "w": ws, "title": _TAG, "d": date.today()},
        )
        await db.commit()

        class FakeEvent:
            id = uuid.uuid4()
            title = "同日 check 測試"
            project_id = None
            start = datetime.now(timezone.utc) - timedelta(hours=1)
            end = datetime.now(timezone.utc)

        await _setup(db)
        try:
            assert await cf._touchpoint_exists(db, T, USER, FakeEvent(), None) is True
        finally:
            await _setup(db)
            await db.execute(
                text("DELETE FROM nexus_crm.touchpoints WHERE tenant_id = :t AND title = :x"),
                {"t": T, "x": _TAG},
            )
            await db.commit()


@pytest.mark.asyncio
async def test_scan_skips_canceled_and_keeps_normal():
    """已取消 event 唔問（title guard），正常 event 照 due。"""
    now = datetime.now(timezone.utc)
    end = now - timedelta(minutes=40)
    normal_id, canceled_id = uuid.uuid4(), uuid.uuid4()

    async with async_session() as db:
        await _setup(db)
        for eid, title in (
            (normal_id, f"{_TAG} 正常會議"),
            (canceled_id, f"Canceled: {_TAG} 取消會議"),
        ):
            await db.execute(
                text(
                    "INSERT INTO nexus_crm.project_calendar_events "
                    "(id, tenant_id, title, start, \"end\", is_all_day, owner_user_id, "
                    " source, followup_status) "
                    "VALUES (:id, :t, :title, :s, :e, false, :uid, 'manual', 'pending')"
                ),
                {"id": eid, "t": T, "title": title, "s": end - timedelta(hours=1), "e": end, "uid": USER},
            )
        await db.commit()

        await _setup(db)
        try:
            due_ids = {ev.id for ev in await cf.scan_followups(db, T, USER, now)}
            assert normal_id in due_ids, "正常 event 應該 due"
            assert canceled_id not in due_ids, "已取消 event 唔可以 due"
        finally:
            await _setup(db)
            await db.execute(
                text("DELETE FROM nexus_crm.project_calendar_events WHERE id = ANY(:ids)"),
                {"ids": [normal_id, canceled_id]},
            )
            await db.commit()
