# Architecture

> **English summary:** Four-layer design (models / parsers / adapters / cli) with an adapter registry so new PM platforms can be added by writing two files and adding one line.

`kc_pm_sync` 把「跟 PM 平台對話」這件事拆成四層獨立模組：

```
┌─────────────────────────────────────────────────────────────┐
│  scripts/sprint.py        CLI entry — argparse + 表格輸出   │
│  ─────────────────────                                       │
│  ADAPTERS registry        platform → (module, class) 對照表 │
│  PM_SYNC_PLATFORM env     選擇用哪個 adapter（default azure）│
└──────────────────────────────┬──────────────────────────────┘
                               │ AdapterCls.from_env()
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  adapters/                                                   │
│  ├── base.py              PMAdapter ABC（list_sprint_items   │
│  │                        / get_item 兩個 abstract method）  │
│  ├── azure_devops.py      AzureDevOpsAdapter — 走 az CLI    │
│  ├── redmine.py           （未來）RedmineAdapter             │
│  └── jira.py              （未來）JiraAdapter                │
└──────────────────────────────┬──────────────────────────────┘
                               │ raw platform JSON
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  parsers/                  把 native JSON 譯成 UnifiedTask   │
│  ├── azure.py             parse_azure(raw) -> UnifiedTask    │
│  ├── redmine.py           （未來）parse_redmine              │
│  └── jira.py              （未來）parse_jira                 │
└──────────────────────────────┬──────────────────────────────┘
                               │ UnifiedTask instance
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  models/task.py           UnifiedTask dataclass — 純資料定義 │
│                           無平台特定邏輯，所有 platform 平等 │
└─────────────────────────────────────────────────────────────┘
```

**核心原則：**
- **UnifiedTask 是共同語言**，不是「Azure 格式」。每個平台直接 native → UnifiedTask，**不繞 Azure 當中間層**。
- **每個 adapter 自己讀自己的 env vars**（透過 `from_env()` classmethod），CLI 不關心細節。
- **CLI 跟 adapter 透過 registry + ABC 解耦**，`scripts/sprint.py` 不 import 任何具體 adapter。

---

## 加新 adapter 步驟（以 Redmine 為例）

### 步驟 1：寫 parser

新檔 `parsers/redmine.py`：

```python
"""Redmine payload parser."""
from __future__ import annotations
from datetime import datetime
from models.task import UnifiedTask


def parse_redmine(raw: dict) -> UnifiedTask:
    """Build UnifiedTask from Redmine REST API issue payload.

    Input shape: Redmine /issues/N.json response, top-level 'issue' object.
    """
    issue = raw["issue"]
    return UnifiedTask(
        id=issue["id"],
        type=issue["tracker"]["name"],     # 'Bug', 'Feature', etc.
        title=issue["subject"],
        state=issue["status"]["name"],
        assignee=issue.get("assigned_to", {}).get("name"),
        sprint_id=_short_sprint(issue.get("fixed_version")),
        sprint_native_id=issue.get("fixed_version", {}).get("name", ""),
        parent_id=issue.get("parent", {}).get("id"),
        area_path=issue["project"]["name"],
        changed_at=datetime.fromisoformat(issue["updated_on"].rstrip("Z") + "+00:00"),
        platform="redmine",
        native=raw,
    )
```

### 步驟 2：寫 adapter

新檔 `adapters/redmine.py`：

