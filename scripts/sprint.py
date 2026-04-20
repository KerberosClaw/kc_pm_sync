"""/pm-sync sprint — CLI entrypoint for pulling sprint work items.

Reads AZDO_ORG_URL / AZDO_PROJECT / AZDO_PAT from environment, instantiates
AzureDevOpsAdapter, calls list_sprint_items(sprint_id), and prints either
an aligned table or JSON.

Usage:
    export AZDO_ORG_URL="https://dev.azure.com/your-org"
    export AZDO_PROJECT="YourProject"
    export AZDO_PAT="..."

    python3 scripts/sprint.py sprint-12
    python3 scripts/sprint.py sprint-12 --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

# Allow running as `python3 scripts/sprint.py` from repo root or anywhere:
# prepend repo root so `adapters` / `models` packages are importable.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from adapters.azure_devops import AzureDevOpsAdapter  # noqa: E402
from models.task import UnifiedTask  # noqa: E402


REQUIRED_ENV = ("AZDO_ORG_URL", "AZDO_PROJECT", "AZDO_PAT")

TITLE_MAX = 60
ASSIGNEE_MAX = 30


def _load_env_or_exit() -> tuple[str, str, str]:
    """Return (org_url, project, pat) from env. Exit(1) with help if any missing."""
    missing = [v for v in REQUIRED_ENV if not os.environ.get(v)]
    if missing:
        sys.stderr.write(
            f"Missing required environment variable(s): {', '.join(missing)}\n"
            "\n"
            "Set them before running, for example:\n"
            '  export AZDO_ORG_URL="https://dev.azure.com/your-org"\n'
            '  export AZDO_PROJECT="YourProject"\n'
            '  export AZDO_PAT="..."\n'
            "\n"
            "See README.md Prerequisites for the full setup.\n"
        )
        sys.exit(1)
    return (
        os.environ["AZDO_ORG_URL"],
        os.environ["AZDO_PROJECT"],
        os.environ["AZDO_PAT"],
    )


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
        d.pop("native", None)  # raw Azure payload excluded (too noisy for CLI)
        d["changed_at"] = t.changed_at.isoformat()
        return d

    return json.dumps([to_dict(t) for t in tasks], indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="pm-sync sprint",
        description="List work items in a sprint from Azure DevOps.",
    )
    parser.add_argument(
        "sprint_id",
        help="Sprint identifier. Short form 'sprint-12' or native "
             "'YourProject\\Sprint 12' both accepted.",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON array instead of table (for piping / scripting).",
    )
    args = parser.parse_args()

    org_url, project, pat = _load_env_or_exit()
    adapter = AzureDevOpsAdapter(org_url=org_url, project=project, pat=pat)
    tasks = adapter.list_sprint_items(args.sprint_id)

    output = _format_json(tasks) if args.json else _format_table(tasks)
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
