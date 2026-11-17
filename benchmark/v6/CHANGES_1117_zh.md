# 11-16/17 改动的 variant（给 muqingj：请跑物理）

背景：按 11-16 的会议，bench 的重点改成 **substitution（替换）**。我（zihan）逐个任务把不是替换的 variant 改成了替换，或者在原 variant 里加了替换。**场景布局、参考路线（GT）、成功条件和打分都写好了**，`define_tasks_v6 → validate_v6 → oracle_check` 静态全过，`pytest benchmark/v6/tests` 492 个通过。**物理还没验证完，请你跑。**

- 要跑的 batch：`benchmark/v6/batches/changed_1117.json`，66 条，每个改过的布局取一个 seed，profile `sticky/gt`。
  ```
  python benchmark/run_episode.py --tasks benchmark/v6/tasks.json --batch benchmark/v6/batches/changed_1117.json --out <out> --jobs 1
  ```
- 每个 variant 的“替换在哪”和四类（缺失 / 损坏 / 被占用 / 能力不足）：`benchmark/v6/SUBSTITUTION_zh.md`。打分：`SCORING_zh.md`，场景说明：`VARIANTS_zh.md`。
- 渲染图：`~/Pictures/<任务>/<variant>/`（zihan 机器上），旧图在 `~/Pictures/renders_stale_2026-11-16/`。
- 我在 zihan 机器上只跑了少数几条（这台机器第一步 tuck 和你那边不一样，见 `PHYSICS_EXCLUDED_zh.md` 的“机器差异”），结果写在下面“已跑”一列。

## 11-17 恢复的（原样加回，和替换版并存，物理同 11-16 以前）

T04 `x6_gd_cup_in_cabinets`、T05 `check_desk_first`、T12 `castle_stays`、T14 `next_in_series`（原版）。它们测“有个像的东西，但用不了或不该用”，场景、路线、打分都和 1d882fa 一样；T04 x6 的 cup_in_4 仍在 PHYSICS_EXCLUDED（A1）。

## 删掉 / 整个换掉的

| 任务 | 变化 |
|---|---|
| T15 | 整个任务换掉：`T15_book_face_up`（翻书）→ `T15_cover_the_pot`（盖锅盖），4 个 variant 都是新的 |
| T16 | 整个任务换掉：`T16_rolling_pin_at_edge`（滚擀面杖）→ `T16_pack_snack_box`（装零食盒），4 个 variant 都是新的 |
| T17 | `hide_both` → `pot_in_use`，`hide_somewhere` → `no_pot` |
| T18 | 整个任务换掉：`T18_check_cabinet_dishes`（看一眼）→ `T18_set_out_bowls`（摆碗勺），5 个 variant 都是新的 |

## 改过的 variant

“风险”是我估计物理上最可能出问题的地方。

