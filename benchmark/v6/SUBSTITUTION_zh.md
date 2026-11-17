# v6 替换分类（2026-11-17 定稿）

每个变体用一句话写：理想的东西或去处 → 为什么用不了 → 换成什么。对照变体不在表里，全部保留。

## 依据（11-17 会议纪要）

- **测的是替换**：指令点名理想物，并说清目的（"用微波炉把燕麦热一下"）。理想物在的是对照，理想物不可用的是替换变体。
- **触发替换的原因**归三类：缺失、被占用、能力不足。原来的"损坏"并进能力不足。原因要让 agent 自己能发现（看到、试了不行），不在指令里写退路。
- **打分分四档**：
  - ideal：点名的东西，或最合适的东西
  - moderate：合理的替代
  - bad：任务能完成，但人一般不会这么选
  - else：任务完成不了
- 前三档都算成功，只是得分不同。"做没做成"和"做得多好"分开算。
- 场景里没有 ideal 时，moderate 不会自动升为 ideal。
- 每个变体都要讲清楚卡住模型的是哪一点，以及它为什么不得不替换。

另外有一组**去处替换**：东西不变，换的是放到哪，由场景里的线索决定。11-17 起，原来的"可互换"并进这一组。

## 被占用

理想的东西在，但正被别人用着，或者被别的东西占着。

| 任务 | 变体 | 理想 → 为什么用不了 → 替代 |
|---|---|---|
| T01 | no_room_fallback | 餐桌每个座位旁都被餐具占了 → 先收进书柜 |
| T02 | tower_for_kid | 近处餐桌堆满杂物，塔放不稳 → 换到西边餐厅那张餐桌搭 |
| T03 | bin_full | 宽收纳箱装满玩具，放不下擀面杖 → 书桌上的托盘 |
| T03 | which_bin_by_contents | 两个一模一样的箱子，一个装着玩具 → 放进装厨具的那个 |
| T04 | clear_the_drinks_spot | 饮品角被燕麦碗和锅盖占着 → 先收走，再放杯子 |
| T05 | pen_in_use | 唯一的钢笔压在奶奶正在写的清单上 → 铅笔 |
| T06 | both_spots_full | 指令说的矮柜顶和电视柜顶都摆满了 → 4 号矮柜顶 |
| T06 | display_spot_or_tv | 柜顶前排被盒子挡住 → 摆前排空处或电视柜 |
| T07 | microwave_holds_pot | 微波炉里放着汤锅 → 用灶加热 |
| T09 | pot_in_use | 灶上的锅装着昨天的汤 → 餐厅那口空锅 |
| T10 | keep_kids_can | 两罐一样的易拉罐，孩子那罐正在喝 → 只扔另一罐 |
| T10 | trash_full | 垃圾桶塞满到桶口 → 回收箱 |
| T12 | bins_capacity | 一个小箱已经装满积木 → 玩具放进空的那个 |
| T12 | castle_stays | 城堡里的积木明天还要接着搭 → 只收散落的积木 |
| T12 | where_his_cup_is | 台面上的瓷杯、马克杯是别人的 → 去矮柜拿他自己的塑料杯 |
| T14 | kids_shelf_full | 孩子书架每层都满了 → 卧室另一个书架 |
| T14 | homework_stays | 该放杯子的厨房台面有人在做饭 → 厨房矮柜顶 |
| T15 | lid_in_use | 锅盖盖在另一锅炖菜上 → 用盘子盖汤锅 |
| T16 | box_in_use | 零食盒里装着蜡笔和积木 → 用碗装 |
| T17 | pot_in_use | 灶上的锅装着汤 → 积木藏进餐桌那口空锅 |
| T18 | bowl_in_use | 一只碗装着剩菜（seed：番茄 / 燕麦）→ 保鲜盒 |
| T19 | recycle_bin_full | 回收箱塞满了 → 电视柜上的空收纳箱 |
| T20 | juice_in_use | 果汁在爷爷座位旁，他正在喝 → 汽水 |
| T21 | tissue_in_use | 纸巾在爷爷座位旁，他正在用 → 岛台上的干海绵 |
| T22 | basket_in_use | 果篮里装着孩子的积木 → 托盘 |
| T23 | toy_box_full | 玩具箱塞满了（泰迪熊露出来）→ 空的小收纳箱 |
| T24 | apple_in_use | 唯一的苹果爷爷正在吃 → 香蕉 |

## 能力不足

东西在，也没人在用，但达不到要求：太小、够不着、坏了，或者不是要的那种。

