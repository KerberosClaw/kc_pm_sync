"""Base abstract adapter for PM platforms.

Defines the read-only MVP contract that concrete platform adapters
(Azure DevOps, Trello, Jira, ...) implement. All adapter methods return
`UnifiedTask` instances so downstream code stays platform-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.task import UnifiedTask


class PMAdapter(ABC):
    """Abstract adapter for a PM platform.

    Subclasses implement platform-specific authentication and API calls,
    but all return `UnifiedTask` instances conforming to the spec 01 schema.
    The MVP contract covers read-only access; write operations
    (push / update / close) are deferred to future specs.

    Constructor is intentionally undefined here because platforms differ
    significantly in their auth requirements (Azure DevOps: PAT + org +
    project; Trello: API key + token + board_id; etc.). Each concrete
    adapter declares its own `__init__`.
    """

    @abstractmethod
    def list_sprint_items(self, sprint_id: str) -> list[UnifiedTask]:
        """Return all work items in the given sprint.

        Parameters
        ----------
        sprint_id : str
            Sprint identifier. Adapter contract:
            - Short form (e.g. ``"sprint-12"``, matching
              ``UnifiedTask.sprint_id`` convention) **MUST** be supported.
            - Native form (e.g. ``"AcmeDev\\Sprint 12"``) **MAY** be
              supported.
            - Platform macros (e.g. ``"@current"``, ``"@current-1"``) **MAY**
              be supported.

            Resolution of the identifier to a platform-specific query is
            the adapter's responsibility.

        Returns
        -------
        list[UnifiedTask]
            All work items assigned to that sprint. Empty list if none.
            Iteration order is adapter-defined (typically by changed-date
            descending but not guaranteed).
        """

    @abstractmethod
    def get_item(self, item_id: int) -> UnifiedTask:
        """Fetch a single work item by its platform-native id.

        Parameters
        ----------
        item_id : int
            Platform-native work item id (e.g. Azure DevOps work item ID,
            Trello card short id as int). Adapters are expected to accept
            the same id format that appears on ``UnifiedTask.id``.

        Returns
        -------
        UnifiedTask
            The work item wrapped in the unified schema. Raises a
            platform-native exception (e.g. HTTP 404 error) if not found;
            MVP does not wrap into a custom exception class.
        """
