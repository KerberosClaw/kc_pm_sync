# 實作計畫

> **English summary:** Write a thin ABC in `adapters/base.py`, export it, and cover it with three ABC-semantics tests. Zero runtime deps beyond stdlib and spec 01.

## 做法

三個檔案、一個 ABC、三個測試。結束。

- `adapters/base.py` — `PMAdapter(ABC)` + 2 個 `@abstractmethod`。契約全寫 docstring。
- `adapters/__init__.py` — re-export `PMAdapter`，跟 `models/__init__.py` 對稱。
- `tests/test_adapter_base.py` — 用一個 `IncompletePMAdapter`（只實作 1 方法）+ 一個 `DummyPMAdapter`（兩方法都實作、回 stub）驗證 ABC 語義。

## 關鍵決策

| 決策 | 選擇 | 理由 |
|------|------|------|
| ABC 還是 Protocol | `abc.ABC` + `abstractmethod` | runtime enforcement（實例化時會檢查），比 `typing.Protocol` 的 structural typing 明確；錯誤發生點近，stack trace 清楚 |
| Constructor 定不定 | **不定義** | 平台認證參數差異大（Azure 3 個、Trello 3 個但不同），base 若定了 `__init__` 會被每個子類覆寫，白忙 |
| Sprint id 解析放哪 | Adapter 內部 | base 只定契約（docstring），不加 helper；避免為了「共通」而過早抽象 |
| 錯誤處理 | 無自訂 exception | MVP 讓 platform native exception（`requests.HTTPError`、`KeyError`）冒出；統一錯誤類別留 future spec |
| 方法數量 | 只 2 個（list_sprint_items、get_item） | 剛好 cover `/pm-sync sprint` + `/pm-sync show` 兩個 MVP 指令。push / update / search 全留 future spec |
| `list_sprint_items` 回傳 | `list[UnifiedTask]`（非 iterator/generator） | MVP 資料量小（< 100 筆/sprint），list 簡單好 debug、好 assert |
| Type hints | 用 `list[UnifiedTask]`（PEP 585 新語法） | 配合 `from __future__ import annotations`，3.9 也能 import |

## 風險

| 風險 | 對策 |
|------|------|
| AC-5 regression 風險：新增 `adapters/__init__.py` 有可能不小心影響 `models/__init__.py` 的 import 路徑 | 執行時 pytest 會抓到；本來就是同一次測試跑全部，regression 直接 red |
| 未來真的要加 `push_item` 時，所有 adapter 都要補實作否則 runtime 失敗 | ABC 的天性就是這樣，加抽象方法要同步升級所有子類；MVP 只有 Azure 一個 adapter，屆時升級成本低 |
| `list_sprint_items` 大量資料時 list 吃記憶體 | MVP 範圍都在百筆級別；真變大再改 iterator，屆時介面演進自然有修改動機 |
| `sprint_id` 契約太鬆（MAY 一堆），adapter 間行為不一致 | 初版接受鬆散；若 CLI 端有困擾再收緊（例如強制所有 adapter 支援 macro） |
| Test 3 裡的 `DummyPMAdapter` 需要回傳合法 `UnifiedTask` | 用 dataclass 直接 instantiate（所有必填欄位）；不用 fixture / from_azure_payload |

## 實作順序

1. **`adapters/base.py`** — ABC 本體。先把 class 跟 2 個方法骨架寫出來，docstring 寫滿契約。不實作任何邏輯。
2. **`adapters/__init__.py`** — re-export + `__all__`。1 分鐘。
3. **`tests/test_adapter_base.py`** — 3 個測試。
   - Test 1 最簡單：`pytest.raises(TypeError): PMAdapter()`
   - Test 2：寫 `class Incomplete(PMAdapter): def list_sprint_items(...)` 但不實作 `get_item`；`pytest.raises(TypeError): Incomplete()`
   - Test 3：寫 `class Dummy(PMAdapter)` 兩方法都實作回 stub，assert 實例化成功、兩方法都可 call 且回預期值
4. **執行 `python -m pytest tests/ -v`** — spec 01 + 02 測試全綠（4 個 test 全 pass）
