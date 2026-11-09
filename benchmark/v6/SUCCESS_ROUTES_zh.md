# ZenoBench v6：每个 variant 的成功条件和参考调用顺序

由 `python benchmark/v6/success_routes.py` 从 `tasks.json` 生成。

- **成功条件**：一局结束时由 GT 状态判定，全部满足才算成功；中间怎么做不限。
- **参考调用顺序**：oracle 路线，即按技能 contract 调用、能走通的一种做法，不是唯一解。标"（补救）"的是发现情况后多做的一步。机器人只会右手。
- 有多种摆法的 variant 每种摆法列一条路线，seed 决定用哪种摆法。
- 物体名保留代码里的 id。

---

## T01_book_to_dining_table

> 有人把平装书落在厨房岛台上了，把它拿到餐桌上，方便吃早饭时看。

### overhang_ready（对照）

**情况**：书已经探出岛台边缘约 6 cm → 直接抓起送到餐桌

**成功条件**：

- `paperback_book` 在 `dining_table_2/top` 上
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `look(target=paperback_book)`（补救） → 4. `pick(object=paperback_book)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.5])`

### table_seats（Action + Task）

**情况**：指令要求把书放在某位客人吃饭的位置旁边、和餐具留出空隙，但没说是哪个空位。餐桌东侧摆了三人份早餐（每个座位一个盘子或碗加一个杯子，另有两盒麦片），桌边有好几个空位：两套餐具之间的窄缝（放得下但会挨着餐具）、麦片外侧桌子尽头的大空地（离座位远），还有一个座位旁边够宽的空位 → 看清桌面，自己判断哪个空位既在客人座位旁边、又放得下、和餐具留得出空隙，放在那里

**指令**：餐桌上已经给客人摆好了早餐。请把岛台上的书拿过去，放在某位客人吃饭的位置旁边，方便边吃边看；书和餐具之间要留出空隙，不要挨着。除了这本书，别的东西都别挪动。

**成功条件**：

- `paperback_book` 在 `dining_table_2/top` 上
- `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
- `paperback_book` 离其中至少一个不超过 15 cm：`bowl_side_table`、`plate_counter_a`、`plate_counter_b`
- `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
- `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
- 手里空着

**参考调用顺序**：

- 摆法 `seats_a`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `look(target=paperback_book)`（补救） → 4. `pick(object=paperback_book)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.059])`
- 摆法 `seats_b`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `look(target=paperback_book)`（补救） → 4. `pick(object=paperback_book)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.138])`
- 摆法 `seats_c`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `look(target=paperback_book)`（补救） → 4. `pick(object=paperback_book)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.35])`
- 摆法 `seats_a_flat`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `expose(object=paperback_book)` → 4. `look(target=paperback_book)` → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.059])`
- 摆法 `seats_b_flat`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `expose(object=paperback_book)` → 4. `look(target=paperback_book)` → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.138])`
- 摆法 `seats_c_flat`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `expose(object=paperback_book)` → 4. `look(target=paperback_book)` → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.35])`

### which_table（Action + Task）

**情况**：家里有两张餐桌（近的在隔壁餐厅约 6 m，远的在西边另一间餐厅约 16 m），早餐只摆在其中一张上（三人份，和 table_seats 一样只有一个座位旁的合适空位），另一张上是孩子的积木和储物箱，桌边也有空位；指令只说放到客人吃饭的那张桌子上 → 先到近桌看，没摆早餐就改去另一间餐厅，在摆了早餐的桌子上选座位旁的空位放下；放到另一张桌子上算失败

**指令**：客人正在吃早饭。把岛台上的书拿到他们吃饭的那张桌子上，放在某位客人的位置旁边，方便边吃边看；书和餐具之间要留出空隙，不要挨着。除了这本书，别的东西都别挪动。

**成功条件**：

- 摆法 `far_a`、`far_b`、`far_a_flat`、`far_b_flat`：
  - `paperback_book` 在 `dining_table_1/top` 上
  - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`spoon_target_table`
  - `paperback_book` 离其中至少一个不超过 15 cm：`bowl_side_table`、`plate_counter_a`、`plate_counter_b`
  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`spoon_target_table`、`wide_storage_bin`、`clutter_cereal_b`、`wooden_block_a`、`wooden_block_b` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a` 立着
  - 手里空着
- 摆法 `near_a`、`near_b`、`near_a_flat`、`near_b_flat`：
  - `paperback_book` 在 `dining_table_2/top` 上
  - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - `paperback_book` 离其中至少一个不超过 15 cm：`bowl_side_table`、`plate_counter_a`、`plate_counter_b`
  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`、`wide_storage_bin`、`wooden_block_a`、`wooden_block_b` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
  - 手里空着

**参考调用顺序**：

- 摆法 `near_a`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `look(target=paperback_book)`（补救） → 4. `pick(object=paperback_book)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.059])`
- 摆法 `near_b`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `look(target=paperback_book)`（补救） → 4. `pick(object=paperback_book)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.138])`
- 摆法 `far_a`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `look(target=paperback_book)`（补救） → 4. `pick(object=paperback_book)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `navigate(destination=dining_table_1/top)` → 8. `look(target=dining_table_1/top)` → 9. `place(object=paperback_book, receptacle=dining_table_1/top, hint_xy=[-7.607, 8.179])`
- 摆法 `far_b`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `look(target=paperback_book)`（补救） → 4. `pick(object=paperback_book)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `navigate(destination=dining_table_1/top)` → 8. `look(target=dining_table_1/top)` → 9. `place(object=paperback_book, receptacle=dining_table_1/top, hint_xy=[-7.607, 7.508])`
- 摆法 `near_a_flat`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `expose(object=paperback_book)` → 4. `look(target=paperback_book)` → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.059])`
- 摆法 `near_b_flat`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `expose(object=paperback_book)` → 4. `look(target=paperback_book)` → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.138])`
- 摆法 `far_a_flat`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `expose(object=paperback_book)` → 4. `look(target=paperback_book)` → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `navigate(destination=dining_table_1/top)` → 9. `look(target=dining_table_1/top)` → 10. `place(object=paperback_book, receptacle=dining_table_1/top, hint_xy=[-7.607, 8.179])`
- 摆法 `far_b_flat`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `expose(object=paperback_book)` → 4. `look(target=paperback_book)` → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `navigate(destination=dining_table_1/top)` → 9. `look(target=dining_table_1/top)` → 10. `place(object=paperback_book, receptacle=dining_table_1/top, hint_xy=[-7.607, 7.508])`

### no_room_fallback（Action + Task）

**情况**：和 table_seats 一样的三人份早餐；指令加了约束：餐具和麦片都别动，桌上没有合适位置就放到餐厅南墙边的矮格子柜顶上 → 先看桌子：有座位旁的合适空位就放那里（这时放格子柜算失败）；唯一的宽空位被一盒麦片占着时，按指令放到格子柜上（挪麦片腾位置算失败）

**指令**：餐桌上已经给客人摆好了早餐。请把岛台上的书拿过去，放在某位客人吃饭的位置旁边，方便边吃边看；书和餐具之间要留出空隙，不要挨着。除了这本书，别的东西都别挪动；要是桌上没有这样的位置，就把书放到餐厅南墙边那个矮格子柜的顶上。

**成功条件**：

- 摆法 `full_a`、`full_a_flat`：
  - `paperback_book` 在 `cell_shelf_4/top` 上
  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
  - 手里空着
- 摆法 `seats_b`、`seats_c`、`seats_b_flat`、`seats_c_flat`：
  - `paperback_book` 在 `dining_table_2/top` 上
  - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - `paperback_book` 离其中至少一个不超过 15 cm：`bowl_side_table`、`plate_counter_a`、`plate_counter_b`
  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
  - 手里空着

**参考调用顺序**：

- 摆法 `seats_b`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `look(target=paperback_book)`（补救） → 4. `pick(object=paperback_book)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.138])`
- 摆法 `seats_c`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `look(target=paperback_book)`（补救） → 4. `pick(object=paperback_book)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.35])`
- 摆法 `full_a`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `look(target=paperback_book)`（补救） → 4. `pick(object=paperback_book)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `navigate(destination=cell_shelf_4/top)` → 8. `place(object=paperback_book, receptacle=cell_shelf_4/top, hint_xy=[4.3, 4.45])`
- 摆法 `seats_b_flat`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `expose(object=paperback_book)` → 4. `look(target=paperback_book)` → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.138])`
- 摆法 `seats_c_flat`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `expose(object=paperback_book)` → 4. `look(target=paperback_book)` → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.35])`
- 摆法 `full_a_flat`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `expose(object=paperback_book)` → 4. `look(target=paperback_book)` → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `navigate(destination=cell_shelf_4/top)` → 9. `place(object=paperback_book, receptacle=cell_shelf_4/top, hint_xy=[4.3, 4.45])`

### reader_seat（Action + Task）

**情况**：三个座位旁边都有够宽的空位；其中一个座位的饮料是马克杯，另外两个是没把手的杯子；指令说书是"早上用带把手的马克杯喝咖啡的那位客人"的（另外两位用没把手的杯子） → 从桌上认出用马克杯的座位，把书放在那个座位旁边（离它的盘子或马克杯不超过 15 cm，离别的座位的盘子超过 15 cm）

**指令**：餐桌上已经给客人摆好了早餐。岛台上那本书是早上用带把手的马克杯喝咖啡的那位客人的（另外两位用的是没把手的杯子），把它放在那位客人的位置旁边，方便边吃边看；书和餐具之间要留出空隙。除了这本书，别的东西都别挪动。

**成功条件**：

- 摆法 `mug_2`、`mug_2_flat`：
  - `paperback_book` 在 `dining_table_2/top` 上
  - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - `paperback_book` 离其中至少一个不超过 15 cm：`bowl_side_table`、`mug_dining_cabinet`
  - `paperback_book` 离这些都超过 15 cm：`plate_counter_a`、`plate_counter_b`
  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
  - 手里空着
- 摆法 `mug_1`、`mug_1_flat`：
  - `paperback_book` 在 `dining_table_2/top` 上
  - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - `paperback_book` 离其中至少一个不超过 15 cm：`plate_counter_a`、`mug_dining_cabinet`
  - `paperback_book` 离这些都超过 15 cm：`bowl_side_table`、`plate_counter_b`
  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
  - 手里空着
- 摆法 `mug_3`、`mug_3_flat`：
  - `paperback_book` 在 `dining_table_2/top` 上
  - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - `paperback_book` 离其中至少一个不超过 15 cm：`plate_counter_a`、`mug_dining_cabinet`
  - `paperback_book` 离这些都超过 15 cm：`plate_counter_b`、`bowl_side_table`
  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
  - 手里空着

**参考调用顺序**：

- 摆法 `mug_1`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `look(target=paperback_book)`（补救） → 4. `pick(object=paperback_book)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 5.69])`
- 摆法 `mug_2`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `look(target=paperback_book)`（补救） → 4. `pick(object=paperback_book)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.428])`
- 摆法 `mug_3`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `look(target=paperback_book)`（补救） → 4. `pick(object=paperback_book)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.094])`
- 摆法 `mug_1_flat`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `expose(object=paperback_book)` → 4. `look(target=paperback_book)` → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 5.69])`
- 摆法 `mug_2_flat`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `expose(object=paperback_book)` → 4. `look(target=paperback_book)` → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.428])`
- 摆法 `mug_3_flat`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `expose(object=paperback_book)` → 4. `look(target=paperback_book)` → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.094])`

### which_book（Task）

**情况**：岛台上有一本书（不是要找的）；指令说客人昨晚在哪个房间看书（客厅看电视时，或卧室睡前），书就留在那里；另一个房间也有一本别的书 → 不拿眼前岛台上的书，去指令说的房间拿那本，送到餐桌；岛台上和另一个房间的书都不动

**指令**：客人昨晚在客厅看电视时看了会儿书，看完就放在那儿了。把那本书拿到餐桌上，客人想边吃早饭边接着看。除了那本书，别的东西都别挪动。

**成功条件**：

- `paperback_book` 在 `dining_table_2/top` 上
- `book_island`、`book_other` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

- 摆法 `living`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.5])`
- 摆法 `bedroom`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=bookcase_2/top)` → 3. `look(target=bookcase_2/top)` → 4. `navigate(destination=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.5])`

---

## T02_stack_blocks

> 收拾孩子落在岛台上的积木：把一块木积木叠到另一块上面。

### clear（对照）

**情况**：两块积木相距 30 cm → 拿 B 叠到 A 上

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `wooden_block_b` 叠在 `wooden_block_a` 上
  - 第 2 组：
    - `wooden_block_a` 叠在 `wooden_block_b` 上

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_b)` → 3. `pick(object=wooden_block_b)` → 4. `rotate(object=wooden_block_b, degrees=30)` → 5. `navigate(destination=wooden_block_a)` → 6. `stack(object=wooden_block_b, base=wooden_block_a)`

### crowded_use_another（Task）

**情况**：积木 B 被满满一碗燕麦和擀面杖夹住（缝只有 3 mm）；指令说夹紧的积木别去拨（燕麦会洒），家里别处还有一块木积木 → 先看 B：夹紧了就不拨它，去找另一块积木和 A 叠在一起，B、碗、擀面杖都不动；B 没被夹住就直接叠岛台上的两块，另一块不动

**指令**：把孩子的两块木积木叠起来。岛台上的燕麦碗是满的：要是有积木被碗和擀面杖夹得很紧，就别去拨它，免得把燕麦碰洒；家里别处还有一块木积木，用那块。

**成功条件**：

- 摆法 `tight_tv`、`tight_dining`：
  - `wooden_block_b`、`oatmeal`、`rolling_pin` 没被挪动（离开局位置不超过 2 cm）
  - `oatmeal` 立着
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_a` 叠在 `floor_block` 上
    - 第 2 组：
      - `floor_block` 叠在 `wooden_block_a` 上
- 摆法 `loose`：
  - `floor_block`、`oatmeal`、`rolling_pin` 没被挪动（离开局位置不超过 2 cm）
  - `oatmeal` 立着
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_a` 叠在 `wooden_block_b` 上
    - 第 2 组：
      - `wooden_block_b` 叠在 `wooden_block_a` 上

**参考调用顺序**：

- 摆法 `tight_tv`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_b)` → 3. `look(target=wooden_block_b)` → 4. `search(object=floor_block, region=living_room_0_0)` → 5. `navigate(destination=floor_block)` → 6. `pick(object=floor_block)` → 7. `navigate(destination=wooden_block_a)` → 8. `stack(object=floor_block, base=wooden_block_a)`
- 摆法 `tight_dining`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_b)` → 3. `look(target=wooden_block_b)` → 4. `search(object=floor_block, region=dining_room_0_1)` → 5. `navigate(destination=floor_block)` → 6. `pick(object=floor_block)` → 7. `navigate(destination=wooden_block_a)` → 8. `stack(object=floor_block, base=wooden_block_a)`
- 摆法 `loose`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_b)` → 3. `pick(object=wooden_block_b)` → 4. `rotate(object=wooden_block_b, degrees=30)` → 5. `navigate(destination=wooden_block_a)` → 6. `stack(object=wooden_block_b, base=wooden_block_a)`

### third_toy_elsewhere（Task）

**情况**：指令只说用孩子的玩具在岛台上搭一座三层的小塔；家里只有两块积木（都在岛台上），旁边的海绵大小像积木但不是玩具；孩子别的玩具在别的房间、开局看不到 → 不能只叠两块就停，也不能拿海绵凑数：先叠好两块，去别的房间找一个玩具当第三层（鸭子没有平顶，只能放最上面）

**指令**：用孩子的玩具在岛台上搭一座三层的小塔。

**成功条件**：

- 摆法 `duck`：
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_b` 叠在 `wooden_block_a` 上
      - `rubber_duck` 叠在 `wooden_block_b` 上
      - `wooden_block_a` 在 `kitchen_island/top` 上
    - 第 2 组：
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `rubber_duck` 叠在 `wooden_block_a` 上
      - `wooden_block_b` 在 `kitchen_island/top` 上
- 摆法 `toy_block`：
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_b` 叠在 `wooden_block_a` 上
      - `toy_block` 叠在 `wooden_block_b` 上
      - `wooden_block_a` 在 `kitchen_island/top` 上
    - 第 2 组：
      - `toy_block` 叠在 `wooden_block_a` 上
      - `wooden_block_b` 叠在 `toy_block` 上
      - `wooden_block_a` 在 `kitchen_island/top` 上
    - 第 3 组：
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `toy_block` 叠在 `wooden_block_a` 上
      - `wooden_block_b` 在 `kitchen_island/top` 上
    - 第 4 组：
      - `toy_block` 叠在 `wooden_block_b` 上
      - `wooden_block_a` 叠在 `toy_block` 上
      - `wooden_block_b` 在 `kitchen_island/top` 上
    - 第 5 组：
      - `wooden_block_a` 叠在 `toy_block` 上
      - `wooden_block_b` 叠在 `wooden_block_a` 上
      - `toy_block` 在 `kitchen_island/top` 上
    - 第 6 组：
      - `wooden_block_b` 叠在 `toy_block` 上
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `toy_block` 在 `kitchen_island/top` 上

**参考调用顺序**：

- 摆法 `duck`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_b)` → 3. `pick(object=wooden_block_b)` → 4. `rotate(object=wooden_block_b, degrees=30)` → 5. `navigate(destination=wooden_block_a)` → 6. `stack(object=wooden_block_b, base=wooden_block_a)` → 7. `search(object=rubber_duck, region=dining_room_0_1)`（补救） → 8. `navigate(destination=rubber_duck)`（补救） → 9. `pick(object=rubber_duck)`（补救） → 10. `navigate(destination=wooden_block_a)`（补救） → 11. `stack(object=rubber_duck, base=wooden_block_b)`（补救）
- 摆法 `toy_block`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_b)` → 3. `pick(object=wooden_block_b)` → 4. `rotate(object=wooden_block_b, degrees=30)` → 5. `navigate(destination=wooden_block_a)` → 6. `stack(object=wooden_block_b, base=wooden_block_a)` → 7. `search(object=toy_block, region=kitchen_0_1)`（补救） → 8. `navigate(destination=toy_block)`（补救） → 9. `pick(object=toy_block)`（补救） → 10. `navigate(destination=wooden_block_a)`（补救） → 11. `stack(object=toy_block, base=wooden_block_b)`（补救）

### tower_for_kid（Task）

**情况**：孩子想在餐桌上看积木塔；三块积木分散在岛台、客厅电视柜和另一间房的桌上（开局看不到）；餐桌上有储物箱、两盒麦片和勺子 → 找全三块，一只手往返三趟、安排先后；第一块放在餐桌上离边缘至少 5 cm、不贴着储物箱和麦片的空处当底座，再叠另外两块；桌上原有东西不动

**指令**：孩子想在餐桌上看积木塔。把家里三块积木都找到，在餐桌上叠成一座塔。

**成功条件**：

- `wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `wooden_block_b` 叠在 `wooden_block_a` 上
    - `floor_block` 叠在 `wooden_block_b` 上
    - `wooden_block_a` 在 `dining_table_2/top` 上
    - `wooden_block_a` 离台面边缘至少 5 cm
    - `wooden_block_a` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - 第 2 组：
    - `floor_block` 叠在 `wooden_block_a` 上
    - `wooden_block_b` 叠在 `floor_block` 上
    - `wooden_block_a` 在 `dining_table_2/top` 上
    - `wooden_block_a` 离台面边缘至少 5 cm
    - `wooden_block_a` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - 第 3 组：
    - `wooden_block_a` 叠在 `wooden_block_b` 上
    - `floor_block` 叠在 `wooden_block_a` 上
    - `wooden_block_b` 在 `dining_table_2/top` 上
    - `wooden_block_b` 离台面边缘至少 5 cm
    - `wooden_block_b` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - 第 4 组：
    - `floor_block` 叠在 `wooden_block_b` 上
    - `wooden_block_a` 叠在 `floor_block` 上
    - `wooden_block_b` 在 `dining_table_2/top` 上
    - `wooden_block_b` 离台面边缘至少 5 cm
    - `wooden_block_b` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - 第 5 组：
    - `wooden_block_a` 叠在 `floor_block` 上
    - `wooden_block_b` 叠在 `wooden_block_a` 上
    - `floor_block` 在 `dining_table_2/top` 上
    - `floor_block` 离台面边缘至少 5 cm
    - `floor_block` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - 第 6 组：
    - `wooden_block_b` 叠在 `floor_block` 上
    - `wooden_block_a` 叠在 `wooden_block_b` 上
    - `floor_block` 在 `dining_table_2/top` 上
    - `floor_block` 离台面边缘至少 5 cm
    - `floor_block` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`

**参考调用顺序**：

- 摆法 `counter`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=dining_table_2/top)` → 5. `look(target=dining_table_2/top)` → 6. `place(object=wooden_block_a, receptacle=dining_table_2/top, hint_xy=[3.7, 6.6])` → 7. `search(object=wooden_block_b, region=living_room_0_0)` → 8. `navigate(destination=wooden_block_b)` → 9. `pick(object=wooden_block_b)` → 10. `navigate(destination=wooden_block_a)` → 11. `stack(object=wooden_block_b, base=wooden_block_a)` → 12. `search(object=floor_block, region=kitchen_0_1)` → 13. `navigate(destination=floor_block)` → 14. `pick(object=floor_block)` → 15. `navigate(destination=wooden_block_a)` → 16. `stack(object=floor_block, base=wooden_block_b)`
- 摆法 `study`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=dining_table_2/top)` → 5. `look(target=dining_table_2/top)` → 6. `place(object=wooden_block_a, receptacle=dining_table_2/top, hint_xy=[3.7, 6.6])` → 7. `search(object=floor_block, region=living_room_0_0)` → 8. `navigate(destination=floor_block)` → 9. `pick(object=floor_block)` → 10. `navigate(destination=wooden_block_a)` → 11. `stack(object=floor_block, base=wooden_block_a)` → 12. `search(object=wooden_block_b, region=living_room_0_1)` → 13. `navigate(destination=wooden_block_b)` → 14. `pick(object=wooden_block_b)` → 15. `navigate(destination=wooden_block_a)` → 16. `stack(object=wooden_block_b, base=floor_block)`

### tower_for_kid_duck（Task）

**情况**：和 tower_for_kid 一样在餐桌上搭三层塔，但家里只有两块积木（岛台一块，电视柜或书房书桌一块）；指令说积木不够就用孩子别的玩具补 → 找到两块后发现没有第三块，去拿小黄鸭补上；鸭子没有平顶，只能放最上面，所以最后拿；底座和桌上东西的要求同 tower_for_kid

**指令**：孩子想在餐桌上看一座三层的塔。把家里的积木找来，在餐桌上叠成塔；积木不够的话，用孩子别的玩具补上缺的那一层。

**成功条件**：

- `wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `wooden_block_b` 叠在 `wooden_block_a` 上
    - `rubber_duck` 叠在 `wooden_block_b` 上
    - `wooden_block_a` 在 `dining_table_2/top` 上
    - `wooden_block_a` 离台面边缘至少 5 cm
    - `wooden_block_a` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - 第 2 组：
    - `wooden_block_a` 叠在 `wooden_block_b` 上
    - `rubber_duck` 叠在 `wooden_block_a` 上
    - `wooden_block_b` 在 `dining_table_2/top` 上
    - `wooden_block_b` 离台面边缘至少 5 cm
    - `wooden_block_b` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`

**参考调用顺序**：

- 摆法 `counter`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=dining_table_2/top)` → 5. `look(target=dining_table_2/top)` → 6. `place(object=wooden_block_a, receptacle=dining_table_2/top, hint_xy=[3.7, 6.6])` → 7. `search(object=wooden_block_b, region=living_room_0_0)` → 8. `navigate(destination=wooden_block_b)` → 9. `pick(object=wooden_block_b)` → 10. `navigate(destination=wooden_block_a)` → 11. `stack(object=wooden_block_b, base=wooden_block_a)` → 12. `search(object=rubber_duck, region=kitchen_0_1)` → 13. `navigate(destination=rubber_duck)` → 14. `pick(object=rubber_duck)` → 15. `navigate(destination=wooden_block_a)` → 16. `stack(object=rubber_duck, base=wooden_block_b)`
- 摆法 `study`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=dining_table_2/top)` → 5. `look(target=dining_table_2/top)` → 6. `place(object=wooden_block_a, receptacle=dining_table_2/top, hint_xy=[3.7, 6.6])` → 7. `search(object=wooden_block_b, region=living_room_0_1)` → 8. `navigate(destination=wooden_block_b)` → 9. `pick(object=wooden_block_b)` → 10. `navigate(destination=wooden_block_a)` → 11. `stack(object=wooden_block_b, base=wooden_block_a)` → 12. `search(object=rubber_duck, region=living_room_0_0)` → 13. `navigate(destination=rubber_duck)` → 14. `pick(object=rubber_duck)` → 15. `navigate(destination=wooden_block_a)` → 16. `stack(object=rubber_duck, base=wooden_block_b)`

### block_put_away（Action + Task）

**情况**：三块积木在岛台上叠塔；岛台上两块，一块在边上不能当底座；第三块被收进客厅靠墙两个关着的矮柜之一（指令点明：离岛台近的那个，或沿墙离岛台远的那个） → 原地把边上那块叠到另一块上（Action），再逐个打开矮柜找第三块，找到后关好柜门，叠到最上面（Task）；两个柜子最后都关着

**指令**：把三块积木在岛台上叠成一座塔。两块在岛台上；第三块我收进了客厅靠墙的两个带门矮柜之一：离岛台近的那个，或者沿墙再往外、离岛台远的那个。找完把柜门关好。

**成功条件**：

- 手里空着
- `kitchen_cabinet_4` 关着
- `kitchen_cabinet_6` 关着
- 满足下面任意一组：
  - 第 1 组：
    - `wooden_block_a` 叠在 `wooden_block_b` 上
    - `floor_block` 叠在 `wooden_block_a` 上
    - `wooden_block_b` 离台面边缘至少 5 cm
    - `wooden_block_b` 在 `kitchen_island/top` 上
  - 第 2 组：
    - `floor_block` 叠在 `wooden_block_b` 上
    - `wooden_block_a` 叠在 `floor_block` 上
    - `wooden_block_b` 离台面边缘至少 5 cm
    - `wooden_block_b` 在 `kitchen_island/top` 上
  - 第 3 组：
    - `wooden_block_a` 叠在 `floor_block` 上
    - `wooden_block_b` 叠在 `wooden_block_a` 上
    - `floor_block` 离台面边缘至少 5 cm
    - `floor_block` 在 `kitchen_island/top` 上
  - 第 4 组：
    - `wooden_block_b` 叠在 `floor_block` 上
    - `wooden_block_a` 叠在 `wooden_block_b` 上
    - `floor_block` 离台面边缘至少 5 cm
    - `floor_block` 在 `kitchen_island/top` 上

**参考调用顺序**：

- 摆法 `in_4`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)`（换做法） → 4. `navigate(destination=wooden_block_b)` → 5. `stack(object=wooden_block_a, base=wooden_block_b)`（换做法） → 6. `navigate(destination=kitchen_cabinet_6)` → 7. `open(articulated=kitchen_cabinet_6)` → 8. `bend()` → 9. `explore_furniture(furniture=kitchen_cabinet_6)` → 10. `straighten()` → 11. `close(articulated=kitchen_cabinet_6)` → 12. `navigate(destination=kitchen_cabinet_4)` → 13. `open(articulated=kitchen_cabinet_4)` → 14. `bend()` → 15. `explore_furniture(furniture=kitchen_cabinet_4)` → 16. `straighten()` → 17. `navigate(destination=floor_block)` → 18. `pick(object=floor_block)` → 19. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 20. `close(articulated=kitchen_cabinet_4)` → 21. `navigate(destination=wooden_block_a)` → 22. `stack(object=floor_block, base=wooden_block_a)`
- 摆法 `in_6`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)`（换做法） → 4. `navigate(destination=wooden_block_b)` → 5. `stack(object=wooden_block_a, base=wooden_block_b)`（换做法） → 6. `navigate(destination=kitchen_cabinet_4)` → 7. `open(articulated=kitchen_cabinet_4)` → 8. `bend()` → 9. `explore_furniture(furniture=kitchen_cabinet_4)` → 10. `straighten()` → 11. `close(articulated=kitchen_cabinet_4)` → 12. `navigate(destination=kitchen_cabinet_6)` → 13. `open(articulated=kitchen_cabinet_6)` → 14. `bend()` → 15. `explore_furniture(furniture=kitchen_cabinet_6)` → 16. `straighten()` → 17. `navigate(destination=floor_block)` → 18. `pick(object=floor_block)` → 19. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 20. `close(articulated=kitchen_cabinet_6)` → 21. `navigate(destination=wooden_block_a)` → 22. `stack(object=floor_block, base=wooden_block_a)`

---

## T03_utensils_one_container

> 烘焙结束了，把擀面杖和勺子一起收进同一个容器里。

### large_only（对照）

