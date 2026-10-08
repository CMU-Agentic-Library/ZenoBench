# GPT / VLM → SkillNode JSON → ZenoBench 实验

## 研究问题

1. 只读动词 SkillNode 卡片（[vlm_skill_catalog.json](../../skill_library/vlm_skill_catalog.json)）时，GPT 能否输出合法的 schema 2 `skill_subgraph`？
2. 合法子图经各 Skill Contract（GT 前置条件 → 按名词选择 policy 路径 → GT 后置条件）在 Isaac Sim 执行后，`TaskEvaluator` 能否判定任务成功？失败发生在规划、grounding、前置条件、policy 还是后置条件？
3. 卡片加入前后条件（默认开启）、加入上一步/下一步/fallback/alternative 关系，或由 GPT 改写卡片名称和描述，是否改变结果？

## 协议

- 任务：`tasks/*/task.json` 中已构建的任务，每个任务一个全新 Isaac Sim 进程，不修改目标或资产。
- 输入：instruction、原始 goal、场景对象/支撑面/关节 ID、当前评估、每个 SkillNode 的卡片：`verb`、`noun`、`signature`、`description`、`use_when`、输入输出类型、前置/后置条件文本、各路径的名词条件；`--with-relations` 时再加关系。不传 policy 实现。场景以符号标注提供，本实验没有图像输入，是文本规划基线。
- 输出：`{"graph": {"schema_version": 2, "kind": "skill_subgraph", ...}}`。节点的 `skill` 是动词或 skill_id；参数为 `{"ref": 精确场景 ID}`、`{"value": 字面值}` 或 `{"from": "节点.输出"}`。[graph.py](../../skill_library/graph.py) 在动作前验证 DAG、类型、输出引用和场景绑定。
- 执行：[runtime.py](../../skill_library/runtime.py) 的 `run_subgraph` 逐个调用 Contract。失败立即停止并返回 `replan_request`（测得的谓词、可修复失败谓词的 fallback 候选、最新观测），交给下一轮；最多 3 轮。最终结果只由 `TaskEvaluator` 判断。
- 指标：子图有效率、各失败码数量（`PRECONDITION_FAILED`、`POLICY_FAILED`、`POSTCONDITION_FAILED` …）、最终成功数和进度、token 用量、wall/sim 时间。

## 运行

先设置 `OPENAI_API_KEY`（不要提交到仓库）。`OPENAI_MODEL` 可选，默认 `gpt-5`。

```bash
export ISAACLAB_PYTHON=/path/to/isaaclab/python
python tools/benchmark_gpt_skill_tasks.py --out runs/gpt_skill_experiment/cards
python tools/benchmark_gpt_skill_tasks.py --with-relations --out runs/gpt_skill_experiment/cards_relations
```

不调用 GPT、直接执行规划器产生的子图（物理对照）：

```bash
python -m skill_library.planner --task collect_fruits          # writes skill_library/plans/collect_fruits.skill_subgraph.json
$ISAACLAB_PYTHON tools/run_gpt_skill_task.py --task collect_fruits \
  --proposal-file skill_library/plans/collect_fruits.skill_subgraph.json --out runs/gpt_skill_experiment/collect_control
```

## 状态

本仓库此前用 50 个 v1 SkillNode 做过两次物理对照（`heat_breakfast_preloaded`、`collect_fruits`），那套接口已被动词库取代，结果不适用于当前卡片。当前库尚未运行 GPT rollout（需要 API key），**不能报告 GPT 成功率**。逐动词物理证据见 [STATUS.md](../../skill_library/verification/STATUS.md)，任务分解见 [planner](../../skill_library/planner.py) 输出。
