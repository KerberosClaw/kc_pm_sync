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
    )


def _set_env(monkeypatch):
    monkeypatch.setenv("AZDO_ORG_URL", "https://dev.azure.com/acme")
    monkeypatch.setenv("AZDO_PROJECT", "AcmeDev")
    monkeypatch.setenv("AZDO_PAT", "dummy-pat")


def test_exits_when_env_missing(monkeypatch, capsys):
    # Ensure AZDO_PAT (and potentially others from a real shell) are absent
    for var in ("AZDO_ORG_URL", "AZDO_PROJECT", "AZDO_PAT"):
        monkeypatch.delenv(var, raising=False)

    from scripts.sprint import main

    with patch("sys.argv", ["sprint.py", "sprint-12"]):
        with pytest.raises(SystemExit) as exc:
            main()

    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "AZDO_PAT" in err
    assert "AZDO_ORG_URL" in err
    assert "export" in err.lower() or "AZDO_" in err


def test_prints_table(monkeypatch, capsys):
    _set_env(monkeypatch)

    from scripts.sprint import main

    stub1 = _make_stub_task(670, title="Run through tech docs", assignee="demo_user@acme")
    stub2 = _make_stub_task(671, title="Another item", assignee="other@acme")

    with patch("scripts.sprint.AzureDevOpsAdapter") as m_adapter_cls:
        m_instance = MagicMock()
        m_instance.list_sprint_items.return_value = [stub1, stub2]
        m_adapter_cls.return_value = m_instance

        with patch("sys.argv", ["sprint.py", "sprint-12"]):
            rc = main()

    assert rc == 0
    out = capsys.readouterr().out
    assert "670" in out and "671" in out
    assert "Run through tech docs" in out
    assert "ID" in out and "Title" in out  # header row
    # verify adapter was constructed with env values
    m_adapter_cls.assert_called_once_with(
        org_url="https://dev.azure.com/acme",
        project="AcmeDev",
        pat="dummy-pat",
    )


def test_json_flag_outputs_json_array(monkeypatch, capsys):
    _set_env(monkeypatch)

    from scripts.sprint import main

    stub = _make_stub_task(670, title="Run through tech docs")

    with patch("scripts.sprint.AzureDevOpsAdapter") as m_adapter_cls:
        m_adapter_cls.return_value.list_sprint_items.return_value = [stub]

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
