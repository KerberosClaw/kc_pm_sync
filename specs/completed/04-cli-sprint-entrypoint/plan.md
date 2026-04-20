# 實作計畫

> **English summary:** argparse CLI, env-var config check, delegate to AzureDevOpsAdapter, stdlib f-string table. Mock the adapter in tests. Real smoke test at the end.

## 做法

一個 `main()` 函數含：
1. argparse 解析 `sprint_id` + `--json`
2. 讀 3 個 env var；缺 → `sys.exit(1)` with helpful message
3. `adapter = AzureDevOpsAdapter(org_url, project, pat)`
4. `tasks = adapter.list_sprint_items(sprint_id)`
5. Branch on `args.json`：dump JSON vs print table

Table 用 stdlib：算每欄最大寬（含 header）、`ljust` 對齊、title/assignee 超過 max width 就 `...`。

```python
if __name__ == "__main__":
    sys.exit(main())
```

Tests 用 `unittest.mock.patch('scripts.sprint.AzureDevOpsAdapter')` 塞 mock adapter，不碰 subprocess / 真 Azure。

Smoke test 單獨在 spec 結束後手動跑一次，不進 pytest。

## 關鍵決策

| 決策 | 選擇 | 理由 |
|------|------|------|
| CLI 框架 | argparse（stdlib） | Click / Typer 漂亮但多一個 dep；MVP 不值 |
| Module layout | `scripts/sprint.py` 單檔，`main()` + `if __name__` guard | pytest import 要 main() 時乾淨；script 直跑也行 |
| Env 讀取 | 直接 `os.environ.get`，不用 `dotenv` | user 自己 `source .env` 或 `direnv`；dep 為零 |
| 缺 env var 訊息 | stderr 印 `export VAR=...` 範例 + `sys.exit(1)` | exit code 讓 scripting 可偵測；範例讓 user 馬上能修 |
| Table library | 自造 f-string + ljust | tabulate/rich 美但 pip install；MVP 壓 stdlib-only |
| Title / Assignee 截斷 | 60 chars title、30 chars assignee、尾加 `…` | terminal 常規 80-120 寬，留 buffer 給其他欄位 |
| `--json` 輸出格式 | `[{"id": ..., "title": ..., ...}, ...]`，略 `native` | CLI pipeline 用；`native` 太大會吃掉訊號 |
| datetime 序列化 | `dataclasses.asdict` + 後處理把 `changed_at` 轉 ISO string | json 不吃 datetime；asdict 保留欄位名 |
| Exit code | 0 ok、1 env/config 錯、其他讓 exception 冒出（non-zero）| CI / script 友善 |
| 測試 mock target | `scripts.sprint.AzureDevOpsAdapter` | import 在 `scripts/sprint.py`，mock 這個 binding 不影響 adapter 模組 |
| Smoke test fixture | 用 the user's sprint-12 + env.local | PAT validity verified separately in a sibling repo |

## 風險

| 風險 | 對策 |
|------|------|
| `scripts/` 沒 `__init__.py` → pytest import 不到 | 選 A：加 `scripts/__init__.py`；選 B：測試用 `importlib.util.spec_from_file_location` 動態 load。初版走 A，簡單 |
| Terminal 寬度不同，截斷策略可能太窄或太寬 | 固定 width 不自適應；若 user 抱怨再 follow up（shutil.get_terminal_size） |
| Title 含 CJK（寬度 2）計算錯誤 | MVP 用 len()（ASCII 優先），CJK 用戶看起來會微亂；future 要補 `east_asian_width` |
| `dataclasses.asdict` on nested dict `native` 會遞歸展開大物件 | 略掉 `native` key：`{k: v for k, v in asdict(t).items() if k != "native"}` |
| Smoke test 可能揭露真實資料 | 執行時只 report 去敏化摘要（count + first item id）；不 commit output |
| Argparse error message 英文 vs 中文 | argparse 預設英文；CLI 自己的 stderr 訊息可雙語或純中文；MVP 純英文（跟 argparse 一致） |

## 實作順序

1. **`scripts/__init__.py`** — 空檔，讓 pytest 可 import `scripts.sprint`
2. **`scripts/sprint.py`** — main() 函數含 argparse / env check / adapter call / table 或 JSON 輸出
3. **`tests/test_sprint_cli.py`** — 3 個 mocked tests（env missing、table output、JSON output）
4. **`python -m pytest tests/ -v`** — 預期 10 passed
5. **`SKILL.md`** — v0.2.0 + usage 範例
6. **End-to-end smoke test**（manual）：`source ~/.pm-sync.env && python3 scripts/sprint.py sprint-12` → 確認 output 有 #670 + 其他 items、無 error。**不 commit output**，只記 count + id 去敏摘要到 report