**情况**：只有电视柜上的宽储物箱能用 → 两样都放进去

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `rolling_pin` 在 `wide_storage_bin` 里
    - `breakfast_spoon` 在 `wide_storage_bin` 里
  - 第 2 组：
    - `rolling_pin` 在 `mug` 里
    - `breakfast_spoon` 在 `mug` 里

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=breakfast_spoon)` → 4. `pick(object=breakfast_spoon)` → 5. `navigate(destination=wide_storage_bin)` → 6. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 7. `navigate(destination=rolling_pin)` → 8. `pick(object=rolling_pin)` → 9. `navigate(destination=wide_storage_bin)` → 10. `place(object=rolling_pin, receptacle=wide_storage_bin)`

### small_bin_or_bedroom_bin（Task）

**情况**：岛台上餐具旁边有个小储物箱（22 × 17 cm），里面已经放了两块积木：勺子还放得下，22 cm 的擀面杖平放、斜放都放不进；宽储物箱在卧室矮书架上 → 看剩下的空间判断放不下，两样要放同一个容器，所以都拿去卧室的宽箱；小箱里的积木不动

**成功条件**：

- `rolling_pin` 在 `wide_storage_bin` 里
- `breakfast_spoon` 在 `wide_storage_bin` 里
- 手里空着
- `small_bin_block_1` 在 `small_storage_bin` 里
- `small_bin_block_2` 在 `small_storage_bin` 里

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `measure(object=small_storage_bin)` → 3. `measure(object=rolling_pin)` → 4. `search(object=wide_storage_bin, region=bedroom_0_1)` → 5. `navigate(destination=bookcase_2/top)` → 6. `look(target=bookcase_2/top)` → 7. `navigate(destination=breakfast_spoon)` → 8. `pick(object=breakfast_spoon)` → 9. `navigate(destination=wide_storage_bin)` → 10. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 11. `navigate(destination=rolling_pin)` → 12. `pick(object=rolling_pin)` → 13. `navigate(destination=wide_storage_bin)` → 14. `place(object=rolling_pin, receptacle=wide_storage_bin)`

### three_containers_bedroom（Task）

**情况**：卧室矮书架上并排放着小储物箱（里面有两块积木）和宽储物箱 → 看剩余空间，擀面杖只能放宽箱，把两样都拿过去；小箱里的积木不动

**指令**：烘焙结束，请把擀面杖和勺子一起收进同一个合适容器，确保两件都完整放入。

**成功条件**：

- `rolling_pin` 在 `wide_storage_bin` 里
- `breakfast_spoon` 在 `wide_storage_bin` 里
- 手里空着
- `small_bin_block_1` 在 `small_storage_bin` 里
- `small_bin_block_2` 在 `small_storage_bin` 里

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `search(object=wide_storage_bin, region=bedroom_0_1)` → 3. `navigate(destination=bookcase_2/top)` → 4. `look(target=bookcase_2/top)` → 5. `measure(object=small_storage_bin)` → 6. `measure(object=rolling_pin)` → 7. `navigate(destination=breakfast_spoon)` → 8. `pick(object=breakfast_spoon)` → 9. `navigate(destination=wide_storage_bin)` → 10. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 11. `navigate(destination=rolling_pin)` → 12. `pick(object=rolling_pin)` → 13. `navigate(destination=wide_storage_bin)` → 14. `place(object=rolling_pin, receptacle=wide_storage_bin)`

### which_bin_by_contents（Task）

**情况**：客厅电视柜和卧室矮书架上各有一个一样的宽箱：玩具箱里是孩子的两块积木，厨房用具箱里是两把勺子；指令说收进放厨房用具的那个箱子 → 往近的箱子里看，是玩具箱就去另一个房间找厨房用具箱，把两样都放进去；箱子里原有的东西不动

**指令**：烘焙结束了，把擀面杖和勺子一起收进放厨房用具的那个箱子里。

**成功条件**：

- `rolling_pin` 在 `wide_storage_bin` 里
- `breakfast_spoon` 在 `wide_storage_bin` 里
- `toy_bin_block_1` 在 `toy_storage_bin` 里
- `toy_bin_block_2` 在 `toy_storage_bin` 里
- `spoon_counter` 在 `wide_storage_bin` 里
- `spoon_side_table` 在 `wide_storage_bin` 里
- 手里空着

**参考调用顺序**：

- 摆法 `toys_near`：1. `look(target=kitchen_island/top)` → 2. `look(target=tv_stand_2/top)` → 3. `search(object=wide_storage_bin, region=bedroom_0_1)` → 4. `navigate(destination=bookcase_2/top)` → 5. `look(target=bookcase_2/top)` → 6. `navigate(destination=breakfast_spoon)` → 7. `pick(object=breakfast_spoon)` → 8. `navigate(destination=wide_storage_bin)` → 9. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 10. `navigate(destination=rolling_pin)` → 11. `pick(object=rolling_pin)` → 12. `navigate(destination=wide_storage_bin)` → 13. `place(object=rolling_pin, receptacle=wide_storage_bin)`
- 摆法 `tools_near`：1. `look(target=kitchen_island/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=breakfast_spoon)` → 4. `pick(object=breakfast_spoon)` → 5. `navigate(destination=wide_storage_bin)` → 6. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 7. `navigate(destination=rolling_pin)` → 8. `pick(object=rolling_pin)` → 9. `navigate(destination=wide_storage_bin)` → 10. `place(object=rolling_pin, receptacle=wide_storage_bin)`

### no_bin_substitute（Task）

**情况**：家里没有储物箱；电视柜上的小箱（22 × 17 cm，里面有两块积木）放不下 22 cm 的擀面杖；餐桌上的果篮够大但装着苹果和橙子；指令说没有储物箱就找能装下两样的东西代替 → 排除小箱，不用果篮，去别的房间找替代品，两样都放进去

**指令**：烘焙结束了，把擀面杖和勺子一起收进储物箱；没有的话，找个能把两样一起装下的东西代替。

**成功条件**：

- 摆法 `tray`：
  - `rolling_pin` 在 `serving_tray` 里
  - `breakfast_spoon` 在 `serving_tray` 里
  - `apple` 在 `fruit_basket` 里
  - `orange` 在 `fruit_basket` 里
  - `small_bin_block_1` 在 `small_storage_bin` 里
  - `small_bin_block_2` 在 `small_storage_bin` 里
  - 手里空着
- 摆法 `basket`：
  - `rolling_pin` 在 `storage_basket` 里
  - `breakfast_spoon` 在 `storage_basket` 里
  - `apple` 在 `fruit_basket` 里
  - `orange` 在 `fruit_basket` 里
  - `small_bin_block_1` 在 `small_storage_bin` 里
  - `small_bin_block_2` 在 `small_storage_bin` 里
  - 手里空着

**参考调用顺序**：

- 摆法 `basket`：1. `look(target=kitchen_island/top)` → 2. `measure(object=rolling_pin)` → 3. `look(target=tv_stand_2/top)` → 4. `measure(object=small_storage_bin)` → 5. `search(object=storage_basket, region=bedroom_0_1)` → 6. `navigate(destination=storage_basket)` → 7. `look(target=storage_basket)` → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=storage_basket)` → 11. `drop(object=breakfast_spoon, container=storage_basket)` → 12. `navigate(destination=rolling_pin)` → 13. `pick(object=rolling_pin)` → 14. `navigate(destination=storage_basket)` → 15. `place(object=rolling_pin, receptacle=storage_basket)`
- 摆法 `tray`：1. `look(target=kitchen_island/top)` → 2. `measure(object=rolling_pin)` → 3. `look(target=tv_stand_2/top)` → 4. `measure(object=small_storage_bin)` → 5. `search(object=serving_tray, region=living_room_0_1)` → 6. `navigate(destination=serving_tray)` → 7. `look(target=serving_tray)` → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=serving_tray)` → 11. `place(object=breakfast_spoon, receptacle=serving_tray)` → 12. `navigate(destination=rolling_pin)` → 13. `pick(object=rolling_pin)` → 14. `navigate(destination=serving_tray)` → 15. `place(object=rolling_pin, receptacle=serving_tray)`

### utensils_apart（Task）

**情况**：擀面杖在岛台上，勺子落在了别的房间（开局看不到），宽箱在卧室矮书架上 → 找到箱子和勺子，一只手分两趟：先送擀面杖，再去拿勺子

**成功条件**：

- `rolling_pin` 在 `wide_storage_bin` 里
- `breakfast_spoon` 在 `wide_storage_bin` 里
- 手里空着

**参考调用顺序**：

- 摆法 `dining`：1. `look(target=kitchen_island/top)` → 2. `search(object=wide_storage_bin, region=bedroom_0_1)` → 3. `navigate(destination=bookcase_2/top)` → 4. `look(target=bookcase_2/top)` → 5. `navigate(destination=rolling_pin)` → 6. `pick(object=rolling_pin)` → 7. `navigate(destination=wide_storage_bin)` → 8. `place(object=rolling_pin, receptacle=wide_storage_bin)` → 9. `search(object=breakfast_spoon, region=dining_room_0_1)` → 10. `navigate(destination=breakfast_spoon)` → 11. `pick(object=breakfast_spoon)` → 12. `navigate(destination=wide_storage_bin)` → 13. `drop(object=breakfast_spoon, container=wide_storage_bin)`
- 摆法 `counter`：1. `look(target=kitchen_island/top)` → 2. `search(object=wide_storage_bin, region=bedroom_0_1)` → 3. `navigate(destination=bookcase_2/top)` → 4. `look(target=bookcase_2/top)` → 5. `navigate(destination=rolling_pin)` → 6. `pick(object=rolling_pin)` → 7. `navigate(destination=wide_storage_bin)` → 8. `place(object=rolling_pin, receptacle=wide_storage_bin)` → 9. `search(object=breakfast_spoon, region=kitchen_0_1)` → 10. `navigate(destination=breakfast_spoon)` → 11. `pick(object=breakfast_spoon)` → 12. `navigate(destination=wide_storage_bin)` → 13. `drop(object=breakfast_spoon, container=wide_storage_bin)`

---

## T04_cup_or_mug_to_cabinet

> 有客人要来，在靠墙矮柜上的饮品角摆一个杯子；没有杯子的话马克杯也行。

### cup_available（对照）

**情况**：岛台上有杯子 → 拿到饮品角

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
    - `cup_counter_b` 立着
  - 第 2 组：
    - `mug` 在 `kitchen_cabinet_6/top` 上
    - `mug` 立着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=cup_counter_b)` → 3. `pick(object=cup_counter_b)` → 4. `navigate(destination=kitchen_cabinet_6/top)` → 5. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)`

### no_cup（Task）

**情况**：家里没有杯子 → 用马克杯代替

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
    - `cup_counter_b` 立着
  - 第 2 组：
    - `mug` 在 `kitchen_cabinet_6/top` 上
    - `mug` 立着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `count(category=cup)` → 3. `search(object=cup)` → 4. `navigate(destination=mug)`（换做法） → 5. `pick(object=mug)`（换做法） → 6. `navigate(destination=kitchen_cabinet_6/top)` → 7. `place(object=mug, receptacle=kitchen_cabinet_6/top)`

### no_cup_mug_away（Task）

**情况**：没杯子，马克杯也不在眼前 → 先找马克杯

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
    - `cup_counter_b` 立着
  - 第 2 组：
    - `mug` 在 `kitchen_cabinet_6/top` 上
    - `mug` 立着

**参考调用顺序**：

- 摆法 `no_cup_mug_away`：1. `look(target=kitchen_island/top)` → 2. `count(category=cup)` → 3. `search(object=cup)` → 4. `search(object=mug, region=living_room_0_0)`（换做法） → 5. `navigate(destination=mug)` → 6. `pick(object=mug)` → 7. `navigate(destination=kitchen_cabinet_6/top)` → 8. `place(object=mug, receptacle=kitchen_cabinet_6/top)`
- 摆法 `alt_dining_table_2`：1. `look(target=kitchen_island/top)` → 2. `count(category=cup)` → 3. `search(object=cup)` → 4. `search(object=mug, region=dining_room_0_1)`（换做法） → 5. `navigate(destination=mug)` → 6. `pick(object=mug)` → 7. `navigate(destination=kitchen_cabinet_6/top)` → 8. `place(object=mug, receptacle=kitchen_cabinet_6/top)`

### h_task_spot_taken（Task）

**情况**：饮品角被燕麦碗和锅盖占满 → 先把碗挪到另一个柜顶腾地方，再放杯子

**成功条件**：

- 手里空着
- `oatmeal`、`pot_lid` 立着
- 满足下面任意一组：
  - 第 1 组：
    - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
    - `cup_counter_b` 立着
  - 第 2 组：
    - `mug` 在 `kitchen_cabinet_6/top` 上
    - `mug` 立着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=kitchen_cabinet_6/top)` → 3. `look(target=kitchen_cabinet_6/top)` → 4. `navigate(destination=oatmeal)` → 5. `pick(object=oatmeal)` → 6. `navigate(destination=kitchen_cabinet_4/top)` → 7. `place(object=oatmeal, receptacle=kitchen_cabinet_4/top)` → 8. `navigate(destination=cup_counter_b)` → 9. `pick(object=cup_counter_b)` → 10. `navigate(destination=kitchen_cabinet_6/top)` → 11. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)`

### two_guests（Task）

**情况**：来两位客人，要在饮品角摆两个杯子，别挨着；家里只有一个杯子（岛台上），马克杯在别的房间（开局看不到）；指令说杯子不够可以用马克杯顶一个 → 先放杯子，发现没有第二个杯子，去别的房间找马克杯补上

**指令**：有两位客人要来。在靠墙矮柜上的饮品角摆两个杯子，两个别挨着；杯子不够的话，可以用马克杯顶一个。

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
    - `cup_counter_b` 立着
    - `mug` 在 `kitchen_cabinet_6/top` 上
    - `mug` 立着
    - `cup_counter_b` 离这些东西都至少 3 cm：`mug`
  - 第 2 组：
    - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
    - `cup_counter_b` 立着
    - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
    - `mug_dining_cabinet` 立着
    - `cup_counter_b` 离这些东西都至少 3 cm：`mug_dining_cabinet`
  - 第 3 组：
    - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
    - `cup_counter_b` 立着
    - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
    - `mug_shelf` 立着
    - `cup_counter_b` 离这些东西都至少 3 cm：`mug_shelf`
  - 第 4 组：
    - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
    - `cup_counter_b` 立着
    - `mug_counter` 在 `kitchen_cabinet_6/top` 上
    - `mug_counter` 立着
    - `cup_counter_b` 离这些东西都至少 3 cm：`mug_counter`

**参考调用顺序**：

- 摆法 `dining`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=cup_counter_b)` → 3. `pick(object=cup_counter_b)` → 4. `navigate(destination=kitchen_cabinet_6/top)` → 5. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top, hint_xy=[3.36, 0.36])` → 6. `search(object=mug, region=dining_room_0_1)` → 7. `navigate(destination=mug)` → 8. `pick(object=mug)` → 9. `navigate(destination=kitchen_cabinet_6/top)` → 10. `place(object=mug, receptacle=kitchen_cabinet_6/top, hint_xy=[3.62, 0.36])`
- 摆法 `study`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=cup_counter_b)` → 3. `pick(object=cup_counter_b)` → 4. `navigate(destination=kitchen_cabinet_6/top)` → 5. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top, hint_xy=[3.36, 0.36])` → 6. `search(object=mug, region=living_room_0_1)` → 7. `navigate(destination=mug)` → 8. `pick(object=mug)` → 9. `navigate(destination=kitchen_cabinet_6/top)` → 10. `place(object=mug, receptacle=kitchen_cabinet_6/top, hint_xy=[3.62, 0.36])`

### x6_gd_cup_in_cabinets（Task）

**情况**：马克杯就在眼前，但更想要杯子；杯子收在两个关着的矮柜之一 → 逐个打开找，找完关门

**指令**：有客人要来。在靠墙矮柜上的饮品角摆一个杯子；杯子收在厨房那两个矮柜里。要是没有杯子，岛台上的马克杯也行。用完把柜门关好。

**成功条件**：

- `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
- `cup_counter_b` 立着
- 手里空着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

- 摆法 `cup_in_4`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=kitchen_cabinet_6)` → 3. `open(articulated=kitchen_cabinet_6)` → 4. `bend()` → 5. `explore_furniture(furniture=kitchen_cabinet_6)` → 6. `straighten()` → 7. `close(articulated=kitchen_cabinet_6)` → 8. `navigate(destination=kitchen_cabinet_4)` → 9. `open(articulated=kitchen_cabinet_4)` → 10. `bend()` → 11. `explore_furniture(furniture=kitchen_cabinet_4)` → 12. `straighten()` → 13. `navigate(destination=cup_counter_b)` → 14. `pick(object=cup_counter_b)` → 15. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 16. `close(articulated=kitchen_cabinet_4)` → 17. `navigate(destination=kitchen_cabinet_6/top)` → 18. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)`
- 摆法 `cup_in_6`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=kitchen_cabinet_4)` → 3. `open(articulated=kitchen_cabinet_4)` → 4. `bend()` → 5. `explore_furniture(furniture=kitchen_cabinet_4)` → 6. `straighten()` → 7. `close(articulated=kitchen_cabinet_4)` → 8. `navigate(destination=kitchen_cabinet_6)` → 9. `open(articulated=kitchen_cabinet_6)` → 10. `bend()` → 11. `explore_furniture(furniture=kitchen_cabinet_6)` → 12. `straighten()` → 13. `navigate(destination=cup_counter_b)` → 14. `pick(object=cup_counter_b)` → 15. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 16. `close(articulated=kitchen_cabinet_6)` → 17. `navigate(destination=kitchen_cabinet_6/top)` → 18. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)`

---

## T05_pen_or_pencil_to_desk

> 孩子写作业要用笔，把一支钢笔拿到书桌上；没有钢笔就拿铅笔。

### e1_pencil_asked（对照）

**情况**：指令直接要铅笔，铅笔在卧室书架上 → 拿到书桌

**指令**：孩子做数学作业需要铅笔，请把铅笔拿到书房的书桌上。

**成功条件**：

- `pencil` 在 `desk_1/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `navigate(destination=pencil)`（换做法） → 4. `pick(object=pencil)`（换做法） → 5. `present(object=pencil)`（补救） → 6. `navigate(destination=desk_1/top)` → 7. `place(object=pencil, receptacle=desk_1/top)`

### no_pen_pencil_away（Task）

**情况**：没钢笔，铅笔在另一个房间的餐桌上 → 去找铅笔

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `pen` 在 `desk_1/top` 上
  - 第 2 组：
    - `pencil` 在 `desk_1/top` 上

**参考调用顺序**：

1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `navigate(destination=pen)` → 4. `navigate(destination=dining_table_2/top)`（补救） → 5. `look(target=dining_table_2/top)`（补救） → 6. `navigate(destination=pencil)` → 7. `pick(object=pencil)` → 8. `navigate(destination=desk_1/top)` → 9. `place(object=pencil, receptacle=desk_1/top)`

### h_task_pencil_in_cabinet（Action + Task）

**情况**：没钢笔（换铅笔），铅笔在关着门的矮柜里 → 开柜门拿铅笔，再关上

**指令**：孩子写作业需要笔。请把钢笔拿到书房书桌上；没有钢笔就拿铅笔。铅笔收在矮墙柜里，拿完请把柜门关好。

**成功条件**：

- 手里空着
- `kitchen_cabinet_6` 关着
- 满足下面任意一组：
  - 第 1 组：
    - `pen` 在 `desk_1/top` 上
  - 第 2 组：
    - `pencil` 在 `desk_1/top` 上

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()`（补救） → 4. `explore_furniture(furniture=kitchen_cabinet_6)`（补救） → 5. `straighten()`（补救） → 6. `navigate(destination=pencil)` → 7. `pick(object=pencil)` → 8. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 9. `close(articulated=kitchen_cabinet_6)` → 10. `navigate(destination=desk_1/top)` → 11. `place(object=pencil, receptacle=desk_1/top)`

### check_desk_first（Task）

**情况**：指令照常（拿钢笔，没有就拿铅笔），但书桌上其实已经有了：钢笔在桌上；或者家里没有钢笔、铅笔已经在桌上 → 先看书桌，确认已经有了就停手；再拿一支来算失败，别处的笔要原地不动

**成功条件**：

- 摆法 `pen_on_desk`：
  - `pen` 在 `desk_1/top` 上
  - `pen` 没被挪动（离开局位置不超过 10 cm）
  - `pencil` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `pencil_on_desk`：
  - `pencil` 在 `desk_1/top` 上
  - `pencil` 没被挪动（离开局位置不超过 10 cm）
  - `pencil_2` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着

**参考调用顺序**：

- 摆法 `pen_on_desk`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `identify(object=pen)`
- 摆法 `pencil_on_desk`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `identify(object=pencil)`

### all_pens（Task）

**情况**：孩子整理文具盒，把家里所有钢笔和铅笔都收到书桌上；指令不说有几支，2 到 4 支分散在卧室书架、餐桌、电视柜、厨房台面 → 一间间找，一次拿一支，每个地方都找过才算完；漏一支算失败

**指令**：孩子要整理文具盒。把家里所有的钢笔和铅笔都收到书房的书桌上。

**成功条件**：

- 摆法 `two`：
  - `pencil` 在 `desk_1/top` 上
  - `pen` 在 `desk_1/top` 上
  - 手里空着
- 摆法 `three`：
  - `pencil` 在 `desk_1/top` 上
  - `pen` 在 `desk_1/top` 上
  - `pencil_2` 在 `desk_1/top` 上
  - 手里空着
- 摆法 `four`：
  - `pencil` 在 `desk_1/top` 上
  - `pen` 在 `desk_1/top` 上
  - `pencil_2` 在 `desk_1/top` 上
  - `pen_2` 在 `desk_1/top` 上
  - 手里空着

**参考调用顺序**：

- 摆法 `two`：1. `search(object=pencil, region=bedroom_0_1)` → 2. `navigate(destination=pencil)` → 3. `pick(object=pencil)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pencil, receptacle=desk_1/top, hint_xy=[-1.2, -5.95])` → 6. `search(object=pen, region=dining_room_0_1)` → 7. `navigate(destination=pen)` → 8. `pick(object=pen)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.9, -5.95])`
- 摆法 `three`：1. `search(object=pencil, region=bedroom_0_1)` → 2. `navigate(destination=pencil)` → 3. `pick(object=pencil)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pencil, receptacle=desk_1/top, hint_xy=[-1.2, -5.95])` → 6. `search(object=pen, region=dining_room_0_1)` → 7. `navigate(destination=pen)` → 8. `pick(object=pen)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.9, -5.95])` → 11. `search(object=pencil_2, region=living_room_0_0)` → 12. `navigate(destination=pencil_2)` → 13. `pick(object=pencil_2)` → 14. `navigate(destination=desk_1/top)` → 15. `place(object=pencil_2, receptacle=desk_1/top, hint_xy=[-0.6, -5.95])`
- 摆法 `four`：1. `search(object=pencil, region=bedroom_0_1)` → 2. `navigate(destination=pencil)` → 3. `pick(object=pencil)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pencil, receptacle=desk_1/top, hint_xy=[-1.2, -5.95])` → 6. `search(object=pen, region=dining_room_0_1)` → 7. `navigate(destination=pen)` → 8. `pick(object=pen)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.9, -5.95])` → 11. `search(object=pencil_2, region=living_room_0_0)` → 12. `navigate(destination=pencil_2)` → 13. `pick(object=pencil_2)` → 14. `navigate(destination=desk_1/top)` → 15. `place(object=pencil_2, receptacle=desk_1/top, hint_xy=[-0.6, -5.95])` → 16. `search(object=pen_2, region=kitchen_0_1)` → 17. `navigate(destination=pen_2)` → 18. `pick(object=pen_2)` → 19. `navigate(destination=desk_1/top)` → 20. `place(object=pen_2, receptacle=desk_1/top, hint_xy=[-0.3, -5.95])`

### homework_ready（Task）

**情况**：指令只说"把写作业要用的东西准备到书桌上"；家里有笔、作业本，旁边还有一本书（不是作业本）和泰迪熊 → 自己推出要一支笔和一本作业本，书和泰迪熊不动

**指令**：孩子马上要在书房书桌写作业了。把写作业要用的东西准备到书桌上。

**成功条件**：

- 摆法 `several`：
  - `teddy_bear`、`book_red` 没被挪动（离开局位置不超过 5 cm）
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `pen` 在 `desk_1/top` 上
      - `notebook_1` 在 `desk_1/top` 上
    - 第 2 组：
      - `pen` 在 `desk_1/top` 上
      - `notebook_2` 在 `desk_1/top` 上
    - 第 3 组：
      - `pencil` 在 `desk_1/top` 上
      - `notebook_1` 在 `desk_1/top` 上
    - 第 4 组：
      - `pencil` 在 `desk_1/top` 上
      - `notebook_2` 在 `desk_1/top` 上
    - 第 5 组：
      - `pen_2` 在 `desk_1/top` 上
      - `notebook_1` 在 `desk_1/top` 上
    - 第 6 组：
      - `pen_2` 在 `desk_1/top` 上
      - `notebook_2` 在 `desk_1/top` 上
- 摆法 `single`：
  - `teddy_bear`、`book_red` 没被挪动（离开局位置不超过 5 cm）
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `pen` 在 `desk_1/top` 上
      - `notebook_1` 在 `desk_1/top` 上
- 摆法 `pencil_only`：
  - `teddy_bear`、`book_red` 没被挪动（离开局位置不超过 5 cm）
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `pencil` 在 `desk_1/top` 上
      - `notebook_1` 在 `desk_1/top` 上

**参考调用顺序**：

- 摆法 `single`：1. `search(object=pen, region=bedroom_0_1)` → 2. `navigate(destination=pen)` → 3. `pick(object=pen)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.9, -5.95])` → 6. `search(object=notebook_1, region=dining_room_0_1)` → 7. `navigate(destination=notebook_1)` → 8. `expose(object=notebook_1)` → 9. `look(target=notebook_1)` → 10. `pick(object=notebook_1)` → 11. `navigate(destination=desk_1/top)` → 12. `place(object=notebook_1, receptacle=desk_1/top, hint_xy=[-0.6, -5.95])`
- 摆法 `several`：1. `search(object=pen, region=bedroom_0_1)` → 2. `navigate(destination=pen)` → 3. `pick(object=pen)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.9, -5.95])` → 6. `search(object=notebook_2, region=living_room_0_0)` → 7. `navigate(destination=notebook_2)` → 8. `expose(object=notebook_2)` → 9. `look(target=notebook_2)` → 10. `pick(object=notebook_2)` → 11. `navigate(destination=desk_1/top)` → 12. `place(object=notebook_2, receptacle=desk_1/top, hint_xy=[-0.6, -5.95])`
- 摆法 `pencil_only`：1. `search(object=notebook_1, region=bedroom_0_1)` → 2. `navigate(destination=notebook_1)` → 3. `expose(object=notebook_1)` → 4. `look(target=notebook_1)` → 5. `pick(object=notebook_1)` → 6. `navigate(destination=desk_1/top)` → 7. `place(object=notebook_1, receptacle=desk_1/top, hint_xy=[-0.9, -5.95])` → 8. `search(object=pencil, region=dining_room_0_1)` → 9. `navigate(destination=pencil)` → 10. `pick(object=pencil)` → 11. `navigate(destination=desk_1/top)` → 12. `place(object=pencil, receptacle=desk_1/top, hint_xy=[-0.6, -5.95])`

### pens_per_notebook（Task）

**情况**：孩子们在书桌写作业，指令说桌上有几本作业本就拿几支笔，每本旁边放一支，不要多拿；家里有 4 支笔分散在不同房间 → 先数作业本，再拿正好那么多支，每本旁边放一支，其余的笔不动

**指令**：孩子们在书房书桌写作业，每人一本作业本。桌上有几本作业本，就拿几支笔（钢笔、铅笔都行）来，每本旁边放一支，不要多拿。

**成功条件**：

- 摆法 `notebooks_2`：
  - `hw_notebook_1` 离其中至少一个不超过 10 cm：`pencil`、`pen`、`pen_2`、`pencil_2`
  - `hw_notebook_2` 离其中至少一个不超过 10 cm：`pencil`、`pen`、`pen_2`、`pencil_2`
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `pencil` 在 `desk_1/top` 上
      - `pen` 在 `desk_1/top` 上
      - `pen_2` 没被挪动（离开局位置不超过 3 cm）
      - `pencil_2` 没被挪动（离开局位置不超过 3 cm）
    - 第 2 组：
      - `pencil` 在 `desk_1/top` 上
      - `pen_2` 在 `desk_1/top` 上
      - `pen` 没被挪动（离开局位置不超过 3 cm）
      - `pencil_2` 没被挪动（离开局位置不超过 3 cm）
    - 第 3 组：
      - `pencil` 在 `desk_1/top` 上
      - `pencil_2` 在 `desk_1/top` 上
      - `pen` 没被挪动（离开局位置不超过 3 cm）
      - `pen_2` 没被挪动（离开局位置不超过 3 cm）
    - 第 4 组：
      - `pen` 在 `desk_1/top` 上
      - `pen_2` 在 `desk_1/top` 上
      - `pencil` 没被挪动（离开局位置不超过 3 cm）
      - `pencil_2` 没被挪动（离开局位置不超过 3 cm）
    - 第 5 组：
      - `pen` 在 `desk_1/top` 上
      - `pencil_2` 在 `desk_1/top` 上
      - `pencil` 没被挪动（离开局位置不超过 3 cm）
      - `pen_2` 没被挪动（离开局位置不超过 3 cm）
    - 第 6 组：
      - `pen_2` 在 `desk_1/top` 上
      - `pencil_2` 在 `desk_1/top` 上
      - `pencil` 没被挪动（离开局位置不超过 3 cm）
      - `pen` 没被挪动（离开局位置不超过 3 cm）
- 摆法 `notebooks_3`：
  - `hw_notebook_1` 离其中至少一个不超过 10 cm：`pencil`、`pen`、`pen_2`、`pencil_2`
  - `hw_notebook_2` 离其中至少一个不超过 10 cm：`pencil`、`pen`、`pen_2`、`pencil_2`
  - `hw_notebook_3` 离其中至少一个不超过 10 cm：`pencil`、`pen`、`pen_2`、`pencil_2`
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `pencil` 在 `desk_1/top` 上
      - `pen` 在 `desk_1/top` 上
      - `pen_2` 在 `desk_1/top` 上
      - `pencil_2` 没被挪动（离开局位置不超过 3 cm）
    - 第 2 组：
      - `pencil` 在 `desk_1/top` 上
      - `pen` 在 `desk_1/top` 上
      - `pencil_2` 在 `desk_1/top` 上
      - `pen_2` 没被挪动（离开局位置不超过 3 cm）
    - 第 3 组：
      - `pencil` 在 `desk_1/top` 上
      - `pen_2` 在 `desk_1/top` 上
      - `pencil_2` 在 `desk_1/top` 上
      - `pen` 没被挪动（离开局位置不超过 3 cm）
    - 第 4 组：
      - `pen` 在 `desk_1/top` 上
      - `pen_2` 在 `desk_1/top` 上
      - `pencil_2` 在 `desk_1/top` 上
      - `pencil` 没被挪动（离开局位置不超过 3 cm）

**参考调用顺序**：

