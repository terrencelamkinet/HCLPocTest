"""Calendar T+30 touchpoint follow-up engine (P3, 2026-09-09).

Design: docs/calendar-crm-integration-design-v3-2026-09-09.md §1/§5 + §11:
- T+30 (event end + 30min): check whether a touchpoint already exists for the
  event (linked company/contact within the event window). If yes -> silent
  (status 'created'). If no -> ASK the user once.
- Reply handling routes through telegram_inbound (_handle_pending_followup)
  — "唔使" -> skipped; content -> AI composes a touchpoint draft (reusing the
  draft->confirm flow), confirm executes and links the resolved company.
- WhatsApp channel bypassed (user 2026-09-09).

產出物只有 touchpoint，冇 task（KB-048，2026-09-16）：
  2026-09-12 `fd66569` 曾經喺 `ask_followup()` 加咗一條 task 生產線
  （`meeting_task.create_task_from_meeting`），令同一場會議生兩樣 artefact
  （touchpoint 意圖 + task 實體），產出 6 條「跟進會議：」task（連取消咗嘅
  會議都開單）。該生產線已移除：會議嘅唯一記錄 = touchpoint（用戶覆 → 草稿
  → 確認，見 telegram_inbound.py）。要 task 就人手開。
"""
from datetime import timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import text

from app.services.calendar_lifecycle_job import (  # noqa: E402
    _channel_enabled,
    _inapp_notify,
    _push_channel,
    _utcnow,
)

FOLLOWUP_DELAY_MIN = 30       # event end + 30 min → ask
FOLLOWUP_WINDOW_HOURS = 24    # user reply window before auto-expire

HK_TZ = ZoneInfo("Asia/Hong_Kong")

# `touchpoints.date` 係 DATE 欄（唔係 timestamptz）⇒ 一定要用「日」比。
# 舊寫法 `date >= :start`（start 係 event timestamptz）等於攞當日 00:00 同
# event 時間比 ⇒ 永遠 false ⇒「已記錄就唔問」失效（KB-048）。
TOUCHPOINT_EXISTS_SQL = (
    "SELECT id FROM nexus_crm.touchpoints "
    "WHERE (company_id = :cid OR (company_id IS NULL AND :cid IS NULL)) "
    "  AND date >= :d_from AND date <= :d_to "
    "LIMIT 1"
)


async def _event_company_id(db, ev) -> str | None:
    """Resolve the CRM company linked to this event (via project_id)."""
    pid = getattr(ev, "project_id", None)
    if not pid:
        return None
    row = (
        await db.execute(
            text("SELECT company_id FROM nexus_crm.projects WHERE id = :pid"),
            {"pid": str(pid)},
        )
    ).fetchone()
    return str(row[0]) if row and row[0] else None


async def _touchpoint_exists(db, tenant_id, user_id, ev, company_id: str | None) -> bool:
    """Event 當日（start 日 ~ end+30min 日）已經有 touchpoint ⇒ 當已記錄。

    KB-048：一定要落「日」層面比（見 TOUCHPOINT_EXISTS_SQL 註解）。
    """
    start = getattr(ev, "start", None)
    if not start:
        return False
    end = getattr(ev, "end", None)
    d_from = start.astimezone(HK_TZ).date()
    d_to = (end + timedelta(minutes=FOLLOWUP_DELAY_MIN)).astimezone(HK_TZ).date() if end else d_from
    rows = (
        await db.execute(
            text(TOUCHPOINT_EXISTS_SQL),
            {"cid": company_id, "d_from": d_from, "d_to": d_to},
        )
    ).fetchall()
    return len(rows) > 0


def _compose_ask(ev, company_name: str | None) -> str:
    head = (
        f"🤖 你啱啱開完會（{getattr(ev, 'end', None).astimezone().strftime('%H:%M') if getattr(ev, 'end', None) else ''}完）\n"
        f"📋 {getattr(ev, 'title', '')}"
    )
    if company_name:
        head += f"\n🏢 {company_name}"
    head += (
        "\n\nCRM 未有今次 meeting 嘅記錄。要唔要我幫你記低？\n"
        "直接講內容（例如「傾咗續約，佢話下個月決定」），或者覆「唔使」。"
    )
    return head


async def scan_followups(db, tenant_id, user_id, now) -> list[dict]:
    """T+30 due check — returns list of due follow-up events (P3a).

    Only events that ended within the last 48h are asked about (older ones
    auto-expire below — no spam from historical events).

    資格審查（KB-048）：已取消嘅 event 唔問（Google sync 會將 title 改成
    "Canceled: …"，表冇 status 欄，所以靠 title）。
    """
    try:
        await db.execute(
            text(
                "UPDATE nexus_crm.project_calendar_events SET followup_status = 'expired' "
                "WHERE owner_user_id = :uid AND followup_status = 'pending' "
                "  AND \"end\" < :recent"
            ),
            {"uid": str(user_id), "recent": now - timedelta(hours=48)},
        )
    except Exception:
        pass
    due: list[dict] = []
    rows = (
        await db.execute(
            text(
                "SELECT id, title, start, \"end\", project_id, followup_status, "
                "       followup_asked_at "
                "FROM nexus_crm.project_calendar_events "
                "WHERE owner_user_id = :uid "
                "  AND is_all_day = false "
                "  AND followup_status = 'pending' "
                "  AND \"end\" + interval '30 minutes' <= :now "
                "  AND \"end\" >= :recent "
                "  AND coalesce(title, '') !~* '^\\s*(canceled|cancelled)\\s*:' "
                "ORDER BY \"end\" LIMIT 10"
            ),
            {"uid": str(user_id), "now": now, "recent": now - timedelta(hours=48)},
        )
    ).fetchall()
    for row in rows:
        ev = type("E", (), {
            "id": row[0], "title": row[1], "start": row[2], "end": row[3],
            "project_id": row[4], "fp_status": row[5], "fp_asked_at": row[6],
        })()
        due.append(ev)
    return due


async def ask_followup(db, tenant_id, user_id, ev) -> dict:
    """Run the T+30 ask for one event (P3a). Returns result dict."""
    company_id = await _event_company_id(db, ev)
    company_name = None
    if company_id:
        comp = (
            await db.execute(
                text("SELECT name FROM nexus_crm.companies WHERE id = :cid"),
                {"cid": company_id},
            )
        ).fetchone()
        company_name = comp[0] if comp else None

    # Already logged by the user in CRM → silent (status created).
    if await _touchpoint_exists(db, tenant_id, user_id, ev, company_id):
        await db.execute(
            text(
                "UPDATE nexus_crm.project_calendar_events SET followup_status = 'created' "
                "WHERE id = :eid"
            ),
            {"eid": ev.id},
        )
        return {"asked": False, "reason": "touchpoint_exists", "company_id": company_id}

    body = _compose_ask(ev, company_name)
    inapp_ok = await _inapp_notify(
        db, tenant_id, user_id, ev, body, title=f"📝 記錄 Touchpoint：{getattr(ev, 'title', '')}"
    )
    tg_result = "skipped"
    if await _channel_enabled(db, tenant_id, user_id, "telegram"):
        tg_result = await _push_channel(db, tenant_id, user_id, "telegram", body)
    await db.execute(
        text(
            "UPDATE nexus_crm.project_calendar_events "
            "SET followup_status = 'asked', followup_asked_at = :ts "
            "WHERE id = :eid"
        ),
        {"ts": _utcnow(), "eid": ev.id},
    )
    return {
        "asked": True,
        "company_id": company_id,
        "channels": {"inapp": inapp_ok, "telegram": tg_result},
    }
