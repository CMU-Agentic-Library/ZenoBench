# baseline/

SHIFT 论文要跑的规划器 baseline。计划见 [`docs/guides/BASELINE_PLAN_zh.md`](../docs/guides/BASELINE_PLAN_zh.md)。

| 目录 / 模块 | 方法 | 状态 |
|---|---|---|
| `graph_manager/` | Graph Manager：子目标 + 每个子目标一个 skill DAG，子目标边界或失败时由 VLM 决定 continue / 重规划 / finish | submodule（`b766b66`），待接入本仓库的技能库和统一设置 |
| （待写） | VLM open-loop、ReAct / tool-use、Code-as-Policies、SayPlan 式 | 见计划第 5 节 |

## graph_manager/

- git submodule，指向 <https://github.com/CMU-Agentic-Library/Graph_manager>，当前固定在 `main` 的 `b766b66`（2026-10-29）。克隆本仓库后执行 `git submodule update --init baseline/graph_manager`。
- 下面要改的地方提交到 Graph_manager 仓库（或其 fork），再在本仓库更新 submodule 指针：`git -C baseline/graph_manager pull` 后 `git add baseline/graph_manager`。
- 独立的 Python 包（`pyproject.toml`，Python ≥ 3.12，依赖 `deepseek-harness-sdk==0.1.5rc1`）。安装和运行方法见 `graph_manager/README.md`：

  ```bash
  cd baseline/graph_manager
  uv sync --locked --extra dev
  .venv/bin/python -m unittest discover -s tests
  ```

- 运行方式：`graph-manager-run` 通过 env_service HTTP 接口（`python -m env_service.server --port 8800`）驱动 Isaac Sim。

### 和本仓库对齐前要改的地方

1. **技能库**：`graph_manager/vendor/zenobench/` 是旧快照（70 个技能，ZenoBench `eb4b3f0`），`graph-manager-run` 每次运行前还会从 git 拉最新 ZenoBench（`adapters/zenobench_sync.py`）。改为直接读本仓库的 `skill_library/`，保证和冻结 commit 一致。
2. **调用预算**：已统一为 60。env_service 按请求的 profile 定预算（`sticky/benchmark` = 60；兜底默认 11-23 从 40 改为 60）。启动服务要加 `--catalog benchmark/v6/tasks.json=sticky/benchmark`（默认 catalog 不含 v6），请求里写 `profile: sticky/benchmark`，不要用 `gt`（40 次、给 GT 信息）。
3. **观察**：env_service 返回物体位置和目标状态，`sticky/benchmark` 不给；要保证 Graph Manager 看到的和其他 baseline 一样。
4. **模型后端**：现在是本地 vLLM 的 Qwen3.5-4B（`examples/vllm-qwen3.5-4b.compose.yml`）；要加 Claude Opus 5.5、GPT、Gemini。
