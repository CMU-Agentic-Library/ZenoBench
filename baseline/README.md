# baseline/

SHIFT 论文要跑的规划器 baseline。计划见 [`docs/guides/BASELINE_PLAN_zh.md`](../docs/guides/BASELINE_PLAN_zh.md)。

本分支在 Isaac Sim 6.0.0.1 上独立比较三个本地 VLM。表中列出已完成的局数、主实验、观测和提示消融，以及同一布局上的脚本参考结果。[本地 VLM 对比表](results/local_v6_sim6.md) · [实验设置和逐局证据](LOCAL_COMPARISON_zh.md)

| 文件 / 目录 | 方法 | 状态 |
|---|---|---|
| `open_loop.py` `OpenLoop` | 1 VLM open-loop：开头一次查询写出整份调用列表，照着执行，第一次失败或列表用完就停 | 已写，离线测试通过 |
| `code_policy.py` `CodeAsPolicies` | 3 Code-as-Policies：VLM 写一段 Python，每个技能是一个函数（技能本身不变）；程序在线程里跑，每调一次技能暂停交给环境；出错时可重写一次程序 | 已写，离线测试通过 |
| `sayplan.py` `SayPlan` | 4 SayPlan 式：折叠的场景图（房间 → 家具 → 台面，物体看到才加入）；先展开节点搜索，再写剩余计划；失败或看到新物体时重规划；计划里有未知技能或没见过的物体会退回改一次 | 已写，离线测试通过 |
| `react.py` `ReAct` | 2 ReAct / tool-use：每步把指令、观察和历史交给 VLM，简短思考后给一个调用或 finish | 已写，离线测试通过，未在仿真里跑过 |
| `react.py` `ReActHint` | 消融：同上，system prompt 多一句"不可用时可以用合理替代，但能用原物就不换" | 已写 |
| `react.py` `ReAct` + `--profile sticky/privileged` | 上界：同一个 ReAct，额外看到所有任务物体及位置（GT，仍匿名），不给目标状态 | 已写（profile 在 `episode/profiles/sticky/privileged.yaml`） |
| `human.py` `Human` | 人类参考：人在终端里看到和 VLM 完全一样的文字和图片路径，输入调用 | 已写 |
| `graph_manager/` | 5 Graph Manager：子目标 + 每个子目标一个 skill DAG，子目标边界或失败时由 VLM 决定 continue / 重规划 / finish | submodule（`b766b66`），待接入本仓库的技能库和统一设置 |

共用组件：`base.py`（技能菜单、调用历史、token 统计）、`vlm.py`（四家模型一个 `chat()`）、`prompt.py`（技能说明、观察、历史的文字）、`parse.py`（从回答里取出调用）。

## 运行（模型和仿真分开，同 Graph Manager）

```bash
# 1. 仿真机：env_service（Isaac 环境）
$ISAACLAB_PYTHON -m env_service.server --port 8800 --max-sims 2 \
    --catalog benchmark/v6/tasks.json=sticky/benchmark

# 2. Qwen（需要时）：vLLM 服务，端口 8001，和 Graph Manager 共用
bash baseline/serve_qwen.sh

# 3. 规划器侧：不需要 Isaac，用 .venvs/shift-planner（最新 anthropic / openai）
PY=../.venvs/shift-planner/bin/python
$PY -m baseline.check_models                       # qwen3.5-4b / claude-opus-5-5 / gpt-6 是否可用
$PY -m baseline.run_http --server http://localhost:8800 --model claude-opus-5-5 \
    --policy baseline.react:ReAct --batch benchmark/v6/batches/category_control.json --limit 3
#   --policy baseline.open_loop:OpenLoop | baseline.code_policy:CodeAsPolicies | baseline.sayplan:SayPlan
#   消融 baseline.react:ReActHint；上界 --profile sticky/privileged；单个 episode：--task T --variant V --seed 10
#   输出 baseline/runs/<方法>@<模型>/<任务>/s<seed>_<variant>/，已有 result.json 的会跳过（可断点续跑）

$PY -m pytest baseline/tests -q                    # 离线测试：假模型、假观察、假 HTTP
```

- Qwen 服务（11-23 在本机测通）：显存占 0.60（约 15.8 GB），并发上限 16；系统 nvcc 是 CUDA 12.2，编不了 FlashInfer 的采样 kernel，脚本里关了 FlashInfer 采样（`VLLM_USE_FLASHINFER_SAMPLER=0`）。启动约 2 分钟。
- Qwen 思考模式：默认开。一步 ReAct 约 4k 输出 token、40 s；`SHIFT_QWEN_THINKING=0` 关掉后约 100 token、1 s。论文用哪种还没定。
- 环境（都在 `physical_harnessing/` 下，仓库外）：`.venvs/vllm-qwen`（vLLM 0.32.0）、`.venvs/shift-planner`（规划器）、`models/Qwen3.5-4B`（权重）。
- key：`cp baseline/.env.example baseline/.env` 后自己填（已 gitignore），或在 shell 里 export。
- 调试也可以在进程内跑：`SHIFT_MODEL=... $ISAACLAB_PYTHON benchmark/run_episode.py --planner recovery --policy baseline.react:ReAct --profile sticky/benchmark ...`。isaaclab 环境里装的是旧版 SDK（anthropic 0.85、openai 1.109）：新版要求 typing_extensions>=4.14，和 Isaac Sim 锁的 4.12.2 / idna 3.10 冲突，不要 `pip install -U`。人类参考只能用这条路径（要终端）。

- 设置都从环境变量或 `baseline/.env` 读（runner 不给 planner 传参数）：`SHIFT_MODEL`（默认 `claude-opus-5-5`；`claude-*` / `gpt-*` / `gemini-*` / 其他走本地 vLLM），`SHIFT_MAX_CALLS`（默认 60）。`SHIFT_REVEAL`（默认 `off`）是物体注册表的消融开关：`objects` 时，观测里附上 robot 已经看到过的每种物体的分类、用途、材质和尺寸；`full` 时再给每个已知支撑面附上用途和净空。只给种类层面的事实，不给哪个实例被占用，也不给任务要求和替代判断（`baseline/reveal.py`），所选模式记在 `result.json` 的 planner 里。主结果用 `off`。Graph Manager 子模块还没有接这个开关。论文用 Qwen3.5-4B、Claude Opus 5.5、GPT-6 三个模型（Gemini 不跑）；GPT-6 的模型 id 暂写 `gpt-6`，有 key 后用 `check_models` 确认，可用 `SHIFT_GPT_MODEL` 改。
- 四家模型拿到完全相同的文字和 JSON 回答格式，不用各家的原生工具调用。每次请求都是无状态的一问一答，历史由 planner 自己写进 prompt（最近 8 步完整，更早的压成一行）。
- 回答解析不了时再问一次，最多 2 次；这算 VLM 查询，不算技能调用。
- `calls.jsonl` 每行多了 `planner_usage`（这一步的 token），`result.json` 多了 `planner_summary`（整局的 VLM 查询数、token、停止原因，含最后 finish 那一问）。
- 人类 planner 会提前拦住拼错的技能名，不浪费调用；VLM 拼错会被环境拒绝并计入预算。

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
4. **模型后端**：现在是本地 vLLM 的 Qwen3.5-4B（`examples/vllm-qwen3.5-4b.compose.yml`）；要加 Claude Opus 5.5、GPT-6。
