"""T1 — /name-cards/{id}/resolve 單一定義 + action 詞彙正規化（KB-039）。

背景（實證）：
  · crm.py 曾經有兩個同名 POST /name-cards/{id}/resolve handler。
    FastAPI 先註冊先贏 ⇒ 第一個（收 merge / separate）係 live，
    第二個（收 overwrite / keep_both）永遠唔會執行。
  · live handler 用 `else:` 兜未知 action ⇒ 靜默當 separate（開新聯絡人）。
  · Telegram IM 名片流程送 overwrite / keep_both
    ⇒ 撳「覆蓋」實際開咗重複聯絡人，回覆仲話「已用名片更新現有聯絡人」。

呢個 test 鎖住：① 只可以有一條 resolve route ② 兩套詞彙都要映射正確 ③ 未知 action 回 None（→ 422）。
"""
import re
from pathlib import Path

import pytest

ROUTE = "/name-cards/{name_card_id}/resolve"
CRM = Path(__file__).resolve().parents[1] / "app" / "routers" / "crm.py"


def test_resolve_route_defined_exactly_once():
    """回歸測試：唔可以再有第二條同名 route（FastAPI 先註冊先贏 ⇒ 死代碼）。"""
    src = CRM.read_text(encoding="utf-8")
    hits = re.findall(r'@router\.(get|post|patch|delete|put)\("' + re.escape(ROUTE) + r'"', src)
    assert len(hits) == 1, f"resolve route 定義咗 {len(hits)} 次（應該 1 次）: {hits}"


def test_resolve_aliases_cover_both_vocabularies():
    """merge/overwrite 都要去 merge；separate/keep_both 都要去 separate。"""
    from app.routers.crm import _RESOLVE_ACTION_ALIASES as A

    assert A["merge"] == "merge"
    assert A["overwrite"] == "replace"
    assert A["separate"] == "separate"
    assert A["keep_both"] == "separate"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("merge", "merge"),
        ("MERGE", "merge"),
        (" merge ", "merge"),
        ("overwrite", "replace"),
        ("Overwrite", "replace"),
        ("separate", "separate"),
        ("keep_both", "separate"),
        ("KEEP_BOTH", "separate"),
    ],
)
def test_normalisation_is_case_and_space_insensitive(raw, expected):
    from app.routers.crm import _RESOLVE_ACTION_ALIASES as A

    assert A.get(str(raw).strip().lower()) == expected


@pytest.mark.parametrize("bad", ["", "garbage", "delete", "merge2", "0", "none"])
def test_unknown_action_maps_to_none(bad):
    """未知 action 必須 None ⇒ handler 回 422。唔可以再有 else 靜默當 separate。"""
    from app.routers.crm import _RESOLVE_ACTION_ALIASES as A

    assert A.get(str(bad).strip().lower()) is None


def test_no_silent_else_fallthrough_in_handler():
    """handler 唔可以再靠 else 兜 action（要顯式 422）。"""
    src = CRM.read_text(encoding="utf-8")
    start = src.index('async def resolve_name_card(')
    end = src.index('@router.patch("/name-cards/{name_card_id}"', start)
    body = src[start:end]
    assert "_RESOLVE_ACTION_ALIASES.get(raw_action)" in body
    assert "status_code=422" in body
    # 舊寫法（直接讀 body action 再 if/else）唔應該再存在
    assert 'action = (body.get("action") or "merge").lower()' not in body


# ── KB-045（2026-09-16）系統事件唔准自動寫 touchpoints ─────────────────────────
# 實證：cbe1e0a（2026-09-07 namecard-pending workflow）起，resolve_name_card 每次
# 都會 insert 一筆 type=namecard / title="Name card scanned & linked" 嘅 touchpoint，
# 但 description、company、location、channel、duration、participants 全部為空
# （14 筆，09-07 → 09-16），而同一個事實已經由 contact_changes（source=card）、
# activity log、中央通知三處記錄 ⇒ timeline 第四條重複記錄。


def test_resolve_handler_does_not_create_touchpoint():
    """回歸測試：resolve handler 唔准再自動創建 Touchpoint（人按／AI tool 才可以）。"""
    src = CRM.read_text(encoding="utf-8")
    start = src.index("async def resolve_name_card(")
    end = src.index('@router.patch("/name-cards/{name_card_id}"', start)
    body = src[start:end]
    assert "Touchpoint(" not in body, (
        "resolve_name_card 又再自動寫 touchpoint —— 系統事件唔屬於 touchpoints（KB-045）"
    )


def test_no_auto_namecard_touchpoint_title_left_in_source():
    """硬編碼英文 title 亦唔應該留低（順手鎖住 i18n 違規）。"""
    src = CRM.read_text(encoding="utf-8")
    assert "Name card scanned & linked" not in src


def test_resolve_still_records_the_fact_elsewhere():
    """移除 touchpoint 之後，好事實仍然要有人記（唔可以靜默唔記）。"""
    src = CRM.read_text(encoding="utf-8")
    start = src.index("async def resolve_name_card(")
    end = src.index('@router.patch("/name-cards/{name_card_id}"', start)
    body = src[start:end]
    assert "_log_contact_changes" in body or "contact_changes" in body
    assert "Notification" in body or "notification" in body

