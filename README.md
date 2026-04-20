# PM Sync — Sprint Boards in Your Terminal, Not 17 Browser Tabs

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)

[正體中文](README_zh.md)

> Pull sprint work items from your PM platform straight into the terminal.
> Azure DevOps today; Redmine / Jira / GitHub Issues on the roadmap (a.k.a. "things I'll get to eventually").
> Output as a clean table or pipeline-ready JSON.

## What It Does

One command, one platform-neutral schema, zero browser tabs:

```bash
sprint sprint-12              # table
sprint sprint-12 --json | jq  # pipe it
```

Why this exists: I got tired of reloading the Azure DevOps web board every time I wanted to know what was in flight this sprint. Now I type `sprint sprint-12` in any terminal and the board prints itself. Same data, 100× less clicking.

## Status

**MVP shipped.** What actually works today:
- ✅ List sprint work items (Azure DevOps adapter via `az` CLI)
- ✅ Table + JSON output
- ✅ Adapter pattern + `PM_SYNC_PLATFORM` env var → other platforms can drop in without breaking the existing one

What doesn't work yet (a.k.a. the roadmap, a.k.a. promises) is in [`docs/USAGE.md`](docs/USAGE.md) §6. Spoiler: `show <id>` is one weekend away, `push` is several weekends away, and a Wiki adapter exists in spirit only.

## Prerequisites

Azure DevOps adapter (the default — and, today, the only one) needs:

1. **`az` CLI** 2.50+ — `brew install azure-cli` on macOS; other OSes see [`docs/USAGE.md`](docs/USAGE.md) §1
2. **Personal Access Token** with `Work Items (Read)` scope — minimum to read your sprint
3. **Three env vars** set:
   ```bash
   export AZDO_ORG_URL="https://dev.azure.com/your-org"
   export AZDO_PROJECT="YourProject"
   export AZDO_PAT="..."
   ```

Want to never type these again? Set up the `~/.pm-sync.env` + alias pattern — [`docs/USAGE.md`](docs/USAGE.md) §1.

## Quick Start

```bash
git clone https://github.com/KerberosClaw/kc_pm_sync.git ~/dev/kc_pm_sync
cd ~/dev/kc_pm_sync

# (after Prerequisites are set)
python3 scripts/sprint.py --help                # sanity check
python3 scripts/sprint.py sprint-12             # your first sprint pull
```

If `sprint-12` returns `(no items)` but you swear the sprint has tickets — your iteration path is probably named differently than `Project\Sprint 12`. Welcome to "every Azure DevOps project picks its own iteration naming" hell. See [`docs/USAGE.md`](docs/USAGE.md) §2 — there's a one-liner to find your real iteration path and a fallback that always works.

## Security Notice

- **PAT never goes on the command line.** It's injected into the `az` subprocess via the `AZURE_DEVOPS_EXT_PAT` env var (won't show up in `ps` or shell history).
- **Recommended PAT storage:** `~/.pm-sync.env` with `chmod 600`, sourced by alias. Never commit it.
- **Test fixtures are sanitized** (org / user / GUID replaced with placeholders) per [`tests/fixtures/README.md`](tests/fixtures/README.md). The fixture directory is safe to inspect publicly.
- **Read-only by default.** Current MVP only has read paths. Future write paths will require `--confirm` and draft-preview gates.

## Docs

| Doc | Purpose |
|---|---|
| [`docs/USAGE.md`](docs/USAGE.md) | Full CLI usage, sprint_id format, troubleshooting, roadmap |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Four-layer design, how to add a new adapter (Redmine worked example) |
| [`SKILL.md`](SKILL.md) | Claude Code skill manifest — symlink the repo into `~/.claude/skills/` and use `/pm-sync` in Claude Code |
| [`specs/completed/`](specs/completed/) | Spec-driven development history (01: schema, 02: ABC, 03: Azure adapter, 04: CLI). Some specs have been superseded by later refactors — see banners. |

## License

MIT — see [LICENSE](LICENSE).