| 任务 | variant（布局：seed） | 改了什么 | GT 路线要点 | 风险 | 已跑（zihan 机器） |
|---|---|---|---|---|---|
| T01 | `homework_on_island`（原 which_book）<br>living: 10,11,12,15,17<br>bedroom: 13,14,16,18,19 | 岛台上只有作业本+铅笔，书在客厅电视柜 / 卧室书柜 | 去别的房间拿书 → 餐桌 | 低（拿书、放餐桌都是原有路线） | 两条都 OK |
| T02 | `tower_for_kid`<br>study: 10,16-19<br>counter: 11-15 | 近处餐桌摆了 19 件杂物（玩具箱、篮子、托盘、盘子、书、麦片…），塔改搭在西边餐厅那张餐桌（离边 10 cm） | 积木 A 放远桌 (-7.64, 7.80) 当底座，再找另外两块叠上 | 远桌叠积木；杂物开局是否稳定 | 两条都 OK（2035 s / 2515 s） |
| T03 | `bin_full`（原 utensils_apart）<br>counter: 10,12,17-19<br>dining: 11,13-16 | 卧室宽收纳箱装满玩具（熊、车、鸭、两块积木）；书房书桌前沿一个小浅托盘（27×20 cm）代替 | 先找勺子、丢进托盘，再放擀面杖 | 往托盘里放 / 丢；箱里玩具开局是否稳定 | 前两轮失败：大托盘放在桌子靠里，放不到（已改成桌沿小托盘，未再跑） |
| T04 | `two_guests`<br>study: 10,12,16,17,19<br>dining: 11,13-15,18 | 第二个杯子的替代品：马克杯 / 孩子塑料杯 / 岛台空碗；高处 3 个马克杯拿掉 | 玻璃杯放饮品角 → 找马克杯放旁边 | 低 | 未跑 |
| T04 | `no_cup_in_cabinets`（原 x6_gd_cup_in_cabinets）<br>cup_on_dining: 10,12,13,15,16<br>cup_on_desk: 11,14,17-19 | 两个矮柜里只有盘子，没有杯子；孩子塑料杯在餐桌 / 书桌；岛台有空碗和果汁 | 开两个柜看、关上 → 拿塑料杯到饮品角 | 开柜看（原有）；不再从柜里拿杯子，原来排除表 A1 的问题没了 | 未跑 |
| T05 | `no_pencil`（替换 v5 no_pen_pencil_away）<br>pen_dining: 10-12,15,16<br>pen_bedroom: 13,14,17-19 | 要铅笔，家里没有，用钢笔 | 找钢笔 → 书桌 | 低 | 未跑 |
| T05 | `pen_in_use`（原 check_desk_first）<br>pencil_bedroom: 10,11,14,15,18<br>pencil_living: 12,13,16,17,19 | 唯一的钢笔压在餐桌上奶奶的笔记本上（z 0.879），用铅笔 | 找铅笔 → 书桌 | 钢笔叠在本子上开局是否稳定 | 未跑 |
| T05 | `pens_for_two`（原 all_pens）<br>pen_dining: 10-12,16,19<br>pen_living: 13-15,17,18 | 书房、卧室书桌各一本作业本；一支钢笔两支铅笔 | 钢笔放书房本子旁，铅笔放卧室书桌 (6.20, -5.50) 本子旁 | 卧室书桌放置 | 未跑 |
| T05 | `pens_per_notebook`<br>two_short: 10,11,15-17<br>one_short: 12-14,18,19 | 3 本作业本；钢笔只有 1 或 2 支（seed），其余用铅笔补 | 逐支拿到书桌前沿每本本子旁 | 低 | 未跑 |
| T05 | `errand_combined`<br>pencil_dining: 10,12,13,15,18<br>pencil_bedroom: 11,14,16,17,19 | 没有钢笔，用铅笔；顺路带马克杯回厨房 | 铅笔 → 书桌，马克杯 → 厨房台面 | 低 | 未跑 |
| T06 | `both_spots_full`（原 display_row）<br>block_at_hand: 10,11,13-15<br>block_away: 12,16-19 | 靠墙矮柜顶（4 件）和电视柜顶（6 件）摆满；积木放 4 号矮柜顶 (1.40, 0.45) | 看两处 → 积木到 4 号柜 | 杂物开局是否稳定 | 未跑 |
| T10 | `trash_full`（新加；trash_moved 已加回，不变）<br>living: 10,11,16-18<br>dining: 12-15,19 | 垃圾桶里叠了零食盒、两个罐、纸巾盒、饭盒到桶口；罐子丢进回收箱（宽收纳箱，内有塑料杯，在电视柜 / 餐桌） | 拿罐 → 看垃圾桶 → 找回收箱 → 丢进去 | **垃圾桶里叠放的东西开局是否稳定**（z 0.037–0.222） | 未跑 |
| T11 | `no_apple_for_kid`（原 leave_one_for_kid）<br>全部 seed 同一布局 | 没有苹果，桌上香蕉和橙子，指令说孩子不爱吃橙子 | 香蕉 → 书桌 | 低 | 未跑 |
| T11 | `fruit_plate_for_guests`<br>tray_by_table: 10,11,13,17,19<br>tray_in_study: 12,14-16,18 | 没有托盘，用小收纳盒；先把空盒放电视柜再装苹果、橙子 | 盒子 → 电视柜 → 水果逐个放进盒 | 拿小收纳盒（rim_pinch_rect）、往盒里放水果 | 未跑 |
| T12 | `bedtime_toy`（替换 v5 duck_in_study）<br>teddy_there: 10,12,14,15,19<br>no_teddy: 11,13,16-18 | 要能抱着睡的玩具；有熊拿熊，没熊拿鸭子 | 电视柜 → 床头书架 (2.10, -4.78) | 低（T26 bear_to_bed 同路线） | 未跑 |
| T13 | `finish_the_table`<br>adult_and_kid: 10,13,15,17,19<br>kid_seat: 11,12,14,16,18 | 没有第二个塑料杯，孩子位的杯子用小碗（台面 (-0.30, 8.05)）；“只剩大人位”的布局删掉 | 碗、小碗放到孩子位勺子旁 | 低 | 未跑 |
| T14 | `kids_shelf_full`（原 stack_them_stably）<br>全部 seed 同一布局 | 孩子书架三层各 6 本书摆满；书放到床头书架 (2.10, -4.85) | 看孩子书架 → 床头书架 | 书架里 18 本书开局是否稳定 | 未跑 |
| T14 | `homework_stays`<br>全部 seed 同一布局 | 两个厨房台面上各一根擀面杖和一个碗（有人在做饭）；马克杯放厨房矮柜 6 号顶 (3.43, 0.45) | 书上书架 → 马克杯到柜顶 | 低 | 未跑 |
| T14 | `no_second_red_book`（next_in_series 的替换版，原版已恢复）<br>green_on_bookcase: 10,11,14,17,19<br>green_on_tall_shelf: 12,13,15,16,18 | 没有第二本红皮书，拿孩子的绿皮书 | 红书上书架 → 绿皮书到书桌 | 高书架 shelf_1 取书 | 未跑 |
| T14 | `whose_book`<br>blue_book: 10,14,16,18<br>both: 11,15,17<br>paperback: 12,13,19 | 平装书架下三层各 11 本平装书摆满，只有最高层（1.17 m）有空；平装书改放床头书架 | 平装书 → 看平装书架 → 床头书架 | 33 本书开局是否稳定 | 未跑 |
| T15 | `lid_by_pot`（对照，新任务）<br>全部 seed | 锅在左灶眼，锅盖在岛台 (8.05, 1.80) | 拿锅盖 → cover | 低（T09 同动作） | 未跑 |
| T15 | `lid_elsewhere`<br>counter: 10,12,15-17<br>dining: 11,13,14,18,19 | 锅盖在餐桌 / 厨房台面 | 找锅盖 → cover | 低 | 未跑 |
| T15 | `no_lid`<br>全部 seed | 没有锅盖，用台面上的盘子 `plate_counter_a` 盖；岛台上有书 | 拿盘子 → cover（cover 接受任何拿在手里的东西） | **用盘子 cover**：盘子 thickness_pinch 拿起、盖到锅沿上居中 | 未跑 |
| T15 | `lid_in_use`<br>全部 seed | 右灶眼加一口汤锅（soup_pot），锅盖盖在它上面（z 0.8591）；用盘子盖左边的锅 | 同 no_lid | 两口锅并排、锅盖叠在右锅上开局是否稳定；用盘子 cover | 未跑 |

