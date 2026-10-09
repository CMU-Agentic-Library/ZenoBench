# 环境服务化：待做修改与待定事项

更新于 2026-10-08。本文列出把本仓库改造成 Isaac Sim 环境服务时，已经确定要做但尚未完成的修改，以及仍待决定的问题。

## 目标

本仓库是基于 Isaac Sim 的环境服务。上级 planner 不在本仓库内，它通过接口完成三件事：

- 获取任务描述、图片观察、场景物件列表，以及每个 goal 子句当前的真假；
- 读取与本库 skill 同步的仓库（同步机制暂不实现），按 `skill_library/skills/*/SKILL.md` 中写明的方式发送 contract 调用 `{"contract": "<动词>", "args": {...}}`；
- 查询任务是否完成。

本库不做规划，也不推断 fallback。

## 已确定的设计

| 问题 | 决定 |
|---|---|
| contract 名字 | 用动词，70 个动词互不重复 |
| planner 能否指定 policy 路径 | 不能，路径由 contract 按绑定的名词自动选择；SKILL.md 不出现路径和 policy 编号 |
| 物件信息 | 现阶段只给场景中有哪些物件 |
| 进度 | 每个 goal 子句的真假 |
| 失败时 | 只返回测得的谓词，不给 fallback 候选，本地也不自动修复或重试 |
| contract 之间的关系 | 没有 sequence / fallback / alternative；skill 与 contract 不强制一一对应 |
| 任务来源 | `skill_library/tasks.json`（35 个任务，goal 为 GT 谓词） |

以上决定已经体现在代码和文档中：planner、subgraph 执行器、GPT 实验代码、relations 及其检查、runtime 的 recovery 与嵌套 repair 都已删除；SKILL.md 已补上调用格式，去掉了 policy 路径、Verifier 和 GT 来源。

## 待做修改

### 1. 服务接口（尚未实现）

| 接口 | 输入 | 返回 |
|---|---|---|
| `initial_task` | `task_id`（来自 `tasks.json`；为空时跑全量） | `exp_id`、任务名、任务描述、observation |
| `do_contract` | `exp_id` + 一个或多个 `{"contract", "args"}` | 每个调用的结果 + 最新 observation；多个调用时遇到第一个失败即停止 |
| `check_task` | `exp_id` | 任务是否完成（T/F），附每个子句的结果 |

- observation：头部相机图片、场景物件名列表、goal 每个子句的真假。
- 单个 contract 的结果：`success`、`error_code`、前置/后置谓词的测量值、动词声明的 outputs。`SkillResult` 里的 `selected_path`、`policy_steps`、`bound_nouns`、`children` 是内部信息，返回给 planner 前要去掉。
- 需要新增会话层：启动 Isaac、加载场景与热力学配置、按动词调用 `SkillContractRunner`、用 `zeno_skills/predicates.py` 判定 goal。relative 谓词（如 `flipped`）以任务开始时的 `before_snapshot` 为基准。
- 一个 Isaac 进程只能有一个 SimulationApp，每个 exp 需要独立的 worker 进程；24 GB 显存约可同时运行 2 个 sim（实测两个并行峰值约 7 GB）。

### 2. 删除旧 contract 层（`contract_001`–`contract_008`）

- 代码：`zeno_skills/contracts.py`、`contract_runtime.py`、`contract_profiles.json`；`tools/run_contracts.py`、`render_contract_layers.py`、`export_interface_libraries.py` 中的 legacy 部分。
- 数据与文档：`contract_library/legacy_family_catalog.json`、`contracts/contract_001`–`008`、`docs/CONTRACT_PROPOSAL.md`、`docs/contract_layers.*`；`docs/INTERFACE_IDS.md` 的 legacy 表。
- 测试：`tests/test_contract_runtime.py`、`test_contract_profiles.py`、`tests/fixtures/contract_microwave_cycle.json`。
- 注意：`tools/build_skill_library.py` 仍 import `contracts.py` 生成 legacy 索引，要先切断；`interface_ids.py` 只删 contract 部分，policy ID 仍被 `zeno_skills/policies/` 使用；policy 记录里的 `legacy_family_contracts` 字段一并去掉。

### 3. 删除脚本化 GT 求解器

- `zeno_skills/task_policy.py`、`tools/run_task.py`、`evaluator.py` 中的 `TaskEvaluator`、`docs/GT_POLICY.md` 中的 legacy 章节、`tasks/heat_breakfast/STATUS.md`。
- `evaluator.py` 不能整个删：`quat_R`、`room_of`、`Geometry` 被 policy、`predicates.py`、`rig.py` 使用，先挪到新模块。

### 4. 统一任务定义

