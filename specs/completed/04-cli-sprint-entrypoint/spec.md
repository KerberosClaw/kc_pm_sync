# CLI Sprint Entrypoint

> **English summary:** `scripts/sprint.py` — argparse-based CLI that reads `AZDO_*` env vars, instantiates `AzureDevOpsAdapter`, calls `list_sprint_items`, and prints a readable table (or JSON). Completes the MVP loop: `python3 scripts/sprint.py sprint-12` actually fetches and shows real data.

## 六要素摘要（Task Prompt Schema）

- **目標（Goal）：** 把 spec 01-03 串起來變成可跑的 `/pm-sync sprint` MVP — user 執行一個命令就能看到 sprint 進度 table。
- **範圍（Scope）：**
  - `scripts/sprint.py`（新增）
  - `tests/test_sprint_cli.py`（新增）
  - `SKILL.md`（修改，v0.1.0 → v0.2.0，加 usage example）
- **輸入（Inputs）：**
  - `adapters.azure_devops.AzureDevOpsAdapter`（spec 03）
  - `models.task.UnifiedTask`（spec 01）
  - env vars：`AZDO_ORG_URL`、`AZDO_PROJECT`、`AZDO_PAT`
  - CLI argv：`sprint_id`（positional）+ `--json` flag（optional）
- **輸出（Outputs）：**
  - stdout：aligned table（預設）或 JSON array（`--json`）
  - exit code 0 成功、1 config error（env 缺）、sub-error 讓 exception 冒出
  - 3 個 mocked tests + 1 個 end-to-end smoke test 結果記錄（manual AC）
- **驗收（Acceptance）：** 見 AC-1~9
- **邊界（Boundaries）：** 不做互動式 prompt、不做 default sprint resolution（`@current`）、不做 colored output、不做 sprint 比較 / summary

## 背景

Spec 01-03 已完成但**沒有入口**：跑不起來，user 無法實際用。本 spec 把三層兜起來，產生第一個可操作的 MVP 命令。

完成後這個命令第一次可以對 live Azure DevOps 跑，是整條 pipeline 的端到端驗證 —— schema → factory → adapter → CLI → 表格。所有過去兩個月討論的東西第一次「真的動」。

## 驗收條件

- [ ] **AC-1**：`scripts/sprint.py` 可直接執行（`python3 scripts/sprint.py <sprint_id>`），用 argparse 解析 positional `sprint_id` + optional `--json` flag + `--help` 自動產生
- [ ] **AC-2**：從 env 讀 `AZDO_ORG_URL` / `AZDO_PROJECT` / `AZDO_PAT`，傳給 `AzureDevOpsAdapter` constructor
- [ ] **AC-3**：任一 env var 缺失 → 印到 stderr 清楚指出**哪個**缺 + 怎麼補（export 範例）+ `sys.exit(1)`
- [ ] **AC-4**：預設輸出 aligned table，欄位：`ID` / `Type` / `State` / `Title`（truncated to ~60 chars）/ `Assignee`（truncated）/ `Parent`
- [ ] **AC-5**：`--json` flag：印 JSON array，每個元素是 UnifiedTask 的 dict 表示（用 `dataclasses.asdict` + `datetime` 轉 ISO string + 略去 `native` 欄位避免雜訊 —— 除非加 `--verbose`，簡化：MVP 一律省略 `native`）
- [ ] **AC-6**：`tests/test_sprint_cli.py` 三個 mocked test：
  - `test_exits_when_env_missing` — 清空 `AZDO_PAT` → stderr 含變數名 → exit code 1
  - `test_prints_table` — mock `AzureDevOpsAdapter` 回兩個 stub task → stdout 含兩 id + Title 字串 + 欄位 header
  - `test_json_flag_outputs_json_array` — mock adapter → `--json` → stdout 可 json.loads 成 list of dict，每個 dict 有 `id` / `title` / 不含 `native`
- [ ] **AC-7**：跑 `python -m pytest tests/ -v` 10 passed 全綠（spec 01 × 1 + 02 × 3 + 03 × 3 + 04 × 3）
- [ ] **AC-8**：`SKILL.md` 更新：`version: 0.1.0 → 0.2.0`；status `mvp-in-progress → mvp`；加「當前狀態」勾選 CLI 完成；加一個 `## Usage` 章節含真實範例 command
- [ ] **AC-9**（manual / end-to-end smoke test）：用 `source ~/.pm-sync.env && python3 scripts/sprint.py sprint-12` 跑**真實**的 Azure DevOps，output 含 the user's #670 + 該 sprint 其他 items，無 error。結果**不 commit**（含 acme 資料），在 report.md 摘要「N 筆 items，第一筆 id=670 state=In Progress」這種去敏化敘述

## 不做的事

- **不做互動 prompt**（無 `input()`）；env 缺就 exit，不臨時問
- **不做 default sprint resolution**（沒有 `@current`、沒有 auto-detect）；user 必須明確給 sprint_id
- **不做 colored output**（terminal escape codes 在 CI / pipe 會亂；MVP 純文字）
- **不做進階 flag**：`--filter-state`、`--by-assignee`、`--blocked-only` 等 future spec
- **不做 summary stat**（總點數、完成率）：無 Effort 欄位（spec 01 決策），無此可能
- **不做 `show` / `push` 命令**：只做 `sprint`；其他 future spec
- **不做 `python -m pm_sync ...`  / 安裝成 `kc-pm-sync` 套件**：CLI 純 script，`python3 scripts/sprint.py` 直接跑
- **不用 Rich / tabulate 等第三方**：stdlib only（argparse + f-string ljust）
- **不寫 bash wrapper / alias**：user 自己建 alias / function

## 依賴

- **Spec 03（03-azure-devops-adapter）**：`AzureDevOpsAdapter` 必須存在
- **Spec 02 / 01**：透過 spec 03 間接依賴
- **Python**：3.9+（sys, os, argparse, json, dataclasses, datetime — 全 stdlib）
- **Runtime env vars**：`AZDO_ORG_URL`、`AZDO_PROJECT`、`AZDO_PAT`（測試 mock，smoke test 真用）
- **`az` CLI**：由 spec 03 runtime check（測試 mock，smoke test 真用）
