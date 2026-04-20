# PM Sync — Sprint 進度看 terminal 就好，不用開 17 個瀏覽器分頁

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)

[English](README.md)

> 把遠端 PM 平台的 sprint work items 拉到 terminal。
> 目前支援 Azure DevOps，roadmap 有 Redmine / Jira / GitHub Issues（= 「之後再說啦」）。
> 輸出乾淨的 table 或 pipeline 友善的 JSON。

## 它做什麼

一個指令、一個平台中立 schema、零個瀏覽器 tab：

```bash
sprint sprint-12              # table
sprint sprint-12 --json | jq  # 接 pipeline
```

為什麼有這個東西：每次想看 sprint 進度都要重整 Azure DevOps 網頁 board，點到天荒地老。現在 terminal 打 `sprint sprint-12` 就直接吐出來，同樣的資料，100 倍少的滑鼠點擊。

## 狀態

**MVP 已 ship。** 真的能動的部分：
- ✅ 列 sprint work items（Azure DevOps adapter 走 `az` CLI）
- ✅ Table + JSON 輸出
- ✅ Adapter pattern + `PM_SYNC_PLATFORM` env var → 其他平台之後可以乾淨擴充而不會壞掉現有的

還沒能動的部分（也叫 roadmap，也叫嘴砲清單）見 [`docs/USAGE.md`](docs/USAGE.md) §6。劇透：`show <id>` 一個週末就能補；`push` 要好幾個週末；Wiki adapter 目前只存在於概念中。

## Prerequisites

Azure DevOps adapter（目前的預設，也是目前唯一）需要：

1. **`az` CLI** 2.50+ — macOS 用 `brew install azure-cli`；其他 OS 見 [`docs/USAGE.md`](docs/USAGE.md) §1
2. **Personal Access Token** scope 勾 `Work Items (Read)` — 讀 sprint 最低需求
3. **三個環境變數：**
   ```bash
   export AZDO_ORG_URL="https://dev.azure.com/your-org"
   export AZDO_PROJECT="YourProject"
   export AZDO_PAT="..."
   ```

想再也不用手打這些？設好 `~/.pm-sync.env` + alias pattern — [`docs/USAGE.md`](docs/USAGE.md) §1。

## Quick Start

```bash
git clone https://github.com/KerberosClaw/kc_pm_sync.git ~/dev/kc_pm_sync
cd ~/dev/kc_pm_sync

# （Prerequisites 設好之後）
python3 scripts/sprint.py --help                # sanity check
python3 scripts/sprint.py sprint-12             # 拉你的第一個 sprint
```

如果 `sprint-12` 回 `(no items)` 但你明明知道 sprint 有東西 — 你的 iteration path 命名八成不是 `Project\Sprint 12`。歡迎來到「每個 Azure DevOps project 自己 iteration 怎麼命名都行」的地獄。看 [`docs/USAGE.md`](docs/USAGE.md) §2 — 裡面有一行指令幫你找真實的 iteration path，還有一個永遠 work 的 fallback 寫法。

## Security Notice

- **PAT 絕不上命令列。** 透過 `AZURE_DEVOPS_EXT_PAT` env var 注入 `az` subprocess（不會出現在 `ps` 或 shell history）。
- **PAT 推薦儲存位置：** `~/.pm-sync.env` + `chmod 600`，用 alias source 進來。絕不 commit。
- **測試 fixture 已去敏**（組織名 / 個人 / GUID 全替換為 placeholder），規範見 [`tests/fixtures/README.md`](tests/fixtures/README.md)。Fixture 目錄安全可公開檢視。
- **預設 read-only。** 當前 MVP 只有讀路徑。未來寫路徑會強制 `--confirm` flag 跟 draft preview gate。

## 文件

| 文件 | 內容 |
|---|---|
| [`docs/USAGE.md`](docs/USAGE.md) | 完整 CLI 用法、sprint_id 格式、troubleshooting、roadmap |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | 四層架構設計、加新 adapter 步驟（Redmine 範例） |
| [`SKILL.md`](SKILL.md) | Claude Code skill manifest — 把 repo symlink 進 `~/.claude/skills/` 後可在 Claude Code 用 `/pm-sync` |
| [`specs/completed/`](specs/completed/) | Spec-driven 開發歷程（01: schema, 02: ABC, 03: Azure adapter, 04: CLI）。部分 spec 已被後續 refactor 取代 — 見 banner。 |

## License

MIT — 見 [LICENSE](LICENSE)。
