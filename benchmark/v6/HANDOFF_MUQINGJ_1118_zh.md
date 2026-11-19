# 11-17 / 11-18 bench 改动：给 muqingj 的物理侧注意事项

整理：2026-11-18。分支 `benchmark-v5-extensible`，从 `1bdff398`（11-17 回退点）到本文件所在提交，共 40 多个 bench 提交。
bench 只改了任务、布局、目标和评分，**没有改任何 skill / contract**。

## 1. 先看这个：变了什么

- 从 11-17 起，每个变体（design）都至少有一个**替换 seed**：理想的东西缺失、被占用、放不下、有看着像的诱惑，或者去处换了。变体内的 seed 换的是**用什么替代、放在哪**，不只是挪位置。
- 很多 seed 的 id 改名或重建了（例如 `eat_now` → `eat_now__desk_free` / `eat_now__desk_corner`）。
  - **旧 id 的物理结果不能沿用**。
  - 和 `1bdff398` 比：新增或改名的摆法 104 个，去掉的旧 id 64 个。
- 场景文件改了一处（提交 `5022bb44`）：`bed_2` 往东挪了 0.6 m，`cell_shelf_2` 挪到 `bedroom_0_0` 西南角，让那间屋从西门能进。
  - **需要重新拉场景（`tasks/kitchen_skills`）**。
- 总数不变：30 个任务、155 个变体、1550 个 episode。
- bench 侧检查全部通过：
  - 静态检查 1550/1550；
  - 参考路线符号检查 326/326；
  - `pytest benchmark/v6/tests failure_injection` 685 个通过（1 个 xfail）。
- 每个新摆法都渲染过，图在我这边 `~/Pictures/<任务>/<变体>/`，需要的话我传给你。

## 2. 要跑的 episode

- **只跑新增或改名的摆法**：`benchmark/v6/batches/physics_1118_changed.json`，464 个 episode，104 个摆法。
- 全部待跑的：`benchmark/v6/batches/physics_todo.json`。

```
$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json \
  --batch benchmark/v6/batches/physics_1118_changed.json --jobs 2 --out benchmark/runs/v6_physics_1118 --no-eval
```

## 3. 物理上最可能出问题的新摆法（建议先跑这些）

都是新加的摆放：东西摆得很满、放进书架中间层，或者东西放在别的东西里面。

