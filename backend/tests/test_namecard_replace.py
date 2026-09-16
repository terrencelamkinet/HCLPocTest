"""replace（2026-09-15 Terrence spec ①）— 「取代現有」純邏輯測試。

Spec：pending 卡重複決定 = 3 個 object
  ① replace  現有值被新卡值覆蓋，**舊值自動入 history**（contact_changes）、contact status 更新
  ② separate 開新記錄（唔覆蓋）
  ③ delete   刪除新卡（唔覆蓋）→ 走 DELETE /name-cards/{id}，唔經 resolve

呢個 file 鎖住 ① 嘅規則：每改一個欄位 → 一行 history、卡冇值唔清空、no-op 唔加行、
contact status（dedup_status=resolved + last_verified_at）同卡狀態（matched/replaced）都要轉。
"""
import asyncio
import uuid
from types import SimpleNamespace

from app.routers.crm import _apply_card_replacement, _log_contact_changes

TENANT = uuid.uuid4()
ACTOR = uuid.uuid4()


class FakeDB:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)


def mk_contact(**kw):
    base = dict(
        id=uuid.uuid4(), tenant_id=TENANT, name="Old Name", email="old@x.com",
        phone="+852 1111", job_title="Sales", source="manual",
        dedup_status="pending_review", last_verified_at=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def mk_card():
    return SimpleNamespace(id=uuid.uuid4(), status="pending", dedup_status=None, review_candidates=[{"x": 1}])


def test_replace_overwrites_contact_and_old_values_go_to_history():
    contact, card = mk_contact(), mk_card()
    diff = _apply_card_replacement(
        contact, card,
        {"email": "NEW@X.com", "phone": "+852 2222", "title": "CTO"},
        "New Name",
    )
    # 新值生效（email 正規化成細寫）
    assert contact.name == "New Name"
    assert contact.email == "new@x.com"
    assert contact.phone == "+852 2222"
    assert contact.job_title == "CTO"
    # 舊值完整保留俾 history 用
    assert diff["name"] == ("Old Name", "New Name")
    assert diff["email"] == ("old@x.com", "new@x.com")
    assert diff["job_title"] == ("Sales", "CTO")

    db = FakeDB()
    n = asyncio.run(_log_contact_changes(
        db, tenant_id=TENANT, contact_id=contact.id, changes=diff,
        source="card", source_id=card.id, actor_id=ACTOR, confidence="high",
    ))
    # name / email / phone / job_title 四個欄位都變咗 ⇒ 四行 history
    assert n == 4 and len(db.added) == 4
    by_field = {o.field: o for o in db.added}
    assert by_field["email"].old_value == "old@x.com"
    assert by_field["email"].new_value == "new@x.com"
    assert by_field["email"].source == "card"
    assert by_field["email"].source_id == card.id


def test_replace_updates_contact_status_and_card_state():
    contact, card = mk_contact(), mk_card()
    _apply_card_replacement(contact, card, {"title": "CTO"}, "Old Name")
    # contact status 更新
    assert contact.dedup_status == "resolved"
    assert contact.last_verified_at is not None
    # 卡：已配對 + 標記 replaced + 清空候選
    assert card.status == "matched"
    assert card.dedup_status == "replaced"
    assert card.review_candidates == []


def test_replace_never_wipes_fields_the_card_did_not_show():
    contact, card = mk_contact(), mk_card()
    diff = _apply_card_replacement(
        contact, card, {"email": None, "phone": "   ", "title": ""}, None,
    )
    assert diff == {}
    assert contact.name == "Old Name"
    assert contact.email == "old@x.com"
    assert contact.phone == "+852 1111"
    assert contact.job_title == "Sales"


def test_replace_same_value_is_a_noop():
    contact, card = mk_contact(email="same@x.com"), mk_card()
    diff = _apply_card_replacement(contact, card, {"email": "same@x.com"}, "Old Name")
    assert diff == {}


def test_replace_keeps_source_when_set_and_defaults_to_namecard():
    kept, card1 = mk_contact(source="import"), mk_card()
    _apply_card_replacement(kept, card1, {"title": "CTO"}, None)
    assert kept.source == "import"

    blank, card2 = mk_contact(source=None), mk_card()
    _apply_card_replacement(blank, card2, {"title": "CFO"}, None)
    assert blank.source == "namecard"