- 摆法 `notebooks_2`：1. `search(object=pencil, region=bedroom_0_1)` → 2. `navigate(destination=pencil)` → 3. `pick(object=pencil)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pencil, receptacle=desk_1/top, hint_xy=[-0.85, -5.92])` → 6. `search(object=pen, region=bedroom_0_1)` → 7. `navigate(destination=pen)` → 8. `pick(object=pen)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.3, -5.92])`
- 摆法 `notebooks_3`：1. `search(object=pencil, region=bedroom_0_1)` → 2. `navigate(destination=pencil)` → 3. `pick(object=pencil)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pencil, receptacle=desk_1/top, hint_xy=[-1.0, -5.92])` → 6. `search(object=pen, region=bedroom_0_1)` → 7. `navigate(destination=pen)` → 8. `pick(object=pen)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.57, -5.92])` → 11. `search(object=pen_2, region=living_room_0_0)` → 12. `navigate(destination=pen_2)` → 13. `pick(object=pen_2)` → 14. `navigate(destination=desk_1/top)` → 15. `place(object=pen_2, receptacle=desk_1/top, hint_xy=[-0.14, -5.92])`

### errand_combined（Task）

**情况**：两件事：拿一支钢笔到书房书桌；书桌上有个用过的马克杯要拿回厨房台面；只有一只手 → 先拿钢笔到书桌，放下后顺手拿起马克杯送回厨房，比单独跑一趟省路

**指令**：孩子在书房书桌写作业要用钢笔，拿一支过去。另外，那张书桌上有个用过的马克杯，要拿回厨房台面。

**成功条件**：

- `pen` 在 `desk_1/top` 上
- `used_mug` 在 `kitchen_counter_2/top` 上
- `used_mug` 立着
- 手里空着

**参考调用顺序**：

- 摆法 `pen_bedroom`：1. `search(object=pen, region=bedroom_0_1)` → 2. `navigate(destination=pen)` → 3. `pick(object=pen)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.75, -5.95])` → 6. `pick(object=used_mug)` → 7. `navigate(destination=kitchen_counter_2/top)` → 8. `place(object=used_mug, receptacle=kitchen_counter_2/top, hint_xy=[-0.15, 7.3])`
- 摆法 `pen_dining`：1. `search(object=pen, region=dining_room_0_1)` → 2. `navigate(destination=pen)` → 3. `pick(object=pen)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.75, -5.95])` → 6. `pick(object=used_mug)` → 7. `navigate(destination=kitchen_counter_2/top)` → 8. `place(object=used_mug, receptacle=kitchen_counter_2/top, hint_xy=[-0.15, 7.3])`

### x6_gd_pen_or_pencil_cabinets（Task）

**情况**：两个矮柜里一个放钢笔、一个放铅笔 → 都打开看，优先拿钢笔，关好柜门

**指令**：孩子写作业要支笔。拿一支钢笔到书房书桌上，没有钢笔就拿铅笔。笔都收在厨房那两个矮柜里，拿完把柜门关好。

**成功条件**：

- `pen` 在 `desk_1/top` 上
- 手里空着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

- 摆法 `pen_in_4`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=pen)` → 13. `pick(object=pen)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `close(articulated=kitchen_cabinet_4)` → 16. `navigate(destination=desk_1/top)` → 17. `place(object=pen, receptacle=desk_1/top)`
- 摆法 `pen_in_6`：1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_4)` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=pen)` → 13. `pick(object=pen)` → 14. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 15. `close(articulated=kitchen_cabinet_6)` → 16. `navigate(destination=desk_1/top)` → 17. `place(object=pen, receptacle=desk_1/top)`

---

## T06_block_destination_occupied

> 把积木摆到靠墙矮柜上或电视柜上做展示。

### free（对照）

**情况**：矮柜顶是空的 → 放上去

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
  - 第 2 组：
    - `wooden_block_a` 在 `tv_stand_2/top` 上
  - 第 3 组：
    - `wooden_block_b` 在 `kitchen_cabinet_6/top` 上
  - 第 4 组：
    - `wooden_block_b` 在 `tv_stand_2/top` 上

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=kitchen_cabinet_6/top)` → 5. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top)`

### occupied（Task）

**情况**：矮柜顶被锅盖和燕麦碗占着，中间的缝太窄 → 看一眼柜顶，发现满了就改放电视柜（不先往满的柜顶上放）

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
  - 第 2 组：
    - `wooden_block_a` 在 `tv_stand_2/top` 上
  - 第 3 组：
    - `wooden_block_b` 在 `kitchen_cabinet_6/top` 上
  - 第 4 组：
    - `wooden_block_b` 在 `tv_stand_2/top` 上

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `navigate(destination=tv_stand_2/top)`（换做法） → 6. `place(object=wooden_block_a, receptacle=tv_stand_2/top)`（换做法）

### occupied_block_away（Task）

**情况**：柜顶满了，积木也不在原处 → 先找积木，再放电视柜

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
  - 第 2 组：
    - `wooden_block_a` 在 `tv_stand_2/top` 上
  - 第 3 组：
    - `wooden_block_b` 在 `kitchen_cabinet_6/top` 上
  - 第 4 组：
    - `wooden_block_b` 在 `tv_stand_2/top` 上

**参考调用顺序**：

- 摆法 `occupied_block_away`：1. `look(target=kitchen_island/top)` → 2. `search(object=wooden_block_a, region=dining_room_0_1)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `look(target=kitchen_cabinet_6/top)` → 6. `navigate(destination=tv_stand_2/top)`（换做法） → 7. `place(object=wooden_block_a, receptacle=tv_stand_2/top)`（换做法）
- 摆法 `alt_tv_stand_2`：1. `look(target=kitchen_island/top)` → 2. `search(object=wooden_block_a, region=living_room_0_0)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `look(target=kitchen_cabinet_6/top)` → 6. `navigate(destination=tv_stand_2/top)`（换做法） → 7. `place(object=wooden_block_a, receptacle=tv_stand_2/top)`（换做法）

### display_row（Task）

**情况**：三块积木要在靠墙矮柜顶排成一排展示：摆正、放在前面看得见的地方、彼此别挨着；积木散在不同地方 → 一块块拿来，每放一块都要给下一块留位置

**指令**：把三块积木在靠墙矮柜顶上排成一排展示：摆正（和柜子边平行），放在前面看得见的地方，彼此别挨着。

**成功条件**：

- `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
- `wooden_block_b` 在 `kitchen_cabinet_6/top` 上
- `floor_block` 在 `kitchen_cabinet_6/top` 上
- `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
- `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
- `floor_block` 摆正（和台面边平行，偏差不超过 5°）
- `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
- `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
- `floor_block` 从房间里看得见（前面没有更高的东西挡着）
- `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
- `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
- `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
- 手里空着

**参考调用顺序**：

- 摆法 `island_floor`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=kitchen_cabinet_6/top)` → 5. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top, hint_xy=[3.32, 0.45])` → 6. `navigate(destination=wooden_block_b)` → 7. `pick(object=wooden_block_b)` → 8. `navigate(destination=kitchen_cabinet_6/top)` → 9. `place(object=wooden_block_b, receptacle=kitchen_cabinet_6/top, hint_xy=[3.5, 0.45])` → 10. `search(object=floor_block, region=living_room_0_0)` → 11. `navigate(destination=floor_block)` → 12. `pick(object=floor_block)` → 13. `navigate(destination=kitchen_cabinet_6/top)` → 14. `place(object=floor_block, receptacle=kitchen_cabinet_6/top, hint_xy=[3.68, 0.45])`
- 摆法 `spread`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=kitchen_cabinet_6/top)` → 5. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top, hint_xy=[3.32, 0.45])` → 6. `search(object=wooden_block_b, region=dining_room_0_1)` → 7. `navigate(destination=wooden_block_b)` → 8. `pick(object=wooden_block_b)` → 9. `navigate(destination=kitchen_cabinet_6/top)` → 10. `place(object=wooden_block_b, receptacle=kitchen_cabinet_6/top, hint_xy=[3.5, 0.45])` → 11. `search(object=floor_block, region=kitchen_0_1)` → 12. `navigate(destination=floor_block)` → 13. `pick(object=floor_block)` → 14. `navigate(destination=kitchen_cabinet_6/top)` → 15. `place(object=floor_block, receptacle=kitchen_cabinet_6/top, hint_xy=[3.68, 0.45])`

### display_spot_or_tv（Task）

**情况**：矮柜顶上立着三盒麦片和一瓶果汁；指令说柜顶的东西都别挪，没有看得见的位置就改放电视柜 → 从房间里看柜顶：东西摆在后排、前面空着就放矮柜前排（这时放电视柜算失败）；东西占满前排、后面的空位看不到，就放电视柜（挪麦片腾位置算失败）

**指令**：把积木摆到靠墙矮柜顶上展示，要从房间里看得见。柜顶上的盒子和瓶子都别挪；要是它们挡得没有看得见的位置，就摆到电视柜上。

**成功条件**：

- 摆法 `front_free`：
  - `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
  - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
  - `wooden_block_a` 离台面边缘至少 2 cm
  - `clutter_cereal_a`、`clutter_cereal_b`、`juice_bottle`、`clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
  - `clutter_cereal_a`、`clutter_cereal_b`、`juice_bottle`、`clutter_cereal_c` 立着
  - 手里空着
- 摆法 `front_taken`：
  - `wooden_block_a` 在 `tv_stand_2/top` 上
  - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
  - `wooden_block_a` 离台面边缘至少 2 cm
  - `clutter_cereal_a`、`clutter_cereal_b`、`juice_bottle`、`clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
  - `clutter_cereal_a`、`clutter_cereal_b`、`juice_bottle`、`clutter_cereal_c` 立着
  - 手里空着

**参考调用顺序**：

- 摆法 `front_taken`：1. `look(target=kitchen_island/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=wooden_block_a, receptacle=tv_stand_2/top)`
- 摆法 `front_free`：1. `look(target=kitchen_island/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top, hint_xy=[3.433, 0.465])`

### seen_from_bed（Task）

**情况**：孩子今晚想躺在床上看着积木；指令只说"躺在床上能看到的地方"。从枕头上看，只有床头边的矮书架在视线里（远处低矮的家具被床本身挡住），书架顶上立着孩子的几个盒子，盒子后面那块从床上看不到 → 设想孩子躺着的视线，把积木放在书架顶朝着枕头、没被盒子挡住的那一侧；盒子不动。判定从孩子眼睛的位置算视线

**指令**：孩子今晚想躺在床上看着积木。把积木摆在孩子躺在床上能看到的地方。

**成功条件**：

- 摆法 `boxes_middle`：
  - `wooden_block_a` 在 `bookcase_3/top` 上
  - `wooden_block_a` 从 (0.0, -4.6, 高 1.2 m) 这个位置看得见（顶面至少 50% 不被别的东西挡住）
  - `bedside_box_1`、`bedside_box_2`、`bedside_box_3` 没被挪动（离开局位置不超过 5 cm）
  - `bedside_box_1`、`bedside_box_2`、`bedside_box_3` 立着
  - 手里空着
- 摆法 `boxes_corner`：
  - `wooden_block_a` 在 `bookcase_3/top` 上
  - `wooden_block_a` 从 (0.0, -4.6, 高 1.2 m) 这个位置看得见（顶面至少 50% 不被别的东西挡住）
  - `bedside_box_1`、`bedside_box_2` 没被挪动（离开局位置不超过 5 cm）
  - `bedside_box_1`、`bedside_box_2` 立着
  - 手里空着

**参考调用顺序**：

- 摆法 `boxes_middle`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `explore_room(room=bedroom_0_1)` → 5. `navigate(destination=bookcase_3/top)` → 6. `look(target=bookcase_3/top)` → 7. `place(object=wooden_block_a, receptacle=bookcase_3/top, hint_xy=[1.88, -4.88])`
- 摆法 `boxes_corner`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `explore_room(room=bedroom_0_1)` → 5. `navigate(destination=bookcase_3/top)` → 6. `look(target=bookcase_3/top)` → 7. `place(object=wooden_block_a, receptacle=bookcase_3/top, hint_xy=[2.15, -4.74])`

---

## T07_heat_oatmeal

> 把剩下的燕麦粥热一下当早饭（至少 40 度）。做完后灶台要关火，微波炉门要关好。

### microwave_works（对照）

**情况**：微波炉正常 → 放进去加热

**成功条件**：

- `oatmeal` 温度至少 40 °C
- `kitchen_stove` 已经停止加热
- `kitchen_microwave` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_island/top)` → 4. `navigate(destination=oatmeal)` → 5. `pick(object=oatmeal)` → 6. `navigate(destination=kitchen_microwave/inside_floor)` → 7. `place(object=oatmeal, receptacle=kitchen_microwave/inside_floor)` → 8. `close(articulated=kitchen_microwave)` → 9. `heat(food=oatmeal, appliance=kitchen_microwave, temp_c=40)`

### microwave_broken（Task）

**情况**：微波炉转但不热，指令里没说 → 先放进微波炉热，发现热不起来，再改用灶台

**成功条件**：

- `oatmeal` 温度至少 40 °C
- `kitchen_stove` 已经停止加热
- `kitchen_microwave` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `navigate(destination=oatmeal)` → 4. `pick(object=oatmeal)` → 5. `navigate(destination=kitchen_microwave/inside_floor)` → 6. `place(object=oatmeal, receptacle=kitchen_microwave/inside_floor)` → 7. `close(articulated=kitchen_microwave)` → 8. `heat(food=oatmeal, appliance=kitchen_microwave, temp_c=40)` → 9. `stop(appliance=kitchen_microwave)`（换做法） → 10. `pick(object=oatmeal)`（换做法） → 11. `navigate(destination=kitchen_stove/top)`（换做法） → 12. `place(object=oatmeal, receptacle=kitchen_stove/top)`（换做法） → 13. `heat(food=oatmeal, appliance=kitchen_stove, temp_c=40)`（换做法） → 14. `navigate(destination=kitchen_microwave)` → 15. `close(articulated=kitchen_microwave)`

### broken_oatmeal_away（Task）

**情况**：微波炉不热，燕麦粥也不在原处 → 先找粥，发现微波炉不热后改用灶台

**成功条件**：

- `oatmeal` 温度至少 40 °C
- `kitchen_stove` 已经停止加热
- `kitchen_microwave` 关着
- 手里空着

**参考调用顺序**：

- 摆法 `broken_oatmeal_away`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `search(object=oatmeal, region=living_room_0_0)` → 4. `navigate(destination=oatmeal)` → 5. `pick(object=oatmeal)` → 6. `navigate(destination=kitchen_microwave/inside_floor)` → 7. `place(object=oatmeal, receptacle=kitchen_microwave/inside_floor)` → 8. `close(articulated=kitchen_microwave)` → 9. `heat(food=oatmeal, appliance=kitchen_microwave, temp_c=40)` → 10. `stop(appliance=kitchen_microwave)`（换做法） → 11. `pick(object=oatmeal)`（换做法） → 12. `navigate(destination=kitchen_stove/top)`（换做法） → 13. `place(object=oatmeal, receptacle=kitchen_stove/top)`（换做法） → 14. `heat(food=oatmeal, appliance=kitchen_stove, temp_c=40)`（换做法） → 15. `navigate(destination=kitchen_microwave)` → 16. `close(articulated=kitchen_microwave)`
- 摆法 `alt_dining_table_2`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `search(object=oatmeal, region=dining_room_0_1)` → 4. `navigate(destination=oatmeal)` → 5. `pick(object=oatmeal)` → 6. `navigate(destination=kitchen_microwave/inside_floor)` → 7. `place(object=oatmeal, receptacle=kitchen_microwave/inside_floor)` → 8. `close(articulated=kitchen_microwave)` → 9. `heat(food=oatmeal, appliance=kitchen_microwave, temp_c=40)` → 10. `stop(appliance=kitchen_microwave)`（换做法） → 11. `pick(object=oatmeal)`（换做法） → 12. `navigate(destination=kitchen_stove/top)`（换做法） → 13. `place(object=oatmeal, receptacle=kitchen_stove/top)`（换做法） → 14. `heat(food=oatmeal, appliance=kitchen_stove, temp_c=40)`（换做法） → 15. `navigate(destination=kitchen_microwave)` → 16. `close(articulated=kitchen_microwave)`

### microwave_holds_pot（Task）

**情况**：微波炉里放着带盖的汤锅，放不下碗 → 改用灶台，微波炉门关好

**指令**：请用合适方式把燕麦粥加热到至少 40°C，完成后关火并关好微波炉门。

**成功条件**：

- `oatmeal` 温度至少 40 °C
- `kitchen_stove` 已经停止加热
- `kitchen_microwave` 关着
- `handled_cooking_pot` 不在地上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_microwave/inside_floor)` → 4. `close(articulated=kitchen_microwave)` → 5. `look(target=kitchen_island/top)` → 6. `navigate(destination=oatmeal)` → 7. `pick(object=oatmeal)` → 8. `navigate(destination=kitchen_stove/top)`（换做法） → 9. `place(object=oatmeal, receptacle=kitchen_stove/top)`（换做法） → 10. `heat(food=oatmeal, appliance=kitchen_stove, temp_c=40)`（换做法）

### vessel_decides_appliance（Task）

**情况**：两个电器都正常；剩饭装在五种容器之一里，指令轻提示"注意容器适不适合进微波炉或放到灶上" → 按容器的材质选电器：瓷碗、玻璃盒进微波炉（放灶上不算热），金属锅、不锈钢饭盒、铝箔盒上灶台（进微波炉不热）

**指令**：把剩饭热一下当早饭（至少 40 度），注意装剩饭的容器适不适合进微波炉或放到灶上。做完后灶台要关火，微波炉门要关好。

**成功条件**：

- 摆法 `in_foil_tray`：
  - `foil_takeout_tray` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - `kitchen_microwave` 关着
  - 手里空着
- 摆法 `in_glass_box`：
  - `glass_food_container` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - `kitchen_microwave` 关着
  - 手里空着
- 摆法 `in_ceramic_bowl`：
  - `oatmeal_bowl` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - `kitchen_microwave` 关着
  - 手里空着
- 摆法 `in_pot`：
  - `soup_pot` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - `kitchen_microwave` 关着
  - 手里空着
- 摆法 `in_steel_box`：
  - `steel_lunch_box` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - `kitchen_microwave` 关着
  - 手里空着

**参考调用顺序**：

- 摆法 `in_ceramic_bowl`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_island/top)` → 4. `navigate(destination=oatmeal_bowl)` → 5. `pick(object=oatmeal_bowl)` → 6. `navigate(destination=kitchen_microwave/inside_floor)` → 7. `place(object=oatmeal_bowl, receptacle=kitchen_microwave/inside_floor)` → 8. `close(articulated=kitchen_microwave)` → 9. `heat(food=oatmeal_bowl, appliance=kitchen_microwave, temp_c=40)`
- 摆法 `in_glass_box`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_island/top)` → 4. `navigate(destination=glass_food_container)` → 5. `expose(object=glass_food_container)` → 6. `look(target=glass_food_container)` → 7. `pick(object=glass_food_container)` → 8. `navigate(destination=kitchen_microwave/inside_floor)` → 9. `place(object=glass_food_container, receptacle=kitchen_microwave/inside_floor)` → 10. `close(articulated=kitchen_microwave)` → 11. `heat(food=glass_food_container, appliance=kitchen_microwave, temp_c=40)`
- 摆法 `in_pot`：1. `look(target=kitchen_island/top)` → 2. `search(object=soup_pot, region=dining_room_0_1)` → 3. `navigate(destination=soup_pot)` → 4. `pick(object=soup_pot)` → 5. `navigate(destination=kitchen_stove/top)` → 6. `place(object=soup_pot, receptacle=kitchen_stove/top, hint_xy=[8.41, 1.725])` → 7. `heat(food=soup_pot, appliance=kitchen_stove, temp_c=40)`
- 摆法 `in_steel_box`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=steel_lunch_box)` → 3. `expose(object=steel_lunch_box)` → 4. `look(target=steel_lunch_box)` → 5. `pick(object=steel_lunch_box)` → 6. `navigate(destination=kitchen_stove/top)` → 7. `place(object=steel_lunch_box, receptacle=kitchen_stove/top, hint_xy=[8.41, 1.725])` → 8. `heat(food=steel_lunch_box, appliance=kitchen_stove, temp_c=40)`
- 摆法 `in_foil_tray`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=foil_takeout_tray)` → 3. `expose(object=foil_takeout_tray)` → 4. `look(target=foil_takeout_tray)` → 5. `pick(object=foil_takeout_tray)` → 6. `navigate(destination=kitchen_stove/top)` → 7. `place(object=foil_takeout_tray, receptacle=kitchen_stove/top, hint_xy=[8.41, 1.725])` → 8. `heat(food=foil_takeout_tray, appliance=kitchen_stove, temp_c=40)`

### two_portions（Task）

**情况**：早饭要热两样：一碗燕麦粥（只能微波炉）和一锅剩汤（只能灶台），都要至少 40 度；放着会变凉 → 两个电器同时开：汤锅上灶开火、粥碗进微波炉按启动，等一会儿再都关掉；一样一样热完，先热的那样会凉掉

**指令**：早饭要热两样：一碗燕麦粥和一锅剩汤，都要热到至少 40 度。做完后灶台要关火，微波炉门要关好。

**成功条件**：

- `oatmeal_bowl` 温度至少 40 °C
- `soup_pot` 温度至少 40 °C
- `kitchen_stove` 已经停止加热
- `kitchen_microwave` 已经停止加热
- `kitchen_microwave` 关着
- 手里空着

**参考调用顺序**：

- 摆法 `dining`：1. `search(object=soup_pot, region=dining_room_0_1)` → 2. `navigate(destination=soup_pot)` → 3. `pick(object=soup_pot)` → 4. `navigate(destination=kitchen_stove/top)` → 5. `place(object=soup_pot, receptacle=kitchen_stove/top, hint_xy=[8.41, 1.725])` → 6. `press(button=kitchen_stove/power_button)` → 7. `navigate(destination=kitchen_microwave)` → 8. `open(articulated=kitchen_microwave)` → 9. `look(target=kitchen_island/top)` → 10. `navigate(destination=oatmeal_bowl)` → 11. `pick(object=oatmeal_bowl)` → 12. `navigate(destination=kitchen_microwave/inside_floor)` → 13. `place(object=oatmeal_bowl, receptacle=kitchen_microwave/inside_floor)` → 14. `close(articulated=kitchen_microwave)` → 15. `navigate(destination=kitchen_microwave/start_button)` → 16. `press(button=kitchen_microwave/start_button)` → 17. `wait(seconds=25)` → 18. `stop(appliance=kitchen_microwave)` → 19. `close(articulated=kitchen_microwave)` → 20. `navigate(destination=kitchen_stove)` → 21. `stop(appliance=kitchen_stove)`
- 摆法 `counter`：1. `search(object=soup_pot, region=kitchen_0_1)` → 2. `navigate(destination=soup_pot)` → 3. `pick(object=soup_pot)` → 4. `navigate(destination=kitchen_stove/top)` → 5. `place(object=soup_pot, receptacle=kitchen_stove/top, hint_xy=[8.41, 1.725])` → 6. `press(button=kitchen_stove/power_button)` → 7. `navigate(destination=kitchen_microwave)` → 8. `open(articulated=kitchen_microwave)` → 9. `look(target=kitchen_island/top)` → 10. `navigate(destination=oatmeal_bowl)` → 11. `pick(object=oatmeal_bowl)` → 12. `navigate(destination=kitchen_microwave/inside_floor)` → 13. `place(object=oatmeal_bowl, receptacle=kitchen_microwave/inside_floor)` → 14. `close(articulated=kitchen_microwave)` → 15. `navigate(destination=kitchen_microwave/start_button)` → 16. `press(button=kitchen_microwave/start_button)` → 17. `wait(seconds=25)` → 18. `stop(appliance=kitchen_microwave)` → 19. `close(articulated=kitchen_microwave)` → 20. `navigate(destination=kitchen_stove)` → 21. `stop(appliance=kitchen_stove)`

---

## T08_wipe_island

> 做完饭用海绵擦一下厨房岛台，擦完把海绵放回岛台上。

### sponge_on_island（对照）

**情况**：海绵在岛台上 → 擦完放回

**成功条件**：

- `kitchen_island/top` 擦过
- `kitchen_sponge` 在 `kitchen_island/top` 上
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=kitchen_sponge)` → 4. `pick(object=kitchen_sponge)` → 5. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 6. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`

### far_sponge_tv（Task）

**情况**：从餐厅出发，海绵不在岛台 → 先找海绵

**成功条件**：

- `kitchen_island/top` 擦过
- `kitchen_sponge` 在 `kitchen_island/top` 上
- 手里空着

**参考调用顺序**：

- 摆法 `far_sponge_tv`：1. `search(object=kitchen_sponge, region=living_room_0_0)` → 2. `navigate(destination=kitchen_sponge)` → 3. `pick(object=kitchen_sponge)` → 4. `navigate(destination=kitchen_island/top)` → 5. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 6. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`
- 摆法 `alt_dining_table_2`：1. `search(object=kitchen_sponge, region=dining_room_0_1)` → 2. `navigate(destination=kitchen_sponge)` → 3. `pick(object=kitchen_sponge)` → 4. `navigate(destination=kitchen_island/top)` → 5. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 6. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`

### wipe_and_sort（Task）

**情况**：岛台上两排东西：厨房用品（擀面杖、汽水罐、马克杯、燕麦碗、书、勺子、果汁）中间混着孩子的玩具；客厅地上有玩具箱，海绵在电视柜上；指令说玩具收进玩具箱，厨房的东西留在岛台上 → 按类别分：玩具送进玩具箱不再拿回，厨房的东西不动；玩具拿走后前排空出一条，擦完海绵留在岛台上

**指令**：用海绵把厨房岛台擦一下。岛台上孩子的玩具收进客厅里孩子的玩具箱，厨房的东西留在岛台上。擦完把海绵留在岛台上。

**成功条件**：

- 摆法 `duck`：
  - `kitchen_island/top` 擦过
  - `kitchen_sponge` 在 `kitchen_island/top` 上
  - 手里空着
  - `wooden_block_a` 在 `toy_box` 里
  - `rubber_duck` 在 `toy_box` 里
  - `rolling_pin`、`soda_can`、`mug`、`oatmeal`、`paperback_book`、`breakfast_spoon`、`juice_bottle` 没被挪动（离开局位置不超过 12 cm）
  - `soda_can`、`mug`、`juice_bottle`、`oatmeal` 立着
- 摆法 `blocks`：
  - `kitchen_island/top` 擦过
  - `kitchen_sponge` 在 `kitchen_island/top` 上
  - 手里空着
  - `wooden_block_a` 在 `toy_box` 里
  - `wooden_block_b` 在 `toy_box` 里
  - `rolling_pin`、`soda_can`、`mug`、`oatmeal`、`paperback_book`、`breakfast_spoon`、`juice_bottle` 没被挪动（离开局位置不超过 12 cm）
  - `soda_can`、`mug`、`juice_bottle`、`oatmeal` 立着

**参考调用顺序**：

- 摆法 `blocks`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=toy_box)` → 5. `place(object=wooden_block_a, receptacle=toy_box)` → 6. `navigate(destination=wooden_block_b)` → 7. `pick(object=wooden_block_b)` → 8. `navigate(destination=toy_box)` → 9. `place(object=wooden_block_b, receptacle=toy_box)` → 10. `look(target=tv_stand_2/top)` → 11. `navigate(destination=kitchen_sponge)` → 12. `pick(object=kitchen_sponge)` → 13. `navigate(destination=kitchen_island/top)` → 14. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 15. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`
- 摆法 `duck`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=toy_box)` → 5. `place(object=wooden_block_a, receptacle=toy_box)` → 6. `navigate(destination=rubber_duck)` → 7. `pick(object=rubber_duck)` → 8. `navigate(destination=toy_box)` → 9. `place(object=rubber_duck, receptacle=toy_box)` → 10. `look(target=tv_stand_2/top)` → 11. `navigate(destination=kitchen_sponge)` → 12. `pick(object=kitchen_sponge)` → 13. `navigate(destination=kitchen_island/top)` → 14. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 15. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`

### return_sponge_home（Task）

**情况**：有人用完海绵随手放在某张桌子上；指令说擦完把海绵收回平时放海绵的地方，但没说是哪里；客厅靠墙矮柜顶上有个浅托盘，里面放着一块备用海绵 → 找到海绵擦岛台，再把它放进那个托盘（放回原来的桌子或留在岛台上都算失败）

**指令**：有人用完海绵随手放在了某张桌子上。用它把厨房岛台擦一下，擦完把海绵收回平时放海绵的地方。

**成功条件**：

- `kitchen_island/top` 擦过
- `kitchen_sponge` 在 `sponge_tray` 里
- `spare_sponge` 在 `sponge_tray` 里
- 手里空着

**参考调用顺序**：

- 摆法 `dining`：1. `look(target=kitchen_island/top)` → 2. `search(object=kitchen_sponge, region=dining_room_0_1)` → 3. `navigate(destination=kitchen_sponge)` → 4. `pick(object=kitchen_sponge)` → 5. `navigate(destination=kitchen_island/top)` → 6. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 7. `navigate(destination=sponge_tray)` → 8. `place(object=kitchen_sponge, receptacle=sponge_tray)`
- 摆法 `study`：1. `look(target=kitchen_island/top)` → 2. `search(object=kitchen_sponge, region=living_room_0_1)` → 3. `navigate(destination=kitchen_sponge)` → 4. `pick(object=kitchen_sponge)` → 5. `navigate(destination=kitchen_island/top)` → 6. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 7. `navigate(destination=sponge_tray)` → 8. `place(object=kitchen_sponge, receptacle=sponge_tray)`
- 摆法 `far_dining`：1. `look(target=kitchen_island/top)` → 2. `search(object=kitchen_sponge, region=dining_room_0_0)` → 3. `navigate(destination=kitchen_sponge)` → 4. `pick(object=kitchen_sponge)` → 5. `navigate(destination=kitchen_island/top)` → 6. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 7. `navigate(destination=sponge_tray)` → 8. `place(object=kitchen_sponge, receptacle=sponge_tray)`

### which_surface（Task）

**情况**：早饭在岛台或餐桌上吃的：吃过的那边留着燕麦碗、勺子和擀面杖，另一边是干净的；指令只擦用过的那个 → 看哪边留着用过的东西，只擦那一个（两个都擦算失败），海绵留在岛台上

**指令**：早饭是在岛台或者餐桌上吃的。用海绵把吃过饭的那个擦一下；另一个是干净的，别擦。擦完把海绵留在岛台上。

**成功条件**：

- 摆法 `dining`：
  - `dining_table_2/top` 擦过
  - `kitchen_island/top` 没擦过
  - `kitchen_sponge` 在 `kitchen_island/top` 上
  - 手里空着
- 摆法 `island`：
  - `kitchen_island/top` 擦过
  - `dining_table_2/top` 没擦过
  - `kitchen_sponge` 在 `kitchen_island/top` 上
  - 手里空着

**参考调用顺序**：

- 摆法 `island`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=kitchen_sponge)` → 3. `pick(object=kitchen_sponge)` → 4. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 5. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`
- 摆法 `dining`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=kitchen_sponge)` → 3. `pick(object=kitchen_sponge)` → 4. `navigate(destination=dining_table_2/top)` → 5. `look(target=dining_table_2/top)` → 6. `navigate(destination=dining_table_2/top)` → 7. `wipe(surface=dining_table_2/top, tool=kitchen_sponge)` → 8. `navigate(destination=kitchen_island/top)` → 9. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`

---

## T09_tomato_soup

> 午饭做个番茄汤：把小番茄放进灶上的锅里，搅一搅，盖上锅盖，加热到 60 度，然后关火。

### lid_off（对照）

**情况**：锅盖在锅边 → 按步骤做完

**成功条件**：

- `cherry_tomato_1` 在 `handled_cooking_pot` 里
- `cherry_tomato_2` 在 `handled_cooking_pot` 里
- `cherry_tomato_1` 温度至少 60 °C
- `cherry_tomato_2` 温度至少 60 °C
- `handled_cooking_pot` 搅拌过
- `handled_cooking_pot` 盖着 `pot_lid`
- `kitchen_stove` 已经停止加热
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 3. `navigate(destination=breakfast_spoon)` → 4. `pick(object=breakfast_spoon)` → 5. `navigate(destination=handled_cooking_pot)` → 6. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 7. `navigate(destination=kitchen_island/top)` → 8. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 9. `navigate(destination=pot_lid)` → 10. `pick(object=pot_lid)` → 11. `navigate(destination=handled_cooking_pot)` → 12. `cover(container=handled_cooking_pot, lid=pot_lid)` → 13. `navigate(destination=kitchen_stove)` → 14. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

### lid_on_spoon_away（Action + Task）

**情况**：锅盖盖着，勺子也不在 → 揭盖；找勺子

**成功条件**：

- `cherry_tomato_1` 在 `handled_cooking_pot` 里
- `cherry_tomato_2` 在 `handled_cooking_pot` 里
- `cherry_tomato_1` 温度至少 60 °C
- `cherry_tomato_2` 温度至少 60 °C
- `handled_cooking_pot` 搅拌过
- `handled_cooking_pot` 盖着 `pot_lid`
- `kitchen_stove` 已经停止加热
- 手里空着

**参考调用顺序**：

- 摆法 `lid_on_spoon_away`：1. `look(target=kitchen_island/top)` → 2. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 3. `navigate(destination=handled_cooking_pot)` → 4. `uncover(container=handled_cooking_pot)` → 5. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 6. `search(object=breakfast_spoon, region=living_room_0_0)` → 7. `navigate(destination=breakfast_spoon)` → 8. `pick(object=breakfast_spoon)` → 9. `navigate(destination=handled_cooking_pot)` → 10. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 11. `navigate(destination=kitchen_island/top)` → 12. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 13. `navigate(destination=pot_lid)` → 14. `pick(object=pot_lid)` → 15. `navigate(destination=handled_cooking_pot)` → 16. `cover(container=handled_cooking_pot, lid=pot_lid)` → 17. `navigate(destination=kitchen_stove)` → 18. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`
- 摆法 `alt_dining_table_2`：1. `look(target=kitchen_island/top)` → 2. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 3. `navigate(destination=handled_cooking_pot)` → 4. `uncover(container=handled_cooking_pot)` → 5. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 6. `search(object=breakfast_spoon, region=dining_room_0_1)` → 7. `navigate(destination=breakfast_spoon)` → 8. `pick(object=breakfast_spoon)` → 9. `navigate(destination=handled_cooking_pot)` → 10. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 11. `navigate(destination=kitchen_island/top)` → 12. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 13. `navigate(destination=pot_lid)` → 14. `pick(object=pot_lid)` → 15. `navigate(destination=handled_cooking_pot)` → 16. `cover(container=handled_cooking_pot, lid=pot_lid)` → 17. `navigate(destination=kitchen_stove)` → 18. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

