# Contract Library

<!-- counts:start -->
当前有 **70 个 Skill Contract**（`contract_009`–`contract_078`），与 `skill_001`–`skill_070` 一一对应，共 120 条 policy 路径。
<!-- counts:end -->

每个 SkillNode 恰好对应一个 Contract（`contracts/contract_XXX/contract.json` 与 `CONTRACT.md`），运行时目录为 [skill_contracts.json](skill_contracts.json)，由 [`zeno_skills/skill_runtime.py`](../zeno_skills/skill_runtime.py) 的 `SkillContractRunner` 执行。Contract 记录：

- `inputs` / `outputs`：类型化槽位与实测输出；
- `noun_binding`：每个名词槽位在执行前计算的 GT 属性（抓取标注、所在支撑面、是否在冰箱或柜子里、盖子、离边缘距离等）；
- `precheck`：技能级和路径级前置条件，每条附带含义和 GT 来源，执行前在实时状态上评估；
- `policy_plan.paths`：按名词条件选择的路径，第一条条件全部成立的路径生效；每条路径顺序调用 policy、嵌套 Skill Contract 或循环，并可声明额外的前置/后置条件；
- `verifier`：技能级和路径级后置条件，执行后在 GT 状态上评估，全部成立才报告成功；
- `relations`：上一步、下一步、fallback、alternative 提示，失败时据此返回恢复候选，不自动执行。

`contract_001`–`contract_008` 是旧的八类 family Contract，仅供 [`tools/run_contracts.py`](../tools/run_contracts.py) 等兼容脚本使用，索引见 [legacy_family_catalog.json](legacy_family_catalog.json)。

目录由 `python tools/build_skill_library.py` 从 [`skill_library/definitions.py`](../skill_library/definitions.py) 生成，旧 family 记录由 `python tools/export_interface_libraries.py` 生成；两者都支持 `--check`。
