# SkillNode、Contract、Policy 的范围

- **SkillNode**：上层规划的一个有意义的状态变化，包含语义说明、类型化输入、前置/后置条件、调用接口、条件化关系及失败后重新观察的要求。
- **Contract**：恰好对应一个 SkillNode；接收已 grounding 的名词槽位，验证对象类别、标注与当前持有状态，按名词属性和实时状态在执行前选 policy 路径，并在最后检查每项对上层声明的状态变化。`contract_009`–`contract_058` 是当前活跃接口。
- **Low-level policy**：具体控制入口；同一 Contract 的一条路径可调用一个或多个 policy；一个 Contract 可声明多条条件化路径。`policy_001`–`policy_064` 是公开 ID。
- **兼容 family Contract**：`contract_001`–`contract_008` 是历史通用接口，活跃 Contract 可复用其物理 verifier；它们不再作为新 SkillNode 的一对一配对。
- **Task goal**：由 `TaskEvaluator` 最终判定。单个 SkillNode 的成功不等于任务成功。

每个 SkillNode 另有唯一动词＋名词的 `action_predicate`；动作成功后才随测得的状态事实一起返回。共享的 `requires`/`achieves` 表示可组合的物理状态，不能为了让名称唯一而拆散。见 [动作谓词表](ACTION_PREDICATES.md) 与 [目标映射](goal_predicates.json)。

[relations.json](relations.json) 只提供有条件的规划提示；`depends_on` 是 VLM 为当前任务提出的具体依赖。Graph Manager 校验 ID、参数和 DAG；运行时还须看 live observation。失败时停止本 Contract 的剩余 policy，记录已完成步骤、失败步骤和可读取的动作后状态。上层据此重试或换路，Contract 不自动调用替代 Skill。

前置条件标记为 `contract_precheck` 的项目会在执行前检查；`policy_attempt` 由控制器在尝试时确认，不能当成静态保证。后置条件只有被 ContractRunner 测量通过才可宣称。任务审计中的“覆盖”指 10 个任务全部 42 条目标子句可表达或可终态检验；不承诺全部场景的物理成功。`skill_015`、`skill_020`–`skill_022` 仍无配对 Contract 的物理通过记录；`skill_040` 的温度等待和 `skill_038/039` 的区域放置已有代表性实跑，但其他物体和更长搬运路径仍需验证。
