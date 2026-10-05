# Contract Library

当前上层接口包含 **42 个 Skill Contract**：`contract_009`–`contract_050`，分别对应 `skill_001`–`skill_042`。每个 `contracts/<id>/contract.json` 定义输入、`noun_bindings` 名词槽位与约束、前置条件、固定或按名词选择的 policy 路径、可测后置条件、verifier 和失败记录；`CONTRACT.md` 是逐项说明。机器可读主源为 [node_contracts.json](../zeno_skills/node_contracts.json)。

同一个 SkillNode/Contract 是**参数化能力**，不会在库里写死“苹果”或“碗”。例如 `skill_004` / `contract_012` 的 `object` 槽位可填场景实例 `apple`、`bowl_side_table` 或 `serving_tray`；Contract 查询 `rig.ann.objects` 与对应 asset 的 `grasps`，执行前分别选 `top_pinch → policy_010`、`round_rim → policy_011` 或 `rectangular_rim → policy_012`。薄物体还区分地面和支撑面抓法。`contract_011` 对抽屉、铰链门和有动力按钮的微波炉也按注释选择不同开门路径。选择是声明式 `policy_plan.paths[].when`，按顺序取第一条匹配路径；若名词无效或没有匹配路径，立即报错而不移动。

Contract 的 `noun_bindings` 还可要求“已由右手持有”、特定抓取类型、目标必须是容器或微波炉支撑面等。调用入口 `ContractRunner.run_bound("contract_012", object="apple")` 接收已 grounding 的场景实例 ID。返回的 `bound_nouns` 与 `selected_policy_path` 用于上层追踪；失败后不会自动切换到另一条路径，仍由上层根据新观察重规划。

一个 Contract 可以顺序调用多个 policy。例如 `contract_013` 在名词绑定为微波炉支撑面时选“插入 → 释放 → 撤手”三 policy 路径；专用的 `contract_022` 也采用这三步完成炉腔放置；`contract_045` 先扶正再放置并检查最终倾角；`contract_047` 还核对距离目标提示点的误差；`contract_048` 等待温度达到目标。已有多阶段控制器若已封装完整动作，只调用一次。

`contract_001`–`contract_008` 是旧的通用 family Contract，仍供兼容脚本调用，也供活跃 Contract 复用既有实测 verifier。它们在 [catalog.json](catalog.json) 中单列为 `legacy_family_contracts`。新上层只使用 `contracts` 数组的一对一条目。失败时 ContractRunner 停止后续 policy，返回已完成步骤、失败步骤及尽力读取的当前场景状态。

记录由 `python tools/export_interface_libraries.py` 导出，用 `--check` 验证。SkillNode 的条件化关系在 [relations.json](../skill_library/relations.json) 中，由上层按当前观察选择，不属于 Contract 内部 policy 计划。
