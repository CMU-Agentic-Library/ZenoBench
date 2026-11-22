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
| T05 `pen_or_pencil_cabinets` | 柜子里的笔、铅笔放得太深，抓不到 | 笔放 4 号柜 (1.40, 0.46)，铅笔放 6 号柜 (3.50, 0.41) |
| T02 `block_put_away__in_6` | 柜子里的积木太深 | 6 号柜里的积木放 (3.50, 0.41) |
| T07 `two_portions` | 退役的 `approach` 变成 `navigate(start_button)`，按按钮时没有 IK（2/2） | 路线关微波炉门后直接按开始，和 heat 一样 |
| 全局：会滚的东西 | T11 s10 苹果离餐桌边 1.7 cm，第一步前就滚下去了 | `layout.ROLLING`：苹果、橙子、小番茄、大番茄离台面每条边至少 6 cm |
| 全局：PICK_ZONE | T13 s10 盘子中心在 9.04，伸到吊柜北端下面 | 整个物体（不只中心）都要在区域里；counter_2 y 到 9.05 |
| T14 书架 | 书架顶上的书放在中间，被放的那本找不到能捏边放的空边（4/4）；不给 hint 时 59 次失败 41 次 | 书架上原有的书转 90° 立在两端，中间留空；所有放到书架的步骤给 hint (1.00, -0.45) |
| T24 香蕉 | 香蕉在果篮里抓不到（2/2） | 改放果篮旁边 (7.40, 1.85)，说明文字同步 |
| T17 `hide_both__two_pots` | 锅盖在灶台汤锅旁边，抓不到（2/2） | 锅盖挪到岛台 (7.75, 1.85) |
| 全局：hide / cover | 要拿起的东西周围没有手指空间 | layout 把 hide / cover 要拿的物体和盖子也算进"要拿的"，周围留 3 cm |
| T18 `door_stuck`（11-22） | 1.18 的碗贴着柜子左壁抓不到；第二只碗单独在 (1.41, 0.42) 也抓不到 | 两只碗贴 4 号柜层板前沿：(1.22, 0.47)、(1.42, 0.47) |
| T05 `pen_or_pencil_cabinets`（11-22） | 柜子里的笔、铅笔放在里面 10 cm 都抓不到（2/2） | 铅笔挪到 6 号柜层板前沿后 2 cm (3.50, 0.48)，能抓起来了；4 号柜层板太低（z 0.31，净空 0.30 m），前沿也抓不到，`pen_in_4` 的笔改放 4 号柜顶（同柜子里杯子的处理），路线改成 `navigate`/`look` 柜顶 |
| T14 `next_in_series__on_bookcase`（11-22） | 第二本红书在书架东端，拿的时候往边上推，手臂撞到书架后面的墙 | 放到书架南沿中间、伸出 6 cm（和 T01 卧室那本书一样，以前拿起来过）；路线先拿它去书桌，再把第一本放上书架 |
| T07 汤锅在餐桌、T03 `utensils_apart`（11-22） | `search_object(dining_room_0_1)` 去看 3 号柜的两个视点 (0.16, 5.27)、(0.01, 5.67) 从来没到过（0/4），第三个视点 5/5 | 路线改成 `navigate`/`look` 餐桌 |

## 4. 已知过不去的（不是布局问题）

- **T04 `cup_in_4` 和柜子里的杯子：** 已经按用户的意思改到 4 号柜顶，不再有"杯子在柜子里"的设计。
- **T22 冰箱门关不上：** 要靠你那边没推上来的 snap.patch（door_access.py 的 YAW_STEP）。请推上来再跑全量。
- **搬运滑落：** 开 sticky/gt 就没有了。
- **开局第一次收臂没到位（tuck）：** 只在 zihan 的机器上出现，13 次，都是第 0 步就失败。
- **place 只试附近的几个站位，不会换到另一边：** T23 台面那次就是这样。bench 已经绕开了。
- **T15 用盘子盖锅（`no_lid`、`lid_in_use`、`lid_elsewhere__covering_bowl`）：** 参数检查过了，但盘子是捏边拿起来的，cover 走 place 的捏边放置，要在锅沿上找"空边"，报 `no free edge spot on rim:handled_cooking_pot`（3/3）。要改的是 place 的捏边分支对 rim 目标的处理，是技能侧的事。
- **铅笔拿着却判成没拿（T05 `pen_in_use`，11-22）：** 铅笔从 6 号柜抓起来了，sticky 也焊上了（slip 0.001 m），但放书桌前 `holding` 检查看手指读数 [0.0, 0.0004] 判成没拿着，报 `PRECONDITION_FAILED`。细东西 + sticky 时 holding 检查应该信焊接。
- **碗叠到盘子上（T13 `copy_the_setting__plate_bowl_mug_left`，11-22 第一次走到这一步）：** 盘子捏边拿、`edge_held_flat` 放上餐桌都成功了；`stack_object(bowl, plate)` 松手时碗碰到桌面（4.7 mm），碗歪 15° 卡在盘沿上，报 `on support False`。`stack` 对准盘子的精度/放下高度的问题，技能侧。
- **`search_object` 的视点不检查能不能到：** 餐厅里 3 号柜的两个视点从来规划不到底盘路径（search limit），bench 那两个路线已经改成看餐桌，别的在餐厅里 search 的路线机器人一般从东边进来，用的是能到的那个视点。
- **偶发、没修（成功过很多次）：** T07 `broken_oatmeal`；T29 `several__toy_box` 拿着车走不到玩具箱（另外 3 个设计同路线成功）；T23 s13。
- **需要用户定的设计问题：**
  - T10 `after_dinner_clear` 的 `rubbish_leftovers` / `rubbish_mug`：锡纸盒 20×14 cm，垃圾桶口 26 cm，手爪撞桶沿差 3 mm，从没成功过。
  - T11 `fruit_plate_for_guests__tray_in_use`：托盘 42×36 cm，电视柜 tv_stand_2 只有 30 cm 深，放不上。

## 5. 11-21 夜到 11-22 上午的验证结果（sticky/gt，种子 10，一次只跑一个）

只跑有代表性的 episode，其余种子只做静态检查（1510/1510 通过）。

**成功：** T04 `two_guests__glass_in_cabinet`、`cup_in_4`、`plastic_only`；T28 `where_his_cup_is__in_cabinet`；T30 `bowl_put_away__mug_inside`；T25 `drink_in_fridge__juice`；T18 `one_bowl__glass_box`；T05 `errand_combined__pen_bedroom`；T03 `utensils_apart__bin_free`；T02 `block_put_away__in_4`；T17 `hide_both__two_pots`；T24 `no_apples_for_him__apple_in_use`、`two_kids__desk3_covered`；T11 `basket_gone_bowl_there`；T16 `box_in_use`。

**失败、已改布局（11-22 合进 main，结果见下面"今早改动的复跑"）：** T18 `door_stuck`、T05 `pen_or_pencil_cabinets`（两个）、T14 `next_in_series__on_bookcase`、T07 `two_portions__dining`、T03 `utensils_apart__bin_full_tray`。

**失败、不是布局（见第 4 节）：** T15 三个（盘子当盖）；T05 `pen_in_use` 铅笔 holding 检查；T13 `copy_the_setting__plate_bowl_mug_left` 碗叠盘子；T25 s11、T10 `rubbish_mug` 开局 tuck；T02 `block_put_away__in_6` 开 6 号柜门规划失败一次（这个门别处都开得了）；T27 `two_leftovers` 两个各一次（米饭在桌角、冰箱放置规划失败，以前成功过）。

**今早改动的复跑：**

（跑完补上）
