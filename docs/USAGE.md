# Usage

> **English summary:** Detailed usage guide for `pm-sync`. Covers full Prerequisites, the sprint_id format pitfall, all CLI flags, common pipelines, and Troubleshooting.

完整 CLI 使用手冊。如果你只想快速跑起來，先看 README.md 的 Quick Start；以下是「裝完之後」想做進階操作的詳細參考。

## 1. Prerequisites（完整版）

### 1.1 裝 `az` CLI（Azure DevOps adapter 需要）

| OS | 指令 |
|---|---|
| macOS | `brew install azure-cli` |
| Linux (Debian/Ubuntu) | `curl -sL https://aka.ms/InstallAzureCLIDeb \| sudo bash` |
| Linux (其他) | [MS 官方安裝指引](https://learn.microsoft.com/cli/azure/install-azure-cli-linux) |
| Windows | [MS 官方 installer](https://learn.microsoft.com/cli/azure/install-azure-cli-windows) |

需要 `az` 2.50+。第一次用 `az boards` 系列指令時會提示安裝 `azure-devops` extension，照提示裝；或手動：

```bash
az extension add --name azure-devops
```

### 1.2 PAT（Personal Access Token）

到 Azure DevOps web UI → User Settings → Personal access tokens → New Token。

**Scope 最低需求：** `Work Items (Read)` — 跑 `sprint` 命令夠用。

未來支援 push / wiki sync 後會需要更多 scope，屆時再加。

### 1.3 環境變數

需要三個：

```bash
export AZDO_ORG_URL="https://dev.azure.com/your-org"
export AZDO_PROJECT="YourProject"
export AZDO_PAT="your-pat-token"
```

**推薦做法：** 存到 `~/.pm-sync.env` + chmod 600 + 用 alias source 進去。範例：

```bash
# ~/.pm-sync.env
export AZDO_ORG_URL="https://dev.azure.com/your-org"
export AZDO_PROJECT="YourProject"
export AZDO_PAT="your-pat-token"
```

```bash
chmod 600 ~/.pm-sync.env
```

```bash
# ~/.zshrc
alias sprint='source ~/.pm-sync.env && python3 ~/dev/kc_pm_sync/scripts/sprint.py'
```

之後 terminal 直接 `sprint sprint-12` 就跑。

---

## 2. Sprint ID 格式（最常見的踩雷點）

`sprint <sprint_id>` 接受兩種格式：

### 短形式（推薦，假設你的 iteration path 命名規律）

```bash
sprint sprint-12
```

內部展開為 `{AZDO_PROJECT}\Sprint 12`。**只在 iteration path 命名為 `Project\Sprint N` 的 project 工作。**

### Native 形式（fallback，總是 work）

```bash
sprint 'YourProject\Iteration 12'
sprint 'YourProject\2026\Q2\Sprint 12'
sprint 'YourProject\TeamA\Sprint 12'
```

任何含 `\` 的字串都當 native iteration path 直接用，不做轉換。

### 怎麼找你 project 的實際 iteration path

```bash
az boards iteration project list --project "$AZDO_PROJECT" -o table
```

輸出會列出所有 iteration paths，挑一個丟給 `sprint` 命令。

---

## 3. CLI Commands

### `sprint <sprint_id> [--json]`

列 sprint 內所有 work items。

**輸出欄位：** ID / Type / State / Title / Assignee / Parent

**範例：**

```bash
# Table（預設）
sprint sprint-12

# JSON（pipeline 用）
sprint sprint-12 --json
```

**JSON 結構（每個 element）：**

```json
{
  "id": 670,
  "type": "Task",
  "title": "...",
  "state": "In Progress",
  "assignee": "user@org.onmicrosoft.com",
  "sprint_id": "sprint-12",
  "sprint_native_id": "YourProject\\Sprint 12",
  "parent_id": 597,
  "area_path": "YourProject",
  "changed_at": "2026-04-20T02:11:40+00:00",
  "platform": "azure"
}
```

`native` 欄位（adapter 內部存原始 API response）在 `--json` 輸出中**故意省略**，避免 noise。

---

## 4. Common Patterns

### 4.1 Filter by state（jq）

```bash
sprint sprint-12 --json | jq '[.[] | select(.state == "In Progress")]'
sprint sprint-12 --json | jq '.[] | select(.state == "Blocked")'
```

### 4.2 Filter by assignee

```bash
sprint sprint-12 --json | jq '.[] | select(.assignee == "you@org.com") | {id, title, state}'
```

### 4.3 Count by state

```bash
sprint sprint-12 --json | jq 'group_by(.state) | map({state: .[0].state, count: length})'
```

### 4.4 整合 Claude Code

把 repo symlink 進 `~/.claude/skills/`：

```bash
ln -s ~/dev/kc_pm_sync ~/.claude/skills/pm-sync
```

之後在 Claude Code 對話用 `/pm-sync sprint-12` 或自然語言「拉一下 sprint 12 進度」，Claude 會讀 SKILL.md 然後 Bash 執行。

### 4.5 切 platform（未來，目前只有 Azure）

```bash
export PM_SYNC_PLATFORM=redmine   # 切到 Redmine（待實作）
unset PM_SYNC_PLATFORM             # 回 default azure
```

---

## 5. Troubleshooting

| 症狀 | 可能原因 | 解 |
|---|---|---|
| `(no items)` 但你知道 sprint 有東西 | sprint_id 短形式跟 iteration path 命名不符 | 改傳 native form（見 §2） |
| `Missing required environment variable(s)` | env 沒 export 或 source | 檢查 `env \| grep AZDO_` |
| `command not found: az` | az CLI 沒裝或不在 PATH | 跑 §1.1 的安裝命令 |
| 第一次 `az boards` 卡住問你裝 extension | normal | 照提示按 y 裝 azure-devops extension |
| `TF400813: The user '...' is not authorized` | PAT 沒有 Work Items (Read) scope，或 PAT 過期 | 重生 PAT 確認 scope |
| `(parse_azure raises KeyError on 'System.Title')` | WIQL 沒 SELECT 完整欄位（regression） | 看 `adapters/azure_devops.py:list_sprint_items` 是否被改過 |
| `RuntimeError: Azure CLI ('az') not found on PATH` | 同 `command not found` | 同上 |
| `Unknown PM_SYNC_PLATFORM=...` | 拼錯或設了未實作的 platform | `unset PM_SYNC_PLATFORM` 回 default |
| 速度突然變超慢（>10s） | 可能 N+1 regression | 跑 `pytest tests/test_azure_adapter.py::test_list_sprint_items_uses_single_wiql_with_full_fields`，紅燈代表 regression |

---

## 6. Roadmap

當前 MVP 只有 `sprint` 一個指令。以下依優先順序分 phase 列出，歡迎 PR 填坑。

**終極 vision：** 跟 [`kc_ai_skills/spec`](https://github.com/KerberosClaw/kc_ai_skills/tree/main/spec) + [`kc_claude_harness`](https://github.com/KerberosClaw/kc_claude_harness) 串成「數位 PM pipeline」—— 長官一句話需求 → `/spec` 釐清 → `/pm-sync push` 切 work items → 每日 `/pm-sync daily` 推 Telegram standup。

### Phase A — Read paths 完整化

- [ ] `show <id>` — 單筆 work item 細節（adapter 已有 `get_item`，差 CLI 套殼）
- [ ] `daily` — 拉當日 sprint + diff 昨天 snapshot + standup-friendly format
- [ ] `--state X` / `--assignee Y` filter flags
- [ ] `--mine` shortcut（讀 `git config user.email` 或 `AZDO_USER` env）
- [ ] `@current` macro（自動解析「當前 sprint」）
- [ ] `sprints` — 列所有 iteration paths
- [ ] Backlog 模式（不指定 sprint，列整個 backlog）
- [ ] Sprint 比較（兩個 sprint diff）
- [ ] State snapshot cache（本地 SQLite / json，daily diff 需要）

### Phase B — Write paths（首個寫遠端的 feature 組）

- [ ] `push <spec-name>` — 把 `specs/<name>/tasks.md` 推 Azure 建 work items
  - 六要素 → work item fields 的權威 mapping 表
  - Hierarchy：spec.md = Feature，tasks.md 每項 = 掛在下面的 Task
  - Draft preview + `--confirm` gate（README 設計哲學的 Read-before-write）
  - Idempotent：重跑不重建已有的 task（用 spec id 做 mark）
- [ ] `assign <id> <engineer>` — 改 work item AssignedTo
- [ ] `state <id> <new-state>` — 改狀態（New / Active / In Progress / Done）
- [ ] Pull 反向：work item state 改了 → 反向更新本地 `tasks.md` 的 checkbox

### Phase C — Sprint planning（半智慧）

- [ ] `sprint-plan <spec-name>` — 自動切 sprint
  - Effort 估算策略（先 user 標 → 後加 LLM 自動估 + feedback loop 學準）
  - 依賴排序（task A 先，task B 後）
  - Capacity-aware 派人（滿載的人不給新任務）

### Phase D — Team / roster / capacity

- [ ] `~/.pm-sync.team.yml` schema（engineer 清單 / skill / capacity）
- [ ] `team` command — 顯示當前每人 load
- [ ] 自動從 Azure DevOps team settings 抓成員（選用，vs 手動維護）

### Wiki sync（獨立 feature）

- [ ] Azure DevOps Wiki pull（遠端 → 本地 markdown）
- [ ] Azure DevOps Wiki push（本地 markdown → 遠端）

### 其他 adapters

加新 adapter 步驟見 [`ARCHITECTURE.md`](ARCHITECTURE.md)。目前是「寫兩個檔 + 改一行 registry」。

- [ ] Redmine
- [ ] Jira
- [ ] GitHub Issues
- [ ] 禪道

### 跨 spec 設計議題（非 feature，是必須先敲定的事）

- [ ] 六要素 → Azure work item 欄位 mapping 權威表（`docs/SPEC_INTEGRATION.md` 是合適位置）
- [ ] Idempotency strategy：spec 改完 push 第二次時怎麼識別「這 task 已存在」（spec-id 進 description / tag / 關聯欄位？）
- [ ] Spec ↔ work item 雙向同步的 conflict resolution（同時改兩邊怎麼辦）
- [ ] `/pm-sync daily` 的 Telegram 推播格式跟 skill-cron 整合

---

詳細設計哲學跟加新 adapter 的步驟見 [`ARCHITECTURE.md`](ARCHITECTURE.md)。
