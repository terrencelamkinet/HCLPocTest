"""KB-047 回歸測試：custom fields 寫入路徑。

背景（實證 2026-09-16）：`nexus_crm.custom_field_values` 曾經 **0 行** —— 即係自
`module_name` 欄位加入之後，**所有 module**（tasks / contacts / companies / deals）
嘅 custom fields 寫入都從來冇成功過一次。兩個獨立根因：

  1. PG 函數 `nexus_crm.upsert_custom_field_value()` 冇填 `module_name`
     （column 係 NOT NULL 且無 default）→ `NotNullViolationError` → API 500。
  2. app 側 raw SQL 寫 `:param::type`。SQLAlchemy/asyncpg 會將 `:p_value_date::timestamptz`
     當成**一個** parameter 名 → `PostgresSyntaxError: syntax error at or near ":"`。
     正確寫法：`CAST(:param AS type)`。

呢個 test 同時鎖住兩者（① 靜態掃 app/，② 真 DB 行一次 upsert）。
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app"
TENANT = "00000000-0000-0000-0000-000000000001"
KEY = "zz_regression_cf"


def test_no_bind_param_double_colon_cast():
    """`:param::type` 會 500（asyncpg 當成 param 名）。必須用 `CAST(:param AS type)`。"""
    pat = re.compile(r":[a-z_][a-z0-9_]*::")
    offenders: list[str] = []
    for path in sorted(APP.rglob("*.py")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("--"):
                continue  # 註解／SQL 註解（正常會提到呢個 pattern）
            if pat.search(line):
                offenders.append(f"{path.relative_to(APP.parent)}:{lineno}")
    assert not offenders, f"app 內仍有 `:param::type`（會 500，改用 CAST）：{offenders}"


def test_upsert_custom_field_value_fills_module_name(db_conn):
    """真 DB：函數要自動由 definition 取 module_name，並且 upsert（第二次要更新同一行）。"""
    cur = db_conn.cursor()
    record_id = str(uuid.uuid4())
    def_id = None
    # 一定要 transaction-local GUC + 單一 transaction：session-level（false）會經
    # pgbouncer transaction pooling 漏俾下一個 app session（實測令
    # test_rag_citation_controls_isolation 見到 582 份文件，2026-09-16 踩過）。
    db_conn.autocommit = False
    try:
        cur.execute("SELECT set_config('app.tenant_id', %s, true)", (TENANT,))
        cur.execute(
            "INSERT INTO nexus_crm.custom_field_definitions "
            "(tenant_id, module_name, field_key, field_label, field_type, display_order) "
            "VALUES (%s, 'tasks', %s, 'ZZ regression', 'text', 999) RETURNING id",
            (TENANT, KEY),
        )
        def_id = cur.fetchone()[0]

        cur.execute(
            "SELECT nexus_crm.upsert_custom_field_value(%s, %s, %s, %s)",
            (TENANT, def_id, record_id, "regression-1"),
        )
        cur.execute(
            "SELECT module_name, value_text FROM nexus_crm.custom_field_values "
            "WHERE definition_id = %s AND record_id = %s",
            (def_id, record_id),
        )
        row = cur.fetchone()
        assert row is not None, "函數應該要寫入 custom_field_values"
        assert row[0] == "tasks", f"module_name 要自動填（實際 {row[0]!r}）"
        assert row[1] == "regression-1"

        # 第二次 upsert → 同一行更新，唔會多一行
        cur.execute(
            "SELECT nexus_crm.upsert_custom_field_value(%s, %s, %s, %s)",
            (TENANT, def_id, record_id, "regression-2"),
        )
        cur.execute(
            "SELECT count(*), max(value_text) FROM nexus_crm.custom_field_values "
            "WHERE definition_id = %s AND record_id = %s",
            (def_id, record_id),
        )
        n, latest = cur.fetchone()
        assert n == 1, f"upsert 唔應該出多過一行（實際 {n}）"
        assert latest == "regression-2"

        # 讀回路徑（API 用嘅 function）都要見到
        cur.execute(
            "SELECT count(*) FROM nexus_crm.get_custom_fields(%s, 'tasks', ARRAY[%s::uuid])",
            (TENANT, record_id),
        )
        assert cur.fetchone()[0] == 1, "get_custom_fields() 應該讀到啱啱寫入嘅值"
    finally:
        db_conn.rollback()          # 收 transaction（GUC 係 transaction-local，會自動清）
        if def_id:
            # 清理要自己一個 transaction（一樣要 transaction-local GUC —— 冇 GUC 嘅
            # query 會撞 RLS policy 爆 uuid ""）
            cur.execute("SELECT set_config('app.tenant_id', %s, true)", (TENANT,))
            cur.execute("DELETE FROM nexus_crm.custom_field_values WHERE definition_id = %s", (def_id,))
            cur.execute("DELETE FROM nexus_crm.custom_field_definitions WHERE id = %s", (def_id,))
            db_conn.commit()
        db_conn.autocommit = True
