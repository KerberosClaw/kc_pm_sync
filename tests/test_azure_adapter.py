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


def test_list_sprint_items_calls_wiql_then_fetches_each():
    raw_670 = _load_fixture("work_item_670")
    wiql_result = [{"id": 670}]

    with patch("adapters.azure_devops.shutil.which", return_value="/usr/bin/az"), \
         patch("adapters.azure_devops.subprocess.run") as m_run:
        m_run.side_effect = [
            MagicMock(stdout=json.dumps(wiql_result), returncode=0),  # WIQL query
            MagicMock(stdout=json.dumps(raw_670), returncode=0),       # show #670
        ]
        adapter = AzureDevOpsAdapter(
            org_url="https://dev.azure.com/acme",
            project="AcmeDev",
            pat="pat",
        )
        tasks = adapter.list_sprint_items("sprint-12")

    assert len(tasks) == 1
    assert isinstance(tasks[0], UnifiedTask)
    assert tasks[0].id == 670
    assert m_run.call_count == 2
    # First call should be the WIQL query
    first_argv = m_run.call_args_list[0].args[0]
    assert "query" in first_argv
    assert "--wiql" in first_argv
