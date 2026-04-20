"""/pm-sync sprint — CLI entrypoint for pulling sprint work items.

Selects a PM adapter via the `PM_SYNC_PLATFORM` env var (default: ``azure``),
hands off to that adapter's `from_env()` classmethod for credentials, then
calls `list_sprint_items(sprint_id)` and prints either an aligned table or
JSON.

Usage:
    # Azure DevOps (default platform)
    export AZDO_ORG_URL="https://dev.azure.com/your-org"
    export AZDO_PROJECT="YourProject"
    export AZDO_PAT="..."

    python3 scripts/sprint.py sprint-12
    python3 scripts/sprint.py sprint-12 --json

    # Switch platform later (when other adapters land):
    # export PM_SYNC_PLATFORM=redmine
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

# Allow running as `python3 scripts/sprint.py` from repo root or anywhere:
# prepend repo root so `adapters` / `models` / `parsers` packages are importable.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from adapters.base import PMAdapter  # noqa: E402
from models.task import UnifiedTask  # noqa: E402


# Adapter registry — add a row when shipping a new adapter; CLI auto-dispatches.
ADAPTERS = {
    "azure": ("adapters.azure_devops", "AzureDevOpsAdapter"),
    # Future:
    # "redmine": ("adapters.redmine", "RedmineAdapter"),
    # "jira":    ("adapters.jira",    "JiraAdapter"),
}

DEFAULT_PLATFORM = "azure"

TITLE_MAX = 60
ASSIGNEE_MAX = 30


def _load_adapter() -> PMAdapter:
    """Resolve the adapter for the current PM_SYNC_PLATFORM (default 'azure').

    Each adapter's `from_env()` classmethod reads its own platform-specific
    env vars and raises `EnvironmentError` (with a helpful message) if any
    are missing. CLI catches that and exits 1.
    """
    platform = os.environ.get("PM_SYNC_PLATFORM", DEFAULT_PLATFORM)
    if platform not in ADAPTERS:
        sys.stderr.write(
            f"Unknown PM_SYNC_PLATFORM={platform!r}. "
            f"Available: {sorted(ADAPTERS)}\n"
            f"Default is '{DEFAULT_PLATFORM}'; unset PM_SYNC_PLATFORM to use it.\n"
        )
        sys.exit(1)

    module_path, class_name = ADAPTERS[platform]
    AdapterCls = getattr(importlib.import_module(module_path), class_name)
    try:
        return AdapterCls.from_env()
    except EnvironmentError as e:
        sys.stderr.write(f"{e}\n")
        sys.exit(1)


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def _format_table(tasks: list[UnifiedTask]) -> str:
    if not tasks:
        return "(no items)"

    rows = [
        {
            "id": str(t.id),
            "type": t.type,
            "state": t.state,
            "title": _truncate(t.title, TITLE_MAX),
            "assignee": _truncate(t.assignee or "-", ASSIGNEE_MAX),
            "parent": str(t.parent_id) if t.parent_id is not None else "-",
        }
        for t in tasks
    ]
    header = {"id": "ID", "type": "Type", "state": "State",
              "title": "Title", "assignee": "Assignee", "parent": "Parent"}
    cols = ["id", "type", "state", "title", "assignee", "parent"]
    widths = {c: max(len(header[c]), *(len(r[c]) for r in rows)) for c in cols}

    def fmt(row: dict) -> str:
        return "  ".join(row[c].ljust(widths[c]) for c in cols)

    lines = [fmt(header), "  ".join("-" * widths[c] for c in cols)]
    lines.extend(fmt(r) for r in rows)
    return "\n".join(lines)


def _format_json(tasks: list[UnifiedTask]) -> str:
    def to_dict(t: UnifiedTask) -> dict:
        d = asdict(t)
        d.pop("native", None)  # raw payload excluded (too noisy for CLI)
        d["changed_at"] = t.changed_at.isoformat()
        return d

    return json.dumps([to_dict(t) for t in tasks], indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pm-sync sprint",
        description=(
            "List work items in a sprint. Platform selected via "
            "PM_SYNC_PLATFORM env var (default: azure)."
        ),
    )
    parser.add_argument(
        "sprint_id",
        help="Sprint identifier. Short form 'sprint-12' or platform-native "
             "form (e.g. Azure 'YourProject\\Sprint 12') both accepted.",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON array instead of table (for piping / scripting).",
    )
    args = parser.parse_args()

    adapter = _load_adapter()
    tasks = adapter.list_sprint_items(args.sprint_id)

    output = _format_json(tasks) if args.json else _format_table(tasks)
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