- 任务 ID、描述、goal 只从 `skill_library/tasks.json` 读取。
- `tasks/<task>/task.json` 去掉 `goal`、`alternatives`、`roles` 等仅供旧求解器和打分用的字段，只保留场景、标注、机器人初始位姿和热力学配置；同步修改 `tools/build_tasks.py` 和 `task_specs/`。
- README 中 legacy 任务章节、任务视频表随之删除或改写。

### 5. 删除展示与汇报材料

- `media/`、`presentations/`、`runs/` 中已提交的结果；`tools/make_media.py`、`render_asset_gallery.py`、`render_policy_catalog.py`；`docs/POLICY_CATALOG.md`、`POLICY_VERIFICATION.md`、`PHYSICS_AUDIT.md`；`policy_library/policies/` 审阅文档。
- 确定无用的场景：`scenes/kitchen_pot/`、`sim/zeno_house_partnet.usd`、`tasks/preview_grid.png`。
- 删除后重写 README。

### 6. GT plan 文件

- `skill_library/plans/*.skill_subgraph.json` 由已删除的符号规划器生成：只用前后条件做 A* 搜索，没有几何检查，从未在仿真中整条跑通。
- 实测：`heat_without_microwave` 的 plan 成功；`flip_book` 的 plan 在 `flip` 失败（书在初始位置推到桌边后，没有底盘位姿能够到伸出部分）。
- 待做：决定保留与否。若保留作服务回归测试，需改成新的调用格式（去掉 `skill_subgraph`、`depends_on`），并逐个在仿真中验证。

### 7. 重跑物理验证

- 现有 [STATUS.md](../skill_library/verification/STATUS.md) 是第 30 轮的结果（65/70 个动词、97/120 条路径），其中 `search`、`drop`、`expose`、`heat` 的证据来自已删除的 3 个 subgraph 场景；失败原因见 [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md)。
- 删除多物体动词内部的自动 repair、以及 `separate`、`restore`、`pick` 的几条人为条件之后，需用 `tools/verify_skills.py --all` 重跑剩余 32 个场景，并用 `tools/verify_summary.py --write` 重新生成 STATUS.md。
- 运行 Isaac 时一次最多 2 个实例。

## 待定事项

### 影响代码整理

- [ ] 10 个基准任务的 goal 沿用 `tasks.json`（较宽），还是按旧 `task.json` 加严（备选容器、所有门关闭、无物体掉落）？加严需要先给谓词补上"或"和"全部"的写法。
- [ ] 任务描述用英文 `description`、中文 `instruction_zh`，还是两者都给？基准任务以外的 25 个任务只有英文。
- [ ] 9 个多物体动词（`fetch`、`collect`、`sort`、`clear`、`empty`、`arrange`、`restore`、`swap`、`hide`）在内部写死了对其他 contract 的调用，这是 contract 之间的依赖。是否继续对 planner 开放？
- [ ] 检查器"每个 policy 都必须被某条路径用到"这条规则，让几条从未在仿真中通过的路径保留了下来：`pick` 的双手抓平放物体和双手抓箱子、`open` 在左手持物时开门、`handover`。删除规则和路径，还是在 SKILL.md 里注明不可靠？
- [ ] SKILL.md 中随名词变化的条件使用内部字段名（如 `object.flat`、`'top_pinch' in object.grasp_types`），planner 只拿到物件列表时看不到这些字段。改成通俗说法，还是在 observation 里提供这些属性？
- [ ] 物件名是否需要可读化？支撑面目前是 `SimpleBookcaseFactory_6105320_spawn_asset_9196243/surface_3` 这样的 ID。
- [ ] 物件列表包括哪些：只有可移动物体，还是也包括家具表面、门、按钮、房间？参数类型里这些都会用到。
- [ ] 同步给 planner 的 skill 仓库里，文件夹是否从 `skill_XXX` 改成动词名？是否去掉 `vlm_skill_catalog.json` 谓词表里的 `gt_sources`？
- [ ] 资产与场景制作流水线（`tools/` 下建场景、做资产、标注的脚本，`task_specs/`、`scene_specs/`、`sim/checks/`、`tasks/*/check/`、`docs/README.md`）留在本库、移到子目录，还是拆成单独仓库？

### 开发服务时再定

- [ ] 会话生命周期：创建、重置、释放；`task_id` 为空时"跑全量"的含义。
- [ ] 并发与排队。
- [ ] 同步阻塞还是异步轮询（单个 contract 需要几十秒到几分钟）。
- [ ] 图片的视角、分辨率和传输格式（base64 或 URL）。
- [ ] 步数或时间上限由谁执行。

### 已知限制（暂不处理）

- memory 类 goal 谓词（`stirred`、`wiped`、`waved`、`nodded`、`observed`、`room_explored`、`counted`）判定的是"机器人是否实测有效地做了这个动作"，不是世界留下的物理结果；`counted` 只检查是否有计数记录。
- 温度来自任务级热力学模型（`zeno_skills/thermal.py`），不是物理仿真。
