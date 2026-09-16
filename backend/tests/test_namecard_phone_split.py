"""電話／傳真分類 + 地址抽取（2026-09-15 Terrence：除 office phone 外要有 mobile、fax、office address）。

舊 bug：任何 8 位數字都當 mobile ⇒ 8 位公司直線被當成手機、真手機反而跌入 office；fax 亦會被當 office。
新邏輯：先睇 label（同段、號碼之前），再用 HK 手機特徵 fallback。
"""
from app.services.namecard_ocr import _hk_digits, classify_phones, extract_address


def test_label_mobile_and_office_separated():
    blob = "Marco Chan\nMobile: 9123 4567\nTel: 2345 6789\n"
    assert classify_phones(blob, ["9123 4567", "2345 6789"]) == ("9123 4567", "2345 6789", None)


def test_reversed_order_still_correct():
    """號碼次序倒轉都唔可以食隔籬 label（舊版會攞 8 位數當 mobile）。"""
    blob = "Office 2345 6789\nMobile 9876 5432\n"
    assert classify_phones(blob, ["2345 6789", "9876 5432"]) == ("9876 5432", "2345 6789", None)


def test_chinese_labels():
    blob = "陳大文\n手提 6123 4567\n電話 2988 7766\n"
    assert classify_phones(blob, ["6123 4567", "2988 7766"]) == ("6123 4567", "2988 7766", None)


def test_fallback_hk_mobile_shape_without_labels():
    mobile, office, fax = classify_phones("", ["6789 1234", "2345 6789"])
    assert (mobile, office, fax) == ("6789 1234", "2345 6789", None)


def test_plus852_mobile_recognised():
    assert _hk_digits("+852 9123 4567") == "91234567"
    mobile, _, _ = classify_phones("", ["+852 9123 4567"])
    assert mobile == "+852 9123 4567"


def test_one_office_number_only_mobile_stays_empty():
    mobile, office, fax = classify_phones("Tel 2345 6789", ["2345 6789"])
    assert mobile is None and office == "2345 6789" and fax is None


def test_mobile_only_card_gives_mobile_and_no_office():
    mobile, office, fax = classify_phones("WhatsApp 9876 5432", ["9876 5432"])
    assert mobile == "9876 5432" and office is None and fax is None


# ── fax（新）──────────────────────────────────────────────────────────
def test_fax_not_mistaken_for_office():
    """卡片：Tel + Fax ⇒ fax 唔可以當 office（舊版會當 office）。"""
    blob = "Wymax Technologies\nTel: 2345 6789\nFax: 2345 6780\n"
    mobile, office, fax = classify_phones(blob, ["2345 6789", "2345 6780"])
    assert office == "2345 6789" and fax == "2345 6780" and mobile is None


def test_fax_first_then_mobile_then_office():
    blob = "Fax 2345 6780\nMobile 9123 4567\nTel 2345 6789\n"
    mobile, office, fax = classify_phones(blob, ["2345 6780", "9123 4567", "2345 6789"])
    assert (mobile, office, fax) == ("9123 4567", "2345 6789", "2345 6780")


def test_chinese_fax_label():
    blob = "傳真 2988 7700\n電話 2988 7766\n"
    mobile, office, fax = classify_phones(blob, ["2988 7700", "2988 7766"])
    assert office == "2988 7766" and fax == "2988 7700" and mobile is None


def test_short_f_label():
    assert classify_phones("F: 2345 6780", ["2345 6780"]) == (None, None, "2345 6780")


# ── office address（新）────────────────────────────────────────────────
def test_address_extracted_when_keywords_present():
    lines = ["Wymax Technologies Limited", "Unit 1203, 12/F, Tower 2", "Metroplaza, Kwai Chung", "Hong Kong"]
    addr = extract_address(lines)
    assert "12/F" in addr or "Hong Kong" in addr


def test_address_absent_when_no_keywords():
    """冇地址關鍵字就唔可以亂抽（唔准填充）。"""
    lines = ["Marco Chan", "Sales Manager", "Wymax Technologies Limited"]
    assert extract_address(lines) == ""


def test_two_line_address_joined():
    lines = ["Metroplaza Tower 2", "223 Hing Fong Road, Kwai Chung"]
    assert extract_address(lines) == "Metroplaza Tower 2 223 Hing Fong Road, Kwai Chung"


def test_chinese_address():
    lines = ["永豐科技有限公司", "香港新界葵涌興芳路223號新都會廣場2座12樓1203室"]
    assert "葵涌" in extract_address(lines)
