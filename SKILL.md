---
name: pm-sync
description: "Sync tasks / work items between local spec files and PM platforms (Azure DevOps first). Pull sprint progress, push spec tasks to tickets."
version: 0.0.1
status: skeleton
triggers: ["pm-sync", "sprint 進度", "推 ticket", "拉 sprint"]
---

# /pm-sync

將 local `specs/<name>/tasks.md` 同步到遠端專案管理平台，並能反向拉 sprint 進度下來。

## 當前狀態

Skeleton only。MVP 開發中：`/pm-sync sprint`。

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
