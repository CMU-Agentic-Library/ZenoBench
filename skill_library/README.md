# ZenoBench 动词 SkillNode 库（schema 2）

<!-- counts:start -->
**70 个 SkillNode**（`skill_001`–`skill_070`，70 个不同动词），**70 个 Contract**（`contract_009`–`contract_078`，按动词调用），共 **120 条按名词选择的 policy 路径**，覆盖 **114/115 个底层 policy**（1 个因物理上不可行而退役，原因见 [POLICY_COVERAGE.md](../policy_library/POLICY_COVERAGE.md)）；前后条件来自 **71 个 GT 谓词**。[tasks.json](tasks.json) 列出 35 个任务。
<!-- counts:end -->

## 设计

每个 SkillNode 是 **一个动词 + 一个名词**，动词之间不是近义词。同一个动作只保留一个动词：抓取不再拆成 acquire / grasp / clamp / clasp / pinch 等多个节点，只有 `pick(object)`；放置只有 `place(object, receptacle)`。名词绑定到场景实例后，Contract 根据该实例的 GT 标注和实时状态选择 **policy 路径**，每条路径顺序调用一个或多个底层 policy。路径和 policy 是 Contract 的内部实现：上层规划器只按动词调用 Contract，不能指定路径，SKILL.md 中也不出现它们。下表供开发者参考：

| 动词 | 名词绑定 | 选中的路径 | policy 链 |
| --- | --- | --- | --- |
| `pick` | 苹果（`top_pinch` 标注） | `top_pinch` | `policy_010` |
| `pick` | 平放的书（只有 `edge_pinch` 标注） | `flat_edge` | `policy_045` 推到桌边 → `policy_013` 夹悬出部分 |
| `pick` | 地上的积木 | `floor_top` | `policy_065` 靠近 → `policy_042` 降躯干前倾预抓 → `policy_010` 顶部夹取 |
| `pick` | 微波炉腔内的碗 | `microwave_cavity` | `policy_048`（路径前置条件：`is_open(微波炉)`） |
| `heat` | `kitchen_microwave` | `microwave` | `policy_032` 按启动键 → `policy_064` 等待温度 |
| `heat` | `kitchen_stove` | `stove_pot` | `policy_094` 按电源键 → `policy_090` 等待温度并关火 |
| `open` | 冰箱 / 抽屉 / 铰链门 / 微波炉 | 各自路径 | 收臂 → 抓把手 → 随门运动 → 松手；微波炉按门键 + 铰链驱动 |

多物体动词（`fetch`、`collect`、`sort`、`clear`、`empty`、`arrange`、`restore`、`swap`、`hide`）的路径在内部调用其他 Contract，嵌套的每一步都各自检查前后条件。这是 Contract 的内部实现，不构成技能之间的关系；规划器看不到也不能选择这些子调用。

## 前置条件与后置条件

前后条件都是 [`zeno_skills/predicates.py`](../zeno_skills/predicates.py) 中带参数的谓词，例如 `holding(hand=right, object=$object)`、`is_open(articulated=@object.appliance)`、`in_cookware_on_burner(food=$food, appliance=$appliance)`。每个谓词：

- 有类型化参数（`object_ref`、`support_ref`、`hand` …），由检查器核对；
- 有 GT 评估函数，读取仿真器真值：物体位姿、关节角、手指间隙、头相机正运动学、温度状态、事件日志等（GT 来源只写在 `contract_library/` 的导出里，不给规划器）；
- 分为 `fluent`（当前状态）、`memory`（机器人记录的事实，如看到过、擦过）和 `relative`（相对 Contract 开始时的变化，如 `object_moved`，只能作后置条件）。

`SkillContractRunner`（[`zeno_skills/skill_runtime.py`](../zeno_skills/skill_runtime.py)）执行一次调用：

1. 校验输入类型，绑定名词并计算 GT 属性（抓取标注、所在支撑面、是否在冰箱或柜子里、盖着的锅盖、离边缘远近等）；
2. **执行前**在实时状态上评估全部前置条件，任何一条为假就不动作并返回 `PRECONDITION_FAILED`；
3. 选择第一条名词条件全部成立的路径，再检查该路径的额外前置条件；
4. 依次执行 policy、嵌套 Contract 或循环；
5. **执行后**评估技能级和路径级后置条件，全部成立才报告成功；
6. 返回实测输出和每个谓词的测量值。失败即停止，不自动重试，也不推断 fallback。

## 给上层规划器的文件