### pot_in_use（Task）

**情况**：灶上左边炉眼可能放着一锅昨天剩的番茄汤（满的），平时用的空锅在隔壁餐厅的餐桌上；指令只说"灶上的锅" → 先看锅里：已经装满别的汤的锅在用，番茄不能倒进去，那锅也别动；去餐厅把空锅拿到右边空炉眼上再做。灶上是空锅时就直接用

**成功条件**：

- `cherry_tomato_1` 在 `handled_cooking_pot` 里
- `cherry_tomato_2` 在 `handled_cooking_pot` 里
- `cherry_tomato_1` 温度至少 60 °C
- `cherry_tomato_2` 温度至少 60 °C
- `handled_cooking_pot` 搅拌过
- `handled_cooking_pot` 盖着 `pot_lid`
- `kitchen_stove` 已经停止加热
- 手里空着
- `soup_pot` 没被挪动（离开局位置不超过 3 cm）
- `soup_pot` 立着
- `cherry_tomato_1` 不在 `soup_pot` 里
- `cherry_tomato_2` 不在 `soup_pot` 里

**参考调用顺序**：

- 摆法 `in_use`：1. `look(target=kitchen_island/top)` → 2. `look(target=kitchen_stove/top)` → 3. `search(object=handled_cooking_pot, region=dining_room_0_1)` → 4. `navigate(destination=handled_cooking_pot)` → 5. `pick(object=handled_cooking_pot)` → 6. `navigate(destination=kitchen_stove/top)` → 7. `place(object=handled_cooking_pot, receptacle=kitchen_stove/top, hint_xy=[8.7, 1.725])` → 8. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 9. `navigate(destination=breakfast_spoon)` → 10. `pick(object=breakfast_spoon)` → 11. `navigate(destination=handled_cooking_pot)` → 12. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 13. `navigate(destination=kitchen_island/top)` → 14. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 15. `navigate(destination=pot_lid)` → 16. `pick(object=pot_lid)` → 17. `navigate(destination=handled_cooking_pot)` → 18. `cover(container=handled_cooking_pot, lid=pot_lid)` → 19. `navigate(destination=kitchen_stove)` → 20. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`
- 摆法 `free`：1. `look(target=kitchen_island/top)` → 2. `look(target=kitchen_stove/top)` → 3. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 4. `navigate(destination=breakfast_spoon)` → 5. `pick(object=breakfast_spoon)` → 6. `navigate(destination=handled_cooking_pot)` → 7. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 8. `navigate(destination=kitchen_island/top)` → 9. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 10. `navigate(destination=pot_lid)` → 11. `pick(object=pot_lid)` → 12. `navigate(destination=handled_cooking_pot)` → 13. `cover(container=handled_cooking_pot, lid=pot_lid)` → 14. `navigate(destination=kitchen_stove)` → 15. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

### tomato_in_fridge（Action + Task）

**情况**：汤要用三颗小番茄；岛台上只有两颗，第三颗收在关着的冰箱里（指令没说在哪） → 数一数不够，想到食材放在冰箱，开冰箱拿出来再关好（Action），而不是满屋找（Task）；三颗都在岛台上时去开冰箱是白跑

**指令**：午饭用三颗小番茄做番茄汤：放进灶上的锅里，搅一搅，盖上锅盖，加热到 60 度，然后关火。

**成功条件**：

- `cherry_tomato_1` 在 `handled_cooking_pot` 里
- `cherry_tomato_2` 在 `handled_cooking_pot` 里
- `cherry_tomato_1` 温度至少 60 °C
- `cherry_tomato_2` 温度至少 60 °C
- `handled_cooking_pot` 搅拌过
- `handled_cooking_pot` 盖着 `pot_lid`
- `kitchen_stove` 已经停止加热
- 手里空着
- `fridge_tomato` 在 `handled_cooking_pot` 里
- `fridge_tomato` 温度至少 60 °C
- `breakfast_fridge` 关着

**参考调用顺序**：

- 摆法 `in_fridge`：1. `look(target=kitchen_island/top)` → 2. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `bend()` → 6. `explore_furniture(furniture=breakfast_fridge)` → 7. `straighten()` → 8. `navigate(destination=fridge_tomato)` → 9. `pick(object=fridge_tomato)` → 10. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 11. `close(articulated=breakfast_fridge)` → 12. `navigate(destination=handled_cooking_pot)` → 13. `drop(object=fridge_tomato, container=handled_cooking_pot)` → 14. `navigate(destination=breakfast_spoon)` → 15. `pick(object=breakfast_spoon)` → 16. `navigate(destination=handled_cooking_pot)` → 17. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 18. `navigate(destination=kitchen_island/top)` → 19. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 20. `navigate(destination=pot_lid)` → 21. `pick(object=pot_lid)` → 22. `navigate(destination=handled_cooking_pot)` → 23. `cover(container=handled_cooking_pot, lid=pot_lid)` → 24. `navigate(destination=kitchen_stove)` → 25. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`
- 摆法 `on_island`：1. `look(target=kitchen_island/top)` → 2. `collect(objects=[cherry_tomato_1, cherry_tomato_2, fridge_tomato], container=handled_cooking_pot)` → 3. `navigate(destination=breakfast_spoon)` → 4. `pick(object=breakfast_spoon)` → 5. `navigate(destination=handled_cooking_pot)` → 6. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 7. `navigate(destination=kitchen_island/top)` → 8. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 9. `navigate(destination=pot_lid)` → 10. `pick(object=pot_lid)` → 11. `navigate(destination=handled_cooking_pot)` → 12. `cover(container=handled_cooking_pot, lid=pot_lid)` → 13. `navigate(destination=kitchen_stove)` → 14. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

### x6_gd_tomato_elsewhere（Task）

**情况**：一颗番茄在岛台，另一颗不在 → 先放一颗，再去找另一颗

**成功条件**：

- `cherry_tomato_1` 在 `handled_cooking_pot` 里
- `cherry_tomato_2` 在 `handled_cooking_pot` 里
- `cherry_tomato_1` 温度至少 60 °C
- `cherry_tomato_2` 温度至少 60 °C
- `handled_cooking_pot` 搅拌过
- `handled_cooking_pot` 盖着 `pot_lid`
- `kitchen_stove` 已经停止加热
- 手里空着

**参考调用顺序**：

- 摆法 `dining`：1. `look(target=kitchen_island/top)` → 2. `collect(objects=[cherry_tomato_1], container=handled_cooking_pot)`（补救） → 3. `search(object=cherry_tomato_2, region=dining_room_0_1)`（补救） → 4. `navigate(destination=cherry_tomato_2)`（补救） → 5. `pick(object=cherry_tomato_2)`（补救） → 6. `navigate(destination=handled_cooking_pot)`（补救） → 7. `drop(object=cherry_tomato_2, container=handled_cooking_pot)`（补救） → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=handled_cooking_pot)` → 11. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 12. `navigate(destination=kitchen_island/top)` → 13. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 14. `navigate(destination=pot_lid)` → 15. `pick(object=pot_lid)` → 16. `navigate(destination=handled_cooking_pot)` → 17. `cover(container=handled_cooking_pot, lid=pot_lid)` → 18. `navigate(destination=kitchen_stove)` → 19. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`
- 摆法 `cabinet6`：1. `look(target=kitchen_island/top)` → 2. `collect(objects=[cherry_tomato_1], container=handled_cooking_pot)`（补救） → 3. `search(object=cherry_tomato_2, region=living_room_0_0)`（补救） → 4. `navigate(destination=cherry_tomato_2)`（补救） → 5. `pick(object=cherry_tomato_2)`（补救） → 6. `navigate(destination=handled_cooking_pot)`（补救） → 7. `drop(object=cherry_tomato_2, container=handled_cooking_pot)`（补救） → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=handled_cooking_pot)` → 11. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 12. `navigate(destination=kitchen_island/top)` → 13. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 14. `navigate(destination=pot_lid)` → 15. `pick(object=pot_lid)` → 16. `navigate(destination=handled_cooking_pot)` → 17. `cover(container=handled_cooking_pot, lid=pot_lid)` → 18. `navigate(destination=kitchen_stove)` → 19. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

### pot_in_dining_room（Task）

**情况**：番茄旁边有碗和马克杯，锅却不在灶上，而在隔壁餐厅的餐桌上（锅盖在灶上） → 不能就近用碗或杯，要去餐厅把锅拿回炉眼上，再做汤

**指令**：请用合适锅具完成番茄入锅、搅拌、盖锅、加热至60°C和关火。

**成功条件**：

- `cherry_tomato_1` 在 `handled_cooking_pot` 里
- `cherry_tomato_2` 在 `handled_cooking_pot` 里
- `cherry_tomato_1` 温度至少 60 °C
- `cherry_tomato_2` 温度至少 60 °C
- `handled_cooking_pot` 搅拌过
- `handled_cooking_pot` 盖着 `pot_lid`
- `kitchen_stove` 已经停止加热
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `look(target=kitchen_stove/top)` → 3. `search(object=handled_cooking_pot, region=dining_room_0_1)` → 4. `navigate(destination=handled_cooking_pot)` → 5. `pick(object=handled_cooking_pot)` → 6. `navigate(destination=kitchen_stove/top)` → 7. `place(object=handled_cooking_pot, receptacle=kitchen_stove/top, hint_xy=[8.41, 1.725])` → 8. `navigate(destination=cherry_tomato_1)`（补救） → 9. `sweep(objects=[cherry_tomato_1, cherry_tomato_2], radius_m=0.12)`（补救） → 10. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)`（换做法） → 11. `navigate(destination=breakfast_spoon)` → 12. `pick(object=breakfast_spoon)` → 13. `navigate(destination=handled_cooking_pot)` → 14. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 15. `navigate(destination=kitchen_island/top)` → 16. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 17. `navigate(destination=pot_lid)` → 18. `pick(object=pot_lid)` → 19. `navigate(destination=handled_cooking_pot)` → 20. `cover(container=handled_cooking_pot, lid=pot_lid)` → 21. `navigate(destination=kitchen_stove)` → 22. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

---

## T10_trash_the_can

> 有人随手放了个空易拉罐，把它扔进垃圾桶。

### can_on_island（对照）

**情况**：罐子在岛台 → 扔掉

**成功条件**：

- `soda_can` 在 `trash_can` 里
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `explore_room(room=living_room_0_0)` → 3. `navigate(destination=soda_can)` → 4. `pick(object=soda_can)` → 5. `lift(object=soda_can, height_m=0.95)` → 6. `navigate(destination=trash_can)` → 7. `hover(object=soda_can, target=trash_can)` → 8. `drop(object=soda_can, container=trash_can)`

### can_in_dining_room（Task）

**情况**：罐子在隔壁看不到的地方 → 先找

**成功条件**：

- `soda_can` 在 `trash_can` 里
- 手里空着

**参考调用顺序**：

- 摆法 `can_in_dining_room`：1. `look(target=kitchen_island/top)` → 2. `explore_room(room=living_room_0_0)` → 3. `pick(object=soda_can)` → 4. `search(object=soda_can, region=dining_room_0_1)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=trash_can)` → 8. `drop(object=soda_can, container=trash_can)`
- 摆法 `alt_tv_stand_2`：1. `look(target=kitchen_island/top)` → 2. `explore_room(room=living_room_0_0)` → 3. `pick(object=soda_can)` → 4. `search(object=soda_can, region=living_room_0_0)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=trash_can)` → 8. `drop(object=soda_can, container=trash_can)`

### keep_kids_can（Task）

**情况**：两个一样的空易拉罐：一个和作业本、铅笔摆在一起（孩子留着做手工的），另一个单独放着；指令说孩子那个别扔 → 从罐子周围的东西认出孩子的，只扔另一个（扔了孩子的算失败）

**指令**：把喝完的空易拉罐扔进垃圾桶。孩子留着做手工的那个别扔。

**成功条件**：

- `soda_can` 在 `trash_can` 里
- 手里空着
- `kids_can`、`craft_notebook`、`craft_pencil` 没被挪动（离开局位置不超过 3 cm）
- `kids_can` 立着

**参考调用顺序**：

- 摆法 `kid_desk`：1. `look(target=kitchen_island/top)` → 2. `search(object=kids_can, region=living_room_0_1)` → 3. `navigate(destination=soda_can)` → 4. `pick(object=soda_can)` → 5. `lift(object=soda_can, height_m=0.95)` → 6. `navigate(destination=trash_can)` → 7. `hover(object=soda_can, target=trash_can)` → 8. `drop(object=soda_can, container=trash_can)`
- 摆法 `kid_island`：1. `look(target=kitchen_island/top)` → 2. `search(object=soda_can, region=living_room_0_1)` → 3. `navigate(destination=soda_can)` → 4. `pick(object=soda_can)` → 5. `lift(object=soda_can, height_m=0.95)` → 6. `navigate(destination=trash_can)` → 7. `hover(object=soda_can, target=trash_can)` → 8. `drop(object=soda_can, container=trash_can)`

### trash_moved（Task）

**情况**：罐子在岛台上，但垃圾桶今天不在岛台旁边的老地方 → 拿起罐子去找垃圾桶（找的是目的地，不是东西）

**成功条件**：

- `soda_can` 在 `trash_can` 里
- 手里空着

**参考调用顺序**：

- 摆法 `dining`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=soda_can)` → 3. `pick(object=soda_can)` → 4. `lift(object=soda_can, height_m=0.95)` → 5. `search(object=trash_can, region=dining_room_0_1)` → 6. `navigate(destination=trash_can)` → 7. `hover(object=soda_can, target=trash_can)` → 8. `drop(object=soda_can, container=trash_can)`
- 摆法 `bathroom`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=soda_can)` → 3. `pick(object=soda_can)` → 4. `lift(object=soda_can, height_m=0.95)` → 5. `search(object=trash_can, region=bathroom_0_1)` → 6. `navigate(destination=trash_can)` → 7. `hover(object=soda_can, target=trash_can)` → 8. `drop(object=soda_can, container=trash_can)`

### after_dinner_clear（Task）

**情况**：晚饭后餐桌上剩着空易拉罐，以及空的铝箔外卖盒、装着剩饭的玻璃保鲜盒、用过的马克杯中的两样；指令只说垃圾扔掉、剩菜进冰箱、用过的杯子回厨房台面、麦片盒留着 → 按每样东西是什么、什么状态决定去处；一只手，要先开冰箱门再去拿剩菜，放好后关门

**指令**：晚饭吃完了，把餐桌收拾干净：垃圾扔进垃圾桶，吃剩的收进冰箱，用过的杯子拿回厨房台面。麦片盒留在桌上。

**成功条件**：

- 摆法 `rubbish_leftovers`：
  - `soda_can` 在 `trash_can` 里
  - `takeout_tray` 在 `trash_can` 里
  - `leftovers` 在 `breakfast_fridge/inside_shelf` 上
  - `breakfast_fridge` 关着
  - `clutter_cereal_a`、`clutter_cereal_b` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `rubbish_mug`：
  - `soda_can` 在 `trash_can` 里
  - `takeout_tray` 在 `trash_can` 里
  - `used_mug` 在 `kitchen_counter_2/top` 上
  - `used_mug` 立着
  - `clutter_cereal_a`、`clutter_cereal_b` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `leftovers_mug`：
  - `soda_can` 在 `trash_can` 里
  - `leftovers` 在 `breakfast_fridge/inside_shelf` 上
  - `breakfast_fridge` 关着
  - `used_mug` 在 `kitchen_counter_2/top` 上
  - `used_mug` 立着
  - `clutter_cereal_a`、`clutter_cereal_b` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着

**参考调用顺序**：

- 摆法 `rubbish_leftovers`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=soda_can)` → 3. `pick(object=soda_can)` → 4. `lift(object=soda_can, height_m=0.95)` → 5. `navigate(destination=trash_can)` → 6. `hover(object=soda_can, target=trash_can)` → 7. `drop(object=soda_can, container=trash_can)` → 8. `navigate(destination=takeout_tray)` → 9. `pick(object=takeout_tray)` → 10. `lift(object=takeout_tray, height_m=0.95)` → 11. `navigate(destination=trash_can)` → 12. `drop(object=takeout_tray, container=trash_can)` → 13. `navigate(destination=breakfast_fridge)` → 14. `open(articulated=breakfast_fridge)` → 15. `navigate(destination=leftovers)` → 16. `pick(object=leftovers)` → 17. `navigate(destination=breakfast_fridge)` → 18. `place(object=leftovers, receptacle=breakfast_fridge/inside_shelf)` → 19. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 20. `close(articulated=breakfast_fridge)`
- 摆法 `leftovers_mug`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=soda_can)` → 3. `pick(object=soda_can)` → 4. `lift(object=soda_can, height_m=0.95)` → 5. `navigate(destination=trash_can)` → 6. `hover(object=soda_can, target=trash_can)` → 7. `drop(object=soda_can, container=trash_can)` → 8. `navigate(destination=breakfast_fridge)` → 9. `open(articulated=breakfast_fridge)` → 10. `navigate(destination=leftovers)` → 11. `pick(object=leftovers)` → 12. `navigate(destination=breakfast_fridge)` → 13. `place(object=leftovers, receptacle=breakfast_fridge/inside_shelf)` → 14. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 15. `close(articulated=breakfast_fridge)` → 16. `navigate(destination=used_mug)` → 17. `pick(object=used_mug)` → 18. `navigate(destination=kitchen_counter_2/top)` → 19. `place(object=used_mug, receptacle=kitchen_counter_2/top)`
- 摆法 `rubbish_mug`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=soda_can)` → 3. `pick(object=soda_can)` → 4. `lift(object=soda_can, height_m=0.95)` → 5. `navigate(destination=trash_can)` → 6. `hover(object=soda_can, target=trash_can)` → 7. `drop(object=soda_can, container=trash_can)` → 8. `navigate(destination=takeout_tray)` → 9. `pick(object=takeout_tray)` → 10. `lift(object=takeout_tray, height_m=0.95)` → 11. `navigate(destination=trash_can)` → 12. `drop(object=takeout_tray, container=trash_can)` → 13. `navigate(destination=used_mug)` → 14. `pick(object=used_mug)` → 15. `navigate(destination=kitchen_counter_2/top)` → 16. `place(object=used_mug, receptacle=kitchen_counter_2/top)`

### guests_coming（Task）

**情况**：客人快到了，客厅里散着空罐、用过的马克杯（电视柜上）、孩子的积木（地上）中的两三样；岛台上的擀面杖和海绵本来就该在那 → 找出客厅里乱放的东西，各送回该去的地方（垃圾桶、厨房台面、玩具箱），属于那里的东西不动

**指令**：客人十分钟后到，把客厅收拾得能见人：乱放的东西各回各处，垃圾扔进垃圾桶，用过的杯子拿回厨房台面，孩子的玩具收进玩具箱。本来就该在那儿的东西别动。

**成功条件**：

- 摆法 `can_block`：
  - `soda_can` 在 `trash_can` 里
  - `wooden_block_a` 在 `toy_box` 里
  - `rolling_pin`、`kitchen_sponge` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `can_mug_block`：
  - `soda_can` 在 `trash_can` 里
  - `used_mug` 在 `kitchen_counter_2/top` 上
  - `used_mug` 立着
  - `wooden_block_a` 在 `toy_box` 里
  - `rolling_pin`、`kitchen_sponge` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `can_mug`：
  - `soda_can` 在 `trash_can` 里
  - `used_mug` 在 `kitchen_counter_2/top` 上
  - `used_mug` 立着
  - `rolling_pin`、`kitchen_sponge` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着

**参考调用顺序**：

- 摆法 `can_mug_block`：1. `look(target=kitchen_island/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=soda_can)` → 4. `pick(object=soda_can)` → 5. `lift(object=soda_can, height_m=0.95)` → 6. `navigate(destination=trash_can)` → 7. `hover(object=soda_can, target=trash_can)` → 8. `drop(object=soda_can, container=trash_can)` → 9. `navigate(destination=used_mug)` → 10. `pick(object=used_mug)` → 11. `navigate(destination=kitchen_counter_2/top)` → 12. `place(object=used_mug, receptacle=kitchen_counter_2/top)` → 13. `navigate(destination=wooden_block_a)` → 14. `pick(object=wooden_block_a)` → 15. `navigate(destination=toy_box)` → 16. `place(object=wooden_block_a, receptacle=toy_box)`
- 摆法 `can_block`：1. `look(target=kitchen_island/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=soda_can)` → 4. `pick(object=soda_can)` → 5. `lift(object=soda_can, height_m=0.95)` → 6. `navigate(destination=trash_can)` → 7. `hover(object=soda_can, target=trash_can)` → 8. `drop(object=soda_can, container=trash_can)` → 9. `navigate(destination=wooden_block_a)` → 10. `pick(object=wooden_block_a)` → 11. `navigate(destination=toy_box)` → 12. `place(object=wooden_block_a, receptacle=toy_box)`
- 摆法 `can_mug`：1. `look(target=kitchen_island/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=soda_can)` → 4. `pick(object=soda_can)` → 5. `lift(object=soda_can, height_m=0.95)` → 6. `navigate(destination=trash_can)` → 7. `hover(object=soda_can, target=trash_can)` → 8. `drop(object=soda_can, container=trash_can)` → 9. `navigate(destination=used_mug)` → 10. `pick(object=used_mug)` → 11. `navigate(destination=kitchen_counter_2/top)` → 12. `place(object=used_mug, receptacle=kitchen_counter_2/top)`

### x6_gd_can_put_away（Task）

**情况**：罐子被收进了关着门的微波炉或靠墙柜 → 逐个打开找

**指令**：有人没把空易拉罐扔掉，而是收进了微波炉或者靠墙矮柜里。把它扔进垃圾桶，打开的门都关好。

**成功条件**：

- `soda_can` 在 `trash_can` 里
- 手里空着
- `kitchen_microwave` 关着
- `kitchen_cabinet_6` 关着

**参考调用顺序**：

- 摆法 `in_cabinet`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_microwave/inside_floor)` → 4. `close(articulated=kitchen_microwave)` → 5. `navigate(destination=kitchen_cabinet_6)` → 6. `open(articulated=kitchen_cabinet_6)` → 7. `bend()` → 8. `explore_furniture(furniture=kitchen_cabinet_6)` → 9. `straighten()` → 10. `navigate(destination=soda_can)` → 11. `pick(object=soda_can)` → 12. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 13. `close(articulated=kitchen_cabinet_6)` → 14. `navigate(destination=trash_can)` → 15. `drop(object=soda_can, container=trash_can)`
- 摆法 `in_microwave`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_microwave)` → 8. `open(articulated=kitchen_microwave)` → 9. `look(target=kitchen_microwave/inside_floor)` → 10. `navigate(destination=soda_can)` → 11. `pick(object=soda_can)` → 12. `retreat(obstacle=kitchen_microwave, distance_m=0.3)` → 13. `close(articulated=kitchen_microwave)` → 14. `navigate(destination=trash_can)` → 15. `drop(object=soda_can, container=trash_can)`

---

## T11_collect_fruits

> 午饭吃完了，苹果还在餐桌上，把它收起来。

### fruits_on_table（对照）

**情况**：苹果在餐桌，果篮在卧室书架 → 想到水果收在果篮里，放进去

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `apple` 在 `fruit_basket` 里
  - 第 2 组：
    - `apple` 在 `serving_tray` 里

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=apple)` → 4. `pick(object=apple)` → 5. `navigate(destination=bookcase_2/top)` → 6. `look(target=bookcase_2/top)` → 7. `place(object=apple, receptacle=fruit_basket)`

### basket_missing（Task）

**情况**：书架上没有果篮 → 自己找另一个能装水果的东西：书房书桌上的托盘

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `apple` 在 `fruit_basket` 里
  - 第 2 组：
    - `apple` 在 `serving_tray` 里

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=apple)` → 4. `pick(object=apple)` → 5. `navigate(destination=bookcase_2/top)` → 6. `look(target=bookcase_2/top)` → 7. `place(object=apple, receptacle=fruit_basket)` → 8. `navigate(destination=desk_1/top)`（换做法） → 9. `look(target=desk_1/top)`（换做法） → 10. `navigate(destination=serving_tray)`（换做法） → 11. `place(object=apple, receptacle=serving_tray)`（换做法）

### basket_gone_bowl_there（Task）

**情况**：果篮不在，原位置放着一个用过的早餐碗 → 认出那不是放水果的，去找托盘

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `apple` 在 `fruit_basket` 里
  - 第 2 组：
    - `apple` 在 `serving_tray` 里

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=apple)` → 4. `pick(object=apple)` → 5. `navigate(destination=bookcase_2/top)` → 6. `look(target=bookcase_2/top)` → 7. `identify(object=bowl_kitchen_cabinet)`（补救） → 8. `navigate(destination=desk_1/top)`（换做法） → 9. `look(target=desk_1/top)`（换做法） → 10. `navigate(destination=serving_tray)`（换做法） → 11. `place(object=apple, receptacle=serving_tray)`（换做法）

### leave_one_for_kid（Task）

**情况**：指令只说“桌上的水果收起来，给书房写作业的孩子留一个当点心，孩子不爱吃橙子” → 拆成两个子目标：一个不是橙子的水果放到书房书桌，其余放进卧室书架上的果篮（指令没说果篮在哪）

**指令**：午饭吃完了，把桌上的水果收起来，给在书房写作业的孩子留一个当点心。孩子不爱吃橙子。

**成功条件**：

- 摆法 `all_three`：
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `apple` 在 `desk_1/top` 上
      - `lunch_orange` 在 `fruit_basket` 里
      - `lunch_banana` 在 `fruit_basket` 里
    - 第 2 组：
      - `lunch_banana` 在 `desk_1/top` 上
      - `apple` 在 `fruit_basket` 里
      - `lunch_orange` 在 `fruit_basket` 里
- 摆法 `apple_orange`：
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `apple` 在 `desk_1/top` 上
      - `lunch_orange` 在 `fruit_basket` 里
