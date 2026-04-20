# 任務清單

> **English summary:** Task checklist for unified-task-schema. Six steps, roughly 30 min each, designed for weeknight execution.

**Spec:** 01-unified-task-schema
**Status:** IN_PROGRESS

## Checklist

- [x] **Task 1: 產出 fixture #670**（2026-04-20 完成）
  - 預備：`source ~/.pm-sync.env`（含 AZDO_* 環境變數）
  - 執行：`mkdir -p tests/fixtures/azure && az boards work-item show --id 670 -o json > tests/fixtures/azure/work_item_670.json`
  - **去敏**（repo public，按 feedback_commit_desensitization 規則）：替換 `acme → acme`、`Acme → Acme`、`demo_user → demo_user`、`Demo User / Demo User → Demo User`、project UUID → `00000000-0000-0000-0000-000000000001`、user GUID → `11111111-1111-1111-1111-111111111111`、descriptor → `aad.REDACTED`
  - 驗證：檢視 JSON 結構，所有 needed fields 齊（grep `acme|demo_user` 零 hit）
  - 交付：`tests/fixtures/azure/work_item_670.json`（sanitized）
  - 預期 assertion 值（Task 4 要對）：id=670, type="Task", state="In Progress", title="Run through tech docs", iterationPath="AcmeDev\\Sprint 12", areaPath="AcmeDev", parent=597, assignee="demo_user@acme.onmicrosoft.com", changedDate="2026-04-20T02:11:40.087Z"

- [ ] **Task 2: UnifiedTask dataclass**（~30 分）
  - 新增 `models/task.py`：按 spec.md AC-1 列出全部欄位，用 `@dataclass` 標註，含 type hints
  - 新增 `models/__init__.py`：`from .task import UnifiedTask`
  - 不寫任何邏輯 / method，只宣告資料結構
  - **完成條件：** `python -c "from models.task import UnifiedTask; print(UnifiedTask.__dataclass_fields__.keys())"` 列出所有欄位

- [ ] **Task 3: from_azure_payload factory**（~40 分）
  - 在 `models/task.py` 的 `UnifiedTask` 類別裡加 `@classmethod def from_azure_payload(cls, raw: dict) -> "UnifiedTask"`
  - 實作 mapping：
    - `id` ← `raw["id"]`
    - `type` ← `raw["fields"]["System.WorkItemType"]`
    - `title` ← `raw["fields"]["System.Title"]`
    - `state` ← `raw["fields"]["System.State"]`
    - `assignee` ← `raw["fields"].get("System.AssignedTo", {}).get("uniqueName")`（可能整個 key 不存在）
    - `sprint_native_id` ← `raw["fields"]["System.IterationPath"]`
    - `sprint_id` ← `sprint_native_id` 最後一段轉小寫 + `-` 替換空格（`"AcmeDev\\Sprint 12"` → `"sprint-12"`）
    - `parent_id` ← `raw["fields"].get("System.Parent")`（int 或 None）
    - `area_path` ← `raw["fields"]["System.AreaPath"]`
    - `changed_at` ← 解析 `raw["fields"]["System.ChangedDate"]` ISO 字串為 tz-aware datetime
    - `platform` ← `"azure"`
    - `native` ← 完整 raw dict
  - 短名轉換規則寫進 docstring
  - **完成條件：** `python -c "import json; from models.task import UnifiedTask; t = UnifiedTask.from_azure_payload(json.load(open('tests/fixtures/azure/work_item_670.json'))); print(t)"` 印出合理結果

- [ ] **Task 4: pytest 測試**（~30 分）
  - 新增 `tests/__init__.py`（空）
  - 新增 `tests/test_task.py`：寫一支 `test_from_azure_payload_work_item_670()`
    - 用 `pathlib.Path` 定位 fixture
    - `json.load` 讀進 raw
    - 呼叫 `UnifiedTask.from_azure_payload(raw)`
    - assert 每個欄位值（**以去敏後 fixture 為準**）：id=670, type="Task", state="In Progress", title="Run through tech docs", sprint_id="sprint-12", sprint_native_id="AcmeDev\\Sprint 12", parent_id=597, assignee="demo_user@acme.onmicrosoft.com", `isinstance(changed_at, datetime)` 且 `changed_at.tzinfo is not None`
  - 不要加額外測試（其他 fixture 是後續 spec）
  - **完成條件：** `python -m pytest tests/test_task.py -v` 綠燈

- [ ] **Task 5: 安裝 pytest + 跑完整測試**（~15 分）
  - 檢查：`python -m pytest --version` 是否已裝
  - 沒裝 → `pip install --user pytest` 或建 venv（`python -m venv .venv && source .venv/bin/activate && pip install pytest`）— **任選，寫入 plan.md Notes**
  - 執行：`cd ~/dev/kc_pm_sync && python -m pytest tests/ -v`
  - **完成條件：** 所有測試 pass，output 至少一行 `PASSED`

- [ ] **Task 6: 更新 SKILL.md**（~15 分）
  - `version: 0.0.1` → `version: 0.1.0`
  - `status: skeleton` → `status: mvp-in-progress`
  - 在「當前狀態」章節加一句：「Schema layer complete（UnifiedTask + Azure payload factory）。Adapter / CLI 開發中。」
  - **完成條件：** commit 前 SKILL.md 已更新

## 備註

- Task 間依賴：1 → 2 → 3 → 4 → 5 → 6，不要跳
- 碎片型節奏：每晚一個 task，累的晚上跳過不影響（status 在 tasks.md 本身追蹤）
- 如果 Task 3 的 sprint_id 轉換規則遇到奇怪 path（Azure 多階層 iteration），先 hard-code 取 `split('\\')[-1].lower().replace(' ', '-')`，複雜 case 補進 future spec
- Task 4 的 assertion 值參考 `an internal Azure DevOps snapshot note` 裡 #670 的 snapshot（state="In Progress", parent=597, iterationPath="AcmeDev\\Sprint 12"）
- 全部完成後跑 `/spec check 01-unified-task-schema` 驗收，pass 後 `/spec report` 結案 + 資料夾自動搬去 `specs/completed/`
