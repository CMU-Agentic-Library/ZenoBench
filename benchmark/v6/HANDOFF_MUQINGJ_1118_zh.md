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