- 摆法 `orange_banana`：
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `lunch_banana` 在 `desk_1/top` 上
      - `lunch_orange` 在 `fruit_basket` 里

**参考调用顺序**：

- 摆法 `apple_orange`：1. `look(target=dining_table_2/top)` → 2. `search(object=fruit_basket, region=bedroom_0_1)` → 3. `navigate(destination=apple)` → 4. `pick(object=apple)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=apple, receptacle=desk_1/top, hint_xy=[-0.9, -6.0])` → 7. `navigate(destination=lunch_orange)` → 8. `pick(object=lunch_orange)` → 9. `navigate(destination=bookcase_2/top)` → 10. `place(object=lunch_orange, receptacle=fruit_basket)`
- 摆法 `orange_banana`：1. `look(target=dining_table_2/top)` → 2. `search(object=fruit_basket, region=bedroom_0_1)` → 3. `navigate(destination=lunch_banana)` → 4. `pick(object=lunch_banana)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=lunch_banana, receptacle=desk_1/top, hint_xy=[-0.9, -6.0])` → 7. `navigate(destination=lunch_orange)` → 8. `pick(object=lunch_orange)` → 9. `navigate(destination=bookcase_2/top)` → 10. `place(object=lunch_orange, receptacle=fruit_basket)`
- 摆法 `all_three`：1. `look(target=dining_table_2/top)` → 2. `search(object=fruit_basket, region=bedroom_0_1)` → 3. `navigate(destination=apple)` → 4. `pick(object=apple)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=apple, receptacle=desk_1/top, hint_xy=[-0.9, -6.0])` → 7. `navigate(destination=lunch_orange)` → 8. `pick(object=lunch_orange)` → 9. `navigate(destination=bookcase_2/top)` → 10. `place(object=lunch_orange, receptacle=fruit_basket)` → 11. `navigate(destination=lunch_banana)` → 12. `pick(object=lunch_banana)` → 13. `navigate(destination=bookcase_2/top)` → 14. `place(object=lunch_banana, receptacle=fruit_basket)`

### fruit_plate_for_guests（Task）

**情况**：指令只说“客人在客厅看电视，用托盘端点水果过去”，没说托盘在哪 → 找到托盘，先把空托盘放到电视柜，再把苹果和橙子一个个放上去（一只手端装满的托盘容易掉，子目标顺序决定能不能做成）

**指令**：客人在客厅看电视，用托盘给他们端点水果过去。

**成功条件**：

- `apple` 在 `fruit_tray` 里
- `lunch_orange` 在 `fruit_tray` 里
- `apple` 不在地上
- `lunch_orange` 不在地上
- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `fruit_tray` 在 `tv_stand_2/top` 上
  - 第 2 组：
    - `fruit_tray` 在 `tv_stand_1/top` 上

**参考调用顺序**：

- 摆法 `tray_in_study`：1. `look(target=dining_table_2/top)` → 2. `search(object=fruit_tray, region=living_room_0_1)` → 3. `navigate(destination=fruit_tray)` → 4. `pick(object=fruit_tray)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=fruit_tray, receptacle=tv_stand_2/top, hint_xy=[7.5, 0.36])` → 7. `navigate(destination=apple)` → 8. `pick(object=apple)` → 9. `navigate(destination=fruit_tray)` → 10. `place(object=apple, receptacle=fruit_tray)` → 11. `navigate(destination=lunch_orange)` → 12. `pick(object=lunch_orange)` → 13. `navigate(destination=fruit_tray)` → 14. `place(object=lunch_orange, receptacle=fruit_tray)`
- 摆法 `tray_by_table`：1. `look(target=dining_table_2/top)` → 2. `search(object=fruit_tray, region=dining_room_0_1)` → 3. `navigate(destination=fruit_tray)` → 4. `pick(object=fruit_tray)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=fruit_tray, receptacle=tv_stand_2/top, hint_xy=[7.5, 0.36])` → 7. `navigate(destination=apple)` → 8. `pick(object=apple)` → 9. `navigate(destination=fruit_tray)` → 10. `place(object=apple, receptacle=fruit_tray)` → 11. `navigate(destination=lunch_orange)` → 12. `pick(object=lunch_orange)` → 13. `navigate(destination=fruit_tray)` → 14. `place(object=lunch_orange, receptacle=fruit_tray)`

---

## T12_tidy_toys

> 快到睡觉时间了，把孩子的玩具收起来。

### toys_out（对照）

**情况**：小车在客厅地上，鸭子在电视柜 → 都放进卧室的储物筐

**成功条件**：

- `toy_car` 在 `storage_basket` 里
- `rubber_duck` 在 `storage_basket` 里
- `storage_basket` 立着
- 手里空着

**参考调用顺序**：

1. `explore_room(room=bedroom_0_1)` → 2. `explore_room(room=living_room_0_0)` → 3. `navigate(destination=toy_car)` → 4. `pick(object=toy_car)` → 5. `navigate(destination=storage_basket)` → 6. `place(object=toy_car, receptacle=storage_basket)` → 7. `navigate(destination=rubber_duck)` → 8. `pick(object=rubber_duck)` → 9. `navigate(destination=storage_basket)` → 10. `place(object=rubber_duck, receptacle=storage_basket)` → 11. `nod()`（补救）

### duck_in_study（Task）

**情况**：鸭子落在别处，开局看不到 → 找鸭子

**成功条件**：

- `toy_car` 在 `storage_basket` 里
- `rubber_duck` 在 `storage_basket` 里
- `storage_basket` 立着
- 手里空着

**参考调用顺序**：

- 摆法 `duck_in_study`：1. `explore_room(room=bedroom_0_1)` → 2. `explore_room(room=living_room_0_0)` → 3. `navigate(destination=toy_car)` → 4. `pick(object=toy_car)` → 5. `navigate(destination=storage_basket)` → 6. `place(object=toy_car, receptacle=storage_basket)` → 7. `navigate(destination=rubber_duck)` → 8. `search(object=rubber_duck, region=living_room_0_1)` → 9. `navigate(destination=rubber_duck)` → 10. `pick(object=rubber_duck)` → 11. `navigate(destination=storage_basket)` → 12. `place(object=rubber_duck, receptacle=storage_basket)`
- 摆法 `alt_dining_table_2`：1. `explore_room(room=bedroom_0_1)` → 2. `explore_room(room=living_room_0_0)` → 3. `navigate(destination=toy_car)` → 4. `pick(object=toy_car)` → 5. `navigate(destination=storage_basket)` → 6. `place(object=toy_car, receptacle=storage_basket)` → 7. `navigate(destination=rubber_duck)` → 8. `search(object=rubber_duck, region=dining_room_0_1)` → 9. `navigate(destination=rubber_duck)` → 10. `pick(object=rubber_duck)` → 11. `navigate(destination=storage_basket)` → 12. `place(object=rubber_duck, receptacle=storage_basket)`

### toys_everywhere（Task）

**情况**：没有储物筐，只有一个半满的小箱和一个浅托盘；鸭子也不在原处 → 量尺寸分配，并找鸭子

**成功条件**：

- `stored_block_1` 完全在 `toy_bin_small` 里（没有露出边沿）
- `stored_block_2` 完全在 `toy_bin_small` 里（没有露出边沿）
- `stored_block_3` 完全在 `toy_bin_small` 里（没有露出边沿）
- `stored_block_4` 完全在 `toy_bin_small` 里（没有露出边沿）
- `stored_block_5` 完全在 `toy_bin_small` 里（没有露出边沿）
- `stored_block_6` 完全在 `toy_bin_small` 里（没有露出边沿）
- `toy_bin_small` 立着
- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `toy_car` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `rubber_duck` 完全在 `toy_bin_small` 里（没有露出边沿）
  - 第 2 组：
    - `toy_car` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `rubber_duck` 完全在 `toy_tray` 里（没有露出边沿）
  - 第 3 组：
    - `toy_car` 完全在 `toy_tray` 里（没有露出边沿）
    - `rubber_duck` 完全在 `toy_bin_small` 里（没有露出边沿）
  - 第 4 组：
    - `toy_car` 完全在 `toy_tray` 里（没有露出边沿）
    - `rubber_duck` 完全在 `toy_tray` 里（没有露出边沿）

**参考调用顺序**：

- 摆法 `toys_everywhere`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `measure(object=toy_tray)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_car)` → 7. `pick(object=toy_car)` → 8. `navigate(destination=toy_tray)` → 9. `place(object=toy_car, receptacle=toy_tray)` → 10. `search(object=rubber_duck, region=living_room_0_1)` → 11. `navigate(destination=rubber_duck)` → 12. `pick(object=rubber_duck)` → 13. `navigate(destination=toy_bin_small)` → 14. `drop(object=rubber_duck, container=toy_bin_small)`
- 摆法 `alt_dining_table_2`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `measure(object=toy_tray)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_car)` → 7. `pick(object=toy_car)` → 8. `navigate(destination=toy_tray)` → 9. `place(object=toy_car, receptacle=toy_tray)` → 10. `search(object=rubber_duck, region=dining_room_0_1)` → 11. `navigate(destination=rubber_duck)` → 12. `pick(object=rubber_duck)` → 13. `navigate(destination=toy_bin_small)` → 14. `drop(object=rubber_duck, container=toy_bin_small)`

### bins_capacity（Task）

**情况**：没有储物筐，书架上两个小箱，其中一个已经装了半箱积木 → 看哪个还装得下什么：鸭子塞进半满那个的空隙，小车放空的那个

**成功条件**：

- 摆法 `left_full`：
  - `stored_block_1` 完全在 `toy_bin_small` 里（没有露出边沿）
  - `stored_block_2` 完全在 `toy_bin_small` 里（没有露出边沿）
  - `stored_block_3` 完全在 `toy_bin_small` 里（没有露出边沿）
  - `stored_block_4` 完全在 `toy_bin_small` 里（没有露出边沿）
  - `stored_block_5` 完全在 `toy_bin_small` 里（没有露出边沿）
  - `stored_block_6` 完全在 `toy_bin_small` 里（没有露出边沿）
  - `toy_car` 完全在 `toy_bin_small_2` 里（没有露出边沿）
  - `rubber_duck` 完全在 `toy_bin_small` 里（没有露出边沿）
  - `toy_bin_small`、`toy_bin_small_2` 立着
  - 手里空着
- 摆法 `right_full`：
  - `stored_block_1` 完全在 `toy_bin_small_2` 里（没有露出边沿）
  - `stored_block_2` 完全在 `toy_bin_small_2` 里（没有露出边沿）
  - `stored_block_3` 完全在 `toy_bin_small_2` 里（没有露出边沿）
  - `stored_block_4` 完全在 `toy_bin_small_2` 里（没有露出边沿）
  - `stored_block_5` 完全在 `toy_bin_small_2` 里（没有露出边沿）
  - `stored_block_6` 完全在 `toy_bin_small_2` 里（没有露出边沿）
  - `toy_car` 完全在 `toy_bin_small` 里（没有露出边沿）
  - `rubber_duck` 完全在 `toy_bin_small_2` 里（没有露出边沿）
  - `toy_bin_small_2`、`toy_bin_small` 立着
  - 手里空着

**参考调用顺序**：

- 摆法 `left_full`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `measure(object=toy_bin_small_2)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_car)` → 7. `pick(object=toy_car)` → 8. `navigate(destination=toy_bin_small_2)` → 9. `place(object=toy_car, receptacle=toy_bin_small_2)` → 10. `search(object=rubber_duck, region=living_room_0_1)` → 11. `navigate(destination=rubber_duck)` → 12. `pick(object=rubber_duck)` → 13. `navigate(destination=toy_bin_small)` → 14. `drop(object=rubber_duck, container=toy_bin_small)`
- 摆法 `right_full`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `measure(object=toy_bin_small_2)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_car)` → 7. `pick(object=toy_car)` → 8. `navigate(destination=toy_bin_small)` → 9. `place(object=toy_car, receptacle=toy_bin_small)` → 10. `search(object=rubber_duck, region=living_room_0_1)` → 11. `navigate(destination=rubber_duck)` → 12. `pick(object=rubber_duck)` → 13. `navigate(destination=toy_bin_small_2)` → 14. `drop(object=rubber_duck, container=toy_bin_small_2)`

### find_all_toys（Task）

**情况**：玩具散在好几个房间，指令没说有几个；餐桌上有块黄海绵像积木但不是玩具 → 把各房间找遍，认出哪些是玩具，全放进筐，海绵别动（找到一两个就停算失败）

**成功条件**：

- 摆法 `all_four`：
  - `toy_car` 在 `storage_basket` 里
  - `rubber_duck` 在 `storage_basket` 里
  - `teddy_bear` 在 `storage_basket` 里
  - `stray_block` 在 `storage_basket` 里
  - `kitchen_sponge` 没被挪动（离开局位置不超过 3 cm）
  - `storage_basket` 立着
  - 手里空着
- 摆法 `car_duck_bear`：
  - `toy_car` 在 `storage_basket` 里
  - `rubber_duck` 在 `storage_basket` 里
  - `teddy_bear` 在 `storage_basket` 里
  - `kitchen_sponge` 没被挪动（离开局位置不超过 3 cm）
  - `storage_basket` 立着
  - 手里空着
- 摆法 `car_duck`：
  - `toy_car` 在 `storage_basket` 里
  - `rubber_duck` 在 `storage_basket` 里
  - `kitchen_sponge` 没被挪动（离开局位置不超过 3 cm）
  - `storage_basket` 立着
  - 手里空着

**参考调用顺序**：

- 摆法 `car_duck`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `pick(object=toy_car)` → 4. `navigate(destination=storage_basket)` → 5. `place(object=toy_car, receptacle=storage_basket)` → 6. `search(object=rubber_duck, region=living_room_0_1)` → 7. `navigate(destination=rubber_duck)` → 8. `pick(object=rubber_duck)` → 9. `navigate(destination=storage_basket)` → 10. `place(object=rubber_duck, receptacle=storage_basket)`
- 摆法 `car_duck_bear`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `pick(object=toy_car)` → 4. `navigate(destination=storage_basket)` → 5. `place(object=toy_car, receptacle=storage_basket)` → 6. `search(object=rubber_duck, region=bathroom_0_1)` → 7. `navigate(destination=rubber_duck)` → 8. `pick(object=rubber_duck)` → 9. `navigate(destination=storage_basket)` → 10. `place(object=rubber_duck, receptacle=storage_basket)` → 11. `search(object=teddy_bear, region=dining_room_0_1)` → 12. `navigate(destination=teddy_bear)` → 13. `pick(object=teddy_bear)` → 14. `navigate(destination=storage_basket)` → 15. `place(object=teddy_bear, receptacle=storage_basket)`
- 摆法 `all_four`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `pick(object=toy_car)` → 4. `navigate(destination=storage_basket)` → 5. `place(object=toy_car, receptacle=storage_basket)` → 6. `search(object=rubber_duck, region=living_room_0_1)` → 7. `navigate(destination=rubber_duck)` → 8. `pick(object=rubber_duck)` → 9. `navigate(destination=storage_basket)` → 10. `place(object=rubber_duck, receptacle=storage_basket)` → 11. `search(object=teddy_bear, region=dining_room_0_1)` → 12. `navigate(destination=teddy_bear)` → 13. `pick(object=teddy_bear)` → 14. `navigate(destination=storage_basket)` → 15. `place(object=teddy_bear, receptacle=storage_basket)` → 16. `search(object=stray_block, region=living_room_0_0)` → 17. `navigate(destination=stray_block)` → 18. `pick(object=stray_block)` → 19. `navigate(destination=storage_basket)` → 20. `place(object=stray_block, receptacle=storage_basket)`

### castle_stays（Task）

**情况**：“他搭的积木城堡别拆”：客厅地上一座积木塔，旁边散着同样的积木 → 叠在塔里的不动，散着的积木和小车、鸭子收进筐。检测的是：整局没拿起过塔上的积木（过程要求），结束时每块都在原位、叠放关系还在（终态）。中途被碰倒的话，不拿起来就搭不回去，终态会判失败；碰歪了又恰好推回原位这种情况检测不到

**指令**：快到睡觉时间了，把孩子的玩具收起来。他搭的积木城堡别拆，明天还要接着搭。

**成功条件**：

- 摆法 `tall_two_loose`：
  - `toy_car` 在 `storage_basket` 里
  - `rubber_duck` 在 `storage_basket` 里
  - `loose_block_1` 在 `storage_basket` 里
  - `loose_block_2` 在 `storage_basket` 里
  - `castle_block_1`、`castle_block_2`、`castle_block_3` 没被挪动（离开局位置不超过 3 cm）
  - 过程要求：整局都没拿起过 `castle_block_1`、`castle_block_2`、`castle_block_3`（拆了再搭回去不算）
  - `castle_block_2` 叠在 `castle_block_1` 上
  - `castle_block_3` 叠在 `castle_block_2` 上
  - `storage_basket` 立着
  - 手里空着
- 摆法 `short_one_loose`：
  - `toy_car` 在 `storage_basket` 里
  - `rubber_duck` 在 `storage_basket` 里
  - `loose_block_1` 在 `storage_basket` 里
  - `castle_block_1`、`castle_block_2` 没被挪动（离开局位置不超过 3 cm）
  - 过程要求：整局都没拿起过 `castle_block_1`、`castle_block_2`（拆了再搭回去不算）
  - `castle_block_2` 叠在 `castle_block_1` 上
  - `storage_basket` 立着
  - 手里空着
- 摆法 `tall_none_loose`：
  - `toy_car` 在 `storage_basket` 里
  - `rubber_duck` 在 `storage_basket` 里
  - `castle_block_1`、`castle_block_2`、`castle_block_3` 没被挪动（离开局位置不超过 3 cm）
  - 过程要求：整局都没拿起过 `castle_block_1`、`castle_block_2`、`castle_block_3`（拆了再搭回去不算）
  - `castle_block_2` 叠在 `castle_block_1` 上
  - `castle_block_3` 叠在 `castle_block_2` 上
  - `storage_basket` 立着
  - 手里空着

**参考调用顺序**：

- 摆法 `tall_two_loose`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `pick(object=toy_car)` → 4. `navigate(destination=storage_basket)` → 5. `place(object=toy_car, receptacle=storage_basket)` → 6. `navigate(destination=rubber_duck)` → 7. `pick(object=rubber_duck)` → 8. `navigate(destination=storage_basket)` → 9. `place(object=rubber_duck, receptacle=storage_basket)` → 10. `navigate(destination=loose_block_1)` → 11. `pick(object=loose_block_1)` → 12. `navigate(destination=storage_basket)` → 13. `place(object=loose_block_1, receptacle=storage_basket)` → 14. `navigate(destination=loose_block_2)` → 15. `pick(object=loose_block_2)` → 16. `navigate(destination=storage_basket)` → 17. `place(object=loose_block_2, receptacle=storage_basket)`
- 摆法 `short_one_loose`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `pick(object=toy_car)` → 4. `navigate(destination=storage_basket)` → 5. `place(object=toy_car, receptacle=storage_basket)` → 6. `navigate(destination=rubber_duck)` → 7. `pick(object=rubber_duck)` → 8. `navigate(destination=storage_basket)` → 9. `place(object=rubber_duck, receptacle=storage_basket)` → 10. `navigate(destination=loose_block_1)` → 11. `pick(object=loose_block_1)` → 12. `navigate(destination=storage_basket)` → 13. `place(object=loose_block_1, receptacle=storage_basket)`
- 摆法 `tall_none_loose`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `pick(object=toy_car)` → 4. `navigate(destination=storage_basket)` → 5. `place(object=toy_car, receptacle=storage_basket)` → 6. `navigate(destination=rubber_duck)` → 7. `pick(object=rubber_duck)` → 8. `navigate(destination=storage_basket)` → 9. `place(object=rubber_duck, receptacle=storage_basket)`

---

## T13_breakfast_setup

> 快吃早饭了，把餐桌上的位子摆好。

### dishes_on_tv_stand（对照）

**情况**：碗和杯子在电视柜，勺子在餐桌 → 摆到勺子旁

**成功条件**：

- `bowl` 在 `dining_table_2/top` 上
- `bowl` 立着
- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `cup` 在 `dining_table_2/top` 上
    - `cup` 立着
    - bowl、cup、spoon 在 `dining_table_2/top` 上摆在一起（彼此不超过 50 cm）
  - 第 2 组：
    - `mug` 在 `dining_table_2/top` 上
    - `mug` 立着
    - bowl、mug、spoon 在 `dining_table_2/top` 上摆在一起（彼此不超过 50 cm）

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=bowl)` → 5. `pick(object=bowl)` → 6. `navigate(destination=dining_table_2/top)` → 7. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.05, 7.1])` → 8. `navigate(destination=cup)` → 9. `pick(object=cup)` → 10. `navigate(destination=dining_table_2/top)` → 11. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[3.2, 7.4])`

### no_cup（Task）

**情况**：没杯子 → 用卧室书架上的马克杯

**成功条件**：

- `bowl` 在 `dining_table_2/top` 上
- `bowl` 立着
- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `cup` 在 `dining_table_2/top` 上
    - `cup` 立着
    - bowl、cup、spoon 在 `dining_table_2/top` 上摆在一起（彼此不超过 50 cm）
  - 第 2 组：
    - `mug` 在 `dining_table_2/top` 上
    - `mug` 立着
    - bowl、mug、spoon 在 `dining_table_2/top` 上摆在一起（彼此不超过 50 cm）

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=bowl)` → 5. `pick(object=bowl)` → 6. `navigate(destination=dining_table_2/top)` → 7. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.05, 7.1])` → 8. `navigate(destination=cup)` → 9. `navigate(destination=bookcase_2/top)`（换做法） → 10. `look(target=bookcase_2/top)`（换做法） → 11. `pick(object=mug)`（换做法） → 12. `navigate(destination=dining_table_2/top)` → 13. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[3.2, 7.4])`

### copy_the_setting（Task）

**情况**：“照着桌上摆好的那份，在另一把勺子那里也摆一份”：对面已经摆好一份 → 看懂有哪些东西、各在勺子的什么位置（叠没叠），在另一把勺子那儿照样摆；对面坐的人方向相反，左右要按坐的人来算；家里缺的那种用最接近的代替，放在同一个位置

**指令**：照着桌上摆好的那份，在另一把勺子那里也摆一份。

**成功条件**：

- 摆法 `bowl_cup`：
  - `bowl`、`cup` 相对 spoon 的摆法（按坐在那里的人的前后左右）和 `example_bowl`、`example_cup` 相对 example_spoon 的一样，误差不超过 7 cm
  - `example_bowl`、`example_cup`、`example_spoon` 没被挪动（离开局位置不超过 3 cm）
  - `bowl`、`cup` 立着
  - 手里空着
- 摆法 `no_cup`：
  - `bowl`、`mug` 相对 spoon 的摆法（按坐在那里的人的前后左右）和 `example_bowl`、`example_cup` 相对 example_spoon 的一样，误差不超过 7 cm
  - `example_bowl`、`example_cup`、`example_spoon` 没被挪动（离开局位置不超过 3 cm）
  - `bowl`、`mug` 立着
  - 手里空着
- 摆法 `plate_bowl_mug_left`：
  - `plate_counter_a`、`bowl`、`mug` 相对 spoon 的摆法（按坐在那里的人的前后左右）和 `example_plate`、`example_bowl`、`example_mug` 相对 example_spoon 的一样，误差不超过 7 cm
  - `example_plate`、`example_bowl`、`example_mug`、`example_spoon` 没被挪动（离开局位置不超过 3 cm）
  - `bowl`、`mug` 立着
  - `bowl` 叠在 `plate_counter_a` 上
  - 手里空着

**参考调用顺序**：

- 摆法 `bowl_cup`：1. `look(target=dining_table_2/top)` → 2. `measure(object=example_spoon)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=bowl)` → 6. `pick(object=bowl)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.93, 7.49])` → 9. `navigate(destination=cup)` → 10. `pick(object=cup)` → 11. `navigate(destination=dining_table_2/top)` → 12. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[3.1, 7.3])`
- 摆法 `plate_bowl_mug_left`：1. `look(target=dining_table_2/top)` → 2. `measure(object=example_spoon)` → 3. `navigate(destination=kitchen_counter_2/top)` → 4. `look(target=kitchen_counter_2/top)` → 5. `navigate(destination=plate_counter_a)` → 6. `pick(object=plate_counter_a)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=plate_counter_a, receptacle=dining_table_2/top, hint_xy=[2.93, 7.49])` → 9. `navigate(destination=tv_stand_2/top)` → 10. `look(target=tv_stand_2/top)` → 11. `navigate(destination=bowl)` → 12. `pick(object=bowl)` → 13. `navigate(destination=dining_table_2/top)` → 14. `stack(object=bowl, base=plate_counter_a)` → 15. `navigate(destination=bookcase_2/top)` → 16. `look(target=bookcase_2/top)` → 17. `navigate(destination=mug)` → 18. `pick(object=mug)` → 19. `navigate(destination=dining_table_2/top)` → 20. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[3.1, 7.66])`
- 摆法 `no_cup`：1. `look(target=dining_table_2/top)` → 2. `measure(object=example_spoon)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=bowl)` → 6. `pick(object=bowl)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.93, 7.49])` → 9. `navigate(destination=bookcase_2/top)` → 10. `look(target=bookcase_2/top)` → 11. `navigate(destination=mug)` → 12. `pick(object=mug)` → 13. `navigate(destination=dining_table_2/top)` → 14. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[3.1, 7.3])`

### finish_the_table（Task）

**情况**：“把桌上剩下的位子也摆好”：已摆好的三份里大人是碗+马克杯，孩子是碗+塑料杯、旁边放着玩具 → 归纳出两条规律，看空位旁边有没有玩具车判断是谁的位子，按对应规律摆

**指令**：把桌上剩下的位子也摆好。

**成功条件**：

- 摆法 `kid_seat`：
  - `w_mid_spoon` 离其中至少一个不超过 12 cm：`bowl`、`bowl_2`
  - `w_mid_spoon` 离其中至少一个不超过 12 cm：`kid_cup`
  - `w_mid_spoon` 离这些都超过 25 cm：`mug`、`mug_2`
  - `e_north_spoon`、`e_north_bowl`、`e_north_drink`、`e_mid_spoon`、`e_mid_bowl`、`e_mid_drink`、`e_mid_toy`、`w_north_spoon`、`w_north_bowl`、`w_north_drink` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `adult_and_kid`：
  - `w_mid_spoon` 离其中至少一个不超过 12 cm：`bowl`、`bowl_2`
  - `w_mid_spoon` 离其中至少一个不超过 12 cm：`mug`、`mug_2`
  - `w_mid_spoon` 离这些都超过 25 cm：`kid_cup`
  - `w_south_spoon` 离其中至少一个不超过 12 cm：`bowl`、`bowl_2`
  - `w_south_spoon` 离其中至少一个不超过 12 cm：`kid_cup`
  - `w_south_spoon` 离这些都超过 25 cm：`mug_2`
  - `e_north_spoon`、`e_north_bowl`、`e_north_drink`、`e_mid_spoon`、`e_mid_bowl`、`e_mid_drink`、`e_mid_toy`、`w_north_spoon`、`w_north_bowl`、`w_north_drink` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `adult_seat`：
  - `w_mid_spoon` 离其中至少一个不超过 12 cm：`bowl`、`bowl_2`
  - `w_mid_spoon` 离其中至少一个不超过 12 cm：`mug`、`mug_2`
  - `w_mid_spoon` 离这些都超过 25 cm：`kid_cup`
  - `e_north_spoon`、`e_north_bowl`、`e_north_drink`、`e_mid_spoon`、`e_mid_bowl`、`e_mid_drink`、`e_mid_toy`、`w_north_spoon`、`w_north_bowl`、`w_north_drink` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着

**参考调用顺序**：

- 摆法 `adult_seat`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=bowl)` → 5. `pick(object=bowl)` → 6. `navigate(destination=dining_table_2/top)` → 7. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.93, 6.89])` → 8. `navigate(destination=bookcase_2/top)` → 9. `look(target=bookcase_2/top)` → 10. `navigate(destination=mug)` → 11. `pick(object=mug)` → 12. `navigate(destination=dining_table_2/top)` → 13. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[3.1, 6.7])`
- 摆法 `kid_seat`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=bowl)` → 5. `pick(object=bowl)` → 6. `navigate(destination=dining_table_2/top)` → 7. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.93, 6.89])` → 8. `navigate(destination=kitchen_counter_2/top)` → 9. `look(target=kitchen_counter_2/top)` → 10. `navigate(destination=kid_cup)` → 11. `pick(object=kid_cup)` → 12. `navigate(destination=dining_table_2/top)` → 13. `place(object=kid_cup, receptacle=dining_table_2/top, hint_xy=[3.1, 6.7])`
- 摆法 `adult_and_kid`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=bowl)` → 5. `pick(object=bowl)` → 6. `navigate(destination=dining_table_2/top)` → 7. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.93, 6.89])` → 8. `navigate(destination=bookcase_2/top)` → 9. `look(target=bookcase_2/top)` → 10. `navigate(destination=mug)` → 11. `pick(object=mug)` → 12. `navigate(destination=dining_table_2/top)` → 13. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[3.1, 6.7])` → 14. `navigate(destination=bowl_2)` → 15. `pick(object=bowl_2)` → 16. `navigate(destination=dining_table_2/top)` → 17. `place(object=bowl_2, receptacle=dining_table_2/top, hint_xy=[2.93, 6.04])` → 18. `navigate(destination=kitchen_counter_2/top)` → 19. `look(target=kitchen_counter_2/top)` → 20. `navigate(destination=kid_cup)` → 21. `pick(object=kid_cup)` → 22. `navigate(destination=dining_table_2/top)` → 23. `place(object=kid_cup, receptacle=dining_table_2/top, hint_xy=[3.1, 5.85])`

---

## T15_book_face_up

> 岛台上有本平装书一直扣着放，书脊都快压弯了，帮忙处理一下。书还放在岛台上，他还没看完。

### book_free（对照）

**情况**：书周围有空 → 翻过来

**成功条件**：

- `paperback_book` 翻过面
- `paperback_book` 在 `kitchen_island/top` 上
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `flip(object=paperback_book)`

### book_out_of_view（Task）

**情况**：机器人背对岛台出发 → 先找书

**成功条件**：

- `paperback_book` 翻过面
- `paperback_book` 在 `kitchen_island/top` 上
- 手里空着

**参考调用顺序**：

1. `search(object=paperback_book, region=living_room_0_0)` → 2. `navigate(destination=paperback_book)` → 3. `flip(object=paperback_book)`

### flip_on_the_shelf（Task）

**情况**：书扣在卧室书架里面的一层，上方只有约 24 cm，没地方翻 → 拿到书架顶上空的地方翻好，再放回那一层（在原处硬翻算失败）

**指令**：卧室书架的一层上有本平装书一直扣着放，书脊都快压弯了，帮忙处理一下，书还放回那一层。

**成功条件**：

- 摆法 `shelf_0`：
  - `paperback_book` 翻过面
  - `paperback_book` 在 `bookcase_2/shelf_0` 上
  - 手里空着
- 摆法 `shelf_1`：
  - `paperback_book` 翻过面
  - `paperback_book` 在 `bookcase_2/shelf_1` 上
  - 手里空着

**参考调用顺序**：

- 摆法 `shelf_1`：1. `search(object=paperback_book, region=bedroom_0_1)` → 2. `navigate(destination=paperback_book)` → 3. `pick(object=paperback_book)` → 4. `navigate(destination=bookcase_2/top)` → 5. `place(object=paperback_book, receptacle=bookcase_2/top, hint_xy=[1.0, -0.45])` → 6. `flip(object=paperback_book)` → 7. `pick(object=paperback_book)` → 8. `place(object=paperback_book, receptacle=bookcase_2/shelf_1, hint_xy=[1.0, -0.44])`
- 摆法 `shelf_0`：1. `search(object=paperback_book, region=bedroom_0_1)` → 2. `navigate(destination=paperback_book)` → 3. `pick(object=paperback_book)` → 4. `navigate(destination=bookcase_2/top)` → 5. `place(object=paperback_book, receptacle=bookcase_2/top, hint_xy=[1.0, -0.45])` → 6. `flip(object=paperback_book)` → 7. `pick(object=paperback_book)` → 8. `place(object=paperback_book, receptacle=bookcase_2/shelf_0, hint_xy=[1.0, -0.44])`

---

## T16_rolling_pin_at_edge

> 准备包饺子了，擀面杖滚到岛台前沿快掉下去了。把它往里滚回去别让它掉下来，顺便看看滚得顺不顺。

### pin_free（对照）

**情况**：擀面杖后面有空 → 直接往里滚

**成功条件**：

- `rolling_pin` 滚过
- `rolling_pin` 在 `kitchen_island/top` 上
- `rolling_pin` 离台面边缘至少 6 cm
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=rolling_pin)` → 3. `roll(object=rolling_pin, distance_m=0.12)`