- `skills/skill_XXX/SKILL.md`：规划器读取的文件，包括签名、输入输出、调用格式、前后条件（含随名词变化的条件）、可能失效的状态和失败码。不含 policy 路径和 policy 编号。
- `skills/skill_XXX/skill.json`：同一内容的机器可读版本。
- [vlm_skill_catalog.json](vlm_skill_catalog.json)：全部 `skill.json` 和谓词表合在一个文件里。

调用方式：发送 JSON `{"contract": "<动词>", "args": {...}}`，参数是观测里列出的场景物体名或字面值（服务接口尚未实现；进程内等价于 `SkillContractRunner(rig).run(verb, args)`）。失败时返回错误码和测得的谓词，不重试。

## 任务

[tasks.json](tasks.json) 用 GT 谓词描述本场景可完成的任务：10 个原有 ZenoBench 任务，加上厨房场景的灶台煮汤、无微波炉时用灶台加热、冰箱冷却、丢垃圾、叠积木、擦台面、翻书、藏物、找东西、探索房间、计数、敲门、分类、清空等。tasks.json 是任务的唯一来源。每个任务的 ground-truth SkillNode 链在 [plans/](plans/)，仅作参考数据，不是规划器输入，目前也没有执行器。

## 物理验证

[verification/scenarios.json](verification/scenarios.json) 中的场景在 Isaac Sim 中逐条执行 Contract（`tools/verify_skills.py`），每一步都测量前后条件。结果汇总见 [verification/STATUS.md](verification/STATUS.md)，由 `tools/verify_summary.py --write` 生成。

## 生成与检查

```bash
python tools/build_skill_library.py --check        # 定义 -> 导出是否一致，库是否通过全部静态检查
python -m pytest tests skill_library/tests -q
$ISAACLAB_PYTHON tools/verify_skills.py --all --jobs 3   # 物理验证
```

源文件只有 [definitions.py](definitions.py)（技能）和 [zeno_skills/predicates.py](../zeno_skills/predicates.py)（谓词）。`skills/`、`contract_library/` 中 `contract_009` 起的 Contract、`vlm_skill_catalog.json`、`SKILLS.md`、`docs/INTERFACE_IDS.md` 都由 `tools/build_skill_library.py` 生成。

<!-- skills:start -->
## 全部 SkillNode

