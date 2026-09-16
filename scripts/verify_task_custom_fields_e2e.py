#!/usr/bin/env python3
"""[one-off] 驗 KB-047 真身：Task custom fields 係「定義驅動」存喺 custom_field_values，
唔係 tasks table 嘅 column。

步驟（全部自清）：
 1. 為 tenant 1 / module 'tasks' 插一條臨時定義 zz_qa_probe
 2. API create task 帶 custom_fields → 讀 API + 讀 DB
 3. API patch  帶 custom_fields → 讀 DB（呢步係關鍵：update 有冇真正寫入）
 4. 清走 value / task / definition
"""
import json
import subprocess
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8001"
TENANT = "00000000-0000-0000-0000-000000000001"
KEY = "zz_qa_probe"
creds = json.load(open("/tmp/.nc_creds.json"))


def psql(sql):
    out = subprocess.run(
        ["sudo", "-u", "postgres", "psql", "-d", "nexus_crm", "-tAc", sql],
        capture_output=True, text=True, check=False,
    )
    return (out.stdout or out.stderr).strip()


def call(method, path, token=None, body=None):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data, timeout=60) as r:
            raw = r.read().decode() or "null"
            return r.status, (json.loads(raw) if raw.strip().startswith(("{", "[")) else raw)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def db_value(task_id):
    return psql(
        "select coalesce(v.value_text,'<null>') from nexus_crm.custom_field_values v "
        "join nexus_crm.custom_field_definitions d on d.id = v.definition_id "
        f"where v.record_id = '{task_id}' and d.field_key = '{KEY}'"
    )


s, tok = call("POST", "/api/v1/auth/login", body=creds)
token = tok["access_token"]
print("login:", s)

psql(
    "insert into nexus_crm.custom_field_definitions "
    "(tenant_id, module_name, field_key, field_label, field_type, display_order) values "
    f"('{TENANT}', 'tasks', '{KEY}', 'ZZ QA Probe', 'text', 999)"
)
def_id = psql(f"select id from nexus_crm.custom_field_definitions where tenant_id='{TENANT}' and module_name='tasks' and field_key='{KEY}'")
print("temp definition id:", def_id or "(失敗)")
if not def_id:
    raise SystemExit("定義插入失敗，停手")

st, created = call("POST", "/api/v1/crm/tasks", token, {"title": "ZZ QA cf probe", "custom_fields": {KEY: "hello-123"}})
print("POST /tasks ->", st, "| body =", created if not isinstance(created, dict) else {k: created.get(k) for k in ("id", "title", "custom_fields")})
if not isinstance(created, dict):
    psql(f"delete from nexus_crm.custom_field_definitions where id='{def_id}'")
    raise SystemExit("create 失敗，已清走臨時定義")
tid = created.get("id")
print("  DB custom_field_values.value_text =", db_value(tid))

st, _ = call("PATCH", f"/api/v1/crm/tasks/{tid}", token, {"custom_fields": {KEY: "updated-456"}})
print("PATCH /tasks/{id} ->", st)
print("  DB custom_field_values.value_text =", db_value(tid))

st, read = call("GET", f"/api/v1/crm/tasks/{tid}", token)
print("GET API custom_fields =", read.get("custom_fields"))

# cleanup
print("cleanup: value", psql(f"delete from nexus_crm.custom_field_values where record_id='{tid}'"),
      "| task", call("DELETE", f"/api/v1/crm/tasks/{tid}", token)[0],
      "| def", psql(f"delete from nexus_crm.custom_field_definitions where id='{def_id}'"))
print("殘留檢查: values =", psql(f"select count(*) from nexus_crm.custom_field_values where record_id='{tid}'"),
      "| defs =", psql(f"select count(*) from nexus_crm.custom_field_definitions where field_key='{KEY}'"),
      "| task =", psql("select count(*) from nexus_crm.tasks where title='ZZ QA cf probe'"))
