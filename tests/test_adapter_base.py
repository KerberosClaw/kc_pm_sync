"""Unit tests for adapters.base.PMAdapter — ABC semantics + contract."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from adapters.base import PMAdapter
from models.task import UnifiedTask


def _make_stub_task(id: int = 1) -> UnifiedTask:
    """Build a minimal valid UnifiedTask for adapter-return stubs."""
    return UnifiedTask(
        id=id,
        type="Task",
        title="stub",
        state="New",
        assignee=None,
        sprint_id="sprint-1",
        sprint_native_id="X\\Sprint 1",
        parent_id=None,
        area_path="X",
        changed_at=datetime.now(timezone.utc),
    )


def test_cannot_instantiate_abstract():
    """Direct instantiation of PMAdapter must raise TypeError."""
    with pytest.raises(TypeError):
        PMAdapter()  # type: ignore[abstract]


def test_subclass_missing_method_cannot_instantiate():
    """A subclass that implements only one abstract method must still be abstract."""

    class Incomplete(PMAdapter):
        def list_sprint_items(self, sprint_id):
            return []
        # get_item intentionally not implemented

    with pytest.raises(TypeError):
        Incomplete()  # type: ignore[abstract]


def test_fully_implemented_subclass_instantiates():
    """A subclass implementing both methods instantiates and returns UnifiedTasks."""

    class Dummy(PMAdapter):
        def list_sprint_items(self, sprint_id):
            return [_make_stub_task()]

        def get_item(self, item_id):
            return _make_stub_task(id=item_id)

    adapter = Dummy()

    items = adapter.list_sprint_items("sprint-12")
    assert len(items) == 1
    assert isinstance(items[0], UnifiedTask)
    assert items[0].type == "Task"

    item = adapter.get_item(42)
    assert isinstance(item, UnifiedTask)
    assert item.id == 42