| T16 | `box_on_counter`（对照，新任务）<br>全部 seed | 零食盒 = 小收纳盒，在厨房台面 (-0.10, 7.30)；苹果在餐桌 (3.70, 6.30) | 空盒先放书桌 (-0.70, -6.20)，再把苹果放进盒 | **往小收纳盒里放苹果**（第一次） | 未跑 |
| T16 | `box_in_cabinet`<br>全部 seed | 零食盒在靠墙矮柜 6 号内层板 (3.50, 0.40) | 开柜 → 取盒 → 关柜 → 书桌 → 装苹果 | 从柜内层板取盒（之前柜内取杯子有问题） | 未跑 |
| T16 | `no_box`<br>全部 seed | 没有零食盒；碗在台面 (-0.10, 7.70)，大收纳箱在电视柜 | 碗 → 书桌 → 苹果放进碗 | **往碗里放苹果**（第一次）；拿碗 | 未跑 |
| T16 | `box_in_use`<br>全部 seed | 零食盒里叠放两支铅笔和一块积木（z 1.009）；碗在旁边 | 同 no_box | 盒里东西开局是否稳定 | 未跑 |
| T17 | `pot_in_use`（原 hide_both）<br>全部 seed | 灶上加一口装汤的锅（soup_pot）；空锅在餐桌 (3.548, 5.715)，锅盖在岛台 (7.25, 1.85)（同 T09 pot_in_use） | 找空锅 → hide（积木进锅、拿锅盖、盖上） | 在餐桌上 hide | 未跑 |
| T17 | `no_pot`（原 hide_somewhere）<br>全部 seed | 锅和锅盖都拿掉 | 开 4 号矮柜 → 积木（侧抓）放内层板 (1.40, 0.42) → 关柜 | 往柜内层板放（原 hide_somewhere 的 lid_away 布局同路线） | 未跑 |

