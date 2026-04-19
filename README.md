# kc_pm_sync

Claude Code skill — 把 local spec 檔案跟遠端專案管理平台（首發 Azure DevOps）對接起來。

## 當前狀態

Skeleton，尚未實作。

## MVP 範圍

**Pull 路徑（read-only）**
- `/pm-sync sprint` → 列出當前 sprint 的 tasks、assignee、狀態、blocked 項目
- 目的：第一次當 PM 快速看清現況，不開 web UI 點來點去

## Roadmap TODO

- [ ] **MVP: `/pm-sync sprint`** — pull 本 sprint 進度（read-only）
- [ ] `/pm-sync show <id>` — pull 個別 work item 細節
- [ ] **Push: `/pm-sync push <spec-name>`** — 把新需求用 `spec` skill 整理後，透過 pm-sync 推到 Azure DevOps 建 work items
- [ ] Wiki sync（Azure DevOps Wiki pull / push）
- [ ] Confirmation gate + draft preview（所有寫遠端操作）
- [ ] Revision check / ETag 避 race condition
- [ ] 加其他 adapter：Redmine / Jira / GitHub Issues / 禪道

## 設計哲學

- **Adapter pattern**：平台隔離，`adapters/` 下每個 platform 一個檔
- **Unified Task model**：各平台的 work item 轉成同一個 schema
- **Loose coupling 與 `spec` skill**：兩者透過 `specs/<name>/tasks.md` 的 markdown format 對接，互不依賴
- **Read-before-write**：所有 push 都先 draft preview，user confirm 才寫遠端

## 目標架構

```
kc_pm_sync/
├── SKILL.md                 # /pm-sync 入口
├── adapters/
│   ├── base.py              # abstract interface
│   ├── azure_devops.py      # 第一個實作
│   └── ...
├── models/
│   └── task.py              # unified Task model
└── scripts/
    ├── sprint.py            # MVP: pull current sprint
    ├── show.py              # pull individual work item
    ├── push.py              # TODO: local tasks.md → remote
    └── pull.py              # TODO: remote → local (general)
```

## 相關 repo

- `kc_ai_skills/spec` — Spec-driven lifecycle skill，產出 `specs/<name>/tasks.md`
- 本 repo 負責把那些 tasks 同步到遠端 PM 平台（pm-sync）

## 認證

Azure DevOps 透過 Personal Access Token (PAT)。不進 repo，用環境變數或本地 config：

```
export AZDO_ORG_URL="https://dev.azure.com/{org}"
export AZDO_PROJECT="{project}"
export AZDO_PAT="{pat}"
```
