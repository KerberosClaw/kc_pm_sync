# Azure DevOps Adapter

> **English summary:** Concrete `AzureDevOpsAdapter(PMAdapter)` that fetches sprint items and individual work items by shelling out to the `az` CLI. Plus runtime prerequisite check, README Prerequisites section, and mocked subprocess tests.

## 六要素摘要（Task Prompt Schema）

- **目標（Goal）：** 寫一個可用的 Azure DevOps adapter，透過 `az` CLI 拿真實 sprint / work item 資料，餵給 `UnifiedTask.from_azure_payload()`。kc_pm_sync 首個「能真的抓資料」的 adapter。
- **範圍（Scope）：**
  - `adapters/azure_devops.py`（新增）
  - `tests/test_azure_adapter.py`（新增）
  - `README.md`（修改，加 Prerequisites 章節）
- **輸入（Inputs）：**
  - `adapters.base.PMAdapter`（spec 02）
  - `models.task.UnifiedTask`（spec 01）
  - `subprocess`、`shutil`、`json` stdlib
  - 系統裝有 `az` CLI（runtime 檢查）
  - 環境變數 `AZDO_ORG_URL` / `AZDO_PROJECT` / `AZDO_PAT`（CLI 呼叫時用）
- **輸出（Outputs）：**
  - `AzureDevOpsAdapter` class 實作兩個 abstract 方法
  - `__init__` runtime check（`az` 不存在時明確報錯 + 裝機指引）
  - README 新增 Prerequisites 章節（az CLI 裝設、env var、PAT scope）
  - mocked subprocess tests 3-4 個
- **驗收（Acceptance）：** 見 AC-1~8
- **邊界（Boundaries）：** 不 live call Azure API（全 mocked）、不做 push / update、不做 retry / batch 優化、不做 OAuth device code flow

## 背景

Spec 01 + 02 鋪好 schema + 介面。本 spec 是第一個**真的會去拉資料**的 adapter — `az` CLI subprocess route，pragmatic 取向：

- smoke test（2026-04-20 via (a separate private repo)）已驗證 `az boards work-item show` + `az boards query` 回傳格式跟 REST API 一致
- `UnifiedTask.from_azure_payload()` 直接可吃
- auth / retry / error mapping 交給 `az` 本身處理，不重造輪子

依賴代價：user 需裝 `az` CLI（brew / MS installer），PAT 走 env var。README 會有一段 Prerequisites 引導。

## 驗收條件

- [ ] **AC-1**：`AzureDevOpsAdapter` 繼承 `PMAdapter`，實作兩個 `@abstractmethod`（`list_sprint_items`、`get_item`）。`__init__(org_url, project, pat)` 儲存為 instance 屬性。
- [ ] **AC-2**：`__init__` 做 runtime check：`shutil.which("az")` 為 `None` 時 raise `RuntimeError`，訊息含三平台安裝指引（macOS / Linux / Windows）。
- [ ] **AC-3**：`list_sprint_items(sprint_id)` 流程：
  - 把 `"sprint-12"` 短形式轉 native（初版規則：`f"{self.project}\\Sprint {n}"`，其中 `n = sprint_id.rsplit('-', 1)[1]`）
  - 用 WIQL 查該 `IterationPath` 的所有 work item id
  - 對每個 id 再呼叫 `get_item(id)` 組裝成 `list[UnifiedTask]`
- [ ] **AC-4**：`get_item(item_id)` 直接 `az boards work-item show --id <n> -o json`，把 JSON 過 `UnifiedTask.from_azure_payload()` 回傳。
- [ ] **AC-5**：所有 `az` 呼叫都走 `self._az(*args) -> dict` private helper，集中管理：
  - `--organization` / `--project` / `-o json` flag 統一加
  - PAT 透過 `AZURE_DEVOPS_EXT_PAT` env var 傳入 subprocess（不寫命令列，避免 log 洩）
  - `subprocess.run(..., check=True, capture_output=True, text=True)`
- [ ] **AC-6**：`tests/test_azure_adapter.py` 以 `unittest.mock.patch('subprocess.run')` 塞假 JSON 回傳值，**不打 live API**。至少涵蓋：
  - `test_init_raises_when_az_missing` — `patch('shutil.which', return_value=None)` → 實例化 raise `RuntimeError`，訊息含 "az CLI" / "brew install"
  - `test_get_item_maps_azure_payload` — mock subprocess 回已有 fixture（`work_item_670.json`），assert 回傳 `UnifiedTask.id == 670` 且 `state == "In Progress"`
  - `test_list_sprint_items_calls_wiql_then_fetches_each` — mock 兩類 subprocess call（wiql 回 id list、show 回 fixture），assert 最後 list 長度 + 每個元素是 `UnifiedTask`
- [ ] **AC-7**：`README.md` 新增「Prerequisites」章節（頂層、顯眼位置），包含：
  - 安裝 `az` CLI 的連結 + 各 OS 命令
  - 三個 env var 的 export 範例
  - 所需 PAT scope（`Work Items (Read)`）
  - 未來其他 adapter 可能有其他依賴的提示
- [ ] **AC-8**：跑 `python -m pytest tests/ -v` 全綠（spec 01 + 02 + 03 測試），無 regression。

## 不做的事

- **不 live call Azure**（全 mock）；live call 留給 spec 04 CLI 的「端到端 smoke test」那一次
- **不做 push / update / close / delete**（未來 spec）
- **不做 retry / rate limiting**（`az` 自己會處理一般 transient error）
- **不做批次 fetch（`/_apis/wit/workitemsbatch`）**：N+1 對 MVP 足夠，100 筆 × 100ms = 10s 可接受；真慢再優化
- **不做 OAuth interactive / device code flow**：只支援 PAT
- **不做 pagination**：MVP 單 sprint < 200 筆，WIQL 預設 return top 20000 夠用
- **不做 custom exception class**：讓 `subprocess.CalledProcessError` 自然冒出，包裝留 future spec
- **不處理 sprint_id 短名轉 native 的複雜 case**（多階層 iteration、非 `Sprint N` 命名 convention）：初版 hard-code convention，邊界 case 補 fixture + future spec
- **不做 az login 檢查**：假設 user 已經 `az login` 或 `AZURE_DEVOPS_EXT_PAT` 環境變數準備好

## 依賴

- **Spec 01（01-unified-task-schema）**：`UnifiedTask.from_azure_payload()` 必須存在
- **Spec 02（02-adapter-base-interface）**：`PMAdapter` ABC 必須存在
- **系統工具**：`az` CLI 2.50+ 裝好且在 PATH 上
- **Python**：3.9+（接 spec 01/02 的 runtime）
- **測試**：pytest（已裝）+ `unittest.mock` stdlib
- **環境變數（runtime 用，測試不需）**：`AZDO_ORG_URL`、`AZDO_PROJECT`、`AZDO_PAT`
