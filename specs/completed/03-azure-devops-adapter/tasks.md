# 任務清單

> **English summary:** Task checklist for azure-devops-adapter. Five steps covering adapter implementation, mocked tests, and README update.

**Spec:** 03-azure-devops-adapter
**Status:** VERIFIED

## Checklist

- [x] **Task 1: `adapters/azure_devops.py`**（2026-04-20 完成）
  - 新增檔案；`from __future__ import annotations` + `import json, os, shutil, subprocess`
  - Import `from adapters.base import PMAdapter` + `from models.task import UnifiedTask`
  - Class `AzureDevOpsAdapter(PMAdapter)`：
    - `__init__(self, org_url: str, project: str, pat: str)`：runtime check `shutil.which("az")`；None → `RuntimeError` 含三平台安裝指引
    - `_az(self, *args: str) -> dict`：拼 argv + PAT env + `subprocess.run(..., check=True, capture_output=True, text=True)` + `json.loads(stdout)`
    - `_sprint_id_to_native(self, sprint_id: str) -> str`：`"\\" in sprint_id` → 當 native 用；否則 `"sprint-12"` → `f"{self.project}\\Sprint 12"`
    - `get_item(self, item_id: int) -> UnifiedTask`：`raw = self._az("boards", "work-item", "show", "--id", str(item_id))`；`return UnifiedTask.from_azure_payload(raw)`
    - `list_sprint_items(self, sprint_id: str) -> list[UnifiedTask]`：
      - `native = self._sprint_id_to_native(sprint_id)`
      - `wiql = f"SELECT [System.Id] FROM WorkItems WHERE [System.IterationPath] = '{native}'"`
      - `id_rows = self._az("boards", "query", "--wiql", wiql)`
      - `return [self.get_item(row["id"]) for row in id_rows]`
  - **完成條件：** `python3 -c "from adapters.azure_devops import AzureDevOpsAdapter; print(AzureDevOpsAdapter.__mro__)"` 列出 class hierarchy 含 `PMAdapter` 跟 `ABC`

- [x] **Task 2: `tests/test_azure_adapter.py`**（2026-04-20 完成）
  - 新增檔案；`import json`、`from pathlib import Path`、`from unittest.mock import patch, MagicMock`、`import pytest`
  - Import `from adapters.azure_devops import AzureDevOpsAdapter` + `from models.task import UnifiedTask`
  - Fixture helper：`_load_fixture(name)` 讀 `tests/fixtures/azure/<name>.json`
  - Test 1 — `test_init_raises_when_az_missing`：
    ```python
    with patch("adapters.azure_devops.shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="az"):
            AzureDevOpsAdapter("https://dev.azure.com/acme", "AcmeDev", "dummy-pat")
    ```
  - Test 2 — `test_get_item_maps_azure_payload`：
    ```python
    raw_670 = _load_fixture("work_item_670")
    with patch("adapters.azure_devops.shutil.which", return_value="/usr/bin/az"), \
         patch("adapters.azure_devops.subprocess.run") as m_run:
        m_run.return_value = MagicMock(stdout=json.dumps(raw_670), returncode=0)
        adapter = AzureDevOpsAdapter("https://dev.azure.com/acme", "AcmeDev", "pat")
        task = adapter.get_item(670)
    assert isinstance(task, UnifiedTask)
    assert task.id == 670 and task.state == "In Progress"
    ```
  - Test 3 — `test_list_sprint_items_calls_wiql_then_fetches_each`：
    ```python
    raw_670 = _load_fixture("work_item_670")
    wiql_result = [{"id": 670}]
    with patch("adapters.azure_devops.shutil.which", return_value="/usr/bin/az"), \
         patch("adapters.azure_devops.subprocess.run") as m_run:
        m_run.side_effect = [
            MagicMock(stdout=json.dumps(wiql_result), returncode=0),  # WIQL
            MagicMock(stdout=json.dumps(raw_670), returncode=0),      # show #670
        ]
        adapter = AzureDevOpsAdapter("https://dev.azure.com/acme", "AcmeDev", "pat")
        tasks = adapter.list_sprint_items("sprint-12")
    assert len(tasks) == 1
    assert isinstance(tasks[0], UnifiedTask) and tasks[0].id == 670
    assert m_run.call_count == 2
    ```
  - **完成條件：** `python3 -m pytest tests/test_azure_adapter.py -v` 3 個 test 全 pass

- [x] **Task 3: 跑全測試確認無 regression**（2026-04-20 完成，7 passed）
  - `cd ~/dev/kc_pm_sync && python3 -m pytest tests/ -v`
  - 預期：7 passed（spec 01 × 1 + spec 02 × 3 + spec 03 × 3）
  - **完成條件：** 7 passed, 0 failed

- [x] **Task 4: `README.md` 加 Prerequisites 章節**（2026-04-20 完成）
  - 讀現有 README.md 結構
  - Edit 插入新章節在「當前狀態」之後、「MVP 範圍」之前
  - 內容涵蓋：
    - 裝 `az` CLI 各 OS（macOS `brew install azure-cli`、Linux MS doc 連結、Windows MS doc 連結）
    - 三個 env var export 範例
    - PAT scope 需求：`Work Items (Read)`
    - 提醒未來其他 adapter 可能有不同依賴，見各 adapter docstring
  - **完成條件：** README.md 有 `## Prerequisites` 章節，位置正確、內容完整

- [x] **Task 5: 再跑 pytest 確認文件改動不影響測試**（2026-04-20 完成，7 passed）
  - `python3 -m pytest tests/ -v`
  - **完成條件：** 仍 7 passed

## 備註

- Task 間依賴：1 → 2 → 3 → 4 → 5，不跳（4 依賴 3 的綠燈確定 code 無誤再改文件）
- mock subprocess 的 `side_effect` 是 ordered list，對應多次 `subprocess.run` 呼叫
- Test 2/3 都用 spec 01 已去敏的 `work_item_670.json` fixture，確保跨 spec 一致
- README 改動要 surgical，不動其他段落；改完 `git diff README.md` 肉眼過一遍
- Sprint id 轉換規則（`sprint-12` → `AcmeDev\\Sprint 12`）初版 hard-code；遇到多階層 iteration 時補到 future spec
