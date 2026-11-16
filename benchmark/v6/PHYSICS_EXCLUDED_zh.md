# 暂时排除出统计的 v6 episode（物理 policy 做不到）

2026-11-15 整理。依据：v6 全量跑 1109 / 1111 / 1112 / 1113 / 1115（1115 跑到 102/153 停止，
`/data/zenobench/v6full_1115/runs`），以及 11-14 的候选手臂图（`/data/zenobench/nograsp_1114/png`）。

这些 variation 失败的原因是**物体的摆放或物体本身超出了当前物理 policy 的能力**（柜内空间、
高度、夹爪开口、缺抓取方式），不是规划或感知代码的 bug。在 policy 补上对应能力之前，从 v6 成功率
统计里排除；能力补上后逐条放回并重跑。

历史一列按 1109 / 1111 / 1112 / 1113 / 1115 的顺序，O = 成功，x = 失败。profile 都是 `sticky_gt`，seed 10。

## A. 柜内 / 冰箱内 / 高处：空间受限，够不到

| # | episode | 失败步骤 | 物体与几何 | 历史 |
|---|---|---|---|---|
| A1 | `T04_cup_or_mug_to_cabinet/s10_x6_gd_cup_in_cabinets__cup_in_4_v6_x6_gd_cup_in_cabinets__cup_in_4` | pick cup_counter_b：no reachable grasp from any base pose | 杯子在 kitchen_cabinet_4/inside_shelf（z 0.31，上方净空 0.30 m）。breakfast_cup 只有从上方捏杯沿的抓法，600/600 个候选手臂的 link5-7 和夹爪都撞到柜顶板（z 0.6–0.7）。杯底直径 7.3 cm，大于 PINCH_MAX 6.8 cm，没有侧捏 | xxxxx |
| A2 | `T25_drink_for_guest/s10_cups_for_two__one_there_v6_cups_for_two__one_there` | pick stock_cup_1：同上 | 同一层板，同 A1，600/600 撞柜顶板 | xxxxx |
| A3 | `T21_bring_tissues/s10_tissue_put_away__in_4_v6_tissue_put_away__in_4` | pick tissue：同上 | 同一层板（净空 0.30 m），69 个候选在预抓取姿态全部撞固定物体（手指、link5-7） | xxxxx |
| A4 | `T25_drink_for_guest/s10_cup_elsewhere_v6_cup_elsewhere` | pick cup_counter_b：同上 | 杯子在 kitchen_counter_2/top（z 1.0，头顶有吊柜，净空 0.39 m），杯沿约 1.15 m。1192 个没有 IK 解，9 个有 IK 且不碰撞，只构建出 2 个，都在 carry_in 失败 | Oxxxx |
| A5 | `T18_check_cabinet_dishes/s10_enough_for_dinner__two_short_v6_enough_for_dinner__two_short` | pick bowl_kitchen_cabinet：同上 | 碗在 kitchen_cabinet_3/top，z 1.17 m，太高，没有一个候选有 IK 解 | xxxxx |
| A6 | `T22_put_away_shopping/s10_two_spots_v6_two_spots` | place bought_snack → kitchen_cabinet_6/inside_shelf：no spot of 4 reachable | 要放进柜内层板（z 0.41，净空 0.38 m）。160 个目标里，footprint 筛掉 18.9 万个候选，IK 失败 1.2 万个，只构建出 11 个，全部失败 | xxxxx |

## B. 物体超出夹爪能力，只能"推到桌边再抓"，而这条路走不通

夹爪最大开口 8 cm（PINCH_MAX 6.8 cm）。物体太宽、或者平放的书没有能直接夹的面时，pick 会先把物体
推到桌边，让它伸出桌沿再从侧面夹。下面这些里，推这一步本身做不到。

