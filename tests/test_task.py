"""Unit tests for models.task.UnifiedTask."""

import json
from datetime import datetime
from pathlib import Path

from models.task import UnifiedTask


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "azure"


def test_from_azure_payload_work_item_670():
    raw = json.loads((FIXTURE_DIR / "work_item_670.json").read_text())
    task = UnifiedTask.from_azure_payload(raw)

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
