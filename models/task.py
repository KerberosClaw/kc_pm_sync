"""Unified Task schema for kc_pm_sync.

Platform-neutral dataclass representing a PM work item, plus a factory
method to construct from Azure DevOps work item API payloads.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime


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


@dataclass
class UnifiedTask:
    # 識別
    id: int
    type: str                  # "Task" | "Product Backlog Item" | "Feature" | "Epic"
    # 內容
    title: str
    state: str                 # "New" | "Active" | "In Progress" | "Resolved" | "Closed"
    # 人
    assignee: str | None
    # Sprint（雙 ID：short + native）
    sprint_id: str             # internal short, e.g. "sprint-12"
    sprint_native_id: str      # platform raw, e.g. "AcmeDev\\Sprint 12"
    # 階層
    parent_id: int | None
    # 分類
    area_path: str
    # 時間
    changed_at: datetime
    # 平台 hint + raw escape hatch
    platform: str = "azure"
    native: dict = field(default_factory=dict)

    @classmethod
    def from_azure_payload(cls, raw: dict) -> "UnifiedTask":
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

        # Azure returns ISO 8601 strings with varying fractional-second
        # precision and a trailing 'Z'. Python 3.9/3.10 fromisoformat rejects
        # both; normalize first for broader compat.
        changed_at = datetime.fromisoformat(_normalize_iso(fields_["System.ChangedDate"]))

        return cls(
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