| SkillNode | Verb + noun | Signature | Postconditions |
|---|---|---|---|
| `skill_001` | **navigate** place | `navigate(destination)` | `base_near` |
| `skill_002` | **approach** target | `approach(target, pass_by?)` | `reachable` |
| `skill_003` | **face** target | `face(target)` | `facing` |
| `skill_004` | **retreat** obstacle | `retreat(obstacle, distance_m)` | `base_clear_of` |
| `skill_005` | **crouch** torso | `crouch(height_m?)` | `torso_raised` + `torso_at`, `torso_lowered` |
| `skill_006` | **stand** torso | `stand()` | `torso_raised` |
| `skill_007` | **bend** waist | `bend(pitch_rad?)` | `waist_bent` |
| `skill_008` | **straighten** waist | `straighten()` | `waist_straight` |
| `skill_009` | **tuck** arm | `tuck(hand)` | `arm_stowed` |
| `skill_010` | **reset** posture | `reset()` | `arm_stowed`, `torso_raised`, `waist_straight` |
| `skill_011` | **look** target | `look(target)` | `in_view`, `observed` |
| `skill_012` | **inspect** receptacle | `inspect(receptacle)` | `observed` |
| `skill_013` | **search** object | `search(object, region?)` | `observed` |
| `skill_014` | **explore** room | `explore(room)` | `room_explored` |
| `skill_015` | **point** target | `point(target)` | `pointing_at`, `hand_empty` |
| `skill_016` | **present** object | `present(object)` | `presenting`, `holding` |
| `skill_017` | **pick** object | `pick(object, hands?, grasp?, pass_by?)` | `holding` + `holding` |
| `skill_018` | **place** object | `place(object, receptacle, hint_xy?, pass_by?)` | `hand_empty` + `in_appliance`, `inside`, `on`, `on_burner` |
| `skill_019` | **drop** object | `drop(object, container)` | `inside`, `hand_empty` |
| `skill_020` | **stack** object | `stack(object, base)` | `on_top_of`, `hand_empty` |
| `skill_021` | **release** object | `release(object, hand)` | `hand_empty` |
| `skill_022` | **handover** object | `handover(object)` | `holding`, `hand_empty` |
| `skill_023` | **lift** object | `lift(object, height_m)` | `held_above`, `holding` |
| `skill_024` | **lower** object | `lower(object, height_m)` | `held_below`, `holding` |
| `skill_025` | **rotate** object | `rotate(object, degrees)` | `yaw_rotated`, `holding` |
| `skill_026` | **regrasp** object | `regrasp(object, support)` | `holding` |
| `skill_027` | **brace** object | `brace(object)` | `steadied`, `holding` |
| `skill_028` | **flip** object | `flip(object)` | `flipped`, `hand_empty` |
| `skill_029` | **push** object | `push(object, direction_xy, distance_m)` | `object_moved` |
| `skill_030` | **pull** object | `pull(object, distance_m)` | `moved_toward_base`, `reachable` |
| `skill_031` | **expose** object | `expose(object)` | `edge_overhang` |
| `skill_032` | **separate** object | `separate(object)` | `grasp_clearance` |
| `skill_033` | **center** object | `center(object, margin_m)` | `away_from_edge` |
| `skill_034` | **roll** object | `roll(object, distance_m)` | `object_rolled` |
| `skill_035` | **tip** object | `tip(object)` | `lying` |
| `skill_036` | **upright** object | `upright(object)` | `upright`, `hand_empty` + `on` |
| `skill_037` | **wipe** surface | `wipe(surface, tool)` | `wiped`, `holding` |
| `skill_038` | **stir** container | `stir(container, tool)` | `stirred`, `holding` |
| `skill_039` | **pour** contents | `pour(source, target)` | `poured_into`, `holding` |
| `skill_040` | **open** articulated | `open(articulated)` | `is_open` |
| `skill_041` | **close** articulated | `close(articulated)` | `is_closed` |
| `skill_042` | **press** button | `press(button)` | `button_pressed`, `hand_empty` + `heating` |
| `skill_043` | **heat** food | `heat(food, appliance, temp_c)` | `temperature_at_least`, `heating` |
| `skill_044` | **chill** food | `chill(food, appliance, temp_c)` | `temperature_at_most` |
| `skill_045` | **cover** container | `cover(container, lid)` | `covered`, `hand_empty` |
| `skill_046` | **uncover** container | `uncover(container)` | `uncovered`, `hand_empty` + `on` |
| `skill_047` | **fetch** object | `fetch(object, receptacle)` | `hand_empty` + `inside`, `on` |
| `skill_048` | **collect** objects | `collect(objects, container)` | `all_inside` |
| `skill_049` | **sort** objects | `sort(objects, rule)` | `sorted_by_category` |
| `skill_050` | **clear** support | `clear(support, receptacle)` | `support_clear` |
| `skill_051` | **empty** container | `empty(container, receptacle)` | `container_empty` |
| `skill_052` | **arrange** objects | `arrange(objects, support, max_dist_m)` | `grouped` |
| `skill_053` | **restore** object | `restore(object)` | `at_initial_place`, `hand_empty` |
| `skill_054` | **swap** objects | `swap(a, b)` | `positions_swapped`, `hand_empty` |
| `skill_055` | **sidestep** base | `sidestep(distance_m)` | `sidestepped` |
| `skill_056` | **wait** duration | `wait(seconds)` | `waited` |
| `skill_057` | **identify** object | `identify(object)` | `identified`, `in_view` |
| `skill_058` | **measure** object | `measure(object)` | `measured`, `in_view` |
| `skill_059` | **count** category | `count(category)` | `counted` |
| `skill_060` | **wave** hand | `wave()` | `waved`, `hand_empty` |
| `skill_061` | **nod** head | `nod()` | `nodded` |
| `skill_062` | **shake** object | `shake(object)` | `shaken`, `holding` |
| `skill_063` | **hover** object | `hover(object, target)` | `hovering_over`, `holding` |
| `skill_064` | **square** object | `square(object)` | `squared`, `hand_empty` |
| `skill_065` | **touch** object | `touch(object)` | `touched`, `hand_empty` |
| `skill_066` | **knock** articulated | `knock(articulated)` | `knocked`, `is_closed` |
| `skill_067` | **sweep** objects | `sweep(objects, radius_m)` | `clustered` |
| `skill_068` | **stop** appliance | `stop(appliance)` | `heating` + `is_open` |
| `skill_069` | **dip** utensil | `dip(tool, container)` | `dipped`, `holding` |
| `skill_070` | **hide** object | `hide(object, receptacle, lid?)` | `hidden`, `hand_empty` |
<!-- skills:end -->
