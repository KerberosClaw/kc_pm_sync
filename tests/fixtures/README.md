# Fixtures — 去敏規範

這個資料夾存 PM 平台 API 回傳的**去敏樣本**，供離線單元測試使用。

**repo 是 public，任何提交進 fixtures/ 的資料必須過去敏。**

## 為什麼用 fixture 不用 live API

- Dev / CI 跑測試不需要 PAT、不打網路、不吃 API rate limit
- 不同 contributor clone 下來立刻能跑測試
- 變動 schema 時，固定 fixture 才能比對 before/after 行為
- 真正打 live API 只在「end-to-end smoke test」那一次（scripts/sprint.py 第一次跑）

## 去敏 checklist（每次新增 fixture 前跑一遍）

grep 確認下列**真實字串零出現**（替換為對應 placeholder）：

| 類別 | 取代規則 |
|------|---------|
| 組織名（小寫） | 真實 org slug → `acme`（或自選 generic placeholder） |
| 組織名（camel / title case） | 真實 `XxxDev` → `AcmeDev` |
| 個人 email 前綴 | 真實 user ID → `demo_user` / `user` |
| 個人顯示名 | 真實姓名（中英版本都要）→ `Demo User` |
| Project UUID | → `00000000-0000-0000-0000-000000000001`（可疊號區分不同 project） |
| User identity GUID | → `11111111-1111-1111-1111-111111111111` |
| AAD descriptor | `aad.<base64>` → `aad.REDACTED` |
| 內網 IP / hostname | 移除或改 `10.0.0.1` / `internal.example.com` |
| 客戶 / 專案代號 | 改為字母代號（A、B、C...） |

> **公開 repo 注意：** 這份 README 本身**不要列出真實 org / user 字串**（即使作為「before 範例」）。把實際字串放在你本機的 `.env` / 私人筆記，公開檔只描述 pattern。

## 範例：Azure DevOps Work Item

```
tests/fixtures/azure/
└── work_item_670.json     # Task，包含 Parent + AssignedTo，已去敏
```

未來加 fixture 時命名慣例：
- `work_item_<id>.json` — 單一 work item（`az boards work-item show` 輸出）
- `sprint_<name>_list.json` — sprint 清單（`az boards query` 輸出）
- `wiql_<desc>_result.json` — WIQL 查詢結果

## 工作流程（建新 fixture 時）

1. 本地用真實 PAT 抓 raw：`az boards work-item show --id <id> -o json > /tmp/raw.json`
2. 對照上表去敏（可寫成 script：`scripts/sanitize_fixture.py`，目前手動）
3. 檢視：`grep -iE '<your-real-org>|<your-real-username>' fixture.json` 應零結果（pattern 自填本機真實字串）
4. 進 `tests/fixtures/<platform>/`
5. Commit；pm-sync 的 hook 會擋明顯 secret，但 email / org 名靠這份規範自律

## 絕不進 repo

- 真實 PAT / token
- 含客戶識別資訊的 work item title / description
- 含內網 IP / 實際 endpoint 的 payload
- 未去敏的 raw dump（即使含關鍵測試資料 — 那個留本機用 `*.raw.local.json` 或 gitignore）
