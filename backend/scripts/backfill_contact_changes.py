#!/usr/bin/env python3
"""由 activity_log 舊快照補錄 contact_changes（source='legacy'，confidence='low'）。

背景（實測 2026-09-15）：activity_log 有 14 行 contact 'updated'，存嘅係「更新後
完整欄位快照」（冇 old value，而且 None 被字串化成 "None"）→ 唯一忠實做法係
「前一條快照 vs 呢一條」diff。第一條快照冇 baseline（唔知之前係咩）→ 刻意 skip，
唔可以扮「由某值改過來」（Terrence 鐵律：AI 冇資料要明講，唔准填充當事實）。

可重複執行（同一 contact+field+changed_at 已存在就 skip）。
用法：cd backend && PYTHONPATH=. ./venv/bin/python scripts/backfill_contact_changes.py
"""
import asyncio
import sys
from datetime import timezone

from sqlalchemy import text

from app.db import async_session

TENANT = '00000000-0000-0000-0000-000000000001'

# 唔係「人嘅資料」嘅欄位 → 唔入歷史（source/namecard_path 等係系統欄位）
SKIP_FIELDS = {'source', 'namecard_path', 'dedup_status', 'last_verified_at', 'updated_at'}


def norm(v):
    if v is None:
        return None
    s = str(v).strip()
    if s == '' or s == 'None':
        return None
    return s


async def main() -> None:
    async with async_session() as s:
        await s.execute(text("SELECT set_config('app.tenant_id', :t, false)"), {'t': TENANT})
        rows = (await s.execute(text("""
            SELECT id, entity_id, actor_id, changes, created_at
            FROM nexus_crm.activity_log
            WHERE entity_type = 'contact' AND action = 'updated' AND changes IS NOT NULL
            ORDER BY entity_id, created_at
        """))).mappings().all()

        by_contact = {}
        for r in rows:
            by_contact.setdefault(str(r['entity_id']), []).append(r)

        inserted = 0
        skipped_first = 0
        for cid, snaps in by_contact.items():
            prev = None
            for snap in snaps:
                cur = snap['changes'] if isinstance(snap['changes'], dict) else {}
                if prev is None:
                    skipped_first += 1  # 冇 baseline，唔可以編造 old value
                    prev = cur
                    continue
                for field, raw_new in cur.items():
                    if field in SKIP_FIELDS:
                        continue
                    new_v = norm(raw_new)
                    old_v = norm(prev.get(field))
                    if old_v == new_v:
                        continue
                    exists = (await s.execute(text("""
                        SELECT count(*) FROM nexus_crm.contact_changes
                        WHERE contact_id = :c AND field = :f AND changed_at = :ts
                    """), {'c': cid, 'f': field, 'ts': snap['created_at']})).scalar()
                    if exists:
                        continue
                    await s.execute(text("""
                        INSERT INTO nexus_crm.contact_changes
                          (id, tenant_id, contact_id, field, old_value, new_value, source,
                           source_id, actor_id, confidence, verification_status, changed_at)
                        VALUES (gen_random_uuid(), :t, :c, :f, :o, :n, 'legacy',
                                :src, :a, 'low', 'unverified', :ts)
                    """), {
                        't': TENANT, 'c': cid, 'f': field, 'o': old_v, 'n': new_v,
                        'src': str(snap['id']), 'a': str(snap['actor_id']) if snap['actor_id'] else None,
                        'ts': snap['created_at'].astimezone(timezone.utc),
                    })
                    inserted += 1
                prev = cur

        await s.commit()
        total = (await s.execute(text(
            "SELECT count(*) FROM nexus_crm.contact_changes"))).scalar()
        by_src = (await s.execute(text(
            "SELECT source, count(*) FROM nexus_crm.contact_changes GROUP BY 1 ORDER BY 1"))).all()
        print(f"legacy rows inserted: {inserted}")
        print(f"first-snapshot skipped (no baseline): {skipped_first}")
        print(f"contact_changes total now: {total}")
        print(f"by source: {[tuple(x) for x in by_src]}")


asyncio.run(main())
sys.exit(0)
