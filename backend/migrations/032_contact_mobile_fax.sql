-- ============================================================================
-- 032 — Contact：補回 mobile / fax 欄位（KB-046）
-- ============================================================================
-- 背景：f37a5b47（2026-09-15）喺 `app/schemas/crm.py` 加咗 mobile / fax
-- （同一批改動亦加咗名片 UI 傳真欄同 OCR 抽 fax），但 model + DB 都冇跟上。
-- route 用 `Contact(**payload.model_dump())` ⇒ Pydantic dump 全部欄位（含 None）
-- ⇒ SQLAlchemy TypeError ⇒ HTTP 500：
--   · POST /api/v1/crm/contacts                    → 100% 500（連最小 payload）
--   · POST /api/v1/crm/name-cards/{id}/resolve     → action=separate 500
-- Idempotent（IF NOT EXISTS），唔會改動任何現有資料。
-- ============================================================================

ALTER TABLE nexus_crm.contacts ADD COLUMN IF NOT EXISTS mobile TEXT;
ALTER TABLE nexus_crm.contacts ADD COLUMN IF NOT EXISTS fax    TEXT;

-- 驗證
-- SELECT column_name FROM information_schema.columns
--  WHERE table_schema='nexus_crm' AND table_name='contacts'
--    AND column_name IN ('mobile','fax');