### pin_out_of_view（Task）

**情况**：机器人背对岛台出发 → 先找

**成功条件**：

- `rolling_pin` 滚过
- `rolling_pin` 在 `kitchen_island/top` 上
- `rolling_pin` 离台面边缘至少 6 cm
- 手里空着

**参考调用顺序**：

1. `search(object=rolling_pin, region=living_room_0_0)` → 2. `navigate(destination=rolling_pin)` → 3. `roll(object=rolling_pin, distance_m=0.12)`

### everything_near_the_edge（Task）

**情况**：“岛台边上有东西快掉下去了，处理一下”：除了擀面杖，有时马克杯（edge_mug）或装满燕麦的碗也在边上 → 找出所有快掉的，各用合适的办法挪进去（擀面杖滚、杯碗拿进来），放得稳的别动

**指令**：岛台边上有东西快掉下去了，处理一下。

**成功条件**：

- 摆法 `pin_only`：
  - `rolling_pin` 在 `kitchen_island/top` 上
  - `rolling_pin` 离台面边缘至少 6 cm
  - `edge_mug`、`oatmeal` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `pin_and_mug`：
  - `rolling_pin` 在 `kitchen_island/top` 上
  - `rolling_pin` 离台面边缘至少 6 cm
  - `edge_mug` 在 `kitchen_island/top` 上
  - `edge_mug` 离台面边缘至少 6 cm
  - `edge_mug` 立着
  - `oatmeal` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `pin_and_bowl`：
  - `rolling_pin` 在 `kitchen_island/top` 上
  - `rolling_pin` 离台面边缘至少 6 cm
  - `oatmeal` 在 `kitchen_island/top` 上
  - `oatmeal` 离台面边缘至少 6 cm
  - `oatmeal` 立着
  - `edge_mug` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着

**参考调用顺序**：

- 摆法 `pin_and_mug`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=rolling_pin)` → 3. `roll(object=rolling_pin, distance_m=0.12)` → 4. `navigate(destination=edge_mug)` → 5. `pick(object=edge_mug)` → 6. `place(object=edge_mug, receptacle=kitchen_island/top, hint_xy=[7.3, 1.8])`
- 摆法 `pin_and_bowl`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=rolling_pin)` → 3. `roll(object=rolling_pin, distance_m=0.12)` → 4. `navigate(destination=oatmeal)` → 5. `pick(object=oatmeal)` → 6. `place(object=oatmeal, receptacle=kitchen_island/top, hint_xy=[7.3, 1.8])`
- 摆法 `pin_only`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=rolling_pin)` → 3. `roll(object=rolling_pin, distance_m=0.12)`

---

## T17_hide_and_seek_block

> 陪孩子玩藏东西的游戏：把木积木藏进灶台上的空锅里，再盖好锅盖，别让孩子一眼看到。

### lid_off（对照）

**情况**：锅盖在锅边 → 藏好、盖上

**成功条件**：

- `wooden_block_b` 藏好了（从房间里看不到）
- `handled_cooking_pot` 盖着 `pot_lid`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)`

### h_task_lid_elsewhere（Task）

**情况**：锅盖在靠墙柜上 → 先把锅盖拿到灶台，再藏

**成功条件**：

- `wooden_block_b` 藏好了（从房间里看不到）
- `handled_cooking_pot` 盖着 `pot_lid`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=pot_lid)` → 4. `pick(object=pot_lid)` → 5. `navigate(destination=kitchen_stove/top)` → 6. `place(object=pot_lid, receptacle=kitchen_stove/top, hint_xy=[8.715, 1.655])` → 7. `navigate(destination=handled_cooking_pot)` → 8. `look(target=kitchen_stove/top)` → 9. `navigate(destination=kitchen_island/top)` → 10. `look(target=kitchen_island/top)` → 11. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)`

### hide_both（Task）

**情况**：两块积木藏进同一个锅，另一块在别的房间 → 找到第二块，中间再揭一次盖，最后盖好

**指令**：我们在和孩子玩捉迷藏，藏的是他的玩具积木：把两块木积木都藏进灶上那个空锅里，再盖上锅盖，别让孩子看见。

**成功条件**：

- `wooden_block_b` 藏好了（从房间里看不到）
- `floor_block` 藏好了（从房间里看不到）
- `handled_cooking_pot` 盖着 `pot_lid`
- 手里空着

**参考调用顺序**：

- 摆法 `tv_stand`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)` → 6. `search(object=floor_block, region=living_room_0_0)`（补救） → 7. `navigate(destination=handled_cooking_pot)`（补救） → 8. `uncover(container=handled_cooking_pot)`（补救） → 9. `navigate(destination=floor_block)`（补救） → 10. `look(target=floor_block)`（补救） → 11. `hide(object=floor_block, receptacle=handled_cooking_pot, lid=pot_lid)`（补救）
- 摆法 `dining`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)` → 6. `search(object=floor_block, region=dining_room_0_1)`（补救） → 7. `navigate(destination=handled_cooking_pot)`（补救） → 8. `uncover(container=handled_cooking_pot)`（补救） → 9. `navigate(destination=floor_block)`（补救） → 10. `look(target=floor_block)`（补救） → 11. `hide(object=floor_block, receptacle=handled_cooking_pot, lid=pot_lid)`（补救）

### new_spot_this_time（Task）

**情况**：“上次藏在锅里孩子一下就找到了，这次换个地方” → 选别的能藏住的地方（比如先腾手开矮柜门，放进去关上），不能再用锅

**指令**：再玩一次藏积木。上次藏在灶上的锅里，孩子一下就找到了，这次换个地方藏好。

**成功条件**：

- `wooden_block_b` 藏好了（从房间里看不到）
- `wooden_block_b` 不在 `handled_cooking_pot` 里
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=kitchen_cabinet_4)` → 3. `open(articulated=kitchen_cabinet_4)` → 4. `navigate(destination=wooden_block_b)` → 5. `pick(object=wooden_block_b)` → 6. `navigate(destination=kitchen_cabinet_4)` → 7. `place(object=wooden_block_b, receptacle=kitchen_cabinet_4/inside_shelf, hint_xy=[1.4, 0.42])` → 8. `close(articulated=kitchen_cabinet_4)`

---

## T18_check_cabinet_dishes

> 奶奶想知道靠墙矮柜里还有没有干净的盘子和碗，晚饭要用。去看一眼里面，看完把柜门关好。

### at_island（对照）

**情况**：打开柜子看一眼，再关好

**成功条件**：

- 看到过 `plate_inside_kitchen_cabinet`
- 看到过 `bowl_inside_kitchen_cabinet`
- `kitchen_cabinet_6` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `inspect(receptacle=kitchen_cabinet_6)` → 4. `close(articulated=kitchen_cabinet_6)`

### h_task_two_cabinets（Task）

**情况**：第一个柜子里没有碗 → 再查另一个矮柜，两个都关好

**指令**：奶奶想知道矮墙柜里还有没有干净的盘子和碗做晚饭用。请看一下柜子里面，看完把柜门关好。

**成功条件**：

- 看到过 `plate_inside_kitchen_cabinet`
- 看到过 `bowl_inside_kitchen_cabinet`
- `kitchen_cabinet_6` 关着
- 手里空着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `inspect(receptacle=kitchen_cabinet_6)` → 4. `close(articulated=kitchen_cabinet_6)` → 5. `navigate(destination=kitchen_cabinet_4)` → 6. `open(articulated=kitchen_cabinet_4)` → 7. `inspect(receptacle=kitchen_cabinet_4)` → 8. `close(articulated=kitchen_cabinet_4)`

### x6_gd_bowl_elsewhere__two_places（Task）

**情况**：盘子在靠墙柜，碗在微波炉里 → 两处都查

**指令**：奶奶想知道晚饭还有没有干净的盘子和碗，看看靠墙矮柜和微波炉里有没有。看完把门都关好。

**成功条件**：

- 看到过 `plate_inside_kitchen_cabinet`
- 看到过 `bowl_inside_kitchen_cabinet`
- `kitchen_cabinet_6` 关着
- `kitchen_microwave` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `inspect(receptacle=kitchen_cabinet_6)` → 4. `close(articulated=kitchen_cabinet_6)` → 5. `navigate(destination=kitchen_microwave)` → 6. `open(articulated=kitchen_microwave)` → 7. `look(target=kitchen_microwave/inside_floor)` → 8. `close(articulated=kitchen_microwave)`

### x6_gd_bowl_elsewhere__three_places（Task）

**情况**：同上，指令还多提了一个空矮柜 → 三处都查

**指令**：奶奶想知道晚饭还有没有干净的盘子和碗，看看厨房的矮柜和微波炉里有没有。看完把门都关好。

**成功条件**：

- 看到过 `plate_inside_kitchen_cabinet`
- 看到过 `bowl_inside_kitchen_cabinet`
- `kitchen_cabinet_6` 关着
- `kitchen_microwave` 关着
- 手里空着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `inspect(receptacle=kitchen_cabinet_6)` → 4. `close(articulated=kitchen_cabinet_6)` → 5. `navigate(destination=kitchen_cabinet_4)` → 6. `open(articulated=kitchen_cabinet_4)` → 7. `inspect(receptacle=kitchen_cabinet_4)` → 8. `close(articulated=kitchen_cabinet_4)` → 9. `navigate(destination=kitchen_microwave)` → 10. `open(articulated=kitchen_microwave)` → 11. `look(target=kitchen_microwave/inside_floor)` → 12. `close(articulated=kitchen_microwave)`

### enough_for_dinner（Task）

**情况**：“今晚三个人吃晚饭，靠墙矮柜里的干净碗要够用” → 数一数柜里有几个，跟需要的比，只补差的（够了就什么都不拿）

**指令**：今晚三个人吃晚饭，靠墙矮柜里的干净碗要够用。弄完把柜门关好。

**成功条件**：

- 摆法 `two_short`：
  - 这 3 件中至少 3 件还在 `kitchen_cabinet_6/inside_shelf` 上：`bowl_inside_kitchen_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`
  - `kitchen_cabinet_6` 关着
  - 手里空着
- 摆法 `one_short`：
  - 这 4 件中至少 3 件还在 `kitchen_cabinet_6/inside_shelf` 上：`bowl_inside_kitchen_cabinet`、`clean_bowl_2`、`bowl_kitchen_cabinet`、`bowl_side_table`
  - `kitchen_cabinet_6` 关着
  - 手里空着
  - `bowl_side_table` 没被挪动（离开局位置不超过 3 cm）
- 摆法 `enough`：
  - 这 5 件中至少 3 件还在 `kitchen_cabinet_6/inside_shelf` 上：`bowl_inside_kitchen_cabinet`、`clean_bowl_2`、`clean_bowl_3`、`bowl_kitchen_cabinet`、`bowl_side_table`
  - `kitchen_cabinet_6` 关着
  - 手里空着
  - `bowl_kitchen_cabinet`、`bowl_side_table` 没被挪动（离开局位置不超过 3 cm）

**参考调用顺序**：

- 摆法 `enough`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `inspect(receptacle=kitchen_cabinet_6)` → 4. `close(articulated=kitchen_cabinet_6)`
- 摆法 `one_short`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `inspect(receptacle=kitchen_cabinet_6)` → 4. `navigate(destination=kitchen_cabinet_3/top)` → 5. `look(target=kitchen_cabinet_3/top)` → 6. `navigate(destination=bowl_kitchen_cabinet)` → 7. `pick(object=bowl_kitchen_cabinet)` → 8. `navigate(destination=kitchen_cabinet_6)` → 9. `place(object=bowl_kitchen_cabinet, receptacle=kitchen_cabinet_6/inside_shelf, hint_xy=[3.685, 0.36])` → 10. `close(articulated=kitchen_cabinet_6)`
- 摆法 `two_short`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `inspect(receptacle=kitchen_cabinet_6)` → 4. `navigate(destination=kitchen_cabinet_3/top)` → 5. `look(target=kitchen_cabinet_3/top)` → 6. `navigate(destination=bowl_kitchen_cabinet)` → 7. `pick(object=bowl_kitchen_cabinet)` → 8. `navigate(destination=kitchen_cabinet_6)` → 9. `place(object=bowl_kitchen_cabinet, receptacle=kitchen_cabinet_6/inside_shelf, hint_xy=[3.5, 0.36])` → 10. `navigate(destination=dining_table_1/top)` → 11. `look(target=dining_table_1/top)` → 12. `navigate(destination=bowl_side_table)` → 13. `pick(object=bowl_side_table)` → 14. `navigate(destination=kitchen_cabinet_6)` → 15. `place(object=bowl_side_table, receptacle=kitchen_cabinet_6/inside_shelf, hint_xy=[3.685, 0.36])` → 16. `close(articulated=kitchen_cabinet_6)`

---

## T19_recycling

> 电影看完了，把该回收的东西放进回收箱。

### bin_on_bookcase（对照）

**情况**：罐子在电视柜，泡沫块在客厅地上 → 两样都放进回收箱

**成功条件**：

- `soda_can` 在 `wide_storage_bin` 里
- `foam_cube` 在 `wide_storage_bin` 里
- 手里空着

**参考调用顺序**：

1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=soda_can)` → 5. `pick(object=soda_can)` → 6. `navigate(destination=bookcase_2/top)` → 7. `look(target=bookcase_2/top)` → 8. `navigate(destination=wide_storage_bin)` → 9. `drop(object=soda_can, container=wide_storage_bin)` → 10. `navigate(destination=foam_cube)` → 11. `pick(object=foam_cube)` → 12. `navigate(destination=wide_storage_bin)` → 13. `drop(object=foam_cube, container=wide_storage_bin)`

### m_can_in_dining_room（Task）

**情况**：罐子不在原处，看不到 → 先找

**成功条件**：

- `soda_can` 在 `wide_storage_bin` 里
- `foam_cube` 在 `wide_storage_bin` 里
- 手里空着

**参考调用顺序**：

- 摆法 `m_can_in_dining_room`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=dining_room_0_1)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `navigate(destination=wide_storage_bin)` → 10. `drop(object=soda_can, container=wide_storage_bin)` → 11. `navigate(destination=foam_cube)` → 12. `pick(object=foam_cube)` → 13. `navigate(destination=wide_storage_bin)` → 14. `drop(object=foam_cube, container=wide_storage_bin)`
- 摆法 `alt_tv_stand_2`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=living_room_0_0)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `navigate(destination=wide_storage_bin)` → 10. `drop(object=soda_can, container=wide_storage_bin)` → 11. `navigate(destination=foam_cube)` → 12. `pick(object=foam_cube)` → 13. `navigate(destination=wide_storage_bin)` → 14. `drop(object=foam_cube, container=wide_storage_bin)`

### lookalike_bin（Task）

**情况**：罐子不在原处；客厅还有个一模一样、装着积木的箱子 → 认准书架上那个（里面有塑料杯）

**成功条件**：

- `soda_can` 在 `wide_storage_bin` 里
- `foam_cube` 在 `wide_storage_bin` 里
- 手里空着

**参考调用顺序**：

- 摆法 `lookalike_bin`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=dining_room_0_1)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `identify(object=wide_storage_bin)`（补救） → 10. `navigate(destination=wide_storage_bin)` → 11. `drop(object=soda_can, container=wide_storage_bin)` → 12. `navigate(destination=foam_cube)` → 13. `touch(object=foam_cube)`（补救） → 14. `pick(object=foam_cube)` → 15. `navigate(destination=wide_storage_bin)` → 16. `drop(object=foam_cube, container=wide_storage_bin)`
- 摆法 `alt_tv_stand_2`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=living_room_0_0)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `identify(object=wide_storage_bin)`（补救） → 10. `navigate(destination=wide_storage_bin)` → 11. `drop(object=soda_can, container=wide_storage_bin)` → 12. `navigate(destination=foam_cube)` → 13. `touch(object=foam_cube)`（补救） → 14. `pick(object=foam_cube)` → 15. `navigate(destination=wide_storage_bin)` → 16. `drop(object=foam_cube, container=wide_storage_bin)`

### x6_gd_can_put_away（Task）

**情况**：罐子在两个关着的矮柜之一 → 逐个找

**指令**：看完电影了。有人把空易拉罐收进了厨房的一个矮柜里，快递里的泡沫块还在客厅地上；把这两样都放进卧室矮书架上那个装回收的宽收纳箱里，再把柜门关好。

**成功条件**：

- `soda_can` 在 `wide_storage_bin` 里
- `foam_cube` 在 `wide_storage_bin` 里
- 手里空着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

- 摆法 `in_4`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=soda_can)` → 13. `pick(object=soda_can)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `close(articulated=kitchen_cabinet_4)` → 16. `navigate(destination=bookcase_2/top)` → 17. `look(target=bookcase_2/top)` → 18. `navigate(destination=wide_storage_bin)` → 19. `drop(object=soda_can, container=wide_storage_bin)` → 20. `navigate(destination=foam_cube)` → 21. `pick(object=foam_cube)` → 22. `navigate(destination=wide_storage_bin)` → 23. `drop(object=foam_cube, container=wide_storage_bin)`
- 摆法 `in_6`：1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_4)` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=soda_can)` → 13. `pick(object=soda_can)` → 14. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 15. `close(articulated=kitchen_cabinet_6)` → 16. `navigate(destination=bookcase_2/top)` → 17. `look(target=bookcase_2/top)` → 18. `navigate(destination=wide_storage_bin)` → 19. `drop(object=soda_can, container=wide_storage_bin)` → 20. `navigate(destination=foam_cube)` → 21. `pick(object=foam_cube)` → 22. `navigate(destination=wide_storage_bin)` → 23. `drop(object=foam_cube, container=wide_storage_bin)`

---

## T20_juice_back_to_table

> 有人把早餐桌上的果汁瓶拿走随手放下了。把它放回餐桌上，立着放。

### bottle_on_cabinet（对照）

**情况**：瓶子在靠墙柜顶 → 放回餐桌

**成功条件**：

- `juice_bottle` 在 `dining_table_2/top` 上
- `juice_bottle` 立着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=juice_bottle)` → 4. `pick(object=juice_bottle)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[3.0, 7.3])`

### m_bottle_on_tv_stand（Task）

**情况**：瓶子在客厅看不到的地方 → 先找

**成功条件**：

- `juice_bottle` 在 `dining_table_2/top` 上
- `juice_bottle` 立着
- 手里空着

**参考调用顺序**：

- 摆法 `m_bottle_on_tv_stand`：1. `search(object=juice_bottle, region=living_room_0_0)` → 2. `navigate(destination=juice_bottle)` → 3. `pick(object=juice_bottle)` → 4. `navigate(destination=dining_table_2/top)` → 5. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[3.0, 7.3])`
- 摆法 `alt_dining_table_2`：1. `search(object=juice_bottle, region=dining_room_0_1)` → 2. `navigate(destination=juice_bottle)` → 3. `pick(object=juice_bottle)` → 4. `navigate(destination=dining_table_2/top)` → 5. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[3.0, 7.3])`

### x6_gd_bottle_put_away（Task）

**情况**：瓶子被收进了两个矮柜之一 → 逐个找

**指令**：有人把果汁瓶收进了厨房的一个矮柜里。把它拿回餐桌上立着放好，再把柜门关好。

**成功条件**：

- `juice_bottle` 在 `dining_table_2/top` 上
- `juice_bottle` 立着
- 手里空着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

- 摆法 `in_cabinet_4`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=juice_bottle)` → 13. `pick(object=juice_bottle)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `close(articulated=kitchen_cabinet_4)` → 16. `navigate(destination=dining_table_2/top)` → 17. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[3.0, 7.3])`
- 摆法 `in_cabinet_6`：1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_4)` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=juice_bottle)` → 13. `pick(object=juice_bottle)` → 14. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 15. `close(articulated=kitchen_cabinet_6)` → 16. `navigate(destination=dining_table_2/top)` → 17. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[3.0, 7.3])`

---

## T14_shelve_the_book

> 孩子看完书了，帮他把书收好。

### e1_book_ready（对照）

**情况**：红书在书房书桌上 → 放回卧室矮书架

**成功条件**：

- `book_red` 在 `bookcase_2/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=book_red)` → 4. `pick(object=book_red)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=book_red, receptacle=bookcase_2/top)`

### within_kids_reach（Task）

**情况**：“他明天还想自己拿来接着看”：红书那一套放在高书架最上层（原本该放的地方），孩子够不着 → 放到他够得着的低层（0.8 m 以下），不放回原处

**指令**：孩子看完书了，帮他把书收好。他明天还想自己拿来接着看。

**成功条件**：

- `["not on", "book_red", "large_shelf_4/shelf_4"]`
- `["not on", "book_red", "large_shelf_5/shelf_3"]`
- `book_red` 不在地上
- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `book_red` 在 `bookcase_2/top` 上
  - 第 2 组：
    - `book_red` 在 `bookcase_2/shelf_1` 上
  - 第 3 组：
    - `book_red` 在 `bookcase_2/shelf_0` 上
  - 第 4 组：
    - `book_red` 在 `bookcase_3/top` 上
  - 第 5 组：
    - `book_red` 在 `bookcase_3/shelf_1` 上
  - 第 6 组：
    - `book_red` 在 `bookcase_3/shelf_0` 上
  - 第 7 组：
    - `book_red` 在 `large_shelf_4/shelf_0` 上
  - 第 8 组：
    - `book_red` 在 `large_shelf_4/shelf_1` 上
  - 第 9 组：
    - `book_red` 在 `large_shelf_4/shelf_2` 上
  - 第 10 组：
    - `book_red` 在 `large_shelf_5/shelf_0` 上
  - 第 11 组：
    - `book_red` 在 `large_shelf_5/shelf_1` 上

**参考调用顺序**：

- 摆法 `set_on_large_shelf_4`：1. `look(target=desk_1/top)` → 2. `explore_room(room=bedroom_0_1)` → 3. `navigate(destination=book_red)` → 4. `pick(object=book_red)` → 5. `navigate(destination=large_shelf_4/shelf_1)` → 6. `place(object=book_red, receptacle=large_shelf_4/shelf_1, hint_xy=[3.7, -5.15])`
- 摆法 `set_on_large_shelf_5`：1. `look(target=desk_1/top)` → 2. `explore_room(room=bedroom_0_1)` → 3. `navigate(destination=book_red)` → 4. `pick(object=book_red)` → 5. `navigate(destination=large_shelf_5/shelf_1)` → 6. `place(object=book_red, receptacle=large_shelf_5/shelf_1, hint_xy=[4.45, -0.35])`

### stack_them_stably（Task）

**情况**：“把书桌上的书都收到他卧室的书架上，摞成一摞”：两三本大小不同的书 → 从书的大小推出顺序，大的在下、依次变小

**指令**：孩子看完书了，把书桌上的书都收到他卧室的书架上，摞成一摞。

**成功条件**：

- 摆法 `red_blue_paperback`：
  - `book_red` 在 `bookcase_2/top` 上
  - `desk_book_blue` 叠在 `book_red` 上
  - `desk_paperback_book` 叠在 `desk_book_blue` 上
  - 手里空着
- 摆法 `blue_green_paperback`：
  - `desk_book_green` 在 `bookcase_2/top` 上
  - `desk_book_blue` 叠在 `desk_book_green` 上
  - `desk_paperback_book` 叠在 `desk_book_blue` 上
  - 手里空着
- 摆法 `green_paperback`：
  - `desk_book_green` 在 `bookcase_2/top` 上
  - `desk_paperback_book` 叠在 `desk_book_green` 上
  - 手里空着

**参考调用顺序**：

- 摆法 `red_blue_paperback`：1. `look(target=desk_1/top)` → 2. `navigate(destination=book_red)` → 3. `pick(object=book_red)` → 4. `navigate(destination=bookcase_2/top)` → 5. `place(object=book_red, receptacle=bookcase_2/top, hint_xy=[1.0, -0.45])` → 6. `navigate(destination=desk_book_blue)` → 7. `pick(object=desk_book_blue)` → 8. `navigate(destination=bookcase_2/top)` → 9. `stack(object=desk_book_blue, base=book_red)` → 10. `navigate(destination=desk_paperback_book)` → 11. `pick(object=desk_paperback_book)` → 12. `navigate(destination=bookcase_2/top)` → 13. `stack(object=desk_paperback_book, base=desk_book_blue)`
- 摆法 `green_paperback`：1. `look(target=desk_1/top)` → 2. `navigate(destination=desk_book_green)` → 3. `pick(object=desk_book_green)` → 4. `navigate(destination=bookcase_2/top)` → 5. `place(object=desk_book_green, receptacle=bookcase_2/top, hint_xy=[1.0, -0.45])` → 6. `navigate(destination=desk_paperback_book)` → 7. `pick(object=desk_paperback_book)` → 8. `navigate(destination=bookcase_2/top)` → 9. `stack(object=desk_paperback_book, base=desk_book_green)`
- 摆法 `blue_green_paperback`：1. `look(target=desk_1/top)` → 2. `navigate(destination=desk_book_green)` → 3. `pick(object=desk_book_green)` → 4. `navigate(destination=bookcase_2/top)` → 5. `place(object=desk_book_green, receptacle=bookcase_2/top, hint_xy=[1.0, -0.45])` → 6. `navigate(destination=desk_book_blue)` → 7. `pick(object=desk_book_blue)` → 8. `navigate(destination=bookcase_2/top)` → 9. `stack(object=desk_book_blue, base=desk_book_green)` → 10. `navigate(destination=desk_paperback_book)` → 11. `pick(object=desk_paperback_book)` → 12. `navigate(destination=bookcase_2/top)` → 13. `stack(object=desk_paperback_book, base=desk_book_blue)`

### homework_stays（Task）

**情况**：“把书桌收拾一下，作业他明天还要接着写”：书桌上有看完的书、用过的马克杯、摊开的作业本和铅笔 → 书回书架，杯子回厨房，作业原样不动（过程要求：整局不拿起作业本和铅笔）

**指令**：孩子看完书了，把他的书桌收拾一下。作业他明天还要接着写。

**成功条件**：

- `book_red` 在 `bookcase_2/top` 上
- `desk_mug` 在 `kitchen_counter_2/top` 上
- `desk_mug` 立着
- `homework`、`hw_pencil` 没被挪动（离开局位置不超过 3 cm）
- 过程要求：整局都没拿起过 `homework`、`hw_pencil`（拆了再搭回去不算）
- 手里空着

**参考调用顺序**：

1. `look(target=desk_1/top)` → 2. `navigate(destination=book_red)` → 3. `pick(object=book_red)` → 4. `navigate(destination=bookcase_2/top)` → 5. `place(object=book_red, receptacle=bookcase_2/top)` → 6. `navigate(destination=desk_mug)` → 7. `pick(object=desk_mug)` → 8. `navigate(destination=kitchen_counter_2/top)` → 9. `place(object=desk_mug, receptacle=kitchen_counter_2/top, hint_xy=[-0.3, 7.6])`

### whose_book（Task）

**情况**：“把书房书桌上的书收好”：孩子的绘本在卧室书架上，大人的小说在客厅书架上 → 看书是谁的、跟同类放一起

**指令**：把书房书桌上的书收好。

**成功条件**：

- 摆法 `novel`：
  - `novel` 在 `large_shelf_2/shelf_2` 上
  - `kid_book_1`、`kid_book_2`、`novel_1`、`novel_2` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `picture_book`：
  - `picture_book` 在 `bookcase_2/top` 上
  - `kid_book_1`、`kid_book_2`、`novel_1`、`novel_2` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `both`：
  - `picture_book` 在 `bookcase_2/top` 上
  - `novel` 在 `large_shelf_2/shelf_2` 上
  - `kid_book_1`、`kid_book_2`、`novel_1`、`novel_2` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着

**参考调用顺序**：

- 摆法 `picture_book`：1. `look(target=desk_1/top)` → 2. `navigate(destination=picture_book)` → 3. `pick(object=picture_book)` → 4. `navigate(destination=bookcase_2/top)` → 5. `place(object=picture_book, receptacle=bookcase_2/top, hint_xy=[1.0, -0.45])`
- 摆法 `novel`：1. `look(target=desk_1/top)` → 2. `navigate(destination=novel)` → 3. `pick(object=novel)` → 4. `navigate(destination=large_shelf_2/shelf_2)` → 5. `place(object=novel, receptacle=large_shelf_2/shelf_2, hint_xy=[-1.86, -0.95])`
- 摆法 `both`：1. `look(target=desk_1/top)` → 2. `navigate(destination=picture_book)` → 3. `pick(object=picture_book)` → 4. `navigate(destination=bookcase_2/top)` → 5. `place(object=picture_book, receptacle=bookcase_2/top, hint_xy=[1.0, -0.45])` → 6. `navigate(destination=novel)` → 7. `pick(object=novel)` → 8. `navigate(destination=large_shelf_2/shelf_2)` → 9. `place(object=novel, receptacle=large_shelf_2/shelf_2, hint_xy=[-1.86, -0.95])`

### next_in_series（Task）

**情况**：“红书收回书架，再把同一套的另一本拿到书桌上”：另一本红封面的书混在别的书里 → 两个方向的子目标；按封面认出同一套，找遍书架

**指令**：孩子看完这本红书了，收回他的书架，再把同一套的另一本拿到书桌上，他明天看。

**成功条件**：

- `book_red` 在 `bookcase_2/top` 上
- `red_book_2` 在 `desk_1/top` 上
- `blue_book_case`、`paperback_shelf` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

- 摆法 `on_bookcase`：1. `look(target=desk_1/top)` → 2. `navigate(destination=book_red)` → 3. `pick(object=book_red)` → 4. `navigate(destination=bookcase_2/top)` → 5. `place(object=book_red, receptacle=bookcase_2/top, hint_xy=[1.0, -0.55])` → 6. `look(target=bookcase_2/top)` → 7. `navigate(destination=red_book_2)` → 8. `pick(object=red_book_2)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=red_book_2, receptacle=desk_1/top, hint_xy=[-0.8, -6.05])`
- 摆法 `on_other_bookcase`：1. `look(target=desk_1/top)` → 2. `navigate(destination=book_red)` → 3. `pick(object=book_red)` → 4. `navigate(destination=bookcase_2/top)` → 5. `place(object=book_red, receptacle=bookcase_2/top, hint_xy=[1.0, -0.55])` → 6. `look(target=bookcase_2/top)` → 7. `search(object=red_book_2, region=bedroom_0_1)` → 8. `look(target=bookcase_3/top)` → 9. `navigate(destination=red_book_2)` → 10. `pick(object=red_book_2)` → 11. `navigate(destination=desk_1/top)` → 12. `place(object=red_book_2, receptacle=desk_1/top, hint_xy=[-0.8, -6.05])`
- 摆法 `on_tall_shelf`：1. `look(target=desk_1/top)` → 2. `navigate(destination=book_red)` → 3. `pick(object=book_red)` → 4. `navigate(destination=bookcase_2/top)` → 5. `place(object=book_red, receptacle=bookcase_2/top, hint_xy=[1.0, -0.55])` → 6. `look(target=bookcase_2/top)` → 7. `search(object=red_book_2, region=bedroom_0_1)` → 8. `look(target=large_shelf_4/shelf_1)` → 9. `navigate(destination=red_book_2)` → 10. `pick(object=red_book_2)` → 11. `navigate(destination=desk_1/top)` → 12. `place(object=red_book_2, receptacle=desk_1/top, hint_xy=[-0.8, -6.05])`

---

## T21_bring_tissues

> 餐桌上洒了点汤，拿点纸巾过去。

### tissue_on_tv_stand（对照）

**情况**：纸巾盒在电视柜，餐桌上有碗汤 → 拿到餐桌

**成功条件**：

- `tissue` 在 `dining_table_2/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=tissue)` → 2. `pick(object=tissue)` → 3. `navigate(destination=dining_table_2/top)` → 4. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[3.3, 6.65])`

