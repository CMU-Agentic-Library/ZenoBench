# v6 改成替换的 variant（2026-11-16 起）

每个 variant 一句话：点名的东西或地方为什么用不了 → 换成什么。类别按 11-16 会议的四类：缺失（不存在或找不到）、损坏（在但不能正常用）、被占用（当前不可用，包括放的地方被占满）、能力不足（能用但达不到要求，比如装不下、够不着）。打分仍是 好 / 次好 / 最不好（`SCORING_zh.md`）。

| 任务 | variant | 类别 | 替换在哪 |
|---|---|---|---|
| T01 | homework_on_island（原 which_book） | 缺失 | 岛台上只有孩子的作业本，不是能读的书 → 去别的房间拿一本真书 |
| T02 | tower_for_kid | 被占用 | 近处餐桌堆满杂物，塔放不稳 → 换到西边餐厅那张餐桌搭 |
| T03 | bin_full（原 utensils_apart） | 被占用 | 宽收纳箱装满玩具，放不下擀面杖 → 改用书桌上的托盘 |
| T04 | two_guests | 缺失 | 只有一个玻璃杯 → 第二个从替代品里挑：马克杯 > 孩子的塑料杯 > 早餐碗 |
| T04 | no_cup_in_cabinets（新加；x6_gd_cup_in_cabinets 已恢复） | 缺失 | 柜子里没有杯子，家里也没有马克杯 → 孩子的塑料杯（碗最差） |
| T05 | no_pencil（原 no_pen_pencil_away） | 缺失 | 要铅笔，家里没有 → 钢笔 |
| T05 | pen_in_use（新加；check_desk_first 已恢复） | 被占用 | 唯一的钢笔压在奶奶正在写的清单上 → 铅笔 |
| T05 | pens_for_two（原 all_pens） | 缺失 | 两个孩子各要一支钢笔，只有一支 → 另一个给铅笔 |
| T05 | pens_per_notebook | 缺失 | 钢笔比本子少一支或两支（seed） → 缺的用铅笔补 |
| T05 | errand_combined | 缺失 | 要钢笔，家里没有 → 铅笔（顺路带马克杯回厨房不变） |
| T06 | both_spots_full（原 display_row） | 被占用 | 指令说的矮柜顶和电视柜顶都摆满了 → 摆到 4 号矮柜顶 |
| T10 | trash_full（新加；trash_moved 11-17 加回，并列） | 被占用 | 垃圾桶塞满到桶口 → 扔进回收箱 |
| T11 | no_apple_for_kid（原 leave_one_for_kid） | 缺失 | 孩子要的苹果没了 → 香蕉（他不爱吃橙子） |
| T11 | fruit_plate_for_guests | 缺失 | 家里没有托盘 → 小收纳盒装水果 |
| T12 | bedtime_toy（原 duck_in_study） | 缺失 | 要能抱着睡的玩具；seed 有泰迪熊（用熊）或没有 → 没有时用软的橡皮鸭（小车最差） |
| T13 | finish_the_table | 缺失 | 孩子位要塑料杯，家里没有第二个 → 小碗顶上（马克杯次之） |
| T14 | kids_shelf_full（原 stack_them_stably） | 被占用 | 孩子书架每层都满了 → 卧室另一个书架 |
| T14 | homework_stays | 被占用 | 杯子该放的厨房台面有人在做饭 → 厨房矮柜顶 |
| T14 | no_second_red_book（原 next_in_series 的替换版；原版已恢复） | 缺失 | 同套的下一本红皮书不在家 → 孩子的另一套（绿皮/蓝皮）书，不拿大人的平装书 |
| T14 | whose_book | 能力不足 | 平装书的书架只有最高一层有空，够不着 → 放到别的书架（不放进精装书那个） |
| T15 | no_lid（新任务：盖锅盖，替换翻书） | 缺失 | 家里没有锅盖 → 用盘子盖（用书最差） |
| T15 | lid_in_use（新任务） | 被占用 | 锅盖盖在另一锅炖菜上 → 用盘子盖汤锅，不拿炖菜的盖子 |
| T16 | no_box（新任务：装零食盒，替换滚擀面杖） | 缺失 | 家里没有零食盒 → 用碗装（大收纳箱最差） |
| T16 | box_in_use（新任务） | 被占用 | 零食盒里装着孩子的蜡笔和积木 → 用碗装 |
| T17 | pot_in_use（原 hide_both） | 被占用 | 灶上的锅装着汤 → 积木藏进餐桌那口空锅 |
| T17 | no_pot（原 hide_somewhere） | 缺失 | 家里没有锅 → 藏进厨房矮柜关上门 |
| T18 | one_bowl（新任务：摆碗勺，替换只看一眼） | 缺失 | 只有一只碗 → 玻璃保鲜盒（盘子最差） |
| T18 | bowl_in_use（新任务） | 被占用 | 一只碗装着剩菜 → 保鲜盒 |
| T18 | door_stuck（新任务） | 损坏 | 靠墙矮柜门卡住打不开 → 去 4 号矮柜拿碗（sim 要支持锁住的门） |
| T19 | recycle_bin_full（原 m_can_in_dining_room） | 被占用 | 回收箱塞满了 → 电视柜上的空收纳箱 |
| T19 | bin_out_of_reach（原 x6_gd_can_put_away） | 能力不足 | 回收箱在 1.42 m 高架子顶上够不着 → 餐桌上的小收纳箱 |
| T20 | juice_finished（新加） | 缺失 | 果汁喝完了 → 汽水（拿空瓶最差） |
| T20 | juice_in_use（新加） | 被占用 | 果汁在爷爷座位旁正在喝 → 汽水 |
| T21 | tissue_in_use（新加） | 被占用 | 纸巾在爷爷座位旁正在用 → 岛台上的干海绵 |
| T22 | by_kind | 可互换（不属四类） | 苹果、零食放果篮或矮柜都算，同一件东西有几个都对的去处 |
| T22 | two_spots | 可互换（不属四类） | 同 by_kind，东西分在两处 |
| T22 | basket_missing | 缺失 | 家里没有果篮 → 岛台上的托盘 |
| T22 | tray_elsewhere | 缺失 | 没有果篮 → 西边餐厅的托盘（有橙子直接放；被书占满先把书放回书架） |
| T22 | basket_in_use（新加） | 被占用 | 果篮里装着孩子的积木 → 托盘（苹果混进玩具最差） |
| T22 | basket_out_of_reach（新加） | 能力不足 | 果篮在 1.41 m 高架子顶上够不着 → 岛台上的托盘 |
| T23 | by_kind | 可互换（不属四类） | 勺子放哪个厨房台面或岛台都算 |
| T23 | belongs_on_floor（改） | 缺失 | 没有玩具箱，手边的洗衣篮不是替代品 → 电视柜上的小收纳箱 |
| T23 | toy_box_full（新加） | 被占用 | 玩具箱塞满（泰迪熊露出）→ 空的小收纳箱 |
| T23 | no_toy_box（新加） | 缺失 | 没有玩具箱 → 小收纳箱（只放桌面最差） |
| T24 | dinner_soon | 能力不足（此时不合适） | 快吃晚饭了，零食不合适 → 苹果 |
| T24 | where_is_he | 可互换（送的位置） | 孩子在哪张书桌按作业本决定 |
| T24 | apple_in_use（新加） | 被占用 | 唯一的苹果爷爷正在吃 → 香蕉 |
| T24 | apple_on_floor（新加） | 损坏 | 苹果掉地上脏了 → 橙子 |
| T25 | cold_one | 能力不足（此时不合适） | 天热，常温果汁不合适 → 冰箱里冰的那瓶 |
| T25 | cups_for_two | 缺失 | 普通杯子不够两个 → 餐厅的马克杯补 |
| T25 | little_guest | 能力不足（不合适） | 瓷杯给小朋友不合适 → 塑料杯 |

T15 整个换成了新任务“盖锅盖”（T15_cover_the_pot）：lid_by_pot（对照）、lid_elsewhere（锅盖在别处，去找）、no_lid、lid_in_use。T16 整个换成了新任务“装零食盒”（T16_pack_snack_box）：box_on_counter（对照）、box_in_cabinet（去柜子里找）、no_box、box_in_use。

目前“损坏”有 T07 microwave_broken 和 T18 door_stuck，后面的任务里可以有意识地补几个（比如一个灶眼打不着火）。

11-17 恢复（“有个像的东西，但用不了或不该用”，和上面的替换版并存）：T04 x6_gd_cup_in_cabinets、T05 check_desk_first、T12 castle_stays、T14 next_in_series（原版）。T01 which_book 仍是 homework_on_island，T19 lookalike_bin 一直保留。
