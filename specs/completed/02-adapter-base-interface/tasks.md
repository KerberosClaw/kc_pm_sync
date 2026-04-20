# 任務清單

> **English summary:** Task checklist for adapter-base-interface. Four small steps, ~15 min each.

**Spec:** 02-adapter-base-interface
**Status:** VERIFIED

## Checklist

- [x] **Task 1: `adapters/base.py`**（2026-04-20 完成）
  - 新增檔案；`from __future__ import annotations` + `from abc import ABC, abstractmethod` + `from models.task import UnifiedTask`
  - 定 `class PMAdapter(ABC):`，class-level docstring 說明 adapter pattern 用途
  - 加 `@abstractmethod def list_sprint_items(self, sprint_id: str) -> list[UnifiedTask]:`，docstring 明寫 sprint_id 契約（短 MUST / native MAY / macro MAY）
  - 加 `@abstractmethod def get_item(self, item_id: int) -> UnifiedTask:`，docstring 說明參數意義
  - **完成條件：** `python3 -c "from adapters.base import PMAdapter; print(PMAdapter.__abstractmethods__)"` 列出 `{'list_sprint_items', 'get_item'}`

- [x] **Task 2: `adapters/__init__.py`**（2026-04-20 完成）
  - `from .base import PMAdapter`
  - `__all__ = ["PMAdapter"]`
  - **完成條件：** `python3 -c "from adapters import PMAdapter; print(PMAdapter)"` 不爆錯

- [x] **Task 3: `tests/test_adapter_base.py`**（2026-04-20 完成）
  - 新增檔案；`import pytest`、`from adapters.base import PMAdapter`、`from models.task import UnifiedTask`、`from datetime import datetime, timezone`
  - `test_cannot_instantiate_abstract`：
    ```python
    with pytest.raises(TypeError):
        PMAdapter()
    ```
  - `test_subclass_missing_method_cannot_instantiate`：
    ```python
    class Incomplete(PMAdapter):
        def list_sprint_items(self, sprint_id): return []
    # get_item 未實作
    with pytest.raises(TypeError):
        Incomplete()
    ```
  - `test_fully_implemented_subclass_instantiates`：
    ```python
    class Dummy(PMAdapter):
        def list_sprint_items(self, sprint_id):
            return [_make_stub_task()]
        def get_item(self, item_id):
            return _make_stub_task(id=item_id)

    def _make_stub_task(id=1):
        return UnifiedTask(
            id=id, type="Task", title="stub", state="New",
            assignee=None, sprint_id="sprint-1",
            sprint_native_id="X\\Sprint 1", parent_id=None,
            area_path="X", changed_at=datetime.now(timezone.utc),
        )

    adapter = Dummy()
    items = adapter.list_sprint_items("sprint-12")
    assert len(items) == 1 and items[0].type == "Task"
    item = adapter.get_item(42)
    assert item.id == 42
    ```
  - **完成條件：** `python3 -m pytest tests/test_adapter_base.py -v` 3 個 test 全 pass

- [x] **Task 4: 跑全測試 + 確認無 regression**（2026-04-20 完成，4 passed）
  - `cd ~/dev/kc_pm_sync && python3 -m pytest tests/ -v`
  - 預期：4 passed（spec 01 的 1 個 + spec 02 的 3 個）
  - **完成條件：** 4 passed, 0 failed, 0 errors

## 備註

- Task 間依賴：1 → 2 → 3 → 4，不跳
- Python 3.9 相容：沿用 spec 01 的 `from __future__ import annotations` pattern，`list[UnifiedTask]` 在 3.9 也能 import
- Task 3 的 `_make_stub_task` helper 放在 test module 裡，不進 production code（production 不需要「隨便弄一個 UnifiedTask」的 utility）
- ABC 語義小知識：Python `abc.ABCMeta` 會在 `__new__` 階段檢查 `__abstractmethods__` set，子類若未清空該 set 就實例化會 raise `TypeError: Can't instantiate abstract class X with abstract methods ...`
