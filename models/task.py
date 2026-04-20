"""Unified Task schema for kc_pm_sync.

Platform-neutral dataclass representing a PM work item. Parsing from
specific platforms lives in `parsers/<platform>.py` (e.g. `parsers.azure`)
so this module stays a pure data definition with no platform bias.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UnifiedTask:
    # 識別
    id: int
    type: str                  # "Task" | "Product Backlog Item" | "Feature" | "Epic" | (platform-specific)
    # 內容
    title: str
    state: str                 # "New" | "Active" | "In Progress" | "Resolved" | "Closed" | (platform-specific)
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
    platform: str              # required, no default — each parser sets explicitly ("azure" / "redmine" / "jira" / ...)
    native: dict = field(default_factory=dict)