| 任务 | 变体 | 理想 → 为什么用不了 → 替代 |
|---|---|---|
| T01 | table_seats | 座位之间的空太窄，远端的空不挨着座位 → 放在挨着座位的宽空位 |
| T01 | which_table | 另一张桌子不是客人吃饭的那张 → 放有早餐的那张 |
| T01 | reader_seat | 别的座位旁坐的不是用马克杯的那位客人 → 放他旁边 |
| T02 | crowded_use_another | 积木 B 卡在满碗旁，拿它会碰洒 → 用屋里另一块积木 |
| T02 | block_put_away | 积木 A 探出边缘，不能当底座 → 用别的当底，第三块去柜里拿 |
| T03 | small_bin_or_bedroom_bin | 小箱只有 22 cm，放不下擀面杖 → 卧室的宽箱 |
| T04 | x6_gd_cup_in_cabinets | 马克杯带把手，要的是不带把手的 → 开柜拿玻璃杯 |
| T05 | check_desk_first | 桌上只有铅笔，要的是钢笔 → 去卧室拿钢笔 |
| T05 | x6_gd_pen_or_pencil_cabinets | 先找到的是铅笔，要的是钢笔 → 开另一个柜拿钢笔 |
| T05 | homework_ready | 书不是作业本，泰迪熊也不是文具 → 拿本子和笔 |
| T06 | seen_from_bed | 床头柜的盒子后面，从枕头上看不见 → 摆到看得见的位置 |
| T07 | microwave_broken | 微波炉能转但不加热（原"损坏"）→ 用灶 |
| T07 | vessel_decides_appliance | 容器不能进微波炉或不能上灶 → 换另一个电器 |
| T07 | two_portions | 瓷碗只能用微波炉，铁锅只能上灶 → 各用各的 |
| T12 | his_things_whose | 大人的小说不是他的 → 只拿他的图画书 |
| T14 | within_kids_reach | 同一套书在高架子上，孩子够不着 → 放到孩子够得着的书架 |
| T14 | next_in_series | 其他颜色的书不是这一套的 → 找红皮的那本 |
| T14 | whose_book | 平装书书架只有最高一层有空，够不着 → 放到别的书架（不放进精装书那个） |
| T18 | plate_not_bowl | 盘子盛不了汤 → 去 4 号柜找第二只碗 |
| T18 | door_stuck | 柜门卡住打不开（原"损坏"）→ 去 4 号矮柜拿碗 |
| T19 | lookalike_bin | 长得一样的箱子是玩具箱 → 放进真正的回收箱 |
| T19 | bin_out_of_reach | 回收箱在 1.42 m 高的架子顶上，够不着 → 餐桌上的小收纳箱 |
| T22 | not_shopping | 小车和绘本不是买回来的东西 → 只收果汁 |
| T22 | basket_out_of_reach | 果篮在 1.41 m 高的架子顶上，够不着 → 岛台上的托盘 |
| T24 | dinner_soon | 快吃晚饭了，零食不合适 → 苹果 |
| T24 | apple_on_floor | 苹果掉在地上脏了（原"损坏"）→ 橙子 |
| T25 | cold_one | 天热，常温果汁不合适 → 冰箱里冰的那瓶 |
| T25 | little_guest | 瓷杯给小朋友用不合适 → 塑料杯 |

## 缺失

理想的东西不存在，或者不在该在的地方。

