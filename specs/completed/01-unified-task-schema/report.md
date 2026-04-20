# 結案報告：Unified Task Schema

> **English summary:** Platform-neutral `UnifiedTask` dataclass shipped with an Azure DevOps payload factory, a sanitized real-world fixture, and a passing pytest. MVP schema layer for kc_pm_sync is done.

**Spec:** specs/completed/01-unified-task-schema
**Status:** completed
**Date:** 2026-04-20

## 摘要

Task #1 of kc_pm_sync MVP roadmap 完成。`models.task.UnifiedTask` dataclass 就位，可吃 Azure DevOps work item JSON、攤平成平台中立結構、pytest 驗證通過。Schema 層就緒後，Task #2（adapter interface）有共同語言可寫。

## 方案

見 `plan.md` 關鍵決策。核心幾條：
- `@dataclass` 而非 pydantic（stdlib only）
- Sprint 雙 ID（`sprint_id` 短 + `sprint_native_id` 原樣）
- `native: dict` 當 escape hatch
- `from_azure_payload()` 只處理 Azure，不做多平台分支
- 不做 Effort 欄位（Azure 真實填寫率為 0）

## 改動

| 檔案 | 重點 |
|---|---|
| `models/task.py`（新） | `UnifiedTask` dataclass（12 欄位）+ `from_azure_payload()` classmethod。加 `from __future__ import annotations` 讓 `str \| None` 語法在 Python 3.9 可 import |
| `models/__init__.py`（新） | export `UnifiedTask` |
| `tests/__init__.py`（新） | 空檔，讓 tests/ 變 package |
| `tests/test_task.py`（新） | `test_from_azure_payload_work_item_670()` — 讀 fixture → 過 factory → assert 12 欄位值 |
| `tests/fixtures/azure/work_item_670.json`（新） | 去敏後的 Azure Task #670 payload — 組織名 / 個人 email / project UUID / user GUID / aad descriptor 全部替換為 placeholder（規則見 `tests/fixtures/README.md`） |
| `tests/fixtures/README.md`（新） | 去敏規範 + 未來新 fixture 命名慣例 |
| `SKILL.md` | v0.0.1 → v0.1.0；status skeleton → mvp-in-progress；補當前狀態清單（schema ✅ / adapter 🚧 / CLI 🚧） |

## 影響分析

- **下游模組**：尚無（這是第一個 module，下一個是 `adapters/base.py`，會 import `UnifiedTask`）
- **呼叫方**：尚無（factory 還沒被 CLI 叫）
- **測試**：新加一個 pytest test，既有測試無（原本就無）
- **public repo 風險**：fixture 已照 `tests/fixtures/README.md` 規範去敏，grep 真實 org / user 字串零 hit，可安全推 public

## 三問自審

- **方案正確嗎？** ✅ 對。六要素全符合原始需求；Azure 真實欄位都驗證過（source: `an internal Azure DevOps snapshot note`）；沒誤解範圍（沒做 adapter、沒連 live API、沒加 Effort）。
- **影響分析全面嗎？** ✅ 目前無下游，未來 adapter 要 import `UnifiedTask`，屬新增依賴不是修改，無回歸風險。
- **有回歸風險嗎？** ✅ 無。全新 module，無重構既有 code。唯一接觸現存檔案的改動是 `SKILL.md` frontmatter 跟「當前狀態」段，純 metadata。

## 驗收條件結果

| 驗收條件 | 狀態 |
|---|---|
| AC-1: dataclass 含全部欄位 + type hints | PASS |
| AC-2: from_azure_payload 正確 map | PASS |
| AC-3: fixture #670 存在 | PASS |
| AC-4: pytest 通過 | PASS |
| AC-5: 不連網、不依賴外部服務 | PASS |

## 剩餘風險

- **Python 3.9 相容性**：實作用 `from __future__ import annotations` 讓 `str | None` 可在 3.9 import。Type hints 不 runtime evaluate，功能照跑。**但 `dataclasses.fields()` / `get_type_hints()` 等 introspection 在 3.9 會拿到字串 annotation** — 未來若 adapter 或序列化邏輯需 runtime type check，要走 `typing.get_type_hints(...)` 正規路線。
- **ChangedDate 3.9 修復 hack**：手動把 `Z` 替 `+00:00` 再 `fromisoformat`。Python 3.11+ 原生支援 `Z`，code 內保留兼容寫法無負擔，但未來若其他欄位遇到 ISO 8601 也要記得同樣處理。
- **單一 fixture 覆蓋**：只驗 `Task` type + 有 Parent + 有 AssignedTo 這個 path。未測 PBI / Feature / Epic 的格式差異、未測 AssignedTo 缺失 case、未測 Parent 缺失 case。
- **缺 required key 的行為未驗**：code 讓 `KeyError` 自然 raise（fail fast），spec 明列但測試沒 assert。要加的話是 one-liner `pytest.raises(KeyError)`，留 future spec。

## 關鍵 Commit

| Commit | 說明 |
|---|---|
| 45bb4f0 | spec + task 1（fixture captured with sanitization）|
| _next_ | tasks 2-6（dataclass + factory + test + pytest install + SKILL bump）|

## 與計畫的偏差

- **Plan 的實作順序照走無偏差**（1→2→3→4→5→6）。
- **Python 版本 fallback**：plan.md 的 Risks 有提到 Python 版本風險，當時對策是「task 裡加 `python --version` 檢查；版本不足先提示」。實際上發現 3.9 時沒中止 — 因為 spec 已明列 `from __future__ import annotations` 可選作為 compat 手段，剛好套用即可。符合 spec 授權範圍。
- **一次跑完 vs 碎片**：plan.md 建議每晚一 task。user 今天 session 內一口氣跑完，實際時間 ~30 分鐘（比預估 2.5h 快）。

## 備註

- 本 spec 是 kc_pm_sync 落地的第一個實作 module，確立了 adapter pattern 之前的「共同語言」。
- 去敏規範（`tests/fixtures/README.md`）是 public repo 吸收公司資料進測試的關鍵守則。未來新 fixture 都走這個檔的 checklist。
- 下一 spec 建議：`02-adapter-base-interface` 定義 `PMAdapter` abstract class + `list_sprint_items()` / `get_item()` 契約，之後 `03-azure-devops-adapter` 實作，`04-cli-sprint-entrypoint` 接起來就是 MVP `/pm-sync sprint` 可跑。
