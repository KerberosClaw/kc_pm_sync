"""Azure DevOps adapter using the `az` CLI.

Shell out to `az boards work-item show` / `az boards query` and parse JSON
through `UnifiedTask.from_azure_payload()`. Auth, retries, and HTTP error
mapping are handled by `az` itself.

Prerequisites:
    - `az` CLI 2.50+ installed and on PATH
    - Azure DevOps extension available (auto-installs on first `az boards`)
    - PAT exposed via `AZURE_DEVOPS_EXT_PAT` env var (handled internally;
      caller passes the PAT string to the constructor)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess

from adapters.base import PMAdapter
from models.task import UnifiedTask


_AZ_MISSING_MSG = (
    "Azure CLI ('az') not found on PATH. Install:\n"
    "  macOS:   brew install azure-cli\n"
    "  Linux:   https://learn.microsoft.com/cli/azure/install-azure-cli-linux\n"
    "  Windows: https://learn.microsoft.com/cli/azure/install-azure-cli-windows\n"
    "After install, run once: az extension add --name azure-devops"
)


class AzureDevOpsAdapter(PMAdapter):
    """Concrete PMAdapter backed by the `az` CLI.

    Constructor parameters are stored as instance attributes; the adapter
    never reads them from env itself (the caller — typically a CLI layer —
    is responsible for resolving env/config into explicit values).
    """

    def __init__(self, org_url: str, project: str, pat: str):
        if shutil.which("az") is None:
            raise RuntimeError(_AZ_MISSING_MSG)
        self.org_url = org_url
        self.project = project
        self.pat = pat

    def _az(self, *args: str) -> dict | list:
        """Invoke `az <args> --organization ... --project ... -o json` and
        return the parsed JSON stdout.

        PAT is injected via `AZURE_DEVOPS_EXT_PAT` env var (never on argv
        to avoid leaking through process listings).
        """
        env = {**os.environ, "AZURE_DEVOPS_EXT_PAT": self.pat}
        argv = [
            "az", *args,
            "--organization", self.org_url,
            "--project", self.project,
            "-o", "json",
        ]
        result = subprocess.run(
            argv, capture_output=True, text=True, check=True, env=env,
        )
        return json.loads(result.stdout)

    def _sprint_id_to_native(self, sprint_id: str) -> str:
        """Convert short sprint_id (``"sprint-12"``) to Azure IterationPath
        native form (``"AcmeDev\\Sprint 12"``).

        If the input already contains ``\\``, treat it as native and return
        as-is (satisfies the base contract's "native MAY be supported").
        """
        if "\\" in sprint_id:
            return sprint_id
        # Expect form "sprint-N" → project + "\Sprint N"
        _, _, number = sprint_id.rpartition("-")
        return f"{self.project}\\Sprint {number}"

    def get_item(self, item_id: int) -> UnifiedTask:
        raw = self._az("boards", "work-item", "show", "--id", str(item_id))
        # _az returns dict for show; callers that receive a list should crash loud.
        if not isinstance(raw, dict):
            raise TypeError(f"az work-item show returned {type(raw).__name__}, expected dict")
        return UnifiedTask.from_azure_payload(raw)

    def list_sprint_items(self, sprint_id: str) -> list[UnifiedTask]:
        native = self._sprint_id_to_native(sprint_id)
        wiql = (
            "SELECT [System.Id] FROM WorkItems "
            f"WHERE [System.IterationPath] = '{native}'"
        )
        rows = self._az("boards", "query", "--wiql", wiql)
        if not isinstance(rows, list):
            raise TypeError(f"az boards query returned {type(rows).__name__}, expected list")
        return [self.get_item(row["id"]) for row in rows]
