# 結案報告：CLI Sprint Entrypoint

> **English summary:** `/pm-sync sprint` MVP shipped. Live smoke test against real Azure DevOps returned 68 work items from Sprint 12, including the user's #670, with a clean state-distribution breakdown. Two real-data bugs caught and fixed during smoke (missing --project flag on `work-item show`, 2-digit fractional seconds breaking Python 3.9 `fromisoformat`).

**Spec:** specs/completed/04-cli-sprint-entrypoint
**Status:** completed
**Date:** 2026-04-20

## 摘要

kc_pm_sync MVP 達成。spec 01-04 全部收口，`python3 scripts/sprint.py sprint-12` 真的能從 Azure DevOps 拉 sprint 資料印出來。

## 方案

見 `plan.md`。重點：
- argparse（stdlib only）
- env var 缺失立刻 exit with helpful message
- stdlib f-string + ljust 排表（無 tabulate / rich dep）
- `--json` 輸出（去 `native`、datetime → ISO string）
- tests 全 mock `scripts.sprint.AzureDevOpsAdapter`

## 改動

| 檔案 | 重點 |
|---|---|
| `scripts/__init__.py`（新） | 空檔，讓 pytest 可 import |
| `scripts/sprint.py`（新，130 行） | argparse + env check + adapter call + table/JSON 輸出 + `sys.path` inject 以支援直跑 |
| `tests/test_sprint_cli.py`（新） | 3 mocked tests（missing env、table、--json） |
| `tests/test_task.py`（修） | 新增 `_normalize_iso` parametrized test 5 case（含 .62 短 fractional 的 regression 防禦） |
| `models/task.py`（修） | 加 `_normalize_iso` helper；`from_azure_payload` 用之取代 inline Z-replace，解決 Python 3.9/3.10 `fromisoformat` 不吃變動 fractional precision 的問題 |
| `adapters/azure_devops.py`（修） | `_az` helper 不再 auto-加 `--project`（`work-item show` 不接受）；`list_sprint_items` 自己加 |
| `SKILL.md` | v0.1.0 → v0.2.0；status `mvp-in-progress → mvp`；新增 `## Usage` 章節含真實範例 |

## 影響分析

- **下游**：MVP 完成 — `/pm-sync sprint` 是終端 user 直接用的 entry，無進一步下游
- **上游**：spec 01 / 02 / 03 全部間接被 exercise；spec 01 的 `_normalize_iso` / spec 03 的 `--project` 拆分都是 smoke test 發現後補強
- **現有測試**：全綠 15 passed（spec 01 × 6 + spec 02 × 3 + spec 03 × 3 + spec 04 × 3）
- **public repo 風險**：smoke test output 未 commit、未貼對話；report 只記去敏摘要

## 三問自審

- **方案正確嗎？** ✅ 對。argparse / stdlib-only / env-first / mock tests 全照 plan；spec 01-03 的抽象剛好撐起 MVP 無改動介面。
- **影響分析全面嗎？** ✅ Smoke test 碰到的兩個坑（az flag 語義、Python 3.9 ISO parse）都補了 regression test，不只修當下。
- **有回歸風險嗎？** ✅ 無。既有 fixture #670 依然通過，新補的 parametrized test 涵蓋原本的 case + 3 個新 case。

## 驗收條件結果

| 驗收條件 | 狀態 |
|---|---|
| AC-1 argparse CLI + positional + --json + --help | PASS |
| AC-2 env var 讀取傳 constructor | PASS |
| AC-3 缺 env → stderr + exit 1 | PASS |
| AC-4 aligned table 輸出 | PASS |
| AC-5 --json 輸出 (去 native + datetime ISO) | PASS |
| AC-6 3 個 mocked tests | PASS |
| AC-7 10+ passed 無 regression | PASS（實際 15 passed，含新補的 `_normalize_iso` 5 個） |
| AC-8 SKILL.md v0.2.0 + Usage 章節 | PASS |
| AC-9 End-to-end smoke test（manual） | PASS（the full sprint roster, 670 present, 狀態分佈合理） |

## Smoke Test 結果（2026-04-20，去敏摘要）

```
✅ Live call succeeded: the full sprint roster
   id range elided
   670 present: True
   states: Approved 6 / Removed 2 / Done 27 / New 2 / To Do 17 / In Progress 14
```

不 commit raw output（含公司資料），只記上述去敏統計。

## 剩餘風險

- **Smoke test 過程發現兩個實作 bug**：
  1. `az boards work-item show` 不吃 `--project`（只 `query` 吃）— `_az` helper 當初設計太一視同仁。已修，但顯示**沒 live test 發現不了 CLI 層語義差異**。未來新 az 子命令要謹慎。
  2. Python 3.9/3.10 `fromisoformat` 對 fractional seconds 位數很嚴格（只接受 3 或 6 位），Azure 實際資料有 2 位（`.62`）、也可能 1 位。已補 `_normalize_iso`。
- **單 sprint test coverage**：只跑過 `sprint-12`。其他 sprint / 多階層 iteration path / 非 Scrum template project 未驗證。
- **Unicode / CJK 在 table 對齊**：MVP 用 `len()`；若 title 含 CJK，視覺會偏移。future spec 補 `east_asian_width` 正確計算。
- **`.env.local` convention 不一致**：(a separate private repo) 的 `.env.local` 只有部分變數有 `export` prefix，`source` 後非 exported var 不會傳給 subprocess。未來整理 juhan env 時對齊。
- **Rate limit / 大 sprint**：the full sprint roster 跑完約 5-6 秒（N+1 query）。若 > 500 items 會痛，補批次 fetch 或 cache。
- **PAT 期限**：PAT 過期時 `az` 會 stderr 噴錯、subprocess raise `CalledProcessError`；CLI 沒特別處理（just 讓 exception 冒出）。體驗可以更好，future spec。

## 關鍵 Commit

| Commit | 說明 |
|---|---|
| _next_ | CLI + tests + SKILL.md + 兩個 smoke-test-driven fixes (models / adapters) |

## 與計畫的偏差

Plan 預估 Task 1-5 共 ~92 分 + Task 6（smoke）~5 分。實際跑：
- Task 1-5 一口氣做完 + 第一次 smoke 撞兩坑修正 ≈ 30 分
- Task 6 第二次 smoke ✅

計畫沒預期 smoke test 會發現 implementation bug（只當成「驗證」），實際上它是**本 spec 的最有價值環節**：靠 mock test 根本發現不了 `az --project` 跟 `fromisoformat` 的真實行為。

## 備註

- **MVP 里程碑**：kc_pm_sync 從 2026-04-19 skeleton → 2026-04-20 可跑 MVP，今天一次 session 內收完 4 個 spec。
- **Mock 測試的極限**：再多 mocked test 都沒辦法撞到 az CLI 語義 + Python ISO parser 邊界。**Smoke test 是 spec 認真的一環，不是附錄。** 這個教訓可以沿用到未來所有外部依賴的 spec。
- **下一步建議**：
  - `05-show-and-push-commands` — 補 `/pm-sync show <id>` 跟 `/pm-sync push <spec-name>`（MVP push 寫 Azure work item）
  - `06-error-handling-polish` — PAT 過期 / 網路失敗 / rate limit 友善訊息
  - Wiki adapter（(a separate private repo) 的 wiki_dump.py 已經實作過一版，可抽出）
