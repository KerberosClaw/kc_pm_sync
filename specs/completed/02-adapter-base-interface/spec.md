# PMAdapter 抽象介面

> **English summary:** Abstract base class `PMAdapter` defining the read-only MVP contract (`list_sprint_items`, `get_item`) so future Azure / Trello / Jira adapters implement against a shared interface and return `UnifiedTask` instances.

## 六要素摘要（Task Prompt Schema）

- **目標（Goal）：** 定義跨平台 PM adapter 契約，讓 Azure 實作跟未來 Trello / Jira 用同一個介面，下游 CLI 不用關心平台細節。
- **範圍（Scope）：**
  - `adapters/base.py`（新增）
  - `adapters/__init__.py`（新增）
  - `tests/test_adapter_base.py`（新增）
- **輸入（Inputs）：**
  - `models.task.UnifiedTask`（spec 01 已完成）
  - Python stdlib `abc`（ABC + abstractmethod）
- **輸出（Outputs）：**
  - `PMAdapter` ABC（2 個 `@abstractmethod`：`list_sprint_items` / `get_item`）
  - 契約 docstring（sprint_id 短/native/macro 規範）
  - 3 個 passing pytest
- **驗收（Acceptance）：** 見 AC-1~6
- **邊界（Boundaries）：** 不含 Azure 實作、不含 CLI、不擴充非 MVP 方法、不定義 constructor

## 背景

Spec 01 已經交出 `UnifiedTask` — 跨平台的共同「名詞」。Spec 02 要補的是共同「動詞」：**資料怎麼拿進來。**

沒這層抽象，Azure 實作會直接被 CLI 呼叫，未來要加 Trello / Jira 就會寫成多個 if/else 分支，違反 `README.md` 的 adapter pattern 原則。

這個 spec 只定**契約**，不做任何平台實作。交付完成後，spec 03（Azure DevOps adapter）跟 spec 04（CLI）才有可撞牆的對象。

## 驗收條件

- [ ] **AC-1**：`adapters/base.py` 定義 `PMAdapter(ABC)`，含 2 個 `@abstractmethod`：
  - `list_sprint_items(self, sprint_id: str) -> list[UnifiedTask]`
  - `get_item(self, item_id: int) -> UnifiedTask`
  - 兩方法 type hints 完整（argument + return type）
- [ ] **AC-2**：`list_sprint_items` docstring 明確寫出 sprint_id 契約：
  - 短形式（`"sprint-12"`）**MUST** 支援
  - native 形式（`"AcmeDev\\Sprint 12"`）**MAY** 支援
  - 平台 macro（如 `"@current"`）**MAY** 支援
- [ ] **AC-3**：`adapters/__init__.py` export `PMAdapter`（`from .base import PMAdapter` + `__all__`）
- [ ] **AC-4**：`tests/test_adapter_base.py` 3 個測試全過：
  - `test_cannot_instantiate_abstract` — 直接 `PMAdapter()` raise `TypeError`
  - `test_subclass_missing_method_cannot_instantiate` — 只實作一個方法的子類實例化 raise `TypeError`
  - `test_fully_implemented_subclass_instantiates` — 完整實作的 mock 子類可實例化、方法呼叫回傳預期值
- [ ] **AC-5**：執行 `python -m pytest tests/ -v` 既有 spec 01 測試 + 新測試全綠（**不可 regression**）
- [ ] **AC-6**：不連網、不 import 任何 live Azure / Trello SDK、不 import 尚未存在的 `adapters/azure_devops.py`

## 不做的事

- **不做 Azure DevOps 實作**（`adapters/azure_devops.py` 是 spec 03）
- **不做 CLI entrypoint**（`scripts/sprint.py` 是 spec 04）
- **不定義 `__init__` 或 constructor**：各平台認證參數不同（Azure: PAT+org+project；Trello: api_key+token+board_id），base 不假設
- **不加 write-path 方法**（`push_item` / `update_item` / `close_item` — future spec）
- **不加其他 read 方法**（`list_sprints` / `list_my_items` / `search` — 非 MVP 範圍）
- **不做 sprint_id 正規化 helper**（留 adapter 內部自理；base 只定契約不給 util）
- **不做自訂 exception class**（初版讓 native 的 `requests.HTTPError` / `KeyError` 自然冒出；future spec 再包統一 `PMAdapterError`）
- **不做 retry / rate limiting**（Azure read quota 很鬆，MVP 用不到）

## 依賴

- **spec 01（01-unified-task-schema）**：必須已完成並可 `from models.task import UnifiedTask`
- **Python 3.9+**：`abc` stdlib 從 Python 2.6 就有；`from __future__ import annotations` 讓 `list[UnifiedTask]` 在 3.9 可 import
- **pytest**：dev only（spec 01 已裝 pytest 8.4.2）
- **stdlib only**（`abc`、`typing` 不必要、沒有第三方 dependency）
