#!/usr/bin/env python3
"""補回名卡 parsed_data 嘅 mobile / office_phone / fax / address（2026-09-15 Terrence）。

做兩件事（只補、唔刪；冇把握就唔寫）：
  1. 有 raw_lines（OCR 原文）→ 重跑 classify_phones + extract_address
  2. 冇原文 → 只做安全判斷：現有 phone 若係 HK 手機形（8 位、開頭 5/6/9）→ 補做 mobile

用法：cd backend && PYTHONPATH=. ./venv/bin/python scripts/backfill_namecard_mobile.py [--apply]
"""
import asyncio
import re
import sys

from sqlalchemy import select, text

from app.db import async_session
from app.models.crm import NameCard
from app.services.namecard_ocr import (
    _PHONE_RE,
    _hk_digits,
    classify_phones,
    extract_address,
)

TENANT = '00000000-0000-0000-0000-000000000001'


def phones_from_lines(lines: list) -> tuple:
    blob = "\n".join(str(x) for x in lines)
    out = []
    for m in _PHONE_RE.finditer(blob):
        p = m.group(0)
        if len(re.sub(r"\D", "", p)) >= 7 and p not in out:
            out.append(p)
    return blob, out


async def main() -> None:
    apply = '--apply' in sys.argv
    fields_written = cards_touched = skipped = 0
    async with async_session() as s:
        # name_cards 有 RLS：唔設 app.tenant_id 會一行都睇唔到（跟 backfill_contact_changes.py）
        await s.execute(text("SELECT set_config('app.tenant_id', :t, false)"), {'t': TENANT})
        rows = (await s.execute(select(NameCard).where(NameCard.tenant_id == TENANT))).scalars().all()
        for card in rows:
            pd = dict(card.parsed_data or {})
            lines = pd.get('raw_lines') or []
            touched = False
            if isinstance(lines, list) and lines:
                blob, phones = phones_from_lines(lines)
                mobile, office, fax = classify_phones(blob, phones) if phones else (None, None, None)
                addr = extract_address(lines)
                for key, val in (('mobile', mobile), ('office_phone', office),
                                 ('fax', fax), ('address', addr)):
                    if val and not (pd.get(key) or '').strip():
                        pd[key] = val
                        if key == 'mobile':
                            pd['phone'] = val  # phone = 主要電話（手機優先）
                        print(f"[{key:12}] {card.id} → {val}")
                        fields_written += 1
                        touched = True
                if not touched:
                    skipped += 1
            else:
                d = _hk_digits(pd.get('phone') or '')
                if not (pd.get('mobile') or '').strip() and len(d) == 8 and d[:1] in '569':
                    pd['mobile'] = (pd.get('phone') or '').strip()
                    print(f"[{'mobile':12}] {card.id} → {pd['mobile']}（由 phone 補）")
                    fields_written += 1
                    touched = True
                else:
                    skipped += 1
            if touched:
                cards_touched += 1
            if apply and touched:
                card.parsed_data = pd  # 重新賦值令 SQLAlchemy 追蹤 jsonb 變更
        if apply:
            await s.commit()
        mode = 'APPLIED' if apply else 'DRY-RUN'
        print(f"\n{mode}：寫入 {fields_written} 個欄位、{cards_touched} 張卡、跳過 {skipped} 張、合共 {len(rows)} 張")


if __name__ == '__main__':
    asyncio.run(main())