```python
"""Redmine adapter (REST API + API key auth)."""
from __future__ import annotations
import os, json, urllib.request

from adapters.base import PMAdapter
from models.task import UnifiedTask
from parsers.redmine import parse_redmine


REQUIRED_ENV = ("REDMINE_URL", "REDMINE_API_KEY")


class RedmineAdapter(PMAdapter):
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    @classmethod
    def from_env(cls) -> "RedmineAdapter":
        missing = [v for v in REQUIRED_ENV if not os.environ.get(v)]
        if missing:
            raise EnvironmentError(
                f"Missing required env var(s) for RedmineAdapter: {', '.join(missing)}\n"
                "\n"
                "Set them before running:\n"
                '  export REDMINE_URL="https://redmine.example.com"\n'
                '  export REDMINE_API_KEY="..."'
            )
        return cls(os.environ["REDMINE_URL"], os.environ["REDMINE_API_KEY"])

    def get_item(self, item_id: int) -> UnifiedTask:
        url = f"{self.base_url}/issues/{item_id}.json"
        req = urllib.request.Request(url, headers={"X-Redmine-API-Key": self.api_key})
        raw = json.loads(urllib.request.urlopen(req).read())
        return parse_redmine(raw)

    def list_sprint_items(self, sprint_id: str) -> list[UnifiedTask]:
        # implement with /issues.json?fixed_version_id=...
        ...
```

### 步驟 3：在 CLI registry 加一行

`scripts/sprint.py` 的 `ADAPTERS` dict：

```python
ADAPTERS = {
    "azure":   ("adapters.azure_devops", "AzureDevOpsAdapter"),
    "redmine": ("adapters.redmine",      "RedmineAdapter"),    # ← 加這行
}
```

### 步驟 4：寫測試

新檔 `tests/test_redmine_adapter.py`：mock `urllib.request.urlopen`，驗 from_env 缺 env 行為、get_item / list_sprint_items 回傳正確 UnifiedTask。

新檔 `tests/test_parsers_redmine.py`：放 fixture `tests/fixtures/redmine/issue_*.json`（**記得去敏**，按 `tests/fixtures/README.md` 規範），測 `parse_redmine` 欄位 mapping。

### 完成

```bash
# user 切換 platform
export PM_SYNC_PLATFORM=redmine
export REDMINE_URL=https://...
export REDMINE_API_KEY=...
python3 scripts/sprint.py sprint-12
```

`scripts/sprint.py` 完全不用改（除了 registry 那一行）；既有 Azure 測試也不會 regression。

---

## 為什麼這樣設計

**Loose coupling：** 加 Redmine 時，**Azure 任何一個檔都不會被 import / modify**。Adapter 之間互相不知道對方存在。

**ABC 強制契約：** `RedmineAdapter` 沒實作 `list_sprint_items` / `get_item` 兩個 abstract method 的話，`from_env()` 實例化會 raise `TypeError`。CI 階段就抓得到。

**`UnifiedTask` 不是 Azure 偽裝：** 各 parser 直接從 native JSON map 過來，沒有「先轉成 Azure 格式」的中間層。schema 本身欄位名都是平台中立的（`sprint_id`、`area_path`），任何平台都能填。

**`from_env()` 在 adapter 裡：** Azure 的 `AZDO_*` 跟 Redmine 的 `REDMINE_*` 各自管理，CLI 不需要知道。要加 Jira 連 CLI 都不會碰。

---

## 跟 specs/ 的關係

`specs/completed/01-04` 是這個 codebase 從 0 到 MVP 的 spec-driven 開發紀錄。閱讀順序：

1. **`02-adapter-base-interface`** — PMAdapter ABC 怎麼來的
2. **`01-unified-task-schema`** — schema 為何長這樣
3. **`03-azure-devops-adapter`** — 第一個 adapter 實作過程
4. **`04-cli-sprint-entrypoint`** — CLI 怎麼把上面三個串起來

⚠️ **Spec 是寫成時的快照，不一定反映當前 code**。後續 refactor（parsers/ 拆出、PM_SYNC_PLATFORM selector）後架構有演進。**永遠以本 ARCHITECTURE.md + 實際 code 為準**，spec 當歷史紀錄看。

主要演進：
- `from_azure_payload` classmethod → `parse_azure(raw)` module function（spec 01 寫法已過時）
- CLI 直接 `import AzureDevOpsAdapter` → `ADAPTERS` registry + `_load_adapter()`（spec 04 寫法已過時）
- CLI 自己讀 env vars → adapter `from_env()` classmethod（spec 04 寫法已過時）
