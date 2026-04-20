"""Azure DevOps payload parser.

Turns the raw JSON returned by `az boards work-item show` (or the equivalent
REST endpoint `/_apis/wit/workItems/N`) into a platform-neutral `UnifiedTask`.

Future parsers for other PM platforms (Redmine, Jira, GitHub Issues, ...)
live as siblings in this package — each one parses its native format
directly into `UnifiedTask`. None of them goes through Azure as an
intermediate format.
"""

from __future__ import annotations

import re
from datetime import datetime

from models.task import UnifiedTask


def _normalize_iso(s: str) -> str:
    """Normalize Azure DevOps ISO 8601 strings for Python 3.9/3.10 fromisoformat.

    - Strip trailing 'Z', replace with '+00:00' (3.9/3.10 don't accept 'Z').
    - Pad fractional seconds to exactly 6 digits (3.9/3.10 require .fff or
      .ffffff; Azure may return 1-3 digits like '.62' or '.087').

    Python 3.11+ handles both natively, but this is cheap so we always run it.
    """
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    m = re.search(r"\.(\d+)", s)
    if m:
        frac = m.group(1)
        padded = (frac + "000000")[:6]
        s = s.replace("." + frac, "." + padded, 1)
    return s


def parse_azure(raw: dict) -> UnifiedTask:
    """Build a UnifiedTask from an Azure DevOps work item API response.

    Input shape: top-level `id`, `fields` dict, plus optional `relations`.
    Matches `az boards work-item show --id N -o json` and REST
    `/_apis/wit/workItems/N` responses.

    Sprint ID convention: the last `\\`-separated segment of
    `System.IterationPath` becomes `sprint_id` (lowercased, spaces→`-`).
    E.g. `"AcmeDev\\Sprint 12"` → `sprint_id="sprint-12"`.

    Missing optional keys (`System.Parent`, `System.AssignedTo`) resolve
    to None. Required keys raise KeyError — fail fast, caller decides
    whether to catch.
    """
    fields_ = raw["fields"]

    native_iter = fields_["System.IterationPath"]
    sprint_id = native_iter.split("\\")[-1].lower().replace(" ", "-")

    assignee_obj = fields_.get("System.AssignedTo")
    assignee = assignee_obj.get("uniqueName") if assignee_obj else None

    changed_at = datetime.fromisoformat(_normalize_iso(fields_["System.ChangedDate"]))

    return UnifiedTask(
        id=raw["id"],
        type=fields_["System.WorkItemType"],
        title=fields_["System.Title"],
        state=fields_["System.State"],
        assignee=assignee,
        sprint_id=sprint_id,
        sprint_native_id=native_iter,
        parent_id=fields_.get("System.Parent"),
        area_path=fields_["System.AreaPath"],
        changed_at=changed_at,
        platform="azure",
        native=raw,
    )