| 任务 | 变体 | 理想 → 为什么用不了 → 替代 |
|---|---|---|
| T01 | homework_on_island | 岛台上只有孩子的作业本，没有能读的书 → 去别的房间拿一本 |
| T02 | third_toy_elsewhere | 只有两块积木（海绵不是玩具）→ 另一个房间的鸭子或积木 |
| T02 | tower_for_kid_duck | 只有两块积木 → 鸭子当第三层 |
| T03 | no_bin_substitute | 家里没有能用的收纳箱（小箱放不下）→ 果篮或托盘 |
| T04 | no_cup | 没有杯子 → 马克杯 |
| T04 | two_guests | 只有一个玻璃杯 → 第二个用马克杯（塑料杯次之，碗最差） |
| T04 | no_cup_in_cabinets | 柜子里没有杯子，家里也没有马克杯 → 孩子的塑料杯（碗最差） |
| T05 | no_pencil | 要铅笔，家里没有 → 钢笔 |
| T05 | pens_for_two | 两个孩子各要一支钢笔，只有一支 → 另一个给铅笔 |
| T05 | pens_per_notebook | 钢笔比本子少一到两支（看 seed）→ 缺的用铅笔补 |
| T05 | errand_combined | 要钢笔，家里没有 → 铅笔 |
| T10 | trash_moved | 垃圾桶不在老地方 → 去餐厅或卫生间找到再扔 |
| T11 | basket_missing | 没有果篮 → 书桌上的托盘 |
| T11 | no_apple_for_kid | 孩子要的苹果没了 → 香蕉（他不爱吃橙子） |
| T11 | fruit_plate_for_guests | 家里没有托盘 → 用小收纳盒装水果 |
| T12 | bedtime_toy | 没有泰迪熊（看 seed）→ 软的橡皮鸭（小车最差） |
| T13 | no_cup | 没有杯子 → 马克杯 |
| T13 | copy_the_setting | 照着已摆好的位子摆，缺杯子 → 马克杯 |
| T13 | finish_the_table | 孩子位要塑料杯，家里没有第二个 → 小碗（马克杯次之） |
| T14 | no_second_red_book | 同套下一本红皮书不在家 → 孩子另一套书，不拿大人的平装书 |
| T15 | no_lid | 没有锅盖 → 用盘子盖（用书最差） |
| T16 | no_box | 没有零食盒 → 用碗装（大收纳箱最差） |
| T17 | no_pot | 没有锅 → 藏进厨房矮柜并关上门 |
| T18 | one_bowl | 只有一只碗 → 第二份用别的容器（seed：玻璃保鲜盒 / 马克杯） |
| T18 | no_bowl | 没有干净的碗 → 马克杯和保鲜盒 |
| T20 | juice_finished | 果汁喝完了 → 汽水（拿空瓶最差） |
| T21 | no_tissue | 没有纸巾 → 干海绵 |
| T22 | tray_elsewhere | 没有果篮 → 西边餐厅的托盘（托盘被书占着就先把书放回书架） |
| T23 | belongs_on_floor | 没有玩具箱，手边的洗衣篮不能当替代 → 电视柜上的小收纳箱 |
| T23 | no_toy_box | 没有玩具箱 → 小收纳箱（只放在桌面上最差） |
| T25 | cups_for_two | 普通杯子不够两个 → 用餐厅的马克杯补 |

## 去处替换

东西不变，换的是放到哪，由场景里的线索决定。原来的"可互换"也归这组。

| 任务 | 变体 | 线索 → 去处 |
|---|---|---|
| T08 | wipe_and_sort | 擦完后东西按类放回 |
| T08 | return_sponge_home | 海绵放回它原来的地方 |
| T08 | which_surface | 擦脏的那个台面 |
| T10 | after_dinner_clear | 饭后收桌，按类放回 |
| T10 | guests_coming | 客人要来，收到看不见的地方 |
| T10 | clear_table_for_dinner | 腾出桌子准备吃饭（seed：小车 / 小车加餐具 / 只有餐具 / 好几样 / 作业） |
| T12 | his_things_by_kind | 他的东西按类放，几个去处都算对 |
| T12 | his_room | 送到他的房间（seed：东卧 / 南卧） |
| T12 | cup_to_bedside | 杯子放到他的床头（seed：东床 / 南床 / 已经在床头） |
| T21 | which_table | 送到有人在用的那张桌子 |
| T21 | the_kids_side | 放在孩子那一侧 |
| T22 | eat_now | 马上要吃的放桌上，不收起来 |
| T22 | by_kind | 苹果、零食放果篮或矮柜都算 |
| T22 | two_spots | 同 by_kind，东西分在两处 |
| T23 | by_kind | 勺子放哪个厨房台面或岛台都算 |
| T24 | where_is_he | 按作业本判断孩子在哪张书桌 |

## 不是替换的变体

- 25 个对照（每个任务一个，理想物在、能直接用）：T01 overhang_ready、T02 clear、T03 large_only、T04 cup_available、T05 e1_pencil_asked、T06 free、T07 microwave_works、T08 sponge_on_island、T09 lid_off、T10 can_on_island、T11 fruits_on_table、T12 toys_out、T13 dishes_on_tv_stand、T14 e1_book_ready、T15 lid_by_pot、T16 box_on_counter、T17 lid_off、T18 bowls_in_cabinet、T19 bin_on_bookcase、T20 bottle_on_cabinet、T21 tissue_on_tv_stand、T22 juice_on_table、T23 spoon_on_floor、T24 apple_on_table、T25 drink_on_island。
- 表里 102 个 + 对照 25 个 = 全部 127 个变体。
- 11-17 删掉了 16 个"只换从哪拿"的变体，清单见 `CHANGES_1117_zh.md`。
- T27 整个删掉。T26 和 T28 并进 T12，T29 并进 T10，T30 并进 T18。
