# 上层 VLM 如何组合 SkillNode 和处理失败

## 当前能做什么

42 个 SkillNode 是可复用的状态变化。上层可反复使用同一个 `skill_id`，为当前任务填不同名词，输出一个 `skill_subgraph`；`depends_on` 表达这次任务的先后关系。例如水果收纳是 `skill_004` 抓苹果 → `skill_006` 放入篮子 → 再抓橙子 → 再放入同一篮子。Graph Manager 会检查 Skill ID、参数类型、依赖 DAG 和 ref 到场景实例的绑定，然后把每个节点编译成唯一配对的 Contract 调用。

[relations.json](relations.json) 目前有 38 条关系：15 条 `enables`、5 条 `preparation`、7 条 `follows`、9 条 `alternative`、2 条 `recovery`。每条都有 `when` 和 `reason`。这是一组**条件提示**，不是一张必须照搬的任务图。例如移动抓取失败后，只有物体已经静止、仍可达且右手空，才考虑 `skill_018 → skill_004`。`skill_006 → skill_005` 的替代还要求任务本身允许把 `inside` 目标改成 `on`；单纯放到桌上不能算完成“放进篮子”。

Contract 内还有按已绑定名词和状态选择的 policy 路径。这与上层 Skill 之间的 alternative 是两层选择：前者在**同一个 Contract 内**选具体控制路线；后者由 VLM 根据新观察提出**新的 SkillNode**。

## 交给上层的接口

```python
from skill_library.planner_handoff import planner_catalog, replan_request
from skill_library.graph import compile_grounded_nodes
from skill_library.runtime import run_grounded_nodes

catalog = planner_catalog()  # 42 个公开 Skill 摘要 + 38 条条件关系
# 上层 VLM 根据 goal、最新 observation、catalog 生成一个 skill_subgraph JSON。
calls = compile_grounded_nodes(graph, bindings, annotation)
result = run_grounded_nodes(rig, calls)

if result["status"] == "failed":
    request = replan_request(goal, graph, result, bindings)
    # 将 request 和 catalog 交回 VLM，生成新的子图与必要的新 bindings。
    # 新子图仍须调用 compile_grounded_nodes 校验，再执行。
```

`replan_request` 包括成功且已验证的节点、失败节点及错误、尚未执行的节点、动作后的真实观察、当前 bindings、来自关系库的 `alternative/recovery` 和该 Skill 的 `fallback_hints`。候选 Skill 附带输入、前置/后置条件及 `availability`，使上层知道哪些路线仍是实验性。它只打包候选，不调用下一步动作。

上层循环应遵守以下判定：

1. 只把 Contract 报告中通过的谓词当成已完成；失败动作可能已经移动物体或底盘，以 `last_observation` 为准。
2. 对候选关系逐条检查 `when`、当前任务目标和名词类别；原参数不一定能直接传给替代 Skill。例如 `skill_018` 的 `base_path` 不属于 `skill_004`。
3. 用新的 `skill_subgraph` 表达剩余目标；先检查 `depends_on` 和 grounding，再执行。若当前条件不支持候选，重新导航、换任务允许的对象，或者报告受阻。
4. 每个子图完成后，用任务评估器核对**整个任务**。单个 Contract 成功不能代替任务成功。

一个上层恢复示例：`skill_018` 移动抓苹果失败，执行结果表明苹果静止在桌上、右手空且可达。VLM 可提出 `skill_004` 抓同一个苹果，再用 `skill_006` 放进原来的篮子；它要保留 `inside(apple, basket)` 目标。若苹果被撞到地面或右手已抓住别的物体，则先重新观察并选择不同计划，不能直接套用这条恢复链。

## 当前边界

仓库提供**目录、关系提示、子图校验、Contract 执行结果和失败交接**；尚未集成某个具体 VLM 的调用、提示词评测或自动多轮重规划器。因此“可以让上层 VLM 推理和做 fallback”的准确含义是：接口已经能支持上层实现这个闭环，不能说当前系统会自主选对 fallback。Graph Manager 的静态校验也无法证明物理前置条件成立；Contract 和实时观测负责运行时检查。42 个节点中 38 个有代表性物理通过记录，4 个仍有物理阻碍，见 [验证状态](verification/STATUS.md)。
