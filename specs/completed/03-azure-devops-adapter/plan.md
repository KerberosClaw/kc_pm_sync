# 實作計畫

> **English summary:** Wrap `az` CLI calls in a PMAdapter subclass, mock `subprocess.run` in tests, update README with Prerequisites. Zero live API during dev.

## 做法

核心就一個 private helper `_az(*args) -> dict`：拼 `az ... --organization --project -o json`，塞 PAT 進 env，`subprocess.run` 回 JSON。其他兩個方法都 delegate 到它。

`__init__` 做 `shutil.which("az")` 檢查；否則實例化當下就 fail-fast。

Sprint id 短→native 用字串拼接：`"sprint-12"` → `f"{project}\\Sprint 12"`。初版不處理多階層 iteration（如 `AcmeDev\\2026\\Sprint 12`），遇到再補。

Tests 全靠 `unittest.mock.patch('subprocess.run')` 塞假回傳值；fixture 重用 spec 01 的 `work_item_670.json`。

README 加 Prerequisites 章節是純文件改動，擺在最前面（Skills 列表之前）。

## 關鍵決策

| 決策 | 選擇 | 理由 |
|------|------|------|
| 呼叫 Azure 方式 | subprocess + `az` CLI | smoke test 驗證過；auth/retry/error mapping 由 az 負責；不用自寫 HTTP 層 |
| PAT 傳遞 | env var `AZURE_DEVOPS_EXT_PAT` | 官方 az extension 認可；不放命令列避免 process list 洩露 |
| `--organization` / `--project` | 每次 call 都加 | 顯式比依賴 `az devops configure` 的全域狀態可靠 |
| `list_sprint_items` 實作 | WIQL 拿 id + N+1 fetch | 簡單、直接；MVP < 200 筆無感；未來慢再改批次 |
| Sprint id 轉換 | 字串拼接 hard-code | 初版只支援 `{project}\\Sprint N`；多階層等實際遇到再補 |
| Sprint native 形式也接受 | 檢查 `"\\" in sprint_id` → 當 native 用 | Base 契約允許 MAY，實作順便支援 |
| `@current` macro 支援 | **不支援**（初版） | WIQL `@CurrentIteration` 要 team 參數，複雜度不值；future spec 補 |
| 錯誤處理 | 讓 `subprocess.CalledProcessError` 自然冒出 | fail loud，MVP 不包自訂 exception |
| 測試 isolation | `patch('subprocess.run')` + `side_effect` list | 逐次 call 回不同 mock data，mock WIQL + 多次 show |
| Fixture 重用 | 指向 `tests/fixtures/azure/work_item_670.json` | 已去敏、已通過 spec 01 測試，一致性高 |
| README Prerequisites 位置 | 放在 `## Current Status` 之後、`## MVP` 之前 | User 看完當前狀態就會想裝，自然接上 |

## 風險

| 風險 | 對策 |
|------|------|
| Sprint id 轉換規則太簡單（多階層 iteration path） | 初版 `f"{project}\\Sprint {n}"` hard-code；若輸入已含 `\\` 當 native 用，繞過轉換；未來 fixture 補進再修 |
| `az boards query` 回傳 shape 跟 `show` 不同（`query` 只給 id + 基本欄位） | `list_sprint_items` 只從 query 拿 id，再用 `show` 拿完整資料 — schema 穩 |
| mock subprocess 側寫不完整（漏 env / args assertion） | 測試加 `mock.call_args_list` 驗證 call argv + env 內含 PAT，避免生產 code 偷走 PAT |
| `az` CLI 版本差異（舊版無 `-o json` 等） | Prerequisites 寫 `az` 2.50+；runtime 暫不檢查版本（過度工程） |
| README 更新誤 break 其他段落（table / code fence） | 用 Edit tool 加章節，不 rewrite 整檔；commit 前肉眼過一遍 |
| WIQL 注入風險（`sprint_id` 插入 SQL-like 字串） | MVP 只對字串做 native 轉換，不接受任意 user input；CLI（spec 04）會限制輸入格式。真要 defense-in-depth → escape `'` → `''`，一行事 |
| N+1 慢 | MVP 百筆級別可接受；若 >500 就優化 |

## 實作順序

1. **`adapters/azure_devops.py`** — 寫 class 骨架：`__init__` + runtime check + `_az` helper + `get_item` + `list_sprint_items` + sprint_id 轉換 helper。~50-60 行含 docstring。
2. **`tests/test_azure_adapter.py`** — 3 個測試：
   - `test_init_raises_when_az_missing`：`patch('adapters.azure_devops.shutil.which')` 回 None → `RuntimeError`
   - `test_get_item_maps_azure_payload`：`patch('subprocess.run')` 回 fixture JSON → assert `UnifiedTask` 欄位
   - `test_list_sprint_items_calls_wiql_then_fetches_each`：`side_effect` = [wiql_result, show_result_1, show_result_2] → assert 長度 + 每個元素型別 + subprocess.run call 次數
3. **跑 pytest** — `python -m pytest tests/ -v`，預期 7 passed（spec 01 + spec 02 + spec 03）
4. **`README.md`** — Edit 加 Prerequisites 章節（az CLI 安裝 + env vars + PAT scope + 未來其他 adapter 提醒）
5. **再跑 pytest 確認 regression** — 文件改動不該影響測試，但照規矩跑一次

## 測試 fixture 補充

`list_sprint_items` 測試需要一個「WIQL query 回 id list」的假回傳。格式參考 `az boards query --wiql ... -o json`：

```json
[
  {"id": 670, "fields": {"System.Id": 670, "System.Title": "..."}},
  {"id": 671, "fields": {"System.Id": 671, "System.Title": "..."}}
]
```

這個不用存 fixture 檔（inline 在測試裡即可），因為 structure 很小、不需持久。`show` 的 fixture 已存在（`work_item_670.json`）重複用。
