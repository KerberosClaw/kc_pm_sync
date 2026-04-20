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
from parsers.azure import parse_azure


REQUIRED_ENV = ("AZDO_ORG_URL", "AZDO_PROJECT", "AZDO_PAT")


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

    @classmethod
    def from_env(cls) -> "AzureDevOpsAdapter":
        """Build adapter from AZDO_* env vars; raise EnvironmentError if any missing.

        Required env vars are listed in `REQUIRED_ENV`. The error message
        includes a copy-paste-ready export block so the caller can act
        without consulting docs.
        """
        missing = [v for v in REQUIRED_ENV if not os.environ.get(v)]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variable(s) for AzureDevOpsAdapter: {', '.join(missing)}\n"
                "\n"
                "Set them before running, for example:\n"
                '  export AZDO_ORG_URL="https://dev.azure.com/your-org"\n'
                '  export AZDO_PROJECT="YourProject"\n'
                '  export AZDO_PAT="..."\n'
                "\n"
                "See README.md Prerequisites for the full setup."
            )
        return cls(
            org_url=os.environ["AZDO_ORG_URL"],
            project=os.environ["AZDO_PROJECT"],
            pat=os.environ["AZDO_PAT"],
        )

    def _az(self, *args: str) -> dict | list:
        """Invoke `az <args> --organization <org> -o json` and return parsed JSON.

        Only `--organization` and `-o json` are added automatically — callers
        that need `--project` must pass it in *args (e.g. `az boards query`
        accepts it; `az boards work-item show` does NOT).

        PAT is injected via `AZURE_DEVOPS_EXT_PAT` env var (never on argv
        to avoid leaking through process listings).
        """
        env = {**os.environ, "AZURE_DEVOPS_EXT_PAT": self.pat}
        argv = ["az", *args, "--organization", self.org_url, "-o", "json"]
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
        return parse_azure(raw)

    def list_sprint_items(self, sprint_id: str) -> list[UnifiedTask]:
        native = self._sprint_id_to_native(sprint_id)
        # SELECT every field parse_azure needs so the WIQL response is
        # parser-ready in one shot — avoids the N+1 of fetching each item
        # individually via `work-item show`.
        wiql = (
            "SELECT [System.Id], [System.WorkItemType], [System.Title], "
            "[System.State], [System.AssignedTo], [System.IterationPath], "
            "[System.Parent], [System.AreaPath], [System.ChangedDate] "
            f"FROM WorkItems WHERE [System.IterationPath] = '{native}'"
        )
        # `query` accepts --project (and needs it); `work-item show` does not.
        rows = self._az("boards", "query", "--wiql", wiql, "--project", self.project)
        if not isinstance(rows, list):
            raise TypeError(f"az boards query returned {type(rows).__name__}, expected list")
        return [parse_azure(row) for row in rows]
