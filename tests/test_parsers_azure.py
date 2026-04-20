"""Unit tests for parsers.azure (parse_azure + _normalize_iso)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from parsers.azure import _normalize_iso, parse_azure


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "azure"


@pytest.mark.parametrize("raw,expected", [
    # trailing Z → +00:00
    ("2026-04-20T02:11:40.087Z", "2026-04-20T02:11:40.087000+00:00"),
    # 2-digit fractional → padded to 6
    ("2026-04-15T00:51:04.62+00:00", "2026-04-15T00:51:04.620000+00:00"),
    # 1-digit fractional → padded to 6
    ("2026-04-15T00:51:04.6+00:00", "2026-04-15T00:51:04.600000+00:00"),
    # already 6-digit → unchanged
    ("2026-04-20T02:11:40.123456+00:00", "2026-04-20T02:11:40.123456+00:00"),
    # no fractional → unchanged
    ("2026-04-20T02:11:40+00:00", "2026-04-20T02:11:40+00:00"),
])
def test_normalize_iso_handles_fractional_and_Z(raw, expected):
    assert _normalize_iso(raw) == expected


def test_parse_azure_work_item_670():
    raw = json.loads((FIXTURE_DIR / "work_item_670.json").read_text())
    task = parse_azure(raw)

    # 識別
    assert task.id == 670
    assert task.type == "Task"
    # 內容
    assert task.title == "Run through tech docs"
    assert task.state == "In Progress"
    # 人
    assert task.assignee == "demo_user@acme.onmicrosoft.com"
    # Sprint 雙 ID
    assert task.sprint_id == "sprint-12"
    assert task.sprint_native_id == "AcmeDev\\Sprint 12"
    # 階層
    assert task.parent_id == 597
    # 分類
    assert task.area_path == "AcmeDev"
    # 時間（tz-aware datetime）
    assert isinstance(task.changed_at, datetime)
    assert task.changed_at.tzinfo is not None
    assert (task.changed_at.year, task.changed_at.month, task.changed_at.day) == (2026, 4, 20)
    # 平台 + raw escape hatch
    assert task.platform == "azure"
    assert task.native == raw