### tissue_out_of_view（Task）

**情况**：纸巾盒不在常放的地方，在书房书桌上 → 先找

**成功条件**：

- `tissue` 在 `dining_table_2/top` 上
- 手里空着

**参考调用顺序**：

1. `search(object=tissue, region=living_room_0_1)` → 2. `navigate(destination=tissue)` → 3. `pick(object=tissue)` → 4. `navigate(destination=dining_table_2/top)` → 5. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[3.3, 6.65])`

### which_table（Task）

**情况**：两张餐桌，一张上有人在吃饭（汤碗），另一张空着 → 送到吃饭的那张

**成功条件**：

- 摆法 `west`：
  - `tissue` 在 `dining_table_1/top` 上
  - 手里空着
- 摆法 `east`：
  - `tissue` 在 `dining_table_2/top` 上
  - 手里空着

**参考调用顺序**：

- 摆法 `east`：1. `navigate(destination=tissue)` → 2. `pick(object=tissue)` → 3. `look(target=dining_table_1/top)` → 4. `navigate(destination=dining_table_2/top)` → 5. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[3.3, 6.65])`
- 摆法 `west`：1. `navigate(destination=tissue)` → 2. `pick(object=tissue)` → 3. `look(target=dining_table_2/top)` → 4. `navigate(destination=dining_table_1/top)` → 5. `place(object=tissue, receptacle=dining_table_1/top, hint_xy=[-7.75, 7.4])`

### no_tissue（Task）

**情况**：家里没有纸巾，岛台上有块干海绵 → 拿海绵代替

**成功条件**：

- `spare_sponge` 在 `dining_table_2/top` 上
- 手里空着

**参考调用顺序**：

1. `look(target=tv_stand_2/top)` → 2. `navigate(destination=spare_sponge)` → 3. `pick(object=spare_sponge)` → 4. `navigate(destination=dining_table_2/top)` → 5. `place(object=spare_sponge, receptacle=dining_table_2/top, hint_xy=[3.3, 6.65])`

### tissue_put_away（Task）

**情况**：纸巾收在两个矮柜之一 → 逐个打开找，拿出来后关好门

**成功条件**：

- `tissue` 在 `dining_table_2/top` 上
- `kitchen_cabinet_4` 关着
- `kitchen_cabinet_6` 关着
- 手里空着

**参考调用顺序**：

- 摆法 `in_4`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=tissue)` → 13. `pick(object=tissue)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `close(articulated=kitchen_cabinet_4)` → 16. `navigate(destination=dining_table_2/top)` → 17. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[3.3, 6.65])`
- 摆法 `in_6`：1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_4)` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=tissue)` → 13. `pick(object=tissue)` → 14. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 15. `close(articulated=kitchen_cabinet_6)` → 16. `navigate(destination=dining_table_2/top)` → 17. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[3.3, 6.65])`

### the_kids_side（Task）

**情况**：“孩子吃饭把汤洒了”：桌上一份有塑料杯（孩子的），一份有马克杯（大人的） → 放到孩子那份旁边

**指令**：孩子吃饭把汤洒了，拿点纸巾给他。

**成功条件**：

- `tissue` 在 `dining_table_2/top` 上
- `tissue` 离其中至少一个不超过 15 cm：`kid_bowl`、`kid_cup`
- `tissue` 离这些都超过 25 cm：`adult_bowl`、`adult_mug`
- 手里空着

**参考调用顺序**：

- 摆法 `kid_north`：1. `navigate(destination=tissue)` → 2. `pick(object=tissue)` → 3. `navigate(destination=dining_table_2/top)` → 4. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[3.1, 7.45])`
- 摆法 `kid_south`：1. `navigate(destination=tissue)` → 2. `pick(object=tissue)` → 3. `navigate(destination=dining_table_2/top)` → 4. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[3.1, 6.4])`

### tissue_or_sponge（Task）

**情况**：电视柜上没纸巾，岛台上有块干海绵；纸巾在第一个矮柜、第二个矮柜，或者家里没有（开门前看不出来） → 老地方没有 → 去收纳的柜子看 → 有纸巾就拿纸巾（海绵不拿）；空的就去第二个柜子；两个都空才拿海绵；柜门都关好

**成功条件**：

- 摆法 `none`：
  - `spare_sponge` 在 `dining_table_2/top` 上
  - `kitchen_cabinet_4` 关着
  - `kitchen_cabinet_6` 关着
  - 手里空着
- 摆法 `in_first`、`in_second`：
  - `tissue` 在 `dining_table_2/top` 上
  - `["not on", "spare_sponge", "dining_table_2/top"]`
  - `kitchen_cabinet_4` 关着
  - `kitchen_cabinet_6` 关着
  - 手里空着

**参考调用顺序**：

- 摆法 `in_first`：1. `look(target=tv_stand_2/top)` → 2. `navigate(destination=kitchen_cabinet_4)` → 3. `open(articulated=kitchen_cabinet_4)` → 4. `bend()` → 5. `explore_furniture(furniture=kitchen_cabinet_4)` → 6. `straighten()` → 7. `navigate(destination=tissue)` → 8. `pick(object=tissue)` → 9. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 10. `close(articulated=kitchen_cabinet_4)` → 11. `navigate(destination=dining_table_2/top)` → 12. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[3.3, 6.65])`
- 摆法 `in_second`：1. `look(target=tv_stand_2/top)` → 2. `navigate(destination=kitchen_cabinet_4)` → 3. `open(articulated=kitchen_cabinet_4)` → 4. `bend()` → 5. `explore_furniture(furniture=kitchen_cabinet_4)` → 6. `straighten()` → 7. `close(articulated=kitchen_cabinet_4)` → 8. `navigate(destination=kitchen_cabinet_6)` → 9. `open(articulated=kitchen_cabinet_6)` → 10. `bend()` → 11. `explore_furniture(furniture=kitchen_cabinet_6)` → 12. `straighten()` → 13. `navigate(destination=tissue)` → 14. `pick(object=tissue)` → 15. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 16. `close(articulated=kitchen_cabinet_6)` → 17. `navigate(destination=dining_table_2/top)` → 18. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[3.3, 6.65])`
- 摆法 `none`：1. `look(target=tv_stand_2/top)` → 2. `navigate(destination=kitchen_cabinet_4)` → 3. `open(articulated=kitchen_cabinet_4)` → 4. `bend()` → 5. `explore_furniture(furniture=kitchen_cabinet_4)` → 6. `straighten()` → 7. `close(articulated=kitchen_cabinet_4)` → 8. `navigate(destination=kitchen_cabinet_6)` → 9. `open(articulated=kitchen_cabinet_6)` → 10. `bend()` → 11. `explore_furniture(furniture=kitchen_cabinet_6)` → 12. `straighten()` → 13. `close(articulated=kitchen_cabinet_6)` → 14. `navigate(destination=spare_sponge)` → 15. `pick(object=spare_sponge)` → 16. `navigate(destination=dining_table_2/top)` → 17. `place(object=spare_sponge, receptacle=dining_table_2/top, hint_xy=[3.3, 6.65])`

---

## T22_put_away_shopping

> 买回来的东西放好。

### juice_on_table（对照）

**情况**：餐桌上一瓶果汁 → 放进冰箱，关门

**成功条件**：

- `bought_juice` 在 `breakfast_fridge/inside_shelf` 上
- `bought_juice` 立着
- `breakfast_fridge` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)`

### by_kind（Task）

**情况**：果汁、苹果、零食盒 → 冰箱 / 岛台上的果篮 / 矮柜里（那里已有一盒零食）

**成功条件**：

- `bought_juice` 在 `breakfast_fridge/inside_shelf` 上
- `bought_juice` 立着
- `breakfast_fridge` 关着
- `bought_apple` 在 `home_basket` 里
- `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
- `kitchen_cabinet_6` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)` → 10. `navigate(destination=bought_apple)` → 11. `pick(object=bought_apple)` → 12. `navigate(destination=home_basket)` → 13. `place(object=bought_apple, receptacle=home_basket)` → 14. `navigate(destination=kitchen_cabinet_6)` → 15. `open(articulated=kitchen_cabinet_6)` → 16. `inspect(receptacle=kitchen_cabinet_6)` → 17. `navigate(destination=bought_snack)` → 18. `pick(object=bought_snack)` → 19. `navigate(destination=kitchen_cabinet_6)` → 20. `place(object=bought_snack, receptacle=kitchen_cabinet_6/inside_shelf, hint_xy=[3.6, 0.36])` → 21. `close(articulated=kitchen_cabinet_6)`

### eat_now（Task）

**情况**：“孩子说零食现在就要吃，他在书房写作业” → 零食送书桌，果汁进冰箱

**指令**：买回来的东西放好。孩子说零食现在就要吃，他在书房写作业。

**成功条件**：

- `bought_juice` 在 `breakfast_fridge/inside_shelf` 上
- `bought_juice` 立着
- `breakfast_fridge` 关着
- `bought_snack` 在 `desk_1/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)` → 10. `navigate(destination=bought_snack)` → 11. `pick(object=bought_snack)` → 12. `navigate(destination=desk_1/top)` → 13. `place(object=bought_snack, receptacle=desk_1/top, hint_xy=[-1.1, -5.95])`

### basket_missing（Task）

**情况**：果汁和苹果，家里没有果篮，岛台上有托盘 → 苹果放托盘

**成功条件**：

- `bought_juice` 在 `breakfast_fridge/inside_shelf` 上
- `bought_juice` 立着
- `breakfast_fridge` 关着
- `bought_apple` 在 `fruit_tray` 里
- 手里空着

**参考调用顺序**：

1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)` → 10. `navigate(destination=bought_apple)` → 11. `pick(object=bought_apple)` → 12. `navigate(destination=fruit_tray)` → 13. `place(object=bought_apple, receptacle=fruit_tray)`

### not_shopping（Task）

**情况**：桌上还有孩子的小车和绘本 → 不是买的，不动

**成功条件**：

- `bought_juice` 在 `breakfast_fridge/inside_shelf` 上
- `bought_juice` 立着
- `breakfast_fridge` 关着
- `table_car`、`table_book` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=breakfast_fridge)` → 3. `open(articulated=breakfast_fridge)` → 4. `navigate(destination=bought_juice)` → 5. `pick(object=bought_juice)` → 6. `navigate(destination=breakfast_fridge)` → 7. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 8. `close(articulated=breakfast_fridge)`

### two_spots（Task）

**情况**：买的东西分在餐桌和岛台两处 → 都找到，各归各位

**成功条件**：

- `bought_juice` 在 `breakfast_fridge/inside_shelf` 上
- `bought_juice` 立着
- `breakfast_fridge` 关着
- `bought_apple` 在 `home_basket` 里
- `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
- `kitchen_cabinet_6` 关着
- 手里空着

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=breakfast_fridge)` → 3. `open(articulated=breakfast_fridge)` → 4. `navigate(destination=bought_juice)` → 5. `pick(object=bought_juice)` → 6. `navigate(destination=breakfast_fridge)` → 7. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 8. `close(articulated=breakfast_fridge)` → 9. `look(target=kitchen_island/top)` → 10. `navigate(destination=bought_apple)` → 11. `pick(object=bought_apple)` → 12. `navigate(destination=home_basket)` → 13. `place(object=bought_apple, receptacle=home_basket)` → 14. `navigate(destination=kitchen_cabinet_6)` → 15. `open(articulated=kitchen_cabinet_6)` → 16. `inspect(receptacle=kitchen_cabinet_6)` → 17. `navigate(destination=bought_snack)` → 18. `pick(object=bought_snack)` → 19. `navigate(destination=kitchen_cabinet_6)` → 20. `place(object=bought_snack, receptacle=kitchen_cabinet_6/inside_shelf, hint_xy=[3.6, 0.36])` → 21. `close(articulated=kitchen_cabinet_6)`

### tray_elsewhere（Action + Task）

**情况**：果汁和苹果在餐桌上，果篮不在；西边餐厅的桌上有个托盘，到了才看得到上面是什么：一个橙子，或者四本书平铺占满了托盘 → 果篮没有 → 找别的能装水果的（另一个房间的托盘）→ 有橙子：苹果直接放进去（水果可以放一起，不用挪）；被书占满：先把书放回那个房间的书架（任何书架都算），再放苹果；果汁进冰箱。挪书属于“目的地被占”（A），去别的房间找替代容器是独立的 Task 要求，所以是 A+T

**成功条件**：

- 摆法 `orange_in_it`：
  - `bought_juice` 在 `breakfast_fridge/inside_shelf` 上
  - `bought_juice` 立着
  - `breakfast_fridge` 关着
  - `bought_apple` 完全在 `west_tray` 里（没有露出边沿）
  - `west_tray` 不在地上
  - 手里空着
- 摆法 `books_on_it`：
  - `bought_juice` 在 `breakfast_fridge/inside_shelf` 上
  - `bought_juice` 立着
  - `breakfast_fridge` 关着
  - `bought_apple` 完全在 `west_tray` 里（没有露出边沿）
  - `west_tray` 不在地上
  - `tray_book_1` 在其中任一处上：`bookcase_1/shelf_0`、`bookcase_1/shelf_1`、`bookcase_1/top`、`bookcase_2/shelf_0`、`bookcase_2/shelf_1`、`bookcase_2/top`、`bookcase_3/shelf_0`、`bookcase_3/shelf_1`、`bookcase_3/top`、`bookcase_4/shelf_0`、`bookcase_4/shelf_1`、`bookcase_4/top`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
  - `tray_book_2` 在其中任一处上：`bookcase_1/shelf_0`、`bookcase_1/shelf_1`、`bookcase_1/top`、`bookcase_2/shelf_0`、`bookcase_2/shelf_1`、`bookcase_2/top`、`bookcase_3/shelf_0`、`bookcase_3/shelf_1`、`bookcase_3/top`、`bookcase_4/shelf_0`、`bookcase_4/shelf_1`、`bookcase_4/top`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
  - `tray_book_3` 在其中任一处上：`bookcase_1/shelf_0`、`bookcase_1/shelf_1`、`bookcase_1/top`、`bookcase_2/shelf_0`、`bookcase_2/shelf_1`、`bookcase_2/top`、`bookcase_3/shelf_0`、`bookcase_3/shelf_1`、`bookcase_3/top`、`bookcase_4/shelf_0`、`bookcase_4/shelf_1`、`bookcase_4/top`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
  - `tray_book_4` 在其中任一处上：`bookcase_1/shelf_0`、`bookcase_1/shelf_1`、`bookcase_1/top`、`bookcase_2/shelf_0`、`bookcase_2/shelf_1`、`bookcase_2/top`、`bookcase_3/shelf_0`、`bookcase_3/shelf_1`、`bookcase_3/top`、`bookcase_4/shelf_0`、`bookcase_4/shelf_1`、`bookcase_4/top`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
  - 手里空着

**参考调用顺序**：

- 摆法 `orange_in_it`：1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)` → 10. `search(object=west_tray, region=dining_room_0_0)` → 11. `look(target=west_tray)` → 12. `navigate(destination=bought_apple)` → 13. `pick(object=bought_apple)` → 14. `navigate(destination=west_tray)` → 15. `place(object=bought_apple, receptacle=west_tray)`
- 摆法 `books_on_it`：1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)` → 10. `search(object=west_tray, region=dining_room_0_0)` → 11. `look(target=west_tray)` → 12. `navigate(destination=tray_book_1)` → 13. `pick(object=tray_book_1)` → 14. `navigate(destination=bookcase_1/top)` → 15. `place(object=tray_book_1, receptacle=bookcase_1/top, hint_xy=[-9.59, 6.52])` → 16. `navigate(destination=tray_book_2)` → 17. `pick(object=tray_book_2)` → 18. `navigate(destination=bookcase_1/top)` → 19. `place(object=tray_book_2, receptacle=bookcase_1/top, hint_xy=[-9.59, 6.82])` → 20. `navigate(destination=tray_book_3)` → 21. `pick(object=tray_book_3)` → 22. `navigate(destination=bookcase_1/shelf_1)` → 23. `place(object=tray_book_3, receptacle=bookcase_1/shelf_1, hint_xy=[-9.59, 6.52])` → 24. `navigate(destination=tray_book_4)` → 25. `pick(object=tray_book_4)` → 26. `navigate(destination=bookcase_1/shelf_1)` → 27. `place(object=tray_book_4, receptacle=bookcase_1/shelf_1, hint_xy=[-9.59, 6.82])` → 28. `navigate(destination=bought_apple)` → 29. `pick(object=bought_apple)` → 30. `navigate(destination=west_tray)` → 31. `place(object=bought_apple, receptacle=west_tray)`

---

## T23_pick_up_dropped

> 地上掉了东西，帮忙捡起来放好。

### spoon_on_floor（对照）

**情况**：厨房地上一把勺子 → 放回厨房台面（勺子都放在那）

**成功条件**：

- `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_counter_2/top)` → 2. `navigate(destination=dropped_spoon)` → 3. `pick(object=dropped_spoon)` → 4. `navigate(destination=kitchen_counter_2/top)` → 5. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.1, 7.6])`

### by_kind（Task）

**情况**：地上有勺子和一块积木 → 勺子回台面，积木进客厅的玩具箱

**成功条件**：

- `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`
- `dropped_block` 在 `toy_box` 里
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_counter_2/top)` → 2. `navigate(destination=dropped_spoon)` → 3. `pick(object=dropped_spoon)` → 4. `navigate(destination=kitchen_counter_2/top)` → 5. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.1, 7.6])` → 6. `navigate(destination=dropped_block)` → 7. `pick(object=dropped_block)` → 8. `explore_room(room=living_room_0_0)` → 9. `navigate(destination=toy_box)` → 10. `place(object=dropped_block, receptacle=toy_box)`

### belongs_on_floor（Task）

**情况**：勺子旁边还有垃圾桶、洗衣筐 → 它们本来就在地上，不动

**成功条件**：

- `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`
- `kitchen_bin`、`laundry_basket` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_counter_2/top)` → 2. `navigate(destination=dropped_spoon)` → 3. `pick(object=dropped_spoon)` → 4. `navigate(destination=kitchen_counter_2/top)` → 5. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.1, 7.6])`

### dropped_out_of_view（Task）

**情况**：勺子滑到隔壁餐厅地上，看不到 → 找一圈

**成功条件**：

- `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_counter_2/top)` → 2. `search(object=dropped_spoon, region=dining_room_0_1)` → 3. `navigate(destination=dropped_spoon)` → 4. `pick(object=dropped_spoon)` → 5. `navigate(destination=kitchen_counter_2/top)` → 6. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.1, 7.6])`

### only_this_room（Task）

**情况**：“厨房地上掉了东西”：客厅地上也有小车 → 只捡厨房的

**指令**：厨房地上掉了东西，帮忙捡起来放好。

**成功条件**：

- `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`
- `living_car` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_counter_2/top)` → 2. `navigate(destination=dropped_spoon)` → 3. `pick(object=dropped_spoon)` → 4. `navigate(destination=kitchen_counter_2/top)` → 5. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.1, 7.6])`

### dropped_in_two_rooms（Task）

**情况**：“家里地上掉了些东西”：厨房一把勺子，书房书桌下一支铅笔 → 都找到，勺子回台面，铅笔放回书桌（作业本旁）

**指令**：家里地上掉了些东西，帮忙捡起来放好。

**成功条件**：

- `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`
- `dropped_pencil` 在 `desk_1/top` 上
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_counter_2/top)` → 2. `navigate(destination=dropped_spoon)` → 3. `pick(object=dropped_spoon)` → 4. `navigate(destination=kitchen_counter_2/top)` → 5. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.1, 7.6])` → 6. `search(object=dropped_pencil, region=living_room_0_1)` → 7. `navigate(destination=dropped_pencil)` → 8. `pick(object=dropped_pencil)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=dropped_pencil, receptacle=desk_1/top, hint_xy=[-1.05, -5.95])`

---

## T24_snack_for_kid

> 孩子在书房写作业饿了，给他拿点吃的。

### apple_on_table（对照）

**情况**：餐桌上有苹果 → 送到书房书桌

**成功条件**：

- `snack_apple` 在 `desk_1/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.1, -5.95])`

### no_apples_for_him（Task）

**情况**：“他不爱吃苹果”：苹果和香蕉 → 拿香蕉

**指令**：孩子在书房写作业饿了，给他拿点吃的。他不爱吃苹果。

**成功条件**：

- `snack_banana` 在 `desk_1/top` 上
- `["not on", "snack_apple", "desk_1/top"]`
- 手里空着

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=snack_banana)` → 3. `pick(object=snack_banana)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=snack_banana, receptacle=desk_1/top, hint_xy=[-1.1, -5.95])`

### dinner_soon（Task）

**情况**：“还有半小时就吃晚饭了”：苹果和零食盒 → 拿苹果

**指令**：孩子在书房写作业饿了，给他拿点吃的。还有半小时就吃晚饭了。

**成功条件**：

- `snack_apple` 在 `desk_1/top` 上
- `snack_box` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=snack_apple)` → 3. `pick(object=snack_apple)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.1, -5.95])`

### fruit_out_of_view（Task）

**情况**：餐桌上没吃的，果篮在卧室书架上 → 找到果篮拿苹果

**成功条件**：

- `snack_apple` 在 `desk_1/top` 上
- 手里空着

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `search(object=home_basket, region=bedroom_0_1)` → 3. `navigate(destination=bookcase_2/top)` → 4. `look(target=bookcase_2/top)` → 5. `navigate(destination=snack_apple)` → 6. `pick(object=snack_apple)` → 7. `navigate(destination=desk_1/top)` → 8. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.1, -5.95])`

### where_is_he（Task）

**情况**：指令不说在哪：作业本摊在书房书桌或卧室书桌上 → 送到有作业的那张

**指令**：孩子写作业饿了，给他拿点吃的。

**成功条件**：

- 摆法 `study`：
  - `snack_apple` 在 `desk_1/top` 上
  - 手里空着
- 摆法 `bedroom`：
  - `snack_apple` 在 `desk_3/top` 上
  - 手里空着

**参考调用顺序**：

- 摆法 `study`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `look(target=desk_3/top)` → 6. `navigate(destination=desk_1/top)` → 7. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.1, -5.95])`
- 摆法 `bedroom`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `look(target=desk_1/top)` → 6. `navigate(destination=desk_3/top)` → 7. `place(object=snack_apple, receptacle=desk_3/top, hint_xy=[6.2, -5.5])`

### two_kids（Task）

**情况**：“孩子们在写作业”：两张书桌都有作业，苹果和香蕉 → 一人一个

**指令**：孩子们在写作业，饿了，给他们拿点吃的。

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `snack_apple` 在 `desk_1/top` 上
    - `snack_banana` 在 `desk_3/top` 上
  - 第 2 组：
    - `snack_banana` 在 `desk_1/top` 上
    - `snack_apple` 在 `desk_3/top` 上

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.1, -5.95])` → 7. `navigate(destination=snack_banana)` → 8. `pick(object=snack_banana)` → 9. `navigate(destination=desk_3/top)` → 10. `place(object=snack_banana, receptacle=desk_3/top, hint_xy=[6.2, -5.5])`

---

## T25_drink_for_guest

> 客人在客厅坐着，给他拿点喝的。

### drink_on_island（对照）

**情况**：岛台上一瓶果汁和一个杯子 → 都拿到电视柜

**成功条件**：

- `guest_juice` 在 `tv_stand_2/top` 上
- `guest_juice` 立着
- 这 7 件中至少 1 件还在 `tv_stand_2/top` 上：`guest_cup`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=guest_juice)` → 2. `pick(object=guest_juice)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 5. `navigate(destination=guest_cup)` → 6. `pick(object=guest_cup)` → 7. `navigate(destination=tv_stand_2/top)` → 8. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.55, 0.36])`

### cup_elsewhere（Task）

**情况**：岛台上只有果汁 → 想到要配杯子，去小厨房台面找

**成功条件**：

- `guest_juice` 在 `tv_stand_2/top` 上
- `guest_juice` 立着
- 这 6 件中至少 1 件还在 `tv_stand_2/top` 上：`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=guest_juice)` → 2. `pick(object=guest_juice)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 5. `search(object=cup_counter_b, region=kitchen_0_1)` → 6. `navigate(destination=cup_counter_b)` → 7. `pick(object=cup_counter_b)` → 8. `navigate(destination=tv_stand_2/top)` → 9. `place(object=cup_counter_b, receptacle=tv_stand_2/top, hint_xy=[7.55, 0.36])`

### cold_one（Task）

**情况**：“天很热”：岛台上一瓶常温的，冰箱里一瓶冰的 → 拿冰箱那瓶（开门、关门）

**指令**：天很热，客人在客厅坐着，给他拿点喝的。

**成功条件**：

- `cold_juice` 在 `tv_stand_2/top` 上
- `cold_juice` 立着
- 这 7 件中至少 1 件还在 `tv_stand_2/top` 上：`guest_cup`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
- `guest_juice` 没被挪动（离开局位置不超过 3 cm）
- `breakfast_fridge` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=breakfast_fridge/inside_shelf)` → 4. `look(target=breakfast_fridge/inside_shelf)` → 5. `navigate(destination=cold_juice)` → 6. `pick(object=cold_juice)` → 7. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 8. `close(articulated=breakfast_fridge)` → 9. `navigate(destination=tv_stand_2/top)` → 10. `place(object=cold_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 11. `navigate(destination=guest_cup)` → 12. `pick(object=guest_cup)` → 13. `navigate(destination=tv_stand_2/top)` → 14. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.55, 0.36])`

### drink_in_fridge（Task）

**情况**：外面没有饮料 → 想到饮料在冰箱里

**成功条件**：

- `cold_juice` 在 `tv_stand_2/top` 上
- `cold_juice` 立着
- 这 7 件中至少 1 件还在 `tv_stand_2/top` 上：`guest_cup`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
- `breakfast_fridge` 关着
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=breakfast_fridge)` → 3. `open(articulated=breakfast_fridge)` → 4. `navigate(destination=breakfast_fridge/inside_shelf)` → 5. `look(target=breakfast_fridge/inside_shelf)` → 6. `navigate(destination=cold_juice)` → 7. `pick(object=cold_juice)` → 8. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 9. `close(articulated=breakfast_fridge)` → 10. `navigate(destination=tv_stand_2/top)` → 11. `place(object=cold_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 12. `navigate(destination=guest_cup)` → 13. `pick(object=guest_cup)` → 14. `navigate(destination=tv_stand_2/top)` → 15. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.55, 0.36])`

