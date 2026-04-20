# Unified Task Schema

> **English summary:** Platform-neutral `UnifiedTask` dataclass that parses Azure DevOps work item API responses into a stable schema, with offline unit tests driven by real-world fixtures.

## 六要素摘要（Task Prompt Schema）

- **目標（Goal）：** kc_pm_sync 有一個平台中立的 Task schema，能 parse Azure DevOps work item JSON 成統一格式，供後續 adapter / CLI 使用。
- **範圍（Scope）：**
  - `models/task.py`（新增）
  - `models/__init__.py`（新增 / 更新 export）
  - `tests/test_task.py`（新增）
  - `tests/__init__.py`（新增，空檔）
  - `tests/fixtures/azure/work_item_670.json`（新增，去敏後的真實 Azure 資料）
- **輸入（Inputs）：**
  - Azure DevOps work item API 回傳格式（`az boards work-item show --id N` / REST API `/_apis/wit/workitems/N`）
  - 具體欄位已由 2026-04-20 的 `an internal Azure DevOps snapshot note` 驗證過
- **輸出（Outputs）：**
  - `UnifiedTask` dataclass（8 必填 + 2 預設欄位）
  - `UnifiedTask.from_azure_payload(raw: dict) -> UnifiedTask` classmethod
  - 至少 1 個 fixture 檔（work_item_670.json）
  - 1 份 pytest 測試跑通
- **驗收（Acceptance）：** 見下方 AC-1〜AC-5
- **邊界（Boundaries）：** 見下方「不做的事」

## 背景

`kc_pm_sync` 的 MVP 目標是 `/pm-sync sprint` — 列出當前 sprint 的 work items。要做到這件事，**先要有一個「work item 長什麼樣」的型別**，不然 adapter、CLI、整個上層都沒依據。

這個 spec 是 MVP roadmap 的 task #1，**只做 schema 跟 fixture**，讓後續 task #2（adapter base interface）、task #3（Azure adapter 實作）、task #4（CLI entrypoint）有共同語言。

設計原則繼承 `README.md` 的「Adapter pattern + Unified Task model + Loose coupling」。

## 驗收條件

- [ ] **AC-1**：`UnifiedTask` dataclass 定義完整，含所有欄位（id / type / title / state / assignee / sprint_id / sprint_native_id / parent_id / area_path / changed_at / platform / native）+ type hints 完整標註
- [ ] **AC-2**：`UnifiedTask.from_azure_payload(raw: dict) -> UnifiedTask` classmethod 可以吃 Azure work item API 回傳的 JSON，正確 map 所有欄位。特別確認：
  - `fields["System.IterationPath"]` → 拆成 `sprint_id`（短名）+ `sprint_native_id`（原樣）
  - `fields["System.Parent"]` 不存在時 → `parent_id = None`
  - `fields["System.AssignedTo"]` 不存在（未指派）時 → `assignee = None`
  - `fields["System.ChangedDate"]` → 解析成 `datetime` 物件（帶 tzinfo）
  - 完整 raw 進 `native` 欄位
- [ ] **AC-3**：至少 1 個 fixture（the user's Task #670，Azure DevOps 真實資料）存在於 `tests/fixtures/azure/work_item_670.json`
- [ ] **AC-4**：執行 `cd ~/dev/kc_pm_sync && python -m pytest tests/` 通過，至少包含一個測試讀 fixture 過 `from_azure_payload` 後 assert 每個關鍵欄位值
- [ ] **AC-5**：整個 spec 不連網、不呼叫 Azure API、不依賴 `az` CLI，純離線可跑

## 不做的事

- **不做 adapter interface**（`adapters/base.py`、`adapters/azure_devops.py` 是 task #2 / #3）
- **不做 CLI entrypoint**（`scripts/sprint.py` 是 task #4）
- **不打 live Azure DevOps API**（dev 全走 fixture）
- **不支援其他平台**（Trello / Jira / GitHub Issues — future spec）
- **不實作 parent→children 樹狀 walk**（`parent_id` 只存 int，不自動 fetch parent）
- **不加 Effort / Story Points 欄位**（our workplace Azure 真實資料 sampled active backlog，Effort 填寫率 0 → YAGNI）
- **不做 serialize 回 Azure payload 的 `to_azure_payload()`**（push 是後續 task）
- **不做 CI 設定**（pytest 能在本機跑就達標）
- **不處理畸形 / 不完整 payload**：缺 required key（如 Title / State / WorkItemType）時讓 `KeyError` 自然冒出，不包裝自訂 exception。只有 AC-2 明列的 optional key（Parent / AssignedTo）用 `.get()` 容錯。

## 依賴

- **Python 3.10+**（dataclass + `str | None` union syntax + `from __future__ import annotations` 可選）
- **pytest**（dev only，安裝到 venv 或 `pip install --user pytest`；實作時可考慮 `requirements-dev.txt`）
- **stdlib only**（`dataclasses`、`datetime`、`json`、`pathlib`）— 不引入第三方 parser
- **fixture 資料來源**：user needs to run `source ~/.pm-sync.env && az boards work-item show --id 670 -o json > ~/dev/kc_pm_sync/tests/fixtures/azure/work_item_670.json` 產出（或在 task #1 內執行）
