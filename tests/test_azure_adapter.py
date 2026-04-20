"""Unit tests for adapters.azure_devops.AzureDevOpsAdapter (mocked subprocess)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from adapters.azure_devops import AzureDevOpsAdapter
from models.task import UnifiedTask


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "azure"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / f"{name}.json").read_text())


def test_init_raises_when_az_missing():
    with patch("adapters.azure_devops.shutil.which", return_value=None):
        with pytest.raises(RuntimeError, match="az"):
            AzureDevOpsAdapter(
                org_url="https://dev.azure.com/acme",
                project="AcmeDev",
                pat="dummy-pat",
            )


def test_get_item_maps_azure_payload():
    raw_670 = _load_fixture("work_item_670")
    with patch("adapters.azure_devops.shutil.which", return_value="/usr/bin/az"), \
         patch("adapters.azure_devops.subprocess.run") as m_run:
        m_run.return_value = MagicMock(stdout=json.dumps(raw_670), returncode=0)
        adapter = AzureDevOpsAdapter(
            org_url="https://dev.azure.com/acme",
            project="AcmeDev",
            pat="pat",
        )
        task = adapter.get_item(670)

    assert isinstance(task, UnifiedTask)
    assert task.id == 670
    assert task.state == "In Progress"
    assert task.sprint_id == "sprint-12"
    # Verify PAT was injected via env (not argv)
    call_kwargs = m_run.call_args.kwargs
    assert "AZURE_DEVOPS_EXT_PAT" in call_kwargs["env"]
    assert call_kwargs["env"]["AZURE_DEVOPS_EXT_PAT"] == "pat"
    assert "pat" not in " ".join(m_run.call_args.args[0])  # not on argv


def test_list_sprint_items_uses_single_wiql_with_full_fields():
    """One WIQL query returns parser-ready rows; no per-item show round-trip."""
    raw_670 = _load_fixture("work_item_670")
    # az boards query response shape == list of work items with `id` + `fields` dict,
    # same as `work-item show` (just whichever fields the SELECT lists).
    wiql_result = [raw_670]

    with patch("adapters.azure_devops.shutil.which", return_value="/usr/bin/az"), \
         patch("adapters.azure_devops.subprocess.run") as m_run:
        m_run.return_value = MagicMock(stdout=json.dumps(wiql_result), returncode=0)
        adapter = AzureDevOpsAdapter(
            org_url="https://dev.azure.com/acme",
            project="AcmeDev",
            pat="pat",
        )
        tasks = adapter.list_sprint_items("sprint-12")

    assert len(tasks) == 1
    assert isinstance(tasks[0], UnifiedTask)
    assert tasks[0].id == 670
    # Critical: ONE subprocess call, not N+1
    assert m_run.call_count == 1
    argv = m_run.call_args.args[0]
    assert "query" in argv and "--wiql" in argv
    # WIQL must SELECT all fields parse_azure needs (otherwise rows are partial)
    wiql = argv[argv.index("--wiql") + 1]
    for required in ("System.Title", "System.State", "System.WorkItemType",
                     "System.IterationPath", "System.AreaPath", "System.ChangedDate"):
        assert required in wiql, f"WIQL missing required field: {required}"
