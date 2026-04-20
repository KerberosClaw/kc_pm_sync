# 結案報告：Azure DevOps Adapter

> **English summary:** `AzureDevOpsAdapter` ships: shells out to `az` CLI, parses JSON through `UnifiedTask.from_azure_payload()`, runtime-checks prerequisites, and ships with README Prerequisites section. All seven tests green (mocked, no live API).

**Spec:** specs/completed/03-azure-devops-adapter
**Status:** completed
**Date:** 2026-04-20

## 摘要

Task #3 of kc_pm_sync MVP roadmap 完成。kc_pm_sync 有第一個**可實際抓資料**的 adapter。CLI（spec 04）接上去後 `/pm-sync sprint` 可跑。

## 方案

見 `plan.md`。核心：
- subprocess call `az` CLI（`boards query` + `boards work-item show`）
- PAT 走 `AZURE_DEVOPS_EXT_PAT` env var，**不進 argv**
- sprint_id 轉換：短形式 hard-code 成 `f"{project}\\Sprint {n}"`；含 `\\` 當 native
- N+1 fetch 策略（MVP < 200 筆無感）
- 測試全 mock subprocess，不打 live API
- README 加 Prerequisites 章節（讓新 user 有地方看）

## 改動

| 檔案 | 重點 |
|---|---|
| `adapters/azure_devops.py`（新） | `AzureDevOpsAdapter` class，88 行含 docstring。`__init__` runtime check、`_az` helper、`_sprint_id_to_native` 轉換、`get_item` / `list_sprint_items` 兩方法實作 |
| `tests/test_azure_adapter.py`（新） | 3 mocked tests：missing az、get_item mapping、list_sprint_items 兩階段 call。驗證 PAT 不洩 argv |
| `README.md` | 加 Prerequisites 章節（az 裝設 + env vars + PAT scope + 未來 adapter 提示）；更新「當前狀態」三個 spec 進度 |

## 影響分析

- **下游**：尚無；spec 04 CLI 會 `from adapters.azure_devops import AzureDevOpsAdapter` 並 inject env vars
- **上游**：靠 spec 01（UnifiedTask）+ spec 02（PMAdapter）；ABC 契約符合，subprocess shape 跟 spec 01 fixture 一致
- **現有測試**：spec 01/02 測試完全不動（4 個仍綠）
- **public repo 風險**：adapter code 無敏感資訊；README 範例用 `{your-org}` / `{your-project}` placeholder；測試用 `acme` / `AcmeDev` 已去敏字串

## 三問自審

- **方案正確嗎？** ✅ 對。subprocess + az CLI 是 user 明確認可的路線（取代我原本誤推的 urllib）；契約符合 spec 02；復用 spec 01 factory。
- **影響分析全面嗎？** ✅ 新增檔案為主，README 修改 surgical（只動「當前狀態」+ 插入新章節），無動既有段落。
- **有回歸風險嗎？** ✅ 無。全新 adapter module，其他 code 沒呼叫過 `AzureDevOpsAdapter`。全 7 測試綠含 spec 01/02 既有。

## 驗收條件結果

| 驗收條件 | 狀態 |
|---|---|
| AC-1: class + 兩方法 + 三屬性 | PASS |
| AC-2: runtime check + 三平台指引 | PASS |
| AC-3: list_sprint_items WIQL + per-id fetch | PASS |
| AC-4: get_item show → factory | PASS |
| AC-5: `_az` 集中（flag + PAT env + check=True） | PASS |
| AC-6: 3 mocked tests pass | PASS |
| AC-7: README Prerequisites 章節 | PASS |
| AC-8: 全測試無 regression（7 passed） | PASS |

## 剩餘風險

- **Sprint id 轉換 hard-code 簡單版**：只支援 `{project}\\Sprint N` pattern。實際 org 若 iteration 命名是 `2026\\Q2\\Sprint 12` 之類多階層 → MVP 直接傳 native 字串走 bypass（含 `\\` 的都當 native），暫解；長遠要補 fixture + 更通用解析
- **N+1 query**：100 item sprint 約 10s。真正大 sprint 或 rate limit 卡到再改批次 `_apis/wit/workitemsbatch`
- **WIQL 字串拼接**：`native` 插入 `WHERE [System.IterationPath] = '{native}'`。若 project/iteration 名含 `'` 會破查詢（現實罕見但不是零）。MVP 未 escape；future spec 收緊
- **無 retry / rate limit handling**：`az` 本身有基本 retry，不處理 429 的 back-off。MVP 個人使用量低，不補
- **未驗證 PBI / Feature / Epic type 的 fixture**：現有測試只涵蓋 Task type 的 fixture。理論上 `from_azure_payload()` 通用（只讀 `System.*` 欄位），但未經真實驗證。端到端 smoke test（spec 04）會第一次撞到
- **`az extension` 需要使用者手動首次安裝**：adapter code 不自動裝（會觸發 user prompt，非互動環境會卡）；靠 README 說明 + 首次 call 時 az 自己會提示

## 關鍵 Commit

| Commit | 說明 |
|---|---|
| _next_ | AzureDevOpsAdapter + tests + README Prerequisites |

## 與計畫的偏差

無。plan.md 的 5 步實作順序照跑，測試一次綠燈。唯一一點：plan.md 的 side_effect mock 預期 WIQL 回傳值含 `fields` dict（仿照 `az boards query` 真實格式），實作時發現只要有 `id` key 就夠（list_sprint_items 只 `row["id"]`），測試跟著簡化。

## 備註

- **PAT 不洩漏 argv 設計**：測試 `test_get_item_maps_azure_payload` 有明確 assert `"pat" not in " ".join(argv)` — 這是 security 的 one-liner 檢查，值得之後其他 adapter 都抄
- **子進程 subprocess vs stdlib urllib 的選擇**：user 在 spec 03 開工前直接挑戰我的 urllib 方案。對的挑戰 — smoke test 已證明 az 可用，urllib 是過度工程。決策 transparency 教訓記在心
- **下一 spec**：`04-cli-sprint-entrypoint` — `scripts/sprint.py` 讀 `AZDO_*` env vars → 實例化 `AzureDevOpsAdapter` → 呼叫 `list_sprint_items(...)` → 以 table / Rich 格式印 work items。完成後 MVP 跑得動，才是真正「能抓下來看」的里程碑
