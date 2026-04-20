---
name: pm-sync
description: "Sync tasks / work items between local spec files and PM platforms (Azure DevOps first). Pull sprint progress, push spec tasks to tickets."
version: 0.2.0
status: mvp
triggers: ["pm-sync", "sprint 進度", "推 ticket", "拉 sprint"]
---

# /pm-sync

將 local `specs/<name>/tasks.md` 同步到遠端專案管理平台，並能反向拉 sprint 進度下來。

## 當前狀態

**MVP 可跑：`/pm-sync sprint` 命令完成。**

- ✅ UnifiedTask schema + `from_azure_payload` factory（spec 01）
- ✅ PMAdapter ABC（spec 02）
- ✅ AzureDevOpsAdapter via `az` CLI（spec 03）
- ✅ CLI entrypoint `scripts/sprint.py`（spec 04）
- 🚧 `/pm-sync show <id>`、`/pm-sync push`、其他 adapter — future

## Usage

先照 `README.md` Prerequisites 裝 `az` CLI 跟 export 三個 env vars。然後：

```bash
# 列出 sprint-12 的 work items，table 形式
python3 scripts/sprint.py sprint-12

# JSON 輸出，供 pipeline 用
python3 scripts/sprint.py sprint-12 --json | jq '.[] | {id, title, state}'

# 也接受 native iteration path
python3 scripts/sprint.py 'YourProject\Sprint 12'
```

預期 table output（去敏示意）：

```
ID   Type  State        Title                      Assignee             Parent
---  ----  -----------  -------------------------  -------------------  ------
670  Task  In Progress  Run through tech docs      demo_user@acme.com   597
671  Task  New          Another item …             other@acme.com       -
```

## 目標使用方式

```
/pm-sync sprint                # 列出本 sprint 進度（pull，MVP）
/pm-sync show <id>             # 看特定 work item 細節（pull）
/pm-sync push <spec-name>      # 把 spec 的 tasks 推到 azure 建 work items（TODO）
```

詳細規畫與 roadmap 見 `README.md`。

## 跟 `spec` skill 的關係

- `spec` skill 負責：需求釐清 → plan → tasks.md → 驗收
- `pm-sync` 負責：把 `tasks.md` 的內容 sync 到遠端平台
- 兩者透過 `specs/<name>/tasks.md` 的 markdown 格式對接，不互相 import
