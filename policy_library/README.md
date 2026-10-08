# Low-level Policy Library

<!-- counts:start -->
当前有 **115 个公开 policy**（`policy_001`–`policy_115`），其中 7 个是只计算目标、不运动的规划 policy；全部被 70 个 Skill Contract 的路径覆盖。
<!-- counts:end -->

每个 `policies/<id>/` 目录包含 `policy.json` 和 `POLICY.md`：控制器范围、实际 `execute()` 参数、绑定类、验证状态，以及调用该 policy 的 Skill Contract 路径。运行时用 `PolicySuite(rig).policy_010.execute(...)` 调用，旧的描述性名称（如 `PolicySuite(rig).pick_top`）保留为别名，对照见 [docs/INTERFACE_IDS.md](../docs/INTERFACE_IDS.md)。

policy 只负责一个控制动作，自身的检查在控制器内部完成；上层可依赖的前后条件由 Contract 在调用前后用 GT 谓词评估。规划类 policy（`plan_*`）只计算目标而不运动，Contract 在运动 policy 前调用它们，并用 `#step.key` 传递结果。

[POLICY_COVERAGE.md](POLICY_COVERAGE.md) 列出每个 policy 被哪些 SkillNode 路径使用；检查器要求全部 policy 至少被一条路径覆盖。记录由 `python tools/export_interface_libraries.py` 生成，`--check` 检查是否过期。
