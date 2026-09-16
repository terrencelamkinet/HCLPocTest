"""公司自動連（2026-09-15 Terrence：「公司當然要自動連」）。

比對語意跟 review_candidates（crm.py:2352）：① 逐字 case-insensitive ② normalize 後互相包含。
"""
from app.routers.crm import _apply_card_replacement, _pick_company_match

EX = [("c1", "Wymax Technologies Limited"), ("c2", "Kinetix Systems Ltd")]
def test_exact_match_case_insensitive():
    assert _pick_company_match("wymax technologies limited", EX) == "c1"


def test_suffix_variant_matches_after_normalise():
    assert _pick_company_match("Wymax Technologies Ltd.", EX) == "c1"


def test_short_name_contained_in_long_name():
    assert _pick_company_match("Wymax", EX) == "c1"


def test_no_match_returns_none():
    assert _pick_company_match("Cheung Kong Holdings", EX) is None


def test_empty_name_returns_none():
    assert _pick_company_match("", EX) is None
    assert _pick_company_match("   ", EX) is None


class _Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _pair(company_id=None):
    contact = _Obj(name="Old Name", email="a@x.com", phone=None, job_title=None,
                   company_id=company_id, dedup_status="pending",
                   last_verified_at=None, source="manual")
    card = _Obj(status="pending", dedup_status="pending", review_candidates=[{"x": 1}])
    return contact, card


def test_replace_sets_company_and_puts_old_value_in_history_diff():
    contact, card = _pair()
    diff = _apply_card_replacement(contact, card, {"email": "a@x.com"}, "Old Name",
                                   company_id="NEWCO")
    assert contact.company_id == "NEWCO"
    assert diff["company_id"] == (None, "NEWCO")   # 舊值 None → 新值，會寫入 contact_changes


def test_replace_records_previous_company_as_old_value():
    contact, card = _pair(company_id="OLDCO")
    diff = _apply_card_replacement(contact, card, {"email": "a@x.com"}, "Old Name",
                                   company_id="NEWCO")
    assert contact.company_id == "NEWCO"
    assert diff["company_id"] == ("OLDCO", "NEWCO")


def test_replace_skips_company_when_already_linked():
    contact, card = _pair(company_id="SAME")
    diff = _apply_card_replacement(contact, card, {"email": "a@x.com"}, "Old Name",
                                   company_id="SAME")
    assert "company_id" not in diff


def test_replace_without_company_does_not_touch_company_id():
    contact, card = _pair(company_id="KEEP")
    diff = _apply_card_replacement(contact, card, {"email": "b@y.com"}, "Old Name")
    assert contact.company_id == "KEEP"
    assert "company_id" not in diff