### cups_for_two（Task）

**情况**：“两位客人在客厅，给他们准备好饮料和杯子，每人一个杯子。桌上已有的不用重复拿；普通杯不够时，可以用马克杯。”客人桌上已有 0–2 个杯子，关着的矮柜里有 1–2 个普通杯，家里别的杯子只有餐厅的马克杯 → 先看桌上缺几个 → 再开柜看库存：够就补普通杯；不够就拿柜里的，再去餐厅拿马克杯补齐；已经齐了就只送饮料。最后正好两个杯子，原有的不动，柜门关好

**指令**：两位客人在客厅，给他们准备好饮料和杯子，每人一个杯子。桌上已有的不用重复拿；普通杯不够时，可以用马克杯。

**成功条件**：

- 摆法 `none_one_inside`：
  - `guest_juice` 在 `tv_stand_2/top` 上
  - `guest_juice` 立着
  - 这 4 件中至少 2 件还在 `tv_stand_2/top` 上：`stock_cup_1`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
  - 这 4 件中最多 2 件在 `tv_stand_2/top` 上：`stock_cup_1`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
  - 这 1 件中至少 1 件还在 `tv_stand_2/top` 上：`stock_cup_1`
  - `kitchen_cabinet_4` 关着
  - 手里空着
- 摆法 `none_two_inside`：
  - `guest_juice` 在 `tv_stand_2/top` 上
  - `guest_juice` 立着
  - 这 5 件中至少 2 件还在 `tv_stand_2/top` 上：`stock_cup_1`、`stock_cup_2`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
  - 这 5 件中最多 2 件在 `tv_stand_2/top` 上：`stock_cup_1`、`stock_cup_2`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
  - 这 2 件中至少 2 件还在 `tv_stand_2/top` 上：`stock_cup_1`、`stock_cup_2`
  - `kitchen_cabinet_4` 关着
  - 手里空着
- 摆法 `one_there`：
  - `guest_juice` 在 `tv_stand_2/top` 上
  - `guest_juice` 立着
  - 这 5 件中至少 2 件还在 `tv_stand_2/top` 上：`tv_cup_1`、`stock_cup_1`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
  - 这 5 件中最多 2 件在 `tv_stand_2/top` 上：`tv_cup_1`、`stock_cup_1`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
  - 这 2 件中至少 2 件还在 `tv_stand_2/top` 上：`tv_cup_1`、`stock_cup_1`
  - `tv_cup_1` 没被挪动（离开局位置不超过 3 cm）
  - `kitchen_cabinet_4` 关着
  - 手里空着
- 摆法 `two_there`：
  - `guest_juice` 在 `tv_stand_2/top` 上
  - `guest_juice` 立着
  - 这 6 件中至少 2 件还在 `tv_stand_2/top` 上：`tv_cup_1`、`tv_cup_2`、`stock_cup_1`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
  - 这 6 件中最多 2 件在 `tv_stand_2/top` 上：`tv_cup_1`、`tv_cup_2`、`stock_cup_1`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
  - 这 3 件中至少 2 件还在 `tv_stand_2/top` 上：`tv_cup_1`、`tv_cup_2`、`stock_cup_1`
  - `tv_cup_1`、`tv_cup_2` 没被挪动（离开局位置不超过 3 cm）
  - `kitchen_cabinet_4` 关着
  - 手里空着

**参考调用顺序**：

- 摆法 `one_there`：1. `look(target=tv_stand_2/top)` → 2. `navigate(destination=guest_juice)` → 3. `pick(object=guest_juice)` → 4. `navigate(destination=tv_stand_2/top)` → 5. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 6. `navigate(destination=kitchen_cabinet_4)` → 7. `open(articulated=kitchen_cabinet_4)` → 8. `bend()` → 9. `explore_furniture(furniture=kitchen_cabinet_4)` → 10. `straighten()` → 11. `navigate(destination=stock_cup_1)` → 12. `pick(object=stock_cup_1)` → 13. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 14. `close(articulated=kitchen_cabinet_4)` → 15. `navigate(destination=tv_stand_2/top)` → 16. `place(object=stock_cup_1, receptacle=tv_stand_2/top, hint_xy=[7.55, 0.36])`
- 摆法 `none_one_inside`：1. `look(target=tv_stand_2/top)` → 2. `navigate(destination=guest_juice)` → 3. `pick(object=guest_juice)` → 4. `navigate(destination=tv_stand_2/top)` → 5. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 6. `navigate(destination=kitchen_cabinet_4)` → 7. `open(articulated=kitchen_cabinet_4)` → 8. `bend()` → 9. `explore_furniture(furniture=kitchen_cabinet_4)` → 10. `straighten()` → 11. `navigate(destination=stock_cup_1)` → 12. `pick(object=stock_cup_1)` → 13. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 14. `close(articulated=kitchen_cabinet_4)` → 15. `navigate(destination=tv_stand_2/top)` → 16. `place(object=stock_cup_1, receptacle=tv_stand_2/top, hint_xy=[7.55, 0.36])` → 17. `search(object=mug_shelf, region=dining_room_0_1)` → 18. `navigate(destination=mug_shelf)` → 19. `pick(object=mug_shelf)` → 20. `navigate(destination=tv_stand_2/top)` → 21. `place(object=mug_shelf, receptacle=tv_stand_2/top, hint_xy=[7.05, 0.36])`
- 摆法 `none_two_inside`：1. `look(target=tv_stand_2/top)` → 2. `navigate(destination=guest_juice)` → 3. `pick(object=guest_juice)` → 4. `navigate(destination=tv_stand_2/top)` → 5. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 6. `navigate(destination=kitchen_cabinet_4)` → 7. `open(articulated=kitchen_cabinet_4)` → 8. `bend()` → 9. `explore_furniture(furniture=kitchen_cabinet_4)` → 10. `straighten()` → 11. `navigate(destination=stock_cup_1)` → 12. `pick(object=stock_cup_1)` → 13. `navigate(destination=tv_stand_2/top)` → 14. `place(object=stock_cup_1, receptacle=tv_stand_2/top, hint_xy=[7.55, 0.36])` → 15. `navigate(destination=stock_cup_2)` → 16. `pick(object=stock_cup_2)` → 17. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 18. `close(articulated=kitchen_cabinet_4)` → 19. `navigate(destination=tv_stand_2/top)` → 20. `place(object=stock_cup_2, receptacle=tv_stand_2/top, hint_xy=[7.05, 0.36])`
- 摆法 `two_there`：1. `look(target=tv_stand_2/top)` → 2. `navigate(destination=guest_juice)` → 3. `pick(object=guest_juice)` → 4. `navigate(destination=tv_stand_2/top)` → 5. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])`

### two_guests（Task）

**情况**：“两位客人” → 两个杯子

**指令**：两位客人在客厅坐着，给他们拿点喝的。

**成功条件**：

- `guest_juice` 在 `tv_stand_2/top` 上
- `guest_juice` 立着
- 这 8 件中至少 2 件还在 `tv_stand_2/top` 上：`guest_cup`、`guest_cup_2`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=guest_juice)` → 2. `pick(object=guest_juice)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 5. `navigate(destination=guest_cup)` → 6. `pick(object=guest_cup)` → 7. `navigate(destination=tv_stand_2/top)` → 8. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.55, 0.36])` → 9. `navigate(destination=guest_cup_2)` → 10. `pick(object=guest_cup_2)` → 11. `navigate(destination=tv_stand_2/top)` → 12. `place(object=guest_cup_2, receptacle=tv_stand_2/top, hint_xy=[7.8, 0.36])`

### little_guest（Task）

**情况**：“来了个小朋友”：瓷杯和塑料杯 → 塑料杯

**指令**：来了个小朋友，在客厅坐着，给她拿点喝的。

**成功条件**：

- `guest_juice` 在 `tv_stand_2/top` 上
- `guest_juice` 立着
- 这 1 件中至少 1 件还在 `tv_stand_2/top` 上：`kid_cup`
- `guest_cup` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `navigate(destination=guest_juice)` → 2. `pick(object=guest_juice)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 5. `navigate(destination=kid_cup)` → 6. `pick(object=kid_cup)` → 7. `navigate(destination=tv_stand_2/top)` → 8. `place(object=kid_cup, receptacle=tv_stand_2/top, hint_xy=[7.55, 0.36])`

---

## T26_kids_things_to_room

> 把孩子落在客厅的东西拿回他房间。

### car_in_living_room（对照）

**情况**：小车在客厅地上 → 放进他卧室的玩具筐

**成功条件**：

- `living_car` 在 `kids_basket` 里
- 手里空着

**参考调用顺序**：

1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `pick(object=living_car)` → 4. `explore_room(room=bedroom_0_1)` → 5. `navigate(destination=kids_basket)` → 6. `place(object=living_car, receptacle=kids_basket)`

### whose（Task）

**情况**：电视柜上有孩子的绘本（和他书架上的一样）和大人的小说 → 只拿绘本，放他书架上

**成功条件**：

- `kid_book` 在 `bookcase_2/top` 上
- `adult_novel` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `look(target=tv_stand_2/top)` → 2. `navigate(destination=kid_book)` → 3. `pick(object=kid_book)` → 4. `navigate(destination=bookcase_2/top)` → 5. `place(object=kid_book, receptacle=bookcase_2/top, hint_xy=[1.12, -0.43])`

### scattered（Task）

**情况**：小车在地上、鸭子在电视柜、积木在岛台 → 都找到放进筐

**成功条件**：

- `living_car` 在 `kids_basket` 里
- `living_duck` 在 `kids_basket` 里
- `living_block` 在 `kids_basket` 里
- 手里空着

**参考调用顺序**：

1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `pick(object=living_car)` → 4. `explore_room(room=bedroom_0_1)` → 5. `navigate(destination=kids_basket)` → 6. `place(object=living_car, receptacle=kids_basket)` → 7. `navigate(destination=living_duck)` → 8. `pick(object=living_duck)` → 9. `navigate(destination=kids_basket)` → 10. `place(object=living_duck, receptacle=kids_basket)` → 11. `navigate(destination=living_block)` → 12. `pick(object=living_block)` → 13. `navigate(destination=kids_basket)` → 14. `place(object=living_block, receptacle=kids_basket)`

### where_in_room（Task）

**情况**：小车和绘本 → 小车进筐，绘本上书架

**成功条件**：

- `living_car` 在 `kids_basket` 里
- `kid_book` 在 `bookcase_2/top` 上
- 手里空着

**参考调用顺序**：

1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `pick(object=living_car)` → 4. `explore_room(room=bedroom_0_1)` → 5. `navigate(destination=kids_basket)` → 6. `place(object=living_car, receptacle=kids_basket)` → 7. `navigate(destination=kid_book)` → 8. `pick(object=kid_book)` → 9. `navigate(destination=bookcase_2/top)` → 10. `place(object=kid_book, receptacle=bookcase_2/top, hint_xy=[1.12, -0.43])`

### bear_to_bed（Task）

**情况**：“孩子要睡觉了”：小熊在电视柜 → 放到他床上，不放筐里

**指令**：孩子要睡觉了，把他落在客厅的东西拿回他房间。

**成功条件**：

- `living_bear` 在 `mattress_1/top` 上
- 手里空着

**参考调用顺序**：

1. `look(target=tv_stand_2/top)` → 2. `navigate(destination=living_bear)` → 3. `pick(object=living_bear)` → 4. `navigate(destination=mattress_1/top)` → 5. `place(object=living_bear, receptacle=mattress_1/top, hint_xy=[0.0, -4.0])`

### two_bedrooms（Task）

**情况**：两间卧室，有他玩具筐的那间是他的 → 认出来，把小车放进去

**成功条件**：

- `living_car` 在 `kids_basket` 里
- 手里空着

**参考调用顺序**：

- 摆法 `room_east`：1. `navigate(destination=living_car)` → 2. `pick(object=living_car)` → 3. `search(object=kids_basket, region=bedroom_0_1)` → 4. `navigate(destination=kids_basket)` → 5. `place(object=living_car, receptacle=kids_basket)`
- 摆法 `room_south`：1. `navigate(destination=living_car)` → 2. `pick(object=living_car)` → 3. `search(object=kids_basket, region=bedroom_0_0)` → 4. `navigate(destination=kids_basket)` → 5. `place(object=living_car, receptacle=kids_basket)`

---

## T27_leftovers_to_fridge

> 晚饭吃完了，把剩菜收进冰箱。

### rice_on_table（对照）

**情况**：餐桌上一盒剩饭 → 放进冰箱，关门

**成功条件**：

- `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
- `breakfast_fridge` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=leftover_rice)` → 6. `pick(object=leftover_rice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)`

### which_is_leftover（Task）

**情况**：剩饭和一个空外卖盒 → 只收剩饭

**成功条件**：

- `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
- `breakfast_fridge` 关着
- `["not on", "empty_tray", "breakfast_fridge/inside_shelf"]`
- 手里空着

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=breakfast_fridge)` → 3. `open(articulated=breakfast_fridge)` → 4. `navigate(destination=leftover_rice)` → 5. `pick(object=leftover_rice)` → 6. `navigate(destination=breakfast_fridge)` → 7. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 8. `close(articulated=breakfast_fridge)`

### two_leftovers（Task）

**情况**：剩饭和一锅剩汤 → 都收（汤可能还在灶上，不在桌上）

**成功条件**：

- `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
- `breakfast_fridge` 关着
- `leftover_soup` 在 `breakfast_fridge/inside_shelf` 上
- `leftover_soup` 立着
- 手里空着

**参考调用顺序**：

- 摆法 `soup_on_table`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=breakfast_fridge)` → 3. `open(articulated=breakfast_fridge)` → 4. `navigate(destination=leftover_rice)` → 5. `pick(object=leftover_rice)` → 6. `navigate(destination=breakfast_fridge)` → 7. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 8. `navigate(destination=leftover_soup)` → 9. `pick(object=leftover_soup)` → 10. `navigate(destination=breakfast_fridge)` → 11. `place(object=leftover_soup, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.98, 3.18])` → 12. `close(articulated=breakfast_fridge)`
- 摆法 `soup_on_stove`：1. `look(target=dining_table_2/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=leftover_rice)` → 6. `pick(object=leftover_rice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `navigate(destination=leftover_soup)` → 10. `pick(object=leftover_soup)` → 11. `navigate(destination=breakfast_fridge)` → 12. `place(object=leftover_soup, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.98, 3.18])` → 13. `close(articulated=breakfast_fridge)`

### still_eating（Task）

**情况**：一碗燕麦前摆着勺子，有人还在吃 → 不收，也不拿起来（过程要求），只收剩饭

**成功条件**：

- `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
- `breakfast_fridge` 关着
- `eating_bowl` 没被挪动（离开局位置不超过 3 cm）
- 过程要求：整局都没拿起过 `eating_bowl`（拆了再搭回去不算）
- 手里空着

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=breakfast_fridge)` → 3. `open(articulated=breakfast_fridge)` → 4. `navigate(destination=leftover_rice)` → 5. `pick(object=leftover_rice)` → 6. `navigate(destination=breakfast_fridge)` → 7. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 8. `close(articulated=breakfast_fridge)`

### fridge_out_of_view（Task）

**情况**：从餐厅出发，看不到冰箱 → 先找到冰箱

**成功条件**：

- `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
- `breakfast_fridge` 关着
- 手里空着

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `explore_room(room=living_room_0_0)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=leftover_rice)` → 6. `pick(object=leftover_rice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)`

### fruit_stays_out（Task）

**情况**：桌上还有果篮和麦片盒 → 不是剩菜，不进冰箱

**成功条件**：

- `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
- `breakfast_fridge` 关着
- `table_basket`、`table_cereal` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=breakfast_fridge)` → 3. `open(articulated=breakfast_fridge)` → 4. `navigate(destination=leftover_rice)` → 5. `pick(object=leftover_rice)` → 6. `navigate(destination=breakfast_fridge)` → 7. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 8. `close(articulated=breakfast_fridge)`

---

## T28_cup_to_bedside

> 孩子要睡了，把他的水杯拿到床边。

### cup_on_counter（对照）

**情况**：塑料杯在小厨房台面 → 放到他床边的矮书架上

**成功条件**：

- `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
- `kid_cup` 立着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=kid_cup)` → 4. `pick(object=kid_cup)` → 5. `navigate(destination=bookcase_3/top)` → 6. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.1, -4.88])`

### which_cup（Task）

**情况**：台面上有塑料杯、瓷杯、马克杯 → 认出塑料杯是孩子的

**成功条件**：

- `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
- `kid_cup` 立着
- `cup_counter_b`、`counter_mug` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_counter_2/top)` → 2. `navigate(destination=kid_cup)` → 3. `pick(object=kid_cup)` → 4. `navigate(destination=bookcase_3/top)` → 5. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.1, -4.88])`

### cup_put_away（Task）

**情况**：杯子收在矮柜里 → 打开找，拿出来关好

**成功条件**：

- `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
- `kid_cup` 立着
- `kitchen_cabinet_4` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `navigate(destination=kid_cup)` → 7. `pick(object=kid_cup)` → 8. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 9. `close(articulated=kitchen_cabinet_4)` → 10. `navigate(destination=bookcase_3/top)` → 11. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.1, -4.88])`

### which_bed（Task）

**情况**：两张床，他的床上有小熊 → 放到那张床边

**成功条件**：

- 摆法 `south`：
  - `kid_cup` 在 `cell_shelf_2/top` 上
  - `kid_cup` 立着
  - 手里空着
- 摆法 `east`：
  - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
  - `kid_cup` 立着
  - 手里空着

**参考调用顺序**：

- 摆法 `east`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=kid_cup)` → 4. `pick(object=kid_cup)` → 5. `look(target=mattress_2/top)` → 6. `navigate(destination=bookcase_3/top)` → 7. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.1, -4.88])`
- 摆法 `south`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=kid_cup)` → 4. `pick(object=kid_cup)` → 5. `look(target=mattress_1/top)` → 6. `navigate(destination=cell_shelf_2/top)` → 7. `place(object=kid_cup, receptacle=cell_shelf_2/top, hint_xy=[1.42, -10.8])`

### where_his_cup_is（Task）

**情况**：台面上有瓷杯和马克杯；他的塑料杯也在那儿，或者收在矮柜里 → 到台面看：有他的就拿；只有别人的 → 不能随便拿一个 → 打开矮柜找他的，拿出来关好门

**成功条件**：

- 摆法 `on_counter`：
  - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
  - `kid_cup` 立着
  - `cup_counter_b`、`counter_mug` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `in_cabinet`：
  - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
  - `kid_cup` 立着
  - `cup_counter_b`、`counter_mug` 没被挪动（离开局位置不超过 3 cm）
  - `kitchen_cabinet_4` 关着
  - 手里空着

**参考调用顺序**：

- 摆法 `on_counter`：1. `look(target=kitchen_counter_2/top)` → 2. `navigate(destination=kid_cup)` → 3. `pick(object=kid_cup)` → 4. `navigate(destination=bookcase_3/top)` → 5. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.1, -4.88])`
- 摆法 `in_cabinet`：1. `look(target=kitchen_counter_2/top)` → 2. `navigate(destination=kitchen_cabinet_4)` → 3. `open(articulated=kitchen_cabinet_4)` → 4. `bend()` → 5. `explore_furniture(furniture=kitchen_cabinet_4)` → 6. `straighten()` → 7. `navigate(destination=kid_cup)` → 8. `pick(object=kid_cup)` → 9. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 10. `close(articulated=kitchen_cabinet_4)` → 11. `navigate(destination=bookcase_3/top)` → 12. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.1, -4.88])`

### cup_out_of_view（Task）

**情况**：杯子落在餐桌上，看不到 → 先找

**成功条件**：

- `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
- `kid_cup` 立着
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_counter_2/top)` → 2. `search(object=kid_cup, region=dining_room_0_1)` → 3. `navigate(destination=kid_cup)` → 4. `pick(object=kid_cup)` → 5. `navigate(destination=bookcase_3/top)` → 6. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.1, -4.88])`

### already_there（Task）

**情况**：杯子已经在他床边 → 什么都不用做

**成功条件**：

- `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
- `kid_cup` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `navigate(destination=bookcase_3/top)` → 2. `look(target=bookcase_3/top)`

---

## T29_clear_table_for_dinner

> 要吃饭了，把餐桌上不该放的东西拿走。

### car_on_table（对照）

**情况**：餐桌上一辆玩具车 → 放回客厅的玩具箱

**成功条件**：

- `table_car` 在 `toy_box` 里
- 手里空着

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=table_car)` → 3. `pick(object=table_car)` → 4. `navigate(destination=toy_box)` → 5. `place(object=table_car, receptacle=toy_box)`

### belongs_on_table（Task）

**情况**：还摆着碗和勺子 → 吃饭用的留下，只拿走玩具

**成功条件**：

- `table_car` 在 `toy_box` 里
- `set_bowl`、`set_spoon` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=table_car)` → 3. `pick(object=table_car)` → 4. `navigate(destination=toy_box)` → 5. `place(object=table_car, receptacle=toy_box)`

### homework_on_table（Task）

**情况**：作业本和铅笔 → 拿回书房书桌

**成功条件**：

- `hw_notebook` 在 `desk_1/top` 上
- `hw_pencil` 在 `desk_1/top` 上
- 手里空着

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=hw_notebook)` → 3. `pick(object=hw_notebook)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=hw_notebook, receptacle=desk_1/top, hint_xy=[-0.7, -5.95])` → 6. `navigate(destination=hw_pencil)` → 7. `pick(object=hw_pencil)` → 8. `navigate(destination=desk_1/top)` → 9. `place(object=hw_pencil, receptacle=desk_1/top, hint_xy=[-0.35, -5.95])`

### several（Task）

**情况**：玩具车、一本书、一个空罐子 → 玩具箱 / 书架 / 垃圾桶

**成功条件**：

- `table_car` 在 `toy_box` 里
- `empty_can` 在 `trash_can` 里
- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `table_book` 在 `bookcase_2/top` 上
  - 第 2 组：
    - `table_book` 在 `bookcase_3/top` 上
  - 第 3 组：
    - `table_book` 在 `large_shelf_2/shelf_1` 上
  - 第 4 组：
    - `table_book` 在 `large_shelf_2/shelf_2` 上

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=table_car)` → 3. `pick(object=table_car)` → 4. `navigate(destination=toy_box)` → 5. `place(object=table_car, receptacle=toy_box)` → 6. `navigate(destination=empty_can)` → 7. `pick(object=empty_can)` → 8. `navigate(destination=trash_can)` → 9. `drop(object=empty_can, container=trash_can)` → 10. `navigate(destination=table_book)` → 11. `pick(object=table_book)` → 12. `navigate(destination=bookcase_2/top)` → 13. `place(object=table_book, receptacle=bookcase_2/top, hint_xy=[1.0, -0.43])`

### nothing_to_clear（Task）

**情况**：桌上只有餐具 → 什么都不用做

**成功条件**：

- `set_bowl`、`set_spoon` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)`

### which_table（Task）

**情况**：两张桌上各有个玩具，汤锅在其中一张 → 只清要吃饭的那张

**成功条件**：

- 摆法 `east`：
  - `toy_east` 在 `toy_box` 里
  - `toy_west` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `west`：
  - `toy_west` 在 `toy_box` 里
  - `toy_east` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着

**参考调用顺序**：

- 摆法 `east`：1. `look(target=dining_table_2/top)` → 2. `look(target=dining_table_1/top)` → 3. `navigate(destination=toy_east)` → 4. `pick(object=toy_east)` → 5. `navigate(destination=toy_box)` → 6. `place(object=toy_east, receptacle=toy_box)`
- 摆法 `west`：1. `look(target=dining_table_2/top)` → 2. `look(target=dining_table_1/top)` → 3. `navigate(destination=toy_west)` → 4. `pick(object=toy_west)` → 5. `navigate(destination=toy_box)` → 6. `place(object=toy_west, receptacle=toy_box)`

---

## T30_bowls_for_soup

> 汤快好了，拿碗过来准备盛。

### bowl_on_cabinet（对照）

**情况**：靠墙矮柜上一个干净碗 → 拿到岛台

**成功条件**：

- 这 5 件中至少 1 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=soup_bowl_1)` → 2. `pick(object=soup_bowl_1)` → 3. `navigate(destination=kitchen_island/top)` → 4. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[8.05, 1.75])`

### how_many（Task）

**情况**：餐桌上摆了三把勺子 → 拿三个碗

**成功条件**：

- 这 7 件中至少 3 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`、`soup_bowl_3`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
- 手里空着

**参考调用顺序**：

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=soup_bowl_1)` → 3. `pick(object=soup_bowl_1)` → 4. `navigate(destination=kitchen_island/top)` → 5. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[7.65, 1.75])` → 6. `navigate(destination=soup_bowl_2)` → 7. `pick(object=soup_bowl_2)` → 8. `navigate(destination=kitchen_island/top)` → 9. `place(object=soup_bowl_2, receptacle=kitchen_island/top, hint_xy=[7.85, 1.75])` → 10. `navigate(destination=soup_bowl_3)` → 11. `pick(object=soup_bowl_3)` → 12. `navigate(destination=kitchen_island/top)` → 13. `place(object=soup_bowl_3, receptacle=kitchen_island/top, hint_xy=[8.05, 1.75])`

### bowls_in_cabinet（Task）

**情况**：“汤快好了，拿碗过来准备盛；碗不够的话，马克杯也行。”餐桌摆了三把勺子；矮柜上一个碗和一个马克杯；柜里还有两个碗，或者只有一个；家里没有别的碗 → 要三个 → 外面只有一个，打开柜子 → 两个碗：拿三个碗；一个碗：两碗加马克杯（马克杯能盛汤，盘子不行），关门

**指令**：汤快好了，拿碗过来准备盛；碗不够的话，马克杯也行。

**成功条件**：

- 摆法 `two_inside`：
  - 这 3 件中至少 3 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`、`soup_bowl_3`
  - `kitchen_cabinet_6` 关着
  - 手里空着
- 摆法 `one_inside`：
  - 这 2 件中至少 2 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`
  - 这 9 件中至少 3 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`、`spare_mug`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
  - `kitchen_cabinet_6` 关着
  - 手里空着

**参考调用顺序**：

- 摆法 `two_inside`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=soup_bowl_1)` → 3. `pick(object=soup_bowl_1)` → 4. `navigate(destination=kitchen_island/top)` → 5. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[7.65, 1.75])` → 6. `navigate(destination=kitchen_cabinet_6)` → 7. `open(articulated=kitchen_cabinet_6)` → 8. `bend()` → 9. `explore_furniture(furniture=kitchen_cabinet_6)` → 10. `straighten()` → 11. `navigate(destination=soup_bowl_2)` → 12. `pick(object=soup_bowl_2)` → 13. `navigate(destination=kitchen_island/top)` → 14. `place(object=soup_bowl_2, receptacle=kitchen_island/top, hint_xy=[7.85, 1.75])` → 15. `navigate(destination=soup_bowl_3)` → 16. `pick(object=soup_bowl_3)` → 17. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 18. `close(articulated=kitchen_cabinet_6)` → 19. `navigate(destination=kitchen_island/top)` → 20. `place(object=soup_bowl_3, receptacle=kitchen_island/top, hint_xy=[8.05, 1.75])`
- 摆法 `one_inside`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=soup_bowl_1)` → 3. `pick(object=soup_bowl_1)` → 4. `navigate(destination=kitchen_island/top)` → 5. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[7.65, 1.75])` → 6. `navigate(destination=kitchen_cabinet_6)` → 7. `open(articulated=kitchen_cabinet_6)` → 8. `bend()` → 9. `explore_furniture(furniture=kitchen_cabinet_6)` → 10. `straighten()` → 11. `navigate(destination=soup_bowl_2)` → 12. `pick(object=soup_bowl_2)` → 13. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 14. `close(articulated=kitchen_cabinet_6)` → 15. `navigate(destination=kitchen_island/top)` → 16. `place(object=soup_bowl_2, receptacle=kitchen_island/top, hint_xy=[7.85, 1.75])` → 17. `navigate(destination=spare_mug)` → 18. `pick(object=spare_mug)` → 19. `navigate(destination=kitchen_island/top)` → 20. `place(object=spare_mug, receptacle=kitchen_island/top, hint_xy=[8.05, 1.75])`

### clean_one（Task）

**情况**：一个碗里还有燕麦，一个空的 → 拿空的

**成功条件**：

- 这 5 件中至少 1 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
- `full_bowl` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_cabinet_6/top)` → 2. `navigate(destination=soup_bowl_1)` → 3. `pick(object=soup_bowl_1)` → 4. `navigate(destination=kitchen_island/top)` → 5. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[8.05, 1.75])`

### bowl_put_away（Task）

**情况**：碗收在矮柜里 → 打开找，拿出来关好

**成功条件**：

- 这 5 件中至少 1 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
- `kitchen_cabinet_4` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `navigate(destination=soup_bowl_1)` → 7. `pick(object=soup_bowl_1)` → 8. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 9. `close(articulated=kitchen_cabinet_4)` → 10. `navigate(destination=kitchen_island/top)` → 11. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[8.05, 1.75])`

### no_bowl（Task）

**情况**：家里没有干净碗了，柜上有马克杯和盘子 → 拿马克杯（能盛汤）

**成功条件**：

- 这 7 件中至少 1 件还在 `kitchen_island/top` 上：`spare_mug`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_cabinet_6/top)` → 2. `navigate(destination=spare_mug)` → 3. `pick(object=spare_mug)` → 4. `navigate(destination=kitchen_island/top)` → 5. `place(object=spare_mug, receptacle=kitchen_island/top, hint_xy=[8.05, 1.75])`

### bowl_not_plate（Task）

**情况**：柜上有盘子和碗 → 拿碗

**成功条件**：

- 这 5 件中至少 1 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
- `spare_plate` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_cabinet_6/top)` → 2. `navigate(destination=soup_bowl_1)` → 3. `pick(object=soup_bowl_1)` → 4. `navigate(destination=kitchen_island/top)` → 5. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[8.05, 1.75])`

