"""結構性守門（KB-046）：request schema 嘅欄位一定要存在於 SQLAlchemy model。

為何要鎖：route 用 `Model(**payload.model_dump())` 建 row。Pydantic 會 dump **全部**
欄位（包括值係 None 嘅），所以 schema 多咗一個 model 冇嘅欄位 ⇒ 每個 request 都
`TypeError: '<field>' is an invalid keyword argument for <Model>` ⇒ HTTP 500。

實證（2026-09-16 發現）：f37a5b47（2026-09-15）喺 `schemas/crm.py` 加咗
`mobile` / `fax`（同一批 commit 亦加咗 UI 傳真欄、OCR 抽取 fax），但
`models/crm.py` 嘅 Contact 同 DB 都冇呢兩條 column ⇒
  · POST /api/v1/crm/contacts           → 100% HTTP 500（連最小 payload 都死）
  · POST /name-cards/{id}/resolve(separate) → HTTP 500
本 test 令同類 drift 喺 CI 就被攔住，唔會再流入 production。
"""
from __future__ import annotations

import inspect

import pytest
from pydantic import BaseModel

from app import models, schemas

SUFFIXES = ("Create", "Update", "Base")

# 已知、經人手核實屬於「刻意唔入 model」嘅欄位（route 有 pop() 或 exclude=）。
# 加新 entry 一定要寫低喺邊度 pop／exclude，否則就係掩蓋真 bug。
HANDLED_OUTSIDE_MODEL: dict[tuple[str, str], str] = {
    ("NoteUpdate", "expected_version"): "crm.py:4173 payload.pop() — 樂觀鎖用，唔係 Note column",
    ("TouchpointCreate", "contact_ids"): "crm.py:1602 model_dump(exclude=…) — M2M 另外處理",
    ("TouchpointCreate", "participants"): "crm.py:1602 model_dump(exclude=…) — M2M 另外處理",
    ("TouchpointCreate", "companies"): "crm.py:1602 model_dump(exclude=…) — M2M 另外處理",
    ("TouchpointUpdate", "contact_ids"): "update_touchpoint 以 exclude_unset + pop 處理 M2M",
    ("TouchpointUpdate", "participants"): "update_touchpoint 以 exclude_unset + pop 處理 M2M",
    ("TouchpointUpdate", "companies"): "update_touchpoint 以 exclude_unset + pop 處理 M2M",
    # Task custom fields 唔存喺 tasks table：由 crm.py create_task / update_task 嘅
    # `_apply_task_cf()` 寫入 nexus_crm.custom_field_values（定義驅動，讀由
    # `_load_custom_fields()` / nexus_crm.get_custom_fields()）。冇定義嘅 key 會（按設計）略過。
    ("TaskCreate", "custom_fields"): "create_task exclude= 後由 _apply_task_cf() 寫入 custom_field_values",
    ("TaskUpdate", "custom_fields"): "update_task pop 後由 _apply_task_cf() 寫入 custom_field_values",
}


def _load_all_model_modules() -> None:
    """app/models/__init__.py 唔會 import 各 module ⇒ 要自己掃。"""
    import importlib
    import pkgutil

    import app.models as models_pkg

    for mod in pkgutil.iter_modules(models_pkg.__path__):
        importlib.import_module(f"app.models.{mod.name}")


def _model_columns() -> dict[str, set[str]]:
    import sys

    _load_all_model_modules()
    out: dict[str, set[str]] = {}
    for name, module in list(sys.modules.items()):
        if module is None or not name.startswith("app.models"):
            continue
        for obj_name, obj in vars(module).items():
            mapper = getattr(obj, "__mapper__", None)
            if mapper is not None:
                out[obj_name] = {c.key for c in mapper.columns}
    return out


def _request_schemas() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for module_name in dir(schemas):
        module = getattr(schemas, module_name)
        if not inspect.ismodule(module):
            continue
        for name, obj in vars(module).items():
            if not (inspect.isclass(obj) and issubclass(obj, BaseModel)) or obj is BaseModel:
                continue
            if not name.endswith(SUFFIXES):
                continue
            out[name] = set(obj.model_fields)
    return out


def test_every_request_schema_field_exists_on_its_model():
    cols = _model_columns()
    offenders: list[str] = []
    checked = 0
    for schema_name, fields in sorted(_request_schemas().items()):
        base = schema_name
        for suffix in SUFFIXES:
            if base.endswith(suffix):
                base = base[: -len(suffix)]
                break
        model_cols = cols.get(base)
        if model_cols is None:
            continue  # 冇對應 model（例如純 response/內部 schema）
        checked += 1
        extra = sorted(
            f for f in fields
            if f not in model_cols and (schema_name, f) not in HANDLED_OUTSIDE_MODEL
        )
        if extra:
            offenders.append(f"{schema_name} → {base}: model 冇 {extra}")
    assert checked >= 5, f"只檢查到 {checked} 對 schema/model，selector 可能壞咗"
    assert not offenders, (
        "schema 有欄位但 model 冇（會令 route 一律 500）：\n  "
        + "\n  ".join(offenders)
        + "\n修正：喺 model + DB 加返 column，或喺 schema 移除該欄位（KB-046）。"
    )


@pytest.mark.parametrize("field", ["mobile", "fax"])
def test_contact_has_phone_book_columns(field: str):
    """名片 OCR / UI 傳真欄要真係入到 DB（唔可以得個 schema 名）。"""
    assert field in _model_columns()["Contact"]
