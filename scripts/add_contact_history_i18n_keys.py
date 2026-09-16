"""add_contact_history_i18n_keys.py — 「欄位變更紀錄」（contact_changes v1 UI）嘅 i18n key。

跟 scripts/add_editor_i18n_keys.py 同一套做法：
  • 只加 missing key（idempotent）
  • **純文字插入**，唔 reformat 成個 locale 檔
  • 插完一定 json.loads 返嚟核對 + 其他 section 冇被動
特例：locale 檔本來冇 `contact` 呢個 top-level section → 今次係新建一個。
（zh-CN 冇 local JSON 檔，靠 DB／interim fallback 去 zh-TW，見 skill
 i18n-translation-management §判斷邊個 source 贏）

執行：python3 scripts/add_contact_history_i18n_keys.py --apply
"""
import json
import sys

LOCALES = "src/i18n/locales"
INDENT = "  "

SECTION = {
    "title": "Field change history",
    "sub": "One row per change — time, source, old value → new value",
    "retracted": "Retracted",
    "source": {
        "card": "Business card",
        "manual": "Manual",
        "merge": "Merged",
        "import": "Import",
        "ai": "AI",
        "legacy": "Legacy data",
    },
    "field": {
        "name": "Name",
        "email": "Email",
        "phone": "Phone",
        "job_title": "Job title",
        "title": "Job title",
        "company_id": "Company",
        "company": "Company",
        "notes": "Notes",
        "tags": "Tags",
        "address": "Address",
        "status": "Status",
        "source": "Source",
        "owner_id": "Owner",
        "next_follow_up": "Next follow-up",
    },
}

SECTION_TW = {
    "title": "欄位變更紀錄",
    "sub": "每次改動一行 — 時間、來源、舊值 → 新值",
    "retracted": "已撤回",
    "source": {
        "card": "名片",
        "manual": "人手",
        "merge": "併入",
        "import": "匯入",
        "ai": "AI",
        "legacy": "舊資料",
    },
    "field": {
        "name": "姓名",
        "email": "Email",
        "phone": "電話",
        "job_title": "職位",
        "title": "職位",
        "company_id": "公司",
        "company": "公司",
        "notes": "備註",
        "tags": "標籤",
        "address": "地址",
        "status": "狀態",
        "source": "來源",
        "owner_id": "負責人",
        "next_follow_up": "下次跟進",
    },
}

ALL = {"en.json": SECTION, "zh-TW.json": SECTION_TW}


def add_top_section(raw: str, section: str, value: dict) -> str:
    """喺最尾一個 top-level entry 之後插入一個新 section（保留原檔其餘內容）。"""
    end = raw.rstrip()
    if not end.endswith("}"):
        raise ValueError("locale 檔結尾唔係 }")
    body = end[:-1].rstrip()
    if not body.endswith(","):
        body += ","
    dumped = json.dumps(value, ensure_ascii=False, indent=2)
    indented = dumped.replace("\n", "\n" + INDENT)
    return body + '\n' + INDENT + '"%s": %s\n}' % (section, indented) + "\n"


def append_missing(raw: str, dotted: list, value: dict) -> str:
    """將 `contact.history.*` 入面缺嘅 key 補入已存在嘅 section（dict 遞歸）。"""
    data = json.loads(raw)
    node = data
    for k in dotted:
        node = node[k]
    added = {}

    def walk(target: dict, payload: dict, prefix: str):
        for k, v in payload.items():
            if isinstance(v, dict):
                target.setdefault(k, {})
                walk(target[k], v, "%s.%s" % (prefix, k))
            else:
                if k not in target:
                    target[k] = v
                    added["%s.%s" % (prefix, k)] = v

    walk(node, value, ".".join(dotted))
    if not added:
        return raw
    # 用純文字插入：搵到 section 物件 span（最簡單可靠 = json.dumps 整段換走該 section）
    start = raw.find('"%s"' % dotted[0])
    if start < 0:
        raise KeyError(dotted[0])
    brace = raw.index("{", start)
    depth, i = 0, brace
    while i < len(raw):
        if raw[i] == "{":
            depth += 1
        elif raw[i] == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    new_sec = json.dumps(data[dotted[0]], ensure_ascii=False, indent=2).replace("\n", "\n" + INDENT)
    rewritten = raw[:brace] + new_sec + raw[i:]
    if json.loads(rewritten)[dotted[0]] != data[dotted[0]]:
        raise ValueError("重寫 %s 之後內容唔一致" % dotted[0])
    return rewritten


def main() -> int:
    apply = "--apply" in sys.argv
    rc = 0
    for name, section in ALL.items():
        path = "%s/%s" % (LOCALES, name)
        raw = open(path, encoding="utf-8").read()
        old = json.loads(raw)
        if "contact" not in old:
            candidate = add_top_section(raw, "contact", {"history": section})
        else:
            candidate = append_missing(raw, ["contact"], {"history": section})
        parsed = json.loads(candidate)
        if parsed.get("contact", {}).get("history") != section:
            print("REFUSE %s：contact.history 內容唔一致" % name)
            rc = 1
            continue
        others_ok = all(parsed.get(k) == v for k, v in old.items() if k != "contact")
        if not others_ok:
            print("REFUSE %s：其他 section 被改動" % name)
            rc = 1
            continue
        nkeys = 3 + len(section["source"]) + len(section["field"])
        print("OK %s：contact.history（%d keys）" % (name, nkeys))
        if apply:
            open(path, "w", encoding="utf-8").write(candidate)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