| # | episode | 失败步骤 | 物体与几何 | 历史 |
|---|---|---|---|---|
| B6 | `T07_heat_oatmeal/s10_two_portions__counter_v6_two_portions__counter` | pick soup_pot：no pinch annotated (has ['handle_pinch']) | soup_pot（宽 26 cm）在 kitchen_counter_2/top，头顶有吊柜（净空 0.39 m）。只标了把手抓取点，而 pick 现在不支持抓把手 | xxxxx |

## 可修、已移出排除（2026-11-15）

| episode | 原来的编号 | 结论 |
|---|---|---|
| `T09_tomato_soup/s10_tomato_in_fridge__in_fridge_v6_tomato_in_fridge__in_fridge` | A7 | **已修**（88197712）：番茄从 y 3.30（冰箱正面往里 29 cm）挪到 y 3.14（离层板前沿 10 cm），pick 成功（sim 检查 fridgetomato_1115）。门开到 80° 或 92° 都没用 |
| `T22_put_away_shopping/s10_juice_on_table_nominal` | A8 | 和番茄同一个原因：冰箱门开度有限，放置位置太靠里。改法同番茄，把冰箱里的目标位置往前挪（待改） |
| `T26_kids_things_to_room/s10_where_in_room_v6_where_in_room` | B5 | **已修**（e3dcbb8）：书沿 14 cm 那边只能伸出 5.495 cm，比要求的 5.5 cm 差 0.05 mm；-x 端要推 46.5 cm，超过 45 cm 上限。在 new_tasks_v6.py 里把书转 90°（长边朝前沿）后，前沿只需推 6.9 cm，sim 检查 bookrot_1115 整条 episode 成功（11 步，700 s） |
| `T27_leftovers_to_fridge/s10_rice_on_table_nominal`、`s10_which_is_leftover…`、`s10_fridge_out_of_view…` | B1、B2、B4 | **已修**（bf9c598）：饭盒 16 × 11 × 7 → 18 × 16 × 5 cm。边缘抓取要伸出 ≥ 5.5 cm 且重心留在桌面内 1.5 cm，所以朝桌边那条边至少 14 cm；原来 11 cm 的一边永远不行，7 cm 高时夹爪上下只剩约 5 mm。sim 检查 ricebox_1115：rice_on_table、which_is_leftover、fridge_out_of_view、fruit_stays_out 整条成功 |
| `T27_leftovers_to_fridge/s10_two_leftovers__soup_on_table…` | B3 | 改尺寸后仍失败：slide_push 停在目标前 7 mm（1113/1115 是 6/12 mm），同 T27 still_eating、T07 in_glass_box（7–9 mm）。不是物理极限，是 slide_push 的到位问题（待查） |

## 放回统计的条件

- A1–A3：杯子类容器需要从侧面斜着捏杯沿，或者支持侧捏；纸巾需要在 0.30 m 净空里能伸进去的预抓取姿态。
- A4、A5：高处取物要能从侧面抓，或者把底盘位置和躯干高度一起搜索。
- A6：在柜内层板上放置，要能找到可用的空位。
- B6：pick 支持 `handle_pinch`。

每补上一项能力，就把对应条目移出本文档，并对这些 episode 做一次定向重跑。

## 没有列入的失败

下面这些失败**留在统计里**，因为它们是可以修的软件问题，物理上做得到：

- 感知：`bookcase_2/top`（只有 0.71 m 高）视线被挡、看地面物体、search 漏看位置、explore 覆盖率 0。
- T14 书放到书架顶面报 `no free edge spot`：edge-place 空位生成的问题。
- 以前成功过、这次失败的：T09 stir ×2（倾斜规则）、T01 no_room_fallback、T08 wipe_and_sort、T03 no_bin_substitute、T23 belongs_on_floor、T14 homework_stays、T29 several。
- 规划或执行问题：T13 copy_the_setting、T10 rubbish_leftovers lift、T08 return_sponge wipe、T05 pen_in_6 close。
- 灵巧操作：T15 book_free_nominal flip、T06 display_row__spread square。这两条暂时也留在统计里，以后再决定要不要排除。
