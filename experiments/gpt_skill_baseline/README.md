# GPT → SkillNode JSON → ZenoBench 实验

## 研究问题

1. 50 个 SkillNode 能否**表达** ZenoBench 目前 10 个任务的目标？静态审计为 10/10 任务、42/42 目标子句提供了候选路径，但这只是接口表达覆盖。
2. GPT 只读全部 50 个 `name`、`description` 和必需的参数类型，能否输出合法的 `skill_subgraph` JSON？
3. 合法子图经现有 Contract 和底层 policy 在 Isaac Sim 执行后，最终 `TaskEvaluator` 能否判定任务成功？失败发生在规划、grounding、Contract，还是底层控制？
4. 给 GPT 增加条件化 Skill 关系提示，或让 GPT 基于现有 Contract 重写部分 Skill 的 name/description，是否改变结果？

## 固定实验协议

- 任务：`tasks/*/task.json` 中的全部 8 个已构建任务，每个任务一个全新 Isaac Sim 进程，不修改任务目标或资产。
- 基线输入：任务 instruction、原始 goal、场景内的对象/相关支撑面/关节 ID、当前任务评估、50 个公开 Skill 的 `skill_id`、`name`、`description`、参数名和类型。**不传 Contract policy 计划、详细 SKILL.md 或已有任务蓝图**。这样测的是直接读 Skill 简介后规划。场景以符号标注提供；本实验没有图像输入，因此是 GPT 文本规划基线，不是视觉 VLM 基线。
- 模型输出：一个 `{"graph": {"schema_version":1,"kind":"skill_subgraph","subgoal_id":"...","nodes":[...]}}`。`args` 的 `ref` 必须是场景词表里的**精确实例 ID**；数值放在 `value`。不使用隐式名词解析。Graph Manager 在动作前验证 DAG、Skill ID、类型和标注绑定。
- 执行：每个节点调用一对一的现有 Contract；Contract 自己选 policy 路径并测量后置条件。失败立即停止当前子图，给 GPT 最新状态；最多 3 轮。最终结果只由 `TaskEvaluator` 判断。
- 指标：JSON/子图有效率、Contract 失败数、10 个任务的最终成功数和进度、失败节点/错误码、GPT token 用量及 wall/sim 时间。`runs/.../result.json` 保留每轮模型输入、图、编译后的 Contract 调用及执行观测。`summary.json` 区分模型规划失败和物理执行失败。

## 运行

先在运行环境中设置 `OPENAI_API_KEY`（不要把密钥提交到仓库或发在聊天里）。`OPENAI_MODEL` 可选；默认 `gpt-5`。`ISAACLAB_PYTHON` 指向可启动 Isaac Sim 的 Python。下例是这台机器当前找到的 launcher：

```bash
cd zeno-house
export ISAACLAB_PYTHON=/home/all/miniforge3/envs/isaaclab/bin/python
python tools/benchmark_gpt_skill_tasks.py --out runs/gpt_skill_experiment/names_only
python tools/benchmark_gpt_skill_tasks.py --with-relations --out runs/gpt_skill_experiment/with_relations
python tools/benchmark_gpt_skill_tasks.py --with-predicates --out runs/gpt_skill_experiment/with_predicates
```

基于现有 Contract 让 GPT 重写 6 个 Skill 的 **name/description**，保留其 ID、Contract 配对、输入、policy 和 verifier，再用这些卡片跑同一协议：

```bash
python tools/propose_gpt_skill_cards.py --out runs/gpt_skill_experiment/gpt_authored_cards.json
python tools/benchmark_gpt_skill_tasks.py \
  --card-overrides runs/gpt_skill_experiment/gpt_authored_cards.json \
  --out runs/gpt_skill_experiment/gpt_authored_names
```

若要先验证 JSON 到 Contract 的物理执行链路，不调用 GPT：

```bash
$ISAACLAB_PYTHON tools/run_gpt_skill_task.py --task heat_breakfast_preloaded \
  --proposal-file skill_library/examples/heat_preloaded.skill_subgraph.json \
  --bindings-file skill_library/examples/heat_preloaded.bindings.json \
  --out runs/gpt_skill_experiment/preloaded_control
```

## 已得到的结果

- `heat_breakfast_preloaded` **物理对照通过**：两个节点 `skill_010 → skill_040` 的 Contract 都成功，进度从 0.667 到 1.0，最终任务成功。记录在 `runs/gpt_skill_experiment/preloaded_control/result.json`。
- `collect_fruits` **物理对照通过**：四节点 `skill_004 → skill_006 → skill_004 → skill_006` 的 Contract 都成功，进度从 0.6 到 1.0，最终任务成功；模拟时间 193.2 秒。记录在 `runs/gpt_skill_experiment/collect_fruits_control/result.json`。
- 这次会话的实验进程没有 `OPENAI_API_KEY`。`propose_gpt_skill_cards.py` 没有生成 GPT 卡片；`benchmark_gpt_skill_tasks.py` 没有启动 GPT 任务 rollout，状态写入 `runs/gpt_skill_experiment/batch_attempt/summary.json`。**不能把物理对照记成 GPT 成功率。**

当前 Skill 库的逐节点物理证据见 [STATUS.md](../../skill_library/verification/STATUS.md)。其中 46/50 有代表性物理通过，4 个尚未通过或被准备动作阻塞。完整任务可能触发此前未测的名词、路线和更长时间的抓持，因此 42/42 目标表达覆盖不能推论 10/10 任务成功。
