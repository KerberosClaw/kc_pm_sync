# 任務清單

> **English summary:** Six steps to ship the CLI MVP, ending with one real end-to-end smoke test.

**Spec:** 04-cli-sprint-entrypoint
**Status:** VERIFIED

## Checklist

- [x] **Task 1: `scripts/__init__.py`**（2026-04-20 完成）
  - 空檔，讓 pytest 可 import `scripts.sprint` module
  - **完成條件：** 檔案存在且為空（或只有註解）

- [x] **Task 2: `scripts/sprint.py`**（2026-04-20 完成）
  - `from __future__ import annotations`；import `argparse, json, os, sys`、`dataclasses.asdict`、`from adapters.azure_devops import AzureDevOpsAdapter`
  - `REQUIRED_ENV = ("AZDO_ORG_URL", "AZDO_PROJECT", "AZDO_PAT")`
  - `def _load_env_or_exit() -> tuple[str, str, str]`：檢查三個 env vars，缺就 stderr 印訊息 + `sys.exit(1)`
  - `def _truncate(s: str, n: int) -> str`：`s if len(s) <= n else s[:n-1] + "…"`
  - `def _format_table(tasks: list[UnifiedTask]) -> str`：計算欄寬、ljust、輸出含 header 的表
  - `def _format_json(tasks: list[UnifiedTask]) -> str`：asdict + 去 `native` + datetime → isoformat → json.dumps(indent=2)
  - `def main() -> int`：
    - argparse：positional `sprint_id`、optional `--json`
    - call `_load_env_or_exit()` 拿三個值
    - `adapter = AzureDevOpsAdapter(org, project, pat)`
    - `tasks = adapter.list_sprint_items(args.sprint_id)`
    - print JSON 或 table，return 0
  - `if __name__ == "__main__": sys.exit(main())`
  - **完成條件：** `python3 scripts/sprint.py --help` 出 argparse 自動 help，無 import error

- [x] **Task 3: `tests/test_sprint_cli.py`**（2026-04-20 完成）
  - `import json, os`、`from unittest.mock import patch, MagicMock`、`import pytest`
  - Import `from scripts.sprint import main` + helpers
  - Helper `_make_stub_task(id, title, assignee, ...)` 造 UnifiedTask（抄 test_adapter_base.py 的 _make_stub_task）
  - Test 1 — `test_exits_when_env_missing`：
    - `monkeypatch.delenv("AZDO_PAT", raising=False)`
    - `patch('sys.argv', ['sprint.py', 'sprint-12'])`
    - `with pytest.raises(SystemExit) as exc: main()` → `exc.value.code == 1`
    - `capsys.readouterr().err` 含 "AZDO_PAT"
  - Test 2 — `test_prints_table`：
    - set 3 env vars via monkeypatch
    - `patch('scripts.sprint.AzureDevOpsAdapter')` 回 mock with `list_sprint_items.return_value = [stub1, stub2]`
    - `patch('sys.argv', ['sprint.py', 'sprint-12'])`
    - 執行 `main()` → capsys stdout 含兩 id + 第一個 title 字串 + 欄位 header（如 "ID"）
  - Test 3 — `test_json_flag_outputs_json_array`：
    - 同上但 argv 加 `--json`
    - stdout 可 `json.loads` 成 list
    - len == 2，第一元素 dict 有 `id` / `title`，**不含** `native` key
  - **完成條件：** `python3 -m pytest tests/test_sprint_cli.py -v` 3 pass

- [x] **Task 4: 全測試無 regression**（2026-04-20 完成，15 passed）
  - `python3 -m pytest tests/ -v`
  - 預期 10 passed
  - **完成條件：** 10 passed, 0 failed

- [x] **Task 5: `SKILL.md` v0.2.0 + Usage 章節**（2026-04-20 完成）
  - frontmatter `version: 0.1.0 → 0.2.0`
  - `status: mvp-in-progress → mvp`
  - 「當前狀態」段加「CLI entrypoint complete」
  - 新增 `## Usage` 章節含：
    - env vars 設定範例（指到 README Prerequisites）
    - `python3 scripts/sprint.py sprint-12` 基本用法
    - `python3 scripts/sprint.py sprint-12 --json | jq ...` pipeline 範例
    - 預期 output 長相（table 示意、去敏值）
  - **完成條件：** SKILL.md 更新完成，肉眼讀順

- [x] **Task 6: End-to-end smoke test**（2026-04-20 完成，the full sprint roster, 670 present）
  - `source ~/.pm-sync.env`（已含 AZDO_*）
  - `cd ~/dev/kc_pm_sync && python3 scripts/sprint.py sprint-12`
  - 預期：table 出現，含 the user #670，可能多筆 Sprint 12 items
  - `python3 scripts/sprint.py sprint-12 --json | python3 -c "import sys, json; print(len(json.load(sys.stdin)))"` 印總筆數
  - **完成條件：** 命令執行成功、output 有 #670、筆數 ≥ 1
  - **⚠️ output 不 commit**（含 acme 資料）；在 report.md 只記去敏摘要（"N items returned, first id=670 state=In Progress"）

## 備註

- Task 間依賴：1 → 2 → 3 → 4 → 5 → 6，不跳
- Task 6 是唯一的 live API call，是整個 MVP 的端到端驗證
- Test 2/3 的 `_make_stub_task` 可以跟 `test_adapter_base.py` 共用 helper 嗎？共用會產生跨 module import 依賴；MVP 簡單複製一份，DRY 拖 future spec
- Task 6 output 含真實公司資料 → 不 commit terminal buffer / 不貼到對話；只報告「成功 + 筆數 + 特定 id 驗證存在」
