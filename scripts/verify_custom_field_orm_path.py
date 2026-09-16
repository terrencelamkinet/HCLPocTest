#!/usr/bin/env python3
"""[one-off] 驗 KB-047 第三條路：ORM endpoint
PUT /api/v1/crm/custom-field-values/{definition_id}（contacts/companies 等 UI 用嘅路徑）。

自清：臨時 definition + value 全部刪返。
"""
import json
import subprocess
import urllib.error
import urllib.request
import uuid

BASE = "http://127.0.0.1:8001"
TENANT = "00000000-0000-0000-0000-000000000001"
KEY = "zz_qa_probe_orm"
creds = json.load(open("/tmp/.nc_creds.json"))


def psql(sql):
    out = subprocess.run(["sudo", "-u", "postgres", "psql", "-d", "nexus_crm", "-tAc", sql],
                         capture_output=True, text=True, check=False)
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


s, tok = call("POST", "/api/v1/auth/login", body=creds)
token = tok["access_token"]
print("login:", s)

psql("insert into nexus_crm.custom_field_definitions "
     "(tenant_id, module_name, field_key, field_label, field_type, display_order) values "
     f"('{TENANT}','tasks','{KEY}','ZZ QA ORM','text',998)")
def_id = psql(f"select id from nexus_crm.custom_field_definitions where tenant_id='{TENANT}' and field_key='{KEY}'")
print("temp definition:", def_id)
if not def_id:
    raise SystemExit("定義插入失敗")

rec = str(uuid.uuid4())
st, body = call("PUT", f"/api/v1/crm/custom-field-values/{def_id}",
                token, {"record_id": rec, "value_text": "orm-1"})
print("PUT（新增）->", st, "|", body if not isinstance(body, dict) else {k: body.get(k) for k in ("record_id", "value_text", "module_name", "definition_id")})
print("  DB module_name =", psql(f"select module_name from nexus_crm.custom_field_values where definition_id='{def_id}' and record_id='{rec}'"))

st, body = call("PUT", f"/api/v1/crm/custom-field-values/{def_id}",
                token, {"record_id": rec, "value_text": "orm-2"})
print("PUT（更新）->", st, "| value_text =", body.get("value_text") if isinstance(body, dict) else body)
print("  DB rows/值 =", psql(f"select count(*)||' 行 / '||max(value_text) from nexus_crm.custom_field_values where definition_id='{def_id}' and record_id='{rec}'"))

print("cleanup: values", psql(f"delete from nexus_crm.custom_field_values where definition_id='{def_id}'"),
      "| defs", psql(f"delete from nexus_crm.custom_field_definitions where id='{def_id}'"))
print("殘留:", psql(f"select count(*) from nexus_crm.custom_field_definitions where field_key='{KEY}'"),
      psql(f"select count(*) from nexus_crm.custom_field_values where definition_id='{def_id}'"))