| T18 | `bowls_in_cabinet`（对照，新任务）<br>全部 seed | 靠墙矮柜 6 号内层板两只碗 (3.32/3.60, 0.40)；台面两把勺子 (0.10, 7.30/7.55) | 开柜 → 碗 1 → 餐桌 (3.66, 6.20) → 碗 2 → 关柜 → 餐桌 (3.66, 6.75) → 勺子 ×2 | 从柜内层板取碗；柜门开着时来回 | 未跑 |
| T18 | `bowls_apart`<br>全部 seed | 第二只碗在 4 号矮柜内层板 (1.40, 0.42) | 两个柜子各开一次 | **4 号柜内层板净空 0.30 m**（之前那里取杯子失败过） | 未跑 |
| T18 | `one_bowl`<br>全部 seed | 只有一只碗；玻璃保鲜盒在台面 (0.19, 7.85)，探出台面前沿（thickness_pinch 要探出） | 碗 → 餐桌 → 保鲜盒 → 餐桌 | 保鲜盒捏取 | 未跑 |
| T18 | `bowl_in_use`<br>全部 seed | 碗 2 里有两颗小番茄（z 0.425） | 同 one_bowl | 柜里碗里番茄开局是否稳定 | 未跑 |
| T18 | `door_stuck`<br>全部 seed | **新字段 `locked_articulated: ["kitchen_cabinet_6"]`：需要你在 sim 里支持（open 这个门时失败/反馈“卡住了”）**；碗在 4 号矮柜 (1.25/1.55, 0.42) | 看 6 号柜 → 开 4 号柜拿两只碗 | 锁门还没实现；4 号柜内层板取碗 | 未跑（锁门未实现前不计入统计） |

| T19 | `recycle_bin_full`（原 m_can_in_dining_room） | 回收箱里竖着两盒麦片、两个塑料杯、两个罐（z 0.718）；空收纳箱在电视柜 (7.30, 0.40) | 罐、泡沫块丢进空收纳箱 | 回收箱内物品开局是否稳定 | 未跑 |
| T19 | `bin_out_of_reach`（原 x6_gd_can_put_away） | 回收箱在 large_shelf_6 顶 (5.12, 8.42)，1.42 m；小收纳箱在餐桌 (3.62, 6.30) | 看高架子 → 丢进小收纳箱 | 低 | 未跑 |

