"""Unit tests for scripts.sprint CLI entrypoint."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from models.task import UnifiedTask


def _make_stub_task(id: int, title: str = "stub", assignee: str | None = None) -> UnifiedTask:
    return UnifiedTask(
        id=id,
        type="Task",
        title=title,
        state="In Progress",
        assignee=assignee,
        sprint_id="sprint-12",
        sprint_native_id="AcmeDev\\Sprint 12",
        parent_id=None,
        area_path="AcmeDev",
        changed_at=datetime(2026, 4, 20, 2, 11, 40, tzinfo=timezone.utc),
        platform="test",
    )


def _clear_platform_env(monkeypatch):
    """Ensure PM_SYNC_PLATFORM and adapter-specific env vars don't leak in."""
    monkeypatch.delenv("PM_SYNC_PLATFORM", raising=False)
    for var in ("AZDO_ORG_URL", "AZDO_PROJECT", "AZDO_PAT"):
        monkeypatch.delenv(var, raising=False)


def test_exits_when_env_missing(monkeypatch, capsys):
    """Default platform (azure) with no env → adapter.from_env raises → CLI exits 1."""
    _clear_platform_env(monkeypatch)

    from scripts.sprint import main

    with patch("sys.argv", ["sprint.py", "sprint-12"]):
        with pytest.raises(SystemExit) as exc:
            main()

    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "AZDO_PAT" in err
    assert "AZDO_ORG_URL" in err
    assert "export" in err.lower()


def test_exits_when_unknown_platform(monkeypatch, capsys):
    """PM_SYNC_PLATFORM set to something not in registry → exit 1 with available list."""
    monkeypatch.setenv("PM_SYNC_PLATFORM", "azur")  # typo

    from scripts.sprint import main

    with patch("sys.argv", ["sprint.py", "sprint-12"]):
        with pytest.raises(SystemExit) as exc:
            main()

    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "azur" in err
    assert "azure" in err  # available list contains the real one


def test_prints_table(monkeypatch, capsys):
    """Mock _load_adapter so the test stays platform-agnostic."""
    from scripts.sprint import main

    stub1 = _make_stub_task(670, title="Run through tech docs", assignee="demo_user@acme")
    stub2 = _make_stub_task(671, title="Another item", assignee="other@acme")

    m_adapter = MagicMock()
    m_adapter.list_sprint_items.return_value = [stub1, stub2]

    with patch("scripts.sprint._load_adapter", return_value=m_adapter):
        with patch("sys.argv", ["sprint.py", "sprint-12"]):
            rc = main()

    assert rc == 0
    out = capsys.readouterr().out
    assert "670" in out and "671" in out
    assert "Run through tech docs" in out
    assert "ID" in out and "Title" in out  # header row
    m_adapter.list_sprint_items.assert_called_once_with("sprint-12")


def test_json_flag_outputs_json_array(monkeypatch, capsys):
    """Mock _load_adapter; verify --json output shape stays clean."""
    from scripts.sprint import main

    stub = _make_stub_task(670, title="Run through tech docs")
    m_adapter = MagicMock()
    m_adapter.list_sprint_items.return_value = [stub]

    with patch("scripts.sprint._load_adapter", return_value=m_adapter):
        with patch("sys.argv", ["sprint.py", "sprint-12", "--json"]):
            rc = main()

    assert rc == 0
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert isinstance(parsed, list) and len(parsed) == 1
    first = parsed[0]
    assert first["id"] == 670
    assert first["title"] == "Run through tech docs"
    assert "native" not in first  # explicitly excluded
    assert first["changed_at"] == "2026-04-20T02:11:40+00:00"
