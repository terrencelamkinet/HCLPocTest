-- ============================================================================
-- 033 — Custom fields 寫入路徑修復（KB-047）
-- ============================================================================
-- 病徵：`PUT /tasks` 帶 `custom_fields` → HTTP 500。
--       實際 DB 檢查：`nexus_crm.custom_field_values` **0 行** —— 即係自
--       `module_name` 欄位加入之後，成個 custom fields 寫入路徑（所有 module）
--       從來冇成功寫過一次。
--
-- 根因（兩個獨立缺陷）：
--   1. `module_name`（NOT NULL，無 default）後加；但
--      `nexus_crm.upsert_custom_field_value()` 由 migration 003 開始就冇填呢個欄位
--      ⇒ NotNullViolationError。
--   2. App 側 `text()` 寫 `:p_value_date::timestamptz` —— asyncpg 會將
--      `:param::type` 當成一個 parameter 名 ⇒ PostgresSyntaxError（見 app/routers/crm.py）。
--
-- 本 migration 只修 (1)：函數由 definition 取 module_name 自動填入。
-- (2) 屬 app 層，已喺 crm.py / admin.py 改成 CAST(:x AS type)。
-- Idempotent（CREATE OR REPLACE），唔改任何現有 row。
-- ============================================================================

CREATE OR REPLACE FUNCTION nexus_crm.upsert_custom_field_value(
    p_tenant_id     UUID,
    p_definition_id UUID,
    p_record_id     UUID,
    p_value_text    TEXT DEFAULT NULL,
    p_value_number  NUMERIC DEFAULT NULL,
    p_value_boolean BOOLEAN DEFAULT NULL,
    p_value_date    DATE DEFAULT NULL,
    p_value_json    JSONB DEFAULT NULL
) RETURNS UUID LANGUAGE plpgsql AS $$
DECLARE
    v_id     UUID;
    v_module VARCHAR(50);
BEGIN
    -- module_name 由 definition 推導（caller 唔需要傳，避免又一個要同步嘅位）
    SELECT module_name INTO v_module
      FROM nexus_crm.custom_field_definitions
     WHERE id = p_definition_id;

    IF v_module IS NULL THEN
        RAISE EXCEPTION 'custom field definition % not found', p_definition_id;
    END IF;

    INSERT INTO nexus_crm.custom_field_values
        (tenant_id, definition_id, record_id, module_name,
         value_text, value_number, value_boolean, value_date, value_json)
    VALUES
        (p_tenant_id, p_definition_id, p_record_id, v_module,
         p_value_text, p_value_number, p_value_boolean, p_value_date, p_value_json)
    ON CONFLICT ON CONSTRAINT uq_custom_field_values_def_record
    DO UPDATE SET
        module_name   = COALESCE(custom_field_values.module_name, EXCLUDED.module_name),
        value_text    = COALESCE(p_value_text, custom_field_values.value_text),
        value_number  = COALESCE(p_value_number, custom_field_values.value_number),
        value_boolean = COALESCE(p_value_boolean, custom_field_values.value_boolean),
        value_date    = COALESCE(p_value_date, custom_field_values.value_date),
        value_json    = COALESCE(p_value_json, custom_field_values.value_json),
        updated_at    = now()
    RETURNING id INTO v_id;

    RETURN v_id;
END;
$$;
