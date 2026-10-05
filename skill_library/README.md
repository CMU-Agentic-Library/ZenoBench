# ZenoBench Agent SkillNode Library

上层可选择 **42 个 SkillNode**（`skill_001`–`skill_042`）；每个节点恰好对应一个可执行 Contract（`contract_009`–`contract_050`）。节点目录采用 Agent Skill 风格：`SKILL.md` 有名称、用途、参数、前置条件、预期状态变化、调用方式、内部 policy 计划、相关 Skill、失败处理与适用边界；同目录的 `skill.json` 供程序读取。

Contract 是该节点的执行与验证边界。上层 SkillNode 保留抽象的 `object_ref`、`support_ref` 等名词槽位；场景实例 ID 由 Graph Manager grounding 后填入配对 Contract。Contract 对已填名词做标注与状态检查，可在执行前按名词属性选一个 policy 路径，每条路径再顺序组合一个或多个底层 policy。底层现有 64 个公开 policy 入口；不是每个控制阶段都要成为上层节点。任务目标仍由 `TaskEvaluator` 在整条子图执行后判断。

## 能力分组

| 范围 | SkillNode | 上层可规划的变化 |
| --- | --- | --- |
| 底盘、姿态、携物 | `001–002`, `011–013`, `021`, `031–034`, `041–042` | 导航、调整姿态、抬高携物、后退让位 |
| 门与电器 | `003`, `007`, `009–010`, `022–026`, `040` | 手柄或动力门开关、按钮按压、等待温度达标 |
| 抓取与准备 | `004`, `015–018`, `020`, `027–029`, `035–036` | 常规、边缘、杯柄、腔体、地面抓取；制造可抓边缘及扶正 |
| 放置与推动 | `005–006`, `008`, `014`, `019`, `030`, `037–039` | 支撑面、容器、炉腔、薄物边缘、指定区域放置；推动 |

新增节点主要补齐任务谓词：`skill_040` 验证食品达到指定温度；`skill_037` 和 `skill_039` 在放下后验证直立；`skill_038` 和 `skill_039` 验证与同一个放置提示点的距离。薄物体可以先用 `skill_035` 制造安全悬边，再尝试 `skill_016` 边缘抓取。每项的物理适用条件和验证状态见其 `SKILL.md`。

## 与上层如何对接

VLM 根据任务目标及当前观察生成当前子目标的 `skill_subgraph`：每个节点只有 `id`、`skill_id`、`args`、`depends_on`。对象引用用 `{"ref":"the apple"}`；数值用 `{"value":...}`。Grounding 模块另提供 ref 到唯一场景实例 ID 的绑定。见 [四节点水果示例](examples/collect_fruits.skill_subgraph.json)、[加热示例](examples/heat_preloaded.skill_subgraph.json) 和 [子图 Schema](subgraph.schema.json)。

[关系目录](relations.json) 提供 38 条**有条件的**准备、使能、后续、替代和恢复提示。例如“微波炉关门 → 启动加热 → 等待温度达标”，以及“薄物制造悬边 → 边缘抓取”。这些关系帮助 VLM 提出 `depends_on`，不是固定的全局任务图；Graph Manager 必须根据实时状态、参数类型和任务目标验证，再按需执行。失败后返回测得的部分状态，上层重新规划；关系和 fallback 不会自动触发其他动作。

上层获取公开目录和失败后的恢复候选可用 [planner_handoff.py](planner_handoff.py)；请求字段、恢复循环和当前边界见 [上层对接说明](UPPER_LAYER_HANDOFF.md)。

Graph Manager 在 [graph.py](graph.py) 中检查 ID、参数、依赖 DAG、场景绑定和 SkillNode／Contract 一对一关系，然后编译为 `ContractRunner.run(contract_id, "compose", *args)`。直接调用时也可用 `ContractRunner.run_bound("contract_012", object="apple")` 按名词槽位填写。选中的路径与绑定属性写入结果的 `selected_policy_path`、`bound_nouns`；无匹配路径时不执行 policy。已有 rig 时使用 `skill_library.runtime.run_subgraph(rig, graph, bindings)`。

## 任务覆盖的含义

[逐任务蓝图](TASK_PLANS.md) 给出条件化动作链；[逐任务审计](task_coverage.json) 对照 `tasks/*/task.json`：8 个任务的 **32 条目标子句**均有可表达的动作路径或终态检查，涉及 `inside`、`on`、直立、成组靠近、加热、关门和 `not_dropped`。例如 `near` 是**成组两两距离**；单次 `skill_038` 只验证一个物体与提示点的距离。上层应选共同提示点，把每个物体放在任务阈值一半以内，再用 `TaskEvaluator` 核对整个组。

这是**目标表达覆盖**，不等于所有随机场景都物理成功。`not_dropped` 和 `closed: all` 是终态条件，分别要靠各动作维持或逐门修复，并由任务评估器最终核对。可达性、抓持稳定性、候选物是否存在等仍是运行时问题；地面容器翻倒后的复位尚无独立实跑保证。

## 生成与检查

```bash
python -m skill_library.graph --graph skill_library/examples/collect_fruits.skill_subgraph.json \
  --bindings skill_library/examples/collect_fruits.bindings.json \
  --ann tasks/collect_fruits/annotation.json --format upper
PYTHONDONTWRITEBYTECODE=1 python -m pytest tests -q
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skill_library/tests -q
PYTHONDONTWRITEBYTECODE=1 python tools/export_agent_skill_docs.py --check
PYTHONDONTWRITEBYTECODE=1 python tools/export_interface_libraries.py --check
PYTHONDONTWRITEBYTECODE=1 python tools/audit_skill_task_coverage.py --check
```

Contract 明细见 [Contract Library](../contract_library/README.md)，policy 明细见 [Policy Library](../policy_library/README.md)，逐技能实跑状态见 [42 节点验证清单](verification/STATUS.md)，未通过的四项见 [物理测试发现](verification/FINDINGS.md)，完整成功与失败轨迹见 [验证摘要](verification/node_contract_smoke.json)。其中温度达到 63.6°C；区域放置误差约 2.1 cm；另有早餐碗搬运滑脱案例。