| 任务 / 摆法 | 场景 | 要注意的 |
|---|---|---|
| T25 `cup_elsewhere__blocks_in_cup` | 台面杯子 `cup_counter_b` 里叠了 3 块木积木（杯子内底 z≈1.018，内径 7.2 cm） | 生成时积木和杯壁会不会顶开。我渲染时杯子立得好好的。原来想放海绵（9×6 cm），放不进去，把杯子挤飞了，所以换成积木 |
| T22 `eat_now__desk_corner` | `desk_1` 上 19 件作业分三排，只剩东头前角（x -0.25..-0.03, y -6.33..-6.16） | 零食放到 (-0.14, -6.22)，place 的精度要够 |
| T24 `two_kids__desk3_covered` | `desk_3` 上 21 本书三排，间隙约 4 cm | 香蕉放 `bookcase_4/top` (7.00, -6.76)，只有西侧边能站 |
| T29 `homework_on_table__desk_covered` | `desk_1` 整张盖满（作业 + 角上一本） | 作业本和铅笔放 `desk_3` (6.20/6.50, -5.50) |
| T23 `*bin_full`、T29 `several__bin_full` | 电视柜上的小玩具盒里两层共 24 块积木（T12 的满盒） | 积木要一直在盒里（目标里有 `fully_inside`）；玩具放旁边托盘，参考路线先 `measure` 再放托盘 |
| T23 `dropped_out_of_view__*` | 小厨房台面摆了 23 个盘碗杯 | 勺子和盘子从餐厅地上捡起，放岛台 |
| T23 `only_this_room__cabinet_full` | 4 号矮柜里两口汤锅（yaw 90）加 3 个塑料杯 | 开柜、看、关柜，杯子放台面 |
| T23 `dropped_in_two_rooms__shelf_full`、T26 `whose__shelf_full` | `bookcase_2` 每层 4 摞红书，每摞 2 本，离侧板 2 cm | 之前有一摞离侧板 0.5 cm 时掉过地上，已内移 2 cm |
| T26 `bear_to_bed__top_covered`、T28 `cup_out_of_view__side_covered` | `bookcase_3/top` 摆满 6 本书 | 小熊、杯子要放进**中间层** `bookcase_3/shelf_1`（z 0.443，上面到顶约 29 cm），提示点 (2.10, -4.85) |
| T26 `scattered__no_basket` | `bookcase_2/top` 上一个小储物盒 (1.00, -0.43) | 小车、鸭子、积木都要放进这个 22×17×9 cm 的盒子，高度 0.709 m |
| T26 `where_in_room__waste_bin` | 原来放玩具筐的地上是个垃圾桶 | 小车放 `bookcase_2/top` (1.15, -0.43)，书放 `bookcase_3/top` |
| T27 `fridge_out_of_view__fridge_crowded` | 冰箱层板左半边放了 4 个不锈钢饭盒（yaw 90）和 2 瓶果汁 | 剩饭放右边 (6.05, 3.30)；原有的东西挪动要扣分 |
| T27 `two_leftovers__soup_at_seat` | 汤锅 (3.35, 7.40) 和别人正在吃的碗挨得很近（约 1 cm） | 只收剩饭，不要碰到汤锅和碗 |
| T28 `already_there__wrong_cup` | `bookcase_3/top` 上已经有个瓷杯 (2.28, -4.88) | 他的杯子放 (2.00, -4.88)，瓷杯不能动 |
| T30 `bowl_put_away__mug_inside` | 4 号矮柜里有马克杯 (1.40, 0.42) 和盘子 (1.20, 0.42) | 从关着的柜里拿马克杯（`from_closed`），杯子在盘子旁边 |
| T25 `two_guests__one_cup`、`cup_elsewhere__only_mugs`、T30 `how_many__two_bowls` | 要去拿马克杯 `mug_shelf`（`large_shelf_6/top`，z 1.48） | 和 `cups_for_two` 走的是同一条路线 |
| T29 `belongs_on_table__no_toy_box` | 电视柜上的托盘 (7.80, 0.36) | 小车放进托盘 |

## 4. 评分改了（不影响跑 episode，影响算分）

- 很多变体改成**按 seed 分档**：`scoring.LAYOUT_TIERS`，用 `cost_tiers` 生成。所以每个 seed 的 `variants[lid].scoring.tiers` 可能各不相同，要按 seed 读，不要按变体读。
- 11-18 新加 `benchmark/v6/ideals.py`：每个替换 seed 写明理想是什么、在这个 seed 里能不能用。seed 的 scoring 上新增两个字段：`ideal_present`（true/false）和 `ideal_zh`。
- 打分规则：
  - 理想在：最好那档就是理想。
  - 理想不在：最好的替代品就是这个 seed 的理想，算 1.0；后面依次 0.6、0.3。
  - `top` 字段只表示理想在不在：在是 `ideal`，不在是 `moderate`。分数照常给。
- 每个 seed 的类别和理想：`benchmark/v6/SUBSTITUTION_STATS_zh.md`。各变体的说明：`benchmark/v6/VARIANTS_zh.md`。

## 5. 有问题找我

- 摆放或目标不合理（物理上做不到、被挤掉、够不着）：告诉我任务、摆法和 seed，我在 bench 这边改布局。
- 技能本身的问题：照旧记进 `SKILL_ISSUES_zh.md` 和 `SKILL_FIX_LIST.md`。

## 6. 物理侧回复（muqingj，11-19）

合并进 `remove-handcoded-motion` 后，我按现在的 skill contract（`skill_library/definitions.py`）和 `docs/skills/` 里对调用方的要求，把 326 条参考路线重放了一遍。`oracle_check.py` 照样 326/326，但有几条前提它没查（见 6.5），所以多查出下面这些。**都还没跑仿真。**