| T20 | `juice_finished`（新加） | 果汁瓶放进厨房旁新加的垃圾桶 (9.05, 1.12)，z 0.037；汽水罐在电视柜 (7.30, 0.36)。T20 指令改成“早饭要喝果汁，把果汁瓶拿到早餐桌上，立着放” | 看垃圾桶 → 汽水 → 早餐桌 | 瓶子在垃圾桶里开局是否稳定 | 未跑 |
| T20 | `juice_in_use`（新加） | 果汁瓶在西边餐桌 (-7.70, 8.05)，爷爷的杯子和碗旁；汽水在电视柜 | 看西边餐桌 → 汽水 → 早餐桌 | 低 | 未跑 |
| T21 | `tissue_in_use`（新加） | 纸巾盒在西边餐桌 (-7.68, 7.95) 爷爷座位旁；干海绵在岛台 (8.00, 1.80)；汤在东边餐桌 | 看西边餐桌 → 岛台海绵 → 东边餐桌 | 低 | 未跑 |
| T22 | `basket_in_use`（新加） | 果篮在岛台 (7.10, 1.78)，篮里三块 wooden_block + 一个 toy_block，z 0.874（篮底 1.2 cm）；空托盘在岛台 (7.60, 1.75) | 果汁进冰箱 → 看岛台 → 苹果进托盘 | **篮里积木开局是否稳定**；托盘和果篮挨着时放苹果是否碰到果篮 | 未跑 |
| T22 | `basket_out_of_reach`（新加） | 果篮在 large_shelf_6 顶 (5.12, 8.42)，转 90°（架顶宽 0.34 m，篮宽 0.30 m）；托盘在岛台 (7.20, 1.75) | 果汁进冰箱 → 看高架 → 苹果进托盘 | 果篮在架顶开局是否稳定 | 未跑 |
| T23 | `belongs_on_floor`（改） | 积木 wooden_block 在地上 (-0.95, 8.10)，洗衣篮 (-1.15, 8.40)、垃圾桶 (-1.10, 7.25) 不变；空小收纳箱在电视柜 (7.30, 0.40)；没有玩具箱 | 勺子回台面 → 积木进小收纳箱 | 低 | 未跑 |
| T23 | `toy_box_full`（新加） | 卧室书架上的宽收纳箱照 T03 bin_full 装满（泰迪、车、鸭子、两块积木，z 0.718）；空小收纳箱在电视柜 | 勺子回台面 → 拿积木 → 看卧室玩具箱 → 小收纳箱 | 照搬 T03 布局 | 未跑 |
| T23 | `no_toy_box`（新加） | 同上无玩具箱，空小收纳箱在电视柜 | 勺子回台面 → 积木进小收纳箱 | 低 | 未跑 |
| T23 | 删掉 dropped_out_of_view、only_this_room、dropped_in_two_rooms（用户要求） | | | | 不用跑 |
| T24 | `apple_in_use`（新加） | 苹果在西边餐桌 (-7.70, 8.05) 爷爷的碗和杯旁；香蕉在东边餐桌 (3.30, 7.10)；指令点名苹果 | 找苹果 → 看两张餐桌 → 香蕉送书桌 | 低 | 未跑 |
| T24 | `apple_on_floor`（新加，condition `resource_broken`） | 苹果在厨房地上 (-0.85, 7.70)；橙子在东边餐桌 (3.30, 7.10) | 看餐桌 → 找苹果（厨房） → 橙子送书桌 | 苹果在地上滚不滚 | 未跑 |
| T24 | 删掉 no_apples_for_him、fruit_out_of_view、two_kids（用户要求） | | | | 不用跑 |

## 我这边的约定

- 布局都按“东西放在离能站的边 20 cm 以内”摆；堆满的台面 / 书架用脚本确认过放不下（间隔都 ≥ 1 cm，不互相挤）。
- 如果某个布局物理上不行（够不到、开局倒、放不进），告诉我是哪一步，我来改布局；skill 的问题你那边定。
