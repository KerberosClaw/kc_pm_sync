# 結案報告：PMAdapter 抽象介面

> **English summary:** Thin ABC defining the read-only MVP contract (`list_sprint_items`, `get_item`) is in place. Three ABC-semantic tests pass alongside spec 01 — total 4/4 green with zero regression.

**Spec:** specs/completed/02-adapter-base-interface
**Status:** completed
**Date:** 2026-04-20

## 摘要

Task #2 of kc_pm_sync MVP roadmap 完成。`adapters.base.PMAdapter` ABC 就位，定義 2 個 `@abstractmethod` + sprint_id 契約 docstring。Azure 實作（spec 03）跟 CLI（spec 04）有穩定的撞牆對象。

## 方案

見 `plan.md`。重點：
- 用 `abc.ABC` + `@abstractmethod` 做 runtime-enforced 介面
- Constructor 不定義（平台差異大）
- 只 2 個方法涵蓋 MVP 兩個 CLI 指令
- 契約寫 docstring，不加 util helper
- 無自訂 exception（讓 platform native 冒出）

## 改動

| 檔案 | 重點 |
|---|---|
| `adapters/base.py`（新） | `PMAdapter(ABC)` + `list_sprint_items` + `get_item`，完整 docstring 含 sprint_id 短/native/macro 契約 |
| `adapters/__init__.py`（新） | export `PMAdapter` |
| `tests/test_adapter_base.py`（新） | 3 個測試：不能實例化 ABC、不完整子類 raise、完整子類可用 |

## 影響分析

- **下游模組**：尚無 — spec 03（Azure adapter）會 `from adapters.base import PMAdapter` 並繼承；CLI（spec 04）會 type-hint `adapter: PMAdapter`
- **呼叫方**：目前無，僅測試 call
- **現有測試**：`tests/test_task.py` 不受影響，spec 01 測試 regression 確認綠燈
- **public repo 風險**：無敏感資訊、純 ABC 宣告

## 三問自審

- **方案正確嗎？** ✅ 對。ABC 是業界 adapter pattern 標準；2 方法精準對應 MVP 需求；沒做過度抽象（沒加 unused method、沒定 `__init__`）。
- **影響分析全面嗎？** ✅ 尚無下游，唯一影響是 `adapters/__init__.py` 開始存在 — `models/__init__.py` 路徑獨立，無衝突（regression test 確認）。
- **有回歸風險嗎？** ✅ 無。新增檔案，無修改既有 code。pytest 全綠包含 spec 01 的 `test_from_azure_payload_work_item_670`。

## 驗收條件結果

| 驗收條件 | 狀態 |
|---|---|
| AC-1: ABC + 2 abstractmethods + type hints | PASS |
| AC-2: sprint_id 契約 docstring | PASS |
| AC-3: `__init__.py` export | PASS |
| AC-4: 3 個 test pass | PASS |
| AC-5: 全測試無 regression（4 passed） | PASS |
| AC-6: 不連網、不 live SDK | PASS |

## 剩餘風險

- **無自訂 exception**：初版讓 `requests.HTTPError` / `KeyError` 等原生例外冒出。CLI 或下游若要做 graceful degradation，會得處理多種 exception 類別。未來若要統一 → spec 加 `PMAdapterError`（類似 `ValueError` 家族）。
- **Sprint id 契約「MAY」太鬆**：adapter 間支援的 macro 集合不一致時 CLI 難做通用 UX。若之後 CLI 端需要「所有 adapter 都支援 `@current`」，要收緊為 MUST — 屆時 breaking change（需重訪 adapter 實作）。
- **`list_sprint_items` 回 list 不回 iterator**：MVP 百筆級別沒問題；單 sprint > 1000 items 會吃記憶體，但那是遠期考量。
- **沒加 `__repr__` / `__str__`**：debug 時 `PMAdapter` 子類 instance print 出來是 `<Dummy object at 0x...>`，不夠友善；真的礙事再補（一行事）。

## 關鍵 Commit

| Commit | 說明 |
|---|---|
| _next_ | PMAdapter ABC + 3 tests + adapters/__init__.py export |

## 與計畫的偏差

無。plan.md 的 4 步實作順序照跑，測試一次綠燈。時間比預估（~45 分鐘）更短（實際 ~10 分鐘），因為 ABC 本身邏輯簡單、stub 測試無邊界條件要煩惱。

## 備註

- 這個 spec 是最小可行的「介面決策」spec：code 只 ~60 行（含 docstring），測試 ~50 行，但它決定 kc_pm_sync 未來所有 adapter 都要長成什麼樣。ROI 高在於「避免未來改壞 3 個 adapter」。
- Python `abc` 的小 trivia：`ABCMeta.__call__` 檢查 `__abstractmethods__` set；子類若沒實作完就 instantiate，Python 自動 raise `TypeError: Can't instantiate abstract class X with abstract methods ...`。這是 runtime enforcement 的核心機制。
- 下一 spec 建議：`03-azure-devops-adapter` — 實作 `AzureDevOpsAdapter(PMAdapter)`，用 `az` CLI 或直接 `urllib.request` 打 REST API（推後者，0 subprocess overhead）。MVP 只實作兩個 abstract method。完成後 spec 04 CLI 接起來就能跑 `/pm-sync sprint`。
