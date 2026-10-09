# Contract Library

<!-- counts:start -->
当前有 **70 个 Skill Contract**（`contract_009`–`contract_078`），按动词调用，共 120 条 policy 路径。
<!-- counts:end -->

Contract 按动词调用（`contracts/contract_XXX/contract.json` 与 `CONTRACT.md`）；目前每个动词有一个 Contract，但 Skill 与 Contract 不强制一一对应，Contract 之间也没有关系。运行时目录为 [skill_contracts.json](skill_contracts.json)，由 [`zeno_skills/skill_runtime.py`](../zeno_skills/skill_runtime.py) 的 `SkillContractRunner` 执行。Contract 记录：

- `inputs` / `outputs`：类型化槽位与实测输出；
- `noun_binding`：每个名词槽位在执行前计算的 GT 属性（抓取标注、所在支撑面、是否在冰箱或柜子里、盖子、离边缘距离等）；
- `precheck`：技能级和路径级前置条件，每条附带含义和 GT 来源，执行前在实时状态上评估；
- `policy_plan.paths`：按名词条件选择的路径，第一条条件全部成立的路径生效，调用方不能指定；每条路径顺序调用 policy、嵌套 Skill Contract 或循环，并可声明额外的前置/后置条件；
- `verifier`：技能级和路径级后置条件，执行后在 GT 状态上评估，全部成立才报告成功。

`contract_001`–`contract_008` 是旧的八类 family Contract（由调用方指定路线，待删除），仅供 [`tools/run_contracts.py`](../tools/run_contracts.py) 等兼容脚本使用，索引见 [legacy_family_catalog.json](legacy_family_catalog.json)。

目录由 `python tools/build_skill_library.py` 从 [`skill_library/definitions.py`](../skill_library/definitions.py) 生成，旧 family 记录由 `python tools/export_interface_libraries.py` 生成；两者都支持 `--check`。