### 6.1 我已经改的三处路线

改在生成脚本里（`define_tasks_v6.py`：T06、T13；`new_tasks_v6.py`：T23），重新生成会保留。

| 任务 / 摆法 | seed | 改了什么 | 原因 |
|---|---|---|---|
| T06 `seen_from_bed__bookcase_full` | 10 12 15 16 19 | `pick(wooden_block_a)` 改成 `pick(wooden_block_a, grasp="side")` | 积木要放进 `bookcase_3/shelf_1`，上面 27 cm 是隔板。顶部捏取时手掌在积木上方，放下后沿夹爪轴往上抽手会撞隔板，所以要侧面捏取（`docs/skills/pick.md`；和 T17 `lid_away` 放 4 号柜一样） |
| T23 `by_kind__bin_full` | 10 11 14 17 19 | 放托盘前加 `navigate(spare_tray)` | place 要求 `base_near(托盘)`：底盘中心离托盘 1.3 m 以内。`navigate(tv_stand_2/top)` 停在 1.7 m 长的电视柜离来路最近的地方，从西头来离东头的托盘约 1.3 m，正好卡在边上 |
| T23 `belongs_on_floor__no_toy_box` | 10 11 16 18 19 | 同上 | 同上 |
| T23 `belongs_on_floor__bin_full` | 12 13 14 15 17 | 同上 | 同上 |
| T13 `copy_the_setting__plate_bowl_mug_left` | 10 14 18 | stack 前的 `navigate(dining_table_2/top)` 改成 `navigate(plate_counter_a)` | stack 要求 `base_near(盘子)`。11-16 全量运行 seed 10 就停在这一步：`base_near(place=plate_counter_a) is false (distance 2.64 m)`，盘子在桌子远端 |

- 重新生成了 `tasks.json`、`ROUTES.md`、`SUCCESS_ROUTES_zh.md`、`ORACLE_CHECK.json`、`PLAN_DEPENDENCE.json`、`STATIC.json`。
- `report_v6.py` 在我这边跑不完（要读 `benchmark/runs/v5_fix3` 的结果）。它写的其余文件和这三处改动无关，我没动。
- 检查：静态 1550/1550，`oracle_check` 326/326，`pytest benchmark/v6/tests failure_injection` 685 个通过（1 个 xfail），`define_tasks_v6.py --check` 通过。

### 6.2 要改布局：用现在的技能做不成（4 个摆法，20 个 episode）

| 任务 / 摆法 | seed | 问题 | 建议 |
|---|---|---|---|
| T09 `tomato_in_fridge__big_tomato` | 11 14 15 17 18 | `big_tomato` 宽 7.5 cm，超过捏取宽度上限 6.8 cm（`tools/prepare_assets.py` 的 `PINCH_MAX`：夹爪最大开口 8 cm，两边各留 6 mm），所以 `annotations/assets.json` 里它的 `grasps` 是空的。第 9 步 pick 直接失败（`has no Zeno-feasible grasp annotation`） | 换成宽度不超过约 6.5 cm 的东西。原来冰箱里的 `fridge_tomato`（顶部捏取）11-15 从冰箱里拿成功过 |
| T23 `dropped_out_of_view__no_room_for_plate` | 13 14 15 17 19 | 盘子掉在地上。盘子只有厚度捏取（扁平物体），pick 的 contract 写明地上的扁平物体不能 pick：`floor_top` 路径要顶部捏取，`flat_edge` 要先把东西推到支撑面边上 | 掉在地上的换成有顶部捏取、又放不进台面空隙的东西（比如擀面杖 22 cm、锅盖 25 cm），或者盘子不放在地上 |
| T23 `dropped_in_two_rooms__shelf_room` | 10 12 15 18 19 | 书掉在书房地上，原因同上（书也是扁平物体） | 换成有顶部捏取的东西，或者书不放在地上 |
| T23 `dropped_in_two_rooms__shelf_full` | 11 13 14 16 17 | 同上 | 同上 |

### 6.3 很可能做不成：放进上面有隔板的层板（3 个摆法，15 个 episode）

