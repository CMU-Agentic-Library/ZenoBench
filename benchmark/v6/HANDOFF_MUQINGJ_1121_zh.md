# 11-21 bench 改动：给 muqingj 的全量回归说明

整理：2026-11-21 夜。以 `main` 为准（分支 `benchmark-v5-extensible` 已合并进 main）。

## 1. 请跑全量

- 先拉最新的 `main`，再和你那边搬运滑落的修复合在一起跑。
- `tasks.json` 从 11-19 起改了很多：布局、参考路线、评分都变了。**旧的物理结果不能沿用**，请全部重跑。
- 场景文件 11-17 之后没变（`tasks/kitchen_skills`），不用重新拉。
- 总数：30 个任务、151 个变体、1510 个 episode（种子 10–19）。
- bench 侧检查全部通过：
  - 静态检查 1510/1510；
  - 参考路线符号检查（oracle）316/316；
  - `pytest benchmark/v6/tests` 638 个通过。

- **请用 `--profile sticky/gt`**（和你 v6full_1119 一样）。bench 默认的 `benchmark` profile 搬运会滑落，11-21 我这边也改用 sticky/gt 验证。

```
$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json \
  --batch benchmark/v6/batches/category_task.json --jobs 2 --profile sticky/gt --out benchmark/runs/v6full_1122
# 另外三个：category_control.json、category_action_task.json、category_action.json（空）
```

## 2. 改了你的代码两处（用户要求，都是 cover 认盘子）

`zeno_skills/skill_runtime.py` 的 `SLOT_VALIDATORS["lid_ref"]`：带 `plate` 标签的东西也算锅盖。

- **原因：** T15 `no_lid`、`lid_elsewhere__covering_bowl` 要拿盘子盖锅。原来 cover 在参数检查就报 `NOUN_INVALID`，你 11-19 的回归两个都卡在这。
- **影响范围：** 只放开了这个检查。`lids()`、`uncovered`、`objects_inside` 都没动。
- **几何：** 盘子直径 24.8 cm，锅盖 25 cm。`CoverWithLidPolicy` 和 `lid_on` 对锅盖没有别的假设。
- 第二处（82f5f945）：`is_lid` 也认 `plate` 标签。只改 lid_ref 时参数检查过了，但 cover 的 rim_plane 路径匹配不上，报 `NO_PATH`。
- 你觉得不合适可以改回去，那这两个设计就得换一种替代品。

## 3. 这两天 bench 改了什么（11-20 → 11-21）

| 任务 / 设计 | 原来的问题 | 改法 |
|---|---|---|
| T23 地上掉东西（全部） | `explore_room(kitchen_0_1)` 看不到掉落物 | 掉落点改在小厨房西北角 (-1.10, 12.30)。逛厨房有两个站位，都扫得到 |
| T23 放勺子 | 从地上捡起的勺子放不上小厨房台面：拿着勺子保持倾斜往下放规划不出来，12 次成功 3 次 | 参考路线改放岛台 (7.40, 1.62)。目标本来就接受任何厨房台面 |
| T23 `dropped_in_two_rooms` | 小熊夹在书桌和床之间，逛客厅扫不到 | 挪到书桌前面 (0.20, -7.00) |
| T09 番茄汤（全部） | 从岛台看不到灶台那头的锅 | 路线开头先 `navigate`/`look` 灶台 |
| T09 `tomato_in_fridge` | 加热时等第一颗小番茄到 60°C 就关火，大番茄只到 55.9°C；锅盖在灶台右侧灶眼上，7 次够不着 4 次 | 改成等最慢的那颗；锅盖挪到岛台番茄旁边 (7.25, 1.85) |
| T10 扔垃圾（全部） | 垃圾桶在灶台南边，看不到 | 路线开头先 `navigate`/`look` 灶台 |
| T13 `copy_the_setting` | 照着摆的勺子离桌边只有 10 cm，放碗时身体蹭到桌子 | 勺子挪到离桌边 16 cm |
| T25 `cups_for_two` | 柜子里的杯子拿不出来：只能从上方捏杯沿，被柜子里的隔板挡住（4 号柜 1/6、6 号柜 0/3） | 库存杯子改放小厨房台面前沿 (-0.45, 8.20 / 7.80)，位置固定 |
| 全局：小厨房台面 counter_2 | 种子把杯子、勺子滑到台面两端或吊柜下面，够不着 | `layout.PICK_ZONE`：路线要拿的东西只留在台面西侧前沿（x ≤ -0.36，y 7.25–9.15）；4 号柜顶上的东西只留在前沿（y ≥ 0.38） |
| 柜子里的杯子（T04 `glass_in_cabinet`、`cup_in_cabinets`，T28 `where_his_cup_is__in_cabinet`，T30 `mug_inside`） | 柜子里的杯子只能从上方捏杯沿，被隔板挡住 | 用户决定：改放 4 号柜顶（0.62 m），路线先 `navigate`/`look` 柜顶 |
| T25 `cups_for_two` 备用马克杯 | 在 large_shelf_6 顶上（1.48 m），从没拿起来过 | 挪到矮格架 cell_shelf_4 顶（0.95 m） |
| T25 饮料在冰箱 | 放在冰箱里 18 cm 深，抓不到 | 挪到冰箱门边 y 3.16 |
| T27 `two_leftovers` | 汤锅和米饭盒在冰箱层板上放不下 | 用户决定：剩汤改成带盖的不锈钢小饭盒（桌上或灶台上），和米饭并排放冰箱层板前沿。正在吃的那锅汤（`soup_at_seat`）还是锅 |
| T15 盘子当盖、T13 `plate_bowl_mug_left` | 盘子在吊柜下面滑到台面边缘规划不出来 | 盘子开局就伸出台面西沿 4 cm |
| T03 托盘 | 26×19 cm 托盘先放勺子后，22 cm 擀面杖放不下 | 放托盘时先放擀面杖 |
| T03 `utensils_apart__bin_free` | 擀面杖先放进宽口箱后，勺子 drop 时手臂停在半路（两次）；勺子丢进这个箱子其他 193 次都成功 | 先丢勺子再放擀面杖（和 put_both 一样） |
| T18 `door_stuck` | 4 号柜里 x=1.55 的碗抓不到，后来 1.45 的也抓不到 | 两只碗放 1.18 / 1.41（1.40 单独放成功过） |
| T18 勺子/马克杯/玻璃饭盒 | 在 counter_2 东半边，没地方站 | 挪到 counter_2 西侧前沿 |
| T10 用过的马克杯 | 放回 counter_2 找不到空位（4 次失败 3 次） | 路线改放岛台 |
| T05 跑腿 | 马克杯目标点在 counter_2 里面 37 cm | 改到西侧前沿 |

## 4. 已知过不去的（不是布局问题）

- **T04 `cup_in_4` 和柜子里的杯子：** 已经按用户的意思改到 4 号柜顶，不再有"杯子在柜子里"的设计。
- **T22 冰箱门关不上：** 要靠你那边没推上来的 snap.patch（door_access.py 的 YAW_STEP）。请推上来再跑全量。
- **搬运滑落：** 开 sticky/gt 就没有了。
- **开局第一次收臂没到位（tuck）：** 只在 zihan 的机器上出现，13 次，都是第 0 步就失败。
- **place 只试附近的几个站位，不会换到另一边：** T23 台面那次就是这样。bench 已经绕开了。

## 5. 今晚验证的结果

（见下一节，跑完补上）
