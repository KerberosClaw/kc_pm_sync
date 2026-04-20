# 實作計畫

> **English summary:** Build the UnifiedTask dataclass first, then the Azure payload factory method, validate against one real fixture, and keep everything stdlib + pytest.

## 做法

分三層思考：

1. **資料層（dataclass）**：純宣告 `UnifiedTask` 欄位，不含邏輯。
2. **轉換層（factory）**：`from_azure_payload` classmethod 把 Azure 的巢狀 JSON 攤平到 dataclass 欄位。只處理 Azure，不做多平台分支。
3. **驗證層（test）**：pytest 讀 fixture，過 factory，assert 欄位值。用真實資料驅動，比手刻 mock 準。

實作順序照依賴：先產 fixture（task #1）→ 寫 dataclass（task #2）→ 寫 factory（task #3）→ 寫 test（task #4）→ 跑通（task #5）→ 更 SKILL.md（task #6）。

## 關鍵決策

| 決策 | 選擇 | 理由 |
|------|------|------|
| 欄位容器 | `@dataclass` | stdlib 內建、type hints 天然、`asdict()` 免費、不用引入 pydantic |
| Sprint 識別 | 雙欄位 `sprint_id` + `sprint_native_id` | 短名好讀、原樣可推回平台；對應 2026-04-20 設計討論 |
| Parent 表示 | 只存 `parent_id: int \| None` | MVP 用不到樹狀走訪，YAGNI；未來需要再加方法 |
| 時間欄位 | `datetime`（帶 tzinfo） | Azure 回傳 ISO 8601 UTC，解析後保留 tz 比 naive datetime 安全 |
| raw 存放 | `native: dict` 欄位 | escape hatch，未來查 mapping 漏掉的欄位不用改 schema |
| 不做 Effort | 不加欄位 | Azure 真實資料抽樣顯示 Effort 欄位填寫率為 0（百筆級 active sample）— YAGNI |
| 平台標記 | `platform: str = "azure"` | 預設值，未來 Trello adapter 會覆寫 |
| 測試框架 | pytest | python 社群主流，比 unittest 語法簡潔 |
| Fixture 路徑 | `tests/fixtures/azure/` | 按平台分層，未來加 `tests/fixtures/trello/` 自然擴展 |
| 欄位未出現的處理 | 用 `.get()` 或 try/except，缺 → `None` 或合理預設 | Azure 某些欄位（如 Parent、AssignedTo）未指派時整個 key 不在 payload |

## 風險

| 風險 | 對策 |
|------|------|
| `IterationPath` 格式變動（例如 `AcmeDev\Sprint 12` → `AcmeDev\2026\Q2\Sprint 12`） | `sprint_id` 抽取用「取最後一段 path」邏輯，規則明確寫在 docstring；未來異常 case 補進 fixture 跟測試 |
| `ChangedDate` 時區解析 | 用 `datetime.fromisoformat()`（Python 3.11+ 支援 `Z`）或 `.replace('Z', '+00:00')` 後 parse；測試 assert tzinfo 不是 None |
| 某些 work item type 欄位不一致（Epic 沒有 parent、Task 一定有） | 先只用 Task #670 當 fixture，AC 不要求其他 type 正確；Epic/Feature/PBI 的兼容性後續 spec 處理 |
| Python 版本 | plan.md 記 3.10+，tasks.md 第一步加 `python --version` 檢查；若版本不足先在 task 裡提示升級 |
| fixture 含敏感資訊（assignee email、內部 title） | Task #670 是 the user's own ticket + 內容中性（「run 文件、更新 wiki」），email 就是 `demo_user@acme...`；不算敏感但 commit 前過一眼 |
| 漏掉欄位 mapping | 測試 assert 每個 AC-2 列出的欄位；漏的話 red → 補上 |

## 實作順序

1. **Fixture 產出** — 用 `az boards work-item show --id 670 -o json` 存到 `tests/fixtures/azure/work_item_670.json`。沒這筆資料後面測試沒依據。
2. **Dataclass 定義** — 純 `models/task.py` + `models/__init__.py` export。不含邏輯。先讓 `from models.task import UnifiedTask` 能 import。
3. **Factory method** — `from_azure_payload` 實作。分析 fixture 結構決定 mapping 寫法。
4. **Test 實作** — `tests/test_task.py` + `tests/__init__.py`。讀 fixture → 呼叫 factory → assert 欄位。
5. **跑通** — `pip install pytest`（若沒裝）、`python -m pytest tests/ -v` 綠燈。
6. **SKILL.md 更新** — v0.0.1 → v0.1.0，把 `status: skeleton` 改成 `status: mvp-in-progress`，加一行「schema layer complete」。