- 顶部捏取、杯沿捏取时，手掌都在物体上方。place 竖直放下以后沿夹爪轴（竖直向上）抽手，会撞上面的隔板。
- 依据：T17 的 4 cm 积木用顶部捏取放 4 号柜层板（上方 29.5 cm）就是这样失败的，改成侧面捏取后成功。11-14 T04、T25 从 4 号柜用杯沿捏取拿杯子，600 个候选全都顶到柜顶，放进去是同一个问题。
- 下面三个物体都没有侧面捏取，没法像 T06 那样改抓法：小熊宽 10.6 cm，超过夹爪开口；塑料杯只有杯沿捏取。
- 注意：`bookcase_3/shelf_1` 到上面隔板的标注净高是 27.3 cm，第 3 节写的是约 29 cm。

| 任务 / 摆法 | seed | 放什么、放到哪 | 物体上方还剩 |
|---|---|---|---|
| T26 `bear_to_bed__top_covered` | 14 15 16 17 19 | 小熊（15 cm 高，只有顶部捏取）放 `bookcase_3/shelf_1` | 约 12 cm |
| T28 `cup_out_of_view__side_covered` | 10 11 13 14 19 | 塑料杯（9.5 cm 高，杯沿捏取）放 `bookcase_3/shelf_1` | 约 18 cm |
| T23 `only_this_room__cabinet_room` | 11 14 15 17 18 | 塑料杯（杯沿捏取）放 `kitchen_cabinet_4/inside_shelf`（净高 29.5 cm） | 约 20 cm |

建议：这几个的去处换成上面敞开的面（柜顶、书架顶、桌面）；或者中间层只给有侧面捏取的东西用（木积木、易拉罐、果汁瓶、零食盒）。这组的判断只依据 T17，没跑仿真。你要是想保留，我先跑这三个，看结果再定。

### 6.4 以前没跑过的取放组合（路线没问题，跑完再告诉你）

- T23 `only_this_room__cabinet_room`、`only_this_room__cabinet_full`：从地上用杯沿捏取塑料杯。以前地上捡的都是顶部捏取的东西（勺子、积木、小车、泡沫块）。
- T30 `bowl_put_away__mug_inside`：从 4 号柜层板拿马克杯（杯沿或把手，杯子上方约 17.5 cm）。11-14 看到 T04 的杯子在 4 号柜里用杯沿捏取会顶到柜顶，这个可能也一样。
- T04 `x6_gd_cup_in_cabinets__plastic_only`：从 6 号柜层板拿塑料杯。
- T05 `x6_gd_pen_or_pencil_cabinets__pen_in_use`：从 6 号柜层板拿铅笔。

### 6.5 `oracle_check.py` 没查的几条（建议加进符号检查）

- **`base_near` 要按距离算。** navigate 停在目的地外 0.45–1.0 m 的一圈上（`base_motion.STANDOFF_RING`），取离来路最近的点；之后的 pick / place / stack / open 要求底盘中心离操作对象 1.3 m 以内（`predicates.NEAR_M`）。现在的判法是"去过同一件家具就算近"，长桌、长电视柜从一头到另一头会漏掉，上面 T13、T23 就是这种。
- **地上的扁平物体没有 pick 路径**：只有厚度捏取的东西，比如书、本子、盘子、饭盒。
- **没有抓取标注的物体 pick 不了**：`assets.json` 里 `grasps` 为空的，现在是 `big_tomato` 和 `cereal_box`。
- **放进上面有隔板的层板**：顶部捏取或杯沿捏取时，物体上方要留够手的高度；有侧面捏取的物体在路线里写 `pick(..., grasp="side")`。
- （可选，不改也没错）`close_hands_free` 假定只有微波炉能拿着东西关门。11-12 起 close 有 `loaded` 路径：右手拿着东西时左手推门（`docs/skills/close.md`）。现在的路线先放下再回来关，只是多走几步。

我这边的检查脚本就是按上面这几条重放路线的。T13 那一步是它先算出来、再和 11-16 的运行结果对上的。你需要的话，我把脚本整理进仓库。
