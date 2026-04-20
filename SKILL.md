---
name: pm-sync
description: "Sync tasks / work items between local spec files and PM platforms (Azure DevOps first). Pull sprint progress, push spec tasks to tickets."
version: 0.2.0
status: mvp
triggers: ["pm-sync", "sprint 進度", "推 ticket", "拉 sprint"]
---

# /pm-sync

把遠端 PM 平台（首發 Azure DevOps）的 sprint 資料拉下來，並能反向把 spec tasks 推上去。

## 當前可用功能

**MVP shipped — 目前只有 `sprint` 一個指令。**

- ✅ `python3 scripts/sprint.py <sprint_id>` — 列 sprint work items（table 預設、`--json` 可接 pipeline）
- 🚧 `show <id>` / `push <spec-name>` / 其他 adapter — see `docs/USAGE.md` §6 roadmap

## Claude 怎麼跑

當 user 在對話中觸發此 skill（例如 `/pm-sync sprint-12` 或「拉一下 sprint 12」）：

1. 確認 user 已設好 `AZDO_ORG_URL` / `AZDO_PROJECT` / `AZDO_PAT` env vars（沒設 → 提示 user 看 `README.md` Prerequisites）
2. Bash 執行：`python3 ~/dev/kc_pm_sync/scripts/sprint.py <sprint_id>`（或加 `--json` 視 user 需求）
3. 把 output 顯示給 user
4. 如 user 沒給 sprint_id 或要 `(no items)`，提示看 `docs/USAGE.md` §2 sprint_id 格式說明

## 詳細文件

- **使用手冊**（CLI flags / sprint_id 格式 / pipeline 範例 / troubleshooting）：[`docs/USAGE.md`](docs/USAGE.md)
- **架構 + 加新 adapter**：[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **首頁**：[`README.md`](README.md)

## 跟 `spec` skill 的關係

- `spec` skill 負責：需求釐清 → plan → tasks.md → 驗收
- `pm-sync` 負責：把 `tasks.md` 的內容 sync 到遠端平台（read MVP 已完成；write 是 future）
- 兩者透過 `specs/<name>/tasks.md` 的 markdown 格式對接，不互相 import
