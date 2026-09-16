"""add_namecard_spec_i18n_keys.py — 2026-09-15 Terrence spec 用嘅 i18n key。

插入去已存在嘅 `nameCard` section（唔 reformat 整檔；純文字插入；json.loads 驗證閘）。
跟 scripts/add_editor_i18n_keys.py 同一套做法。
"""
import json
import re
import sys

LOCALES = "src/i18n/locales"
SECTION = "nameCard"
FILES = ["en.json", "zh-TW.json"]

KEYS = {
    # contact 頁名片區（item E）
    "sectionTitle": "名片",
    "zoom": "放大名片",
    "currentCard": "目前",
    "oldCard": "舊紀錄",
    # contact timeline 名片紀錄（item D）
    "tlAdded": "新增名片",
    "tlUpdated": "更新名片",
    "tlOldKept": "舊名片已保留 — 點擊放大對照",
    # compare preview（item B）
    "noImage": "冇圖",
    "noCardImage": "冇名片圖",
    "cmpNewCard": "呢張新卡",
    "cmpExisting": "現有聯絡人",
    "fMobile": "手機",
    "fOfficePhone": "公司電話",
    "fFax": "傳真",
    "fAddress": "公司地址",
    # 3 個決定選項（item C）
    "replaceExisting": "取代現有",
    "replaceExistingSub": "現有資料自動存入紀錄（history），聯絡人狀態同步更新",
    "createNew": "開新記錄",
    "createNewSub": "唔取代現有，以新記錄形式並存",
    "discardNew": "刪除新卡",
    "discardNewSub": "刪除新記錄，唔會覆蓋現有",
    "confirmDiscard": "刪除呢張新卡？現有聯絡人唔會被改動。",
}

KEYS_EN = {
    "sectionTitle": "Name Card",
    "zoom": "Enlarge name card",
    "currentCard": "Current",
    "oldCard": "Previous",
    "tlAdded": "Name card added",
    "tlUpdated": "Name card updated",
    "tlOldKept": "Previous name card kept — click to compare",
    "noImage": "No image",
    "noCardImage": "No name card image",
    "cmpNewCard": "This card",
    "cmpExisting": "Existing contact",
    "fMobile": "Mobile",
    "fOfficePhone": "Office",
    "fFax": "Fax",
    "fAddress": "Office address",
    "replaceExisting": "Replace existing",
    "replaceExistingSub": "Old values are stored in history; contact status updates",
    "createNew": "Create new record",
    "createNewSub": "Keeps the existing contact, both records stay",
    "discardNew": "Delete new card",
    "discardNewSub": "Deletes the new record, nothing is overwritten",
    "confirmDiscard": "Delete this new card? The existing contact will not change.",
}


def parent_span(raw, key):
    depth = 0
    i = 0
    while i < len(raw):
        c = raw[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == '"' and depth == 1:
            j = raw.index('"', i + 1)
            if raw[i + 1:j] == key:
                b = raw.index("{", j)
                d = 0
                for k in range(b, len(raw)):
                    if raw[k] == "{":
                        d += 1
                    elif raw[k] == "}":
                        d -= 1
                        if d == 0:
                            return b, k
            i = j
        i += 1
    raise KeyError(key)


def insert(raw, section, pairs):
    b, e = parent_span(raw, section)
    old = json.loads(raw)
    have = old.get(section) or {}
    missing = {k: v for k, v in pairs.items() if k not in have}
    if not missing:
        return raw, []
    inner = raw.index("{", b) + 1
    m = re.search(r"\n([ \t]+)\"", raw[inner:e])
    indent = m.group(1)
    lines = [
        "%s%s: %s," % (indent, json.dumps(k, ensure_ascii=False), json.dumps(v, ensure_ascii=False))
        for k, v in missing.items()
    ]
    return raw[:inner] + "\n" + "\n".join(lines) + raw[inner:], list(missing)


def main():
    apply = "--apply" in sys.argv
    for name in FILES:
        path = "%s/%s" % (LOCALES, name)
        raw = open(path, encoding="utf-8").read()
        before = json.loads(raw)
        pairs = KEYS if name.startswith("zh") else KEYS_EN
        candidate, added = insert(raw, SECTION, pairs)
        if not added:
            print("SKIP %s：全部 key 已存在" % name)
            continue
        parsed = json.loads(candidate)
        if len(parsed[SECTION]) - len(before[SECTION]) != len(added):
            print("REFUSE %s：key 數唔對（+%d vs +%d）" % (name, len(parsed[SECTION]) - len(before[SECTION]), len(added)))
            return 1
        for k in added:
            if parsed[SECTION][k] != pairs[k]:
                print("REFUSE %s：%s 值唔對" % (name, k))
                return 1
        print("OK %s：+%d keys（nameCard %d → %d）" % (name, len(added), len(before[SECTION]), len(parsed[SECTION])))
        if apply:
            open(path, "w", encoding="utf-8").write(candidate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
