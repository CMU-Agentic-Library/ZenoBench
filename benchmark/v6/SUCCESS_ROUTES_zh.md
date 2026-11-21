# ZenoBench v6：每个 variant 的成功条件和参考调用顺序

由 `python benchmark/v6/success_routes.py` 从 `tasks.json` 生成。

- **成功条件**：一局结束时由 GT 状态判定，全部满足才算成功；中间怎么做不限。
- **参考调用顺序**：oracle 路线，即按技能 contract 调用、能走通的一种做法，不是唯一解。标"（补救）"的是发现情况后多做的一步。机器人只会右手。
- 有多种摆法的 variant 每种摆法列一条路线，seed 决定用哪种摆法。
- 物体名保留代码里的 id。

---

## T01_book_to_dining_table

> 把岛台上那本书拿到餐桌，吃早饭时接着看。

### overhang_ready（对照）

**情况**：书已经探出岛台边缘约 6 cm → 直接抓起送到餐桌

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `paperback_book` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
  - 手里空着
- **不行（0）**：书放在别处（茶几、岛台、台面、地上），或还拿在手里


**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.5])`

### table_seats（Action + Task）

**情况**：指令要求把书放在某位客人吃饭的位置旁边、和餐具留出空隙，但没说是哪个空位。餐桌东侧摆了三人份早餐（每个座位一个盘子或碗加一个杯子，另有两盒麦片），桌边有好几个空位：两套餐具之间的窄缝（放得下但会挨着餐具）、麦片外侧桌子尽头的大空地（离座位远），还有一个座位旁边够宽的空位 → 看清桌面，自己判断哪个空位既在客人座位旁边、又放得下、和餐具留得出空隙，放在那里

**指令**：早餐摆好了，把岛台上的书在餐桌上放好，方便客人边吃边看，别影响用餐。其他东西别动。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `paperback_book` 在 `dining_table_2/top` 上
  - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - `paperback_book` 离其中至少一个不超过 15 cm：`bowl_side_table`、`plate_counter_a`、`plate_counter_b`
  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
  - 手里空着
- **次好（0.6）**：

  - `paperback_book` 在 `dining_table_2/top` 上
  - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
  - 手里空着
- **最不好（0.3）**：

  - `paperback_book` 在 `dining_table_2/top` 上
  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
  - 手里空着
- **不行（0）**：放到另一张没摆早餐的餐桌；为腾地方挪了或碰倒了餐具；放在别处或还拿在手里


**参考调用顺序**：

- 摆法 `seats_a`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.059])`
- 摆法 `seats_b`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.138])`
- 摆法 `seats_c`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.35])`
- 摆法 `seats_a_flat`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.059])`
- 摆法 `seats_b_flat`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.138])`
- 摆法 `seats_c_flat`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.35])`

### which_table（Action + Task）

**情况**：家里有两张餐桌（近的在隔壁餐厅约 6 m，远的在西边另一间餐厅约 16 m），早餐只摆在其中一张上（三人份，和 table_seats 一样只有一个座位旁的合适空位），另一张上是孩子的积木和储物箱，桌边也有空位；指令只说放到客人吃饭的那张桌子上 → 先到近桌看，没摆早餐就改去另一间餐厅，在摆了早餐的桌子上选座位旁的空位放下；放到另一张桌子上算失败

**指令**：客人正在吃早饭，把岛台上的书放到他们桌上，方便边吃边看，别影响用餐。其他东西别动。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **次好（0.6）**：

  - 摆法 `far_a`、`far_b`、`far_a_flat`、`far_b_flat`：
    - `paperback_book` 在 `dining_table_1/top` 上
    - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`spoon_target_table`
    - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`spoon_target_table`、`wide_storage_bin`、`clutter_cereal_b`、`wooden_block_a`、`wooden_block_b` 没被挪动（离开局位置不超过 3 cm）
    - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a` 立着
    - 手里空着
  - 摆法 `near_a`、`near_b`、`near_a_flat`、`near_b_flat`：
    - `paperback_book` 在 `dining_table_2/top` 上
    - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
    - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`、`wide_storage_bin`、`wooden_block_a`、`wooden_block_b` 没被挪动（离开局位置不超过 3 cm）
    - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
    - 手里空着
- **最不好（0.3）**：

  - 摆法 `far_a`、`far_b`、`far_a_flat`、`far_b_flat`：
    - `paperback_book` 在 `dining_table_1/top` 上
    - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`spoon_target_table`、`wide_storage_bin`、`clutter_cereal_b`、`wooden_block_a`、`wooden_block_b` 没被挪动（离开局位置不超过 3 cm）
    - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a` 立着
    - 手里空着
  - 摆法 `near_a`、`near_b`、`near_a_flat`、`near_b_flat`：
    - `paperback_book` 在 `dining_table_2/top` 上
    - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`、`wide_storage_bin`、`wooden_block_a`、`wooden_block_b` 没被挪动（离开局位置不超过 3 cm）
    - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
    - 手里空着
- **不行（0）**：放到放玩具的那张桌（找错桌）；挪了或碰倒餐具；放在别处或还拿在手里


**参考调用顺序**：

- 摆法 `near_a`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.059])`
- 摆法 `near_b`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.138])`
- 摆法 `far_a`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `navigate(destination=dining_table_1/top)` → 9. `look(target=dining_table_1/top)` → 10. `place(object=paperback_book, receptacle=dining_table_1/top, hint_xy=[-7.607, 8.179])`
- 摆法 `far_b`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `navigate(destination=dining_table_1/top)` → 9. `look(target=dining_table_1/top)` → 10. `place(object=paperback_book, receptacle=dining_table_1/top, hint_xy=[-7.607, 7.508])`
- 摆法 `near_a_flat`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.059])`
- 摆法 `near_b_flat`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.138])`
- 摆法 `far_a_flat`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `navigate(destination=dining_table_1/top)` → 10. `look(target=dining_table_1/top)` → 11. `place(object=paperback_book, receptacle=dining_table_1/top, hint_xy=[-7.607, 8.179])`
- 摆法 `far_b_flat`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `navigate(destination=dining_table_1/top)` → 10. `look(target=dining_table_1/top)` → 11. `place(object=paperback_book, receptacle=dining_table_1/top, hint_xy=[-7.607, 7.508])`

### no_room_fallback（Action + Task）

**情况**：和 table_seats 一样的三人份早餐；指令加了约束：餐具和麦片都别动，桌上没有合适位置就把书放到书柜收起来（家里四个书柜，哪个、哪层都算） → 先看桌子：有座位旁的合适空位就放那里（这时放书柜算失败）；唯一的宽空位被一盒麦片占着时，按指令放进书柜（参考路线：卧室的书柜，最近）（挪麦片腾位置算失败）

**指令**：把岛台上的书在餐桌上放好，方便客人边吃边看，别影响用餐；实在没合适的位置，就先收进书柜。其他东西别动。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `seats_b`、`seats_c`、`seats_b_flat`、`seats_c_flat`：
    - `paperback_book` 在 `dining_table_2/top` 上
    - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
    - `paperback_book` 离其中至少一个不超过 15 cm：`bowl_side_table`、`plate_counter_a`、`plate_counter_b`
    - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
    - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
    - 手里空着
  - 摆法 `full_a`、`full_a_flat`：
    - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
    - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `paperback_book` 在 `bookcase_1/top` 上
      - 第 2 组：
        - `paperback_book` 在 `bookcase_1/shelf_1` 上
      - 第 3 组：
        - `paperback_book` 在 `bookcase_1/shelf_0` 上
      - 第 4 组：
        - `paperback_book` 在 `bookcase_2/top` 上
      - 第 5 组：
        - `paperback_book` 在 `bookcase_2/shelf_1` 上
      - 第 6 组：
        - `paperback_book` 在 `bookcase_2/shelf_0` 上
      - 第 7 组：
        - `paperback_book` 在 `bookcase_3/top` 上
      - 第 8 组：
        - `paperback_book` 在 `bookcase_3/shelf_1` 上
      - 第 9 组：
        - `paperback_book` 在 `bookcase_3/shelf_0` 上
      - 第 10 组：
        - `paperback_book` 在 `bookcase_4/top` 上
      - 第 11 组：
        - `paperback_book` 在 `bookcase_4/shelf_1` 上
      - 第 12 组：
        - `paperback_book` 在 `bookcase_4/shelf_0` 上
- **次好（0.6）**：

  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
  - 手里空着
  - `paperback_book` 在 `dining_table_2/top` 上
  - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
- **最不好（0.3）**：

  - 摆法 `full_a`、`full_a_flat`：
    - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
    - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
    - 手里空着
    - `paperback_book` 在 `dining_table_2/top` 上
  - 摆法 `seats_b`、`seats_c`、`seats_b_flat`、`seats_c_flat`：
    - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
    - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `paperback_book` 在 `dining_table_2/top` 上
      - 第 2 组：
        - `paperback_book` 在 `bookcase_1/top` 上
      - 第 3 组：
        - `paperback_book` 在 `bookcase_1/shelf_1` 上
      - 第 4 组：
        - `paperback_book` 在 `bookcase_1/shelf_0` 上
      - 第 5 组：
        - `paperback_book` 在 `bookcase_2/top` 上
      - 第 6 组：
        - `paperback_book` 在 `bookcase_2/shelf_1` 上
      - 第 7 组：
        - `paperback_book` 在 `bookcase_2/shelf_0` 上
      - 第 8 组：
        - `paperback_book` 在 `bookcase_3/top` 上
      - 第 9 组：
        - `paperback_book` 在 `bookcase_3/shelf_1` 上
      - 第 10 组：
        - `paperback_book` 在 `bookcase_3/shelf_0` 上
      - 第 11 组：
        - `paperback_book` 在 `bookcase_4/top` 上
      - 第 12 组：
        - `paperback_book` 在 `bookcase_4/shelf_1` 上
      - 第 13 组：
        - `paperback_book` 在 `bookcase_4/shelf_0` 上
- **不行（0）**：挪了或碰倒餐具、麦片腾地方；放在别处或还拿在手里


**参考调用顺序**：

- 摆法 `seats_b`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.138])`
- 摆法 `seats_c`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.35])`
- 摆法 `full_a`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `navigate(destination=bookcase_2/top)` → 9. `place(object=paperback_book, receptacle=bookcase_2/top, hint_xy=[1.15, -0.43])`
- 摆法 `seats_b_flat`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.138])`
- 摆法 `seats_c_flat`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.35])`
- 摆法 `full_a_flat`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `navigate(destination=bookcase_2/top)` → 10. `place(object=paperback_book, receptacle=bookcase_2/top, hint_xy=[1.15, -0.43])`

### reader_seat（Action + Task）

**情况**：三个座位旁边都有够宽的空位；其中一个座位的饮料是马克杯，另外两个是没把手的杯子；指令说书是"早上用带把手的马克杯喝咖啡的那位客人"的（另外两位用没把手的杯子） → 从桌上认出用马克杯的座位，把书放在那个座位旁边（离它的盘子或马克杯不超过 15 cm，离别的座位的盘子超过 15 cm）

**指令**：用马克杯喝咖啡的客人想边吃早饭边看岛台上那本书，帮他在餐桌上放好，别影响用餐。其他东西别动。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **次好（0.6）**：

  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
  - 手里空着
  - `paperback_book` 在 `dining_table_2/top` 上
  - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - `paperback_book` 离这些都超过 15 cm：`bowl_side_table`、`plate_counter_a`、`plate_counter_b`
- **最不好（0.3）**：

  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
  - 手里空着
  - `paperback_book` 在 `dining_table_2/top` 上
- **不行（0）**：挪了或碰倒餐具；放在别处（包括另一张餐桌）或还拿在手里


**参考调用顺序**：

- 摆法 `mug_1`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 5.69])`
- 摆法 `mug_2`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.428])`
- 摆法 `mug_3`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.094])`
- 摆法 `mug_1_flat`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 5.69])`
- 摆法 `mug_2_flat`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.428])`
- 摆法 `mug_3_flat`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)` → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.094])`

### which_book（Task）

**情况**：岛台上有一本书（不是要找的）；指令不说房间，只说客人昨晚在干什么（看电视时翻的，或睡前读的），书就留在那个房间；另一个房间也有一本别的书 → 由“看电视”推出客厅、由“睡前”推出卧室，去那里拿那本送到餐桌；拿错书（替换）算次好，对的书加多拿或挪了别的书算最不好

**指令**：客人想吃早饭时接着看昨晚看电视时翻的那本书，帮忙拿到餐桌上。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `paperback_book` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
  - `book_island`、`book_other` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- **次好（0.6）**：

  - `paperback_book` 不在其中任何一处上：`dining_table_2/top`、`dining_table_1/top`
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `book_island` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
    - 第 2 组：
      - `book_other` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
- **最不好（0.3）**：

  - `paperback_book` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
  - 手里空着
- **不行（0）**：餐桌上一本书都没有；还拿在手里


**参考调用顺序**：

- 摆法 `living`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=paperback_book)` → 6. `look(target=paperback_book)` → 7. `pick(object=paperback_book)` → 8. `navigate(destination=dining_table_2/top)` → 9. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.5])`
- 摆法 `bedroom`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=bookcase_2/top)` → 4. `look(target=bookcase_2/top)` → 5. `navigate(destination=paperback_book)` → 6. `look(target=paperback_book)` → 7. `pick(object=paperback_book)` → 8. `navigate(destination=dining_table_2/top)` → 9. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.5])`

---

## T02_stack_blocks

> 收拾孩子落在岛台上的积木：把一块木积木叠到另一块上面。

### clear（对照）

**情况**：两块积木相距 30 cm → 拿 B 叠到 A 上

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_b` 叠在 `wooden_block_a` 上
    - 第 2 组：
      - `wooden_block_a` 叠在 `wooden_block_b` 上
- **不行（0）**：没叠上，或积木掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_b)` → 4. `pick(object=wooden_block_b)` → 5. `rotate(object=wooden_block_b, degrees=30)` → 6. `navigate(destination=wooden_block_a)` → 7. `stack(object=wooden_block_b, base=wooden_block_a)`

### crowded_use_another（Task）

**情况**：积木 B 被满满一碗燕麦和擀面杖夹住（缝只有 3 mm）；指令只说碗盛得很满、别碰它周围的东西，没点名哪块积木被夹住，也没说家里别处还有积木 → 先看 B：夹紧了就不拨它，去找另一块积木和 A 叠在一起，B、碗、擀面杖都不动；B 没被夹住就直接叠岛台上的两块，另一块不动

**指令**：把孩子的两块木积木叠起来。岛台上那碗燕麦盛得很满，别碰它周围的东西，免得洒出来。

**成功条件**（D 按摆法：`tight_tv` D = 1、理想物不在，`tight_dining` D = 1、理想物不在，`loose` D = 1、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
    - `oatmeal`、`rolling_pin` 没被挪动（离开局位置不超过 2 cm）
    - `oatmeal` 立着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
      - 第 2 组：
        - `wooden_block_a` 叠在 `floor_block` 上
      - 第 3 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
      - 第 4 组：
        - `wooden_block_b` 叠在 `floor_block` 上
      - 第 5 组：
        - `floor_block` 叠在 `wooden_block_a` 上
      - 第 6 组：
        - `floor_block` 叠在 `wooden_block_b` 上
- **最不好（0.3）**：

  - `oatmeal`、`rolling_pin` 没被挪动（离开局位置不超过 2 cm）
  - `oatmeal` 立着
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_a` 叠在 `wooden_block_b` 上
    - 第 2 组：
      - `wooden_block_a` 叠在 `floor_block` 上
    - 第 3 组：
      - `wooden_block_b` 叠在 `wooden_block_a` 上
    - 第 4 组：
      - `wooden_block_b` 叠在 `floor_block` 上
    - 第 5 组：
      - `floor_block` 叠在 `wooden_block_a` 上
    - 第 6 组：
      - `floor_block` 叠在 `wooden_block_b` 上
- **不行（0）**：碗或擀面杖动了、碗倒了；没叠上


**参考调用顺序**：

- 摆法 `tight_tv`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_b)` → 4. `look(target=wooden_block_b)` → 5. `search(object=floor_block, region=living_room_0_0)` → 6. `navigate(destination=floor_block)` → 7. `pick(object=floor_block)` → 8. `navigate(destination=wooden_block_a)` → 9. `stack(object=floor_block, base=wooden_block_a)`
- 摆法 `tight_dining`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_b)` → 4. `look(target=wooden_block_b)` → 5. `search(object=floor_block, region=dining_room_0_1)` → 6. `navigate(destination=floor_block)` → 7. `pick(object=floor_block)` → 8. `navigate(destination=wooden_block_a)` → 9. `stack(object=floor_block, base=wooden_block_a)`
- 摆法 `loose`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_b)` → 4. `pick(object=wooden_block_b)` → 5. `rotate(object=wooden_block_b, degrees=30)` → 6. `navigate(destination=wooden_block_a)` → 7. `stack(object=wooden_block_b, base=wooden_block_a)`

### third_toy_elsewhere（Task）

**情况**：指令只说用孩子的玩具在岛台上搭一座三层的小塔；家里只有两块积木（都在岛台上），旁边的海绵大小像积木但不是玩具；孩子别的玩具在别的房间、开局看不到 → 不能只叠两块就停，也不能拿海绵凑数：先叠好两块，去别的房间找一个玩具当第三层（鸭子没有平顶，只能放最上面）

**指令**：用孩子的玩具在岛台上搭一座三层的小塔。

**成功条件**（D 按摆法：`duck` D = 1、理想物不在，`toy_block` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **最不好（0.3）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_b` 叠在 `wooden_block_a` 上
      - `kitchen_sponge` 叠在 `wooden_block_b` 上
      - `wooden_block_a` 在 `kitchen_island/top` 上
    - 第 2 组：
      - `kitchen_sponge` 叠在 `wooden_block_a` 上
      - `wooden_block_b` 叠在 `kitchen_sponge` 上
      - `wooden_block_a` 在 `kitchen_island/top` 上
    - 第 3 组：
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `kitchen_sponge` 叠在 `wooden_block_a` 上
      - `wooden_block_b` 在 `kitchen_island/top` 上
    - 第 4 组：
      - `kitchen_sponge` 叠在 `wooden_block_b` 上
      - `wooden_block_a` 叠在 `kitchen_sponge` 上
      - `wooden_block_b` 在 `kitchen_island/top` 上
    - 第 5 组：
      - `wooden_block_a` 叠在 `kitchen_sponge` 上
      - `wooden_block_b` 叠在 `wooden_block_a` 上
      - `kitchen_sponge` 在 `kitchen_island/top` 上
    - 第 6 组：
      - `wooden_block_b` 叠在 `kitchen_sponge` 上
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `kitchen_sponge` 在 `kitchen_island/top` 上
- **不行（0）**：只叠了两层（没找到第三件）；没叠上；塔不在岛台上


**参考调用顺序**：

- 摆法 `duck`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_b)` → 4. `pick(object=wooden_block_b)` → 5. `rotate(object=wooden_block_b, degrees=30)` → 6. `navigate(destination=wooden_block_a)` → 7. `stack(object=wooden_block_b, base=wooden_block_a)` → 8. `search(object=rubber_duck, region=dining_room_0_1)`（补救） → 9. `navigate(destination=rubber_duck)`（补救） → 10. `pick(object=rubber_duck)`（补救） → 11. `navigate(destination=wooden_block_a)`（补救） → 12. `stack(object=rubber_duck, base=wooden_block_b)`（补救）
- 摆法 `toy_block`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_b)` → 4. `pick(object=wooden_block_b)` → 5. `rotate(object=wooden_block_b, degrees=30)` → 6. `navigate(destination=wooden_block_a)` → 7. `stack(object=wooden_block_b, base=wooden_block_a)` → 8. `search(object=toy_block, region=kitchen_0_1)`（补救） → 9. `navigate(destination=toy_block)`（补救） → 10. `pick(object=toy_block)`（补救） → 11. `navigate(destination=wooden_block_a)`（补救） → 12. `stack(object=toy_block, base=wooden_block_b)`（补救）

### tower_for_kid（Task）

**情况**：（11-17 改成换地方的替换）孩子坐在近处餐桌，想看积木塔；三块积木分散在家里（一块开局看不到）→ 找全三块搭塔。搭在哪按位置定档：近处餐桌（孩子那张）好；近处餐桌堆满了就搭到西边餐厅的另一张餐桌，次好；两张餐桌都堆满就只能搭在不是餐桌的台面（如岛台），最不好。离桌边和桌上东西都要 10 cm，桌上东西不能挪

**指令**：孩子想在餐桌上看积木塔。把家里三块积木都找到，在餐桌上叠成一座塔。

**成功条件**（D 按摆法：`counter` D = 1、理想物在，`study` D = 1、理想物在，`near_full` D = 1、理想物不在，`both_full` D = 0、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `near_full`、`both_full`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `counter`、`study`：
    - `wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`、`bowl_side_table`、`cup_side_table`、`spoon_side_table` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 在其中任一处上：`dining_table_2/top`
        - `wooden_block_a` 离台面边缘至少 10 cm
        - `wooden_block_a` 离这些东西都至少 10 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
      - 第 2 组：
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 在其中任一处上：`dining_table_2/top`
        - `wooden_block_a` 离台面边缘至少 10 cm
        - `wooden_block_a` 离这些东西都至少 10 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
      - 第 3 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 在其中任一处上：`dining_table_2/top`
        - `wooden_block_b` 离台面边缘至少 10 cm
        - `wooden_block_b` 离这些东西都至少 10 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
      - 第 4 组：
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 在其中任一处上：`dining_table_2/top`
        - `wooden_block_b` 离台面边缘至少 10 cm
        - `wooden_block_b` 离这些东西都至少 10 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
      - 第 5 组：
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 在其中任一处上：`dining_table_2/top`
        - `floor_block` 离台面边缘至少 10 cm
        - `floor_block` 离这些东西都至少 10 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
      - 第 6 组：
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 在其中任一处上：`dining_table_2/top`
        - `floor_block` 离台面边缘至少 10 cm
        - `floor_block` 离这些东西都至少 10 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
- **次好（0.6）**：

  - 摆法 `both_full`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `counter`、`study`：
    - `wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`、`bowl_side_table`、`cup_side_table`、`spoon_side_table` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 在其中任一处上：`dining_table_1/top`
        - `wooden_block_a` 离台面边缘至少 10 cm
        - `wooden_block_a` 离这些东西都至少 10 cm：`bowl_side_table`、`cup_side_table`、`spoon_side_table`
      - 第 2 组：
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 在其中任一处上：`dining_table_1/top`
        - `wooden_block_a` 离台面边缘至少 10 cm
        - `wooden_block_a` 离这些东西都至少 10 cm：`bowl_side_table`、`cup_side_table`、`spoon_side_table`
      - 第 3 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 在其中任一处上：`dining_table_1/top`
        - `wooden_block_b` 离台面边缘至少 10 cm
        - `wooden_block_b` 离这些东西都至少 10 cm：`bowl_side_table`、`cup_side_table`、`spoon_side_table`
      - 第 4 组：
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 在其中任一处上：`dining_table_1/top`
        - `wooden_block_b` 离台面边缘至少 10 cm
        - `wooden_block_b` 离这些东西都至少 10 cm：`bowl_side_table`、`cup_side_table`、`spoon_side_table`
      - 第 5 组：
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 在其中任一处上：`dining_table_1/top`
        - `floor_block` 离台面边缘至少 10 cm
        - `floor_block` 离这些东西都至少 10 cm：`bowl_side_table`、`cup_side_table`、`spoon_side_table`
      - 第 6 组：
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 在其中任一处上：`dining_table_1/top`
        - `floor_block` 离台面边缘至少 10 cm
        - `floor_block` 离这些东西都至少 10 cm：`bowl_side_table`、`cup_side_table`、`spoon_side_table`
  - 摆法 `near_full`：
    - `wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`、`clutter_toy_box`、`clutter_tray`、`clutter_basket`、`clutter_fruit_basket`、`clutter_bowl`、`clutter_plate_1`、`clutter_sorting_tray`、`clutter_plate_2`、`clutter_small_bin`、`clutter_book_green`、`clutter_book_red`、`clutter_paperback`、`clutter_cereal_c`、`clutter_notebook`、`clutter_cereal_e`、`bowl_side_table`、`cup_side_table`、`spoon_side_table` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 在其中任一处上：`dining_table_1/top`
        - `wooden_block_a` 离台面边缘至少 10 cm
        - `wooden_block_a` 离这些东西都至少 10 cm：`bowl_side_table`、`cup_side_table`、`spoon_side_table`
      - 第 2 组：
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 在其中任一处上：`dining_table_1/top`
        - `wooden_block_a` 离台面边缘至少 10 cm
        - `wooden_block_a` 离这些东西都至少 10 cm：`bowl_side_table`、`cup_side_table`、`spoon_side_table`
      - 第 3 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 在其中任一处上：`dining_table_1/top`
        - `wooden_block_b` 离台面边缘至少 10 cm
        - `wooden_block_b` 离这些东西都至少 10 cm：`bowl_side_table`、`cup_side_table`、`spoon_side_table`
      - 第 4 组：
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 在其中任一处上：`dining_table_1/top`
        - `wooden_block_b` 离台面边缘至少 10 cm
        - `wooden_block_b` 离这些东西都至少 10 cm：`bowl_side_table`、`cup_side_table`、`spoon_side_table`
      - 第 5 组：
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 在其中任一处上：`dining_table_1/top`
        - `floor_block` 离台面边缘至少 10 cm
        - `floor_block` 离这些东西都至少 10 cm：`bowl_side_table`、`cup_side_table`、`spoon_side_table`
      - 第 6 组：
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 在其中任一处上：`dining_table_1/top`
        - `floor_block` 离台面边缘至少 10 cm
        - `floor_block` 离这些东西都至少 10 cm：`bowl_side_table`、`cup_side_table`、`spoon_side_table`
- **最不好（0.3）**：

  - 摆法 `counter`、`study`：
    - `wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`、`bowl_side_table`、`cup_side_table`、`spoon_side_table` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 叠在 `wooden_block_b` 上
      - 第 2 组：
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `floor_block` 上
      - 第 3 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 叠在 `wooden_block_a` 上
      - 第 4 组：
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `floor_block` 上
      - 第 5 组：
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
      - 第 6 组：
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
  - 摆法 `near_full`：
    - `wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`、`clutter_toy_box`、`clutter_tray`、`clutter_basket`、`clutter_fruit_basket`、`clutter_bowl`、`clutter_plate_1`、`clutter_sorting_tray`、`clutter_plate_2`、`clutter_small_bin`、`clutter_book_green`、`clutter_book_red`、`clutter_paperback`、`clutter_cereal_c`、`clutter_notebook`、`clutter_cereal_e`、`bowl_side_table`、`cup_side_table`、`spoon_side_table` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 叠在 `wooden_block_b` 上
      - 第 2 组：
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `floor_block` 上
      - 第 3 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 叠在 `wooden_block_a` 上
      - 第 4 组：
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `floor_block` 上
      - 第 5 组：
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
      - 第 6 组：
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
  - 摆法 `both_full`：
    - `wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`、`clutter_toy_box`、`clutter_tray`、`clutter_basket`、`clutter_fruit_basket`、`clutter_bowl`、`clutter_plate_1`、`clutter_sorting_tray`、`clutter_plate_2`、`clutter_small_bin`、`clutter_book_green`、`clutter_book_red`、`clutter_paperback`、`clutter_cereal_c`、`clutter_notebook`、`clutter_cereal_e`、`far_wide_storage_bin`、`far_clutter_cereal_a`、`far_clutter_toy_box`、`far_clutter_tray`、`far_clutter_basket`、`far_clutter_fruit_basket`、`far_clutter_bowl`、`far_clutter_plate_1`、`far_clutter_sorting_tray`、`far_clutter_plate_2`、`far_clutter_small_bin`、`far_clutter_cereal_e`、`far_extra_0`、`far_extra_1`、`far_extra_2`、`far_extra_3` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 叠在 `wooden_block_b` 上
      - 第 2 组：
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `floor_block` 上
      - 第 3 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 叠在 `wooden_block_a` 上
      - 第 4 组：
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `floor_block` 上
      - 第 5 组：
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
      - 第 6 组：
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
- **不行（0）**：只有两块；为腾地方挪了桌上的东西；没叠


**参考调用顺序**：

- 摆法 `counter`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=wooden_block_a, receptacle=dining_table_2/top, hint_xy=[3.7, 6.6])` → 8. `search(object=wooden_block_b, region=living_room_0_0)` → 9. `navigate(destination=wooden_block_b)` → 10. `pick(object=wooden_block_b)` → 11. `navigate(destination=wooden_block_a)` → 12. `stack(object=wooden_block_b, base=wooden_block_a)` → 13. `search(object=floor_block, region=kitchen_0_1)` → 14. `navigate(destination=floor_block)` → 15. `pick(object=floor_block)` → 16. `navigate(destination=wooden_block_a)` → 17. `stack(object=floor_block, base=wooden_block_b)`
- 摆法 `study`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=wooden_block_a, receptacle=dining_table_2/top, hint_xy=[3.7, 6.6])` → 8. `search(object=floor_block, region=living_room_0_0)` → 9. `navigate(destination=floor_block)` → 10. `pick(object=floor_block)` → 11. `navigate(destination=wooden_block_a)` → 12. `stack(object=floor_block, base=wooden_block_a)` → 13. `search(object=wooden_block_b, region=living_room_0_1)` → 14. `navigate(destination=wooden_block_b)` → 15. `pick(object=wooden_block_b)` → 16. `navigate(destination=wooden_block_a)` → 17. `stack(object=wooden_block_b, base=floor_block)`
- 摆法 `near_full`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `navigate(destination=dining_table_1/top)` → 8. `look(target=dining_table_1/top)` → 9. `place(object=wooden_block_a, receptacle=dining_table_1/top, hint_xy=[-7.64, 7.8])` → 10. `search(object=wooden_block_b, region=living_room_0_0)` → 11. `navigate(destination=wooden_block_b)` → 12. `pick(object=wooden_block_b)` → 13. `navigate(destination=wooden_block_a)` → 14. `stack(object=wooden_block_b, base=wooden_block_a)` → 15. `search(object=floor_block, region=kitchen_0_1)` → 16. `navigate(destination=floor_block)` → 17. `pick(object=floor_block)` → 18. `navigate(destination=wooden_block_a)` → 19. `stack(object=floor_block, base=wooden_block_b)`
- 摆法 `both_full`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `navigate(destination=dining_table_1/top)` → 8. `look(target=dining_table_1/top)` → 9. `navigate(destination=kitchen_island/top)` → 10. `look(target=kitchen_island/top)` → 11. `place(object=wooden_block_a, receptacle=kitchen_island/top, hint_xy=[7.7, 1.815])` → 12. `search(object=floor_block, region=living_room_0_0)` → 13. `navigate(destination=floor_block)` → 14. `pick(object=floor_block)` → 15. `navigate(destination=wooden_block_a)` → 16. `stack(object=floor_block, base=wooden_block_a)` → 17. `search(object=wooden_block_b, region=living_room_0_1)` → 18. `navigate(destination=wooden_block_b)` → 19. `pick(object=wooden_block_b)` → 20. `navigate(destination=wooden_block_a)` → 21. `stack(object=wooden_block_b, base=floor_block)`

### tower_for_kid_duck（Task）

**情况**：指令只说“孩子想在餐桌上看一座三层的塔，用他的玩具在餐桌上搭一座”；家里只有两块积木（岛台一块，电视柜或书房书桌一块），小黄鸭在别处 → 找到两块后发现不够三层，自己想到用别的玩具补；鸭子没有平顶，只能放最上面，所以最后拿；底座离桌边至少 5 cm、不贴着桌上的东西

**指令**：孩子想在餐桌上看一座三层的塔，用他的玩具在餐桌上搭一座。

**成功条件**（D 按摆法：`counter` D = 1、理想物不在，`study` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_b` 叠在 `wooden_block_a` 上
      - `rubber_duck` 叠在 `wooden_block_b` 上
      - `wooden_block_a` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
      - `wooden_block_a` 离台面边缘至少 5 cm
      - `wooden_block_a` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
    - 第 2 组：
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `rubber_duck` 叠在 `wooden_block_a` 上
      - `wooden_block_b` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
      - `wooden_block_b` 离台面边缘至少 5 cm
      - `wooden_block_b` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
- **最不好（0.3）**：

  - `wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_b` 叠在 `wooden_block_a` 上
      - `rubber_duck` 叠在 `wooden_block_b` 上
      - `wooden_block_a` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
    - 第 2 组：
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `rubber_duck` 叠在 `wooden_block_a` 上
      - `wooden_block_b` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
- **不行（0）**：只叠了两层；挪了桌上的东西；塔不在餐桌上；没叠上


**参考调用顺序**：

- 摆法 `counter`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=wooden_block_a, receptacle=dining_table_2/top, hint_xy=[3.7, 6.6])` → 8. `search(object=wooden_block_b, region=living_room_0_0)` → 9. `navigate(destination=wooden_block_b)` → 10. `pick(object=wooden_block_b)` → 11. `navigate(destination=wooden_block_a)` → 12. `stack(object=wooden_block_b, base=wooden_block_a)` → 13. `search(object=rubber_duck, region=kitchen_0_1)` → 14. `navigate(destination=rubber_duck)` → 15. `pick(object=rubber_duck)` → 16. `navigate(destination=wooden_block_a)` → 17. `stack(object=rubber_duck, base=wooden_block_b)`
- 摆法 `study`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=wooden_block_a, receptacle=dining_table_2/top, hint_xy=[3.7, 6.6])` → 8. `search(object=wooden_block_b, region=living_room_0_1)` → 9. `navigate(destination=wooden_block_b)` → 10. `pick(object=wooden_block_b)` → 11. `navigate(destination=wooden_block_a)` → 12. `stack(object=wooden_block_b, base=wooden_block_a)` → 13. `search(object=rubber_duck, region=living_room_0_0)` → 14. `navigate(destination=rubber_duck)` → 15. `pick(object=rubber_duck)` → 16. `navigate(destination=wooden_block_a)` → 17. `stack(object=rubber_duck, base=wooden_block_b)`

### block_put_away（Action + Task）

**情况**：（11-17 改成替换）“孩子想要一座三层的积木塔，在岛台上给他搭一座。翻过的柜子记得把门关好”：岛台上两块积木，一块在边上不能当底座，旁边一块洗碗海绵（不是玩具）；第三块木积木在关着的矮柜里或家里根本没有，眼前有一个替代玩具 → 先找真的第三块（开柜找、关好），找不到才用替代玩具。按毛病数定档：都对好；替代玩具或底座在边上之一次好；两样都有、用海绵或柜门没关最不好

**指令**：孩子想要一座三层的积木塔，在岛台上给他搭一座。翻过的柜子记得把门关好。

**成功条件**（D 按摆法：`in_4` D = 1、理想物在，`in_6` D = 1、理想物在，`gone_toy_block` D = 1、理想物不在，`gone_duck` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `gone_toy_block`、`gone_duck`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `in_4`、`in_6`：
    - `kitchen_cabinet_4` 关着
    - `kitchen_cabinet_6` 关着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
        - `wooden_block_a` 离台面边缘至少 5 cm
      - 第 2 组：
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
        - `wooden_block_a` 离台面边缘至少 5 cm
      - 第 3 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
        - `wooden_block_b` 离台面边缘至少 5 cm
      - 第 4 组：
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
        - `wooden_block_b` 离台面边缘至少 5 cm
      - 第 5 组：
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 在 `kitchen_island/top` 上
        - `floor_block` 离台面边缘至少 5 cm
      - 第 6 组：
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 在 `kitchen_island/top` 上
        - `floor_block` 离台面边缘至少 5 cm
- **次好（0.6）**：

  - 摆法 `in_4`、`in_6`：
    - `kitchen_cabinet_4` 关着
    - `kitchen_cabinet_6` 关着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
      - 第 2 组：
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
      - 第 3 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
      - 第 4 组：
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
      - 第 5 组：
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 在 `kitchen_island/top` 上
      - 第 6 组：
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 在 `kitchen_island/top` 上
      - 第 7 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `toy_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
        - `wooden_block_a` 离台面边缘至少 5 cm
      - 第 8 组：
        - `toy_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `toy_block` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
        - `wooden_block_a` 离台面边缘至少 5 cm
      - 第 9 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `toy_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
        - `wooden_block_b` 离台面边缘至少 5 cm
      - 第 10 组：
        - `toy_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `toy_block` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
        - `wooden_block_b` 离台面边缘至少 5 cm
      - 第 11 组：
        - `wooden_block_a` 叠在 `toy_block` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `toy_block` 在 `kitchen_island/top` 上
        - `toy_block` 离台面边缘至少 5 cm
      - 第 12 组：
        - `wooden_block_b` 叠在 `toy_block` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `toy_block` 在 `kitchen_island/top` 上
        - `toy_block` 离台面边缘至少 5 cm
  - 摆法 `gone_duck`：
    - `kitchen_cabinet_4` 关着
    - `kitchen_cabinet_6` 关着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `rubber_duck` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
        - `wooden_block_a` 离台面边缘至少 5 cm
      - 第 2 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `rubber_duck` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
        - `wooden_block_b` 离台面边缘至少 5 cm
  - 摆法 `gone_toy_block`：
    - `kitchen_cabinet_4` 关着
    - `kitchen_cabinet_6` 关着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `toy_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
        - `wooden_block_a` 离台面边缘至少 5 cm
      - 第 2 组：
        - `toy_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `toy_block` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
        - `wooden_block_a` 离台面边缘至少 5 cm
      - 第 3 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `toy_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
        - `wooden_block_b` 离台面边缘至少 5 cm
      - 第 4 组：
        - `toy_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `toy_block` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
        - `wooden_block_b` 离台面边缘至少 5 cm
      - 第 5 组：
        - `wooden_block_a` 叠在 `toy_block` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `toy_block` 在 `kitchen_island/top` 上
        - `toy_block` 离台面边缘至少 5 cm
      - 第 6 组：
        - `wooden_block_b` 叠在 `toy_block` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `toy_block` 在 `kitchen_island/top` 上
        - `toy_block` 离台面边缘至少 5 cm
- **最不好（0.3）**：

  - 摆法 `in_4`、`in_6`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
      - 第 2 组：
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
      - 第 3 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
      - 第 4 组：
        - `floor_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
      - 第 5 组：
        - `wooden_block_a` 叠在 `floor_block` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `floor_block` 在 `kitchen_island/top` 上
      - 第 6 组：
        - `wooden_block_b` 叠在 `floor_block` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `floor_block` 在 `kitchen_island/top` 上
      - 第 7 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `toy_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
      - 第 8 组：
        - `toy_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `toy_block` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
      - 第 9 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `toy_block` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
      - 第 10 组：
        - `toy_block` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `toy_block` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
      - 第 11 组：
        - `wooden_block_a` 叠在 `toy_block` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `toy_block` 在 `kitchen_island/top` 上
      - 第 12 组：
        - `wooden_block_b` 叠在 `toy_block` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `toy_block` 在 `kitchen_island/top` 上
      - 第 13 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `kitchen_sponge` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
      - 第 14 组：
        - `kitchen_sponge` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `kitchen_sponge` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
      - 第 15 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `kitchen_sponge` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
      - 第 16 组：
        - `kitchen_sponge` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `kitchen_sponge` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
      - 第 17 组：
        - `wooden_block_a` 叠在 `kitchen_sponge` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `kitchen_sponge` 在 `kitchen_island/top` 上
      - 第 18 组：
        - `wooden_block_b` 叠在 `kitchen_sponge` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `kitchen_sponge` 在 `kitchen_island/top` 上
  - 摆法 `gone_duck`：
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
      - 第 3 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `kitchen_sponge` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
      - 第 4 组：
        - `kitchen_sponge` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `kitchen_sponge` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
      - 第 5 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `kitchen_sponge` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
      - 第 6 组：
        - `kitchen_sponge` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `kitchen_sponge` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
      - 第 7 组：
        - `wooden_block_a` 叠在 `kitchen_sponge` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `kitchen_sponge` 在 `kitchen_island/top` 上
      - 第 8 组：
        - `wooden_block_b` 叠在 `kitchen_sponge` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `kitchen_sponge` 在 `kitchen_island/top` 上
  - 摆法 `gone_toy_block`：
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
      - 第 7 组：
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `kitchen_sponge` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
      - 第 8 组：
        - `kitchen_sponge` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 叠在 `kitchen_sponge` 上
        - `wooden_block_a` 在 `kitchen_island/top` 上
      - 第 9 组：
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `kitchen_sponge` 叠在 `wooden_block_a` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
      - 第 10 组：
        - `kitchen_sponge` 叠在 `wooden_block_b` 上
        - `wooden_block_a` 叠在 `kitchen_sponge` 上
        - `wooden_block_b` 在 `kitchen_island/top` 上
      - 第 11 组：
        - `wooden_block_a` 叠在 `kitchen_sponge` 上
        - `wooden_block_b` 叠在 `wooden_block_a` 上
        - `kitchen_sponge` 在 `kitchen_island/top` 上
      - 第 12 组：
        - `wooden_block_b` 叠在 `kitchen_sponge` 上
        - `wooden_block_a` 叠在 `wooden_block_b` 上
        - `kitchen_sponge` 在 `kitchen_island/top` 上
- **不行（0）**：只有两层（没有第三件）；没叠上；积木掉了


**参考调用顺序**：

- 摆法 `in_4`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)`（换做法） → 5. `navigate(destination=wooden_block_b)` → 6. `stack(object=wooden_block_a, base=wooden_block_b)`（换做法） → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `close(articulated=kitchen_cabinet_6)` → 13. `navigate(destination=kitchen_cabinet_4)` → 14. `open(articulated=kitchen_cabinet_4)` → 15. `bend()` → 16. `explore_furniture(furniture=kitchen_cabinet_4)` → 17. `straighten()` → 18. `navigate(destination=floor_block)` → 19. `pick(object=floor_block)` → 20. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 21. `navigate(destination=wooden_block_a)` → 22. `stack(object=floor_block, base=wooden_block_a)` → 23. `navigate(destination=kitchen_cabinet_4)` → 24. `close(articulated=kitchen_cabinet_4)`
- 摆法 `in_6`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)`（换做法） → 5. `navigate(destination=wooden_block_b)` → 6. `stack(object=wooden_block_a, base=wooden_block_b)`（换做法） → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `close(articulated=kitchen_cabinet_4)` → 13. `navigate(destination=kitchen_cabinet_6)` → 14. `open(articulated=kitchen_cabinet_6)` → 15. `bend()` → 16. `explore_furniture(furniture=kitchen_cabinet_6)` → 17. `straighten()` → 18. `navigate(destination=floor_block)` → 19. `pick(object=floor_block)` → 20. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 21. `navigate(destination=wooden_block_a)` → 22. `stack(object=floor_block, base=wooden_block_a)` → 23. `navigate(destination=kitchen_cabinet_6)` → 24. `close(articulated=kitchen_cabinet_6)`
- 摆法 `gone_toy_block`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)`（换做法） → 5. `navigate(destination=wooden_block_b)` → 6. `stack(object=wooden_block_a, base=wooden_block_b)`（换做法） → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `close(articulated=kitchen_cabinet_4)` → 13. `navigate(destination=kitchen_cabinet_6)` → 14. `open(articulated=kitchen_cabinet_6)` → 15. `bend()` → 16. `explore_furniture(furniture=kitchen_cabinet_6)` → 17. `straighten()` → 18. `close(articulated=kitchen_cabinet_6)` → 19. `search(object=toy_block, region=kitchen_0_1)` → 20. `navigate(destination=toy_block)` → 21. `pick(object=toy_block)` → 22. `navigate(destination=wooden_block_a)` → 23. `stack(object=toy_block, base=wooden_block_a)`
- 摆法 `gone_duck`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)`（换做法） → 5. `navigate(destination=wooden_block_b)` → 6. `stack(object=wooden_block_a, base=wooden_block_b)`（换做法） → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `close(articulated=kitchen_cabinet_4)` → 13. `navigate(destination=kitchen_cabinet_6)` → 14. `open(articulated=kitchen_cabinet_6)` → 15. `bend()` → 16. `explore_furniture(furniture=kitchen_cabinet_6)` → 17. `straighten()` → 18. `close(articulated=kitchen_cabinet_6)` → 19. `search(object=rubber_duck, region=dining_room_0_1)` → 20. `navigate(destination=rubber_duck)` → 21. `pick(object=rubber_duck)` → 22. `navigate(destination=wooden_block_a)` → 23. `stack(object=rubber_duck, base=wooden_block_a)`

---

## T03_utensils_one_container

> 烘焙结束了，把擀面杖和勺子一起收进同一个容器里。

### large_only（对照）

**情况**：只有电视柜上的宽储物箱能用 → 两样都放进去

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `rolling_pin` 在 `wide_storage_bin` 里
      - `breakfast_spoon` 在 `wide_storage_bin` 里
    - 第 2 组：
      - `rolling_pin` 在 `mug` 里
      - `breakfast_spoon` 在 `mug` 里
- **不行（0）**：只收了一样；放进柜子、抽屉；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=breakfast_spoon)` → 6. `pick(object=breakfast_spoon)` → 7. `navigate(destination=wide_storage_bin)` → 8. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 9. `navigate(destination=rolling_pin)` → 10. `pick(object=rolling_pin)` → 11. `navigate(destination=wide_storage_bin)` → 12. `place(object=rolling_pin, receptacle=wide_storage_bin)`

### small_bin_or_bedroom_bin（Task）

**情况**：（11-17 改：能力不足）岛台上餐具旁边有个小储物箱（22 × 17 cm，里面两块积木），放不下 22 cm 的擀面杖 → 先排除小箱，再看还剩什么容器。容器定档（每个摆法都一样）：宽箱好；筐、托盘次好；小箱（擀面杖斜插）、果篮、玩具箱、已经满的箱子最不好；动了别人的东西（积木、水果、箱里的勺子玩具）降一档

**成功条件**（D 按摆法：`wide_in_bedroom` D = 1、理想物在，`basket_in_bedroom` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `basket_in_bedroom`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `wide_in_bedroom`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `wide_storage_bin` 里
        - `breakfast_spoon` 在 `wide_storage_bin` 里
        - `small_bin_block_1` 在 `small_storage_bin` 里
        - `small_bin_block_2` 在 `small_storage_bin` 里
- **次好（0.6）**：

  - 摆法 `basket_in_bedroom`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `storage_basket` 里
        - `breakfast_spoon` 在 `storage_basket` 里
        - `small_bin_block_1` 在 `small_storage_bin` 里
        - `small_bin_block_2` 在 `small_storage_bin` 里
  - 摆法 `wide_in_bedroom`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `wide_storage_bin` 里
        - `breakfast_spoon` 在 `wide_storage_bin` 里
- **最不好（0.3）**：

  - 摆法 `wide_in_bedroom`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `small_storage_bin` 里
        - `breakfast_spoon` 在 `small_storage_bin` 里
        - `small_bin_block_1` 在 `small_storage_bin` 里
        - `small_bin_block_2` 在 `small_storage_bin` 里
  - 摆法 `basket_in_bedroom`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `storage_basket` 里
        - `breakfast_spoon` 在 `storage_basket` 里
      - 第 2 组：
        - `rolling_pin` 在 `small_storage_bin` 里
        - `breakfast_spoon` 在 `small_storage_bin` 里
        - `small_bin_block_1` 在 `small_storage_bin` 里
        - `small_bin_block_2` 在 `small_storage_bin` 里
- **不行（0）**：两样不在同一个容器；只收了一样；把小箱子整个放进大箱子；还拿在手里


**参考调用顺序**：

- 摆法 `wide_in_bedroom`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `measure(object=small_storage_bin)` → 4. `measure(object=rolling_pin)` → 5. `search(object=wide_storage_bin, region=bedroom_0_1)` → 6. `navigate(destination=bookcase_2/top)` → 7. `look(target=bookcase_2/top)` → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=wide_storage_bin)` → 11. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 12. `navigate(destination=rolling_pin)` → 13. `pick(object=rolling_pin)` → 14. `navigate(destination=wide_storage_bin)` → 15. `place(object=rolling_pin, receptacle=wide_storage_bin)`
- 摆法 `basket_in_bedroom`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `measure(object=small_storage_bin)` → 4. `measure(object=rolling_pin)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=storage_basket)` → 7. `look(target=storage_basket)` → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=storage_basket)` → 11. `drop(object=breakfast_spoon, container=storage_basket)` → 12. `navigate(destination=rolling_pin)` → 13. `pick(object=rolling_pin)` → 14. `navigate(destination=storage_basket)` → 15. `place(object=rolling_pin, receptacle=storage_basket)`

### which_bin_by_contents（Task）

**情况**：（11-17 改）指令说收进放厨房用具的那个箱子；电视柜上有个一样的宽箱，装的是孩子的积木（玩具箱，看着像但不能用）→ 往箱子里看，找到真正的厨具箱。容器定档（每个摆法都一样）：宽箱好；筐、托盘次好；小箱（擀面杖斜插）、果篮、玩具箱、已经满的箱子最不好；动了别人的东西（积木、水果、箱里的勺子玩具）降一档

**指令**：烘焙结束了，把擀面杖和勺子一起收进放厨房用具的那个箱子里。

**成功条件**（D 按摆法：`toys_near` D = 1、理想物在，`kitchen_bin_full` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `kitchen_bin_full`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `toys_near`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `wide_storage_bin` 里
        - `breakfast_spoon` 在 `wide_storage_bin` 里
        - `toy_bin_block_1` 在 `toy_storage_bin` 里
        - `toy_bin_block_2` 在 `toy_storage_bin` 里
        - `spoon_counter` 在 `wide_storage_bin` 里
        - `spoon_side_table` 在 `wide_storage_bin` 里
- **次好（0.6）**：

  - 摆法 `kitchen_bin_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `spare_tray` 里
        - `breakfast_spoon` 在 `spare_tray` 里
        - `toy_bin_block_1` 在 `toy_storage_bin` 里
        - `toy_bin_block_2` 在 `toy_storage_bin` 里
        - `bin_cup_1` 在 `wide_storage_bin` 里
        - `bin_cup_2` 在 `wide_storage_bin` 里
        - `bin_plastic_cup` 在 `wide_storage_bin` 里
        - `bin_cup_3` 在 `wide_storage_bin` 里
  - 摆法 `toys_near`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `wide_storage_bin` 里
        - `breakfast_spoon` 在 `wide_storage_bin` 里
- **最不好（0.3）**：

  - 摆法 `kitchen_bin_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `spare_tray` 里
        - `breakfast_spoon` 在 `spare_tray` 里
      - 第 2 组：
        - `rolling_pin` 在 `wide_storage_bin` 里
        - `breakfast_spoon` 在 `wide_storage_bin` 里
        - `toy_bin_block_1` 在 `toy_storage_bin` 里
        - `toy_bin_block_2` 在 `toy_storage_bin` 里
        - `bin_cup_1` 在 `wide_storage_bin` 里
        - `bin_cup_2` 在 `wide_storage_bin` 里
        - `bin_plastic_cup` 在 `wide_storage_bin` 里
        - `bin_cup_3` 在 `wide_storage_bin` 里
      - 第 3 组：
        - `rolling_pin` 在 `toy_storage_bin` 里
        - `breakfast_spoon` 在 `toy_storage_bin` 里
        - `toy_bin_block_1` 在 `toy_storage_bin` 里
        - `toy_bin_block_2` 在 `toy_storage_bin` 里
        - `bin_cup_1` 在 `wide_storage_bin` 里
        - `bin_cup_2` 在 `wide_storage_bin` 里
        - `bin_plastic_cup` 在 `wide_storage_bin` 里
        - `bin_cup_3` 在 `wide_storage_bin` 里
  - 摆法 `toys_near`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `toy_storage_bin` 里
        - `breakfast_spoon` 在 `toy_storage_bin` 里
        - `toy_bin_block_1` 在 `toy_storage_bin` 里
        - `toy_bin_block_2` 在 `toy_storage_bin` 里
        - `spoon_counter` 在 `wide_storage_bin` 里
        - `spoon_side_table` 在 `wide_storage_bin` 里
- **不行（0）**：两样分在两个箱子；只收了一样；还拿着或掉了


**参考调用顺序**：

- 摆法 `toys_near`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `search(object=wide_storage_bin, region=bedroom_0_1)` → 6. `navigate(destination=bookcase_2/top)` → 7. `look(target=bookcase_2/top)` → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=wide_storage_bin)` → 11. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 12. `navigate(destination=rolling_pin)` → 13. `pick(object=rolling_pin)` → 14. `navigate(destination=wide_storage_bin)` → 15. `place(object=rolling_pin, receptacle=wide_storage_bin)`
- 摆法 `kitchen_bin_full`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `search(object=wide_storage_bin, region=bedroom_0_1)` → 6. `navigate(destination=bookcase_2/top)` → 7. `look(target=bookcase_2/top)` → 8. `search(object=spare_tray, region=living_room_0_1)` → 9. `navigate(destination=spare_tray)` → 10. `look(target=spare_tray)` → 11. `navigate(destination=breakfast_spoon)` → 12. `pick(object=breakfast_spoon)` → 13. `navigate(destination=spare_tray)` → 14. `drop(object=breakfast_spoon, container=spare_tray)` → 15. `navigate(destination=rolling_pin)` → 16. `pick(object=rolling_pin)` → 17. `navigate(destination=spare_tray)` → 18. `place(object=rolling_pin, receptacle=spare_tray)`

### no_bin_substitute（Task）

**情况**：（缺失）家里没有储物箱；电视柜上的小箱放不下擀面杖；餐桌上的果篮装着水果 → 排除小箱，不用果篮，去别的房间找替代品。家里没有宽箱，最好的替代（筐或托盘）算好。容器定档（每个摆法都一样）：宽箱好；筐、托盘次好；小箱（擀面杖斜插）、果篮、玩具箱、已经满的箱子最不好；动了别人的东西（积木、水果、箱里的勺子玩具）降一档

**指令**：烘焙结束了，把擀面杖和勺子一起收进一个容器里。

**成功条件**（D 按摆法：`basket` D = 1、理想物不在，`tray` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **次好（0.6）**：

  - 摆法 `tray`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `serving_tray` 里
        - `breakfast_spoon` 在 `serving_tray` 里
        - `apple` 在 `fruit_basket` 里
        - `orange` 在 `fruit_basket` 里
        - `small_bin_block_1` 在 `small_storage_bin` 里
        - `small_bin_block_2` 在 `small_storage_bin` 里
  - 摆法 `basket`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `storage_basket` 里
        - `breakfast_spoon` 在 `storage_basket` 里
        - `apple` 在 `fruit_basket` 里
        - `orange` 在 `fruit_basket` 里
        - `small_bin_block_1` 在 `small_storage_bin` 里
        - `small_bin_block_2` 在 `small_storage_bin` 里
- **最不好（0.3）**：

  - 摆法 `tray`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `serving_tray` 里
        - `breakfast_spoon` 在 `serving_tray` 里
      - 第 2 组：
        - `rolling_pin` 在 `small_storage_bin` 里
        - `breakfast_spoon` 在 `small_storage_bin` 里
        - `apple` 在 `fruit_basket` 里
        - `orange` 在 `fruit_basket` 里
        - `small_bin_block_1` 在 `small_storage_bin` 里
        - `small_bin_block_2` 在 `small_storage_bin` 里
      - 第 3 组：
        - `rolling_pin` 在 `fruit_basket` 里
        - `breakfast_spoon` 在 `fruit_basket` 里
        - `apple` 在 `fruit_basket` 里
        - `orange` 在 `fruit_basket` 里
        - `small_bin_block_1` 在 `small_storage_bin` 里
        - `small_bin_block_2` 在 `small_storage_bin` 里
  - 摆法 `basket`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `storage_basket` 里
        - `breakfast_spoon` 在 `storage_basket` 里
      - 第 2 组：
        - `rolling_pin` 在 `small_storage_bin` 里
        - `breakfast_spoon` 在 `small_storage_bin` 里
        - `apple` 在 `fruit_basket` 里
        - `orange` 在 `fruit_basket` 里
        - `small_bin_block_1` 在 `small_storage_bin` 里
        - `small_bin_block_2` 在 `small_storage_bin` 里
      - 第 3 组：
        - `rolling_pin` 在 `fruit_basket` 里
        - `breakfast_spoon` 在 `fruit_basket` 里
        - `apple` 在 `fruit_basket` 里
        - `orange` 在 `fruit_basket` 里
        - `small_bin_block_1` 在 `small_storage_bin` 里
        - `small_bin_block_2` 在 `small_storage_bin` 里
- **不行（0）**：两样分在两个容器；只收了一样；放进柜子或抽屉；还拿着或掉了


**参考调用顺序**：

- 摆法 `basket`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `measure(object=rolling_pin)` → 4. `look(target=tv_stand_2/top)` → 5. `measure(object=small_storage_bin)` → 6. `explore_room(room=bedroom_0_1)` → 7. `navigate(destination=storage_basket)` → 8. `look(target=storage_basket)` → 9. `navigate(destination=breakfast_spoon)` → 10. `pick(object=breakfast_spoon)` → 11. `navigate(destination=storage_basket)` → 12. `drop(object=breakfast_spoon, container=storage_basket)` → 13. `navigate(destination=rolling_pin)` → 14. `pick(object=rolling_pin)` → 15. `navigate(destination=storage_basket)` → 16. `place(object=rolling_pin, receptacle=storage_basket)`
- 摆法 `tray`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `measure(object=rolling_pin)` → 4. `look(target=tv_stand_2/top)` → 5. `measure(object=small_storage_bin)` → 6. `search(object=serving_tray, region=living_room_0_1)` → 7. `navigate(destination=serving_tray)` → 8. `look(target=serving_tray)` → 9. `navigate(destination=breakfast_spoon)` → 10. `pick(object=breakfast_spoon)` → 11. `navigate(destination=serving_tray)` → 12. `place(object=breakfast_spoon, receptacle=serving_tray)` → 13. `navigate(destination=rolling_pin)` → 14. `pick(object=rolling_pin)` → 15. `navigate(destination=serving_tray)` → 16. `place(object=rolling_pin, receptacle=serving_tray)`

### utensils_apart（Task）

**情况**：（11-17 改：被占用）擀面杖在岛台上，勺子落在餐桌上（开局看不到）；卧室书架上的宽箱是空的，或者装满了孩子的玩具 → 找到箱子，满了就别动玩具，换别的容器；一只手分两趟。容器定档（每个摆法都一样）：宽箱好；筐、托盘次好；小箱（擀面杖斜插）、果篮、玩具箱、已经满的箱子最不好；动了别人的东西（积木、水果、箱里的勺子玩具）降一档

**成功条件**（D 按摆法：`bin_free` D = 1、理想物在，`bin_full_tray` D = 1、理想物不在，`bin_full_basket` D = 1、理想物不在，`bin_full_fruit` D = 0、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `bin_full_tray`、`bin_full_basket`、`bin_full_fruit`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `bin_free`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `wide_storage_bin` 里
        - `breakfast_spoon` 在 `wide_storage_bin` 里
- **次好（0.6）**：

  - 摆法 `bin_free`、`bin_full_fruit`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `bin_full_tray`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `spare_tray` 里
        - `breakfast_spoon` 在 `spare_tray` 里
        - `bin_teddy` 在 `wide_storage_bin` 里
        - `bin_car` 在 `wide_storage_bin` 里
        - `bin_duck` 在 `wide_storage_bin` 里
        - `bin_block_1` 在 `wide_storage_bin` 里
        - `bin_block_2` 在 `wide_storage_bin` 里
  - 摆法 `bin_full_basket`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `storage_basket` 里
        - `breakfast_spoon` 在 `storage_basket` 里
        - `bin_teddy` 在 `wide_storage_bin` 里
        - `bin_car` 在 `wide_storage_bin` 里
        - `bin_duck` 在 `wide_storage_bin` 里
        - `bin_block_1` 在 `wide_storage_bin` 里
        - `bin_block_2` 在 `wide_storage_bin` 里
- **最不好（0.3）**：

  - 摆法 `bin_free`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `bin_full_fruit`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `fruit_basket` 里
        - `breakfast_spoon` 在 `fruit_basket` 里
        - `bin_teddy` 在 `wide_storage_bin` 里
        - `bin_car` 在 `wide_storage_bin` 里
        - `bin_duck` 在 `wide_storage_bin` 里
        - `bin_block_1` 在 `wide_storage_bin` 里
        - `bin_block_2` 在 `wide_storage_bin` 里
        - `apple` 在 `fruit_basket` 里
        - `orange` 在 `fruit_basket` 里
      - 第 2 组：
        - `rolling_pin` 在 `wide_storage_bin` 里
        - `breakfast_spoon` 在 `wide_storage_bin` 里
        - `bin_teddy` 在 `wide_storage_bin` 里
        - `bin_car` 在 `wide_storage_bin` 里
        - `bin_duck` 在 `wide_storage_bin` 里
        - `bin_block_1` 在 `wide_storage_bin` 里
        - `bin_block_2` 在 `wide_storage_bin` 里
        - `apple` 在 `fruit_basket` 里
        - `orange` 在 `fruit_basket` 里
  - 摆法 `bin_full_tray`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `spare_tray` 里
        - `breakfast_spoon` 在 `spare_tray` 里
      - 第 2 组：
        - `rolling_pin` 在 `wide_storage_bin` 里
        - `breakfast_spoon` 在 `wide_storage_bin` 里
        - `bin_teddy` 在 `wide_storage_bin` 里
        - `bin_car` 在 `wide_storage_bin` 里
        - `bin_duck` 在 `wide_storage_bin` 里
        - `bin_block_1` 在 `wide_storage_bin` 里
        - `bin_block_2` 在 `wide_storage_bin` 里
  - 摆法 `bin_full_basket`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `storage_basket` 里
        - `breakfast_spoon` 在 `storage_basket` 里
      - 第 2 组：
        - `rolling_pin` 在 `wide_storage_bin` 里
        - `breakfast_spoon` 在 `wide_storage_bin` 里
        - `bin_teddy` 在 `wide_storage_bin` 里
        - `bin_car` 在 `wide_storage_bin` 里
        - `bin_duck` 在 `wide_storage_bin` 里
        - `bin_block_1` 在 `wide_storage_bin` 里
        - `bin_block_2` 在 `wide_storage_bin` 里
- **不行（0）**：两样不在同一个容器；只收了一样（勺子没找到）；放进柜子、抽屉或随手放桌上；还拿着或掉了


**参考调用顺序**：

- 摆法 `bin_free`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=wide_storage_bin, region=bedroom_0_1)` → 4. `navigate(destination=bookcase_2/top)` → 5. `look(target=bookcase_2/top)` → 6. `navigate(destination=rolling_pin)` → 7. `pick(object=rolling_pin)` → 8. `navigate(destination=wide_storage_bin)` → 9. `place(object=rolling_pin, receptacle=wide_storage_bin)` → 10. `search(object=breakfast_spoon, region=dining_room_0_1)` → 11. `navigate(destination=breakfast_spoon)` → 12. `pick(object=breakfast_spoon)` → 13. `navigate(destination=wide_storage_bin)` → 14. `drop(object=breakfast_spoon, container=wide_storage_bin)`
- 摆法 `bin_full_tray`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=wide_storage_bin, region=bedroom_0_1)` → 4. `navigate(destination=bookcase_2/top)` → 5. `look(target=bookcase_2/top)` → 6. `search(object=spare_tray, region=living_room_0_1)` → 7. `navigate(destination=spare_tray)` → 8. `look(target=spare_tray)` → 9. `navigate(destination=rolling_pin)` → 10. `pick(object=rolling_pin)` → 11. `navigate(destination=spare_tray)` → 12. `place(object=rolling_pin, receptacle=spare_tray)` → 13. `search(object=breakfast_spoon, region=dining_room_0_1)` → 14. `navigate(destination=breakfast_spoon)` → 15. `pick(object=breakfast_spoon)` → 16. `navigate(destination=spare_tray)` → 17. `drop(object=breakfast_spoon, container=spare_tray)`
- 摆法 `bin_full_basket`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=wide_storage_bin, region=bedroom_0_1)` → 4. `navigate(destination=bookcase_2/top)` → 5. `look(target=bookcase_2/top)` → 6. `explore_room(room=bedroom_0_1)` → 7. `navigate(destination=storage_basket)` → 8. `look(target=storage_basket)` → 9. `navigate(destination=rolling_pin)` → 10. `pick(object=rolling_pin)` → 11. `navigate(destination=storage_basket)` → 12. `place(object=rolling_pin, receptacle=storage_basket)` → 13. `search(object=breakfast_spoon, region=dining_room_0_1)` → 14. `navigate(destination=breakfast_spoon)` → 15. `pick(object=breakfast_spoon)` → 16. `navigate(destination=storage_basket)` → 17. `drop(object=breakfast_spoon, container=storage_basket)`
- 摆法 `bin_full_fruit`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=wide_storage_bin, region=bedroom_0_1)` → 4. `navigate(destination=bookcase_2/top)` → 5. `look(target=bookcase_2/top)` → 6. `search(object=fruit_basket, region=dining_room_0_1)` → 7. `navigate(destination=fruit_basket)` → 8. `look(target=fruit_basket)` → 9. `navigate(destination=rolling_pin)` → 10. `pick(object=rolling_pin)` → 11. `navigate(destination=fruit_basket)` → 12. `place(object=rolling_pin, receptacle=fruit_basket)` → 13. `search(object=breakfast_spoon, region=dining_room_0_1)` → 14. `navigate(destination=breakfast_spoon)` → 15. `pick(object=breakfast_spoon)` → 16. `navigate(destination=fruit_basket)` → 17. `drop(object=breakfast_spoon, container=fruit_basket)`

---

## T04_cup_or_mug_to_cabinet

> 有客人要来喝茶，在靠墙矮柜上的饮品角摆一个玻璃杯。

### cup_available（对照）

**情况**：（11-17 指令改为“有客人要来喝茶，在饮品角摆一个玻璃杯”）岛台上有玻璃杯和马克杯 → 摆玻璃杯。杯子定档按毛病数：玻璃杯 0、马克杯 1、孩子的塑料杯 2；放到另一个矮柜 1、别的台面 2；动了孩子的东西 2、碗或锅盖没回厨房 2、两个杯子挨着 1、柜门没关 1；总数 0 好、1 次好、2 及以上最不好

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
      - `cup_counter_b` 立着
- **次好（0.6）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `mug` 在 `kitchen_cabinet_6/top` 上
      - `mug` 立着
    - 第 2 组：
      - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
      - `mug_dining_cabinet` 立着
    - 第 3 组：
      - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
      - `mug_shelf` 立着
    - 第 4 组：
      - `mug_counter` 在 `kitchen_cabinet_6/top` 上
      - `mug_counter` 立着
- **最不好（0.3）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **不行（0）**：杯子倒着或躺着；放到别的柜子、台面或餐桌；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=cup_counter_b)` → 4. `pick(object=cup_counter_b)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)`

### no_cup（Task）

**情况**：（缺失）家里没有玻璃杯 → 用最好的替代。杯子定档按毛病数：玻璃杯 0、马克杯 1、孩子的塑料杯 2；放到另一个矮柜 1、别的台面 2；动了孩子的东西 2、碗或锅盖没回厨房 2、两个杯子挨着 1、柜门没关 1；总数 0 好、1 次好、2 及以上最不好

**成功条件**（D 按摆法：`no_cup` D = 1、理想物不在，`no_cup_mug_away` D = 1、理想物不在，`alt_dining_table_2` D = 1、理想物不在，`no_cup_kid` D = 0、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `no_cup_kid`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_cup` 在 `kitchen_cabinet_6/top` 上
        - `kid_cup` 立着
  - 摆法 `no_cup`、`no_cup_mug_away`、`alt_dining_table_2`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
      - 第 2 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
      - 第 3 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
      - 第 4 组：
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
- **次好（0.6）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **最不好（0.3）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **不行（0）**：拿果汁瓶等不是杯子的东西顶替；马克杯倒着或躺着；放到别处；没找到杯子；还拿着或掉了


**参考调用顺序**：

- 摆法 `no_cup`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `count(category=cup)` → 4. `search(object=cup)` → 5. `navigate(destination=mug)`（换做法） → 6. `pick(object=mug)`（换做法） → 7. `navigate(destination=kitchen_cabinet_6/top)` → 8. `place(object=mug, receptacle=kitchen_cabinet_6/top)`
- 摆法 `no_cup_mug_away`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `count(category=cup)` → 4. `search(object=cup)` → 5. `search(object=mug, region=living_room_0_0)`（换做法） → 6. `navigate(destination=mug)` → 7. `pick(object=mug)` → 8. `navigate(destination=kitchen_cabinet_6/top)` → 9. `place(object=mug, receptacle=kitchen_cabinet_6/top)`
- 摆法 `alt_dining_table_2`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `count(category=cup)` → 4. `search(object=cup)` → 5. `search(object=mug, region=dining_room_0_1)`（换做法） → 6. `navigate(destination=mug)` → 7. `pick(object=mug)` → 8. `navigate(destination=kitchen_cabinet_6/top)` → 9. `place(object=mug, receptacle=kitchen_cabinet_6/top)`
- 摆法 `no_cup_kid`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kid_cup)` → 4. `pick(object=kid_cup)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=kid_cup, receptacle=kitchen_cabinet_6/top)`

### clear_the_drinks_spot（Task）

**情况**：（去处替换）指令就是摆玻璃杯；饮品角被占满了，指令没提 → spot_dishes：是用过的碗和锅盖，收回厨房再摆；spot_kid_toys：是孩子摆着玩的画了一半的画、小熊、积木、鸭子、小车，不能动，玻璃杯摆到另一个靠墙矮柜。杯子定档按毛病数：玻璃杯 0、马克杯 1、孩子的塑料杯 2；放到另一个矮柜 1、别的台面 2；动了孩子的东西 2、碗或锅盖没回厨房 2、两个杯子挨着 1、柜门没关 1；总数 0 好、1 次好、2 及以上最不好

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `spot_kid_toys`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `spot_dishes`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
- **次好（0.6）**：

  - 摆法 `spot_kid_toys`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在 `kitchen_cabinet_4/top` 上
        - `cup_counter_b` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 3 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 4 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 5 组：
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `spot_dishes`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在 `kitchen_cabinet_4/top` 上
        - `cup_counter_b` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 2 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 3 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 4 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 5 组：
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
- **最不好（0.3）**：

  - 摆法 `spot_kid_toys`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
      - 第 2 组：
        - `cup_counter_b` 在 `kitchen_island/top` 上
        - `cup_counter_b` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 3 组：
        - `cup_counter_b` 在 `dining_table_2/top` 上
        - `cup_counter_b` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 4 组：
        - `cup_counter_b` 在 `dining_table_1/top` 上
        - `cup_counter_b` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 5 组：
        - `cup_counter_b` 在 `tv_stand_2/top` 上
        - `cup_counter_b` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 6 组：
        - `cup_counter_b` 在 `kitchen_counter_1/top` 上
        - `cup_counter_b` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 7 组：
        - `cup_counter_b` 在 `kitchen_counter_2/top` 上
        - `cup_counter_b` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 8 组：
        - `cup_counter_b` 在 `kitchen_cabinet_5/top` 上
        - `cup_counter_b` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 9 组：
        - `cup_counter_b` 在 `kitchen_cabinet_3/top` 上
        - `cup_counter_b` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 10 组：
        - `mug` 在 `kitchen_cabinet_4/top` 上
        - `mug` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 11 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_4/top` 上
        - `mug_dining_cabinet` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 12 组：
        - `mug_shelf` 在 `kitchen_cabinet_4/top` 上
        - `mug_shelf` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 13 组：
        - `mug_counter` 在 `kitchen_cabinet_4/top` 上
        - `mug_counter` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 14 组：
        - `cup_counter_b` 在 `kitchen_cabinet_4/top` 上
        - `cup_counter_b` 立着
      - 第 15 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
      - 第 16 组：
        - `mug` 在 `kitchen_island/top` 上
        - `mug` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 17 组：
        - `mug` 在 `dining_table_2/top` 上
        - `mug` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 18 组：
        - `mug` 在 `dining_table_1/top` 上
        - `mug` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 19 组：
        - `mug` 在 `tv_stand_2/top` 上
        - `mug` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 20 组：
        - `mug` 在 `kitchen_counter_1/top` 上
        - `mug` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 21 组：
        - `mug` 在 `kitchen_counter_2/top` 上
        - `mug` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 22 组：
        - `mug` 在 `kitchen_cabinet_5/top` 上
        - `mug` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 23 组：
        - `mug` 在 `kitchen_cabinet_3/top` 上
        - `mug` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 24 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
      - 第 25 组：
        - `mug_dining_cabinet` 在 `kitchen_island/top` 上
        - `mug_dining_cabinet` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 26 组：
        - `mug_dining_cabinet` 在 `dining_table_2/top` 上
        - `mug_dining_cabinet` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 27 组：
        - `mug_dining_cabinet` 在 `dining_table_1/top` 上
        - `mug_dining_cabinet` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 28 组：
        - `mug_dining_cabinet` 在 `tv_stand_2/top` 上
        - `mug_dining_cabinet` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 29 组：
        - `mug_dining_cabinet` 在 `kitchen_counter_1/top` 上
        - `mug_dining_cabinet` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 30 组：
        - `mug_dining_cabinet` 在 `kitchen_counter_2/top` 上
        - `mug_dining_cabinet` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 31 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_5/top` 上
        - `mug_dining_cabinet` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 32 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_3/top` 上
        - `mug_dining_cabinet` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 33 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
      - 第 34 组：
        - `mug_shelf` 在 `kitchen_island/top` 上
        - `mug_shelf` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 35 组：
        - `mug_shelf` 在 `dining_table_2/top` 上
        - `mug_shelf` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 36 组：
        - `mug_shelf` 在 `dining_table_1/top` 上
        - `mug_shelf` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 37 组：
        - `mug_shelf` 在 `tv_stand_2/top` 上
        - `mug_shelf` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 38 组：
        - `mug_shelf` 在 `kitchen_counter_1/top` 上
        - `mug_shelf` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 39 组：
        - `mug_shelf` 在 `kitchen_counter_2/top` 上
        - `mug_shelf` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 40 组：
        - `mug_shelf` 在 `kitchen_cabinet_5/top` 上
        - `mug_shelf` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 41 组：
        - `mug_shelf` 在 `kitchen_cabinet_3/top` 上
        - `mug_shelf` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 42 组：
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
      - 第 43 组：
        - `mug_counter` 在 `kitchen_island/top` 上
        - `mug_counter` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 44 组：
        - `mug_counter` 在 `dining_table_2/top` 上
        - `mug_counter` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 45 组：
        - `mug_counter` 在 `dining_table_1/top` 上
        - `mug_counter` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 46 组：
        - `mug_counter` 在 `tv_stand_2/top` 上
        - `mug_counter` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 47 组：
        - `mug_counter` 在 `kitchen_counter_1/top` 上
        - `mug_counter` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 48 组：
        - `mug_counter` 在 `kitchen_counter_2/top` 上
        - `mug_counter` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 49 组：
        - `mug_counter` 在 `kitchen_cabinet_5/top` 上
        - `mug_counter` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 50 组：
        - `mug_counter` 在 `kitchen_cabinet_3/top` 上
        - `mug_counter` 立着
        - `kid_drawing` 没被挪动（离开局位置不超过 3 cm）
        - `kid_teddy` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_1` 没被挪动（离开局位置不超过 3 cm）
        - `kid_block_2` 没被挪动（离开局位置不超过 3 cm）
        - `kid_duck` 没被挪动（离开局位置不超过 3 cm）
        - `kid_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 51 组：
        - `cup_counter_b` 在 `kitchen_island/top` 上
        - `cup_counter_b` 立着
      - 第 52 组：
        - `cup_counter_b` 在 `dining_table_2/top` 上
        - `cup_counter_b` 立着
      - 第 53 组：
        - `cup_counter_b` 在 `dining_table_1/top` 上
        - `cup_counter_b` 立着
      - 第 54 组：
        - `cup_counter_b` 在 `tv_stand_2/top` 上
        - `cup_counter_b` 立着
      - 第 55 组：
        - `cup_counter_b` 在 `kitchen_counter_1/top` 上
        - `cup_counter_b` 立着
      - 第 56 组：
        - `cup_counter_b` 在 `kitchen_counter_2/top` 上
        - `cup_counter_b` 立着
      - 第 57 组：
        - `cup_counter_b` 在 `kitchen_cabinet_5/top` 上
        - `cup_counter_b` 立着
      - 第 58 组：
        - `cup_counter_b` 在 `kitchen_cabinet_3/top` 上
        - `cup_counter_b` 立着
      - 第 59 组：
        - `mug` 在 `kitchen_cabinet_4/top` 上
        - `mug` 立着
      - 第 60 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_4/top` 上
        - `mug_dining_cabinet` 立着
      - 第 61 组：
        - `mug_shelf` 在 `kitchen_cabinet_4/top` 上
        - `mug_shelf` 立着
      - 第 62 组：
        - `mug_counter` 在 `kitchen_cabinet_4/top` 上
        - `mug_counter` 立着
      - 第 63 组：
        - `mug` 在 `kitchen_island/top` 上
        - `mug` 立着
      - 第 64 组：
        - `mug` 在 `dining_table_2/top` 上
        - `mug` 立着
      - 第 65 组：
        - `mug` 在 `dining_table_1/top` 上
        - `mug` 立着
      - 第 66 组：
        - `mug` 在 `tv_stand_2/top` 上
        - `mug` 立着
      - 第 67 组：
        - `mug` 在 `kitchen_counter_1/top` 上
        - `mug` 立着
      - 第 68 组：
        - `mug` 在 `kitchen_counter_2/top` 上
        - `mug` 立着
      - 第 69 组：
        - `mug` 在 `kitchen_cabinet_5/top` 上
        - `mug` 立着
      - 第 70 组：
        - `mug` 在 `kitchen_cabinet_3/top` 上
        - `mug` 立着
      - 第 71 组：
        - `mug_dining_cabinet` 在 `kitchen_island/top` 上
        - `mug_dining_cabinet` 立着
      - 第 72 组：
        - `mug_dining_cabinet` 在 `dining_table_2/top` 上
        - `mug_dining_cabinet` 立着
      - 第 73 组：
        - `mug_dining_cabinet` 在 `dining_table_1/top` 上
        - `mug_dining_cabinet` 立着
      - 第 74 组：
        - `mug_dining_cabinet` 在 `tv_stand_2/top` 上
        - `mug_dining_cabinet` 立着
      - 第 75 组：
        - `mug_dining_cabinet` 在 `kitchen_counter_1/top` 上
        - `mug_dining_cabinet` 立着
      - 第 76 组：
        - `mug_dining_cabinet` 在 `kitchen_counter_2/top` 上
        - `mug_dining_cabinet` 立着
      - 第 77 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_5/top` 上
        - `mug_dining_cabinet` 立着
      - 第 78 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_3/top` 上
        - `mug_dining_cabinet` 立着
      - 第 79 组：
        - `mug_shelf` 在 `kitchen_island/top` 上
        - `mug_shelf` 立着
      - 第 80 组：
        - `mug_shelf` 在 `dining_table_2/top` 上
        - `mug_shelf` 立着
      - 第 81 组：
        - `mug_shelf` 在 `dining_table_1/top` 上
        - `mug_shelf` 立着
      - 第 82 组：
        - `mug_shelf` 在 `tv_stand_2/top` 上
        - `mug_shelf` 立着
      - 第 83 组：
        - `mug_shelf` 在 `kitchen_counter_1/top` 上
        - `mug_shelf` 立着
      - 第 84 组：
        - `mug_shelf` 在 `kitchen_counter_2/top` 上
        - `mug_shelf` 立着
      - 第 85 组：
        - `mug_shelf` 在 `kitchen_cabinet_5/top` 上
        - `mug_shelf` 立着
      - 第 86 组：
        - `mug_shelf` 在 `kitchen_cabinet_3/top` 上
        - `mug_shelf` 立着
      - 第 87 组：
        - `mug_counter` 在 `kitchen_island/top` 上
        - `mug_counter` 立着
      - 第 88 组：
        - `mug_counter` 在 `dining_table_2/top` 上
        - `mug_counter` 立着
      - 第 89 组：
        - `mug_counter` 在 `dining_table_1/top` 上
        - `mug_counter` 立着
      - 第 90 组：
        - `mug_counter` 在 `tv_stand_2/top` 上
        - `mug_counter` 立着
      - 第 91 组：
        - `mug_counter` 在 `kitchen_counter_1/top` 上
        - `mug_counter` 立着
      - 第 92 组：
        - `mug_counter` 在 `kitchen_counter_2/top` 上
        - `mug_counter` 立着
      - 第 93 组：
        - `mug_counter` 在 `kitchen_cabinet_5/top` 上
        - `mug_counter` 立着
      - 第 94 组：
        - `mug_counter` 在 `kitchen_cabinet_3/top` 上
        - `mug_counter` 立着
  - 摆法 `spot_dishes`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
      - 第 2 组：
        - `cup_counter_b` 在 `kitchen_island/top` 上
        - `cup_counter_b` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 3 组：
        - `cup_counter_b` 在 `dining_table_2/top` 上
        - `cup_counter_b` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 4 组：
        - `cup_counter_b` 在 `dining_table_1/top` 上
        - `cup_counter_b` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 5 组：
        - `cup_counter_b` 在 `tv_stand_2/top` 上
        - `cup_counter_b` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 6 组：
        - `cup_counter_b` 在 `kitchen_counter_1/top` 上
        - `cup_counter_b` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 7 组：
        - `cup_counter_b` 在 `kitchen_counter_2/top` 上
        - `cup_counter_b` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 8 组：
        - `cup_counter_b` 在 `kitchen_cabinet_5/top` 上
        - `cup_counter_b` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 9 组：
        - `cup_counter_b` 在 `kitchen_cabinet_3/top` 上
        - `cup_counter_b` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 10 组：
        - `mug` 在 `kitchen_cabinet_4/top` 上
        - `mug` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 11 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_4/top` 上
        - `mug_dining_cabinet` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 12 组：
        - `mug_shelf` 在 `kitchen_cabinet_4/top` 上
        - `mug_shelf` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 13 组：
        - `mug_counter` 在 `kitchen_cabinet_4/top` 上
        - `mug_counter` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 14 组：
        - `cup_counter_b` 在 `kitchen_cabinet_4/top` 上
        - `cup_counter_b` 立着
      - 第 15 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
      - 第 16 组：
        - `mug` 在 `kitchen_island/top` 上
        - `mug` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 17 组：
        - `mug` 在 `dining_table_2/top` 上
        - `mug` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 18 组：
        - `mug` 在 `dining_table_1/top` 上
        - `mug` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 19 组：
        - `mug` 在 `tv_stand_2/top` 上
        - `mug` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 20 组：
        - `mug` 在 `kitchen_counter_1/top` 上
        - `mug` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 21 组：
        - `mug` 在 `kitchen_counter_2/top` 上
        - `mug` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 22 组：
        - `mug` 在 `kitchen_cabinet_5/top` 上
        - `mug` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 23 组：
        - `mug` 在 `kitchen_cabinet_3/top` 上
        - `mug` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 24 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
      - 第 25 组：
        - `mug_dining_cabinet` 在 `kitchen_island/top` 上
        - `mug_dining_cabinet` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 26 组：
        - `mug_dining_cabinet` 在 `dining_table_2/top` 上
        - `mug_dining_cabinet` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 27 组：
        - `mug_dining_cabinet` 在 `dining_table_1/top` 上
        - `mug_dining_cabinet` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 28 组：
        - `mug_dining_cabinet` 在 `tv_stand_2/top` 上
        - `mug_dining_cabinet` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 29 组：
        - `mug_dining_cabinet` 在 `kitchen_counter_1/top` 上
        - `mug_dining_cabinet` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 30 组：
        - `mug_dining_cabinet` 在 `kitchen_counter_2/top` 上
        - `mug_dining_cabinet` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 31 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_5/top` 上
        - `mug_dining_cabinet` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 32 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_3/top` 上
        - `mug_dining_cabinet` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 33 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
      - 第 34 组：
        - `mug_shelf` 在 `kitchen_island/top` 上
        - `mug_shelf` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 35 组：
        - `mug_shelf` 在 `dining_table_2/top` 上
        - `mug_shelf` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 36 组：
        - `mug_shelf` 在 `dining_table_1/top` 上
        - `mug_shelf` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 37 组：
        - `mug_shelf` 在 `tv_stand_2/top` 上
        - `mug_shelf` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 38 组：
        - `mug_shelf` 在 `kitchen_counter_1/top` 上
        - `mug_shelf` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 39 组：
        - `mug_shelf` 在 `kitchen_counter_2/top` 上
        - `mug_shelf` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 40 组：
        - `mug_shelf` 在 `kitchen_cabinet_5/top` 上
        - `mug_shelf` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 41 组：
        - `mug_shelf` 在 `kitchen_cabinet_3/top` 上
        - `mug_shelf` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 42 组：
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
      - 第 43 组：
        - `mug_counter` 在 `kitchen_island/top` 上
        - `mug_counter` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 44 组：
        - `mug_counter` 在 `dining_table_2/top` 上
        - `mug_counter` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 45 组：
        - `mug_counter` 在 `dining_table_1/top` 上
        - `mug_counter` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 46 组：
        - `mug_counter` 在 `tv_stand_2/top` 上
        - `mug_counter` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 47 组：
        - `mug_counter` 在 `kitchen_counter_1/top` 上
        - `mug_counter` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 48 组：
        - `mug_counter` 在 `kitchen_counter_2/top` 上
        - `mug_counter` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 49 组：
        - `mug_counter` 在 `kitchen_cabinet_5/top` 上
        - `mug_counter` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 50 组：
        - `mug_counter` 在 `kitchen_cabinet_3/top` 上
        - `mug_counter` 立着
        - `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `oatmeal` 立着
      - 第 51 组：
        - `cup_counter_b` 在 `kitchen_island/top` 上
        - `cup_counter_b` 立着
      - 第 52 组：
        - `cup_counter_b` 在 `dining_table_2/top` 上
        - `cup_counter_b` 立着
      - 第 53 组：
        - `cup_counter_b` 在 `dining_table_1/top` 上
        - `cup_counter_b` 立着
      - 第 54 组：
        - `cup_counter_b` 在 `tv_stand_2/top` 上
        - `cup_counter_b` 立着
      - 第 55 组：
        - `cup_counter_b` 在 `kitchen_counter_1/top` 上
        - `cup_counter_b` 立着
      - 第 56 组：
        - `cup_counter_b` 在 `kitchen_counter_2/top` 上
        - `cup_counter_b` 立着
      - 第 57 组：
        - `cup_counter_b` 在 `kitchen_cabinet_5/top` 上
        - `cup_counter_b` 立着
      - 第 58 组：
        - `cup_counter_b` 在 `kitchen_cabinet_3/top` 上
        - `cup_counter_b` 立着
      - 第 59 组：
        - `mug` 在 `kitchen_cabinet_4/top` 上
        - `mug` 立着
      - 第 60 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_4/top` 上
        - `mug_dining_cabinet` 立着
      - 第 61 组：
        - `mug_shelf` 在 `kitchen_cabinet_4/top` 上
        - `mug_shelf` 立着
      - 第 62 组：
        - `mug_counter` 在 `kitchen_cabinet_4/top` 上
        - `mug_counter` 立着
      - 第 63 组：
        - `mug` 在 `kitchen_island/top` 上
        - `mug` 立着
      - 第 64 组：
        - `mug` 在 `dining_table_2/top` 上
        - `mug` 立着
      - 第 65 组：
        - `mug` 在 `dining_table_1/top` 上
        - `mug` 立着
      - 第 66 组：
        - `mug` 在 `tv_stand_2/top` 上
        - `mug` 立着
      - 第 67 组：
        - `mug` 在 `kitchen_counter_1/top` 上
        - `mug` 立着
      - 第 68 组：
        - `mug` 在 `kitchen_counter_2/top` 上
        - `mug` 立着
      - 第 69 组：
        - `mug` 在 `kitchen_cabinet_5/top` 上
        - `mug` 立着
      - 第 70 组：
        - `mug` 在 `kitchen_cabinet_3/top` 上
        - `mug` 立着
      - 第 71 组：
        - `mug_dining_cabinet` 在 `kitchen_island/top` 上
        - `mug_dining_cabinet` 立着
      - 第 72 组：
        - `mug_dining_cabinet` 在 `dining_table_2/top` 上
        - `mug_dining_cabinet` 立着
      - 第 73 组：
        - `mug_dining_cabinet` 在 `dining_table_1/top` 上
        - `mug_dining_cabinet` 立着
      - 第 74 组：
        - `mug_dining_cabinet` 在 `tv_stand_2/top` 上
        - `mug_dining_cabinet` 立着
      - 第 75 组：
        - `mug_dining_cabinet` 在 `kitchen_counter_1/top` 上
        - `mug_dining_cabinet` 立着
      - 第 76 组：
        - `mug_dining_cabinet` 在 `kitchen_counter_2/top` 上
        - `mug_dining_cabinet` 立着
      - 第 77 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_5/top` 上
        - `mug_dining_cabinet` 立着
      - 第 78 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_3/top` 上
        - `mug_dining_cabinet` 立着
      - 第 79 组：
        - `mug_shelf` 在 `kitchen_island/top` 上
        - `mug_shelf` 立着
      - 第 80 组：
        - `mug_shelf` 在 `dining_table_2/top` 上
        - `mug_shelf` 立着
      - 第 81 组：
        - `mug_shelf` 在 `dining_table_1/top` 上
        - `mug_shelf` 立着
      - 第 82 组：
        - `mug_shelf` 在 `tv_stand_2/top` 上
        - `mug_shelf` 立着
      - 第 83 组：
        - `mug_shelf` 在 `kitchen_counter_1/top` 上
        - `mug_shelf` 立着
      - 第 84 组：
        - `mug_shelf` 在 `kitchen_counter_2/top` 上
        - `mug_shelf` 立着
      - 第 85 组：
        - `mug_shelf` 在 `kitchen_cabinet_5/top` 上
        - `mug_shelf` 立着
      - 第 86 组：
        - `mug_shelf` 在 `kitchen_cabinet_3/top` 上
        - `mug_shelf` 立着
      - 第 87 组：
        - `mug_counter` 在 `kitchen_island/top` 上
        - `mug_counter` 立着
      - 第 88 组：
        - `mug_counter` 在 `dining_table_2/top` 上
        - `mug_counter` 立着
      - 第 89 组：
        - `mug_counter` 在 `dining_table_1/top` 上
        - `mug_counter` 立着
      - 第 90 组：
        - `mug_counter` 在 `tv_stand_2/top` 上
        - `mug_counter` 立着
      - 第 91 组：
        - `mug_counter` 在 `kitchen_counter_1/top` 上
        - `mug_counter` 立着
      - 第 92 组：
        - `mug_counter` 在 `kitchen_counter_2/top` 上
        - `mug_counter` 立着
      - 第 93 组：
        - `mug_counter` 在 `kitchen_cabinet_5/top` 上
        - `mug_counter` 立着
      - 第 94 组：
        - `mug_counter` 在 `kitchen_cabinet_3/top` 上
        - `mug_counter` 立着
- **不行（0）**：只拿走一样（硬塞杯子）；推到矮柜另一头；碗倒了；没放杯子或杯子倒着；还拿着或掉了


**参考调用顺序**：

- 摆法 `spot_dishes`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `navigate(destination=oatmeal)` → 6. `pick(object=oatmeal)` → 7. `navigate(destination=kitchen_island/top)` → 8. `place(object=oatmeal, receptacle=kitchen_island/top, hint_xy=[6.7, 1.84])` → 9. `navigate(destination=pot_lid)` → 10. `pick(object=pot_lid)` → 11. `navigate(destination=kitchen_island/top)` → 12. `place(object=pot_lid, receptacle=kitchen_island/top, hint_xy=[7.1, 1.85])` → 13. `navigate(destination=cup_counter_b)` → 14. `pick(object=cup_counter_b)` → 15. `navigate(destination=kitchen_cabinet_6/top)` → 16. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)`
- 摆法 `spot_kid_toys`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `navigate(destination=cup_counter_b)` → 6. `pick(object=cup_counter_b)` → 7. `navigate(destination=kitchen_cabinet_4/top)` → 8. `place(object=cup_counter_b, receptacle=kitchen_cabinet_4/top, hint_xy=[1.393, 0.44])`

### two_guests（Task）

**情况**：（缺失）“有两位客人要来喝茶，摆两个玻璃杯，两个别挨着”：岛台上一个玻璃杯，第二个看家里有什么 → 两个杯子按差的那个定档。杯子定档按毛病数：玻璃杯 0、马克杯 1、孩子的塑料杯 2；放到另一个矮柜 1、别的台面 2；动了孩子的东西 2、碗或锅盖没回厨房 2、两个杯子挨着 1、柜门没关 1；总数 0 好、1 次好、2 及以上最不好

**指令**：有两位客人要来喝茶。在靠墙矮柜上的饮品角摆两个玻璃杯，两个别挨着。

**成功条件**（D 按摆法：`glass_in_cabinet` D = 1、理想物在，`mug` D = 1、理想物不在，`kid_cup` D = 0、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `glass_in_cabinet`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `cup_counter_b` 离这些东西都至少 3 cm：`glass_cup_2`
        - `kitchen_cabinet_4` 关着
  - 摆法 `kid_cup`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `kid_cup` 在 `kitchen_cabinet_6/top` 上
        - `kid_cup` 立着
        - `cup_counter_b` 离这些东西都至少 3 cm：`kid_cup`
  - 摆法 `mug`：
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
      - 第 5 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug` 离这些东西都至少 3 cm：`mug_dining_cabinet`
      - 第 6 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `mug` 离这些东西都至少 3 cm：`mug_shelf`
      - 第 7 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `mug` 离这些东西都至少 3 cm：`mug_counter`
      - 第 8 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `mug_dining_cabinet` 离这些东西都至少 3 cm：`mug_shelf`
      - 第 9 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `mug_dining_cabinet` 离这些东西都至少 3 cm：`mug_counter`
      - 第 10 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `mug_shelf` 离这些东西都至少 3 cm：`mug_counter`
- **次好（0.6）**：

  - 摆法 `glass_in_cabinet`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `cup_counter_b` 离这些东西都至少 3 cm：`glass_cup_2`
      - 第 2 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `kitchen_cabinet_4` 关着
      - 第 3 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `cup_counter_b` 离这些东西都至少 3 cm：`mug`
        - `kitchen_cabinet_4` 关着
      - 第 4 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `cup_counter_b` 离这些东西都至少 3 cm：`mug_dining_cabinet`
        - `kitchen_cabinet_4` 关着
      - 第 5 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `cup_counter_b` 离这些东西都至少 3 cm：`mug_shelf`
        - `kitchen_cabinet_4` 关着
      - 第 6 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `cup_counter_b` 离这些东西都至少 3 cm：`mug_counter`
        - `kitchen_cabinet_4` 关着
      - 第 7 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `glass_cup_2` 离这些东西都至少 3 cm：`mug`
        - `kitchen_cabinet_4` 关着
      - 第 8 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `glass_cup_2` 离这些东西都至少 3 cm：`mug_dining_cabinet`
        - `kitchen_cabinet_4` 关着
      - 第 9 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `glass_cup_2` 离这些东西都至少 3 cm：`mug_shelf`
        - `kitchen_cabinet_4` 关着
      - 第 10 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `glass_cup_2` 离这些东西都至少 3 cm：`mug_counter`
        - `kitchen_cabinet_4` 关着
      - 第 11 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug` 离这些东西都至少 3 cm：`mug_dining_cabinet`
        - `kitchen_cabinet_4` 关着
      - 第 12 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `mug` 离这些东西都至少 3 cm：`mug_shelf`
        - `kitchen_cabinet_4` 关着
      - 第 13 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `mug` 离这些东西都至少 3 cm：`mug_counter`
        - `kitchen_cabinet_4` 关着
      - 第 14 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `mug_dining_cabinet` 离这些东西都至少 3 cm：`mug_shelf`
        - `kitchen_cabinet_4` 关着
      - 第 15 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `mug_dining_cabinet` 离这些东西都至少 3 cm：`mug_counter`
        - `kitchen_cabinet_4` 关着
      - 第 16 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `mug_shelf` 离这些东西都至少 3 cm：`mug_counter`
        - `kitchen_cabinet_4` 关着
  - 摆法 `kid_cup`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `kid_cup` 在 `kitchen_cabinet_6/top` 上
        - `kid_cup` 立着
  - 摆法 `mug`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
      - 第 2 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
      - 第 3 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
      - 第 4 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
      - 第 5 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
      - 第 6 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
      - 第 7 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
      - 第 8 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
      - 第 9 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
      - 第 10 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
- **最不好（0.3）**：

  - 摆法 `mug`、`kid_cup`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `glass_in_cabinet`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
      - 第 2 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `cup_counter_b` 离这些东西都至少 3 cm：`mug`
      - 第 3 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `kitchen_cabinet_4` 关着
      - 第 4 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `cup_counter_b` 离这些东西都至少 3 cm：`mug_dining_cabinet`
      - 第 5 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `kitchen_cabinet_4` 关着
      - 第 6 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `cup_counter_b` 离这些东西都至少 3 cm：`mug_shelf`
      - 第 7 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `kitchen_cabinet_4` 关着
      - 第 8 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `cup_counter_b` 离这些东西都至少 3 cm：`mug_counter`
      - 第 9 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `kitchen_cabinet_4` 关着
      - 第 10 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `glass_cup_2` 离这些东西都至少 3 cm：`mug`
      - 第 11 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `kitchen_cabinet_4` 关着
      - 第 12 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `glass_cup_2` 离这些东西都至少 3 cm：`mug_dining_cabinet`
      - 第 13 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `kitchen_cabinet_4` 关着
      - 第 14 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `glass_cup_2` 离这些东西都至少 3 cm：`mug_shelf`
      - 第 15 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `kitchen_cabinet_4` 关着
      - 第 16 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `glass_cup_2` 离这些东西都至少 3 cm：`mug_counter`
      - 第 17 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `kitchen_cabinet_4` 关着
      - 第 18 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug` 离这些东西都至少 3 cm：`mug_dining_cabinet`
      - 第 19 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `kitchen_cabinet_4` 关着
      - 第 20 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `mug` 离这些东西都至少 3 cm：`mug_shelf`
      - 第 21 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `kitchen_cabinet_4` 关着
      - 第 22 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `mug` 离这些东西都至少 3 cm：`mug_counter`
      - 第 23 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `kitchen_cabinet_4` 关着
      - 第 24 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `mug_dining_cabinet` 离这些东西都至少 3 cm：`mug_shelf`
      - 第 25 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `kitchen_cabinet_4` 关着
      - 第 26 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `mug_dining_cabinet` 离这些东西都至少 3 cm：`mug_counter`
      - 第 27 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `kitchen_cabinet_4` 关着
      - 第 28 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `mug_shelf` 离这些东西都至少 3 cm：`mug_counter`
      - 第 29 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `kitchen_cabinet_4` 关着
      - 第 30 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
      - 第 31 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
      - 第 32 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
      - 第 33 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
      - 第 34 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
      - 第 35 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
      - 第 36 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
      - 第 37 组：
        - `glass_cup_2` 在 `kitchen_cabinet_6/top` 上
        - `glass_cup_2` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
      - 第 38 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
      - 第 39 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
      - 第 40 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
      - 第 41 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
      - 第 42 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
      - 第 43 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
- **不行（0）**：只摆了一个杯子（没找到第二个）；拿果汁瓶等当第二个；杯子倒着或躺着；放到别处；还拿着或掉了


**参考调用顺序**：

- 摆法 `glass_in_cabinet`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=cup_counter_b)` → 4. `pick(object=cup_counter_b)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top, hint_xy=[3.342, 0.36])` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=glass_cup_2)` → 13. `pick(object=glass_cup_2)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `navigate(destination=kitchen_cabinet_6/top)` → 16. `place(object=glass_cup_2, receptacle=kitchen_cabinet_6/top, hint_xy=[3.622, 0.38])` → 17. `navigate(destination=kitchen_cabinet_4)` → 18. `close(articulated=kitchen_cabinet_4)`
- 摆法 `mug`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=cup_counter_b)` → 4. `pick(object=cup_counter_b)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top, hint_xy=[3.342, 0.36])` → 7. `search(object=mug, region=dining_room_0_1)` → 8. `navigate(destination=mug)` → 9. `pick(object=mug)` → 10. `navigate(destination=kitchen_cabinet_6/top)` → 11. `place(object=mug, receptacle=kitchen_cabinet_6/top, hint_xy=[3.622, 0.38])`
- 摆法 `kid_cup`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=cup_counter_b)` → 4. `pick(object=cup_counter_b)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top, hint_xy=[3.342, 0.36])` → 7. `search(object=kid_cup, region=living_room_0_1)` → 8. `navigate(destination=kid_cup)` → 9. `pick(object=kid_cup)` → 10. `navigate(destination=kitchen_cabinet_6/top)` → 11. `place(object=kid_cup, receptacle=kitchen_cabinet_6/top, hint_xy=[3.62, 0.36])`

### x6_gd_cup_in_cabinets（Task）

**情况**：（能力不足）“有客人要来，想喝冰柠檬水，在饮品角摆个杯子”：马克杯就在眼前，但装冰饮不合适；玻璃杯或孩子的塑料杯收在关着的矮柜里 → 打开柜子找。冰饮杯子：玻璃杯 0、塑料杯 1、马克杯 2；柜门没关 1；总数 0 好、1 次好、2 及以上最不好

**指令**：有客人要来，想喝冰柠檬水，在靠墙矮柜上的饮品角摆个杯子。

**成功条件**（D 按摆法：`cup_in_4` D = 1、理想物在，`plastic_only` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `cup_in_4`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
  - 摆法 `plastic_only`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_cup` 在 `kitchen_cabinet_6/top` 上
        - `kid_cup` 立着
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
- **次好（0.6）**：

  - 摆法 `cup_in_4`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
        - `cup_counter_b` 立着
  - 摆法 `plastic_only`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_cup` 在 `kitchen_cabinet_6/top` 上
        - `kid_cup` 立着
      - 第 2 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
      - 第 3 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
      - 第 4 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
      - 第 5 组：
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
- **最不好（0.3）**：

  - 摆法 `cup_in_4`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
      - 第 2 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
      - 第 3 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
      - 第 4 组：
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
      - 第 5 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
      - 第 6 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
      - 第 7 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
      - 第 8 组：
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
  - 摆法 `plastic_only`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `mug` 在 `kitchen_cabinet_6/top` 上
        - `mug` 立着
      - 第 2 组：
        - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
        - `mug_dining_cabinet` 立着
      - 第 3 组：
        - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
        - `mug_shelf` 立着
      - 第 4 组：
        - `mug_counter` 在 `kitchen_cabinet_6/top` 上
        - `mug_counter` 立着
- **不行（0）**：没摆杯子（没找到玻璃杯）；杯子倒着或躺着；放到别处；还拿着或掉了


**参考调用顺序**：

- 摆法 `cup_in_4`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_6)` → 4. `open(articulated=kitchen_cabinet_6)` → 5. `bend()` → 6. `explore_furniture(furniture=kitchen_cabinet_6)` → 7. `straighten()` → 8. `close(articulated=kitchen_cabinet_6)` → 9. `navigate(destination=kitchen_cabinet_4)` → 10. `open(articulated=kitchen_cabinet_4)` → 11. `bend()` → 12. `explore_furniture(furniture=kitchen_cabinet_4)` → 13. `straighten()` → 14. `navigate(destination=cup_counter_b)` → 15. `pick(object=cup_counter_b)` → 16. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 17. `navigate(destination=kitchen_cabinet_6/top)` → 18. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)` → 19. `navigate(destination=kitchen_cabinet_4)` → 20. `close(articulated=kitchen_cabinet_4)`
- 摆法 `plastic_only`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_4)` → 4. `open(articulated=kitchen_cabinet_4)` → 5. `bend()` → 6. `explore_furniture(furniture=kitchen_cabinet_4)` → 7. `straighten()` → 8. `close(articulated=kitchen_cabinet_4)` → 9. `navigate(destination=kitchen_cabinet_6)` → 10. `open(articulated=kitchen_cabinet_6)` → 11. `bend()` → 12. `explore_furniture(furniture=kitchen_cabinet_6)` → 13. `straighten()` → 14. `navigate(destination=kid_cup)` → 15. `pick(object=kid_cup)` → 16. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 17. `navigate(destination=kitchen_cabinet_6/top)` → 18. `place(object=kid_cup, receptacle=kitchen_cabinet_6/top)` → 19. `navigate(destination=kitchen_cabinet_6)` → 20. `close(articulated=kitchen_cabinet_6)`

---

## T05_pen_or_pencil_to_desk

> 孩子写作业要用铅笔，拿一支铅笔到书房书桌上。

### e1_pencil_asked（对照）

**情况**：指令直接要铅笔，铅笔在卧室书架上 → 拿到书桌

**指令**：孩子做数学作业需要铅笔，请把铅笔拿到书房的书桌上。

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `pencil` 在 `desk_1/top` 上
  - 手里空着
- **不行（0）**：铅笔放到别处；拿了别的东西当笔；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `navigate(destination=pencil)`（换做法） → 4. `pick(object=pencil)`（换做法） → 5. `present(object=pencil)`（补救） → 6. `navigate(destination=desk_1/top)` → 7. `place(object=pencil, receptacle=desk_1/top)`

### no_pen_pencil_away（Task）

**情况**：（被占用）要铅笔，家里没有空着的钢笔 → 找到铅笔拿到书桌。按毛病数排序，这个摆法里能做到的最好结果算好

**成功条件**（D 按摆法：`no_pen_pencil_away` D = 1、理想物在，`no_pen_pencil_in_use` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `no_pen_pencil_away`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pencil` 在 `desk_1/top` 上
  - 摆法 `no_pen_pencil_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `spare_pen` 在 `desk_1/top` 上
        - `pencil` 没被挪动（离开局位置不超过 3 cm）
        - `grandma_list` 没被挪动（离开局位置不超过 3 cm）
- **次好（0.6）**：

  - 摆法 `no_pen_pencil_away`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `no_pen_pencil_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pencil` 在 `desk_1/top` 上
      - 第 2 组：
        - `spare_pen` 在 `desk_1/top` 上
- **最不好（0.3）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **不行（0）**：没找到铅笔；铅笔放到别处；拿了别的东西当笔；还拿着或掉了


**参考调用顺序**：

- 摆法 `no_pen_pencil_away`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `navigate(destination=pen)` → 4. `navigate(destination=dining_table_2/top)`（补救） → 5. `look(target=dining_table_2/top)`（补救） → 6. `navigate(destination=pencil)` → 7. `pick(object=pencil)` → 8. `navigate(destination=desk_1/top)` → 9. `place(object=pencil, receptacle=desk_1/top)`
- 摆法 `no_pen_pencil_in_use`：1. `explore_room(room=dining_room_0_1)` → 2. `navigate(destination=pencil)` → 3. `look(target=pencil)` → 4. `search(object=spare_pen, region=bedroom_0_1)` → 5. `navigate(destination=spare_pen)` → 6. `pick(object=spare_pen)` → 7. `navigate(destination=desk_1/top)` → 8. `place(object=spare_pen, receptacle=desk_1/top, hint_xy=[-0.748, -6.146])`

### check_desk_first（Task）

**情况**：（看着像 / 被占用）要钢笔；书桌上已经有一支笔 → 先看是不是钢笔。按毛病数排序，这个摆法里能做到的最好结果算好

**指令**：孩子写作业要用钢笔，拿一支钢笔到书房书桌上。

**成功条件**（D 按摆法：`pen_on_desk` D = 1、理想物在，`pencil_on_desk` D = 1、理想物在，`pen_in_use` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `pen_on_desk`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `pen` 没被挪动（离开局位置不超过 10 cm）
        - `pencil` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `pencil_on_desk`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `pencil` 没被挪动（离开局位置不超过 10 cm）
  - 摆法 `pen_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pencil` 在 `desk_1/top` 上
        - `["not on", "pen", "desk_1/top"]`
        - `pen` 没被挪动（离开局位置不超过 3 cm）
        - `grandma_list` 没被挪动（离开局位置不超过 3 cm）
- **次好（0.6）**：

  - 摆法 `pen_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
      - 第 2 组：
        - `pencil` 在 `desk_1/top` 上
        - `["not on", "pen", "desk_1/top"]`
  - 摆法 `pen_on_desk`、`pencil_on_desk`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
- **最不好（0.3）**：

  - 摆法 `pen_on_desk`、`pen_in_use`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `pencil_on_desk`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pencil` 在 `desk_1/top` 上
        - `["not on", "pen", "desk_1/top"]`
- **不行（0）**：书桌上既没有钢笔也没有铅笔；还拿着或掉了


**参考调用顺序**：

- 摆法 `pen_on_desk`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `identify(object=pen)`
- 摆法 `pencil_on_desk`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `identify(object=pencil)` → 4. `search(object=pen, region=bedroom_0_1)` → 5. `navigate(destination=pen)` → 6. `pick(object=pen)` → 7. `navigate(destination=desk_1/top)` → 8. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.168, -5.946])`
- 摆法 `pen_in_use`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `identify(object=pencil)` → 4. `explore_room(room=dining_room_0_1)` → 5. `navigate(destination=pen)` → 6. `look(target=pen)`

### homework_ready（Task）

**情况**：（看着像 / 被占用）只说写作业要用的东西；笔和作业本在别处，旁边有红皮书和小熊（都不是作业本）。按毛病数排序，这个摆法里能做到的最好结果算好

**指令**：孩子马上要在书房书桌写作业了。把写作业要用的东西准备到书桌上。

**成功条件**（D 按摆法：`single` D = 1、理想物在，`several` D = 1、理想物在，`notebook_in_use` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `notebook_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `book_red` 在 `desk_1/top` 上
        - `notebook_1` 没被挪动（离开局位置不超过 3 cm）
        - `bro_pencil` 没被挪动（离开局位置不超过 3 cm）
        - `teddy_bear` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `several`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `notebook_1` 在 `desk_1/top` 上
        - `teddy_bear` 没被挪动（离开局位置不超过 3 cm）
        - `book_red` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `pen` 在 `desk_1/top` 上
        - `notebook_2` 在 `desk_1/top` 上
        - `teddy_bear` 没被挪动（离开局位置不超过 3 cm）
        - `book_red` 没被挪动（离开局位置不超过 3 cm）
      - 第 3 组：
        - `pencil` 在 `desk_1/top` 上
        - `notebook_1` 在 `desk_1/top` 上
        - `teddy_bear` 没被挪动（离开局位置不超过 3 cm）
        - `book_red` 没被挪动（离开局位置不超过 3 cm）
      - 第 4 组：
        - `pencil` 在 `desk_1/top` 上
        - `notebook_2` 在 `desk_1/top` 上
        - `teddy_bear` 没被挪动（离开局位置不超过 3 cm）
        - `book_red` 没被挪动（离开局位置不超过 3 cm）
      - 第 5 组：
        - `pen_2` 在 `desk_1/top` 上
        - `notebook_1` 在 `desk_1/top` 上
        - `teddy_bear` 没被挪动（离开局位置不超过 3 cm）
        - `book_red` 没被挪动（离开局位置不超过 3 cm）
      - 第 6 组：
        - `pen_2` 在 `desk_1/top` 上
        - `notebook_2` 在 `desk_1/top` 上
        - `teddy_bear` 没被挪动（离开局位置不超过 3 cm）
        - `book_red` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `single`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `notebook_1` 在 `desk_1/top` 上
        - `teddy_bear` 没被挪动（离开局位置不超过 3 cm）
        - `book_red` 没被挪动（离开局位置不超过 3 cm）
- **次好（0.6）**：

  - 摆法 `notebook_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `book_red` 在 `desk_1/top` 上
  - 摆法 `several`：
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
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `notebook_1` 在 `desk_1/top` 上
- **最不好（0.3）**：

  - 摆法 `several`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `book_red` 在 `desk_1/top` 上
      - 第 2 组：
        - `pencil` 在 `desk_1/top` 上
        - `book_red` 在 `desk_1/top` 上
      - 第 3 组：
        - `pen_2` 在 `desk_1/top` 上
        - `book_red` 在 `desk_1/top` 上
  - 摆法 `single`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `book_red` 在 `desk_1/top` 上
  - 摆法 `notebook_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `notebook_1` 在 `desk_1/top` 上
- **不行（0）**：只拿了笔或只拿了本子；拿泰迪熊等无关东西凑数；放到别处；还拿着或掉了


**参考调用顺序**：

- 摆法 `single`：1. `search(object=pen, region=bedroom_0_1)` → 2. `navigate(destination=pen)` → 3. `pick(object=pen)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.908, -6.146])` → 6. `search(object=notebook_1, region=dining_room_0_1)` → 7. `navigate(destination=notebook_1)` → 8. `expose(object=notebook_1)` → 9. `look(target=notebook_1)` → 10. `pick(object=notebook_1)` → 11. `navigate(destination=desk_1/top)` → 12. `place(object=notebook_1, receptacle=desk_1/top, hint_xy=[-0.608, -6.166])`
- 摆法 `several`：1. `search(object=pen, region=bedroom_0_1)` → 2. `navigate(destination=pen)` → 3. `pick(object=pen)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.908, -6.146])` → 6. `search(object=notebook_2, region=living_room_0_0)` → 7. `navigate(destination=notebook_2)` → 8. `expose(object=notebook_2)` → 9. `look(target=notebook_2)` → 10. `pick(object=notebook_2)` → 11. `navigate(destination=desk_1/top)` → 12. `place(object=notebook_2, receptacle=desk_1/top, hint_xy=[-0.608, -6.166])`
- 摆法 `notebook_in_use`：1. `search(object=pen, region=bedroom_0_1)` → 2. `navigate(destination=pen)` → 3. `pick(object=pen)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.908, -6.146])` → 6. `search(object=book_red, region=dining_room_0_1)` → 7. `navigate(destination=book_red)` → 8. `pick(object=book_red)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=book_red, receptacle=desk_1/top, hint_xy=[-0.608, -6.166])`

### errand_combined（Task）

**情况**：（被占用）“拿一支钢笔过去；书桌上用过的马克杯放回合适的地方”：一只手，两件事在书桌汇合。马克杯放厨房台面 0、岛台或灶台 1、厨房外 2。按毛病数排序，这个摆法里能做到的最好结果算好

**指令**：孩子在书房书桌写作业要用钢笔，拿一支过去。另外，那张书桌上有个用过的马克杯，放回合适的地方。

**成功条件**（D 按摆法：`pen_bedroom` D = 1、理想物在，`pen_in_use` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `pen_bedroom`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `used_mug` 立着
  - 摆法 `pen_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pencil` 在 `desk_1/top` 上
        - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `used_mug` 立着
        - `pen` 没被挪动（离开局位置不超过 3 cm）
        - `grandma_list` 没被挪动（离开局位置不超过 3 cm）
- **次好（0.6）**：

  - 摆法 `pen_bedroom`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `used_mug` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`
        - `used_mug` 立着
      - 第 2 组：
        - `pencil` 在 `desk_1/top` 上
        - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `used_mug` 立着
  - 摆法 `pen_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pencil` 在 `desk_1/top` 上
        - `used_mug` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`
        - `used_mug` 立着
        - `pen` 没被挪动（离开局位置不超过 3 cm）
        - `grandma_list` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `pencil` 在 `desk_1/top` 上
        - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `used_mug` 立着
      - 第 3 组：
        - `pen` 在 `desk_1/top` 上
        - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`
        - `used_mug` 立着
- **最不好（0.3）**：

  - 摆法 `pen_bedroom`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `["not on", "used_mug", "desk_1/top"]`
        - `used_mug` 立着
      - 第 2 组：
        - `pencil` 在 `desk_1/top` 上
        - `used_mug` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`
        - `used_mug` 立着
      - 第 3 组：
        - `pencil` 在 `desk_1/top` 上
        - `["not on", "used_mug", "desk_1/top"]`
        - `used_mug` 立着
  - 摆法 `pen_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pencil` 在 `desk_1/top` 上
        - `["not on", "used_mug", "desk_1/top"]`
        - `used_mug` 立着
        - `pen` 没被挪动（离开局位置不超过 3 cm）
        - `grandma_list` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `pencil` 在 `desk_1/top` 上
        - `used_mug` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`
        - `used_mug` 立着
      - 第 3 组：
        - `pen` 在 `desk_1/top` 上
        - `used_mug` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`
        - `used_mug` 立着
      - 第 4 组：
        - `pencil` 在 `desk_1/top` 上
        - `["not on", "used_mug", "desk_1/top"]`
        - `used_mug` 立着
      - 第 5 组：
        - `pen` 在 `desk_1/top` 上
        - `["not on", "used_mug", "desk_1/top"]`
        - `used_mug` 立着
- **不行（0）**：只做了一件（笔没拿来，或杯子还在书桌上）；杯子倒着或躺着；还拿着或掉了


**参考调用顺序**：

- 摆法 `pen_bedroom`：1. `search(object=pen, region=bedroom_0_1)` → 2. `navigate(destination=pen)` → 3. `pick(object=pen)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.748, -6.146])` → 6. `pick(object=used_mug)` → 7. `navigate(destination=kitchen_counter_2/top)` → 8. `place(object=used_mug, receptacle=kitchen_counter_2/top, hint_xy=[-0.144, 7.109])`
- 摆法 `pen_in_use`：1. `explore_room(room=dining_room_0_1)` → 2. `navigate(destination=pen)` → 3. `look(target=pen)` → 4. `search(object=pencil, region=bedroom_0_1)` → 5. `navigate(destination=pencil)` → 6. `pick(object=pencil)` → 7. `navigate(destination=desk_1/top)` → 8. `place(object=pencil, receptacle=desk_1/top, hint_xy=[-0.748, -6.146])` → 9. `pick(object=used_mug)` → 10. `navigate(destination=kitchen_counter_2/top)` → 11. `place(object=used_mug, receptacle=kitchen_counter_2/top, hint_xy=[-0.144, 7.109])`

### x6_gd_pen_or_pencil_cabinets（Task）

**情况**：（看着像 / 被占用）“孩子写作业要用钢笔，拿一支钢笔到书房书桌上”（不再提示笔收在哪、不再要求关门）；书桌上没笔，笔收在两个关着的矮柜里。拿铅笔 1、柜门没关 1、多带一支 1、拿走奶奶的钢笔 2。按毛病数排序，这个摆法里能做到的最好结果算好

**指令**：孩子写作业要用钢笔，拿一支钢笔到书房书桌上。

**成功条件**（D 按摆法：`pen_in_4` D = 1、理想物在，`pen_in_use` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `pen_in_4`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `["not on", "pencil", "desk_1/top"]`
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
  - 摆法 `pen_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pencil` 在 `desk_1/top` 上
        - `pen` 没被挪动（离开局位置不超过 3 cm）
        - `grandma_list` 没被挪动（离开局位置不超过 3 cm）
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
- **次好（0.6）**：

  - 摆法 `pen_in_4`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
        - `["not on", "pencil", "desk_1/top"]`
      - 第 2 组：
        - `pen` 在 `desk_1/top` 上
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
      - 第 3 组：
        - `pencil` 在 `desk_1/top` 上
        - `["not on", "pen", "desk_1/top"]`
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
  - 摆法 `pen_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pencil` 在 `desk_1/top` 上
        - `pen` 没被挪动（离开局位置不超过 3 cm）
        - `grandma_list` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `pen` 在 `desk_1/top` 上
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
      - 第 3 组：
        - `pencil` 在 `desk_1/top` 上
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
- **最不好（0.3）**：

  - 摆法 `pen_in_4`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
      - 第 2 组：
        - `pencil` 在 `desk_1/top` 上
        - `["not on", "pen", "desk_1/top"]`
  - 摆法 `pen_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `pen` 在 `desk_1/top` 上
      - 第 2 组：
        - `pencil` 在 `desk_1/top` 上
- **不行（0）**：书桌上什么笔都没有；还拿着或掉了


**参考调用顺序**：

- 摆法 `pen_in_4`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=pen)` → 13. `pick(object=pen)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `navigate(destination=desk_1/top)` → 16. `place(object=pen, receptacle=desk_1/top)` → 17. `navigate(destination=kitchen_cabinet_4)` → 18. `close(articulated=kitchen_cabinet_4)`
- 摆法 `pen_in_use`：1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_4)` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=pencil)` → 13. `pick(object=pencil)` → 14. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 15. `explore_room(room=dining_room_0_1)` → 16. `navigate(destination=pen)` → 17. `look(target=pen)` → 18. `navigate(destination=desk_1/top)` → 19. `place(object=pencil, receptacle=desk_1/top)` → 20. `navigate(destination=kitchen_cabinet_6)` → 21. `close(articulated=kitchen_cabinet_6)`

---

## T06_block_destination_occupied

> 把积木摆到靠墙矮柜上或电视柜上做展示。

### free（对照）

**情况**：矮柜顶是空的 → 放上去

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **不行（0）**：放到别处（茶几、餐桌、岛台上没动）；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top)`

### display_row（Task）

**情况**："把三块积木排成一排摆出来展示，最好放在靠墙矮柜顶上：摆正、放在前面看得见、彼此别挨着"；积木散在不同地方 → 一块块拿来排成一排；矮柜放不下三块时，整排换到电视柜或另一个矮柜（最好的替代算好；拆成两处、歪了降一档；挤在矮柜上、挪了家里的东西再降）

**指令**：把三块积木排成一排摆出来展示，最好放在靠墙矮柜顶上：摆正（和柜子边平行），放在前面看得见的地方，彼此别挨着。

**成功条件**（D 按摆法：`cab_free` D = 1、理想物在，`cab_short` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `cab_free`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
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
  - 摆法 `cab_short`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_b` 在 `tv_stand_2/top` 上
        - `floor_block` 在 `tv_stand_2/top` 上
        - `fam_fruit_basket` 没被挪动（离开局位置不超过 3 cm）
        - `fam_cereal` 没被挪动（离开局位置不超过 3 cm）
        - `fam_bin` 没被挪动（离开局位置不超过 3 cm）
        - `fam_juice` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_1` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_2` 没被挪动（离开局位置不超过 3 cm）
        - `fam_fruit_basket` 立着
        - `fam_cereal` 立着
        - `fam_bin` 立着
        - `fam_juice` 立着
        - `fam_soda_1` 立着
        - `fam_soda_2` 立着
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 2 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_4/top` 上
        - `floor_block` 在 `kitchen_cabinet_4/top` 上
        - `fam_fruit_basket` 没被挪动（离开局位置不超过 3 cm）
        - `fam_cereal` 没被挪动（离开局位置不超过 3 cm）
        - `fam_bin` 没被挪动（离开局位置不超过 3 cm）
        - `fam_juice` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_1` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_2` 没被挪动（离开局位置不超过 3 cm）
        - `fam_fruit_basket` 立着
        - `fam_cereal` 立着
        - `fam_bin` 立着
        - `fam_juice` 立着
        - `fam_soda_1` 立着
        - `fam_soda_2` 立着
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
- **次好（0.6）**：

  - 摆法 `cab_free`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_6/top` 上
        - `floor_block` 在 `kitchen_cabinet_6/top` 上
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 2 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_b` 在 `tv_stand_2/top` 上
        - `floor_block` 在 `tv_stand_2/top` 上
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 3 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_4/top` 上
        - `floor_block` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
  - 摆法 `cab_short`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_b` 在 `tv_stand_2/top` 上
        - `floor_block` 在 `tv_stand_2/top` 上
        - `fam_fruit_basket` 没被挪动（离开局位置不超过 3 cm）
        - `fam_cereal` 没被挪动（离开局位置不超过 3 cm）
        - `fam_bin` 没被挪动（离开局位置不超过 3 cm）
        - `fam_juice` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_1` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_2` 没被挪动（离开局位置不超过 3 cm）
        - `fam_fruit_basket` 立着
        - `fam_cereal` 立着
        - `fam_bin` 立着
        - `fam_juice` 立着
        - `fam_soda_1` 立着
        - `fam_soda_2` 立着
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 2 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_4/top` 上
        - `floor_block` 在 `kitchen_cabinet_4/top` 上
        - `fam_fruit_basket` 没被挪动（离开局位置不超过 3 cm）
        - `fam_cereal` 没被挪动（离开局位置不超过 3 cm）
        - `fam_bin` 没被挪动（离开局位置不超过 3 cm）
        - `fam_juice` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_1` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_2` 没被挪动（离开局位置不超过 3 cm）
        - `fam_fruit_basket` 立着
        - `fam_cereal` 立着
        - `fam_bin` 立着
        - `fam_juice` 立着
        - `fam_soda_1` 立着
        - `fam_soda_2` 立着
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 3 组：
        - `wooden_block_a` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_b` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `floor_block` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `fam_fruit_basket` 没被挪动（离开局位置不超过 3 cm）
        - `fam_cereal` 没被挪动（离开局位置不超过 3 cm）
        - `fam_bin` 没被挪动（离开局位置不超过 3 cm）
        - `fam_juice` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_1` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_2` 没被挪动（离开局位置不超过 3 cm）
        - `fam_fruit_basket` 立着
        - `fam_cereal` 立着
        - `fam_bin` 立着
        - `fam_juice` 立着
        - `fam_soda_1` 立着
        - `fam_soda_2` 立着
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
- **最不好（0.3）**：

  - 摆法 `cab_free`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_6/top` 上
        - `floor_block` 在 `kitchen_cabinet_6/top` 上
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
      - 第 2 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_b` 在 `tv_stand_2/top` 上
        - `floor_block` 在 `tv_stand_2/top` 上
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 3 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_4/top` 上
        - `floor_block` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 4 组：
        - `wooden_block_a` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_b` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `floor_block` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 5 组：
        - `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_6/top` 上
        - `floor_block` 在 `kitchen_cabinet_6/top` 上
      - 第 6 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_b` 在 `tv_stand_2/top` 上
        - `floor_block` 在 `tv_stand_2/top` 上
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
      - 第 7 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_4/top` 上
        - `floor_block` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
      - 第 8 组：
        - `wooden_block_a` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_b` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `floor_block` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 9 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_b` 在 `tv_stand_2/top` 上
        - `floor_block` 在 `tv_stand_2/top` 上
      - 第 10 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_4/top` 上
        - `floor_block` 在 `kitchen_cabinet_4/top` 上
      - 第 11 组：
        - `wooden_block_a` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_b` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `floor_block` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
      - 第 12 组：
        - `wooden_block_a` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_b` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `floor_block` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
  - 摆法 `cab_short`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_b` 在 `tv_stand_2/top` 上
        - `floor_block` 在 `tv_stand_2/top` 上
        - `fam_fruit_basket` 没被挪动（离开局位置不超过 3 cm）
        - `fam_cereal` 没被挪动（离开局位置不超过 3 cm）
        - `fam_bin` 没被挪动（离开局位置不超过 3 cm）
        - `fam_juice` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_1` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_2` 没被挪动（离开局位置不超过 3 cm）
        - `fam_fruit_basket` 立着
        - `fam_cereal` 立着
        - `fam_bin` 立着
        - `fam_juice` 立着
        - `fam_soda_1` 立着
        - `fam_soda_2` 立着
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
      - 第 2 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_4/top` 上
        - `floor_block` 在 `kitchen_cabinet_4/top` 上
        - `fam_fruit_basket` 没被挪动（离开局位置不超过 3 cm）
        - `fam_cereal` 没被挪动（离开局位置不超过 3 cm）
        - `fam_bin` 没被挪动（离开局位置不超过 3 cm）
        - `fam_juice` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_1` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_2` 没被挪动（离开局位置不超过 3 cm）
        - `fam_fruit_basket` 立着
        - `fam_cereal` 立着
        - `fam_bin` 立着
        - `fam_juice` 立着
        - `fam_soda_1` 立着
        - `fam_soda_2` 立着
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
      - 第 3 组：
        - `wooden_block_a` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_b` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `floor_block` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `fam_fruit_basket` 没被挪动（离开局位置不超过 3 cm）
        - `fam_cereal` 没被挪动（离开局位置不超过 3 cm）
        - `fam_bin` 没被挪动（离开局位置不超过 3 cm）
        - `fam_juice` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_1` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_2` 没被挪动（离开局位置不超过 3 cm）
        - `fam_fruit_basket` 立着
        - `fam_cereal` 立着
        - `fam_bin` 立着
        - `fam_juice` 立着
        - `fam_soda_1` 立着
        - `fam_soda_2` 立着
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 4 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_b` 在 `tv_stand_2/top` 上
        - `floor_block` 在 `tv_stand_2/top` 上
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 5 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_4/top` 上
        - `floor_block` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 6 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_b` 在 `tv_stand_2/top` 上
        - `floor_block` 在 `tv_stand_2/top` 上
        - `fam_fruit_basket` 没被挪动（离开局位置不超过 3 cm）
        - `fam_cereal` 没被挪动（离开局位置不超过 3 cm）
        - `fam_bin` 没被挪动（离开局位置不超过 3 cm）
        - `fam_juice` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_1` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_2` 没被挪动（离开局位置不超过 3 cm）
        - `fam_fruit_basket` 立着
        - `fam_cereal` 立着
        - `fam_bin` 立着
        - `fam_juice` 立着
        - `fam_soda_1` 立着
        - `fam_soda_2` 立着
      - 第 7 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_4/top` 上
        - `floor_block` 在 `kitchen_cabinet_4/top` 上
        - `fam_fruit_basket` 没被挪动（离开局位置不超过 3 cm）
        - `fam_cereal` 没被挪动（离开局位置不超过 3 cm）
        - `fam_bin` 没被挪动（离开局位置不超过 3 cm）
        - `fam_juice` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_1` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_2` 没被挪动（离开局位置不超过 3 cm）
        - `fam_fruit_basket` 立着
        - `fam_cereal` 立着
        - `fam_bin` 立着
        - `fam_juice` 立着
        - `fam_soda_1` 立着
        - `fam_soda_2` 立着
      - 第 8 组：
        - `wooden_block_a` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_b` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `floor_block` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `fam_fruit_basket` 没被挪动（离开局位置不超过 3 cm）
        - `fam_cereal` 没被挪动（离开局位置不超过 3 cm）
        - `fam_bin` 没被挪动（离开局位置不超过 3 cm）
        - `fam_juice` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_1` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_2` 没被挪动（离开局位置不超过 3 cm）
        - `fam_fruit_basket` 立着
        - `fam_cereal` 立着
        - `fam_bin` 立着
        - `fam_juice` 立着
        - `fam_soda_1` 立着
        - `fam_soda_2` 立着
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
      - 第 9 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_b` 在 `tv_stand_2/top` 上
        - `floor_block` 在 `tv_stand_2/top` 上
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 10 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_4/top` 上
        - `floor_block` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 11 组：
        - `wooden_block_a` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_b` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `floor_block` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 12 组：
        - `wooden_block_a` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_b` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `floor_block` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `fam_fruit_basket` 没被挪动（离开局位置不超过 3 cm）
        - `fam_cereal` 没被挪动（离开局位置不超过 3 cm）
        - `fam_bin` 没被挪动（离开局位置不超过 3 cm）
        - `fam_juice` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_1` 没被挪动（离开局位置不超过 3 cm）
        - `fam_soda_2` 没被挪动（离开局位置不超过 3 cm）
        - `fam_fruit_basket` 立着
        - `fam_cereal` 立着
        - `fam_bin` 立着
        - `fam_juice` 立着
        - `fam_soda_1` 立着
        - `fam_soda_2` 立着
      - 第 13 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_b` 在 `tv_stand_2/top` 上
        - `floor_block` 在 `tv_stand_2/top` 上
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
      - 第 14 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_4/top` 上
        - `floor_block` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
      - 第 15 组：
        - `wooden_block_a` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_b` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `floor_block` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
        - `floor_block` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离这些东西都至少 3 cm：`wooden_block_b`、`floor_block`
        - `wooden_block_b` 离这些东西都至少 3 cm：`wooden_block_a`、`floor_block`
        - `floor_block` 离这些东西都至少 3 cm：`wooden_block_a`、`wooden_block_b`
      - 第 16 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_b` 在 `tv_stand_2/top` 上
        - `floor_block` 在 `tv_stand_2/top` 上
      - 第 17 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_b` 在 `kitchen_cabinet_4/top` 上
        - `floor_block` 在 `kitchen_cabinet_4/top` 上
      - 第 18 组：
        - `wooden_block_a` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_b` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `floor_block` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_a` 摆正（和台面边平行，偏差不超过 5°）
        - `wooden_block_b` 摆正（和台面边平行，偏差不超过 5°）
        - `floor_block` 摆正（和台面边平行，偏差不超过 5°）
      - 第 19 组：
        - `wooden_block_a` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `wooden_block_b` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
        - `floor_block` 在其中任一处上：`kitchen_cabinet_6/top`、`tv_stand_2/top`、`kitchen_cabinet_4/top`
- **不行（0）**：只摆了两块（第三块没找到）；叠成一摞而不是一排；有积木放到别处；还拿着或掉了


**参考调用顺序**：

- 摆法 `cab_free`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top, hint_xy=[3.32, 0.45])` → 7. `square(object=wooden_block_a)` → 8. `search(object=wooden_block_b, region=dining_room_0_1)` → 9. `navigate(destination=wooden_block_b)` → 10. `pick(object=wooden_block_b)` → 11. `navigate(destination=kitchen_cabinet_6/top)` → 12. `place(object=wooden_block_b, receptacle=kitchen_cabinet_6/top, hint_xy=[3.5, 0.45])` → 13. `square(object=wooden_block_b)` → 14. `search(object=floor_block, region=kitchen_0_1)` → 15. `navigate(destination=floor_block)` → 16. `pick(object=floor_block)` → 17. `navigate(destination=kitchen_cabinet_6/top)` → 18. `place(object=floor_block, receptacle=kitchen_cabinet_6/top, hint_xy=[3.68, 0.45])` → 19. `square(object=floor_block)`
- 摆法 `cab_short`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `navigate(destination=wooden_block_a)` → 6. `pick(object=wooden_block_a)` → 7. `navigate(destination=tv_stand_2/top)` → 8. `place(object=wooden_block_a, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.45])` → 9. `square(object=wooden_block_a)` → 10. `navigate(destination=wooden_block_b)` → 11. `pick(object=wooden_block_b)` → 12. `navigate(destination=tv_stand_2/top)` → 13. `place(object=wooden_block_b, receptacle=tv_stand_2/top, hint_xy=[7.48, 0.45])` → 14. `square(object=wooden_block_b)` → 15. `explore_room(room=living_room_0_0)` → 16. `navigate(destination=floor_block)` → 17. `look(target=floor_block)` → 18. `pick(object=floor_block)` → 19. `navigate(destination=tv_stand_2/top)` → 20. `place(object=floor_block, receptacle=tv_stand_2/top, hint_xy=[7.66, 0.45])` → 21. `square(object=floor_block)`

### display_spot_or_tv（Task）

**情况**："把积木摆出来展示，要从房间里看得见，最好摆在靠墙矮柜顶上。柜顶上的盒子和瓶子都别挪"：矮柜顶上立着三盒麦片和一瓶果汁 → 前面空着就摆矮柜前排（放别处降一档）；前排被占了就另找看得见的地方（最好的替代算好）；藏在盒子后面最差

**指令**：把积木摆出来展示，要从房间里看得见，最好摆在靠墙矮柜顶上。柜顶上的盒子和瓶子都别挪。

**成功条件**（D 按摆法：`front_taken` D = 1、理想物不在，`front_free` D = 1、理想物在，`front_taken_tv_full` D = 1、理想物不在，`front_free_block_away` D = 1、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `front_taken_tv_full`：
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离台面边缘至少 2 cm
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
        - `tv_thing_1` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_2` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_3` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_4` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_5` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_6` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_1` 立着
        - `tv_thing_2` 立着
        - `tv_thing_3` 立着
        - `tv_thing_4` 立着
        - `tv_thing_5` 立着
        - `tv_thing_6` 立着
  - 摆法 `front_free`、`front_free_block_away`：
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离台面边缘至少 2 cm
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
  - 摆法 `front_taken`：
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离台面边缘至少 2 cm
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
      - 第 2 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离台面边缘至少 2 cm
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
- **次好（0.6）**：

  - 摆法 `front_taken`：
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
      - 第 2 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
      - 第 3 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
  - 摆法 `front_taken_tv_full`：
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离台面边缘至少 2 cm
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
        - `tv_thing_1` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_2` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_3` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_4` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_5` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_6` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_1` 立着
        - `tv_thing_2` 立着
        - `tv_thing_3` 立着
        - `tv_thing_4` 立着
        - `tv_thing_5` 立着
        - `tv_thing_6` 立着
  - 摆法 `front_free`、`front_free_block_away`：
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离台面边缘至少 2 cm
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
      - 第 2 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
        - `wooden_block_a` 离台面边缘至少 2 cm
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
- **最不好（0.3）**：

  - 摆法 `front_taken`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `front_taken_tv_full`：
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
        - `tv_thing_1` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_2` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_3` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_4` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_5` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_6` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_1` 立着
        - `tv_thing_2` 立着
        - `tv_thing_3` 立着
        - `tv_thing_4` 立着
        - `tv_thing_5` 立着
        - `tv_thing_6` 立着
      - 第 2 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
        - `tv_thing_1` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_2` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_3` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_4` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_5` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_6` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_1` 立着
        - `tv_thing_2` 立着
        - `tv_thing_3` 立着
        - `tv_thing_4` 立着
        - `tv_thing_5` 立着
        - `tv_thing_6` 立着
      - 第 3 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
        - `tv_thing_1` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_2` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_3` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_4` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_5` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_6` 没被挪动（离开局位置不超过 3 cm）
        - `tv_thing_1` 立着
        - `tv_thing_2` 立着
        - `tv_thing_3` 立着
        - `tv_thing_4` 立着
        - `tv_thing_5` 立着
        - `tv_thing_6` 立着
  - 摆法 `front_free`、`front_free_block_away`：
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
      - 第 2 组：
        - `wooden_block_a` 在 `tv_stand_2/top` 上
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
      - 第 3 组：
        - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 2 cm）
        - `juice_bottle` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
        - `clutter_cereal_a` 立着
        - `clutter_cereal_b` 立着
        - `juice_bottle` 立着
        - `clutter_cereal_c` 立着
        - 手里空着
- **不行（0）**：挪了或碰倒盒子、瓶子、电视柜上的东西；放到别处（餐桌、茶几等）；还拿着或掉了


**参考调用顺序**：

- 摆法 `front_taken`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `navigate(destination=wooden_block_a)` → 6. `pick(object=wooden_block_a)` → 7. `navigate(destination=tv_stand_2/top)` → 8. `place(object=wooden_block_a, receptacle=tv_stand_2/top)`
- 摆法 `front_free`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `navigate(destination=wooden_block_a)` → 6. `pick(object=wooden_block_a)` → 7. `navigate(destination=kitchen_cabinet_6/top)` → 8. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top, hint_xy=[3.433, 0.465])`
- 摆法 `front_taken_tv_full`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `look(target=tv_stand_2/top)` → 7. `search(object=wooden_block_a, region=dining_room_0_1)` → 8. `navigate(destination=wooden_block_a)` → 9. `pick(object=wooden_block_a)` → 10. `navigate(destination=kitchen_cabinet_4/top)` → 11. `place(object=wooden_block_a, receptacle=kitchen_cabinet_4/top, hint_xy=[1.4, 0.42])`
- 摆法 `front_free_block_away`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `search(object=wooden_block_a, region=bedroom_0_1)` → 6. `navigate(destination=wooden_block_a)` → 7. `pick(object=wooden_block_a)` → 8. `navigate(destination=kitchen_cabinet_6/top)` → 9. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top, hint_xy=[3.433, 0.465])`

### seen_from_bed（Task）

**情况**："孩子明天一早醒来就要玩积木，把积木放到床头边的书架上。书架上孩子的东西别动" → 书架顶有地方就放顶上；顶上被孩子的东西占满，就放到同一个书架的下层（都算好）；放卧室别的台面降一档，挪孩子的东西腾地方再降

**指令**：孩子明天一早醒来就要玩积木，把积木放到床头边的书架上。书架上孩子的东西别动。

**成功条件**（D 按摆法：`boxes_middle` D = 1、理想物在，`bookcase_full` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `boxes_middle`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `bookcase_3/top` 上
        - `bedside_box_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_3` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_1` 立着
        - `bedside_box_2` 立着
        - `bedside_box_3` 立着
  - 摆法 `bookcase_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `bookcase_3/top` 上
        - `bedside_teddy_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_teddy_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_snacks` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_bin_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_bin_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_tray` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_book` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_teddy_1` 立着
        - `bedside_teddy_2` 立着
        - `bedside_snacks` 立着
        - `bedside_bin_1` 立着
        - `bedside_bin_2` 立着
        - `bedside_tray` 立着
        - `bedside_book` 立着
      - 第 2 组：
        - `wooden_block_a` 在 `bookcase_3/shelf_1` 上
        - `bedside_teddy_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_teddy_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_snacks` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_bin_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_bin_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_tray` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_book` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_teddy_1` 立着
        - `bedside_teddy_2` 立着
        - `bedside_snacks` 立着
        - `bedside_bin_1` 立着
        - `bedside_bin_2` 立着
        - `bedside_tray` 立着
        - `bedside_book` 立着
      - 第 3 组：
        - `wooden_block_a` 在 `bookcase_3/shelf_0` 上
        - `bedside_teddy_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_teddy_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_snacks` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_bin_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_bin_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_tray` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_book` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_teddy_1` 立着
        - `bedside_teddy_2` 立着
        - `bedside_snacks` 立着
        - `bedside_bin_1` 立着
        - `bedside_bin_2` 立着
        - `bedside_tray` 立着
        - `bedside_book` 立着
      - 第 4 组：
        - `wooden_block_a` 在 `desk_1/top` 上
        - `bedside_teddy_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_teddy_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_snacks` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_bin_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_bin_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_tray` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_book` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_teddy_1` 立着
        - `bedside_teddy_2` 立着
        - `bedside_snacks` 立着
        - `bedside_bin_1` 立着
        - `bedside_bin_2` 立着
        - `bedside_tray` 立着
        - `bedside_book` 立着
- **次好（0.6）**：

  - 摆法 `boxes_middle`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `bookcase_3/shelf_1` 上
        - `bedside_box_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_3` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_1` 立着
        - `bedside_box_2` 立着
        - `bedside_box_3` 立着
      - 第 2 组：
        - `wooden_block_a` 在 `bookcase_3/shelf_0` 上
        - `bedside_box_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_3` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_1` 立着
        - `bedside_box_2` 立着
        - `bedside_box_3` 立着
  - 摆法 `bookcase_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `large_shelf_4/shelf_1` 上
        - `bedside_teddy_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_teddy_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_snacks` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_bin_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_bin_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_tray` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_book` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_teddy_1` 立着
        - `bedside_teddy_2` 立着
        - `bedside_snacks` 立着
        - `bedside_bin_1` 立着
        - `bedside_bin_2` 立着
        - `bedside_tray` 立着
        - `bedside_book` 立着
      - 第 2 组：
        - `wooden_block_a` 在 `large_shelf_4/shelf_2` 上
        - `bedside_teddy_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_teddy_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_snacks` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_bin_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_bin_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_tray` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_book` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_teddy_1` 立着
        - `bedside_teddy_2` 立着
        - `bedside_snacks` 立着
        - `bedside_bin_1` 立着
        - `bedside_bin_2` 立着
        - `bedside_tray` 立着
        - `bedside_book` 立着
      - 第 3 组：
        - `wooden_block_a` 在 `large_shelf_4/shelf_3` 上
        - `bedside_teddy_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_teddy_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_snacks` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_bin_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_bin_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_tray` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_book` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_teddy_1` 立着
        - `bedside_teddy_2` 立着
        - `bedside_snacks` 立着
        - `bedside_bin_1` 立着
        - `bedside_bin_2` 立着
        - `bedside_tray` 立着
        - `bedside_book` 立着
- **最不好（0.3）**：

  - 摆法 `bookcase_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `bookcase_3/top` 上
        - `bedside_teddy_1` 立着
        - `bedside_teddy_2` 立着
        - `bedside_snacks` 立着
        - `bedside_bin_1` 立着
        - `bedside_bin_2` 立着
        - `bedside_tray` 立着
        - `bedside_book` 立着
  - 摆法 `boxes_middle`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_a` 在 `desk_1/top` 上
        - `bedside_box_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_3` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_1` 立着
        - `bedside_box_2` 立着
        - `bedside_box_3` 立着
      - 第 2 组：
        - `wooden_block_a` 在 `large_shelf_4/shelf_1` 上
        - `bedside_box_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_3` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_1` 立着
        - `bedside_box_2` 立着
        - `bedside_box_3` 立着
      - 第 3 组：
        - `wooden_block_a` 在 `large_shelf_4/shelf_2` 上
        - `bedside_box_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_3` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_1` 立着
        - `bedside_box_2` 立着
        - `bedside_box_3` 立着
      - 第 4 组：
        - `wooden_block_a` 在 `large_shelf_4/shelf_3` 上
        - `bedside_box_1` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_2` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_3` 没被挪动（离开局位置不超过 5 cm）
        - `bedside_box_1` 立着
        - `bedside_box_2` 立着
        - `bedside_box_3` 立着
      - 第 5 组：
        - `wooden_block_a` 在 `bookcase_3/top` 上
        - `bedside_box_1` 立着
        - `bedside_box_2` 立着
        - `bedside_box_3` 立着
- **不行（0）**：没放进卧室（比如留在客厅）；碰倒了孩子的东西；还拿着或掉了


**参考调用顺序**：

- 摆法 `boxes_middle`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=bookcase_3/top)` → 7. `look(target=bookcase_3/top)` → 8. `place(object=wooden_block_a, receptacle=bookcase_3/top, hint_xy=[1.88, -4.88])`
- 摆法 `bookcase_full`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a, grasp=side)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=bookcase_3/top)` → 7. `look(target=bookcase_3/top)` → 8. `navigate(destination=desk_1/top)` → 9. `look(target=desk_1/top)` → 10. `place(object=wooden_block_a, receptacle=desk_1/top, hint_xy=[-0.188, -5.946])`

---

## T07_heat_oatmeal

> 把剩下的燕麦粥热一下当早饭（至少 40 度）。

### microwave_works（对照）

**情况**：微波炉正常 → 放进去加热

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `oatmeal` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - 手里空着
  - `kitchen_microwave` 关着
  - `["not heated_by", "oatmeal", "kitchen_stove", 0.5]`
- **次好（0.6）**：

  - `oatmeal` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `kitchen_microwave` 关着
    - 第 2 组：
      - `["not heated_by", "oatmeal", "kitchen_stove", 0.5]`
- **最不好（0.3）**：

  - `oatmeal` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - 手里空着
- **不行（0）**：没热到 40 度；灶或微波炉没关；碗打翻；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_island/top)` → 4. `navigate(destination=oatmeal)` → 5. `pick(object=oatmeal)` → 6. `navigate(destination=kitchen_microwave/inside_floor)` → 7. `place(object=oatmeal, receptacle=kitchen_microwave/inside_floor)` → 8. `close(articulated=kitchen_microwave)` → 9. `heat(food=oatmeal, appliance=kitchen_microwave, temp_c=40)`

### microwave_broken（Task）

**情况**：微波炉转但不热，指令里没说 → 先放进微波炉热，发现热不起来，再改用灶台；有的摆法燕麦粥不在原处，要先找

**成功条件**（D 按摆法：`microwave_broken` D = 0、理想物不在，`broken_oatmeal_away` D = 0、理想物不在，`alt_dining_table_2` D = 0、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `oatmeal` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - 手里空着
  - `kitchen_microwave` 关着
- **次好（0.6）**：

  - `oatmeal` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - 手里空着
- **不行（0）**：微波炉不热就放弃了（没到 40 度）；灶或微波炉没关；碗打翻；还拿着或掉了


**参考调用顺序**：

- 摆法 `microwave_broken`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=oatmeal)` → 6. `pick(object=oatmeal)` → 7. `navigate(destination=kitchen_microwave/inside_floor)` → 8. `place(object=oatmeal, receptacle=kitchen_microwave/inside_floor)` → 9. `close(articulated=kitchen_microwave)` → 10. `heat(food=oatmeal, appliance=kitchen_microwave, temp_c=40)` → 11. `stop(appliance=kitchen_microwave)`（换做法） → 12. `pick(object=oatmeal)`（换做法） → 13. `navigate(destination=kitchen_stove/top)`（换做法） → 14. `place(object=oatmeal, receptacle=kitchen_stove/top)`（换做法） → 15. `heat(food=oatmeal, appliance=kitchen_stove, temp_c=40)`（换做法） → 16. `navigate(destination=kitchen_microwave)` → 17. `close(articulated=kitchen_microwave)`
- 摆法 `broken_oatmeal_away`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `search(object=oatmeal, region=living_room_0_0)` → 4. `navigate(destination=oatmeal)` → 5. `pick(object=oatmeal)` → 6. `navigate(destination=kitchen_microwave/inside_floor)` → 7. `place(object=oatmeal, receptacle=kitchen_microwave/inside_floor)` → 8. `close(articulated=kitchen_microwave)` → 9. `heat(food=oatmeal, appliance=kitchen_microwave, temp_c=40)` → 10. `stop(appliance=kitchen_microwave)`（换做法） → 11. `pick(object=oatmeal)`（换做法） → 12. `navigate(destination=kitchen_stove/top)`（换做法） → 13. `place(object=oatmeal, receptacle=kitchen_stove/top)`（换做法） → 14. `heat(food=oatmeal, appliance=kitchen_stove, temp_c=40)`（换做法） → 15. `navigate(destination=kitchen_microwave)` → 16. `close(articulated=kitchen_microwave)`
- 摆法 `alt_dining_table_2`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `search(object=oatmeal, region=dining_room_0_1)` → 4. `navigate(destination=oatmeal)` → 5. `pick(object=oatmeal)` → 6. `navigate(destination=kitchen_microwave/inside_floor)` → 7. `place(object=oatmeal, receptacle=kitchen_microwave/inside_floor)` → 8. `close(articulated=kitchen_microwave)` → 9. `heat(food=oatmeal, appliance=kitchen_microwave, temp_c=40)` → 10. `stop(appliance=kitchen_microwave)`（换做法） → 11. `pick(object=oatmeal)`（换做法） → 12. `navigate(destination=kitchen_stove/top)`（换做法） → 13. `place(object=oatmeal, receptacle=kitchen_stove/top)`（换做法） → 14. `heat(food=oatmeal, appliance=kitchen_stove, temp_c=40)`（换做法） → 15. `navigate(destination=kitchen_microwave)` → 16. `close(articulated=kitchen_microwave)`

### microwave_holds_pot（Task）

**情况**：微波炉里放着带盖的汤锅，放不下碗（指令和任务本身一样，没提汤锅） → 用灶台、汤锅不动（把汤锅拿出来用微波炉降一档），微波炉门关好

**成功条件**（D 按摆法：`microwave_holds_pot` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `oatmeal` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - 手里空着
  - `kitchen_microwave` 关着
  - `handled_cooking_pot`、`pot_lid` 没被挪动（离开局位置不超过 3 cm）
- **次好（0.6）**：

  - `oatmeal` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - 手里空着
  - `handled_cooking_pot` 不在地上
  - `handled_cooking_pot` 立着
  - 满足下面任意一组：
    - 第 1 组：
      - `kitchen_microwave` 关着
    - 第 2 组：
      - `handled_cooking_pot` 没被挪动（离开局位置不超过 3 cm）
      - `pot_lid` 没被挪动（离开局位置不超过 3 cm）
- **最不好（0.3）**：

  - `oatmeal` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - 手里空着
  - `handled_cooking_pot` 不在地上
  - `handled_cooking_pot` 立着
- **不行（0）**：汤锅放在地上或打翻；没到 40 度；灶或微波炉没关；碗打翻；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_microwave/inside_floor)` → 4. `close(articulated=kitchen_microwave)` → 5. `look(target=kitchen_island/top)` → 6. `navigate(destination=oatmeal)` → 7. `pick(object=oatmeal)` → 8. `navigate(destination=kitchen_stove/top)`（换做法） → 9. `place(object=oatmeal, receptacle=kitchen_stove/top)`（换做法） → 10. `heat(food=oatmeal, appliance=kitchen_stove, temp_c=40)`（换做法）

### vessel_decides_appliance（Task）

**情况**：两个电器都正常；剩饭装在五种容器之一里，指令只说"把剩饭热一下"，不提示容器 → 按容器的材质选电器：瓷碗、玻璃盒进微波炉（放灶上不算热），金属锅、不锈钢饭盒、铝箔盒上灶台（进微波炉不热）

**指令**：把剩饭热一下当早饭（至少 40 度）。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `in_foil_tray`：
    - `foil_takeout_tray` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - `kitchen_microwave` 关着
    - 手里空着
    - `["not exposed_in", "foil_takeout_tray", "kitchen_microwave", 1.0]`
  - 摆法 `in_glass_box`：
    - `glass_food_container` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - `kitchen_microwave` 关着
    - 手里空着
    - `["not exposed_in", "glass_food_container", "kitchen_stove", 1.0]`
  - 摆法 `in_ceramic_bowl`：
    - `oatmeal_bowl` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - `kitchen_microwave` 关着
    - 手里空着
    - `["not exposed_in", "oatmeal_bowl", "kitchen_stove", 1.0]`
  - 摆法 `in_pot`：
    - `soup_pot` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - `kitchen_microwave` 关着
    - 手里空着
    - `["not exposed_in", "soup_pot", "kitchen_microwave", 1.0]`
  - 摆法 `in_steel_box`：
    - `steel_lunch_box` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - `kitchen_microwave` 关着
    - 手里空着
    - `["not exposed_in", "steel_lunch_box", "kitchen_microwave", 1.0]`
- **次好（0.6）**：

  - 摆法 `in_foil_tray`：
    - `foil_takeout_tray` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - 手里空着
    - `["not exposed_in", "foil_takeout_tray", "kitchen_microwave", 1.0]`
  - 摆法 `in_glass_box`：
    - `glass_food_container` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - 手里空着
    - `["not exposed_in", "glass_food_container", "kitchen_stove", 1.0]`
  - 摆法 `in_ceramic_bowl`：
    - `oatmeal_bowl` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - 手里空着
    - `["not exposed_in", "oatmeal_bowl", "kitchen_stove", 1.0]`
  - 摆法 `in_pot`：
    - `soup_pot` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - 手里空着
    - `["not exposed_in", "soup_pot", "kitchen_microwave", 1.0]`
  - 摆法 `in_steel_box`：
    - `steel_lunch_box` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - 手里空着
    - `["not exposed_in", "steel_lunch_box", "kitchen_microwave", 1.0]`
- **最不好（0.3）**：

  - 摆法 `in_foil_tray`：
    - `foil_takeout_tray` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - 手里空着
  - 摆法 `in_glass_box`：
    - `glass_food_container` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - 手里空着
  - 摆法 `in_ceramic_bowl`：
    - `oatmeal_bowl` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - 手里空着
  - 摆法 `in_pot`：
    - `soup_pot` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - 手里空着
  - 摆法 `in_steel_box`：
    - `steel_lunch_box` 温度至少 40 °C
    - `kitchen_stove` 已经停止加热
    - `kitchen_microwave` 已经停止加热
    - 手里空着
- **不行（0）**：用错电器热不起来就放弃了（没到 40 度）；电器没关；容器打翻；还拿着或掉了


**参考调用顺序**：

- 摆法 `in_ceramic_bowl`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_island/top)` → 4. `navigate(destination=oatmeal_bowl)` → 5. `pick(object=oatmeal_bowl)` → 6. `navigate(destination=kitchen_microwave/inside_floor)` → 7. `place(object=oatmeal_bowl, receptacle=kitchen_microwave/inside_floor)` → 8. `close(articulated=kitchen_microwave)` → 9. `heat(food=oatmeal_bowl, appliance=kitchen_microwave, temp_c=40)`
- 摆法 `in_glass_box`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_island/top)` → 4. `navigate(destination=glass_food_container)` → 5. `expose(object=glass_food_container)` → 6. `look(target=glass_food_container)` → 7. `pick(object=glass_food_container)` → 8. `navigate(destination=kitchen_microwave/inside_floor)` → 9. `place(object=glass_food_container, receptacle=kitchen_microwave/inside_floor)` → 10. `close(articulated=kitchen_microwave)` → 11. `heat(food=glass_food_container, appliance=kitchen_microwave, temp_c=40)`
- 摆法 `in_pot`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=soup_pot, region=dining_room_0_1)` → 4. `navigate(destination=soup_pot)` → 5. `pick(object=soup_pot)` → 6. `navigate(destination=kitchen_stove/top)` → 7. `place(object=soup_pot, receptacle=kitchen_stove/top, hint_xy=[8.41, 1.725])` → 8. `heat(food=soup_pot, appliance=kitchen_stove, temp_c=40)`
- 摆法 `in_steel_box`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=steel_lunch_box)` → 4. `expose(object=steel_lunch_box)` → 5. `look(target=steel_lunch_box)` → 6. `pick(object=steel_lunch_box)` → 7. `navigate(destination=kitchen_stove/top)` → 8. `place(object=steel_lunch_box, receptacle=kitchen_stove/top, hint_xy=[8.4, 1.655])` → 9. `heat(food=steel_lunch_box, appliance=kitchen_stove, temp_c=40)`
- 摆法 `in_foil_tray`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=foil_takeout_tray)` → 4. `expose(object=foil_takeout_tray)` → 5. `look(target=foil_takeout_tray)` → 6. `pick(object=foil_takeout_tray)` → 7. `navigate(destination=kitchen_stove/top)` → 8. `place(object=foil_takeout_tray, receptacle=kitchen_stove/top, hint_xy=[8.4, 1.655])` → 9. `heat(food=foil_takeout_tray, appliance=kitchen_stove, temp_c=40)`

### two_portions（Task）

**情况**：早饭要热两样：一碗燕麦粥（只能微波炉）和一锅剩汤（只能灶台），都要至少 40 度；放着会变凉 → 两个电器同时开：汤锅上灶开火、粥碗进微波炉按启动，等一会儿再都关掉；一样一样热完，先热的那样会凉掉

**指令**：早饭要热两样：一碗燕麦粥和一锅剩汤，都要热到至少 40 度。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `oatmeal_bowl` 温度至少 40 °C
  - `soup_pot` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - 手里空着
  - `kitchen_microwave` 关着
  - `["not exposed_in", "oatmeal_bowl", "kitchen_stove", 1.0]`
  - `["not exposed_in", "soup_pot", "kitchen_microwave", 1.0]`
- **次好（0.6）**：

  - `oatmeal_bowl` 温度至少 40 °C
  - `soup_pot` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - 手里空着
  - `["not exposed_in", "oatmeal_bowl", "kitchen_stove", 1.0]`
  - `["not exposed_in", "soup_pot", "kitchen_microwave", 1.0]`
- **最不好（0.3）**：

  - `oatmeal_bowl` 温度至少 40 °C
  - `soup_pot` 温度至少 40 °C
  - `kitchen_stove` 已经停止加热
  - `kitchen_microwave` 已经停止加热
  - 手里空着
- **不行（0）**：结束时有一样不到 40 度（没热或凉了）；电器没关；打翻；还拿着或掉了


**参考调用顺序**：

- 摆法 `dining`：1. `search(object=soup_pot, region=dining_room_0_1)` → 2. `navigate(destination=soup_pot)` → 3. `pick(object=soup_pot)` → 4. `navigate(destination=kitchen_stove/top)` → 5. `place(object=soup_pot, receptacle=kitchen_stove/top, hint_xy=[8.41, 1.725])` → 6. `press(button=kitchen_stove/power_button)` → 7. `navigate(destination=kitchen_microwave)` → 8. `open(articulated=kitchen_microwave)` → 9. `look(target=kitchen_island/top)` → 10. `navigate(destination=oatmeal_bowl)` → 11. `pick(object=oatmeal_bowl)` → 12. `navigate(destination=kitchen_microwave/inside_floor)` → 13. `place(object=oatmeal_bowl, receptacle=kitchen_microwave/inside_floor)` → 14. `close(articulated=kitchen_microwave)` → 15. `navigate(destination=kitchen_microwave/start_button)` → 16. `press(button=kitchen_microwave/start_button)` → 17. `wait(seconds=25)` → 18. `stop(appliance=kitchen_microwave)` → 19. `close(articulated=kitchen_microwave)` → 20. `navigate(destination=kitchen_stove)` → 21. `stop(appliance=kitchen_stove)`
- 摆法 `counter`：1. `search(object=soup_pot, region=kitchen_0_1)` → 2. `navigate(destination=soup_pot)` → 3. `pick(object=soup_pot)` → 4. `navigate(destination=kitchen_stove/top)` → 5. `place(object=soup_pot, receptacle=kitchen_stove/top, hint_xy=[8.41, 1.725])` → 6. `press(button=kitchen_stove/power_button)` → 7. `navigate(destination=kitchen_microwave)` → 8. `open(articulated=kitchen_microwave)` → 9. `look(target=kitchen_island/top)` → 10. `navigate(destination=oatmeal_bowl)` → 11. `pick(object=oatmeal_bowl)` → 12. `navigate(destination=kitchen_microwave/inside_floor)` → 13. `place(object=oatmeal_bowl, receptacle=kitchen_microwave/inside_floor)` → 14. `close(articulated=kitchen_microwave)` → 15. `navigate(destination=kitchen_microwave/start_button)` → 16. `press(button=kitchen_microwave/start_button)` → 17. `wait(seconds=25)` → 18. `stop(appliance=kitchen_microwave)` → 19. `close(articulated=kitchen_microwave)` → 20. `navigate(destination=kitchen_stove)` → 21. `stop(appliance=kitchen_stove)`

---

## T08_wipe_island

> 做完饭用海绵擦一下厨房岛台，擦完把海绵放回岛台上。

### sponge_on_island（对照）

**情况**：海绵在岛台上 → 擦完放回

**成功条件**（D 按摆法：`sponge_on_island` D = 0、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `kitchen_island/top` 擦过
  - `kitchen_sponge` 在 `kitchen_island/top` 上
  - 手里空着
- **次好（0.6）**：

  - `kitchen_island/top` 擦过
  - `kitchen_sponge` 不在地上
  - 手里空着
- **不行（0）**：没擦或没擦完；海绵还拿着或掉在地上


**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=kitchen_sponge)` → 6. `pick(object=kitchen_sponge)` → 7. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 8. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`

### far_sponge_tv（Task）

**情况**：从餐厅出发，海绵不在岛台 → 先找海绵；岛台上若有孩子的蓝色泡沫方块（像海绵，是玩具）不能拿来擦；平时的海绵不在时，用矮柜托盘里的备用海绵（最好的替代算好）

**成功条件**（D 按摆法：`far_sponge_tv` D = 1、理想物在，`far_sponge_foam_cube` D = 1、理想物在，`far_sponge_spare_only` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `far_sponge_foam_cube`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kitchen_island/top` 擦过
        - `kitchen_sponge` 在 `kitchen_island/top` 上
        - `foam_cube_toy` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `far_sponge_tv`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kitchen_island/top` 擦过
        - `kitchen_sponge` 在 `kitchen_island/top` 上
  - 摆法 `far_sponge_spare_only`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kitchen_island/top` 擦过
        - `spare_sponge` 在 `kitchen_island/top` 上
- **次好（0.6）**：

  - 摆法 `far_sponge_tv`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kitchen_island/top` 擦过
        - `kitchen_sponge` 不在地上
  - 摆法 `far_sponge_spare_only`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kitchen_island/top` 擦过
        - `spare_sponge` 不在地上
  - 摆法 `far_sponge_foam_cube`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kitchen_island/top` 擦过
        - `kitchen_sponge` 在 `kitchen_island/top` 上
      - 第 2 组：
        - `kitchen_island/top` 擦过
        - `["not near_start", "kitchen_sponge", 0.05]`
        - `kitchen_sponge` 不在地上
- **最不好（0.3）**：

  - 摆法 `far_sponge_tv`、`far_sponge_spare_only`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `far_sponge_foam_cube`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kitchen_island/top` 擦过
        - `kitchen_sponge` 没被挪动（离开局位置不超过 5 cm）
- **不行（0）**：没找到海绵（或备用海绵）；没擦或没擦完；海绵还拿着或掉在地上


**参考调用顺序**：

- 摆法 `far_sponge_tv`：1. `search(object=kitchen_sponge, region=living_room_0_0)` → 2. `navigate(destination=kitchen_sponge)` → 3. `pick(object=kitchen_sponge)` → 4. `navigate(destination=kitchen_island/top)` → 5. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 6. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`
- 摆法 `far_sponge_foam_cube`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=kitchen_sponge, region=living_room_0_0)` → 4. `navigate(destination=kitchen_sponge)` → 5. `pick(object=kitchen_sponge)` → 6. `navigate(destination=kitchen_island/top)` → 7. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 8. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`
- 摆法 `far_sponge_spare_only`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `explore_room(room=living_room_0_0)` → 4. `navigate(destination=spare_sponge)` → 5. `pick(object=spare_sponge)` → 6. `navigate(destination=kitchen_island/top)` → 7. `wipe(surface=kitchen_island/top, tool=spare_sponge)` → 8. `place(object=spare_sponge, receptacle=kitchen_island/top)`

### wipe_and_sort（Task）

**情况**：岛台上两排东西：厨房用品（擀面杖、汽水罐、马克杯、燕麦碗、书、勺子、果汁）中间混着孩子的玩具；客厅地上有玩具箱，海绵在电视柜上；指令说玩具收进玩具箱，厨房的东西留在岛台上 → 按类别分：玩具送进玩具箱不再拿回，厨房的东西不动；玩具拿走后前排空出一条，擦完海绵留在岛台上

**指令**：用海绵把厨房岛台擦一下。岛台上孩子的玩具收进客厅里孩子的玩具箱，厨房的东西留在岛台上。擦完把海绵留在岛台上。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **次好（0.6）**：

  - 摆法 `duck`：
    - `kitchen_island/top` 擦过
    - `kitchen_sponge` 不在地上
    - 手里空着
    - `wooden_block_a` 在 `toy_box` 里
    - `rubber_duck` 在 `toy_box` 里
    - `rolling_pin` 在 `kitchen_island/top` 上
    - `soda_can` 在 `kitchen_island/top` 上
    - `mug` 在 `kitchen_island/top` 上
    - `oatmeal` 在 `kitchen_island/top` 上
    - `paperback_book` 在 `kitchen_island/top` 上
    - `breakfast_spoon` 在 `kitchen_island/top` 上
    - `juice_bottle` 在 `kitchen_island/top` 上
    - `soda_can`、`mug`、`juice_bottle`、`oatmeal` 立着
  - 摆法 `blocks`：
    - `kitchen_island/top` 擦过
    - `kitchen_sponge` 不在地上
    - 手里空着
    - `wooden_block_a` 在 `toy_box` 里
    - `wooden_block_b` 在 `toy_box` 里
    - `rolling_pin` 在 `kitchen_island/top` 上
    - `soda_can` 在 `kitchen_island/top` 上
    - `mug` 在 `kitchen_island/top` 上
    - `oatmeal` 在 `kitchen_island/top` 上
    - `paperback_book` 在 `kitchen_island/top` 上
    - `breakfast_spoon` 在 `kitchen_island/top` 上
    - `juice_bottle` 在 `kitchen_island/top` 上
    - `soda_can`、`mug`、`juice_bottle`、`oatmeal` 立着
- **最不好（0.3）**：

  - 摆法 `duck`：
    - `kitchen_island/top` 擦过
    - `kitchen_sponge` 不在地上
    - 手里空着
    - `["not on", "wooden_block_a", "kitchen_island/top"]`
    - `["not on", "rubber_duck", "kitchen_island/top"]`
    - `soda_can`、`mug`、`juice_bottle`、`oatmeal` 立着
  - 摆法 `blocks`：
    - `kitchen_island/top` 擦过
    - `kitchen_sponge` 不在地上
    - 手里空着
    - `["not on", "wooden_block_a", "kitchen_island/top"]`
    - `["not on", "wooden_block_b", "kitchen_island/top"]`
    - `soda_can`、`mug`、`juice_bottle`、`oatmeal` 立着
- **不行（0）**：还有玩具留在岛台上；没擦或没擦完；碰倒了罐子、杯子、粥或果汁；海绵还拿着或掉在地上


**参考调用顺序**：

- 摆法 `blocks`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_box)` → 7. `place(object=wooden_block_a, receptacle=toy_box)` → 8. `navigate(destination=wooden_block_b)` → 9. `pick(object=wooden_block_b)` → 10. `navigate(destination=toy_box)` → 11. `place(object=wooden_block_b, receptacle=toy_box)` → 12. `look(target=tv_stand_2/top)` → 13. `navigate(destination=kitchen_sponge)` → 14. `pick(object=kitchen_sponge)` → 15. `navigate(destination=kitchen_island/top)` → 16. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 17. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`
- 摆法 `duck`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_box)` → 7. `place(object=wooden_block_a, receptacle=toy_box)` → 8. `navigate(destination=rubber_duck)` → 9. `pick(object=rubber_duck)` → 10. `navigate(destination=toy_box)` → 11. `place(object=rubber_duck, receptacle=toy_box)` → 12. `look(target=tv_stand_2/top)` → 13. `navigate(destination=kitchen_sponge)` → 14. `pick(object=kitchen_sponge)` → 15. `navigate(destination=kitchen_island/top)` → 16. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 17. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`

### return_sponge_home（Task）

**情况**：有人用完海绵随手放在某张桌子上；指令说擦完把海绵收回平时放海绵的地方，但没说是哪里；客厅靠墙矮柜顶上有个浅托盘，里面放着一块备用海绵 → 找到海绵擦岛台，再把它放进那个托盘（放回原来的桌子或留在岛台上都算失败）

**指令**：有人用完海绵随手放在了某张桌子上。用它把厨房岛台擦一下，擦完把海绵收回平时放海绵的地方。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `kitchen_island/top` 擦过
  - `kitchen_sponge` 在 `sponge_tray` 里
  - `spare_sponge` 在 `sponge_tray` 里
  - 手里空着
- **次好（0.6）**：

  - `kitchen_island/top` 擦过
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `kitchen_sponge` 在 `sponge_tray` 里
    - 第 2 组：
      - `kitchen_sponge` 在其中任一处上：`kitchen_island/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_stove/top`
- **最不好（0.3）**：

  - `kitchen_island/top` 擦过
  - `kitchen_sponge` 不在地上
  - 手里空着
- **不行（0）**：没找到海绵；没擦或没擦完；海绵还拿着或掉在地上


**参考调用顺序**：

- 摆法 `dining`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=kitchen_sponge, region=dining_room_0_1)` → 4. `navigate(destination=kitchen_sponge)` → 5. `pick(object=kitchen_sponge)` → 6. `navigate(destination=kitchen_island/top)` → 7. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 8. `navigate(destination=kitchen_cabinet_4/top)` → 9. `look(target=kitchen_cabinet_4/top)` → 10. `navigate(destination=sponge_tray)` → 11. `place(object=kitchen_sponge, receptacle=sponge_tray)`
- 摆法 `study`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=kitchen_sponge, region=living_room_0_1)` → 4. `navigate(destination=kitchen_sponge)` → 5. `pick(object=kitchen_sponge)` → 6. `navigate(destination=kitchen_island/top)` → 7. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 8. `navigate(destination=kitchen_cabinet_4/top)` → 9. `look(target=kitchen_cabinet_4/top)` → 10. `navigate(destination=sponge_tray)` → 11. `place(object=kitchen_sponge, receptacle=sponge_tray)`
- 摆法 `far_dining`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=kitchen_sponge, region=dining_room_0_0)` → 4. `navigate(destination=kitchen_sponge)` → 5. `pick(object=kitchen_sponge)` → 6. `navigate(destination=kitchen_island/top)` → 7. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 8. `navigate(destination=kitchen_cabinet_4/top)` → 9. `look(target=kitchen_cabinet_4/top)` → 10. `navigate(destination=sponge_tray)` → 11. `place(object=kitchen_sponge, receptacle=sponge_tray)`

### which_surface（Task）

**情况**：早饭在岛台或餐桌上吃的：吃过的那边留着燕麦碗、勺子和擀面杖，另一边是干净的；指令只擦用过的那个 → 看哪边留着用过的东西，只擦那一个（两个都擦算失败），海绵留在岛台上

**指令**：早饭是在岛台或者餐桌上吃的。用海绵把吃过饭的那个擦一下；另一个是干净的，别擦。擦完把海绵留在岛台上。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **次好（0.6）**：

  - 摆法 `dining`：
    - `dining_table_2/top` 擦过
    - `kitchen_island/top` 没擦过
    - `kitchen_sponge` 不在地上
    - 手里空着
  - 摆法 `island`：
    - `kitchen_island/top` 擦过
    - `dining_table_2/top` 没擦过
    - `kitchen_sponge` 不在地上
    - 手里空着
- **最不好（0.3）**：

  - 摆法 `dining`：
    - `dining_table_2/top` 擦过
    - `kitchen_sponge` 不在地上
    - 手里空着
  - 摆法 `island`：
    - `kitchen_island/top` 擦过
    - `kitchen_sponge` 不在地上
    - 手里空着
- **不行（0）**：只擦了干净的那张；都没擦；海绵还拿着或掉在地上


**参考调用顺序**：

- 摆法 `island`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_sponge)` → 4. `pick(object=kitchen_sponge)` → 5. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 6. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`
- 摆法 `dining`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_sponge)` → 4. `pick(object=kitchen_sponge)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `navigate(destination=dining_table_2/top)` → 8. `wipe(surface=dining_table_2/top, tool=kitchen_sponge)` → 9. `navigate(destination=kitchen_island/top)` → 10. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`

---

## T09_tomato_soup

> 午饭做个番茄汤：把小番茄放进锅里，搅一搅，盖上锅盖，加热到 60 度，然后关火。

### lid_off（对照）

**情况**：锅盖在锅边 → 按步骤做完

**成功条件**（D 按摆法：`lid_off` D = 0、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `cherry_tomato_1` 在 `handled_cooking_pot` 里
  - `cherry_tomato_2` 在 `handled_cooking_pot` 里
  - `cherry_tomato_1` 温度至少 60 °C
  - `cherry_tomato_2` 温度至少 60 °C
  - `handled_cooking_pot` 搅拌过
  - `handled_cooking_pot` 盖着 `pot_lid`
  - `kitchen_stove` 已经停止加热
  - 手里空着
- **次好（0.6）**：

  - `cherry_tomato_1` 在 `handled_cooking_pot` 里
  - `cherry_tomato_2` 在 `handled_cooking_pot` 里
  - `cherry_tomato_1` 温度至少 60 °C
  - `cherry_tomato_2` 温度至少 60 °C
  - `kitchen_stove` 已经停止加热
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `handled_cooking_pot` 盖着 `pot_lid`
    - 第 2 组：
      - `handled_cooking_pot` 搅拌过
- **最不好（0.3）**：

  - `cherry_tomato_1` 在 `handled_cooking_pot` 里
  - `cherry_tomato_2` 在 `handled_cooking_pot` 里
  - `cherry_tomato_1` 温度至少 60 °C
  - `cherry_tomato_2` 温度至少 60 °C
  - `kitchen_stove` 已经停止加热
  - 手里空着
- **不行（0）**：只放了一个番茄；没到 60 度；灶台没关火；番茄掉出锅外；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 6. `navigate(destination=breakfast_spoon)` → 7. `pick(object=breakfast_spoon)` → 8. `navigate(destination=kitchen_stove/top)` → 9. `look(target=kitchen_stove/top)` → 10. `navigate(destination=handled_cooking_pot)` → 11. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 12. `navigate(destination=kitchen_island/top)` → 13. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 14. `navigate(destination=pot_lid)` → 15. `pick(object=pot_lid)` → 16. `navigate(destination=handled_cooking_pot)` → 17. `cover(container=handled_cooking_pot, lid=pot_lid)` → 18. `navigate(destination=kitchen_stove)` → 19. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

### lid_on_spoon_away（Action + Task）

**情况**：锅盖盖着，勺子不在 → 揭盖、找勺子；或家里没有锅盖，岛台上有个同样大的早餐盘 → 用盘子盖锅（最好的替代算好）

**成功条件**（D 按摆法：`lid_on_spoon_away` D = 1、理想物在，`lid_missing` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `lid_missing`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `handled_cooking_pot` 盖着 `lid_plate`
  - 摆法 `lid_on_spoon_away`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `handled_cooking_pot` 盖着 `pot_lid`
- **次好（0.6）**：

  - 摆法 `lid_missing`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 盖着 `lid_plate`
      - 第 2 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
  - 摆法 `lid_on_spoon_away`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 盖着 `pot_lid`
      - 第 2 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
- **最不好（0.3）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `cherry_tomato_1` 在 `handled_cooking_pot` 里
      - `cherry_tomato_2` 在 `handled_cooking_pot` 里
      - `cherry_tomato_1` 温度至少 60 °C
      - `cherry_tomato_2` 温度至少 60 °C
      - `kitchen_stove` 已经停止加热
- **不行（0）**：只放了一个番茄；没到 60 度；灶台没关火；番茄掉出锅外；还拿着或掉了


**参考调用顺序**：

- 摆法 `lid_on_spoon_away`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 6. `navigate(destination=kitchen_stove/top)` → 7. `look(target=kitchen_stove/top)` → 8. `navigate(destination=handled_cooking_pot)` → 9. `uncover(container=handled_cooking_pot)` → 10. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 11. `search(object=breakfast_spoon, region=living_room_0_0)` → 12. `navigate(destination=breakfast_spoon)` → 13. `pick(object=breakfast_spoon)` → 14. `navigate(destination=handled_cooking_pot)` → 15. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 16. `navigate(destination=kitchen_island/top)` → 17. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 18. `navigate(destination=pot_lid)` → 19. `pick(object=pot_lid)` → 20. `navigate(destination=handled_cooking_pot)` → 21. `cover(container=handled_cooking_pot, lid=pot_lid)` → 22. `navigate(destination=kitchen_stove)` → 23. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`
- 摆法 `lid_missing`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 6. `navigate(destination=breakfast_spoon)` → 7. `pick(object=breakfast_spoon)` → 8. `navigate(destination=kitchen_stove/top)` → 9. `look(target=kitchen_stove/top)` → 10. `navigate(destination=handled_cooking_pot)` → 11. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 12. `navigate(destination=kitchen_island/top)` → 13. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 14. `navigate(destination=lid_plate)` → 15. `pick(object=lid_plate)` → 16. `navigate(destination=handled_cooking_pot)` → 17. `cover(container=handled_cooking_pot, lid=lid_plate)` → 18. `navigate(destination=kitchen_stove)` → 19. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

### pot_in_use（Task）

**情况**：灶上左边炉眼可能放着一锅昨天剩的番茄汤（满的），平时用的空锅在隔壁餐厅的餐桌上；指令只说"灶上的锅" → 先看锅里：已经装满别的汤的锅在用，番茄不能倒进去，那锅也别动；去餐厅把空锅拿到右边空炉眼上再做。灶上是空锅时就直接用

**成功条件**（D 按摆法：`in_use` D = 1、理想物不在，`free` D = 1、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **次好（0.6）**：

  - `cherry_tomato_1` 在 `handled_cooking_pot` 里
  - `cherry_tomato_2` 在 `handled_cooking_pot` 里
  - `cherry_tomato_1` 温度至少 60 °C
  - `cherry_tomato_2` 温度至少 60 °C
  - `kitchen_stove` 已经停止加热
  - 手里空着
  - `soup_pot` 立着
  - `cherry_tomato_1` 不在 `soup_pot` 里
  - `cherry_tomato_2` 不在 `soup_pot` 里
  - 满足下面任意一组：
    - 第 1 组：
      - `handled_cooking_pot` 搅拌过
      - `handled_cooking_pot` 盖着 `pot_lid`
    - 第 2 组：
      - `handled_cooking_pot` 搅拌过
      - `soup_pot` 没被挪动（离开局位置不超过 3 cm）
    - 第 3 组：
      - `handled_cooking_pot` 盖着 `pot_lid`
      - `soup_pot` 没被挪动（离开局位置不超过 3 cm）
- **最不好（0.3）**：

  - `kitchen_stove` 已经停止加热
  - 手里空着
  - `soup_pot` 立着
  - 满足下面任意一组：
    - 第 1 组：
      - `cherry_tomato_1` 在 `handled_cooking_pot` 里
      - `cherry_tomato_2` 在 `handled_cooking_pot` 里
      - `cherry_tomato_1` 温度至少 60 °C
      - `cherry_tomato_2` 温度至少 60 °C
      - `kitchen_stove` 已经停止加热
      - 手里空着
      - `soup_pot` 立着
      - `cherry_tomato_1` 不在 `soup_pot` 里
      - `cherry_tomato_2` 不在 `soup_pot` 里
    - 第 2 组：
      - `cherry_tomato_1` 在 `soup_pot` 里
      - `cherry_tomato_2` 在 `soup_pot` 里
      - `cherry_tomato_1` 温度至少 60 °C
      - `cherry_tomato_2` 温度至少 60 °C
      - `kitchen_stove` 已经停止加热
      - `soup_pot` 立着
      - 手里空着
- **不行（0）**：满锅打翻；只放了一个番茄；没到 60 度；灶台没关火；还拿着或掉了


**参考调用顺序**：

- 摆法 `in_use`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=kitchen_stove/top)` → 6. `look(target=kitchen_stove/top)` → 7. `search(object=handled_cooking_pot, region=dining_room_0_1)` → 8. `navigate(destination=handled_cooking_pot)` → 9. `pick(object=handled_cooking_pot)` → 10. `navigate(destination=kitchen_stove/top)` → 11. `place(object=handled_cooking_pot, receptacle=kitchen_stove/top, hint_xy=[8.7, 1.725])` → 12. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 13. `navigate(destination=breakfast_spoon)` → 14. `pick(object=breakfast_spoon)` → 15. `navigate(destination=handled_cooking_pot)` → 16. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 17. `navigate(destination=kitchen_island/top)` → 18. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 19. `navigate(destination=pot_lid)` → 20. `pick(object=pot_lid)` → 21. `navigate(destination=handled_cooking_pot)` → 22. `cover(container=handled_cooking_pot, lid=pot_lid)` → 23. `navigate(destination=kitchen_stove)` → 24. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`
- 摆法 `free`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=kitchen_stove/top)` → 6. `look(target=kitchen_stove/top)` → 7. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=handled_cooking_pot)` → 11. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 12. `navigate(destination=kitchen_island/top)` → 13. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 14. `navigate(destination=pot_lid)` → 15. `pick(object=pot_lid)` → 16. `navigate(destination=handled_cooking_pot)` → 17. `cover(container=handled_cooking_pot, lid=pot_lid)` → 18. `navigate(destination=kitchen_stove)` → 19. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

### tomato_in_fridge（Action + Task）

**情况**：汤要用三颗小番茄；岛台上两颗 → 开冰箱拿第三颗，关好门；冰箱里没有小番茄、只有一个大番茄（和一个苹果）时用大番茄（最好的替代算好；拿苹果凑数不行）

**指令**：午饭用三颗小番茄做番茄汤：放进锅里，搅一搅，盖上锅盖，加热到 60 度，然后关火。

**成功条件**（D 按摆法：`in_fridge` D = 1、理想物在，`big_tomato` D = 0、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `big_tomato`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `big_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `big_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `handled_cooking_pot` 盖着 `pot_lid`
        - `breakfast_fridge` 关着
  - 摆法 `in_fridge`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `handled_cooking_pot` 盖着 `pot_lid`
        - `breakfast_fridge` 关着
- **次好（0.6）**：

  - 摆法 `big_tomato`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `big_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `big_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 盖着 `pot_lid`
        - `breakfast_fridge` 关着
      - 第 2 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `big_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `big_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `breakfast_fridge` 关着
      - 第 3 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `big_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `big_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `handled_cooking_pot` 盖着 `pot_lid`
  - 摆法 `in_fridge`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 盖着 `pot_lid`
        - `breakfast_fridge` 关着
      - 第 2 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `breakfast_fridge` 关着
      - 第 3 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `handled_cooking_pot` 盖着 `pot_lid`
- **最不好（0.3）**：

  - 摆法 `big_tomato`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `big_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `big_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `breakfast_fridge` 关着
      - 第 2 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `big_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `big_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 盖着 `pot_lid`
      - 第 3 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `big_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `big_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
      - 第 4 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `big_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `big_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
  - 摆法 `in_fridge`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `breakfast_fridge` 关着
      - 第 2 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 盖着 `pot_lid`
      - 第 3 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
      - 第 4 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
- **不行（0）**：只放了两颗（没找到冰箱里那颗或大番茄）；拿苹果凑数；没到 60 度；灶台没关火；番茄掉出锅外；还拿着或掉了


**参考调用顺序**：

- 摆法 `in_fridge`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 6. `navigate(destination=breakfast_fridge)` → 7. `open(articulated=breakfast_fridge)` → 8. `bend()` → 9. `explore_furniture(furniture=breakfast_fridge)` → 10. `straighten()` → 11. `navigate(destination=fridge_tomato)` → 12. `pick(object=fridge_tomato)` → 13. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 14. `navigate(destination=kitchen_stove/top)` → 15. `look(target=kitchen_stove/top)` → 16. `navigate(destination=handled_cooking_pot)` → 17. `drop(object=fridge_tomato, container=handled_cooking_pot)` → 18. `navigate(destination=breakfast_fridge)` → 19. `close(articulated=breakfast_fridge)` → 20. `navigate(destination=breakfast_spoon)` → 21. `pick(object=breakfast_spoon)` → 22. `navigate(destination=handled_cooking_pot)` → 23. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 24. `navigate(destination=kitchen_island/top)` → 25. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 26. `navigate(destination=pot_lid)` → 27. `pick(object=pot_lid)` → 28. `navigate(destination=handled_cooking_pot)` → 29. `cover(container=handled_cooking_pot, lid=pot_lid)` → 30. `navigate(destination=kitchen_stove)` → 31. `heat(food=fridge_tomato, appliance=kitchen_stove, temp_c=60)`
- 摆法 `big_tomato`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 6. `navigate(destination=breakfast_fridge)` → 7. `open(articulated=breakfast_fridge)` → 8. `bend()` → 9. `explore_furniture(furniture=breakfast_fridge)` → 10. `straighten()` → 11. `navigate(destination=big_tomato)` → 12. `pick(object=big_tomato)` → 13. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 14. `navigate(destination=kitchen_stove/top)` → 15. `look(target=kitchen_stove/top)` → 16. `navigate(destination=handled_cooking_pot)` → 17. `drop(object=big_tomato, container=handled_cooking_pot)` → 18. `navigate(destination=breakfast_fridge)` → 19. `close(articulated=breakfast_fridge)` → 20. `navigate(destination=breakfast_spoon)` → 21. `pick(object=breakfast_spoon)` → 22. `navigate(destination=handled_cooking_pot)` → 23. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 24. `navigate(destination=kitchen_island/top)` → 25. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 26. `navigate(destination=pot_lid)` → 27. `pick(object=pot_lid)` → 28. `navigate(destination=handled_cooking_pot)` → 29. `cover(container=handled_cooking_pot, lid=pot_lid)` → 30. `navigate(destination=kitchen_stove)` → 31. `heat(food=big_tomato, appliance=kitchen_stove, temp_c=60)`

### x6_gd_tomato_elsewhere（Task）

**情况**：一颗番茄在岛台，另一颗在餐桌：落在桌上就去拿；放在别人午饭的盘子里（旁边有勺子）就别动，用冰箱里那颗（拿盘子里的算差）

**成功条件**（D 按摆法：`dining` D = 1、理想物在，`on_plate` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `dining`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `handled_cooking_pot` 盖着 `pot_lid`
  - 摆法 `on_plate`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `cherry_tomato_2` 没被挪动（离开局位置不超过 3 cm）
        - `lunch_plate` 没被挪动（离开局位置不超过 3 cm）
        - `handled_cooking_pot` 搅拌过
        - `handled_cooking_pot` 盖着 `pot_lid`
        - `breakfast_fridge` 关着
- **次好（0.6）**：

  - 摆法 `dining`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 盖着 `pot_lid`
      - 第 2 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
  - 摆法 `on_plate`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `cherry_tomato_2` 没被挪动（离开局位置不超过 3 cm）
        - `lunch_plate` 没被挪动（离开局位置不超过 3 cm）
        - `handled_cooking_pot` 盖着 `pot_lid`
        - `breakfast_fridge` 关着
      - 第 2 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `cherry_tomato_2` 没被挪动（离开局位置不超过 3 cm）
        - `lunch_plate` 没被挪动（离开局位置不超过 3 cm）
        - `handled_cooking_pot` 搅拌过
        - `breakfast_fridge` 关着
      - 第 3 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `cherry_tomato_2` 没被挪动（离开局位置不超过 3 cm）
        - `lunch_plate` 没被挪动（离开局位置不超过 3 cm）
        - `handled_cooking_pot` 搅拌过
        - `handled_cooking_pot` 盖着 `pot_lid`
- **最不好（0.3）**：

  - 摆法 `dining`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
  - 摆法 `on_plate`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `cherry_tomato_2` 没被挪动（离开局位置不超过 3 cm）
        - `lunch_plate` 没被挪动（离开局位置不超过 3 cm）
        - `breakfast_fridge` 关着
      - 第 2 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `cherry_tomato_2` 没被挪动（离开局位置不超过 3 cm）
        - `lunch_plate` 没被挪动（离开局位置不超过 3 cm）
        - `handled_cooking_pot` 盖着 `pot_lid`
      - 第 3 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `cherry_tomato_2` 没被挪动（离开局位置不超过 3 cm）
        - `lunch_plate` 没被挪动（离开局位置不超过 3 cm）
        - `handled_cooking_pot` 搅拌过
      - 第 4 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `handled_cooking_pot` 盖着 `pot_lid`
        - `breakfast_fridge` 关着
      - 第 5 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `handled_cooking_pot` 盖着 `pot_lid`
        - `breakfast_fridge` 关着
      - 第 6 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `cherry_tomato_2` 没被挪动（离开局位置不超过 3 cm）
        - `lunch_plate` 没被挪动（离开局位置不超过 3 cm）
      - 第 7 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 盖着 `pot_lid`
        - `breakfast_fridge` 关着
      - 第 8 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `breakfast_fridge` 关着
      - 第 9 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `handled_cooking_pot` 盖着 `pot_lid`
      - 第 10 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 盖着 `pot_lid`
        - `breakfast_fridge` 关着
      - 第 11 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `breakfast_fridge` 关着
      - 第 12 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `handled_cooking_pot` 盖着 `pot_lid`
      - 第 13 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `breakfast_fridge` 关着
      - 第 14 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 盖着 `pot_lid`
      - 第 15 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
      - 第 16 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `breakfast_fridge` 关着
      - 第 17 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 盖着 `pot_lid`
      - 第 18 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
      - 第 19 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
      - 第 20 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `fridge_tomato` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `fridge_tomato` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
- **不行（0）**：只放了一颗（没找到另一颗）；没到 60 度；灶台没关火；番茄掉出锅外；还拿着或掉了


**参考调用顺序**：

- 摆法 `dining`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `collect(objects=[cherry_tomato_1], container=handled_cooking_pot)`（补救） → 6. `search(object=cherry_tomato_2, region=dining_room_0_1)`（补救） → 7. `navigate(destination=cherry_tomato_2)`（补救） → 8. `pick(object=cherry_tomato_2)`（补救） → 9. `navigate(destination=kitchen_stove/top)` → 10. `look(target=kitchen_stove/top)` → 11. `navigate(destination=handled_cooking_pot)`（补救） → 12. `drop(object=cherry_tomato_2, container=handled_cooking_pot)`（补救） → 13. `navigate(destination=breakfast_spoon)` → 14. `pick(object=breakfast_spoon)` → 15. `navigate(destination=handled_cooking_pot)` → 16. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 17. `navigate(destination=kitchen_island/top)` → 18. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 19. `navigate(destination=pot_lid)` → 20. `pick(object=pot_lid)` → 21. `navigate(destination=handled_cooking_pot)` → 22. `cover(container=handled_cooking_pot, lid=pot_lid)` → 23. `navigate(destination=kitchen_stove)` → 24. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`
- 摆法 `on_plate`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `collect(objects=[cherry_tomato_1], container=handled_cooking_pot)` → 6. `navigate(destination=breakfast_fridge)` → 7. `open(articulated=breakfast_fridge)` → 8. `bend()` → 9. `explore_furniture(furniture=breakfast_fridge)` → 10. `straighten()` → 11. `navigate(destination=fridge_tomato)` → 12. `pick(object=fridge_tomato)` → 13. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 14. `navigate(destination=kitchen_stove/top)` → 15. `look(target=kitchen_stove/top)` → 16. `navigate(destination=handled_cooking_pot)` → 17. `drop(object=fridge_tomato, container=handled_cooking_pot)` → 18. `navigate(destination=breakfast_fridge)` → 19. `close(articulated=breakfast_fridge)` → 20. `navigate(destination=breakfast_spoon)` → 21. `pick(object=breakfast_spoon)` → 22. `navigate(destination=handled_cooking_pot)` → 23. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 24. `navigate(destination=kitchen_island/top)` → 25. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 26. `navigate(destination=pot_lid)` → 27. `pick(object=pot_lid)` → 28. `navigate(destination=handled_cooking_pot)` → 29. `cover(container=handled_cooking_pot, lid=pot_lid)` → 30. `navigate(destination=kitchen_stove)` → 31. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

### pot_in_dining_room（Task）

**情况**：锅不在灶上（锅盖在灶上），指令只说"锅" → 平时的锅在隔壁餐桌就去拿回来；平时的锅不在了，岛台上有一口同款空锅就用它（最好的替代算好）

**成功条件**（D 按摆法：`pot_away` D = 1、理想物在，`spare_pot` D = 0、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `pot_away`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
        - `handled_cooking_pot` 盖着 `pot_lid`
  - 摆法 `spare_pot`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `spare_pot` 里
        - `cherry_tomato_2` 在 `spare_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `spare_pot` 搅拌过
        - `spare_pot` 盖着 `pot_lid`
- **次好（0.6）**：

  - 摆法 `pot_away`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 盖着 `pot_lid`
      - 第 2 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `handled_cooking_pot` 搅拌过
  - 摆法 `spare_pot`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `spare_pot` 里
        - `cherry_tomato_2` 在 `spare_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `spare_pot` 盖着 `pot_lid`
      - 第 2 组：
        - `cherry_tomato_1` 在 `spare_pot` 里
        - `cherry_tomato_2` 在 `spare_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
        - `spare_pot` 搅拌过
- **最不好（0.3）**：

  - 摆法 `pot_away`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `handled_cooking_pot` 里
        - `cherry_tomato_2` 在 `handled_cooking_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
  - 摆法 `spare_pot`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cherry_tomato_1` 在 `spare_pot` 里
        - `cherry_tomato_2` 在 `spare_pot` 里
        - `cherry_tomato_1` 温度至少 60 °C
        - `cherry_tomato_2` 温度至少 60 °C
        - `kitchen_stove` 已经停止加热
- **不行（0）**：用碗或马克杯代替锅；没找到锅；只放了一颗；没到 60 度；灶台没关火；还拿着或掉了


**参考调用顺序**：

- 摆法 `pot_away`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=kitchen_stove/top)` → 6. `look(target=kitchen_stove/top)` → 7. `search(object=handled_cooking_pot, region=dining_room_0_1)` → 8. `navigate(destination=handled_cooking_pot)` → 9. `pick(object=handled_cooking_pot)` → 10. `navigate(destination=kitchen_stove/top)` → 11. `place(object=handled_cooking_pot, receptacle=kitchen_stove/top, hint_xy=[8.41, 1.725])` → 12. `navigate(destination=cherry_tomato_1)`（补救） → 13. `sweep(objects=[cherry_tomato_1, cherry_tomato_2], radius_m=0.12)`（补救） → 14. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)`（换做法） → 15. `navigate(destination=breakfast_spoon)` → 16. `pick(object=breakfast_spoon)` → 17. `navigate(destination=handled_cooking_pot)` → 18. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 19. `navigate(destination=kitchen_island/top)` → 20. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 21. `navigate(destination=pot_lid)` → 22. `pick(object=pot_lid)` → 23. `navigate(destination=handled_cooking_pot)` → 24. `cover(container=handled_cooking_pot, lid=pot_lid)` → 25. `navigate(destination=kitchen_stove)` → 26. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`
- 摆法 `spare_pot`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=kitchen_stove/top)` → 6. `look(target=kitchen_stove/top)` → 7. `navigate(destination=kitchen_stove/top)` → 8. `look(target=kitchen_stove/top)` → 9. `navigate(destination=spare_pot)` → 10. `pick(object=spare_pot)` → 11. `navigate(destination=kitchen_stove/top)` → 12. `place(object=spare_pot, receptacle=kitchen_stove/top, hint_xy=[8.41, 1.725])` → 13. `navigate(destination=cherry_tomato_1)`（补救） → 14. `sweep(objects=[cherry_tomato_1, cherry_tomato_2], radius_m=0.12)`（补救） → 15. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=spare_pot)`（换做法） → 16. `navigate(destination=breakfast_spoon)` → 17. `pick(object=breakfast_spoon)` → 18. `navigate(destination=spare_pot)` → 19. `stir(container=spare_pot, tool=breakfast_spoon)` → 20. `navigate(destination=kitchen_island/top)` → 21. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 22. `navigate(destination=pot_lid)` → 23. `pick(object=pot_lid)` → 24. `navigate(destination=spare_pot)` → 25. `cover(container=spare_pot, lid=pot_lid)` → 26. `navigate(destination=kitchen_stove)` → 27. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

---

## T10_trash_the_can

> 有人随手放了个空易拉罐，把它扔进垃圾桶。

### can_on_island（对照）

**情况**：罐子在岛台 → 扔掉

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `soda_can` 在 `trash_can` 里
  - 手里空着
- **不行（0）**：易拉罐没进垃圾桶（放别的箱子或没扔）；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=soda_can)` → 7. `pick(object=soda_can)` → 8. `lift(object=soda_can, height_m=0.95)` → 9. `navigate(destination=trash_can)` → 10. `hover(object=soda_can, target=trash_can)` → 11. `drop(object=soda_can, container=trash_can)`

### can_in_dining_room（对照）

**情况**：罐子在隔壁看不到的地方 → 先找

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `soda_can` 在 `trash_can` 里
  - 手里空着
- **不行（0）**：没找到；没进垃圾桶；还拿着或掉了


**参考调用顺序**：

- 摆法 `can_in_dining_room`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `explore_room(room=living_room_0_0)` → 6. `pick(object=soda_can)` → 7. `search(object=soda_can, region=dining_room_0_1)` → 8. `navigate(destination=soda_can)` → 9. `pick(object=soda_can)` → 10. `navigate(destination=trash_can)` → 11. `drop(object=soda_can, container=trash_can)`
- 摆法 `alt_tv_stand_2`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `explore_room(room=living_room_0_0)` → 6. `pick(object=soda_can)` → 7. `search(object=soda_can, region=living_room_0_0)` → 8. `navigate(destination=soda_can)` → 9. `pick(object=soda_can)` → 10. `navigate(destination=trash_can)` → 11. `drop(object=soda_can, container=trash_can)`

### keep_kids_can（Task）

**情况**：两个一样的易拉罐：一个和作业本、铅笔摆在一起（孩子一边写作业一边喝的），另一个单独放着；指令说孩子写作业时喝的那罐别扔 → 从罐子周围的东西认出孩子的，只扔另一个（扔了孩子的算失败）

**指令**：把喝完的易拉罐扔进垃圾桶。孩子一边写作业一边喝的那罐别扔。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `soda_can` 在 `trash_can` 里
  - 手里空着
  - `kids_can`、`craft_notebook`、`craft_pencil` 没被挪动（离开局位置不超过 3 cm）
  - `kids_can` 立着
- **次好（0.6）**：

  - `soda_can` 在 `trash_can` 里
  - 手里空着
  - `kids_can` 立着
  - `kids_can` 不在 `trash_can` 里
- **不行（0）**：把孩子那罐扔了或碰倒；该扔的没扔；还拿着或掉了


**参考调用顺序**：

- 摆法 `kid_desk`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `search(object=kids_can, region=living_room_0_1)` → 6. `navigate(destination=soda_can)` → 7. `pick(object=soda_can)` → 8. `lift(object=soda_can, height_m=0.95)` → 9. `explore_room(room=living_room_0_0)` → 10. `navigate(destination=trash_can)` → 11. `hover(object=soda_can, target=trash_can)` → 12. `drop(object=soda_can, container=trash_can)`
- 摆法 `kid_island`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `search(object=soda_can, region=living_room_0_1)` → 6. `navigate(destination=soda_can)` → 7. `pick(object=soda_can)` → 8. `lift(object=soda_can, height_m=0.95)` → 9. `explore_room(room=living_room_0_0)` → 10. `navigate(destination=trash_can)` → 11. `hover(object=soda_can, target=trash_can)` → 12. `drop(object=soda_can, container=trash_can)`

### trash_moved（Task）

**情况**：罐子在岛台上，垃圾桶不在老地方就去找；岛台旁的垃圾桶塞满了（零食盒冒出桶口）就用卫生间的垃圾桶（最好的替代算好）

**成功条件**（D 按摆法：`dining` D = 1、理想物在，`trash_full` D = 0、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `trash_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `bathroom_trash` 里
        - `trash_fill_1` 没被挪动（离开局位置不超过 5 cm）
        - `trash_fill_2` 没被挪动（离开局位置不超过 5 cm）
        - `trash_fill_3` 没被挪动（离开局位置不超过 5 cm）
        - `trash_fill_4` 没被挪动（离开局位置不超过 5 cm）
  - 摆法 `dining`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `trash_can` 里
- **次好（0.6）**：

  - 摆法 `dining`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `trash_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `bathroom_trash` 里
- **最不好（0.3）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **不行（0）**：罐子没进有空位的垃圾桶（压在满桶上、扔进别的箱子或没扔）；还拿着或掉了


**参考调用顺序**：

- 摆法 `dining`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `lift(object=soda_can, height_m=0.95)` → 8. `explore_room(room=dining_room_0_1)` → 9. `navigate(destination=trash_can)` → 10. `hover(object=soda_can, target=trash_can)` → 11. `drop(object=soda_can, container=trash_can)`
- 摆法 `trash_full`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `lift(object=soda_can, height_m=0.95)` → 8. `explore_room(room=living_room_0_0)` → 9. `navigate(destination=trash_can)` → 10. `look(target=trash_can)` → 11. `explore_room(room=bathroom_0_1)` → 12. `navigate(destination=bathroom_trash)` → 13. `hover(object=soda_can, target=bathroom_trash)` → 14. `drop(object=soda_can, container=bathroom_trash)`

### after_dinner_clear（Task）

**情况**：“晚饭吃完了，把餐桌收拾干净，每样东西拿到它该去的地方。麦片盒留在桌上”：桌上有空易拉罐，以及空铝箔外卖盒、装剩饭的玻璃盒、用过的马克杯中的两样 → 按每样东西是什么、什么状态决定去处：空罐和空外卖盒扔垃圾桶，剩饭进冰箱，杯子回厨房台面或岛台；一只手，先开冰箱门再拿剩饭，放好关门

**指令**：晚饭吃完了，把餐桌收拾干净，每样东西拿到它该去的地方。麦片盒留在桌上。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
    - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_island/top`
    - `used_mug` 立着
    - `clutter_cereal_a`、`clutter_cereal_b` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
  - 摆法 `leftovers_mug`：
    - `soda_can` 在 `trash_can` 里
    - `leftovers` 在 `breakfast_fridge/inside_shelf` 上
    - `breakfast_fridge` 关着
    - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_island/top`
    - `used_mug` 立着
    - `clutter_cereal_a`、`clutter_cereal_b` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
- **次好（0.6）**：

  - 摆法 `rubbish_leftovers`：
    - `soda_can` 在 `trash_can` 里
    - `takeout_tray` 在 `trash_can` 里
    - `leftovers` 在 `breakfast_fridge/inside_shelf` 上
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 3 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `breakfast_fridge` 关着
  - 摆法 `rubbish_mug`：
    - `soda_can` 在 `trash_can` 里
    - `takeout_tray` 在 `trash_can` 里
    - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_island/top`
    - `used_mug` 立着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 3 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
  - 摆法 `leftovers_mug`：
    - `soda_can` 在 `trash_can` 里
    - `leftovers` 在 `breakfast_fridge/inside_shelf` 上
    - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_island/top`
    - `used_mug` 立着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `clutter_cereal_a` 没被挪动（离开局位置不超过 3 cm）
        - `clutter_cereal_b` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `breakfast_fridge` 关着
- **最不好（0.3）**：

  - 摆法 `rubbish_leftovers`：
    - `soda_can` 在 `trash_can` 里
    - `takeout_tray` 在 `trash_can` 里
    - 手里空着
    - `leftovers` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_island/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_stove/top`
  - 摆法 `rubbish_mug`：
    - `soda_can` 在 `trash_can` 里
    - `takeout_tray` 在 `trash_can` 里
    - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_island/top`
    - `used_mug` 立着
    - 手里空着
  - 摆法 `leftovers_mug`：
    - `soda_can` 在 `trash_can` 里
    - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_island/top`
    - `used_mug` 立着
    - 手里空着
    - `leftovers` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_island/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_stove/top`
- **不行（0）**：有东西留在桌上或放错类（剩饭、杯子扔进垃圾桶）；杯子倒了；还拿着或掉了


**参考调用顺序**：

- 摆法 `rubbish_leftovers`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `lift(object=soda_can, height_m=0.95)` → 8. `explore_room(room=living_room_0_0)` → 9. `navigate(destination=trash_can)` → 10. `hover(object=soda_can, target=trash_can)` → 11. `drop(object=soda_can, container=trash_can)` → 12. `navigate(destination=takeout_tray)` → 13. `pick(object=takeout_tray)` → 14. `lift(object=takeout_tray, height_m=0.95)` → 15. `navigate(destination=trash_can)` → 16. `drop(object=takeout_tray, container=trash_can)` → 17. `navigate(destination=breakfast_fridge)` → 18. `open(articulated=breakfast_fridge)` → 19. `navigate(destination=leftovers)` → 20. `pick(object=leftovers)` → 21. `navigate(destination=breakfast_fridge)` → 22. `place(object=leftovers, receptacle=breakfast_fridge/inside_shelf)` → 23. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 24. `close(articulated=breakfast_fridge)`
- 摆法 `leftovers_mug`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `lift(object=soda_can, height_m=0.95)` → 8. `explore_room(room=living_room_0_0)` → 9. `navigate(destination=trash_can)` → 10. `hover(object=soda_can, target=trash_can)` → 11. `drop(object=soda_can, container=trash_can)` → 12. `navigate(destination=breakfast_fridge)` → 13. `open(articulated=breakfast_fridge)` → 14. `navigate(destination=leftovers)` → 15. `pick(object=leftovers)` → 16. `navigate(destination=breakfast_fridge)` → 17. `place(object=leftovers, receptacle=breakfast_fridge/inside_shelf)` → 18. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 19. `close(articulated=breakfast_fridge)` → 20. `navigate(destination=used_mug)` → 21. `pick(object=used_mug)` → 22. `navigate(destination=kitchen_counter_2/top)` → 23. `place(object=used_mug, receptacle=kitchen_counter_2/top)`
- 摆法 `rubbish_mug`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `lift(object=soda_can, height_m=0.95)` → 8. `explore_room(room=living_room_0_0)` → 9. `navigate(destination=trash_can)` → 10. `hover(object=soda_can, target=trash_can)` → 11. `drop(object=soda_can, container=trash_can)` → 12. `navigate(destination=takeout_tray)` → 13. `pick(object=takeout_tray)` → 14. `lift(object=takeout_tray, height_m=0.95)` → 15. `navigate(destination=trash_can)` → 16. `drop(object=takeout_tray, container=trash_can)` → 17. `navigate(destination=used_mug)` → 18. `pick(object=used_mug)` → 19. `navigate(destination=kitchen_counter_2/top)` → 20. `place(object=used_mug, receptacle=kitchen_counter_2/top)`

### guests_coming（Task）

**情况**：“客人十分钟后到，把客厅收拾得能见人：乱放的东西各回各处，本来就该在那儿的东西别动”：客厅里散着空罐、用过的马克杯（电视柜上）、孩子的积木（地上）中的两三样；岛台上的擀面杖和海绵本来就该在那 → 找出乱放的，各送回该去的地方（垃圾桶、厨房台面或岛台、玩具箱）

**指令**：客人十分钟后到，把客厅收拾得能见人：乱放的东西各回各处，本来就该在那儿的东西别动。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `can_block`：
    - `soda_can` 在 `trash_can` 里
    - `wooden_block_a` 在 `toy_box` 里
    - `rolling_pin`、`kitchen_sponge` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
  - 摆法 `can_mug_block`：
    - `soda_can` 在 `trash_can` 里
    - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_island/top`
    - `used_mug` 立着
    - `wooden_block_a` 在 `toy_box` 里
    - `rolling_pin`、`kitchen_sponge` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
  - 摆法 `can_mug`：
    - `soda_can` 在 `trash_can` 里
    - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_island/top`
    - `used_mug` 立着
    - `rolling_pin`、`kitchen_sponge` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
- **次好（0.6）**：

  - 摆法 `can_block`：
    - `soda_can` 在 `trash_can` 里
    - `wooden_block_a` 在 `toy_box` 里
    - 手里空着
  - 摆法 `can_mug`：
    - `soda_can` 在 `trash_can` 里
    - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_island/top`
    - `used_mug` 立着
    - 手里空着
  - 摆法 `can_mug_block`：
    - `soda_can` 在 `trash_can` 里
    - `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_island/top`
    - `used_mug` 立着
    - `wooden_block_a` 在 `toy_box` 里
    - 手里空着
- **最不好（0.3）**：

  - 摆法 `can_block`：
    - `soda_can` 在 `trash_can` 里
    - 手里空着
    - `wooden_block_a` 不在地上
  - 摆法 `can_mug`：
    - `soda_can` 在 `trash_can` 里
    - `used_mug` 立着
    - 手里空着
    - `["not on", "used_mug", "tv_stand_2/top"]`
    - `used_mug` 不在地上
  - 摆法 `can_mug_block`：
    - `soda_can` 在 `trash_can` 里
    - `used_mug` 立着
    - 手里空着
    - `wooden_block_a` 不在地上
    - `["not on", "used_mug", "tv_stand_2/top"]`
    - `used_mug` 不在地上
- **不行（0）**：罐子没扔；有东西还乱放；杯子倒了；还拿着或掉了


**参考调用顺序**：

- 摆法 `can_mug_block`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `look(target=tv_stand_2/top)` → 7. `navigate(destination=soda_can)` → 8. `pick(object=soda_can)` → 9. `lift(object=soda_can, height_m=0.95)` → 10. `explore_room(room=living_room_0_0)` → 11. `navigate(destination=trash_can)` → 12. `hover(object=soda_can, target=trash_can)` → 13. `drop(object=soda_can, container=trash_can)` → 14. `navigate(destination=used_mug)` → 15. `pick(object=used_mug)` → 16. `navigate(destination=kitchen_counter_2/top)` → 17. `place(object=used_mug, receptacle=kitchen_counter_2/top)` → 18. `navigate(destination=wooden_block_a)` → 19. `look(target=wooden_block_a)` → 20. `pick(object=wooden_block_a)` → 21. `navigate(destination=toy_box)` → 22. `place(object=wooden_block_a, receptacle=toy_box)`
- 摆法 `can_block`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `look(target=tv_stand_2/top)` → 7. `navigate(destination=soda_can)` → 8. `pick(object=soda_can)` → 9. `lift(object=soda_can, height_m=0.95)` → 10. `explore_room(room=living_room_0_0)` → 11. `navigate(destination=trash_can)` → 12. `hover(object=soda_can, target=trash_can)` → 13. `drop(object=soda_can, container=trash_can)` → 14. `navigate(destination=wooden_block_a)` → 15. `look(target=wooden_block_a)` → 16. `pick(object=wooden_block_a)` → 17. `navigate(destination=toy_box)` → 18. `place(object=wooden_block_a, receptacle=toy_box)`
- 摆法 `can_mug`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `look(target=tv_stand_2/top)` → 7. `navigate(destination=soda_can)` → 8. `pick(object=soda_can)` → 9. `lift(object=soda_can, height_m=0.95)` → 10. `explore_room(room=living_room_0_0)` → 11. `navigate(destination=trash_can)` → 12. `hover(object=soda_can, target=trash_can)` → 13. `drop(object=soda_can, container=trash_can)` → 14. `navigate(destination=used_mug)` → 15. `pick(object=used_mug)` → 16. `navigate(destination=kitchen_counter_2/top)` → 17. `place(object=used_mug, receptacle=kitchen_counter_2/top)`

### x6_gd_can_put_away（Task）

**情况**：指令只说空易拉罐在厨房里被误收起来了 → 打开带门的地方找，扔掉，门都关好（门没关降一档）；冰箱里饮料旁边那罐是没喝的，别扔（两罐都扔算差）

**指令**：厨房里有个空易拉罐被人误收起来了，找出来扔进垃圾桶。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `in_cabinet`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `trash_can` 里
        - `kitchen_microwave` 关着
        - `kitchen_cabinet_6` 关着
        - `breakfast_fridge` 关着
        - `kitchen_cabinet_4` 关着
  - 摆法 `fridge_drink`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `trash_can` 里
        - `fridge_soda` 没被挪动（离开局位置不超过 3 cm）
        - `kitchen_microwave` 关着
        - `kitchen_cabinet_6` 关着
        - `breakfast_fridge` 关着
        - `kitchen_cabinet_4` 关着
- **次好（0.6）**：

  - 摆法 `fridge_drink`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `trash_can` 里
        - `fridge_soda` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `soda_can` 在 `trash_can` 里
        - `fridge_soda` 不在 `trash_can` 里
        - `kitchen_microwave` 关着
        - `kitchen_cabinet_6` 关着
        - `breakfast_fridge` 关着
        - `kitchen_cabinet_4` 关着
  - 摆法 `in_cabinet`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `trash_can` 里
- **最不好（0.3）**：

  - 摆法 `in_cabinet`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `fridge_drink`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `trash_can` 里
        - `fridge_soda` 不在 `trash_can` 里
      - 第 2 组：
        - `soda_can` 在 `trash_can` 里
        - `kitchen_microwave` 关着
        - `kitchen_cabinet_6` 关着
        - `breakfast_fridge` 关着
        - `kitchen_cabinet_4` 关着
      - 第 3 组：
        - `soda_can` 在 `trash_can` 里
- **不行（0）**：空罐没找到或没扔（只扔了冰箱那罐）；还拿着或掉了


**参考调用顺序**：

- 摆法 `in_cabinet`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_microwave)` → 4. `open(articulated=kitchen_microwave)` → 5. `look(target=kitchen_microwave/inside_floor)` → 6. `close(articulated=kitchen_microwave)` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=soda_can)` → 13. `pick(object=soda_can)` → 14. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 15. `explore_room(room=living_room_0_0)` → 16. `navigate(destination=trash_can)` → 17. `drop(object=soda_can, container=trash_can)` → 18. `navigate(destination=kitchen_cabinet_6)` → 19. `close(articulated=kitchen_cabinet_6)`
- 摆法 `fridge_drink`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `bend()` → 6. `explore_furniture(furniture=breakfast_fridge)` → 7. `straighten()` → 8. `close(articulated=breakfast_fridge)` → 9. `navigate(destination=kitchen_cabinet_4)` → 10. `open(articulated=kitchen_cabinet_4)` → 11. `bend()` → 12. `explore_furniture(furniture=kitchen_cabinet_4)` → 13. `straighten()` → 14. `navigate(destination=soda_can)` → 15. `pick(object=soda_can)` → 16. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 17. `explore_room(room=living_room_0_0)` → 18. `navigate(destination=trash_can)` → 19. `drop(object=soda_can, container=trash_can)` → 20. `navigate(destination=kitchen_cabinet_4)` → 21. `close(articulated=kitchen_cabinet_4)`

---

## T11_collect_fruits

> 午饭吃完了，苹果还在餐桌上，把它收起来。

### fruits_on_table（对照）

**情况**：苹果在餐桌，果篮在卧室书架 → 想到水果收在果篮里，放进去

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `apple` 在 `fruit_basket` 里
  - 手里空着
- **次好（0.6）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `apple` 在 `fruit_basket` 里
    - 第 2 组：
      - `apple` 在 `serving_tray` 里
- **不行（0）**：苹果留在桌上或放别处；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=apple)` → 4. `pick(object=apple)` → 5. `navigate(destination=bookcase_2/top)` → 6. `look(target=bookcase_2/top)` → 7. `place(object=apple, receptacle=fruit_basket)`

### basket_missing（Task）

**情况**：书架上没有果篮 → 自己找另一个能装水果的东西：书房书桌上的托盘；有的摆法果篮原位置放着一个用过的早餐碗，那不是放水果的

**成功条件**（D 按摆法：`basket_missing` D = 1、理想物不在，`basket_gone_bowl_there` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `apple` 在 `fruit_basket` 里
    - 第 2 组：
      - `apple` 在 `serving_tray` 里
- **最不好（0.3）**：

  - 摆法 `basket_gone_bowl_there`：
    - `apple` 在 `bowl_kitchen_cabinet` 里
    - 手里空着
  - 摆法 `basket_missing`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `apple` 在 `fruit_basket` 里
      - 第 2 组：
        - `apple` 在 `serving_tray` 里
- **不行（0）**：苹果留在桌上或放别处；还拿着或掉了


**参考调用顺序**：

- 摆法 `basket_missing`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=apple)` → 4. `pick(object=apple)` → 5. `navigate(destination=bookcase_2/top)` → 6. `look(target=bookcase_2/top)` → 7. `place(object=apple, receptacle=fruit_basket)` → 8. `navigate(destination=desk_1/top)`（换做法） → 9. `look(target=desk_1/top)`（换做法） → 10. `navigate(destination=serving_tray)`（换做法） → 11. `place(object=apple, receptacle=serving_tray)`（换做法）
- 摆法 `basket_gone_bowl_there`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=apple)` → 4. `pick(object=apple)` → 5. `navigate(destination=bookcase_2/top)` → 6. `look(target=bookcase_2/top)` → 7. `identify(object=bowl_kitchen_cabinet)`（补救） → 8. `navigate(destination=desk_1/top)`（换做法） → 9. `look(target=desk_1/top)`（换做法） → 10. `navigate(destination=serving_tray)`（换做法） → 11. `place(object=apple, receptacle=serving_tray)`（换做法）

### leave_one_for_kid（Task）

**情况**：指令只说“桌上的水果收起来，给书房写作业的孩子留一个当点心，孩子不爱吃橙子” → 拆成两个子目标：一个不是橙子的水果放到书房书桌，其余放进卧室书架上的果篮（指令没说果篮在哪）

**指令**：午饭吃完了，把桌上的水果收起来，给在书房写作业的孩子留一个当点心。孩子不爱吃橙子。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **次好（0.6）**：

  - 摆法 `all_three`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `apple` 在 `desk_1/top` 上
        - `["not on", "lunch_orange", "dining_table_2/top"]`
        - `["not on", "lunch_banana", "dining_table_2/top"]`
        - `lunch_orange` 不在地上
        - `lunch_banana` 不在地上
      - 第 2 组：
        - `lunch_banana` 在 `desk_1/top` 上
        - `["not on", "apple", "dining_table_2/top"]`
        - `["not on", "lunch_orange", "dining_table_2/top"]`
        - `apple` 不在地上
        - `lunch_orange` 不在地上
  - 摆法 `apple_orange`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `apple` 在 `desk_1/top` 上
        - `["not on", "lunch_orange", "dining_table_2/top"]`
        - `lunch_orange` 不在地上
  - 摆法 `orange_banana`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `lunch_banana` 在 `desk_1/top` 上
        - `["not on", "lunch_orange", "dining_table_2/top"]`
        - `lunch_orange` 不在地上
- **最不好（0.3）**：

  - 摆法 `all_three`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `lunch_orange` 在 `desk_1/top` 上
        - `apple` 在 `fruit_basket` 里
        - `lunch_banana` 在 `fruit_basket` 里
  - 摆法 `apple_orange`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `lunch_orange` 在 `desk_1/top` 上
        - `apple` 在 `fruit_basket` 里
  - 摆法 `orange_banana`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `lunch_orange` 在 `desk_1/top` 上
        - `lunch_banana` 在 `fruit_basket` 里
- **不行（0）**：没给孩子；水果留在桌上；还拿着或掉了


**参考调用顺序**：

- 摆法 `apple_orange`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `search(object=fruit_basket, region=bedroom_0_1)` → 4. `navigate(destination=apple)` → 5. `pick(object=apple)` → 6. `navigate(destination=desk_1/top)` → 7. `place(object=apple, receptacle=desk_1/top, hint_xy=[-0.908, -6.166])` → 8. `navigate(destination=lunch_orange)` → 9. `pick(object=lunch_orange)` → 10. `navigate(destination=bookcase_2/top)` → 11. `place(object=lunch_orange, receptacle=fruit_basket)`
- 摆法 `orange_banana`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `search(object=fruit_basket, region=bedroom_0_1)` → 4. `navigate(destination=lunch_banana)` → 5. `pick(object=lunch_banana)` → 6. `navigate(destination=desk_1/top)` → 7. `place(object=lunch_banana, receptacle=desk_1/top, hint_xy=[-0.908, -6.186])` → 8. `navigate(destination=lunch_orange)` → 9. `pick(object=lunch_orange)` → 10. `navigate(destination=bookcase_2/top)` → 11. `place(object=lunch_orange, receptacle=fruit_basket)`
- 摆法 `all_three`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `search(object=fruit_basket, region=bedroom_0_1)` → 4. `navigate(destination=apple)` → 5. `pick(object=apple)` → 6. `navigate(destination=desk_1/top)` → 7. `place(object=apple, receptacle=desk_1/top, hint_xy=[-0.908, -6.166])` → 8. `navigate(destination=lunch_orange)` → 9. `pick(object=lunch_orange)` → 10. `navigate(destination=bookcase_2/top)` → 11. `place(object=lunch_orange, receptacle=fruit_basket)` → 12. `navigate(destination=lunch_banana)` → 13. `pick(object=lunch_banana)` → 14. `navigate(destination=bookcase_2/top)` → 15. `place(object=lunch_banana, receptacle=fruit_basket)`

### fruit_plate_for_guests（Task）

**情况**：指令只说“客人在客厅看电视，用托盘端点水果过去”，没说托盘在哪 → 找到托盘，先把空托盘放到电视柜，再把苹果和橙子一个个放上去；书桌上的小托盘装着孩子的作业时别动，用餐桌上的大托盘（最好的替代算好；把孩子的东西拿下来用小托盘降一档）

**指令**：客人在客厅看电视，用托盘给他们端点水果过去。

**成功条件**（D 按摆法：`tray_in_study` D = 1、理想物在，`tray_in_use` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `tray_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `apple` 在 `big_tray` 里
        - `lunch_orange` 在 `big_tray` 里
        - `big_tray` 在其中任一处上：`tv_stand_2/top`、`tv_stand_1/top`
        - `kid_notebook` 没被挪动（离开局位置不超过 3 cm）
        - `kid_pencil` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `tray_in_study`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `apple` 在 `fruit_tray` 里
        - `lunch_orange` 在 `fruit_tray` 里
        - `fruit_tray` 在其中任一处上：`tv_stand_2/top`、`tv_stand_1/top`
- **次好（0.6）**：

  - 摆法 `tray_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `apple` 在 `fruit_tray` 里
        - `lunch_orange` 在 `fruit_tray` 里
        - `fruit_tray` 在其中任一处上：`tv_stand_2/top`、`tv_stand_1/top`
      - 第 2 组：
        - `apple` 在 `big_tray` 里
        - `big_tray` 在其中任一处上：`tv_stand_2/top`、`tv_stand_1/top`
      - 第 3 组：
        - `lunch_orange` 在 `big_tray` 里
        - `big_tray` 在其中任一处上：`tv_stand_2/top`、`tv_stand_1/top`
  - 摆法 `tray_in_study`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `apple` 在 `fruit_tray` 里
        - `fruit_tray` 在其中任一处上：`tv_stand_2/top`、`tv_stand_1/top`
      - 第 2 组：
        - `lunch_orange` 在 `fruit_tray` 里
        - `fruit_tray` 在其中任一处上：`tv_stand_2/top`、`tv_stand_1/top`
- **最不好（0.3）**：

  - 摆法 `tray_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `apple` 在 `fruit_tray` 里
        - `fruit_tray` 在其中任一处上：`tv_stand_2/top`、`tv_stand_1/top`
      - 第 2 组：
        - `lunch_orange` 在 `fruit_tray` 里
        - `fruit_tray` 在其中任一处上：`tv_stand_2/top`、`tv_stand_1/top`
      - 第 3 组：
        - `apple` 在其中任一处上：`tv_stand_2/top`、`tv_stand_1/top`
        - `lunch_orange` 在其中任一处上：`tv_stand_2/top`、`tv_stand_1/top`
  - 摆法 `tray_in_study`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `apple` 在其中任一处上：`tv_stand_2/top`、`tv_stand_1/top`
        - `lunch_orange` 在其中任一处上：`tv_stand_2/top`、`tv_stand_1/top`
- **不行（0）**：什么都没端过去；水果掉了；还拿着


**参考调用顺序**：

- 摆法 `tray_in_study`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `search(object=fruit_tray, region=living_room_0_1)` → 4. `navigate(destination=fruit_tray)` → 5. `pick(object=fruit_tray)` → 6. `navigate(destination=tv_stand_2/top)` → 7. `place(object=fruit_tray, receptacle=tv_stand_2/top, hint_xy=[7.5, 0.36])` → 8. `navigate(destination=apple)` → 9. `pick(object=apple)` → 10. `navigate(destination=fruit_tray)` → 11. `place(object=apple, receptacle=fruit_tray)` → 12. `navigate(destination=lunch_orange)` → 13. `pick(object=lunch_orange)` → 14. `navigate(destination=fruit_tray)` → 15. `place(object=lunch_orange, receptacle=fruit_tray)`
- 摆法 `tray_in_use`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=big_tray)` → 4. `pick(object=big_tray)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=big_tray, receptacle=tv_stand_2/top, hint_xy=[7.5, 0.36])` → 7. `navigate(destination=apple)` → 8. `pick(object=apple)` → 9. `navigate(destination=big_tray)` → 10. `place(object=apple, receptacle=big_tray)` → 11. `navigate(destination=lunch_orange)` → 12. `pick(object=lunch_orange)` → 13. `navigate(destination=big_tray)` → 14. `place(object=lunch_orange, receptacle=big_tray)`

---

## T12_tidy_toys

> 快到睡觉时间了，把孩子的玩具收起来。

### toys_out（对照）

**情况**：小车在客厅地上，鸭子在电视柜 → 都放进卧室的储物筐

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `toy_car` 在 `storage_basket` 里
  - `rubber_duck` 在 `storage_basket` 里
  - `storage_basket` 立着
  - 手里空着
- **不行（0）**：有玩具没收；篮子倒了；还拿着或掉了


**参考调用顺序**：

1. `explore_room(room=bedroom_0_1)` → 2. `explore_room(room=living_room_0_0)` → 3. `navigate(destination=toy_car)` → 4. `look(target=toy_car)` → 5. `pick(object=toy_car)` → 6. `navigate(destination=storage_basket)` → 7. `place(object=toy_car, receptacle=storage_basket)` → 8. `navigate(destination=rubber_duck)` → 9. `pick(object=rubber_duck)` → 10. `navigate(destination=storage_basket)` → 11. `place(object=rubber_duck, receptacle=storage_basket)` → 12. `nod()`（补救）

### duck_in_study（对照）

**情况**：鸭子落在别处，开局看不到 → 找鸭子

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `toy_car` 在 `storage_basket` 里
  - `rubber_duck` 在 `storage_basket` 里
  - `storage_basket` 立着
  - 手里空着
- **不行（0）**：没找到鸭子；有玩具没收；还拿着或掉了


**参考调用顺序**：

- 摆法 `duck_in_study`：1. `explore_room(room=bedroom_0_1)` → 2. `explore_room(room=living_room_0_0)` → 3. `navigate(destination=toy_car)` → 4. `look(target=toy_car)` → 5. `pick(object=toy_car)` → 6. `navigate(destination=storage_basket)` → 7. `place(object=toy_car, receptacle=storage_basket)` → 8. `navigate(destination=rubber_duck)` → 9. `search(object=rubber_duck, region=living_room_0_1)` → 10. `navigate(destination=rubber_duck)` → 11. `pick(object=rubber_duck)` → 12. `navigate(destination=storage_basket)` → 13. `place(object=rubber_duck, receptacle=storage_basket)`
- 摆法 `alt_dining_table_2`：1. `explore_room(room=bedroom_0_1)` → 2. `explore_room(room=living_room_0_0)` → 3. `navigate(destination=toy_car)` → 4. `look(target=toy_car)` → 5. `pick(object=toy_car)` → 6. `navigate(destination=storage_basket)` → 7. `place(object=toy_car, receptacle=storage_basket)` → 8. `navigate(destination=rubber_duck)` → 9. `search(object=rubber_duck, region=dining_room_0_1)` → 10. `navigate(destination=rubber_duck)` → 11. `pick(object=rubber_duck)` → 12. `navigate(destination=storage_basket)` → 13. `place(object=rubber_duck, receptacle=storage_basket)`

### bins_capacity（Task）

**情况**：没有储物筐，只有放不下所有玩具的容器：要么两个小箱（一个已经装满积木，一个空着，有时并排放在卧室书架上，有时分在不同房间），要么一个装了半箱积木的小箱和一个浅托盘（鸭子还不在原处） → 看每个容器还剩多少地方，把小车和鸭子分到放得下的地方，空箱或鸭子不在眼前就去找；箱子里原有的积木不动

**成功条件**（D 按摆法：`side_left_full` D = 1、理想物不在，`side_right_full` D = 1、理想物不在，`apart_full_on_tv` D = 1、理想物不在，`apart_empty_on_desk` D = 1、理想物不在，`half_bin_and_tray` D = 1、理想物不在，`half_bin_and_tray_duck_dining` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `side_left_full`、`apart_full_on_tv`、`apart_empty_on_desk`：
    - `stored_block_1` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_2` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_3` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_4` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_5` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_6` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_7` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_8` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_9` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_10` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_11` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_12` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_13` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_14` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_15` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_16` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_17` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_18` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_19` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_20` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_21` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_22` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_23` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_24` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `toy_car` 在 `toy_bin_small_2` 里
    - `rubber_duck` 在 `toy_bin_small_2` 里
    - `toy_bin_small`、`toy_bin_small_2` 立着
    - 手里空着
  - 摆法 `side_right_full`：
    - `stored_block_1` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_2` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_3` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_4` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_5` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_6` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_7` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_8` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_9` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_10` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_11` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_12` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_13` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_14` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_15` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_16` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_17` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_18` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_19` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_20` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_21` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_22` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_23` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_24` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `toy_car` 在 `toy_bin_small` 里
    - `rubber_duck` 在 `toy_bin_small` 里
    - `toy_bin_small_2`、`toy_bin_small` 立着
    - 手里空着
  - 摆法 `half_bin_and_tray`、`half_bin_and_tray_duck_dining`：
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
        - `toy_car` 在 `toy_bin_small` 里
        - `rubber_duck` 在 `toy_bin_small` 里
      - 第 2 组：
        - `toy_car` 在 `toy_bin_small` 里
        - `rubber_duck` 在 `toy_tray` 里
      - 第 3 组：
        - `toy_car` 在 `toy_tray` 里
        - `rubber_duck` 在 `toy_bin_small` 里
      - 第 4 组：
        - `toy_car` 在 `toy_tray` 里
        - `rubber_duck` 在 `toy_tray` 里
- **次好（0.6）**：

  - 摆法 `side_left_full`、`apart_full_on_tv`、`apart_empty_on_desk`：
    - `stored_block_1` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_2` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_3` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_4` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_5` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_6` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_7` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_8` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_9` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_10` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_11` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_12` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_13` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_14` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_15` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_16` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_17` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_18` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_19` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_20` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_21` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_22` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_23` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `stored_block_24` 完全在 `toy_bin_small` 里（没有露出边沿）
    - `toy_bin_small`、`toy_bin_small_2` 立着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `toy_car` 在 `toy_bin_small` 里
        - `rubber_duck` 在 `toy_bin_small` 里
      - 第 2 组：
        - `toy_car` 在 `toy_bin_small` 里
        - `rubber_duck` 在 `toy_bin_small_2` 里
      - 第 3 组：
        - `toy_car` 在 `toy_bin_small_2` 里
        - `rubber_duck` 在 `toy_bin_small` 里
      - 第 4 组：
        - `toy_car` 在 `toy_bin_small_2` 里
        - `rubber_duck` 在 `toy_bin_small_2` 里
  - 摆法 `half_bin_and_tray`、`half_bin_and_tray_duck_dining`：
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
        - `toy_car` 在 `toy_bin_small` 里
        - `rubber_duck` 在 `toy_bin_small` 里
      - 第 2 组：
        - `toy_car` 在 `toy_bin_small` 里
        - `rubber_duck` 在 `toy_tray` 里
      - 第 3 组：
        - `toy_car` 在 `toy_tray` 里
        - `rubber_duck` 在 `toy_bin_small` 里
      - 第 4 组：
        - `toy_car` 在 `toy_tray` 里
        - `rubber_duck` 在 `toy_tray` 里
  - 摆法 `side_right_full`：
    - `stored_block_1` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_2` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_3` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_4` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_5` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_6` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_7` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_8` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_9` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_10` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_11` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_12` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_13` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_14` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_15` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_16` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_17` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_18` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_19` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_20` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_21` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_22` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_23` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `stored_block_24` 完全在 `toy_bin_small_2` 里（没有露出边沿）
    - `toy_bin_small_2`、`toy_bin_small` 立着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `toy_car` 在 `toy_bin_small` 里
        - `rubber_duck` 在 `toy_bin_small` 里
      - 第 2 组：
        - `toy_car` 在 `toy_bin_small` 里
        - `rubber_duck` 在 `toy_bin_small_2` 里
      - 第 3 组：
        - `toy_car` 在 `toy_bin_small_2` 里
        - `rubber_duck` 在 `toy_bin_small` 里
      - 第 4 组：
        - `toy_car` 在 `toy_bin_small_2` 里
        - `rubber_duck` 在 `toy_bin_small_2` 里
- **最不好（0.3）**：

  - 摆法 `half_bin_and_tray`、`half_bin_and_tray_duck_dining`：
    - `toy_bin_small` 立着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `toy_car` 在 `toy_bin_small` 里
        - `rubber_duck` 在 `toy_bin_small` 里
      - 第 2 组：
        - `toy_car` 在 `toy_bin_small` 里
        - `rubber_duck` 在 `toy_tray` 里
      - 第 3 组：
        - `toy_car` 在 `toy_tray` 里
        - `rubber_duck` 在 `toy_bin_small` 里
      - 第 4 组：
        - `toy_car` 在 `toy_tray` 里
        - `rubber_duck` 在 `toy_tray` 里
  - 摆法 `side_left_full`、`apart_full_on_tv`、`apart_empty_on_desk`：
    - `toy_bin_small`、`toy_bin_small_2` 立着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `toy_car` 在 `toy_bin_small` 里
        - `rubber_duck` 在 `toy_bin_small` 里
      - 第 2 组：
        - `toy_car` 在 `toy_bin_small` 里
        - `rubber_duck` 在 `toy_bin_small_2` 里
      - 第 3 组：
        - `toy_car` 在 `toy_bin_small_2` 里
        - `rubber_duck` 在 `toy_bin_small` 里
      - 第 4 组：
        - `toy_car` 在 `toy_bin_small_2` 里
        - `rubber_duck` 在 `toy_bin_small_2` 里
  - 摆法 `side_right_full`：
    - `toy_bin_small_2`、`toy_bin_small` 立着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `toy_car` 在 `toy_bin_small` 里
        - `rubber_duck` 在 `toy_bin_small` 里
      - 第 2 组：
        - `toy_car` 在 `toy_bin_small` 里
        - `rubber_duck` 在 `toy_bin_small_2` 里
      - 第 3 组：
        - `toy_car` 在 `toy_bin_small_2` 里
        - `rubber_duck` 在 `toy_bin_small` 里
      - 第 4 组：
        - `toy_car` 在 `toy_bin_small_2` 里
        - `rubber_duck` 在 `toy_bin_small_2` 里
- **不行（0）**：有玩具没收；箱子倒了；还拿着或掉了


**参考调用顺序**：

- 摆法 `side_left_full`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `measure(object=toy_bin_small_2)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_car)` → 7. `look(target=toy_car)` → 8. `pick(object=toy_car)` → 9. `navigate(destination=toy_bin_small_2)` → 10. `place(object=toy_car, receptacle=toy_bin_small_2)` → 11. `search(object=rubber_duck, region=living_room_0_1)` → 12. `navigate(destination=rubber_duck)` → 13. `pick(object=rubber_duck)` → 14. `navigate(destination=toy_bin_small_2)` → 15. `drop(object=rubber_duck, container=toy_bin_small_2)`
- 摆法 `side_right_full`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small_2)` → 4. `measure(object=toy_bin_small)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_car)` → 7. `look(target=toy_car)` → 8. `pick(object=toy_car)` → 9. `navigate(destination=toy_bin_small)` → 10. `place(object=toy_car, receptacle=toy_bin_small)` → 11. `search(object=rubber_duck, region=living_room_0_1)` → 12. `navigate(destination=rubber_duck)` → 13. `pick(object=rubber_duck)` → 14. `navigate(destination=toy_bin_small)` → 15. `drop(object=rubber_duck, container=toy_bin_small)`
- 摆法 `apart_full_on_tv`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `search(object=toy_bin_small_2, region=bedroom_0_1)` → 5. `measure(object=toy_bin_small_2)` → 6. `explore_room(room=living_room_0_0)` → 7. `navigate(destination=toy_car)` → 8. `look(target=toy_car)` → 9. `pick(object=toy_car)` → 10. `navigate(destination=toy_bin_small_2)` → 11. `place(object=toy_car, receptacle=toy_bin_small_2)` → 12. `search(object=rubber_duck, region=living_room_0_1)` → 13. `navigate(destination=rubber_duck)` → 14. `pick(object=rubber_duck)` → 15. `navigate(destination=toy_bin_small_2)` → 16. `drop(object=rubber_duck, container=toy_bin_small_2)`
- 摆法 `apart_empty_on_desk`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `search(object=toy_bin_small_2, region=living_room_0_1)` → 5. `measure(object=toy_bin_small_2)` → 6. `explore_room(room=living_room_0_0)` → 7. `navigate(destination=toy_car)` → 8. `look(target=toy_car)` → 9. `pick(object=toy_car)` → 10. `navigate(destination=toy_bin_small_2)` → 11. `place(object=toy_car, receptacle=toy_bin_small_2)` → 12. `search(object=rubber_duck, region=living_room_0_1)` → 13. `navigate(destination=rubber_duck)` → 14. `pick(object=rubber_duck)` → 15. `navigate(destination=toy_bin_small_2)` → 16. `drop(object=rubber_duck, container=toy_bin_small_2)`
- 摆法 `half_bin_and_tray`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `measure(object=toy_tray)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_car)` → 7. `look(target=toy_car)` → 8. `pick(object=toy_car)` → 9. `navigate(destination=toy_tray)` → 10. `place(object=toy_car, receptacle=toy_tray)` → 11. `search(object=rubber_duck, region=living_room_0_1)` → 12. `navigate(destination=rubber_duck)` → 13. `pick(object=rubber_duck)` → 14. `navigate(destination=toy_bin_small)` → 15. `drop(object=rubber_duck, container=toy_bin_small)`
- 摆法 `half_bin_and_tray_duck_dining`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `measure(object=toy_tray)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_car)` → 7. `look(target=toy_car)` → 8. `pick(object=toy_car)` → 9. `navigate(destination=toy_tray)` → 10. `place(object=toy_car, receptacle=toy_tray)` → 11. `search(object=rubber_duck, region=dining_room_0_1)` → 12. `navigate(destination=rubber_duck)` → 13. `pick(object=rubber_duck)` → 14. `navigate(destination=toy_bin_small)` → 15. `drop(object=rubber_duck, container=toy_bin_small)`

### castle_stays（Task）

**情况**：“他搭的积木城堡别拆”：客厅地上一座积木塔，旁边散着同样的积木 → 叠在塔里的不动，散着的积木和小车、鸭子收进筐。检测的是：整局没拿起过塔上的积木（过程要求），结束时每块都在原位、叠放关系还在（终态）。中途被碰倒的话，不拿起来就搭不回去，终态会判失败；碰歪了又恰好推回原位这种情况检测不到

**指令**：快到睡觉时间了，把孩子的玩具收起来。他搭的积木城堡别拆，明天还要接着搭。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **次好（0.6）**：

  - 摆法 `tall_two_loose`、`tall_none_loose`：
    - `toy_car` 在 `storage_basket` 里
    - `rubber_duck` 在 `storage_basket` 里
    - `castle_block_2` 叠在 `castle_block_1` 上
    - `castle_block_3` 叠在 `castle_block_2` 上
    - `storage_basket` 立着
    - 手里空着
  - 摆法 `short_one_loose`：
    - `toy_car` 在 `storage_basket` 里
    - `rubber_duck` 在 `storage_basket` 里
    - `castle_block_2` 叠在 `castle_block_1` 上
    - `storage_basket` 立着
    - 手里空着
- **不行（0）**：城堡拆了没搭回或碰倒了；小车或鸭子没收；还拿着或掉了


**参考调用顺序**：

- 摆法 `tall_two_loose`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `look(target=toy_car)` → 4. `pick(object=toy_car)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=storage_basket)` → 7. `place(object=toy_car, receptacle=storage_basket)` → 8. `navigate(destination=rubber_duck)` → 9. `pick(object=rubber_duck)` → 10. `navigate(destination=storage_basket)` → 11. `place(object=rubber_duck, receptacle=storage_basket)` → 12. `navigate(destination=loose_block_1)` → 13. `look(target=loose_block_1)` → 14. `pick(object=loose_block_1)` → 15. `navigate(destination=storage_basket)` → 16. `place(object=loose_block_1, receptacle=storage_basket)` → 17. `navigate(destination=loose_block_2)` → 18. `look(target=loose_block_2)` → 19. `pick(object=loose_block_2)` → 20. `navigate(destination=storage_basket)` → 21. `place(object=loose_block_2, receptacle=storage_basket)`
- 摆法 `short_one_loose`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `look(target=toy_car)` → 4. `pick(object=toy_car)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=storage_basket)` → 7. `place(object=toy_car, receptacle=storage_basket)` → 8. `navigate(destination=rubber_duck)` → 9. `pick(object=rubber_duck)` → 10. `navigate(destination=storage_basket)` → 11. `place(object=rubber_duck, receptacle=storage_basket)` → 12. `navigate(destination=loose_block_1)` → 13. `look(target=loose_block_1)` → 14. `pick(object=loose_block_1)` → 15. `navigate(destination=storage_basket)` → 16. `place(object=loose_block_1, receptacle=storage_basket)`
- 摆法 `tall_none_loose`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `look(target=toy_car)` → 4. `pick(object=toy_car)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=storage_basket)` → 7. `place(object=toy_car, receptacle=storage_basket)` → 8. `navigate(destination=rubber_duck)` → 9. `pick(object=rubber_duck)` → 10. `navigate(destination=storage_basket)` → 11. `place(object=rubber_duck, receptacle=storage_basket)`

---

## T13_breakfast_setup

> 快吃早饭了，把餐桌上的位子摆好。

### dishes_on_tv_stand（对照）

**情况**：碗和杯子在电视柜，勺子在餐桌 → 摆到勺子旁（杯子在却用马克杯降一档）

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `bowl` 在 `dining_table_2/top` 上
  - `bowl`、`cup` 立着
  - `cup` 在 `dining_table_2/top` 上
  - bowl、cup、spoon 在 `dining_table_2/top` 上摆在一起（彼此不超过 50 cm）
  - 手里空着
- **次好（0.6）**：

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
- **不行（0）**：少一样；倒了；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=bowl)` → 6. `pick(object=bowl)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.948, 7.095])` → 9. `navigate(destination=cup)` → 10. `pick(object=cup)` → 11. `navigate(destination=dining_table_2/top)` → 12. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[2.928, 7.295])`

### no_cup（Task）

**情况**：没杯子 → 用卧室书架上的马克杯

**成功条件**（D 按摆法：`no_cup` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **不行（0）**：少一样；倒了；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=bowl)` → 6. `pick(object=bowl)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.948, 7.095])` → 9. `navigate(destination=cup)` → 10. `navigate(destination=bookcase_2/top)`（换做法） → 11. `look(target=bookcase_2/top)`（换做法） → 12. `pick(object=mug)`（换做法） → 13. `navigate(destination=dining_table_2/top)` → 14. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[2.928, 7.295])`

### copy_the_setting（Task）

**情况**：“照着桌上摆好的那份，在另一把勺子那里也摆一份”：对面已经摆好一份 → 看懂有哪些东西、各在勺子的什么位置（叠没叠），在另一把勺子那儿照样摆；对面坐的人方向相反，左右要按坐的人来算；家里缺的那种用最接近的代替，放在同一个位置

**指令**：照着桌上摆好的那份，在另一把勺子那里也摆一份。

**成功条件**（D 按摆法：`bowl_cup` D = 1、理想物在，`plate_bowl_mug_left` D = 1、理想物在，`no_cup` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `bowl_cup`：
    - `bowl`、`cup` 相对 spoon 的摆法（按坐在那里的人的前后左右）和 `example_bowl`、`example_cup` 相对 example_spoon 的一样，误差不超过 12 cm
    - `example_bowl`、`example_cup`、`example_spoon` 没被挪动（离开局位置不超过 3 cm）
    - `bowl`、`cup` 立着
    - 手里空着
  - 摆法 `no_cup`：
    - `bowl`、`mug` 相对 spoon 的摆法（按坐在那里的人的前后左右）和 `example_bowl`、`example_cup` 相对 example_spoon 的一样，误差不超过 12 cm
    - `example_bowl`、`example_cup`、`example_spoon` 没被挪动（离开局位置不超过 3 cm）
    - `bowl`、`mug` 立着
    - 手里空着
  - 摆法 `plate_bowl_mug_left`：
    - `plate_counter_a`、`bowl`、`mug` 相对 spoon 的摆法（按坐在那里的人的前后左右）和 `example_plate`、`example_bowl`、`example_mug` 相对 example_spoon 的一样，误差不超过 12 cm
    - `example_plate`、`example_bowl`、`example_mug`、`example_spoon` 没被挪动（离开局位置不超过 3 cm）
    - `bowl`、`mug` 立着
    - `bowl` 叠在 `plate_counter_a` 上
    - 手里空着
- **次好（0.6）**：

  - 摆法 `bowl_cup`：
    - `example_bowl`、`example_cup`、`example_spoon` 没被挪动（离开局位置不超过 3 cm）
    - `bowl`、`cup` 立着
    - 手里空着
    - `bowl` 离其中至少一个不超过 30 cm：`spoon`
    - `cup` 离其中至少一个不超过 30 cm：`spoon`
  - 摆法 `no_cup`：
    - `example_bowl`、`example_cup`、`example_spoon` 没被挪动（离开局位置不超过 3 cm）
    - `bowl`、`mug` 立着
    - 手里空着
    - `bowl` 离其中至少一个不超过 30 cm：`spoon`
    - `mug` 离其中至少一个不超过 30 cm：`spoon`
  - 摆法 `plate_bowl_mug_left`：
    - `example_plate`、`example_bowl`、`example_mug`、`example_spoon` 没被挪动（离开局位置不超过 3 cm）
    - `bowl`、`mug` 立着
    - `bowl` 叠在 `plate_counter_a` 上
    - 手里空着
    - `plate_counter_a` 离其中至少一个不超过 30 cm：`spoon`
    - `bowl` 离其中至少一个不超过 30 cm：`spoon`
    - `mug` 离其中至少一个不超过 30 cm：`spoon`
- **最不好（0.3）**：

  - 摆法 `bowl_cup`：
    - `bowl`、`cup` 相对 spoon 的摆法（按坐在那里的人的前后左右）和 `example_bowl`、`example_cup` 相对 example_spoon 的一样，误差不超过 12 cm
    - `bowl`、`cup` 立着
    - 手里空着
  - 摆法 `no_cup`：
    - `bowl`、`mug` 相对 spoon 的摆法（按坐在那里的人的前后左右）和 `example_bowl`、`example_cup` 相对 example_spoon 的一样，误差不超过 12 cm
    - `bowl`、`mug` 立着
    - 手里空着
  - 摆法 `plate_bowl_mug_left`：
    - `plate_counter_a`、`bowl`、`mug` 相对 spoon 的摆法（按坐在那里的人的前后左右）和 `example_plate`、`example_bowl`、`example_mug` 相对 example_spoon 的一样，误差不超过 12 cm
    - `bowl`、`mug` 立着
    - `bowl` 叠在 `plate_counter_a` 上
    - 手里空着
- **不行（0）**：少一样；摆错位置；倒了；还拿着或掉了


**参考调用顺序**：

- 摆法 `bowl_cup`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `measure(object=example_spoon)` → 4. `navigate(destination=tv_stand_2/top)` → 5. `look(target=tv_stand_2/top)` → 6. `navigate(destination=bowl)` → 7. `pick(object=bowl)` → 8. `navigate(destination=dining_table_2/top)` → 9. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.89, 7.49])` → 10. `navigate(destination=cup)` → 11. `pick(object=cup)` → 12. `navigate(destination=dining_table_2/top)` → 13. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[2.89, 7.15])`
- 摆法 `plate_bowl_mug_left`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `measure(object=example_spoon)` → 4. `navigate(destination=kitchen_counter_2/top)` → 5. `look(target=kitchen_counter_2/top)` → 6. `navigate(destination=plate_counter_a)` → 7. `pick(object=plate_counter_a)` → 8. `navigate(destination=dining_table_2/top)` → 9. `place(object=plate_counter_a, receptacle=dining_table_2/top, hint_xy=[2.89, 7.49])` → 10. `navigate(destination=tv_stand_2/top)` → 11. `look(target=tv_stand_2/top)` → 12. `navigate(destination=bowl)` → 13. `pick(object=bowl)` → 14. `navigate(destination=plate_counter_a)` → 15. `stack(object=bowl, base=plate_counter_a)` → 16. `navigate(destination=bookcase_2/top)` → 17. `look(target=bookcase_2/top)` → 18. `navigate(destination=mug)` → 19. `pick(object=mug)` → 20. `navigate(destination=dining_table_2/top)` → 21. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[2.89, 7.68])`
- 摆法 `no_cup`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `measure(object=example_spoon)` → 4. `navigate(destination=tv_stand_2/top)` → 5. `look(target=tv_stand_2/top)` → 6. `navigate(destination=bowl)` → 7. `pick(object=bowl)` → 8. `navigate(destination=dining_table_2/top)` → 9. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.89, 7.49])` → 10. `navigate(destination=bookcase_2/top)` → 11. `look(target=bookcase_2/top)` → 12. `navigate(destination=mug)` → 13. `pick(object=mug)` → 14. `navigate(destination=dining_table_2/top)` → 15. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[2.89, 7.15])`

### finish_the_table（Task）

**情况**：“把桌上剩下的位子也摆好”：已摆好的三份里大人是碗+马克杯，孩子是碗+塑料杯、旁边放着玩具 → 归纳出两条规律，看空位旁边有没有玩具车判断是谁的位子，按对应规律摆

**指令**：把桌上剩下的位子也摆好。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **次好（0.6）**：

  - 摆法 `kid_seat`：
    - `w_mid_spoon` 离其中至少一个不超过 12 cm：`bowl`、`bowl_2`
    - `w_mid_spoon` 离其中至少一个不超过 12 cm：`kid_cup`
    - `w_mid_spoon` 离这些都超过 25 cm：`mug`、`mug_2`
    - 手里空着
  - 摆法 `adult_seat`：
    - `w_mid_spoon` 离其中至少一个不超过 12 cm：`bowl`、`bowl_2`
    - `w_mid_spoon` 离其中至少一个不超过 12 cm：`mug`、`mug_2`
    - `w_mid_spoon` 离这些都超过 25 cm：`kid_cup`
    - 手里空着
  - 摆法 `adult_and_kid`：
    - `w_mid_spoon` 离其中至少一个不超过 12 cm：`bowl`、`bowl_2`
    - `w_mid_spoon` 离其中至少一个不超过 12 cm：`mug`、`mug_2`
    - `w_mid_spoon` 离这些都超过 25 cm：`kid_cup`
    - `w_south_spoon` 离其中至少一个不超过 12 cm：`bowl`、`bowl_2`
    - `w_south_spoon` 离其中至少一个不超过 12 cm：`kid_cup`
    - `w_south_spoon` 离这些都超过 25 cm：`mug_2`
    - 手里空着
- **最不好（0.3）**：

  - 摆法 `adult_seat`、`kid_seat`：
    - `w_mid_spoon` 离其中至少一个不超过 12 cm：`bowl`、`bowl_2`
    - `w_mid_spoon` 离其中至少一个不超过 12 cm：`mug`、`mug_2`、`kid_cup`
    - 手里空着
  - 摆法 `adult_and_kid`：
    - `w_mid_spoon` 离其中至少一个不超过 12 cm：`bowl`、`bowl_2`
    - `w_mid_spoon` 离其中至少一个不超过 12 cm：`mug`、`mug_2`、`kid_cup`
    - `w_south_spoon` 离其中至少一个不超过 12 cm：`bowl`、`bowl_2`
    - `w_south_spoon` 离其中至少一个不超过 12 cm：`mug`、`mug_2`、`kid_cup`
    - 手里空着
- **不行（0）**：有空位没摆或只摆一半；倒了；还拿着或掉了


**参考调用顺序**：

- 摆法 `adult_seat`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=bowl)` → 6. `pick(object=bowl)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.89, 6.89])` → 9. `navigate(destination=bookcase_2/top)` → 10. `look(target=bookcase_2/top)` → 11. `navigate(destination=mug)` → 12. `pick(object=mug)` → 13. `navigate(destination=dining_table_2/top)` → 14. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[2.89, 6.55])`
- 摆法 `kid_seat`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=bowl)` → 6. `pick(object=bowl)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.89, 6.89])` → 9. `navigate(destination=kitchen_counter_2/top)` → 10. `look(target=kitchen_counter_2/top)` → 11. `navigate(destination=kid_cup)` → 12. `pick(object=kid_cup)` → 13. `navigate(destination=dining_table_2/top)` → 14. `place(object=kid_cup, receptacle=dining_table_2/top, hint_xy=[2.89, 6.55])`
- 摆法 `adult_and_kid`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=bowl)` → 6. `pick(object=bowl)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.89, 6.89])` → 9. `navigate(destination=bookcase_2/top)` → 10. `look(target=bookcase_2/top)` → 11. `navigate(destination=mug)` → 12. `pick(object=mug)` → 13. `navigate(destination=dining_table_2/top)` → 14. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[2.89, 6.55])` → 15. `navigate(destination=bowl_2)` → 16. `pick(object=bowl_2)` → 17. `navigate(destination=dining_table_2/top)` → 18. `place(object=bowl_2, receptacle=dining_table_2/top, hint_xy=[2.89, 6.04])` → 19. `navigate(destination=kitchen_counter_2/top)` → 20. `look(target=kitchen_counter_2/top)` → 21. `navigate(destination=kid_cup)` → 22. `pick(object=kid_cup)` → 23. `navigate(destination=dining_table_2/top)` → 24. `place(object=kid_cup, receptacle=dining_table_2/top, hint_xy=[2.89, 5.7])`

---

## T15_cover_the_pot

> 汤要放一会儿再吃，用锅盖把灶台上的汤锅盖好。

### lid_by_pot（对照）

**情况**：锅盖在灶边岛台上 → 盖好

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `handled_cooking_pot` 盖着 `pot_lid`
  - 手里空着
- **不行（0）**：没盖；锅盖掉了或还拿着


**参考调用顺序**：

1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=pot_lid)` → 6. `pick(object=pot_lid)` → 7. `navigate(destination=handled_cooking_pot)` → 8. `cover(container=handled_cooking_pot, lid=pot_lid)`

### lid_elsewhere（Task）

**情况**：锅盖不在灶边，在餐桌上 → 找到；空着就拿来盖；正扣在别人没吃完的燕麦碗上就别动，用厨房台面的盘子盖（最好的替代算好；把锅盖从碗上拿走降一档）

**成功条件**（D 按摆法：`dining` D = 1、理想物在，`covering_bowl` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `dining`：
    - `handled_cooking_pot` 盖着 `pot_lid`
    - 手里空着
  - 摆法 `covering_bowl`：
    - `pot_lid`、`covered_bowl` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `handled_cooking_pot` 盖着 `plate_counter_a`
      - 第 2 组：
        - `handled_cooking_pot` 盖着 `plate_counter_b`
- **次好（0.6）**：

  - 摆法 `dining`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `covering_bowl`：
    - `handled_cooking_pot` 盖着 `pot_lid`
    - `covered_bowl` 立着
    - 手里空着
- **最不好（0.3）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **不行（0）**：没盖；没找到锅盖；碰翻了别人的碗；还拿着


**参考调用顺序**：

- 摆法 `dining`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `search(object=pot_lid, region=dining_room_0_1)` → 6. `navigate(destination=pot_lid)` → 7. `pick(object=pot_lid)` → 8. `navigate(destination=handled_cooking_pot)` → 9. `cover(container=handled_cooking_pot, lid=pot_lid)`
- 摆法 `covering_bowl`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `explore_room(room=dining_room_0_1)` → 6. `look(target=pot_lid)` → 7. `search(object=plate_counter_a, region=kitchen_0_1)` → 8. `navigate(destination=plate_counter_a)` → 9. `pick(object=plate_counter_a)` → 10. `navigate(destination=handled_cooking_pot)` → 11. `cover(container=handled_cooking_pot, lid=plate_counter_a)`

### no_lid（Task）

**情况**：家里没有锅盖；厨房台面有盘子，岛台上有本书 → 用盘子盖（最好的替代算好；用书盖降一档）

**成功条件**（D 按摆法：`no_lid` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `handled_cooking_pot` 盖着 `plate_counter_a`
    - 第 2 组：
      - `handled_cooking_pot` 盖着 `plate_counter_b`
- **次好（0.6）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **最不好（0.3）**：

  - `handled_cooking_pot` 盖着 `cover_book`
  - 手里空着
- **不行（0）**：没盖；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `search(object=plate_counter_a, region=kitchen_0_1)` → 6. `navigate(destination=plate_counter_a)` → 7. `pick(object=plate_counter_a)` → 8. `navigate(destination=handled_cooking_pot)` → 9. `cover(container=handled_cooking_pot, lid=plate_counter_a)`

### lid_in_use（Task）

**情况**：锅盖盖在右边灶眼的炖菜上 → 别动它，用盘子盖汤（拿炖菜的锅盖降一档）

**成功条件**（D 按摆法：`lid_in_use` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `stew_pot` 盖着 `pot_lid`
  - `stew_pot` 立着
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `handled_cooking_pot` 盖着 `plate_counter_a`
    - 第 2 组：
      - `handled_cooking_pot` 盖着 `plate_counter_b`
- **次好（0.6）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **最不好（0.3）**：

  - `handled_cooking_pot` 盖着 `pot_lid`
  - `stew_pot` 立着
  - 手里空着
- **不行（0）**：汤锅没盖；炖菜的锅碰倒了；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `search(object=plate_counter_a, region=kitchen_0_1)` → 6. `navigate(destination=plate_counter_a)` → 7. `pick(object=plate_counter_a)` → 8. `navigate(destination=handled_cooking_pot)` → 9. `cover(container=handled_cooking_pot, lid=plate_counter_a)`

---

## T16_pack_snack_box

> 孩子明天上学要带水果，把一个苹果装进他的零食盒，放到他书桌上。

### box_on_counter（对照）

**情况**：零食盒在厨房台面 → 装好放书桌

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `school_apple` 在 `snack_box` 里
  - `snack_box` 在 `desk_1/top` 上
  - 手里空着
- **不行（0）**：没装好或没放到书桌；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=snack_box)` → 4. `pick(object=snack_box)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=snack_box, receptacle=desk_1/top, hint_xy=[-0.7, -6.2])` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `navigate(destination=school_apple)` → 10. `pick(object=school_apple)` → 11. `navigate(destination=snack_box)` → 12. `place(object=school_apple, receptacle=snack_box)`

### box_in_cabinet（Task）

**情况**：零食盒收在矮柜里 → 开柜拿、关门、装好；零食盒已经装满零食（香蕉、三个橙子）放不下苹果时，用旁边的碗装（最好的替代算好；把零食拿出来腾地方降一档）

**成功条件**（D 按摆法：`in_cabinet` D = 1、理想物在，`box_full` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `in_cabinet`：
    - `school_apple` 在 `snack_box` 里
    - `snack_box` 在 `desk_1/top` 上
    - `kitchen_cabinet_6` 关着
    - 手里空着
  - 摆法 `box_full`：
    - `school_apple` 在 `spare_bowl` 里
    - `spare_bowl` 在 `desk_1/top` 上
    - `box_banana` 在 `snack_box` 里
    - `box_orange_1` 在 `snack_box` 里
    - `box_orange_2` 在 `snack_box` 里
    - `box_orange_3` 在 `snack_box` 里
    - 手里空着
- **次好（0.6）**：

  - `school_apple` 在 `snack_box` 里
  - `snack_box` 在 `desk_1/top` 上
  - 手里空着
- **最不好（0.3）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **不行（0）**：没找到盒子；苹果没装好放到书桌；还拿着或掉了


**参考调用顺序**：

- 摆法 `in_cabinet`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `navigate(destination=snack_box)` → 7. `pick(object=snack_box)` → 8. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=snack_box, receptacle=desk_1/top, hint_xy=[-0.7, -6.2])` → 11. `navigate(destination=kitchen_cabinet_6)` → 12. `close(articulated=kitchen_cabinet_6)` → 13. `navigate(destination=dining_table_2/top)` → 14. `look(target=dining_table_2/top)` → 15. `navigate(destination=school_apple)` → 16. `pick(object=school_apple)` → 17. `navigate(destination=snack_box)` → 18. `place(object=school_apple, receptacle=snack_box)`
- 摆法 `box_full`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=spare_bowl)` → 4. `pick(object=spare_bowl)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=spare_bowl, receptacle=desk_1/top, hint_xy=[-0.7, -6.2])` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `navigate(destination=school_apple)` → 10. `pick(object=school_apple)` → 11. `navigate(destination=spare_bowl)` → 12. `place(object=school_apple, receptacle=spare_bowl)`

### no_box（Task）

**情况**：家里没有零食盒；台面有碗，电视柜有大收纳箱 → 用碗（用大收纳箱降一档）

**成功条件**（D 按摆法：`no_box` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `school_apple` 在 `spare_bowl` 里
  - `spare_bowl` 在 `desk_1/top` 上
  - 手里空着
- **次好（0.6）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **最不好（0.3）**：

  - `school_apple` 在 `big_bin` 里
  - 手里空着
- **不行（0）**：苹果没装；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=spare_bowl)` → 4. `pick(object=spare_bowl)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=spare_bowl, receptacle=desk_1/top, hint_xy=[-0.7, -6.2])` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `navigate(destination=school_apple)` → 10. `pick(object=school_apple)` → 11. `navigate(destination=spare_bowl)` → 12. `place(object=school_apple, receptacle=spare_bowl)`

### box_in_use（Task）

**情况**：零食盒里放着孩子的蜡笔和积木 → 别动，用碗（硬塞进盒子降一档）

**成功条件**（D 按摆法：`box_in_use` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `school_apple` 在 `spare_bowl` 里
  - `spare_bowl` 在 `desk_1/top` 上
  - `box_crayon_1` 在 `snack_box` 里
  - `box_crayon_2` 在 `snack_box` 里
  - `box_block` 在 `snack_box` 里
  - 手里空着
- **次好（0.6）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **最不好（0.3）**：

  - `school_apple` 在 `snack_box` 里
  - `snack_box` 在 `desk_1/top` 上
  - `box_crayon_1` 在 `snack_box` 里
  - `box_crayon_2` 在 `snack_box` 里
  - `box_block` 在 `snack_box` 里
  - 手里空着
- **不行（0）**：把孩子的东西倒出来；苹果没装；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=spare_bowl)` → 4. `pick(object=spare_bowl)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=spare_bowl, receptacle=desk_1/top, hint_xy=[-0.7, -6.2])` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `navigate(destination=school_apple)` → 10. `pick(object=school_apple)` → 11. `navigate(destination=spare_bowl)` → 12. `place(object=school_apple, receptacle=spare_bowl)`

---

## T17_hide_and_seek_block

> 陪孩子玩藏东西的游戏：把木积木藏进灶台上的空锅里，再盖好锅盖，别让孩子一眼看到。

### lid_off（对照）

**情况**：锅盖在锅边 → 藏好、盖上

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `wooden_block_b` 藏好了（从房间里看不到）
  - `handled_cooking_pot` 盖着 `pot_lid`
  - 手里空着
- **次好（0.6）**：

  - `wooden_block_b` 藏好了（从房间里看不到）
  - 手里空着
  - `["not on", "wooden_block_b", "kitchen_microwave/inside_floor"]`
  - `["not on", "wooden_block_b", "breakfast_fridge/inside_shelf"]`
- **不行（0）**：积木一眼能看到；藏进微波炉或冰箱；还拿着


**参考调用顺序**：

1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)`

### h_task_lid_elsewhere（Task）

**情况**：锅盖在靠墙柜上 → 先拿回灶台再藏；锅盖正盖在右边灶眼的炖菜上时别动它，用岛台上的盘子盖（最好的替代算好；拿炖菜的盖子降一档）

**成功条件**（D 按摆法：`h_task_lid_elsewhere` D = 1、理想物在，`hide_lid_in_use` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `hide_lid_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 藏好了（从房间里看不到）
        - `handled_cooking_pot` 盖着 `cover_plate`
        - `stew_pot` 盖着 `pot_lid`
        - `stew_pot` 立着
  - 摆法 `h_task_lid_elsewhere`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 藏好了（从房间里看不到）
        - `handled_cooking_pot` 盖着 `pot_lid`
- **次好（0.6）**：

  - 摆法 `hide_lid_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 藏好了（从房间里看不到）
        - `handled_cooking_pot` 盖着 `pot_lid`
  - 摆法 `h_task_lid_elsewhere`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 藏好了（从房间里看不到）
        - `["not on", "wooden_block_b", "kitchen_microwave/inside_floor"]`
        - `["not on", "wooden_block_b", "breakfast_fridge/inside_shelf"]`
- **最不好（0.3）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **不行（0）**：积木一眼能看到；藏进微波炉或冰箱；碰倒炖菜；还拿着


**参考调用顺序**：

- 摆法 `h_task_lid_elsewhere`：1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=pot_lid)` → 4. `pick(object=pot_lid)` → 5. `navigate(destination=kitchen_stove/top)` → 6. `place(object=pot_lid, receptacle=kitchen_stove/top, hint_xy=[8.715, 1.655])` → 7. `navigate(destination=handled_cooking_pot)` → 8. `look(target=kitchen_stove/top)` → 9. `navigate(destination=kitchen_island/top)` → 10. `look(target=kitchen_island/top)` → 11. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)`
- 摆法 `hide_lid_in_use`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=cover_plate)`

### hide_both（Task）

**情况**：两块积木藏进同一个空锅，另一块在别的房间 → 找到第二块，中间再揭一次盖，最后盖好；灶上另一口锅装着汤，不是空锅（放进汤锅算差）

**指令**：我们在和孩子玩捉迷藏，藏的是他的玩具积木：把两块木积木都藏进灶上那个空锅里，再盖上锅盖，别让孩子看见。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `two_pots`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 藏好了（从房间里看不到）
        - `floor_block` 藏好了（从房间里看不到）
        - `handled_cooking_pot` 盖着 `pot_lid`
        - `full_soup_pot` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `tv_stand`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 藏好了（从房间里看不到）
        - `floor_block` 藏好了（从房间里看不到）
        - `handled_cooking_pot` 盖着 `pot_lid`
- **次好（0.6）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_b` 藏好了（从房间里看不到）
      - `floor_block` 藏好了（从房间里看不到）
      - `["not on", "wooden_block_b", "kitchen_microwave/inside_floor"]`
      - `["not on", "wooden_block_b", "breakfast_fridge/inside_shelf"]`
      - `["not on", "floor_block", "kitchen_microwave/inside_floor"]`
      - `["not on", "floor_block", "breakfast_fridge/inside_shelf"]`
- **最不好（0.3）**：

  - 摆法 `tv_stand`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `two_pots`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 在 `full_soup_pot` 里
      - 第 2 组：
        - `floor_block` 在 `full_soup_pot` 里
- **不行（0）**：积木一眼能看到；藏进微波炉或冰箱；还拿着


**参考调用顺序**：

- 摆法 `tv_stand`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)` → 6. `search(object=floor_block, region=living_room_0_0)`（补救） → 7. `navigate(destination=handled_cooking_pot)`（补救） → 8. `uncover(container=handled_cooking_pot)`（补救） → 9. `navigate(destination=floor_block)`（补救） → 10. `look(target=floor_block)`（补救） → 11. `hide(object=floor_block, receptacle=handled_cooking_pot, lid=pot_lid)`（补救）
- 摆法 `two_pots`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)` → 6. `search(object=floor_block, region=dining_room_0_1)`（补救） → 7. `navigate(destination=handled_cooking_pot)`（补救） → 8. `uncover(container=handled_cooking_pot)`（补救） → 9. `navigate(destination=floor_block)`（补救） → 10. `look(target=floor_block)`（补救） → 11. `hide(object=floor_block, receptacle=handled_cooking_pot, lid=pot_lid)`（补救）

### hide_somewhere（Task）

**情况**：指令只说“把木积木藏到孩子一眼看不到的地方，别藏进电器里，危险”，没说藏哪 → 自己挑能藏住又不是电器的地方：锅盖在手边就藏进灶上的锅里盖好；锅盖被收到靠墙柜上了，就藏进矮柜里关好门（藏进微波炉或冰箱算失败）

**指令**：陪孩子玩捉迷藏，把木积木藏到孩子一眼看不到的地方。别藏进电器里，危险。

**成功条件**（D 按摆法：`pot_ready` D = 1、理想物在，`lid_away` D = 0、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `lid_away`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 藏好了（从房间里看不到）
        - `["not on", "wooden_block_b", "kitchen_microwave/inside_floor"]`
        - `["not on", "wooden_block_b", "breakfast_fridge/inside_shelf"]`
  - 摆法 `pot_ready`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 在 `handled_cooking_pot` 里
        - `handled_cooking_pot` 盖着 `pot_lid`
        - `["not on", "wooden_block_b", "kitchen_microwave/inside_floor"]`
        - `["not on", "wooden_block_b", "breakfast_fridge/inside_shelf"]`
- **次好（0.6）**：

  - 摆法 `lid_away`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `pot_ready`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `wooden_block_b` 藏好了（从房间里看不到）
        - `["not on", "wooden_block_b", "kitchen_microwave/inside_floor"]`
        - `["not on", "wooden_block_b", "breakfast_fridge/inside_shelf"]`
- **最不好（0.3）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **不行（0）**：一眼能看到；藏进微波炉或冰箱；还拿着


**参考调用顺序**：

- 摆法 `pot_ready`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)`
- 摆法 `lid_away`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_stove/top)` → 4. `look(target=kitchen_stove/top)` → 5. `navigate(destination=kitchen_cabinet_4)` → 6. `open(articulated=kitchen_cabinet_4)` → 7. `navigate(destination=wooden_block_b)` → 8. `pick(object=wooden_block_b, grasp=side)` → 9. `navigate(destination=kitchen_cabinet_4)` → 10. `place(object=wooden_block_b, receptacle=kitchen_cabinet_4/inside_shelf, hint_xy=[1.4, 0.42])` → 11. `close(articulated=kitchen_cabinet_4)`

---

## T18_set_out_bowls

> 快吃晚饭了，从靠墙矮柜里拿两只干净的碗摆到餐桌上，每只碗配一把勺子。

### bowls_in_cabinet（对照）

**成功条件**（D 按摆法：`bowls_in_cabinet` D = 0、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `dinner_bowl_1` 在 `dining_table_2/top` 上
  - `dinner_bowl_2` 在 `dining_table_2/top` 上
  - `dinner_spoon_1` 在 `dining_table_2/top` 上
  - `dinner_spoon_2` 在 `dining_table_2/top` 上
  - `kitchen_cabinet_6` 关着
  - 手里空着
- **次好（0.6）**：

  - `dinner_bowl_1` 在 `dining_table_2/top` 上
  - `dinner_bowl_2` 在 `dining_table_2/top` 上
  - `dinner_spoon_1` 在 `dining_table_2/top` 上
  - `dinner_spoon_2` 在 `dining_table_2/top` 上
  - 手里空着
- **不行（0）**：碗或勺子不到两个；碗掉了；还拿着


**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `navigate(destination=dinner_bowl_1)` → 7. `pick(object=dinner_bowl_1)` → 8. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 9. `navigate(destination=dining_table_2/top)` → 10. `place(object=dinner_bowl_1, receptacle=dining_table_2/top, hint_xy=[3.688, 6.195])` → 11. `navigate(destination=dinner_bowl_2)` → 12. `pick(object=dinner_bowl_2)` → 13. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 14. `navigate(destination=dining_table_2/top)` → 15. `place(object=dinner_bowl_2, receptacle=dining_table_2/top, hint_xy=[3.688, 6.755])` → 16. `navigate(destination=kitchen_cabinet_6)` → 17. `close(articulated=kitchen_cabinet_6)` → 18. `navigate(destination=kitchen_counter_2/top)` → 19. `look(target=kitchen_counter_2/top)` → 20. `navigate(destination=dinner_spoon_1)` → 21. `pick(object=dinner_spoon_1)` → 22. `navigate(destination=dining_table_2/top)` → 23. `place(object=dinner_spoon_1, receptacle=dining_table_2/top, hint_xy=[3.688, 6.415])` → 24. `navigate(destination=dinner_spoon_2)` → 25. `pick(object=dinner_spoon_2)` → 26. `navigate(destination=dining_table_2/top)` → 27. `place(object=dinner_spoon_2, receptacle=dining_table_2/top, hint_xy=[3.688, 6.975])`

### bowls_apart（对照）

**成功条件**（D 按摆法：`bowls_apart` D = 0、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `dinner_bowl_1` 在 `dining_table_2/top` 上
  - `dinner_bowl_2` 在 `dining_table_2/top` 上
  - `dinner_spoon_1` 在 `dining_table_2/top` 上
  - `dinner_spoon_2` 在 `dining_table_2/top` 上
  - `kitchen_cabinet_6` 关着
  - `kitchen_cabinet_4` 关着
  - 手里空着
- **次好（0.6）**：

  - `dinner_bowl_1` 在 `dining_table_2/top` 上
  - `dinner_bowl_2` 在 `dining_table_2/top` 上
  - `dinner_spoon_1` 在 `dining_table_2/top` 上
  - `dinner_spoon_2` 在 `dining_table_2/top` 上
  - 手里空着
- **不行（0）**：碗或勺子不到两个；碗掉了；还拿着


**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `navigate(destination=dinner_bowl_1)` → 7. `pick(object=dinner_bowl_1)` → 8. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 9. `navigate(destination=dining_table_2/top)` → 10. `place(object=dinner_bowl_1, receptacle=dining_table_2/top, hint_xy=[3.688, 6.195])` → 11. `navigate(destination=kitchen_cabinet_6)` → 12. `close(articulated=kitchen_cabinet_6)` → 13. `navigate(destination=kitchen_cabinet_4)` → 14. `open(articulated=kitchen_cabinet_4)` → 15. `bend()` → 16. `explore_furniture(furniture=kitchen_cabinet_4)` → 17. `straighten()` → 18. `navigate(destination=dinner_bowl_2)` → 19. `pick(object=dinner_bowl_2)` → 20. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 21. `navigate(destination=dining_table_2/top)` → 22. `place(object=dinner_bowl_2, receptacle=dining_table_2/top, hint_xy=[3.688, 6.755])` → 23. `navigate(destination=kitchen_cabinet_4)` → 24. `close(articulated=kitchen_cabinet_4)` → 25. `navigate(destination=kitchen_counter_2/top)` → 26. `look(target=kitchen_counter_2/top)` → 27. `navigate(destination=dinner_spoon_1)` → 28. `pick(object=dinner_spoon_1)` → 29. `navigate(destination=dining_table_2/top)` → 30. `place(object=dinner_spoon_1, receptacle=dining_table_2/top, hint_xy=[3.688, 6.415])` → 31. `navigate(destination=dinner_spoon_2)` → 32. `pick(object=dinner_spoon_2)` → 33. `navigate(destination=dining_table_2/top)` → 34. `place(object=dinner_spoon_2, receptacle=dining_table_2/top, hint_xy=[3.688, 6.975])`

### one_bowl（Task）

**成功条件**（D 按摆法：`glass_box` D = 1、理想物不在，`mug` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `glass_box`：
    - `dinner_bowl_1` 在 `dining_table_2/top` 上
    - `glass_box` 在 `dining_table_2/top` 上
    - `dinner_spoon_1` 在 `dining_table_2/top` 上
    - `dinner_spoon_2` 在 `dining_table_2/top` 上
    - `kitchen_cabinet_6` 关着
    - 手里空着
  - 摆法 `mug`：
    - `dinner_bowl_1` 在 `dining_table_2/top` 上
    - `spare_mug` 在 `dining_table_2/top` 上
    - `dinner_spoon_1` 在 `dining_table_2/top` 上
    - `dinner_spoon_2` 在 `dining_table_2/top` 上
    - `kitchen_cabinet_6` 关着
    - 手里空着
- **最不好（0.3）**：

  - `dinner_bowl_1` 在 `dining_table_2/top` 上
  - `plate_counter_a` 在其中任一处上：`dining_table_2/top`
  - 手里空着
- **不行（0）**：只摆了一只；碗掉了；还拿着


**参考调用顺序**：

- 摆法 `glass_box`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `navigate(destination=dinner_bowl_1)` → 7. `pick(object=dinner_bowl_1)` → 8. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 9. `navigate(destination=dining_table_2/top)` → 10. `place(object=dinner_bowl_1, receptacle=dining_table_2/top, hint_xy=[3.688, 6.195])` → 11. `navigate(destination=kitchen_cabinet_6)` → 12. `close(articulated=kitchen_cabinet_6)` → 13. `navigate(destination=kitchen_counter_2/top)` → 14. `look(target=kitchen_counter_2/top)` → 15. `navigate(destination=glass_box)` → 16. `pick(object=glass_box)` → 17. `navigate(destination=dining_table_2/top)` → 18. `place(object=glass_box, receptacle=dining_table_2/top, hint_xy=[3.688, 6.755])` → 19. `navigate(destination=dinner_spoon_1)` → 20. `pick(object=dinner_spoon_1)` → 21. `navigate(destination=dining_table_2/top)` → 22. `place(object=dinner_spoon_1, receptacle=dining_table_2/top, hint_xy=[3.688, 6.415])` → 23. `navigate(destination=dinner_spoon_2)` → 24. `pick(object=dinner_spoon_2)` → 25. `navigate(destination=dining_table_2/top)` → 26. `place(object=dinner_spoon_2, receptacle=dining_table_2/top, hint_xy=[3.688, 6.975])`
- 摆法 `mug`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `navigate(destination=dinner_bowl_1)` → 7. `pick(object=dinner_bowl_1)` → 8. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 9. `navigate(destination=dining_table_2/top)` → 10. `place(object=dinner_bowl_1, receptacle=dining_table_2/top, hint_xy=[3.688, 6.195])` → 11. `navigate(destination=kitchen_cabinet_6)` → 12. `close(articulated=kitchen_cabinet_6)` → 13. `navigate(destination=kitchen_counter_2/top)` → 14. `look(target=kitchen_counter_2/top)` → 15. `navigate(destination=spare_mug)` → 16. `pick(object=spare_mug)` → 17. `navigate(destination=dining_table_2/top)` → 18. `place(object=spare_mug, receptacle=dining_table_2/top, hint_xy=[3.688, 6.755])` → 19. `navigate(destination=dinner_spoon_1)` → 20. `pick(object=dinner_spoon_1)` → 21. `navigate(destination=dining_table_2/top)` → 22. `place(object=dinner_spoon_1, receptacle=dining_table_2/top, hint_xy=[3.688, 6.415])` → 23. `navigate(destination=dinner_spoon_2)` → 24. `pick(object=dinner_spoon_2)` → 25. `navigate(destination=dining_table_2/top)` → 26. `place(object=dinner_spoon_2, receptacle=dining_table_2/top, hint_xy=[3.688, 6.975])`

### bowl_in_use（Task）

**成功条件**（D 按摆法：`tomatoes` D = 1、理想物不在，`oatmeal` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `tomatoes`：
    - `dinner_bowl_1` 在 `dining_table_2/top` 上
    - `glass_box` 在 `dining_table_2/top` 上
    - `dinner_spoon_1` 在 `dining_table_2/top` 上
    - `dinner_spoon_2` 在 `dining_table_2/top` 上
    - `kitchen_cabinet_6` 关着
    - 手里空着
    - `dinner_bowl_2` 在 `kitchen_cabinet_6/inside_shelf` 上
    - `left_tomato_1` 在 `dinner_bowl_2` 里
    - `left_tomato_2` 在 `dinner_bowl_2` 里
  - 摆法 `oatmeal`：
    - `dinner_bowl_1` 在 `dining_table_2/top` 上
    - `glass_box` 在 `dining_table_2/top` 上
    - `dinner_spoon_1` 在 `dining_table_2/top` 上
    - `dinner_spoon_2` 在 `dining_table_2/top` 上
    - `kitchen_cabinet_6` 关着
    - 手里空着
    - `dinner_bowl_2` 在 `kitchen_cabinet_6/inside_shelf` 上
- **最不好（0.3）**：

  - `dinner_bowl_1` 在 `dining_table_2/top` 上
  - `dinner_bowl_2` 在 `dining_table_2/top` 上
  - 手里空着
- **不行（0）**：剩菜倒出来了；不到两个；还拿着


**参考调用顺序**：

- 摆法 `tomatoes`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `navigate(destination=dinner_bowl_1)` → 7. `pick(object=dinner_bowl_1)` → 8. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 9. `navigate(destination=dining_table_2/top)` → 10. `place(object=dinner_bowl_1, receptacle=dining_table_2/top, hint_xy=[3.688, 6.195])` → 11. `navigate(destination=kitchen_cabinet_6)` → 12. `close(articulated=kitchen_cabinet_6)` → 13. `navigate(destination=kitchen_counter_2/top)` → 14. `look(target=kitchen_counter_2/top)` → 15. `navigate(destination=glass_box)` → 16. `pick(object=glass_box)` → 17. `navigate(destination=dining_table_2/top)` → 18. `place(object=glass_box, receptacle=dining_table_2/top, hint_xy=[3.688, 6.755])` → 19. `navigate(destination=dinner_spoon_1)` → 20. `pick(object=dinner_spoon_1)` → 21. `navigate(destination=dining_table_2/top)` → 22. `place(object=dinner_spoon_1, receptacle=dining_table_2/top, hint_xy=[3.688, 6.415])` → 23. `navigate(destination=dinner_spoon_2)` → 24. `pick(object=dinner_spoon_2)` → 25. `navigate(destination=dining_table_2/top)` → 26. `place(object=dinner_spoon_2, receptacle=dining_table_2/top, hint_xy=[3.688, 6.975])`
- 摆法 `oatmeal`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `navigate(destination=dinner_bowl_1)` → 7. `pick(object=dinner_bowl_1)` → 8. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 9. `navigate(destination=dining_table_2/top)` → 10. `place(object=dinner_bowl_1, receptacle=dining_table_2/top, hint_xy=[3.688, 6.195])` → 11. `navigate(destination=kitchen_cabinet_6)` → 12. `close(articulated=kitchen_cabinet_6)` → 13. `navigate(destination=kitchen_counter_2/top)` → 14. `look(target=kitchen_counter_2/top)` → 15. `navigate(destination=glass_box)` → 16. `pick(object=glass_box)` → 17. `navigate(destination=dining_table_2/top)` → 18. `place(object=glass_box, receptacle=dining_table_2/top, hint_xy=[3.688, 6.755])` → 19. `navigate(destination=dinner_spoon_1)` → 20. `pick(object=dinner_spoon_1)` → 21. `navigate(destination=dining_table_2/top)` → 22. `place(object=dinner_spoon_1, receptacle=dining_table_2/top, hint_xy=[3.688, 6.415])` → 23. `navigate(destination=dinner_spoon_2)` → 24. `pick(object=dinner_spoon_2)` → 25. `navigate(destination=dining_table_2/top)` → 26. `place(object=dinner_spoon_2, receptacle=dining_table_2/top, hint_xy=[3.688, 6.975])`

### door_stuck（Task）

**成功条件**（D 按摆法：`door_stuck` D = 0、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `dinner_bowl_1` 在 `dining_table_2/top` 上
  - `dinner_bowl_2` 在 `dining_table_2/top` 上
  - `dinner_spoon_1` 在 `dining_table_2/top` 上
  - `dinner_spoon_2` 在 `dining_table_2/top` 上
  - `kitchen_cabinet_4` 关着
  - 手里空着
- **不行（0）**：碗或勺子不到两个；还拿着


**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6)` → 2. `look(target=kitchen_cabinet_6)` → 3. `navigate(destination=kitchen_cabinet_4)` → 4. `open(articulated=kitchen_cabinet_4)` → 5. `bend()` → 6. `explore_furniture(furniture=kitchen_cabinet_4)` → 7. `straighten()` → 8. `navigate(destination=dinner_bowl_1)` → 9. `pick(object=dinner_bowl_1)` → 10. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 11. `navigate(destination=dining_table_2/top)` → 12. `place(object=dinner_bowl_1, receptacle=dining_table_2/top, hint_xy=[3.688, 6.195])` → 13. `navigate(destination=dinner_bowl_2)` → 14. `pick(object=dinner_bowl_2)` → 15. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 16. `navigate(destination=dining_table_2/top)` → 17. `place(object=dinner_bowl_2, receptacle=dining_table_2/top, hint_xy=[3.688, 6.755])` → 18. `navigate(destination=kitchen_cabinet_4)` → 19. `close(articulated=kitchen_cabinet_4)` → 20. `navigate(destination=kitchen_counter_2/top)` → 21. `look(target=kitchen_counter_2/top)` → 22. `navigate(destination=dinner_spoon_1)` → 23. `pick(object=dinner_spoon_1)` → 24. `navigate(destination=dining_table_2/top)` → 25. `place(object=dinner_spoon_1, receptacle=dining_table_2/top, hint_xy=[3.688, 6.415])` → 26. `navigate(destination=dinner_spoon_2)` → 27. `pick(object=dinner_spoon_2)` → 28. `navigate(destination=dining_table_2/top)` → 29. `place(object=dinner_spoon_2, receptacle=dining_table_2/top, hint_xy=[3.688, 6.975])`

---

## T19_recycling

> 电影看完了，把该回收的东西放进回收箱。

### bin_on_bookcase（对照）

**情况**：罐子在电视柜，泡沫块在客厅地上 → 两样都放进回收箱

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `soda_can` 在 `wide_storage_bin` 里
  - `foam_cube` 在 `wide_storage_bin` 里
  - 手里空着
- **不行（0）**：有一样没进回收箱；还拿着或掉了


**参考调用顺序**：

1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=soda_can)` → 5. `pick(object=soda_can)` → 6. `navigate(destination=bookcase_2/top)` → 7. `look(target=bookcase_2/top)` → 8. `navigate(destination=wide_storage_bin)` → 9. `drop(object=soda_can, container=wide_storage_bin)` → 10. `navigate(destination=foam_cube)` → 11. `look(target=foam_cube)` → 12. `pick(object=foam_cube)` → 13. `navigate(destination=wide_storage_bin)` → 14. `drop(object=foam_cube, container=wide_storage_bin)`

### m_can_in_dining_room（Task）

**情况**：罐子不在原处，看不到 → 先找；餐桌上另一罐摆在别人座位上（旁边有燕麦碗和摊开的书，还在喝）就别动，只回收喝完的那罐（把在喝的也回收算差）

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `can_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `wide_storage_bin` 里
        - `foam_cube` 在 `wide_storage_bin` 里
        - `seat_can` 没被挪动（离开局位置不超过 3 cm）
        - `seat_bowl` 没被挪动（离开局位置不超过 3 cm）
        - `seat_book` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `m_can_in_dining_room`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `wide_storage_bin` 里
        - `foam_cube` 在 `wide_storage_bin` 里
- **次好（0.6）**：

  - 摆法 `m_can_in_dining_room`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `can_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `wide_storage_bin` 里
        - `foam_cube` 在 `wide_storage_bin` 里
        - `seat_can` 不在 `wide_storage_bin` 里
- **最不好（0.3）**：

  - 摆法 `m_can_in_dining_room`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `can_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `wide_storage_bin` 里
        - `foam_cube` 在 `wide_storage_bin` 里
- **不行（0）**：罐子或泡沫块没进回收箱；还拿着或掉了


**参考调用顺序**：

- 摆法 `m_can_in_dining_room`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=dining_room_0_1)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `navigate(destination=wide_storage_bin)` → 10. `drop(object=soda_can, container=wide_storage_bin)` → 11. `navigate(destination=foam_cube)` → 12. `look(target=foam_cube)` → 13. `pick(object=foam_cube)` → 14. `navigate(destination=wide_storage_bin)` → 15. `drop(object=foam_cube, container=wide_storage_bin)`
- 摆法 `can_in_use`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=dining_room_0_1)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `navigate(destination=wide_storage_bin)` → 10. `drop(object=soda_can, container=wide_storage_bin)` → 11. `navigate(destination=foam_cube)` → 12. `look(target=foam_cube)` → 13. `pick(object=foam_cube)` → 14. `navigate(destination=wide_storage_bin)` → 15. `drop(object=foam_cube, container=wide_storage_bin)`

### lookalike_bin（Task）

**情况**：罐子不在原处；客厅还有个一模一样、装着积木的箱子 → 认准书架上那个（里面有塑料杯）

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `soda_can` 在 `wide_storage_bin` 里
  - `foam_cube` 在 `wide_storage_bin` 里
  - 手里空着
- **最不好（0.3）**：

  - `soda_can` 在 `toy_storage_bin` 里
  - `foam_cube` 在 `toy_storage_bin` 里
  - `toy_block_in_bin_1` 在 `toy_storage_bin` 里
  - `toy_block_in_bin_2` 在 `toy_storage_bin` 里
  - 手里空着
- **不行（0）**：分在两个箱子；动了积木；有一样没收；还拿着或掉了


**参考调用顺序**：

- 摆法 `lookalike_bin`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=dining_room_0_1)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `identify(object=wide_storage_bin)`（补救） → 10. `navigate(destination=wide_storage_bin)` → 11. `drop(object=soda_can, container=wide_storage_bin)` → 12. `navigate(destination=foam_cube)` → 13. `touch(object=foam_cube)`（补救） → 14. `pick(object=foam_cube)` → 15. `navigate(destination=wide_storage_bin)` → 16. `drop(object=foam_cube, container=wide_storage_bin)`
- 摆法 `alt_tv_stand_2`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=living_room_0_0)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `identify(object=wide_storage_bin)`（补救） → 10. `navigate(destination=wide_storage_bin)` → 11. `drop(object=soda_can, container=wide_storage_bin)` → 12. `navigate(destination=foam_cube)` → 13. `touch(object=foam_cube)`（补救） → 14. `pick(object=foam_cube)` → 15. `navigate(destination=wide_storage_bin)` → 16. `drop(object=foam_cube, container=wide_storage_bin)`

### x6_gd_can_put_away（Task）

**情况**：指令只说“把该回收的东西放进回收箱” → 空罐被收进了厨房矮柜，打开找，泡沫块在客厅地上，两样都放进回收箱，门都关好（门没关降一档）；另一个柜里那瓶果汁没开封，不是垃圾（回收了算差）

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `in_4`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `wide_storage_bin` 里
        - `foam_cube` 在 `wide_storage_bin` 里
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
  - 摆法 `juice_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `wide_storage_bin` 里
        - `foam_cube` 在 `wide_storage_bin` 里
        - `full_juice` 没被挪动（离开局位置不超过 3 cm）
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
- **次好（0.6）**：

  - 摆法 `juice_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `wide_storage_bin` 里
        - `foam_cube` 在 `wide_storage_bin` 里
        - `full_juice` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `soda_can` 在 `wide_storage_bin` 里
        - `foam_cube` 在 `wide_storage_bin` 里
        - `full_juice` 不在 `wide_storage_bin` 里
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
  - 摆法 `in_4`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `wide_storage_bin` 里
        - `foam_cube` 在 `wide_storage_bin` 里
- **最不好（0.3）**：

  - 摆法 `in_4`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `juice_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `soda_can` 在 `wide_storage_bin` 里
        - `foam_cube` 在 `wide_storage_bin` 里
        - `full_juice` 不在 `wide_storage_bin` 里
      - 第 2 组：
        - `soda_can` 在 `wide_storage_bin` 里
        - `foam_cube` 在 `wide_storage_bin` 里
        - `kitchen_cabinet_6` 关着
        - `kitchen_cabinet_4` 关着
      - 第 3 组：
        - `soda_can` 在 `wide_storage_bin` 里
        - `foam_cube` 在 `wide_storage_bin` 里
- **不行（0）**：罐子或泡沫块没进回收箱；还拿着或掉了


**参考调用顺序**：

- 摆法 `in_4`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=soda_can)` → 13. `pick(object=soda_can)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `navigate(destination=bookcase_2/top)` → 16. `look(target=bookcase_2/top)` → 17. `navigate(destination=wide_storage_bin)` → 18. `drop(object=soda_can, container=wide_storage_bin)` → 19. `navigate(destination=kitchen_cabinet_4)` → 20. `close(articulated=kitchen_cabinet_4)` → 21. `explore_room(room=living_room_0_0)` → 22. `navigate(destination=foam_cube)` → 23. `look(target=foam_cube)` → 24. `pick(object=foam_cube)` → 25. `navigate(destination=wide_storage_bin)` → 26. `drop(object=foam_cube, container=wide_storage_bin)`
- 摆法 `juice_full`：1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_4)` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=soda_can)` → 13. `pick(object=soda_can)` → 14. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 15. `navigate(destination=bookcase_2/top)` → 16. `look(target=bookcase_2/top)` → 17. `navigate(destination=wide_storage_bin)` → 18. `drop(object=soda_can, container=wide_storage_bin)` → 19. `navigate(destination=kitchen_cabinet_6)` → 20. `close(articulated=kitchen_cabinet_6)` → 21. `explore_room(room=living_room_0_0)` → 22. `navigate(destination=foam_cube)` → 23. `look(target=foam_cube)` → 24. `pick(object=foam_cube)` → 25. `navigate(destination=wide_storage_bin)` → 26. `drop(object=foam_cube, container=wide_storage_bin)`

---

## T20_juice_back_to_table

> 有人把早餐桌上的果汁瓶拿走随手放下了。把它放回餐桌上，立着放。

### bottle_on_cabinet（对照）

**情况**：瓶子在靠墙柜顶 → 放回餐桌

**成功条件**（D 按摆法：`bottle_on_cabinet` D = 0、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `juice_bottle` 在 `dining_table_2/top` 上
  - `juice_bottle` 立着
  - 手里空着
- **最不好（0.3）**：

  - `juice_bottle` 在 `dining_table_2/top` 上
  - 手里空着
- **不行（0）**：没放回餐桌；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=juice_bottle)` → 4. `pick(object=juice_bottle)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[2.948, 7.295])`

### m_bottle_on_tv_stand（Task）

**情况**：瓶子在客厅看不到的地方 → 先找；早餐那瓶在靠墙柜顶，电视柜上另一瓶一样的果汁旁边有倒好的杯子（有人在喝）就别动（拿错那瓶降一档）

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `bottle_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `juice_bottle` 在 `dining_table_2/top` 上
        - `juice_bottle` 立着
        - `living_juice` 没被挪动（离开局位置不超过 3 cm）
        - `living_cup` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `m_bottle_on_tv_stand`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `juice_bottle` 在 `dining_table_2/top` 上
        - `juice_bottle` 立着
- **次好（0.6）**：

  - 摆法 `m_bottle_on_tv_stand`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `juice_bottle` 在 `dining_table_2/top` 上
  - 摆法 `bottle_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_juice` 在 `dining_table_2/top` 上
        - `living_juice` 立着
      - 第 2 组：
        - `juice_bottle` 在 `dining_table_2/top` 上
        - `living_juice` 没被挪动（离开局位置不超过 3 cm）
        - `living_cup` 没被挪动（离开局位置不超过 3 cm）
- **最不好（0.3）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **不行（0）**：没有瓶子回到餐桌；还拿着或掉了


**参考调用顺序**：

- 摆法 `m_bottle_on_tv_stand`：1. `search(object=juice_bottle, region=living_room_0_0)` → 2. `navigate(destination=juice_bottle)` → 3. `pick(object=juice_bottle)` → 4. `navigate(destination=dining_table_2/top)` → 5. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[2.948, 7.295])`
- 摆法 `bottle_in_use`：1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=juice_bottle)` → 4. `pick(object=juice_bottle)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[2.948, 7.295])`

### x6_gd_bottle_put_away（Task）

**情况**：指令就是任务原话 → 早餐那瓶被随手放在一个台面上（单独一瓶、歪着）；另一个台面上整齐并排放着三瓶新的同款果汁（囤货）→ 拿随手放的那瓶（拿新的、碰乱那排降一档）

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `juice_bottle` 在 `dining_table_2/top` 上
      - `juice_bottle` 立着
      - `stock_juice_1` 没被挪动（离开局位置不超过 3 cm）
      - `stock_juice_2` 没被挪动（离开局位置不超过 3 cm）
      - `stock_juice_3` 没被挪动（离开局位置不超过 3 cm）
- **次好（0.6）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `stock_juice_1` 在 `dining_table_2/top` 上
      - `stock_juice_1` 立着
    - 第 2 组：
      - `stock_juice_2` 在 `dining_table_2/top` 上
      - `stock_juice_2` 立着
    - 第 3 组：
      - `stock_juice_3` 在 `dining_table_2/top` 上
      - `stock_juice_3` 立着
    - 第 4 组：
      - `juice_bottle` 在 `dining_table_2/top` 上
      - `stock_juice_1` 没被挪动（离开局位置不超过 3 cm）
      - `stock_juice_2` 没被挪动（离开局位置不超过 3 cm）
      - `stock_juice_3` 没被挪动（离开局位置不超过 3 cm）
- **最不好（0.3）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `juice_bottle` 在 `dining_table_2/top` 上
- **不行（0）**：瓶子没回到餐桌；还拿着或掉了


**参考调用顺序**：

- 摆法 `on_tv_stand`：1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=juice_bottle)` → 6. `pick(object=juice_bottle)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[2.948, 7.295])`
- 摆法 `in_bedroom`：1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `search(object=juice_bottle, region=bedroom_0_1)` → 6. `navigate(destination=juice_bottle)` → 7. `pick(object=juice_bottle)` → 8. `navigate(destination=dining_table_2/top)` → 9. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[2.948, 7.295])`

---

## T14_shelve_the_book

> 孩子看完书了，帮他把书收好。

### e1_book_ready（对照）

**情况**：红书在书房书桌上 → 放回他卧室的书架（任一层都算）

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `book_red` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
  - 手里空着
- **次好（0.6）**：

  - `book_red` 在其中任一处上：`bookcase_1/top`、`bookcase_1/shelf_1`、`bookcase_1/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_4/top`、`bookcase_4/shelf_1`、`bookcase_4/shelf_0`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
  - 手里空着
- **不行（0）**：书留在桌上或别处；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=book_red)` → 4. `pick(object=book_red)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=book_red, receptacle=bookcase_2/top)`

### within_kids_reach（Task）

**情况**：“他明天还想自己拿来接着看”：红书那一套放在高书架最上层（原本该放的地方），孩子够不着 → 放到他够得着的低层（0.8 m 以下），不放回原处

**指令**：孩子看完书了，帮他把书收好。他明天还想自己拿来接着看。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **最不好（0.3）**：

  - `book_red` 在其中任一处上：`bookcase_1/top`、`bookcase_1/shelf_1`、`bookcase_1/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_4/top`、`bookcase_4/shelf_1`、`bookcase_4/shelf_0`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
  - 手里空着
- **不行（0）**：书留在桌上、地上或别处；还拿着或掉了


**参考调用顺序**：

- 摆法 `set_on_large_shelf_4`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `explore_room(room=bedroom_0_1)` → 4. `navigate(destination=book_red)` → 5. `pick(object=book_red)` → 6. `navigate(destination=large_shelf_4/shelf_1)` → 7. `place(object=book_red, receptacle=large_shelf_4/shelf_1, hint_xy=[3.7, -5.15])`
- 摆法 `set_on_large_shelf_5`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `explore_room(room=bedroom_0_1)` → 4. `navigate(destination=book_red)` → 5. `pick(object=book_red)` → 6. `navigate(destination=large_shelf_5/shelf_1)` → 7. `place(object=book_red, receptacle=large_shelf_5/shelf_1, hint_xy=[4.45, -0.35])`

### homework_stays（Task）

**情况**：“把书桌收拾一下，东西都放到最合适的地方，作业他明天还要接着写”：书桌上有看完的书、用过的马克杯、摊开的作业本和铅笔 → 书放回书柜（家里任一书柜、任一层都算），杯子拿回厨房（两个厨房台面都算），作业原样不动（过程要求：整局不拿起作业本和铅笔）

**指令**：孩子看完书了，把他的书桌收拾一下，东西都放到最合适的地方。作业他明天还要接着写。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `book_red` 在其中任一处上：`bookcase_1/top`、`bookcase_1/shelf_1`、`bookcase_1/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_4/top`、`bookcase_4/shelf_1`、`bookcase_4/shelf_0`
  - `desk_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`
  - `desk_mug` 立着
  - `homework`、`hw_pencil` 没被挪动（离开局位置不超过 3 cm）
  - 过程要求：整局都没拿起过 `homework`、`hw_pencil`（拆了再搭回去不算）
  - 手里空着
- **次好（0.6）**：

  - `book_red` 在其中任一处上：`bookcase_1/top`、`bookcase_1/shelf_1`、`bookcase_1/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_4/top`、`bookcase_4/shelf_1`、`bookcase_4/shelf_0`
  - `desk_mug` 在其中任一处上：`kitchen_island/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_stove/top`
  - `desk_mug` 立着
  - `homework`、`hw_pencil` 没被挪动（离开局位置不超过 3 cm）
  - 过程要求：整局都没拿起过 `homework`、`hw_pencil`（拆了再搭回去不算）
  - 手里空着
- **最不好（0.3）**：

  - `book_red` 在其中任一处上：`bookcase_1/top`、`bookcase_1/shelf_1`、`bookcase_1/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_4/top`、`bookcase_4/shelf_1`、`bookcase_4/shelf_0`
  - `desk_mug` 在其中任一处上：`kitchen_island/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_stove/top`
  - `desk_mug` 立着
  - 手里空着
- **不行（0）**：书或杯子留在书桌；杯子倒了；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=book_red)` → 4. `pick(object=book_red)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=book_red, receptacle=bookcase_2/top)` → 7. `navigate(destination=desk_mug)` → 8. `pick(object=desk_mug)` → 9. `navigate(destination=kitchen_counter_2/top)` → 10. `place(object=desk_mug, receptacle=kitchen_counter_2/top, hint_xy=[-0.384, 7.609])`

### whose_book（Task）

**情况**：“把书房书桌上的书收好，放到摆着同类书的书架上”：卧室书柜上摆着蓝色精装书，客厅书架上摆着平装书；书桌上有其中一类或两类 → 看每本书是哪一类，放到摆着同类书的那个书架上

**指令**：把书房书桌上的书收好，放到摆着同类书的书架上。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `blue_book`：
    - `blue_book` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
    - `blue_shelved_1`、`blue_shelved_2`、`paperback_shelved_1`、`paperback_shelved_2` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
  - 摆法 `both`：
    - `blue_book` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
    - `paperback` 在其中任一处上：`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`
    - `blue_shelved_1`、`blue_shelved_2`、`paperback_shelved_1`、`paperback_shelved_2` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
  - 摆法 `paperback`：
    - `paperback` 在其中任一处上：`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`
    - `blue_shelved_1`、`blue_shelved_2`、`paperback_shelved_1`、`paperback_shelved_2` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
- **次好（0.6）**：

  - 摆法 `blue_book`：
    - `blue_book` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
    - 手里空着
  - 摆法 `both`：
    - `blue_book` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
    - `paperback` 在其中任一处上：`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`
    - 手里空着
  - 摆法 `paperback`：
    - `paperback` 在其中任一处上：`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`
    - 手里空着
- **最不好（0.3）**：

  - 摆法 `blue_book`：
    - `blue_book` 在其中任一处上：`bookcase_1/top`、`bookcase_1/shelf_1`、`bookcase_1/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_4/top`、`bookcase_4/shelf_1`、`bookcase_4/shelf_0`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
    - 手里空着
  - 摆法 `both`：
    - `blue_book` 在其中任一处上：`bookcase_1/top`、`bookcase_1/shelf_1`、`bookcase_1/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_4/top`、`bookcase_4/shelf_1`、`bookcase_4/shelf_0`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
    - `paperback` 在其中任一处上：`bookcase_1/top`、`bookcase_1/shelf_1`、`bookcase_1/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_4/top`、`bookcase_4/shelf_1`、`bookcase_4/shelf_0`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
    - 手里空着
  - 摆法 `paperback`：
    - `paperback` 在其中任一处上：`bookcase_1/top`、`bookcase_1/shelf_1`、`bookcase_1/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_4/top`、`bookcase_4/shelf_1`、`bookcase_4/shelf_0`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
    - 手里空着
- **不行（0）**：有书留在桌上或别处；还拿着或掉了


**参考调用顺序**：

- 摆法 `blue_book`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=blue_book)` → 4. `pick(object=blue_book)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=blue_book, receptacle=bookcase_2/top, hint_xy=[1.0, -0.5])`
- 摆法 `paperback`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=paperback)` → 4. `pick(object=paperback)` → 5. `navigate(destination=large_shelf_2/shelf_2)` → 6. `place(object=paperback, receptacle=large_shelf_2/shelf_2, hint_xy=[-1.86, -0.95])`
- 摆法 `both`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=blue_book)` → 4. `pick(object=blue_book)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=blue_book, receptacle=bookcase_2/top, hint_xy=[1.0, -0.5])` → 7. `navigate(destination=paperback)` → 8. `pick(object=paperback)` → 9. `navigate(destination=large_shelf_2/shelf_2)` → 10. `place(object=paperback, receptacle=large_shelf_2/shelf_2, hint_xy=[-1.86, -0.95])`

### next_in_series（Task）

**情况**：“红书收回书架，再把同一套的另一本拿到书桌上”：另一本红封面的书混在别的书里 → 两个方向的子目标；按封面认出同一套，找遍书架

**指令**：孩子看完这本红书了，收回他的书架，再把同一套的另一本拿到书桌上，他明天看。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `book_red` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
  - `red_book_2` 在 `desk_1/top` 上
  - `blue_book_case`、`paperback_shelf` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- **次好（0.6）**：

  - `red_book_2` 在 `desk_1/top` 上
  - 手里空着
  - `book_red` 在其中任一处上：`bookcase_1/top`、`bookcase_1/shelf_1`、`bookcase_1/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_4/top`、`bookcase_4/shelf_1`、`bookcase_4/shelf_0`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
- **最不好（0.3）**：

  - `book_red` 在其中任一处上：`bookcase_1/top`、`bookcase_1/shelf_1`、`bookcase_1/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_4/top`、`bookcase_4/shelf_1`、`bookcase_4/shelf_0`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `blue_book_case` 在 `desk_1/top` 上
    - 第 2 组：
      - `green_book_case` 在 `desk_1/top` 上
    - 第 3 组：
      - `paperback_shelf` 在 `desk_1/top` 上
- **不行（0）**：书桌上没有书；红书没收；还拿着或掉了


**参考调用顺序**：

- 摆法 `on_bookcase`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=book_red)` → 4. `pick(object=book_red)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=book_red, receptacle=bookcase_2/top, hint_xy=[1.0, -0.55])` → 7. `look(target=bookcase_2/top)` → 8. `navigate(destination=red_book_2)` → 9. `pick(object=red_book_2)` → 10. `navigate(destination=desk_1/top)` → 11. `place(object=red_book_2, receptacle=desk_1/top, hint_xy=[-0.808, -6.166])`
- 摆法 `on_other_bookcase`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=book_red)` → 4. `pick(object=book_red)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=book_red, receptacle=bookcase_2/top, hint_xy=[1.0, -0.55])` → 7. `look(target=bookcase_2/top)` → 8. `search(object=red_book_2, region=bedroom_0_1)` → 9. `look(target=bookcase_3/top)` → 10. `navigate(destination=red_book_2)` → 11. `pick(object=red_book_2)` → 12. `navigate(destination=desk_1/top)` → 13. `place(object=red_book_2, receptacle=desk_1/top, hint_xy=[-0.808, -6.166])`
- 摆法 `on_tall_shelf`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=book_red)` → 4. `pick(object=book_red)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=book_red, receptacle=bookcase_2/top, hint_xy=[1.0, -0.55])` → 7. `look(target=bookcase_2/top)` → 8. `search(object=red_book_2, region=bedroom_0_1)` → 9. `look(target=large_shelf_4/shelf_1)` → 10. `navigate(destination=red_book_2)` → 11. `pick(object=red_book_2)` → 12. `navigate(destination=desk_1/top)` → 13. `place(object=red_book_2, receptacle=desk_1/top, hint_xy=[-0.808, -6.166])`

---

## T21_bring_tissues

> 餐桌上洒了点汤，拿点擦的东西过去。

### tissue_on_tv_stand（对照）

**情况**：纸巾盒在电视柜，餐桌上有碗汤 → 拿到餐桌

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `tissue` 在 `dining_table_2/top` 上
  - 手里空着
- **不行（0）**：没拿到餐桌；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=tissue)` → 4. `pick(object=tissue)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[2.908, 6.655])`

### which_table（Task）

**情况**：两张餐桌，一张上有人在吃饭（汤碗），另一张空着 → 送到吃饭的那张

**成功条件**（D 按摆法：`east` D = 1、理想物在，`west` D = 1、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `west`：
    - `tissue` 在 `dining_table_1/top` 上
    - 手里空着
  - 摆法 `east`：
    - `tissue` 在 `dining_table_2/top` 上
    - 手里空着
- **不行（0）**：拿到另一张空桌；还拿着或掉了


**参考调用顺序**：

- 摆法 `east`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=tissue)` → 4. `pick(object=tissue)` → 5. `navigate(destination=dining_table_1/top)` → 6. `look(target=dining_table_1/top)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[2.908, 6.655])`
- 摆法 `west`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=tissue)` → 4. `pick(object=tissue)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `navigate(destination=dining_table_1/top)` → 8. `place(object=tissue, receptacle=dining_table_1/top, hint_xy=[-7.621, 7.409])`

### no_tissue（Task）

**情况**：家里没有纸巾，岛台上有块干海绵 → 拿海绵代替

**指令**：餐桌上洒了点汤，拿个能擦的用具过去。

**成功条件**（D 按摆法：`no_tissue` D = 0、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `spare_sponge` 在 `dining_table_2/top` 上
  - 手里空着
- **不行（0）**：什么都没拿；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=spare_sponge)` → 6. `pick(object=spare_sponge)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=spare_sponge, receptacle=dining_table_2/top, hint_xy=[2.928, 6.655])`

### the_kids_side（Task）

**情况**：“孩子吃饭把汤洒了，拿点擦的东西过去，放在孩子那一边”：桌上一份有塑料杯（孩子的），一份有马克杯（大人的） → 放到孩子那份旁边

**指令**：孩子吃饭把汤洒了，拿点擦的东西过去，放在孩子那一边。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `tissue` 在 `dining_table_2/top` 上
  - `tissue` 离其中至少一个不超过 15 cm：`kid_bowl`、`kid_cup`
  - `tissue` 离这些都超过 25 cm：`adult_bowl`、`adult_mug`
  - 手里空着
- **次好（0.6）**：

  - `tissue` 在 `dining_table_2/top` 上
  - `tissue` 离这些都超过 25 cm：`adult_bowl`、`adult_mug`
  - 手里空着
- **最不好（0.3）**：

  - `tissue` 在 `dining_table_2/top` 上
  - 手里空着
- **不行（0）**：没放到桌上；还拿着或掉了


**参考调用顺序**：

- 摆法 `kid_north`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=tissue)` → 4. `pick(object=tissue)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[3.708, 7.355])`
- 摆法 `kid_south`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=tissue)` → 4. `pick(object=tissue)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[3.708, 6.495])`

---

## T22_put_away_shopping

> 我刚买东西回来，放在餐桌上了，帮我收好。

### juice_on_table（对照）

**情况**：餐桌上一瓶果汁 → 放进冰箱，关门

**成功条件**（D 按摆法：`juice_on_table` D = 0、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
  - `bought_juice` 立着
  - `breakfast_fridge` 关着
  - `kitchen_cabinet_4` 关着
  - `kitchen_cabinet_6` 关着
  - 手里空着
- **次好（0.6）**：

  - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
  - `bought_juice` 立着
  - 手里空着
- **不行（0）**：没收；躺着；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.9, 3.12])` → 9. `close(articulated=breakfast_fridge)`

### by_kind（Task）

**情况**：果汁、苹果、零食盒 → 果汁进冰箱；苹果和零食放进岛台上的果篮或矮柜里都算（参考路线：苹果进果篮，零食进已有一盒零食的矮柜），柜门关好

**指令**：我刚买东西回来，果汁、苹果和零食都在餐桌上。每样都收到平时放同类东西的地方，开过的门记得关上。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
  - `bought_juice` 立着
  - `breakfast_fridge` 关着
  - `kitchen_cabinet_4` 关着
  - `kitchen_cabinet_6` 关着
  - `kitchen_cabinet_6` 关着
  - `kitchen_cabinet_4` 关着
  - 手里空着
  - `bought_apple` 在 `home_basket` 里
  - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
- **次好（0.6）**：

  - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
  - `bought_juice` 立着
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `bought_apple` 在 `home_basket` 里
      - `bought_snack` 在 `home_basket` 里
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 2 组：
      - `bought_apple` 在 `home_basket` 里
      - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 3 组：
      - `bought_apple` 在 `home_basket` 里
      - `bought_snack` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 4 组：
      - `bought_apple` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `bought_snack` 在 `home_basket` 里
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 5 组：
      - `bought_apple` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 6 组：
      - `bought_apple` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 7 组：
      - `bought_apple` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `bought_snack` 在 `home_basket` 里
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 8 组：
      - `bought_apple` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 9 组：
      - `bought_apple` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 10 组：
      - `bought_apple` 在 `home_basket` 里
      - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
- **最不好（0.3）**：

  - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
  - `bought_juice` 立着
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `bought_apple` 在 `home_basket` 里
      - `bought_snack` 在 `home_basket` 里
    - 第 2 组：
      - `bought_apple` 在 `home_basket` 里
      - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
    - 第 3 组：
      - `bought_apple` 在 `home_basket` 里
      - `bought_snack` 在 `kitchen_cabinet_4/inside_shelf` 上
    - 第 4 组：
      - `bought_apple` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `bought_snack` 在 `home_basket` 里
    - 第 5 组：
      - `bought_apple` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
    - 第 6 组：
      - `bought_apple` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_4/inside_shelf` 上
    - 第 7 组：
      - `bought_apple` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `bought_snack` 在 `home_basket` 里
    - 第 8 组：
      - `bought_apple` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
    - 第 9 组：
      - `bought_apple` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_4/inside_shelf` 上
- **不行（0）**：有东西没收；果汁躺着；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.9, 3.12])` → 9. `close(articulated=breakfast_fridge)` → 10. `navigate(destination=bought_apple)` → 11. `pick(object=bought_apple)` → 12. `navigate(destination=kitchen_island/top)` → 13. `look(target=kitchen_island/top)` → 14. `navigate(destination=home_basket)` → 15. `place(object=bought_apple, receptacle=home_basket)` → 16. `navigate(destination=kitchen_cabinet_6)` → 17. `open(articulated=kitchen_cabinet_6)` → 18. `inspect(receptacle=kitchen_cabinet_6)` → 19. `navigate(destination=bought_snack)` → 20. `pick(object=bought_snack)` → 21. `navigate(destination=kitchen_cabinet_6)` → 22. `place(object=bought_snack, receptacle=kitchen_cabinet_6/inside_shelf, hint_xy=[3.6, 0.36])` → 23. `close(articulated=kitchen_cabinet_6)`

### eat_now（Task）

**情况**：“孩子说零食现在就要吃，他在书房写作业” → 零食送到书桌，果汁收好；按零食放在哪打分（替换的是安放的位置）：书桌上不碰作业算好；书桌被作业摊满、只剩前排东头一角时，放进那一角算好（挪开作业腾地方降一档；压在作业上或收回厨房最不好）

**指令**：我刚买东西回来，放在餐桌上了，帮我收好。孩子说零食现在就要吃，他在书房写作业。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `desk_corner`：
    - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
    - `bought_juice` 立着
    - `breakfast_fridge` 关着
    - `kitchen_cabinet_4` 关着
    - `kitchen_cabinet_6` 关着
    - `bought_snack` 在 `desk_1/top` 上
    - `bought_snack` 离这些东西都至少 0 cm：`homework`、`hw_book_green_1`、`hw_book_green_2`、`hw_book_green_3`、`hw_book_green_4`、`hw_book_green_5`、`hw_book_green_6`、`hw_book_red`、`hw_book_red_2`、`hw_notebook_1`、`hw_notebook_2`、`hw_notebook_3`、`hw_notebook_4`、`hw_notebook_5`、`hw_notebook_6`、`hw_notebook_7`、`hw_paperback`、`hw_pen`、`hw_pencil`
    - `homework`、`hw_book_green_1`、`hw_book_green_2`、`hw_book_green_3`、`hw_book_green_4`、`hw_book_green_5`、`hw_book_green_6`、`hw_book_red`、`hw_book_red_2`、`hw_notebook_1`、`hw_notebook_2`、`hw_notebook_3`、`hw_notebook_4`、`hw_notebook_5`、`hw_notebook_6`、`hw_notebook_7`、`hw_paperback`、`hw_pen`、`hw_pencil` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
  - 摆法 `desk_free`：
    - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
    - `bought_juice` 立着
    - `breakfast_fridge` 关着
    - `kitchen_cabinet_4` 关着
    - `kitchen_cabinet_6` 关着
    - `bought_snack` 在 `desk_1/top` 上
    - 手里空着
- **次好（0.6）**：

  - 摆法 `desk_free`：
    - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
    - `bought_juice` 立着
    - `bought_snack` 在 `desk_1/top` 上
    - 手里空着
  - 摆法 `desk_corner`：
    - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
    - `bought_juice` 立着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `breakfast_fridge` 关着
        - `kitchen_cabinet_4` 关着
        - `kitchen_cabinet_6` 关着
        - `bought_snack` 在 `desk_1/top` 上
        - `bought_snack` 离这些东西都至少 0 cm：`homework`、`hw_book_green_1`、`hw_book_green_2`、`hw_book_green_3`、`hw_book_green_4`、`hw_book_green_5`、`hw_book_green_6`、`hw_book_red`、`hw_book_red_2`、`hw_notebook_1`、`hw_notebook_2`、`hw_notebook_3`、`hw_notebook_4`、`hw_notebook_5`、`hw_notebook_6`、`hw_notebook_7`、`hw_paperback`、`hw_pen`、`hw_pencil`
      - 第 2 组：
        - `bought_snack` 在 `desk_1/top` 上
        - `bought_snack` 离这些东西都至少 0 cm：`homework`、`hw_book_green_1`、`hw_book_green_2`、`hw_book_green_3`、`hw_book_green_4`、`hw_book_green_5`、`hw_book_green_6`、`hw_book_red`、`hw_book_red_2`、`hw_notebook_1`、`hw_notebook_2`、`hw_notebook_3`、`hw_notebook_4`、`hw_notebook_5`、`hw_notebook_6`、`hw_notebook_7`、`hw_paperback`、`hw_pen`、`hw_pencil`
        - `homework` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_1` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_2` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_3` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_4` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_5` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_6` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_red` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_red_2` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_1` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_2` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_3` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_4` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_5` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_6` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_7` 没被挪动（离开局位置不超过 3 cm）
        - `hw_paperback` 没被挪动（离开局位置不超过 3 cm）
        - `hw_pen` 没被挪动（离开局位置不超过 3 cm）
        - `hw_pencil` 没被挪动（离开局位置不超过 3 cm）
- **最不好（0.3）**：

  - 摆法 `desk_free`：
    - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
    - `bought_juice` 立着
    - `bought_snack` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_island/top`
    - 手里空着
  - 摆法 `desk_corner`：
    - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
    - `bought_juice` 立着
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `bought_snack` 在 `desk_1/top` 上
      - 第 2 组：
        - `bought_snack` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`、`kitchen_island/top`
- **不行（0）**：零食留在餐桌上；果汁没收或躺着；还拿着或掉了


**参考调用顺序**：

- 摆法 `desk_free`：1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.9, 3.12])` → 9. `close(articulated=breakfast_fridge)` → 10. `navigate(destination=bought_snack)` → 11. `pick(object=bought_snack)` → 12. `navigate(destination=desk_1/top)` → 13. `place(object=bought_snack, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`
- 摆法 `desk_corner`：1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.9, 3.12])` → 9. `close(articulated=breakfast_fridge)` → 10. `navigate(destination=desk_1/top)` → 11. `look(target=desk_1/top)` → 12. `navigate(destination=bought_snack)` → 13. `pick(object=bought_snack)` → 14. `navigate(destination=desk_1/top)` → 15. `place(object=bought_snack, receptacle=desk_1/top, hint_xy=[-0.14, -6.22])`

### not_shopping（Task）

**情况**：桌上还有孩子的小车和绘本 → 不是买的，不动

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
  - `bought_juice` 立着
  - `breakfast_fridge` 关着
  - `kitchen_cabinet_4` 关着
  - `kitchen_cabinet_6` 关着
  - `table_car`、`table_book` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- **次好（0.6）**：

  - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
  - `bought_juice` 立着
  - `table_car`、`table_book` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- **最不好（0.3）**：

  - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
  - `bought_juice` 立着
  - 手里空着
- **不行（0）**：果汁没收；躺着；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.9, 3.12])` → 9. `close(articulated=breakfast_fridge)`

### two_spots（Task）

**情况**：买的东西分在餐桌和岛台两处 → 都找到；果汁进冰箱，苹果和零食放进果篮或矮柜都算，柜门关好

**指令**：我刚买东西回来，两袋东西拆开放在了两个不同的地方，买的东西都帮我收好。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
  - `bought_juice` 立着
  - `breakfast_fridge` 关着
  - `kitchen_cabinet_4` 关着
  - `kitchen_cabinet_6` 关着
  - `kitchen_cabinet_6` 关着
  - `kitchen_cabinet_4` 关着
  - 手里空着
  - `bought_apple` 在 `home_basket` 里
  - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
- **次好（0.6）**：

  - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
  - `bought_juice` 立着
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `bought_apple` 在 `home_basket` 里
      - `bought_snack` 在 `home_basket` 里
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 2 组：
      - `bought_apple` 在 `home_basket` 里
      - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 3 组：
      - `bought_apple` 在 `home_basket` 里
      - `bought_snack` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 4 组：
      - `bought_apple` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `bought_snack` 在 `home_basket` 里
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 5 组：
      - `bought_apple` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 6 组：
      - `bought_apple` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 7 组：
      - `bought_apple` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `bought_snack` 在 `home_basket` 里
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 8 组：
      - `bought_apple` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 9 组：
      - `bought_apple` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `breakfast_fridge` 关着
      - `kitchen_cabinet_4` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_6` 关着
      - `kitchen_cabinet_4` 关着
    - 第 10 组：
      - `bought_apple` 在 `home_basket` 里
      - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
- **最不好（0.3）**：

  - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
  - `bought_juice` 立着
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `bought_apple` 在 `home_basket` 里
      - `bought_snack` 在 `home_basket` 里
    - 第 2 组：
      - `bought_apple` 在 `home_basket` 里
      - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
    - 第 3 组：
      - `bought_apple` 在 `home_basket` 里
      - `bought_snack` 在 `kitchen_cabinet_4/inside_shelf` 上
    - 第 4 组：
      - `bought_apple` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `bought_snack` 在 `home_basket` 里
    - 第 5 组：
      - `bought_apple` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
    - 第 6 组：
      - `bought_apple` 在 `kitchen_cabinet_6/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_4/inside_shelf` 上
    - 第 7 组：
      - `bought_apple` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `bought_snack` 在 `home_basket` 里
    - 第 8 组：
      - `bought_apple` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_6/inside_shelf` 上
    - 第 9 组：
      - `bought_apple` 在 `kitchen_cabinet_4/inside_shelf` 上
      - `bought_snack` 在 `kitchen_cabinet_4/inside_shelf` 上
- **不行（0）**：有东西没收；果汁躺着；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.9, 3.12])` → 9. `close(articulated=breakfast_fridge)` → 10. `navigate(destination=kitchen_island/top)` → 11. `look(target=kitchen_island/top)` → 12. `navigate(destination=bought_apple)` → 13. `pick(object=bought_apple)` → 14. `navigate(destination=home_basket)` → 15. `place(object=bought_apple, receptacle=home_basket)` → 16. `navigate(destination=kitchen_cabinet_6)` → 17. `open(articulated=kitchen_cabinet_6)` → 18. `inspect(receptacle=kitchen_cabinet_6)` → 19. `navigate(destination=bought_snack)` → 20. `pick(object=bought_snack)` → 21. `navigate(destination=kitchen_cabinet_6)` → 22. `place(object=bought_snack, receptacle=kitchen_cabinet_6/inside_shelf, hint_xy=[3.45, 0.42])` → 23. `close(articulated=kitchen_cabinet_6)`

### tray_elsewhere（Action + Task）

**情况**：果汁和苹果在餐桌上，果篮不在；有的摆法岛台上就有托盘（直接用）；其余摆法西边餐厅的桌上有个托盘，到了才看得到上面是什么：一个橙子，或者四本书平铺占满了托盘 → 果篮没有 → 找别的能装水果的（另一个房间的托盘）→ 有橙子：苹果直接放进去（水果可以放一起，不用挪）；被书占满：先把书放回那个房间的书架（任何书架都算），再放苹果；果汁进冰箱。挪书属于“目的地被占”（A），去别的房间找替代容器是独立的 Task 要求，所以是 A+T

**指令**：我刚买东西回来，果汁和苹果放在餐桌上了，帮我收好。水果平时放在果篮里。

**成功条件**（D 按摆法：`orange_in_it` D = 0、理想物不在，`books_on_it` D = 0、理想物不在，`basket_missing` D = 0、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `orange_in_it`：
    - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
    - `bought_juice` 立着
    - `breakfast_fridge` 关着
    - `kitchen_cabinet_4` 关着
    - `kitchen_cabinet_6` 关着
    - `bought_apple` 完全在 `west_tray` 里（没有露出边沿）
    - `west_tray` 不在地上
    - 手里空着
  - 摆法 `books_on_it`：
    - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
    - `bought_juice` 立着
    - `breakfast_fridge` 关着
    - `kitchen_cabinet_4` 关着
    - `kitchen_cabinet_6` 关着
    - `bought_apple` 完全在 `west_tray` 里（没有露出边沿）
    - `west_tray` 不在地上
    - `tray_book_1` 在其中任一处上：`bookcase_1/shelf_0`、`bookcase_1/shelf_1`、`bookcase_1/top`、`bookcase_2/shelf_0`、`bookcase_2/shelf_1`、`bookcase_2/top`、`bookcase_3/shelf_0`、`bookcase_3/shelf_1`、`bookcase_3/top`、`bookcase_4/shelf_0`、`bookcase_4/shelf_1`、`bookcase_4/top`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
    - `tray_book_2` 在其中任一处上：`bookcase_1/shelf_0`、`bookcase_1/shelf_1`、`bookcase_1/top`、`bookcase_2/shelf_0`、`bookcase_2/shelf_1`、`bookcase_2/top`、`bookcase_3/shelf_0`、`bookcase_3/shelf_1`、`bookcase_3/top`、`bookcase_4/shelf_0`、`bookcase_4/shelf_1`、`bookcase_4/top`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
    - `tray_book_3` 在其中任一处上：`bookcase_1/shelf_0`、`bookcase_1/shelf_1`、`bookcase_1/top`、`bookcase_2/shelf_0`、`bookcase_2/shelf_1`、`bookcase_2/top`、`bookcase_3/shelf_0`、`bookcase_3/shelf_1`、`bookcase_3/top`、`bookcase_4/shelf_0`、`bookcase_4/shelf_1`、`bookcase_4/top`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
    - `tray_book_4` 在其中任一处上：`bookcase_1/shelf_0`、`bookcase_1/shelf_1`、`bookcase_1/top`、`bookcase_2/shelf_0`、`bookcase_2/shelf_1`、`bookcase_2/top`、`bookcase_3/shelf_0`、`bookcase_3/shelf_1`、`bookcase_3/top`、`bookcase_4/shelf_0`、`bookcase_4/shelf_1`、`bookcase_4/top`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
    - 手里空着
  - 摆法 `basket_missing`：
    - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
    - `bought_juice` 立着
    - `breakfast_fridge` 关着
    - `kitchen_cabinet_4` 关着
    - `kitchen_cabinet_6` 关着
    - `bought_apple` 在 `fruit_tray` 里
    - 手里空着
- **次好（0.6）**：

  - 摆法 `orange_in_it`：
    - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
    - `bought_juice` 立着
    - `bought_apple` 完全在 `west_tray` 里（没有露出边沿）
    - `west_tray` 不在地上
    - 手里空着
  - 摆法 `books_on_it`：
    - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
    - `bought_juice` 立着
    - `bought_apple` 完全在 `west_tray` 里（没有露出边沿）
    - `west_tray` 不在地上
    - `tray_book_1` 在其中任一处上：`bookcase_1/shelf_0`、`bookcase_1/shelf_1`、`bookcase_1/top`、`bookcase_2/shelf_0`、`bookcase_2/shelf_1`、`bookcase_2/top`、`bookcase_3/shelf_0`、`bookcase_3/shelf_1`、`bookcase_3/top`、`bookcase_4/shelf_0`、`bookcase_4/shelf_1`、`bookcase_4/top`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
    - `tray_book_2` 在其中任一处上：`bookcase_1/shelf_0`、`bookcase_1/shelf_1`、`bookcase_1/top`、`bookcase_2/shelf_0`、`bookcase_2/shelf_1`、`bookcase_2/top`、`bookcase_3/shelf_0`、`bookcase_3/shelf_1`、`bookcase_3/top`、`bookcase_4/shelf_0`、`bookcase_4/shelf_1`、`bookcase_4/top`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
    - `tray_book_3` 在其中任一处上：`bookcase_1/shelf_0`、`bookcase_1/shelf_1`、`bookcase_1/top`、`bookcase_2/shelf_0`、`bookcase_2/shelf_1`、`bookcase_2/top`、`bookcase_3/shelf_0`、`bookcase_3/shelf_1`、`bookcase_3/top`、`bookcase_4/shelf_0`、`bookcase_4/shelf_1`、`bookcase_4/top`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
    - `tray_book_4` 在其中任一处上：`bookcase_1/shelf_0`、`bookcase_1/shelf_1`、`bookcase_1/top`、`bookcase_2/shelf_0`、`bookcase_2/shelf_1`、`bookcase_2/top`、`bookcase_3/shelf_0`、`bookcase_3/shelf_1`、`bookcase_3/top`、`bookcase_4/shelf_0`、`bookcase_4/shelf_1`、`bookcase_4/top`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`
    - 手里空着
  - 摆法 `basket_missing`：
    - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
    - `bought_juice` 立着
    - `bought_apple` 在 `fruit_tray` 里
    - 手里空着
- **最不好（0.3）**：

  - 摆法 `orange_in_it`、`books_on_it`：
    - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
    - `bought_juice` 立着
    - `bought_apple` 完全在 `west_tray` 里（没有露出边沿）
    - `west_tray` 不在地上
    - 手里空着
  - 摆法 `basket_missing`：
    - `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
    - `bought_juice` 立着
    - `bought_apple` 在 `fruit_tray` 里
    - 手里空着
- **不行（0）**：有东西没收；果汁躺着；还拿着或掉了


**参考调用顺序**：

- 摆法 `orange_in_it`：1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.9, 3.12])` → 9. `close(articulated=breakfast_fridge)` → 10. `search(object=west_tray, region=dining_room_0_0)` → 11. `look(target=west_tray)` → 12. `navigate(destination=bought_apple)` → 13. `pick(object=bought_apple)` → 14. `navigate(destination=west_tray)` → 15. `place(object=bought_apple, receptacle=west_tray)`
- 摆法 `books_on_it`：1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.9, 3.12])` → 9. `close(articulated=breakfast_fridge)` → 10. `search(object=west_tray, region=dining_room_0_0)` → 11. `look(target=west_tray)` → 12. `navigate(destination=tray_book_1)` → 13. `pick(object=tray_book_1)` → 14. `navigate(destination=bookcase_1/top)` → 15. `place(object=tray_book_1, receptacle=bookcase_1/top, hint_xy=[-9.569, 6.528])` → 16. `navigate(destination=tray_book_2)` → 17. `pick(object=tray_book_2)` → 18. `navigate(destination=bookcase_1/top)` → 19. `place(object=tray_book_2, receptacle=bookcase_1/top, hint_xy=[-9.59, 6.82])` → 20. `navigate(destination=tray_book_3)` → 21. `pick(object=tray_book_3)` → 22. `navigate(destination=bookcase_1/shelf_1)` → 23. `place(object=tray_book_3, receptacle=bookcase_1/shelf_1, hint_xy=[-9.59, 6.52])` → 24. `navigate(destination=tray_book_4)` → 25. `pick(object=tray_book_4)` → 26. `navigate(destination=bookcase_1/shelf_1)` → 27. `place(object=tray_book_4, receptacle=bookcase_1/shelf_1, hint_xy=[-9.59, 6.82])` → 28. `navigate(destination=bought_apple)` → 29. `pick(object=bought_apple)` → 30. `navigate(destination=west_tray)` → 31. `place(object=bought_apple, receptacle=west_tray)`
- 摆法 `basket_missing`：1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.9, 3.12])` → 9. `close(articulated=breakfast_fridge)` → 10. `navigate(destination=bought_apple)` → 11. `pick(object=bought_apple)` → 12. `navigate(destination=kitchen_island/top)` → 13. `look(target=kitchen_island/top)` → 14. `navigate(destination=fruit_tray)` → 15. `place(object=bought_apple, receptacle=fruit_tray)`

---

## T23_pick_up_dropped

> 地上掉了东西，帮忙捡起来放好。

### spoon_on_floor（对照）

**情况**：厨房地上一把勺子 → 放回厨房台面（勺子都放在那）

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
  - 手里空着
- **不行（0）**：勺子还在地上或放别处；还拿着


**参考调用顺序**：

1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `explore_room(room=kitchen_0_1)` → 4. `navigate(destination=dropped_spoon)` → 5. `look(target=dropped_spoon)` → 6. `pick(object=dropped_spoon)` → 7. `navigate(destination=kitchen_counter_2/top)` → 8. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.364, 9.109])`

### by_kind（Task）

**情况**：地上有勺子和一块积木 → 勺子回台面，积木放到孩子放玩具的地方；他的小玩具盒已经装满积木时，放进旁边空的分拣托盘（最好的替代算好；把盒里的积木拿出来腾地方降一档；积木没跟玩具放一起最不好）

**成功条件**（D 按摆法：`toy_box` D = 1、理想物在，`bin_full` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `bin_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `dropped_block` 在 `spare_tray` 里
        - `bin_block_1` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_2` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_3` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_4` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_5` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_6` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_7` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_8` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_9` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_10` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_11` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_12` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_13` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_14` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_15` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_16` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_17` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_18` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_19` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_20` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_21` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_22` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_23` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_24` 完全在 `toy_bin` 里（没有露出边沿）
  - 摆法 `toy_box`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `dropped_block` 在 `toy_box` 里
- **次好（0.6）**：

  - 摆法 `bin_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `dropped_block` 在 `toy_bin` 里
  - 摆法 `toy_box`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `dropped_block` 不在地上
- **最不好（0.3）**：

  - 摆法 `toy_box`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `bin_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `dropped_block` 不在地上
- **不行（0）**：有东西还在地上；还拿着


**参考调用顺序**：

- 摆法 `toy_box`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `explore_room(room=kitchen_0_1)` → 4. `navigate(destination=dropped_spoon)` → 5. `look(target=dropped_spoon)` → 6. `pick(object=dropped_spoon)` → 7. `navigate(destination=kitchen_counter_2/top)` → 8. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.364, 9.109])` → 9. `navigate(destination=dropped_block)` → 10. `look(target=dropped_block)` → 11. `pick(object=dropped_block)` → 12. `explore_room(room=living_room_0_0)` → 13. `navigate(destination=toy_box)` → 14. `place(object=dropped_block, receptacle=toy_box)`
- 摆法 `bin_full`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `explore_room(room=kitchen_0_1)` → 4. `navigate(destination=dropped_spoon)` → 5. `look(target=dropped_spoon)` → 6. `pick(object=dropped_spoon)` → 7. `navigate(destination=kitchen_counter_2/top)` → 8. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.364, 9.109])` → 9. `navigate(destination=dropped_block)` → 10. `look(target=dropped_block)` → 11. `pick(object=dropped_block)` → 12. `explore_room(room=living_room_0_0)` → 13. `navigate(destination=tv_stand_2/top)` → 14. `look(target=tv_stand_2/top)` → 15. `measure(object=toy_bin)` → 16. `navigate(destination=spare_tray)` → 17. `place(object=dropped_block, receptacle=spare_tray)`

### belongs_on_floor（Task）

**情况**：孩子的积木掉在厨房地上，旁边是垃圾桶和洗衣篮（本来就放地上，不动）→ 积木放进电视柜上的分拣托盘（碰动桶或篮、把盒里积木拿出来腾地方降一档；扔进洗衣篮或把桶、篮拿起来最不好）

**成功条件**（D 按摆法：`no_toy_box` D = 1、理想物不在，`bin_full` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `bin_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_block` 在 `spare_tray` 里
        - `bin_block_1` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_2` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_3` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_4` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_5` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_6` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_7` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_8` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_9` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_10` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_11` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_12` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_13` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_14` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_15` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_16` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_17` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_18` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_19` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_20` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_21` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_22` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_23` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_24` 完全在 `toy_bin` 里（没有露出边沿）
        - `kitchen_bin` 没被挪动（离开局位置不超过 3 cm）
        - `laundry_basket` 没被挪动（离开局位置不超过 3 cm）
        - `["on_floor", "kitchen_bin"]`
        - `["on_floor", "laundry_basket"]`
  - 摆法 `no_toy_box`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_block` 在 `spare_tray` 里
        - `kitchen_bin` 没被挪动（离开局位置不超过 3 cm）
        - `laundry_basket` 没被挪动（离开局位置不超过 3 cm）
        - `["on_floor", "kitchen_bin"]`
        - `["on_floor", "laundry_basket"]`
- **次好（0.6）**：

  - 摆法 `bin_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_block` 在 `spare_tray` 里
        - `bin_block_1` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_2` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_3` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_4` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_5` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_6` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_7` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_8` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_9` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_10` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_11` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_12` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_13` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_14` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_15` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_16` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_17` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_18` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_19` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_20` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_21` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_22` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_23` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_24` 完全在 `toy_bin` 里（没有露出边沿）
        - `["on_floor", "kitchen_bin"]`
        - `["on_floor", "laundry_basket"]`
      - 第 2 组：
        - `dropped_block` 在 `spare_tray` 里
        - `bin_block_1` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_2` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_3` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_4` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_5` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_6` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_7` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_8` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_9` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_10` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_11` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_12` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_13` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_14` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_15` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_16` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_17` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_18` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_19` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_20` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_21` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_22` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_23` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_24` 完全在 `toy_bin` 里（没有露出边沿）
        - `kitchen_bin` 没被挪动（离开局位置不超过 3 cm）
        - `laundry_basket` 没被挪动（离开局位置不超过 3 cm）
      - 第 3 组：
        - `dropped_block` 在 `toy_bin` 里
        - `kitchen_bin` 没被挪动（离开局位置不超过 3 cm）
        - `laundry_basket` 没被挪动（离开局位置不超过 3 cm）
        - `["on_floor", "kitchen_bin"]`
        - `["on_floor", "laundry_basket"]`
  - 摆法 `no_toy_box`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_block` 在 `spare_tray` 里
        - `["on_floor", "kitchen_bin"]`
        - `["on_floor", "laundry_basket"]`
      - 第 2 组：
        - `dropped_block` 在 `spare_tray` 里
        - `kitchen_bin` 没被挪动（离开局位置不超过 3 cm）
        - `laundry_basket` 没被挪动（离开局位置不超过 3 cm）
- **最不好（0.3）**：

  - 摆法 `bin_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_block` 在 `spare_tray` 里
        - `bin_block_1` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_2` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_3` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_4` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_5` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_6` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_7` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_8` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_9` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_10` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_11` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_12` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_13` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_14` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_15` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_16` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_17` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_18` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_19` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_20` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_21` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_22` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_23` 完全在 `toy_bin` 里（没有露出边沿）
        - `bin_block_24` 完全在 `toy_bin` 里（没有露出边沿）
      - 第 2 组：
        - `dropped_block` 在 `toy_bin` 里
        - `["on_floor", "kitchen_bin"]`
        - `["on_floor", "laundry_basket"]`
      - 第 3 组：
        - `dropped_block` 在 `toy_bin` 里
        - `kitchen_bin` 没被挪动（离开局位置不超过 3 cm）
        - `laundry_basket` 没被挪动（离开局位置不超过 3 cm）
      - 第 4 组：
        - `dropped_block` 在 `laundry_basket` 里
        - `kitchen_bin` 没被挪动（离开局位置不超过 3 cm）
        - `laundry_basket` 没被挪动（离开局位置不超过 3 cm）
        - `["on_floor", "kitchen_bin"]`
        - `["on_floor", "laundry_basket"]`
      - 第 5 组：
        - `dropped_block` 在 `toy_bin` 里
      - 第 6 组：
        - `dropped_block` 在 `laundry_basket` 里
        - `["on_floor", "kitchen_bin"]`
        - `["on_floor", "laundry_basket"]`
      - 第 7 组：
        - `dropped_block` 在 `laundry_basket` 里
        - `kitchen_bin` 没被挪动（离开局位置不超过 3 cm）
        - `laundry_basket` 没被挪动（离开局位置不超过 3 cm）
      - 第 8 组：
        - `dropped_block` 在 `laundry_basket` 里
  - 摆法 `no_toy_box`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_block` 在 `spare_tray` 里
      - 第 2 组：
        - `dropped_block` 在 `laundry_basket` 里
        - `kitchen_bin` 没被挪动（离开局位置不超过 3 cm）
        - `laundry_basket` 没被挪动（离开局位置不超过 3 cm）
        - `["on_floor", "kitchen_bin"]`
        - `["on_floor", "laundry_basket"]`
      - 第 3 组：
        - `dropped_block` 在 `laundry_basket` 里
        - `["on_floor", "kitchen_bin"]`
        - `["on_floor", "laundry_basket"]`
      - 第 4 组：
        - `dropped_block` 在 `laundry_basket` 里
        - `kitchen_bin` 没被挪动（离开局位置不超过 3 cm）
        - `laundry_basket` 没被挪动（离开局位置不超过 3 cm）
      - 第 5 组：
        - `dropped_block` 在 `laundry_basket` 里
- **不行（0）**：积木还在地上或没放进容器；还拿着


**参考调用顺序**：

- 摆法 `no_toy_box`：1. `explore_room(room=kitchen_0_1)` → 2. `navigate(destination=dropped_block)` → 3. `look(target=dropped_block)` → 4. `pick(object=dropped_block)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=tv_stand_2/top)` → 7. `look(target=tv_stand_2/top)` → 8. `navigate(destination=spare_tray)` → 9. `place(object=dropped_block, receptacle=spare_tray)`
- 摆法 `bin_full`：1. `explore_room(room=kitchen_0_1)` → 2. `navigate(destination=dropped_block)` → 3. `look(target=dropped_block)` → 4. `pick(object=dropped_block)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=tv_stand_2/top)` → 7. `look(target=tv_stand_2/top)` → 8. `measure(object=toy_bin)` → 9. `navigate(destination=spare_tray)` → 10. `place(object=dropped_block, receptacle=spare_tray)`

### dropped_out_of_view（Task）

**情况**：东西滑到隔壁餐厅地上，看不到 → 先找；小厨房台面被碗盘占满 → 放到岛台或另一个厨房台面（挪开碗盘腾地方降一档；压在碗盘上最不好）

**成功条件**（D 按摆法：`counter_full` D = 1、理想物不在，`no_room_for_bowl` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `no_room_for_bowl`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_bowl` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_island/top`
  - 摆法 `counter_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_spoon` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_island/top`
- **次好（0.6）**：

  - 摆法 `no_room_for_bowl`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_bowl` 在 `kitchen_counter_2/top` 上
        - `dropped_bowl` 离这些东西都至少 0 cm：`counter_bowl_1`、`counter_bowl_10`、`counter_bowl_2`、`counter_bowl_3`、`counter_bowl_4`、`counter_bowl_5`、`counter_bowl_6`、`counter_bowl_7`、`counter_bowl_8`、`counter_bowl_9`、`counter_cup_w2`、`counter_cup_w4`、`counter_cup_w6`、`counter_plate_n1`、`counter_plate_n2`、`counter_plate_n3`、`counter_plate_s1`、`counter_plate_s2`、`counter_plate_s3`、`counter_plate_w1`、`counter_plate_w3`、`counter_plate_w5`、`counter_plate_w7`
  - 摆法 `counter_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_spoon` 在 `kitchen_counter_2/top` 上
        - `dropped_spoon` 离这些东西都至少 0 cm：`counter_bowl_1`、`counter_bowl_10`、`counter_bowl_2`、`counter_bowl_3`、`counter_bowl_4`、`counter_bowl_5`、`counter_bowl_6`、`counter_bowl_7`、`counter_bowl_8`、`counter_bowl_9`、`counter_plate_n1`、`counter_plate_n2`、`counter_plate_n3`、`counter_plate_s1`、`counter_plate_s2`、`counter_plate_s3`、`counter_plate_w1`、`counter_plate_w2`、`counter_plate_w3`、`counter_plate_w4`、`counter_plate_w5`、`counter_plate_w6`、`counter_plate_w7`
- **最不好（0.3）**：

  - 摆法 `no_room_for_bowl`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_bowl` 在 `kitchen_counter_2/top` 上
  - 摆法 `counter_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_spoon` 在 `kitchen_counter_2/top` 上
- **不行（0）**：没找到；还在地上；还拿着或掉了


**参考调用顺序**：

- 摆法 `counter_full`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `explore_room(room=dining_room_0_1)` → 4. `navigate(destination=dropped_spoon)` → 5. `look(target=dropped_spoon)` → 6. `pick(object=dropped_spoon)` → 7. `navigate(destination=kitchen_island/top)` → 8. `place(object=dropped_spoon, receptacle=kitchen_island/top, hint_xy=[7.4, 1.62])`
- 摆法 `no_room_for_bowl`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `explore_room(room=dining_room_0_1)` → 4. `navigate(destination=dropped_bowl)` → 5. `look(target=dropped_bowl)` → 6. `pick(object=dropped_bowl)` → 7. `navigate(destination=kitchen_island/top)` → 8. `place(object=dropped_bowl, receptacle=kitchen_island/top, hint_xy=[7.4, 1.675])`

### only_this_room（Task）

**情况**：“厨房地上掉了东西”：孩子的塑料杯掉在厨房地上，客厅地上还有小车（不是厨房的，不动）→ 杯子放回他放杯子的矮柜 4，柜门关好；矮柜 4 被两口锅和他的三个杯子占满时，放到另一个矮柜或台面（门没关、柜子有空却放别处、硬塞降一档；把客厅小车也收了最不好）

**指令**：厨房地上掉了东西，帮忙捡起来放好。

**成功条件**（D 按摆法：`cabinet_room` D = 1、理想物在，`cabinet_full` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `cabinet_room`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_cup` 在 `kitchen_cabinet_4/top` 上
        - `kitchen_cabinet_4` 关着
        - `kitchen_cabinet_6` 关着
        - `living_car` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `cabinet_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_cup` 在其中任一处上：`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_cabinet_6/top`
        - `kitchen_cabinet_4` 关着
        - `kitchen_cabinet_6` 关着
        - `living_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `dropped_cup` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `kitchen_cabinet_4` 关着
        - `kitchen_cabinet_6` 关着
        - `living_car` 没被挪动（离开局位置不超过 3 cm）
- **次好（0.6）**：

  - 摆法 `cabinet_room`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_cup` 在 `kitchen_cabinet_4/top` 上
        - `living_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `dropped_cup` 在其中任一处上：`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_cabinet_6/top`
        - `kitchen_cabinet_4` 关着
        - `kitchen_cabinet_6` 关着
        - `living_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 3 组：
        - `dropped_cup` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `kitchen_cabinet_4` 关着
        - `kitchen_cabinet_6` 关着
        - `living_car` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `cabinet_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_cup` 在其中任一处上：`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_cabinet_6/top`
        - `living_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `dropped_cup` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `living_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 3 组：
        - `dropped_cup` 在 `kitchen_cabinet_4/top` 上
        - `dropped_cup` 不在 `stored_pot_1` 里
        - `dropped_cup` 不在 `stored_pot_2` 里
        - `kitchen_cabinet_4` 关着
        - `kitchen_cabinet_6` 关着
        - `living_car` 没被挪动（离开局位置不超过 3 cm）
- **最不好（0.3）**：

  - 摆法 `cabinet_room`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_cup` 在 `kitchen_cabinet_4/top` 上
        - `kitchen_cabinet_4` 关着
        - `kitchen_cabinet_6` 关着
      - 第 2 组：
        - `dropped_cup` 在其中任一处上：`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_cabinet_6/top`
        - `living_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 3 组：
        - `dropped_cup` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `living_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 4 组：
        - `dropped_cup` 在 `kitchen_cabinet_4/top` 上
      - 第 5 组：
        - `dropped_cup` 在其中任一处上：`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_cabinet_6/top`
        - `kitchen_cabinet_4` 关着
        - `kitchen_cabinet_6` 关着
      - 第 6 组：
        - `dropped_cup` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `kitchen_cabinet_4` 关着
        - `kitchen_cabinet_6` 关着
      - 第 7 组：
        - `dropped_cup` 在其中任一处上：`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_cabinet_6/top`
      - 第 8 组：
        - `dropped_cup` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
  - 摆法 `cabinet_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_cup` 在其中任一处上：`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_cabinet_6/top`
        - `kitchen_cabinet_4` 关着
        - `kitchen_cabinet_6` 关着
      - 第 2 组：
        - `dropped_cup` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `kitchen_cabinet_4` 关着
        - `kitchen_cabinet_6` 关着
      - 第 3 组：
        - `dropped_cup` 在 `kitchen_cabinet_4/top` 上
        - `dropped_cup` 不在 `stored_pot_1` 里
        - `dropped_cup` 不在 `stored_pot_2` 里
        - `living_car` 没被挪动（离开局位置不超过 3 cm）
      - 第 4 组：
        - `dropped_cup` 在其中任一处上：`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_cabinet_6/top`
      - 第 5 组：
        - `dropped_cup` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
      - 第 6 组：
        - `dropped_cup` 在 `kitchen_cabinet_4/top` 上
        - `dropped_cup` 不在 `stored_pot_1` 里
        - `dropped_cup` 不在 `stored_pot_2` 里
        - `kitchen_cabinet_4` 关着
        - `kitchen_cabinet_6` 关着
      - 第 7 组：
        - `dropped_cup` 在 `kitchen_cabinet_4/top` 上
        - `dropped_cup` 不在 `stored_pot_1` 里
        - `dropped_cup` 不在 `stored_pot_2` 里
- **不行（0）**：杯子还在地上或放到厨房以外；还拿着


**参考调用顺序**：

- 摆法 `cabinet_room`：1. `explore_room(room=kitchen_0_1)` → 2. `navigate(destination=dropped_cup)` → 3. `look(target=dropped_cup)` → 4. `pick(object=dropped_cup)` → 5. `navigate(destination=kitchen_cabinet_4/top)` → 6. `look(target=kitchen_cabinet_4/top)` → 7. `place(object=dropped_cup, receptacle=kitchen_cabinet_4/top, hint_xy=[1.45, 0.42])`
- 摆法 `cabinet_full`：1. `explore_room(room=kitchen_0_1)` → 2. `navigate(destination=dropped_cup)` → 3. `look(target=dropped_cup)` → 4. `pick(object=dropped_cup)` → 5. `navigate(destination=kitchen_cabinet_4/top)` → 6. `look(target=kitchen_cabinet_4/top)` → 7. `navigate(destination=kitchen_counter_2/top)` → 8. `place(object=dropped_cup, receptacle=kitchen_counter_2/top, hint_xy=[-0.364, 9.109])`

### dropped_in_two_rooms（Task）

**情况**：“家里地上掉了些东西”：厨房一把勺子，书房地上孩子的一本书 → 都找到，勺子回厨房台面，书放回他卧室的书架；书架每层都摞满了书时，放到别的书架或书桌（书架有空却放别处、挤进满的书架降一档；放到餐桌、厨房最不好）

**指令**：家里地上掉了些东西，帮忙捡起来放好。

**成功条件**（D 按摆法：`shelf_room` D = 1、理想物在，`shelf_full` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `shelf_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `dropped_bear` 在其中任一处上：`bookcase_1/shelf_0`、`bookcase_1/shelf_1`、`bookcase_1/top`、`bookcase_3/shelf_0`、`bookcase_3/shelf_1`、`bookcase_3/top`、`bookcase_4/shelf_0`、`bookcase_4/shelf_1`、`bookcase_4/top`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`、`desk_1/top`、`desk_3/top`、`mattress_1/top`
        - `kid_book_shelf_0_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_4b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_4b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_4b` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `shelf_room`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `dropped_bear` 在其中任一处上：`bookcase_2/shelf_0`、`bookcase_2/shelf_1`、`bookcase_2/top`、`mattress_1/top`
- **次好（0.6）**：

  - 摆法 `shelf_room`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `dropped_bear` 在其中任一处上：`bookcase_1/shelf_0`、`bookcase_1/shelf_1`、`bookcase_1/top`、`bookcase_3/shelf_0`、`bookcase_3/shelf_1`、`bookcase_3/top`、`bookcase_4/shelf_0`、`bookcase_4/shelf_1`、`bookcase_4/top`、`large_shelf_1/shelf_0`、`large_shelf_1/shelf_1`、`large_shelf_1/shelf_2`、`large_shelf_1/shelf_3`、`large_shelf_1/shelf_4`、`large_shelf_2/shelf_0`、`large_shelf_2/shelf_1`、`large_shelf_2/shelf_2`、`large_shelf_2/shelf_3`、`large_shelf_3/shelf_0`、`large_shelf_3/shelf_1`、`large_shelf_3/shelf_2`、`large_shelf_3/shelf_3`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`、`large_shelf_6/shelf_0`、`large_shelf_6/shelf_1`、`large_shelf_6/shelf_2`、`large_shelf_6/shelf_3`、`large_shelf_6/top`、`desk_1/top`、`desk_3/top`
  - 摆法 `shelf_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
        - `dropped_bear` 在其中任一处上：`bookcase_2/shelf_0`、`bookcase_2/shelf_1`、`bookcase_2/top`
- **最不好（0.3）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
      - `dropped_bear` 不在地上
- **不行（0）**：有一样还在地上；还拿着


**参考调用顺序**：

- 摆法 `shelf_room`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `explore_room(room=kitchen_0_1)` → 4. `navigate(destination=dropped_spoon)` → 5. `look(target=dropped_spoon)` → 6. `pick(object=dropped_spoon)` → 7. `navigate(destination=kitchen_counter_2/top)` → 8. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.364, 9.109])` → 9. `explore_room(room=living_room_0_1)` → 10. `navigate(destination=dropped_bear)` → 11. `look(target=dropped_bear)` → 12. `pick(object=dropped_bear)` → 13. `navigate(destination=bookcase_2/top)` → 14. `place(object=dropped_bear, receptacle=bookcase_2/top, hint_xy=[1.005, -0.459])`
- 摆法 `shelf_full`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `explore_room(room=kitchen_0_1)` → 4. `navigate(destination=dropped_spoon)` → 5. `look(target=dropped_spoon)` → 6. `pick(object=dropped_spoon)` → 7. `navigate(destination=kitchen_counter_2/top)` → 8. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.364, 9.109])` → 9. `explore_room(room=living_room_0_1)` → 10. `navigate(destination=dropped_bear)` → 11. `look(target=dropped_bear)` → 12. `pick(object=dropped_bear)` → 13. `navigate(destination=bookcase_2/top)` → 14. `look(target=bookcase_2/top)` → 15. `navigate(destination=bookcase_3/top)` → 16. `place(object=dropped_bear, receptacle=bookcase_3/top, hint_xy=[2.093, -4.837])`

---

## T24_snack_for_kid

> 孩子在书房写作业饿了，给他拿点吃的。

### apple_on_table（对照）

**情况**：餐桌上有苹果 → 送到书房书桌

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `snack_apple` 在 `desk_1/top` 上
  - 手里空着
- **不行（0）**：书桌上没吃的；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`

### no_apples_for_him（Task）

**情况**：任务原话（不说不爱吃苹果）：苹果没人用就送苹果；苹果在餐桌一个座位的盘子里、旁边有勺子和杯子（有人在吃）时，送岛台果篮里的香蕉（香蕉和苹果都送降一档；只拿别人盘子里的苹果最不好）

**成功条件**（D 按摆法：`apple_free` D = 1、理想物在，`apple_in_use` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `apple_free`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_apple` 在 `desk_1/top` 上
  - 摆法 `apple_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_banana` 在 `desk_1/top` 上
        - `snack_apple` 没被挪动（离开局位置不超过 3 cm）
        - `seat_plate` 没被挪动（离开局位置不超过 3 cm）
- **次好（0.6）**：

  - 摆法 `apple_free`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `apple_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_banana` 在 `desk_1/top` 上
- **最不好（0.3）**：

  - 摆法 `apple_free`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `apple_in_use`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_apple` 在 `desk_1/top` 上
- **不行（0）**：书桌上没有能吃的；还拿着或掉了


**参考调用顺序**：

- 摆法 `apple_free`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`
- 摆法 `apple_in_use`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=snack_banana)` → 6. `pick(object=snack_banana)` → 7. `navigate(destination=desk_1/top)` → 8. `place(object=snack_banana, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`

### dinner_soon（Task）

**情况**：“还有半小时就吃晚饭了”：水果和零食盒 → 送水果，零食别送（水果零食都送降一档；只送零食最不好）

**指令**：孩子在书房写作业饿了，给他拿点吃的。还有半小时就吃晚饭了。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `apple`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `["not on", "snack_box", "desk_1/top"]`
  - 摆法 `banana`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_banana` 在 `desk_1/top` 上
        - `["not on", "snack_box", "desk_1/top"]`
- **次好（0.6）**：

  - 摆法 `apple`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_apple` 在 `desk_1/top` 上
  - 摆法 `banana`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_banana` 在 `desk_1/top` 上
- **最不好（0.3）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `snack_box` 在 `desk_1/top` 上
- **不行（0）**：书桌上没有能吃的；还拿着或掉了


**参考调用顺序**：

- 摆法 `apple`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`
- 摆法 `banana`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_banana)` → 4. `pick(object=snack_banana)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=snack_banana, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`

### fruit_out_of_view（Task）

**情况**：餐桌上没吃的，果篮在卧室书架上 → 找到果篮拿苹果；果篮是空的时，接着找，厨房台面上有根香蕉（拿空果篮充数最不好）

**成功条件**（D 按摆法：`apple_in_basket` D = 1、理想物在，`basket_empty` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `apple_in_basket`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_apple` 在 `desk_1/top` 上
  - 摆法 `basket_empty`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_banana` 在 `desk_1/top` 上
- **次好（0.6）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `home_basket` 在 `desk_1/top` 上
- **最不好（0.3）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **不行（0）**：书桌上没有能吃的；还拿着或掉了


**参考调用顺序**：

- 摆法 `apple_in_basket`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `search(object=home_basket, region=bedroom_0_1)` → 4. `navigate(destination=bookcase_2/top)` → 5. `look(target=bookcase_2/top)` → 6. `navigate(destination=snack_apple)` → 7. `pick(object=snack_apple)` → 8. `navigate(destination=desk_1/top)` → 9. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`
- 摆法 `basket_empty`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `search(object=home_basket, region=bedroom_0_1)` → 4. `look(target=bookcase_2/top)` → 5. `search(object=snack_banana, region=kitchen_0_1)` → 6. `navigate(destination=snack_banana)` → 7. `pick(object=snack_banana)` → 8. `navigate(destination=desk_1/top)` → 9. `place(object=snack_banana, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`

### where_is_he（Task）

**情况**：指令不说在哪：作业本摊在书房书桌或卧室书桌上 → 送到有作业的那张

**指令**：孩子写作业饿了，给他拿点吃的。

**成功条件**（D 按摆法：`study` D = 1、理想物在，`bedroom` D = 1、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `study`：
    - `snack_apple` 在 `desk_1/top` 上
    - 手里空着
  - 摆法 `bedroom`：
    - `snack_apple` 在其中任一处上：`desk_3/top`、`bookcase_4/top`
    - 手里空着
- **不行（0）**：送到另一张桌；还拿着或掉了


**参考调用顺序**：

- 摆法 `study`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_3/top)` → 6. `look(target=desk_3/top)` → 7. `navigate(destination=desk_1/top)` → 8. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`
- 摆法 `bedroom`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_1/top)` → 6. `look(target=desk_1/top)` → 7. `navigate(destination=desk_3/top)` → 8. `place(object=snack_apple, receptacle=desk_3/top, hint_xy=[6.194, -5.349])`

### two_kids（Task）

**情况**：“孩子们在写作业”：两张书桌都有作业，两样吃的 → 一人一样，按放的位置打分：放在自己书桌上作业旁边最好；压在作业上、或书桌有空却放到旁边书架上降一档；两样都降一档或都给同一个孩子最不好

**指令**：孩子们在写作业，饿了，给他们拿点吃的。

**成功条件**（D 按摆法：`apple_banana` D = 1、理想物在，`apple_snacks` D = 1、理想物不在，`desk3_covered` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `desk3_covered`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_apple` 离这些东西都至少 0 cm：`homework`
        - `snack_banana` 在 `bookcase_4/top` 上
      - 第 2 组：
        - `snack_banana` 在 `desk_1/top` 上
        - `snack_banana` 离这些东西都至少 0 cm：`homework`
        - `snack_apple` 在 `bookcase_4/top` 上
  - 摆法 `apple_banana`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_apple` 离这些东西都至少 0 cm：`homework`
        - `snack_banana` 在 `desk_3/top` 上
        - `snack_banana` 离这些东西都至少 0 cm：`homework_3`
      - 第 2 组：
        - `snack_banana` 在 `desk_1/top` 上
        - `snack_banana` 离这些东西都至少 0 cm：`homework`
        - `snack_apple` 在 `desk_3/top` 上
        - `snack_apple` 离这些东西都至少 0 cm：`homework_3`
  - 摆法 `apple_snacks`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_apple` 离这些东西都至少 0 cm：`homework`
        - `snack_box` 在 `desk_3/top` 上
        - `snack_box` 离这些东西都至少 0 cm：`homework_3`
      - 第 2 组：
        - `snack_box` 在 `desk_1/top` 上
        - `snack_box` 离这些东西都至少 0 cm：`homework`
        - `snack_apple` 在 `desk_3/top` 上
        - `snack_apple` 离这些东西都至少 0 cm：`homework_3`
- **次好（0.6）**：

  - 摆法 `apple_banana`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_apple` 离这些东西都至少 0 cm：`homework`
        - `snack_banana` 在 `bookcase_4/top` 上
      - 第 2 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_apple` 离这些东西都至少 0 cm：`homework`
        - `snack_banana` 在 `desk_3/top` 上
      - 第 3 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_banana` 在 `desk_3/top` 上
        - `snack_banana` 离这些东西都至少 0 cm：`homework_3`
      - 第 4 组：
        - `snack_banana` 在 `desk_1/top` 上
        - `snack_banana` 离这些东西都至少 0 cm：`homework`
        - `snack_apple` 在 `bookcase_4/top` 上
      - 第 5 组：
        - `snack_banana` 在 `desk_1/top` 上
        - `snack_banana` 离这些东西都至少 0 cm：`homework`
        - `snack_apple` 在 `desk_3/top` 上
      - 第 6 组：
        - `snack_banana` 在 `desk_1/top` 上
        - `snack_apple` 在 `desk_3/top` 上
        - `snack_apple` 离这些东西都至少 0 cm：`homework_3`
  - 摆法 `desk3_covered`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_apple` 离这些东西都至少 0 cm：`homework`
        - `snack_banana` 在 `desk_3/top` 上
      - 第 2 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_banana` 在 `bookcase_4/top` 上
      - 第 3 组：
        - `snack_banana` 在 `desk_1/top` 上
        - `snack_banana` 离这些东西都至少 0 cm：`homework`
        - `snack_apple` 在 `desk_3/top` 上
      - 第 4 组：
        - `snack_banana` 在 `desk_1/top` 上
        - `snack_apple` 在 `bookcase_4/top` 上
  - 摆法 `apple_snacks`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_apple` 离这些东西都至少 0 cm：`homework`
        - `snack_box` 在 `bookcase_4/top` 上
      - 第 2 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_apple` 离这些东西都至少 0 cm：`homework`
        - `snack_box` 在 `desk_3/top` 上
      - 第 3 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_box` 在 `desk_3/top` 上
        - `snack_box` 离这些东西都至少 0 cm：`homework_3`
      - 第 4 组：
        - `snack_box` 在 `desk_1/top` 上
        - `snack_box` 离这些东西都至少 0 cm：`homework`
        - `snack_apple` 在 `bookcase_4/top` 上
      - 第 5 组：
        - `snack_box` 在 `desk_1/top` 上
        - `snack_box` 离这些东西都至少 0 cm：`homework`
        - `snack_apple` 在 `desk_3/top` 上
      - 第 6 组：
        - `snack_box` 在 `desk_1/top` 上
        - `snack_apple` 在 `desk_3/top` 上
        - `snack_apple` 离这些东西都至少 0 cm：`homework_3`
- **最不好（0.3）**：

  - 摆法 `apple_banana`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_banana` 在 `bookcase_4/top` 上
      - 第 2 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_banana` 在 `desk_3/top` 上
      - 第 3 组：
        - `snack_banana` 在 `desk_1/top` 上
        - `snack_apple` 在 `bookcase_4/top` 上
      - 第 4 组：
        - `snack_banana` 在 `desk_1/top` 上
        - `snack_apple` 在 `desk_3/top` 上
      - 第 5 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_banana` 在 `desk_1/top` 上
      - 第 6 组：
        - `snack_apple` 在其中任一处上：`desk_3/top`、`bookcase_4/top`
        - `snack_banana` 在其中任一处上：`desk_3/top`、`bookcase_4/top`
  - 摆法 `desk3_covered`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_banana` 在 `desk_3/top` 上
      - 第 2 组：
        - `snack_banana` 在 `desk_1/top` 上
        - `snack_apple` 在 `desk_3/top` 上
      - 第 3 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_banana` 在 `desk_1/top` 上
      - 第 4 组：
        - `snack_apple` 在其中任一处上：`desk_3/top`、`bookcase_4/top`
        - `snack_banana` 在其中任一处上：`desk_3/top`、`bookcase_4/top`
  - 摆法 `apple_snacks`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_box` 在 `bookcase_4/top` 上
      - 第 2 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_box` 在 `desk_3/top` 上
      - 第 3 组：
        - `snack_box` 在 `desk_1/top` 上
        - `snack_apple` 在 `bookcase_4/top` 上
      - 第 4 组：
        - `snack_box` 在 `desk_1/top` 上
        - `snack_apple` 在 `desk_3/top` 上
      - 第 5 组：
        - `snack_apple` 在 `desk_1/top` 上
        - `snack_box` 在 `desk_1/top` 上
      - 第 6 组：
        - `snack_apple` 在其中任一处上：`desk_3/top`、`bookcase_4/top`
        - `snack_box` 在其中任一处上：`desk_3/top`、`bookcase_4/top`
- **不行（0）**：有孩子没拿到、东西留在桌上；还拿着或掉了


**参考调用顺序**：

- 摆法 `apple_banana`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])` → 7. `navigate(destination=snack_banana)` → 8. `pick(object=snack_banana)` → 9. `navigate(destination=desk_3/top)` → 10. `place(object=snack_banana, receptacle=desk_3/top, hint_xy=[6.194, -5.329])`
- 摆法 `apple_snacks`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])` → 7. `navigate(destination=snack_box)` → 8. `pick(object=snack_box)` → 9. `navigate(destination=desk_3/top)` → 10. `place(object=snack_box, receptacle=desk_3/top, hint_xy=[6.194, -5.329])`
- 摆法 `desk3_covered`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])` → 7. `navigate(destination=desk_3/top)` → 8. `look(target=desk_3/top)` → 9. `navigate(destination=snack_banana)` → 10. `pick(object=snack_banana)` → 11. `navigate(destination=bookcase_4/top)` → 12. `place(object=snack_banana, receptacle=bookcase_4/top, hint_xy=[7.0, -6.76])`

---

## T25_drink_for_guest

> 客人在客厅坐着，给他拿点喝的。

### drink_on_island（对照）

**情况**：岛台上一瓶果汁和一个杯子 → 都拿到电视柜

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `guest_juice` 在 `tv_stand_2/top` 上
  - `guest_juice` 立着
  - 这 7 件中至少 1 件还在 `tv_stand_2/top` 上：`guest_cup`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
  - 手里空着
- **不行（0）**：缺饮料或杯子；果汁躺着；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 7. `navigate(destination=guest_cup)` → 8. `pick(object=guest_cup)` → 9. `navigate(destination=tv_stand_2/top)` → 10. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])`

### cup_elsewhere（Task）

**情况**：岛台上只有果汁 → 想到要配杯子，找一个能用来喝的：小厨房台面的杯子；没有普通杯子就用马克杯；台面那个杯子里装着孩子的积木时用马克杯（倒出积木用那个杯子次好，连积木一起拿最不好）

**成功条件**（D 按摆法：`counter_cup` D = 0、理想物在，`only_mugs` D = 0、理想物在，`blocks_in_cup` D = 1、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `counter_cup`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `guest_juice` 在 `tv_stand_2/top` 上
        - `guest_juice` 立着
        - 这 6 件中至少 1 件还在 `tv_stand_2/top` 上：`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
  - 摆法 `blocks_in_cup`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `guest_juice` 在 `tv_stand_2/top` 上
        - `guest_juice` 立着
        - 这 3 件中至少 1 件还在 `tv_stand_2/top` 上：`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
        - `cup_counter_b` 没被挪动（离开局位置不超过 3 cm）
        - `cup_block_1` 在 `cup_counter_b` 里
        - `cup_block_2` 在 `cup_counter_b` 里
        - `cup_block_3` 在 `cup_counter_b` 里
  - 摆法 `only_mugs`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `guest_juice` 在 `tv_stand_2/top` 上
        - `guest_juice` 立着
        - 这 3 件中至少 1 件还在 `tv_stand_2/top` 上：`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
- **次好（0.6）**：

  - 摆法 `counter_cup`、`only_mugs`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `blocks_in_cup`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `guest_juice` 在 `tv_stand_2/top` 上
        - `guest_juice` 立着
        - `cup_counter_b` 在 `tv_stand_2/top` 上
        - `cup_block_1` 不在 `cup_counter_b` 里
        - `cup_block_2` 不在 `cup_counter_b` 里
        - `cup_block_3` 不在 `cup_counter_b` 里
- **最不好（0.3）**：

  - 摆法 `counter_cup`、`only_mugs`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `blocks_in_cup`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `guest_juice` 在 `tv_stand_2/top` 上
        - `guest_juice` 立着
        - `cup_counter_b` 在 `tv_stand_2/top` 上
- **不行（0）**：缺饮料或杯子；果汁躺着；还拿着或掉了


**参考调用顺序**：

- 摆法 `counter_cup`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 7. `search(object=cup_counter_b, region=kitchen_0_1)` → 8. `navigate(destination=cup_counter_b)` → 9. `pick(object=cup_counter_b)` → 10. `navigate(destination=tv_stand_2/top)` → 11. `place(object=cup_counter_b, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])`
- 摆法 `only_mugs`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 7. `search(object=mug_shelf, region=dining_room_0_1)` → 8. `navigate(destination=mug_shelf)` → 9. `pick(object=mug_shelf)` → 10. `navigate(destination=tv_stand_2/top)` → 11. `place(object=mug_shelf, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])`
- 摆法 `blocks_in_cup`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 7. `search(object=cup_counter_b, region=kitchen_0_1)` → 8. `look(target=kitchen_counter_2/top)` → 9. `search(object=mug_shelf, region=dining_room_0_1)` → 10. `navigate(destination=mug_shelf)` → 11. `pick(object=mug_shelf)` → 12. `navigate(destination=tv_stand_2/top)` → 13. `place(object=mug_shelf, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])`

### cold_one（Task）

**情况**：“天很热”：岛台上一瓶常温的，冰箱里一瓶冰的 → 拿冰箱那瓶（开门、关门）；冰箱里没有果汁只有冰汽水时拿汽水

**指令**：天很热，客人在客厅坐着，给他拿点喝的。

**成功条件**（D 按摆法：`cold_juice` D = 1、理想物在，`cold_soda` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `cold_juice`：
    - `cold_juice` 在 `tv_stand_2/top` 上
    - `cold_juice` 立着
    - 这 7 件中至少 1 件还在 `tv_stand_2/top` 上：`guest_cup`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - `guest_juice` 没被挪动（离开局位置不超过 3 cm）
    - `breakfast_fridge` 关着
    - 手里空着
  - 摆法 `cold_soda`：
    - `cold_soda` 在 `tv_stand_2/top` 上
    - `cold_soda` 立着
    - 这 7 件中至少 1 件还在 `tv_stand_2/top` 上：`guest_cup`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - `guest_juice` 没被挪动（离开局位置不超过 3 cm）
    - `breakfast_fridge` 关着
    - 手里空着
- **次好（0.6）**：

  - 摆法 `cold_juice`：
    - `cold_juice` 在 `tv_stand_2/top` 上
    - `cold_juice` 立着
    - 这 7 件中至少 1 件还在 `tv_stand_2/top` 上：`guest_cup`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `guest_juice` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `breakfast_fridge` 关着
  - 摆法 `cold_soda`：
    - `cold_soda` 在 `tv_stand_2/top` 上
    - `cold_soda` 立着
    - 这 7 件中至少 1 件还在 `tv_stand_2/top` 上：`guest_cup`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `guest_juice` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `breakfast_fridge` 关着
- **最不好（0.3）**：

  - `guest_juice` 在 `tv_stand_2/top` 上
  - `guest_juice` 立着
  - 这 7 件中至少 1 件还在 `tv_stand_2/top` 上：`guest_cup`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
  - 手里空着
- **不行（0）**：缺饮料或杯子；躺着；还拿着或掉了


**参考调用顺序**：

- 摆法 `cold_juice`：1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=breakfast_fridge/inside_shelf)` → 4. `look(target=breakfast_fridge/inside_shelf)` → 5. `navigate(destination=cold_juice)` → 6. `pick(object=cold_juice)` → 7. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 8. `navigate(destination=tv_stand_2/top)` → 9. `place(object=cold_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 10. `navigate(destination=breakfast_fridge)` → 11. `close(articulated=breakfast_fridge)` → 12. `navigate(destination=kitchen_island/top)` → 13. `look(target=kitchen_island/top)` → 14. `navigate(destination=guest_cup)` → 15. `pick(object=guest_cup)` → 16. `navigate(destination=tv_stand_2/top)` → 17. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])`
- 摆法 `cold_soda`：1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=breakfast_fridge/inside_shelf)` → 4. `look(target=breakfast_fridge/inside_shelf)` → 5. `navigate(destination=cold_soda)` → 6. `pick(object=cold_soda)` → 7. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 8. `navigate(destination=tv_stand_2/top)` → 9. `place(object=cold_soda, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 10. `navigate(destination=breakfast_fridge)` → 11. `close(articulated=breakfast_fridge)` → 12. `navigate(destination=kitchen_island/top)` → 13. `look(target=kitchen_island/top)` → 14. `navigate(destination=guest_cup)` → 15. `pick(object=guest_cup)` → 16. `navigate(destination=tv_stand_2/top)` → 17. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])`

### drink_in_fridge（Task）

**情况**：外面没有饮料 → 想到饮料在冰箱里，有什么喝的拿什么

**成功条件**（D 按摆法：`juice` D = 1、理想物在，`soda_only` D = 0、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `juice`：
    - `cold_juice` 在 `tv_stand_2/top` 上
    - `cold_juice` 立着
    - 这 7 件中至少 1 件还在 `tv_stand_2/top` 上：`guest_cup`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - `breakfast_fridge` 关着
    - 手里空着
  - 摆法 `soda_only`：
    - `cold_soda` 在 `tv_stand_2/top` 上
    - `cold_soda` 立着
    - 这 7 件中至少 1 件还在 `tv_stand_2/top` 上：`guest_cup`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - `breakfast_fridge` 关着
    - 手里空着
- **次好（0.6）**：

  - 摆法 `juice`：
    - `cold_juice` 在 `tv_stand_2/top` 上
    - `cold_juice` 立着
    - 这 7 件中至少 1 件还在 `tv_stand_2/top` 上：`guest_cup`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 手里空着
  - 摆法 `soda_only`：
    - `cold_soda` 在 `tv_stand_2/top` 上
    - `cold_soda` 立着
    - 这 7 件中至少 1 件还在 `tv_stand_2/top` 上：`guest_cup`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 手里空着
- **不行（0）**：缺饮料或杯子；躺着；还拿着或掉了


**参考调用顺序**：

- 摆法 `juice`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=breakfast_fridge/inside_shelf)` → 6. `look(target=breakfast_fridge/inside_shelf)` → 7. `navigate(destination=cold_juice)` → 8. `pick(object=cold_juice)` → 9. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 10. `navigate(destination=tv_stand_2/top)` → 11. `place(object=cold_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 12. `navigate(destination=breakfast_fridge)` → 13. `close(articulated=breakfast_fridge)` → 14. `navigate(destination=guest_cup)` → 15. `pick(object=guest_cup)` → 16. `navigate(destination=tv_stand_2/top)` → 17. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])`
- 摆法 `soda_only`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=breakfast_fridge/inside_shelf)` → 6. `look(target=breakfast_fridge/inside_shelf)` → 7. `navigate(destination=cold_soda)` → 8. `pick(object=cold_soda)` → 9. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 10. `navigate(destination=tv_stand_2/top)` → 11. `place(object=cold_soda, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 12. `navigate(destination=breakfast_fridge)` → 13. `close(articulated=breakfast_fridge)` → 14. `navigate(destination=guest_cup)` → 15. `pick(object=guest_cup)` → 16. `navigate(destination=tv_stand_2/top)` → 17. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])`

### cups_for_two（Task）

**情况**：“两位客人在客厅，给他们准备好饮料和杯子，每人一个杯子，尽量用普通杯子；桌上已有的不用重复拿。”客人桌上已有 0–2 个杯子，关着的矮柜里有 1–2 个普通杯，家里别的杯子只有餐厅的马克杯 → 先看桌上缺几个 → 再开柜看库存：够就补普通杯；不够就拿柜里的，再去餐厅拿马克杯补齐；已经齐了就只送饮料。最后正好两个杯子，原有的不动，柜门关好

**指令**：两位客人在客厅，给他们准备好饮料和杯子，每人一个杯子，尽量用普通杯子；桌上已有的不用重复拿。

**成功条件**（D 按摆法：`one_there` D = 1、理想物在，`none_one_inside` D = 1、理想物不在，`none_two_inside` D = 1、理想物在，`two_there` D = 1、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **次好（0.6）**：

  - 摆法 `none_one_inside`：
    - `guest_juice` 在 `tv_stand_2/top` 上
    - `guest_juice` 立着
    - 这 4 件中至少 2 件还在 `tv_stand_2/top` 上：`stock_cup_1`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 这 4 件中最多 2 件在 `tv_stand_2/top` 上：`stock_cup_1`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - 这 1 件中至少 1 件还在 `tv_stand_2/top` 上：`stock_cup_1`
      - 第 2 组：
        - 这 1 件中至少 1 件还在 `tv_stand_2/top` 上：`stock_cup_1`
        - `kitchen_cabinet_4` 关着
      - 第 3 组：
        - `kitchen_cabinet_4` 关着
  - 摆法 `none_two_inside`：
    - `guest_juice` 在 `tv_stand_2/top` 上
    - `guest_juice` 立着
    - 这 5 件中至少 2 件还在 `tv_stand_2/top` 上：`stock_cup_1`、`stock_cup_2`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 这 5 件中最多 2 件在 `tv_stand_2/top` 上：`stock_cup_1`、`stock_cup_2`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - 这 2 件中至少 2 件还在 `tv_stand_2/top` 上：`stock_cup_1`、`stock_cup_2`
      - 第 2 组：
        - 这 2 件中至少 2 件还在 `tv_stand_2/top` 上：`stock_cup_1`、`stock_cup_2`
        - `kitchen_cabinet_4` 关着
      - 第 3 组：
        - `kitchen_cabinet_4` 关着
  - 摆法 `one_there`：
    - `guest_juice` 在 `tv_stand_2/top` 上
    - `guest_juice` 立着
    - 这 5 件中至少 2 件还在 `tv_stand_2/top` 上：`tv_cup_1`、`stock_cup_1`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 这 5 件中最多 2 件在 `tv_stand_2/top` 上：`tv_cup_1`、`stock_cup_1`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - 这 2 件中至少 2 件还在 `tv_stand_2/top` 上：`tv_cup_1`、`stock_cup_1`
        - `tv_cup_1` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - 这 2 件中至少 2 件还在 `tv_stand_2/top` 上：`tv_cup_1`、`stock_cup_1`
        - `kitchen_cabinet_4` 关着
      - 第 3 组：
        - `tv_cup_1` 没被挪动（离开局位置不超过 3 cm）
        - `kitchen_cabinet_4` 关着
  - 摆法 `two_there`：
    - `guest_juice` 在 `tv_stand_2/top` 上
    - `guest_juice` 立着
    - 这 6 件中至少 2 件还在 `tv_stand_2/top` 上：`tv_cup_1`、`tv_cup_2`、`stock_cup_1`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 这 6 件中最多 2 件在 `tv_stand_2/top` 上：`tv_cup_1`、`tv_cup_2`、`stock_cup_1`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - 这 3 件中至少 2 件还在 `tv_stand_2/top` 上：`tv_cup_1`、`tv_cup_2`、`stock_cup_1`
        - `tv_cup_1` 没被挪动（离开局位置不超过 3 cm）
        - `tv_cup_2` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - 这 3 件中至少 2 件还在 `tv_stand_2/top` 上：`tv_cup_1`、`tv_cup_2`、`stock_cup_1`
        - `kitchen_cabinet_4` 关着
      - 第 3 组：
        - `tv_cup_1` 没被挪动（离开局位置不超过 3 cm）
        - `tv_cup_2` 没被挪动（离开局位置不超过 3 cm）
        - `kitchen_cabinet_4` 关着
- **最不好（0.3）**：

  - 摆法 `none_two_inside`：
    - `guest_juice` 在 `tv_stand_2/top` 上
    - `guest_juice` 立着
    - 这 5 件中至少 2 件还在 `tv_stand_2/top` 上：`mug_counter`、`mug_dining_cabinet`、`mug_shelf`、`stock_cup_1`、`stock_cup_2`
    - 手里空着
  - 摆法 `two_there`：
    - `guest_juice` 在 `tv_stand_2/top` 上
    - `guest_juice` 立着
    - 这 6 件中至少 2 件还在 `tv_stand_2/top` 上：`mug_counter`、`mug_dining_cabinet`、`mug_shelf`、`stock_cup_1`、`tv_cup_1`、`tv_cup_2`
    - 手里空着
  - 摆法 `one_there`：
    - `guest_juice` 在 `tv_stand_2/top` 上
    - `guest_juice` 立着
    - 这 5 件中至少 2 件还在 `tv_stand_2/top` 上：`mug_counter`、`mug_dining_cabinet`、`mug_shelf`、`stock_cup_1`、`tv_cup_1`
    - 手里空着
  - 摆法 `none_one_inside`：
    - `guest_juice` 在 `tv_stand_2/top` 上
    - `guest_juice` 立着
    - 这 4 件中至少 2 件还在 `tv_stand_2/top` 上：`mug_counter`、`mug_dining_cabinet`、`mug_shelf`、`stock_cup_1`
    - 手里空着
- **不行（0）**：不到两个杯子；没饮料；躺着；还拿着或掉了


**参考调用顺序**：

- 摆法 `one_there`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=guest_juice)` → 6. `pick(object=guest_juice)` → 7. `navigate(destination=tv_stand_2/top)` → 8. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 9. `navigate(destination=kitchen_cabinet_4)` → 10. `open(articulated=kitchen_cabinet_4)` → 11. `bend()` → 12. `explore_furniture(furniture=kitchen_cabinet_4)` → 13. `straighten()` → 14. `navigate(destination=stock_cup_1)` → 15. `pick(object=stock_cup_1)` → 16. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 17. `navigate(destination=tv_stand_2/top)` → 18. `place(object=stock_cup_1, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])` → 19. `navigate(destination=kitchen_cabinet_4)` → 20. `close(articulated=kitchen_cabinet_4)`
- 摆法 `none_one_inside`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=guest_juice)` → 6. `pick(object=guest_juice)` → 7. `navigate(destination=tv_stand_2/top)` → 8. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 9. `navigate(destination=kitchen_cabinet_4)` → 10. `open(articulated=kitchen_cabinet_4)` → 11. `bend()` → 12. `explore_furniture(furniture=kitchen_cabinet_4)` → 13. `straighten()` → 14. `navigate(destination=stock_cup_1)` → 15. `pick(object=stock_cup_1)` → 16. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 17. `navigate(destination=tv_stand_2/top)` → 18. `place(object=stock_cup_1, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])` → 19. `navigate(destination=kitchen_cabinet_4)` → 20. `close(articulated=kitchen_cabinet_4)` → 21. `search(object=mug_shelf, region=dining_room_0_1)` → 22. `navigate(destination=mug_shelf)` → 23. `pick(object=mug_shelf)` → 24. `navigate(destination=tv_stand_2/top)` → 25. `place(object=mug_shelf, receptacle=tv_stand_2/top, hint_xy=[7.044, 0.371])`
- 摆法 `none_two_inside`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=guest_juice)` → 6. `pick(object=guest_juice)` → 7. `navigate(destination=tv_stand_2/top)` → 8. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 9. `navigate(destination=kitchen_cabinet_4)` → 10. `open(articulated=kitchen_cabinet_4)` → 11. `bend()` → 12. `explore_furniture(furniture=kitchen_cabinet_4)` → 13. `straighten()` → 14. `navigate(destination=stock_cup_1)` → 15. `pick(object=stock_cup_1)` → 16. `navigate(destination=tv_stand_2/top)` → 17. `place(object=stock_cup_1, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])` → 18. `navigate(destination=stock_cup_2)` → 19. `pick(object=stock_cup_2)` → 20. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 21. `navigate(destination=tv_stand_2/top)` → 22. `place(object=stock_cup_2, receptacle=tv_stand_2/top, hint_xy=[7.044, 0.371])` → 23. `navigate(destination=kitchen_cabinet_4)` → 24. `close(articulated=kitchen_cabinet_4)`
- 摆法 `two_there`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `navigate(destination=guest_juice)` → 6. `pick(object=guest_juice)` → 7. `navigate(destination=tv_stand_2/top)` → 8. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])`

### two_guests（Task）

**情况**：“两位客人” → 两个杯子；岛台只有一个、家里也没有别的普通杯子时，用餐厅的马克杯补

**指令**：两位客人在客厅坐着，给他们拿点喝的。

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `two_cups`：
    - `guest_juice` 在 `tv_stand_2/top` 上
    - `guest_juice` 立着
    - 这 8 件中至少 2 件还在 `tv_stand_2/top` 上：`guest_cup`、`guest_cup_2`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 手里空着
  - 摆法 `one_cup`：
    - `guest_juice` 在 `tv_stand_2/top` 上
    - `guest_juice` 立着
    - 这 4 件中至少 2 件还在 `tv_stand_2/top` 上：`guest_cup`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 手里空着
- **不行（0）**：只拿一个杯子；缺饮料；还拿着或掉了


**参考调用顺序**：

- 摆法 `two_cups`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 7. `navigate(destination=guest_cup)` → 8. `pick(object=guest_cup)` → 9. `navigate(destination=tv_stand_2/top)` → 10. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])` → 11. `navigate(destination=guest_cup_2)` → 12. `pick(object=guest_cup_2)` → 13. `navigate(destination=tv_stand_2/top)` → 14. `place(object=guest_cup_2, receptacle=tv_stand_2/top, hint_xy=[7.804, 0.371])`
- 摆法 `one_cup`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 7. `navigate(destination=guest_cup)` → 8. `pick(object=guest_cup)` → 9. `navigate(destination=tv_stand_2/top)` → 10. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])` → 11. `search(object=mug_shelf, region=dining_room_0_1)` → 12. `navigate(destination=mug_shelf)` → 13. `pick(object=mug_shelf)` → 14. `navigate(destination=tv_stand_2/top)` → 15. `place(object=mug_shelf, receptacle=tv_stand_2/top, hint_xy=[7.804, 0.371])`

### little_guest（Task）

**情况**：“来了个小朋友”：瓷杯和塑料杯 → 塑料杯

**指令**：来了个小朋友，在客厅坐着，给她拿点喝的。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `guest_juice` 在 `tv_stand_2/top` 上
  - `guest_juice` 立着
  - 这 1 件中至少 1 件还在 `tv_stand_2/top` 上：`kid_cup`
  - `guest_cup` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- **次好（0.6）**：

  - `guest_juice` 在 `tv_stand_2/top` 上
  - `guest_juice` 立着
  - 这 1 件中至少 1 件还在 `tv_stand_2/top` 上：`kid_cup`
  - 手里空着
- **最不好（0.3）**：

  - `guest_juice` 在 `tv_stand_2/top` 上
  - `guest_juice` 立着
  - `guest_cup` 在 `tv_stand_2/top` 上
  - 手里空着
- **不行（0）**：缺饮料或杯子；躺着；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 7. `navigate(destination=kid_cup)` → 8. `pick(object=kid_cup)` → 9. `navigate(destination=tv_stand_2/top)` → 10. `place(object=kid_cup, receptacle=tv_stand_2/top, hint_xy=[7.55, 0.36])`

---

## T26_kids_things_to_room

> 把孩子落在客厅的东西拿回他房间。

### car_in_living_room（对照）

**情况**：小车在客厅地上 → 放进他卧室的玩具筐

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `living_car` 在 `kids_basket` 里
  - 手里空着
- **不行（0）**：还在客厅或放别处；还拿着或掉了


**参考调用顺序**：

1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `look(target=living_car)` → 4. `pick(object=living_car)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=kids_basket)` → 7. `place(object=living_car, receptacle=kids_basket)`

### whose（Task）

**情况**：电视柜上有一本和他书架上一样的蓝色精装书，还有一本大人的平装书 → 只拿他的那本，放到他房间的书架上，平装书不动；他的书架每层都摆满时放床边那个书架（放房间里别的家具上次好）

**成功条件**（D 按摆法：`shelf_room` D = 1、理想物在，`shelf_full` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `shelf_room`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_book` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
        - `adult_novel` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `shelf_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_book` 在其中任一处上：`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
        - `adult_novel` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_4b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_4b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_4b` 没被挪动（离开局位置不超过 3 cm）
- **次好（0.6）**：

  - 摆法 `shelf_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_book` 在其中任一处上：`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
        - `adult_novel` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `kid_book` 在其中任一处上：`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
        - `adult_novel` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_4b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_4b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_4b` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `shelf_room`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_book` 在其中任一处上：`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
        - `adult_novel` 没被挪动（离开局位置不超过 3 cm）
- **最不好（0.3）**：

  - 摆法 `shelf_room`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_book` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
      - 第 2 组：
        - `kid_book` 在其中任一处上：`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
  - 摆法 `shelf_full`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_book` 在其中任一处上：`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
        - `kid_book_shelf_0_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_4b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_4b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_4b` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `kid_book` 在其中任一处上：`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
        - `adult_novel` 没被挪动（离开局位置不超过 3 cm）
      - 第 3 组：
        - `kid_book` 在其中任一处上：`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
      - 第 4 组：
        - `kid_book` 在其中任一处上：`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
        - `kid_book_shelf_0_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_0_4b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_shelf_1_4b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_1a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_1b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_2a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_2b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_3a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_3b` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_4a` 没被挪动（离开局位置不超过 3 cm）
        - `kid_book_top_4b` 没被挪动（离开局位置不超过 3 cm）
      - 第 5 组：
        - `kid_book` 在其中任一处上：`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
- **不行（0）**：图画书没拿回或放到别处；还拿着或掉了


**参考调用顺序**：

- 摆法 `shelf_room`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=kid_book)` → 4. `pick(object=kid_book)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=kid_book, receptacle=bookcase_2/top, hint_xy=[1.12, -0.43])`
- 摆法 `shelf_full`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=kid_book)` → 4. `pick(object=kid_book)` → 5. `navigate(destination=bookcase_2/top)` → 6. `look(target=bookcase_2/top)` → 7. `navigate(destination=bookcase_3/top)` → 8. `place(object=kid_book, receptacle=bookcase_3/top, hint_xy=[2.1, -4.78])`

### scattered（Task）

**情况**：小车在地上、鸭子在电视柜、积木在岛台 → 都找到放进装玩具的地方：玩具筐；没有筐时放进他书架上的小玩具盒（只放到他房间家具上的每样降一档）

**成功条件**（D 按摆法：`basket` D = 1、理想物在，`no_basket` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `basket`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_car` 在 `kids_basket` 里
        - `living_duck` 在 `kids_basket` 里
        - `living_block` 在 `kids_basket` 里
  - 摆法 `no_basket`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_car` 在 `kids_toy_bin` 里
        - `living_duck` 在 `kids_toy_bin` 里
        - `living_block` 在 `kids_toy_bin` 里
- **次好（0.6）**：

  - 摆法 `basket`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `no_basket`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_car` 在 `kids_toy_bin` 里
        - `living_duck` 在 `kids_toy_bin` 里
        - `living_block` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
      - 第 2 组：
        - `living_car` 在 `kids_toy_bin` 里
        - `living_duck` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
        - `living_block` 在 `kids_toy_bin` 里
      - 第 3 组：
        - `living_car` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
        - `living_duck` 在 `kids_toy_bin` 里
        - `living_block` 在 `kids_toy_bin` 里
- **最不好（0.3）**：

  - 摆法 `basket`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `no_basket`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_car` 在 `kids_toy_bin` 里
        - `living_duck` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
        - `living_block` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
      - 第 2 组：
        - `living_car` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
        - `living_duck` 在 `kids_toy_bin` 里
        - `living_block` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
      - 第 3 组：
        - `living_car` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
        - `living_duck` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
        - `living_block` 在 `kids_toy_bin` 里
      - 第 4 组：
        - `living_car` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
        - `living_duck` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
        - `living_block` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
- **不行（0）**：有一样没拿回他房间或还在地上；还拿着或掉了


**参考调用顺序**：

- 摆法 `basket`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `look(target=living_car)` → 4. `pick(object=living_car)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=kids_basket)` → 7. `place(object=living_car, receptacle=kids_basket)` → 8. `navigate(destination=living_duck)` → 9. `pick(object=living_duck)` → 10. `navigate(destination=kids_basket)` → 11. `place(object=living_duck, receptacle=kids_basket)` → 12. `navigate(destination=living_block)` → 13. `pick(object=living_block)` → 14. `navigate(destination=kids_basket)` → 15. `place(object=living_block, receptacle=kids_basket)`
- 摆法 `no_basket`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `look(target=living_car)` → 4. `pick(object=living_car)` → 5. `navigate(destination=bookcase_2/top)` → 6. `look(target=bookcase_2/top)` → 7. `navigate(destination=kids_toy_bin)` → 8. `place(object=living_car, receptacle=kids_toy_bin)` → 9. `navigate(destination=living_duck)` → 10. `pick(object=living_duck)` → 11. `navigate(destination=kids_toy_bin)` → 12. `place(object=living_duck, receptacle=kids_toy_bin)` → 13. `navigate(destination=living_block)` → 14. `pick(object=living_block)` → 15. `navigate(destination=kids_toy_bin)` → 16. `place(object=living_block, receptacle=kids_toy_bin)`

### where_in_room（Task）

**情况**：小车和他的一本书 → 小车进筐，书放到他房间的书架上；没有筐、原处放着一个垃圾桶时，小车放到他书架上，放进垃圾桶最不好

**成功条件**（D 按摆法：`basket` D = 1、理想物在，`waste_bin` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `basket`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_car` 在 `kids_basket` 里
        - `kid_book` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
  - 摆法 `waste_bin`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_car` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
        - `kid_book` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
- **次好（0.6）**：

  - 摆法 `basket`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_car` 在 `kids_basket` 里
        - `kid_book` 在 `kids_basket` 里
      - 第 2 组：
        - `living_car` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
        - `kid_book` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
  - 摆法 `waste_bin`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_car` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
        - `kid_book` 在其中任一处上：`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
      - 第 2 组：
        - `living_car` 在其中任一处上：`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
        - `kid_book` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
- **最不好（0.3）**：

  - 摆法 `basket`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_car` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
        - `kid_book` 在 `kids_basket` 里
  - 摆法 `waste_bin`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_car` 在其中任一处上：`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
        - `kid_book` 在其中任一处上：`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
      - 第 2 组：
        - `living_car` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
        - `kid_book` 在 `kids_room_bin` 里
      - 第 3 组：
        - `living_car` 在 `kids_room_bin` 里
        - `kid_book` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
      - 第 4 组：
        - `living_car` 在其中任一处上：`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
        - `kid_book` 在 `kids_room_bin` 里
      - 第 5 组：
        - `living_car` 在 `kids_room_bin` 里
        - `kid_book` 在其中任一处上：`desk_3/top`、`large_shelf_4/shelf_0`、`large_shelf_4/shelf_1`、`large_shelf_4/shelf_2`、`large_shelf_4/shelf_3`、`large_shelf_4/shelf_4`、`large_shelf_5/shelf_0`、`large_shelf_5/shelf_1`、`large_shelf_5/shelf_2`、`large_shelf_5/shelf_3`
      - 第 6 组：
        - `living_car` 在 `kids_room_bin` 里
        - `kid_book` 在 `kids_room_bin` 里
- **不行（0）**：有一样没拿回他房间；还拿着或掉了


**参考调用顺序**：

- 摆法 `basket`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `look(target=living_car)` → 4. `pick(object=living_car)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=kids_basket)` → 7. `place(object=living_car, receptacle=kids_basket)` → 8. `navigate(destination=kid_book)` → 9. `pick(object=kid_book)` → 10. `navigate(destination=bookcase_2/top)` → 11. `place(object=kid_book, receptacle=bookcase_2/top, hint_xy=[1.12, -0.43])`
- 摆法 `waste_bin`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `look(target=living_car)` → 4. `pick(object=living_car)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=kids_room_bin)` → 7. `look(target=kids_room_bin)` → 8. `navigate(destination=bookcase_2/top)` → 9. `place(object=living_car, receptacle=bookcase_2/top, hint_xy=[1.15, -0.43])` → 10. `navigate(destination=kid_book)` → 11. `pick(object=kid_book)` → 12. `navigate(destination=bookcase_3/top)` → 13. `place(object=kid_book, receptacle=bookcase_3/top, hint_xy=[2.1, -4.78])`

### bear_to_bed（Task）

**情况**：“孩子要睡觉了”：小熊在电视柜 → 放到他床上或床头书架上，不放筐里；床头书架顶上摆满书时放到这个书架的下一层（放另一个书架、放筐里、挪动顶上的书各降一档）

**指令**：孩子要睡觉了，把他落在客厅的东西拿回他房间。

**成功条件**（D 按摆法：`top_free` D = 1、理想物在，`top_covered` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `top_covered`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_bear` 在其中任一处上：`mattress_1/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
        - `b3_book_1` 没被挪动（离开局位置不超过 3 cm）
        - `b3_book_2` 没被挪动（离开局位置不超过 3 cm）
        - `b3_book_3` 没被挪动（离开局位置不超过 3 cm）
        - `b3_paperback_1` 没被挪动（离开局位置不超过 3 cm）
        - `b3_paperback_2` 没被挪动（离开局位置不超过 3 cm）
        - `b3_paperback_3` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `top_free`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_bear` 在其中任一处上：`mattress_1/top`、`bookcase_3/top`
- **次好（0.6）**：

  - 摆法 `top_free`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_bear` 在其中任一处上：`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
      - 第 2 组：
        - `living_bear` 在 `kids_basket` 里
  - 摆法 `top_covered`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_bear` 在其中任一处上：`mattress_1/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
      - 第 2 组：
        - `living_bear` 在 `kids_basket` 里
        - `b3_book_1` 没被挪动（离开局位置不超过 3 cm）
        - `b3_book_2` 没被挪动（离开局位置不超过 3 cm）
        - `b3_book_3` 没被挪动（离开局位置不超过 3 cm）
        - `b3_paperback_1` 没被挪动（离开局位置不超过 3 cm）
        - `b3_paperback_2` 没被挪动（离开局位置不超过 3 cm）
        - `b3_paperback_3` 没被挪动（离开局位置不超过 3 cm）
- **最不好（0.3）**：

  - 摆法 `top_free`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `top_covered`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `living_bear` 在 `kids_basket` 里
- **不行（0）**：熊没拿回他房间；还拿着或掉了


**参考调用顺序**：

- 摆法 `top_free`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=living_bear)` → 4. `pick(object=living_bear)` → 5. `navigate(destination=bookcase_3/top)` → 6. `place(object=living_bear, receptacle=bookcase_3/top, hint_xy=[2.1, -4.78])`
- 摆法 `top_covered`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=living_bear)` → 4. `pick(object=living_bear)` → 5. `navigate(destination=bookcase_3/top)` → 6. `look(target=bookcase_3/top)` → 7. `navigate(destination=bookcase_2/top)` → 8. `place(object=living_bear, receptacle=bookcase_2/top, hint_xy=[1.125, -0.459])`

### two_bedrooms（Task）

**情况**：两间卧室，有他玩具筐的那间是他的 → 认出来，把小车放进去

**成功条件**（D 按摆法：`room_east` D = 1、理想物在，`room_south` D = 1、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `living_car` 在 `kids_basket` 里
  - 手里空着
- **不行（0）**：放进另一间卧室；还拿着或掉了


**参考调用顺序**：

- 摆法 `room_east`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `look(target=living_car)` → 4. `pick(object=living_car)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=kids_basket)` → 7. `place(object=living_car, receptacle=kids_basket)`
- 摆法 `room_south`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `look(target=living_car)` → 4. `pick(object=living_car)` → 5. `explore_room(room=bedroom_0_0)` → 6. `navigate(destination=kids_basket)` → 7. `place(object=living_car, receptacle=kids_basket)`

---

## T27_leftovers_to_fridge

> 晚饭吃完了，把剩菜收进冰箱。

### rice_on_table（对照）

**情况**：餐桌上一盒剩饭 → 放进冰箱，关门

**成功条件**（D 按摆法：`rice_on_table` D = 0、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
  - `breakfast_fridge` 关着
  - 手里空着
- **次好（0.6）**：

  - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
  - 手里空着
- **不行（0）**：有剩菜没进冰箱；倒了；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=leftover_rice)` → 6. `pick(object=leftover_rice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)`

### which_is_leftover（Task）

**情况**：桌上除了剩饭还有不该进冰箱的东西：一个空外卖盒，或者果篮和麦片盒，或者一碗有人还在吃的燕麦（勺子摆在碗前） → 只把剩饭收进冰箱；空外卖盒、果篮、麦片都不进冰箱，正在吃的那碗不收也不拿起来（过程要求）

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `still_eating`：
    - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
    - `breakfast_fridge` 关着
    - `eating_bowl` 没被挪动（离开局位置不超过 3 cm）
    - 过程要求：整局都没拿起过 `eating_bowl`（拆了再搭回去不算）
    - 手里空着
  - 摆法 `fruit_stays_out`：
    - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
    - `breakfast_fridge` 关着
    - `table_basket`、`table_cereal` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
  - 摆法 `which_is_leftover`：
    - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
    - `breakfast_fridge` 关着
    - `["not on", "empty_tray", "breakfast_fridge/inside_shelf"]`
    - 手里空着
- **次好（0.6）**：

  - 摆法 `still_eating`：
    - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
    - `eating_bowl` 没被挪动（离开局位置不超过 3 cm）
    - 过程要求：整局都没拿起过 `eating_bowl`（拆了再搭回去不算）
    - 手里空着
  - 摆法 `fruit_stays_out`：
    - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
    - `table_basket`、`table_cereal` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
  - 摆法 `which_is_leftover`：
    - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
    - `["not on", "empty_tray", "breakfast_fridge/inside_shelf"]`
    - 手里空着
- **最不好（0.3）**：

  - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
  - 手里空着
- **不行（0）**：剩饭没进冰箱；倒了；还拿着或掉了


**参考调用顺序**：

- 摆法 `which_is_leftover`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=leftover_rice)` → 6. `pick(object=leftover_rice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)`
- 摆法 `fruit_stays_out`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=leftover_rice)` → 6. `pick(object=leftover_rice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)`
- 摆法 `still_eating`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=leftover_rice)` → 6. `pick(object=leftover_rice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)`

### two_leftovers（Task）

**情况**：剩饭和一锅汤 → 都收（汤可能还在灶上）；汤锅摆在有人正在吃的座位前时只收剩饭（把汤收走最不好）

**成功条件**（D 按摆法：`soup_at_seat` D = 1、理想物在，`soup_on_table` D = 0、理想物在，`soup_on_stove` D = 0、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `soup_at_seat`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
        - `leftover_soup` 没被挪动（离开局位置不超过 3 cm）
        - `eating_bowl` 没被挪动（离开局位置不超过 3 cm）
        - `breakfast_fridge` 关着
  - 摆法 `soup_on_table`、`soup_on_stove`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
        - `leftover_soup` 在 `breakfast_fridge/inside_shelf` 上
        - `leftover_soup` 立着
        - `breakfast_fridge` 关着
- **次好（0.6）**：

  - 摆法 `soup_at_seat`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
        - `leftover_soup` 没被挪动（离开局位置不超过 3 cm）
        - `eating_bowl` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `soup_on_table`、`soup_on_stove`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
        - `leftover_soup` 在 `breakfast_fridge/inside_shelf` 上
        - `leftover_soup` 立着
- **最不好（0.3）**：

  - 摆法 `soup_on_table`、`soup_on_stove`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `soup_at_seat`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
        - `breakfast_fridge` 关着
      - 第 2 组：
        - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
- **不行（0）**：有剩菜没进冰箱；倒了；还拿着或掉了


**参考调用顺序**：

- 摆法 `soup_at_seat`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=leftover_rice)` → 6. `pick(object=leftover_rice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)`
- 摆法 `soup_on_table`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=leftover_rice)` → 6. `pick(object=leftover_rice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.9, 3.46])` → 9. `navigate(destination=leftover_soup)` → 10. `pick(object=leftover_soup)` → 11. `navigate(destination=breakfast_fridge)` → 12. `place(object=leftover_soup, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.9, 3.2])` → 13. `close(articulated=breakfast_fridge)`
- 摆法 `soup_on_stove`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=kitchen_stove/top)` → 4. `look(target=kitchen_stove/top)` → 5. `navigate(destination=breakfast_fridge)` → 6. `open(articulated=breakfast_fridge)` → 7. `navigate(destination=leftover_rice)` → 8. `pick(object=leftover_rice)` → 9. `navigate(destination=breakfast_fridge)` → 10. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.9, 3.46])` → 11. `navigate(destination=leftover_soup)` → 12. `pick(object=leftover_soup)` → 13. `navigate(destination=breakfast_fridge)` → 14. `place(object=leftover_soup, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.9, 3.2])` → 15. `close(articulated=breakfast_fridge)`

### fridge_out_of_view（Task）

**情况**：从餐厅出发，看不到冰箱 → 先找到冰箱；冰箱层板左半边摆满了饭盒和果汁时放进右边空着的地方，原有的不动

**成功条件**（D 按摆法：`fridge_free` D = 0、理想物在，`fridge_crowded` D = 1、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `fridge_crowded`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
        - `breakfast_fridge` 关着
        - `stored_box_1` 没被挪动（离开局位置不超过 3 cm）
        - `stored_box_2` 没被挪动（离开局位置不超过 3 cm）
        - `stored_box_3` 没被挪动（离开局位置不超过 3 cm）
        - `stored_box_4` 没被挪动（离开局位置不超过 3 cm）
        - `stored_juice_1` 没被挪动（离开局位置不超过 3 cm）
        - `stored_juice_2` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `fridge_free`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
        - `breakfast_fridge` 关着
- **次好（0.6）**：

  - 摆法 `fridge_crowded`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
        - `stored_box_1` 没被挪动（离开局位置不超过 3 cm）
        - `stored_box_2` 没被挪动（离开局位置不超过 3 cm）
        - `stored_box_3` 没被挪动（离开局位置不超过 3 cm）
        - `stored_box_4` 没被挪动（离开局位置不超过 3 cm）
        - `stored_juice_1` 没被挪动（离开局位置不超过 3 cm）
        - `stored_juice_2` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
        - `breakfast_fridge` 关着
  - 摆法 `fridge_free`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
- **最不好（0.3）**：

  - 摆法 `fridge_free`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `fridge_crowded`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
- **不行（0）**：剩饭没进冰箱；倒了；还拿着或掉了


**参考调用顺序**：

- 摆法 `fridge_free`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `explore_room(room=living_room_0_0)` → 4. `navigate(destination=breakfast_fridge)` → 5. `open(articulated=breakfast_fridge)` → 6. `navigate(destination=leftover_rice)` → 7. `pick(object=leftover_rice)` → 8. `navigate(destination=breakfast_fridge)` → 9. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 10. `close(articulated=breakfast_fridge)`
- 摆法 `fridge_crowded`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `explore_room(room=living_room_0_0)` → 4. `navigate(destination=breakfast_fridge)` → 5. `open(articulated=breakfast_fridge)` → 6. `navigate(destination=leftover_rice)` → 7. `pick(object=leftover_rice)` → 8. `navigate(destination=breakfast_fridge)` → 9. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[6.05, 3.3])` → 10. `close(articulated=breakfast_fridge)`

---

## T28_cup_to_bedside

> 孩子要睡了，把他的水杯拿到床边。

### cup_on_counter（对照）

**情况**：塑料杯在小厨房台面 → 放到他床边的矮书架上

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
  - `kid_cup` 立着
  - 手里空着
- **不行（0）**：没放床边；躺着；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=kid_cup)` → 4. `pick(object=kid_cup)` → 5. `navigate(destination=bookcase_3/top)` → 6. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.093, -4.837])`

### which_bed（Task）

**情况**：两张床，他的床上有小熊 → 放到那张床边

**成功条件**（D 按摆法：`east` D = 1、理想物在，`south` D = 1、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `south`：
    - `kid_cup` 在 `cell_shelf_2/top` 上
    - `kid_cup` 立着
    - 手里空着
  - 摆法 `east`：
    - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
    - `kid_cup` 立着
    - 手里空着
- **不行（0）**：放到另一张床边；还拿着或掉了


**参考调用顺序**：

- 摆法 `east`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=kid_cup)` → 4. `pick(object=kid_cup)` → 5. `navigate(destination=mattress_2/top)` → 6. `look(target=mattress_2/top)` → 7. `navigate(destination=bookcase_3/top)` → 8. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.093, -4.837])`
- 摆法 `south`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=kid_cup)` → 4. `pick(object=kid_cup)` → 5. `navigate(destination=mattress_1/top)` → 6. `look(target=mattress_1/top)` → 7. `navigate(destination=cell_shelf_2/top)` → 8. `place(object=kid_cup, receptacle=cell_shelf_2/top, hint_xy=[1.333, -11.897])`

### where_his_cup_is（Task）

**情况**：台面上有瓷杯和马克杯；他的塑料杯也在那儿，或者收在矮柜里，或者家里根本没有 → 到台面看：有他的就拿；只有别人的 → 打开矮柜找他的，拿出来关好门；柜里也没有 → 拿家里的杯子代替

**成功条件**（D 按摆法：`on_counter` D = 1、理想物在，`in_cabinet` D = 1、理想物在，`no_kid_cup` D = 0、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `no_kid_cup`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `cup_counter_b` 立着
        - `kitchen_cabinet_4` 关着
      - 第 2 组：
        - `counter_mug` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `counter_mug` 立着
        - `kitchen_cabinet_4` 关着
      - 第 3 组：
        - `cup_kitchen_cabinet` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `cup_kitchen_cabinet` 立着
        - `kitchen_cabinet_4` 关着
      - 第 4 组：
        - `cup_side_table` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `cup_side_table` 立着
        - `kitchen_cabinet_4` 关着
  - 摆法 `in_cabinet`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `kid_cup` 立着
        - `cup_counter_b` 没被挪动（离开局位置不超过 3 cm）
        - `counter_mug` 没被挪动（离开局位置不超过 3 cm）
        - `kitchen_cabinet_4` 关着
  - 摆法 `on_counter`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `kid_cup` 立着
        - `cup_counter_b` 没被挪动（离开局位置不超过 3 cm）
        - `counter_mug` 没被挪动（离开局位置不超过 3 cm）
- **次好（0.6）**：

  - 摆法 `no_kid_cup`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `cup_counter_b` 立着
      - 第 2 组：
        - `counter_mug` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `counter_mug` 立着
      - 第 3 组：
        - `cup_kitchen_cabinet` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `cup_kitchen_cabinet` 立着
      - 第 4 组：
        - `cup_side_table` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `cup_side_table` 立着
  - 摆法 `in_cabinet`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `kid_cup` 立着
        - `kitchen_cabinet_4` 关着
      - 第 2 组：
        - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `kid_cup` 立着
        - `cup_counter_b` 没被挪动（离开局位置不超过 3 cm）
        - `counter_mug` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `on_counter`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `kid_cup` 立着
- **最不好（0.3）**：

  - 摆法 `no_kid_cup`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `on_counter`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `cup_counter_b` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `cup_counter_b` 立着
        - `cup_counter_b` 没被挪动（离开局位置不超过 3 cm）
        - `counter_mug` 没被挪动（离开局位置不超过 3 cm）
      - 第 2 组：
        - `counter_mug` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `counter_mug` 立着
        - `cup_counter_b` 没被挪动（离开局位置不超过 3 cm）
        - `counter_mug` 没被挪动（离开局位置不超过 3 cm）
      - 第 3 组：
        - `cup_counter_b` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `cup_counter_b` 立着
      - 第 4 组：
        - `counter_mug` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `counter_mug` 立着
  - 摆法 `in_cabinet`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `kid_cup` 立着
      - 第 2 组：
        - `cup_counter_b` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `cup_counter_b` 立着
        - `cup_counter_b` 没被挪动（离开局位置不超过 3 cm）
        - `counter_mug` 没被挪动（离开局位置不超过 3 cm）
        - `kitchen_cabinet_4` 关着
      - 第 3 组：
        - `counter_mug` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `counter_mug` 立着
        - `cup_counter_b` 没被挪动（离开局位置不超过 3 cm）
        - `counter_mug` 没被挪动（离开局位置不超过 3 cm）
        - `kitchen_cabinet_4` 关着
      - 第 4 组：
        - `cup_counter_b` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `cup_counter_b` 立着
        - `kitchen_cabinet_4` 关着
      - 第 5 组：
        - `cup_counter_b` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `cup_counter_b` 立着
        - `cup_counter_b` 没被挪动（离开局位置不超过 3 cm）
        - `counter_mug` 没被挪动（离开局位置不超过 3 cm）
      - 第 6 组：
        - `counter_mug` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `counter_mug` 立着
        - `kitchen_cabinet_4` 关着
      - 第 7 组：
        - `counter_mug` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `counter_mug` 立着
        - `cup_counter_b` 没被挪动（离开局位置不超过 3 cm）
        - `counter_mug` 没被挪动（离开局位置不超过 3 cm）
      - 第 8 组：
        - `cup_counter_b` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `cup_counter_b` 立着
      - 第 9 组：
        - `counter_mug` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
        - `counter_mug` 立着
- **不行（0）**：床边没杯子；躺着；还拿着或掉了


**参考调用顺序**：

- 摆法 `on_counter`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=kid_cup)` → 4. `pick(object=kid_cup)` → 5. `navigate(destination=bookcase_3/top)` → 6. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.093, -4.837])`
- 摆法 `in_cabinet`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=kitchen_cabinet_4)` → 4. `open(articulated=kitchen_cabinet_4)` → 5. `bend()` → 6. `explore_furniture(furniture=kitchen_cabinet_4)` → 7. `straighten()` → 8. `navigate(destination=kid_cup)` → 9. `pick(object=kid_cup)` → 10. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 11. `navigate(destination=bookcase_3/top)` → 12. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.093, -4.837])` → 13. `navigate(destination=kitchen_cabinet_4)` → 14. `close(articulated=kitchen_cabinet_4)`
- 摆法 `no_kid_cup`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=kitchen_cabinet_4)` → 4. `open(articulated=kitchen_cabinet_4)` → 5. `bend()` → 6. `explore_furniture(furniture=kitchen_cabinet_4)` → 7. `straighten()` → 8. `close(articulated=kitchen_cabinet_4)` → 9. `navigate(destination=cup_counter_b)` → 10. `pick(object=cup_counter_b)` → 11. `navigate(destination=bookcase_3/top)` → 12. `place(object=cup_counter_b, receptacle=bookcase_3/top, hint_xy=[2.093, -4.817])`

### cup_out_of_view（Task）

**情况**：杯子落在餐桌上，看不到 → 先找；床边矮书架顶上摆满书时放到它下一层或书桌上（挪书腾地方次好）

**成功条件**（D 按摆法：`cup_found` D = 1、理想物在，`side_covered` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `side_covered`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_cup` 在其中任一处上：`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`desk_1/top`
        - `kid_cup` 立着
        - `b3_book_1` 没被挪动（离开局位置不超过 3 cm）
        - `b3_book_2` 没被挪动（离开局位置不超过 3 cm）
        - `b3_book_3` 没被挪动（离开局位置不超过 3 cm）
        - `b3_paperback_1` 没被挪动（离开局位置不超过 3 cm）
        - `b3_paperback_2` 没被挪动（离开局位置不超过 3 cm）
        - `b3_paperback_3` 没被挪动（离开局位置不超过 3 cm）
  - 摆法 `cup_found`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `kid_cup` 在其中任一处上：`bookcase_3/top`
        - `kid_cup` 立着
- **次好（0.6）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `kid_cup` 在其中任一处上：`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`desk_1/top`
      - `kid_cup` 立着
- **最不好（0.3）**：

    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
- **不行（0）**：床边没杯子；躺着；还拿着或掉了


**参考调用顺序**：

- 摆法 `cup_found`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `search(object=kid_cup, region=dining_room_0_1)` → 4. `navigate(destination=kid_cup)` → 5. `pick(object=kid_cup)` → 6. `navigate(destination=bookcase_3/top)` → 7. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.093, -4.837])`
- 摆法 `side_covered`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `search(object=kid_cup, region=dining_room_0_1)` → 4. `navigate(destination=kid_cup)` → 5. `pick(object=kid_cup)` → 6. `navigate(destination=bookcase_3/top)` → 7. `look(target=bookcase_3/top)` → 8. `navigate(destination=desk_1/top)` → 9. `place(object=kid_cup, receptacle=desk_1/top, hint_xy=[-0.168, -5.946])`

### already_there（Task）

**情况**：杯子已经在他床边 → 什么都不用做；床边那个是瓷杯、不是他的（他的塑料杯在台面）时把他的拿过来

**成功条件**（D 按摆法：`his_cup` D = 0、理想物在，`wrong_cup` D = 1、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `his_cup`：
    - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
    - `kid_cup` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
  - 摆法 `wrong_cup`：
    - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
    - `kid_cup` 立着
    - `bedside_cup` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
- **次好（0.6）**：

  - 摆法 `his_cup`：
    - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
    - 手里空着
  - 摆法 `wrong_cup`：
    - `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
    - `kid_cup` 立着
    - 手里空着
- **不行（0）**：把杯子拿走了；还拿着或掉了


**参考调用顺序**：

- 摆法 `his_cup`：1. `navigate(destination=bookcase_3/top)` → 2. `look(target=bookcase_3/top)`
- 摆法 `wrong_cup`：1. `navigate(destination=bookcase_3/top)` → 2. `look(target=bookcase_3/top)` → 3. `navigate(destination=kitchen_counter_2/top)` → 4. `look(target=kitchen_counter_2/top)` → 5. `navigate(destination=kid_cup)` → 6. `pick(object=kid_cup)` → 7. `navigate(destination=bookcase_3/top)` → 8. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[1.993, -4.837])`

---

## T29_clear_table_for_dinner

> 要吃饭了，把餐桌上不该放的东西拿走。

### car_on_table（对照）

**情况**：餐桌上一辆玩具车 → 放回客厅的玩具箱

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `table_car` 在 `toy_box` 里
  - 手里空着
- **次好（0.6）**：

  - 手里空着
  - `["not on", "table_car", "dining_table_2/top"]`
  - `table_car` 不在地上
- **不行（0）**：小车还在桌上；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=table_car)` → 4. `pick(object=table_car)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_box)` → 7. `place(object=table_car, receptacle=toy_box)`

### belongs_on_table（Task）

**情况**：桌上摆着碗和勺子（吃饭用的），有时还有一辆玩具车 → 吃饭用的留下，有玩具就拿回玩具箱（没有玩具箱就放电视柜上的托盘），没有就什么都不用做

**成功条件**（D 按摆法：`belongs_on_table` D = 1、理想物在，`no_toy_box` D = 1、理想物不在，`nothing_to_clear` D = 1、理想物在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `no_toy_box`：
    - `table_car` 在 `spare_tray` 里
    - `set_bowl`、`set_spoon` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
  - 摆法 `belongs_on_table`：
    - `table_car` 在 `toy_box` 里
    - `set_bowl`、`set_spoon` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
  - 摆法 `nothing_to_clear`：
    - `set_bowl`、`set_spoon` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
- **次好（0.6）**：

  - 摆法 `nothing_to_clear`：
    - 手里空着
    - `set_bowl` 在 `dining_table_2/top` 上
    - `set_spoon` 在 `dining_table_2/top` 上
  - 摆法 `no_toy_box`：
    - `table_car` 在 `spare_tray` 里
    - 手里空着
    - `set_bowl` 在 `dining_table_2/top` 上
    - `set_spoon` 在 `dining_table_2/top` 上
  - 摆法 `belongs_on_table`：
    - `table_car` 在 `toy_box` 里
    - 手里空着
    - `set_bowl` 在 `dining_table_2/top` 上
    - `set_spoon` 在 `dining_table_2/top` 上
- **最不好（0.3）**：

  - 摆法 `nothing_to_clear`：
    - 手里空着
  - 摆法 `no_toy_box`：
    - `table_car` 在 `spare_tray` 里
    - 手里空着
  - 摆法 `belongs_on_table`：
    - `table_car` 在 `toy_box` 里
    - 手里空着
- **不行（0）**：小车还在桌上；碰倒了；还拿着或掉了


**参考调用顺序**：

- 摆法 `belongs_on_table`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=table_car)` → 4. `pick(object=table_car)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_box)` → 7. `place(object=table_car, receptacle=toy_box)`
- 摆法 `no_toy_box`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=table_car)` → 4. `pick(object=table_car)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=spare_tray)` → 7. `place(object=table_car, receptacle=spare_tray)`
- 摆法 `nothing_to_clear`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)`

### homework_on_table（Task）

**情况**：作业本和铅笔 → 拿回书房书桌；书桌被别人的书摊满时放到他卧室的书桌或书架上（压在书上或挪书次好）

**成功条件**（D 按摆法：`desk_free` D = 1、理想物在，`desk_covered` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `desk_free`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `hw_notebook` 在 `desk_1/top` 上
        - `hw_pencil` 在 `desk_1/top` 上
  - 摆法 `desk_covered`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `hw_notebook` 在其中任一处上：`desk_3/top`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
        - `hw_pencil` 在其中任一处上：`desk_3/top`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
        - `desk_pencil` 没被挪动（离开局位置不超过 3 cm）
        - `homework` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_1` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_2` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_3` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_4` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_5` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_6` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_red` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_red_2` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_1` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_2` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_3` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_4` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_5` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_6` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_7` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_corner` 没被挪动（离开局位置不超过 3 cm）
        - `hw_paperback` 没被挪动（离开局位置不超过 3 cm）
        - `hw_pen` 没被挪动（离开局位置不超过 3 cm）
- **次好（0.6）**：

  - 摆法 `desk_free`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `["not on", "hw_notebook", "dining_table_2/top"]`
        - `hw_notebook` 不在地上
        - `["not on", "hw_pencil", "dining_table_2/top"]`
        - `hw_pencil` 不在地上
  - 摆法 `desk_covered`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `hw_notebook` 在其中任一处上：`desk_3/top`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
        - `hw_pencil` 在其中任一处上：`desk_3/top`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
      - 第 2 组：
        - `hw_notebook` 在 `desk_1/top` 上
        - `hw_pencil` 在 `desk_1/top` 上
        - `desk_pencil` 没被挪动（离开局位置不超过 3 cm）
        - `homework` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_1` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_2` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_3` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_4` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_5` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_6` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_red` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_red_2` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_1` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_2` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_3` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_4` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_5` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_6` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_7` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_corner` 没被挪动（离开局位置不超过 3 cm）
        - `hw_paperback` 没被挪动（离开局位置不超过 3 cm）
        - `hw_pen` 没被挪动（离开局位置不超过 3 cm）
- **最不好（0.3）**：

  - 摆法 `desk_free`：
    - 这个摆法没有这一档（理想的东西 / 位置不在或用不了）
  - 摆法 `desk_covered`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `hw_notebook` 在 `desk_1/top` 上
        - `hw_pencil` 在 `desk_1/top` 上
      - 第 2 组：
        - `["not on", "hw_notebook", "dining_table_2/top"]`
        - `hw_notebook` 不在地上
        - `["not on", "hw_pencil", "dining_table_2/top"]`
        - `hw_pencil` 不在地上
        - `desk_pencil` 没被挪动（离开局位置不超过 3 cm）
        - `homework` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_1` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_2` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_3` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_4` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_5` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_green_6` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_red` 没被挪动（离开局位置不超过 3 cm）
        - `hw_book_red_2` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_1` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_2` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_3` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_4` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_5` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_6` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_7` 没被挪动（离开局位置不超过 3 cm）
        - `hw_notebook_corner` 没被挪动（离开局位置不超过 3 cm）
        - `hw_paperback` 没被挪动（离开局位置不超过 3 cm）
        - `hw_pen` 没被挪动（离开局位置不超过 3 cm）
      - 第 3 组：
        - `["not on", "hw_notebook", "dining_table_2/top"]`
        - `hw_notebook` 不在地上
        - `["not on", "hw_pencil", "dining_table_2/top"]`
        - `hw_pencil` 不在地上
- **不行（0）**：作业还在桌上；还拿着或掉了


**参考调用顺序**：

- 摆法 `desk_free`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=hw_notebook)` → 4. `pick(object=hw_notebook)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=hw_notebook, receptacle=desk_1/top, hint_xy=[-0.708, -6.166])` → 7. `navigate(destination=hw_pencil)` → 8. `pick(object=hw_pencil)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=hw_pencil, receptacle=desk_1/top, hint_xy=[-0.188, -5.946])`
- 摆法 `desk_covered`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=hw_notebook)` → 4. `pick(object=hw_notebook)` → 5. `navigate(destination=desk_1/top)` → 6. `look(target=desk_1/top)` → 7. `navigate(destination=desk_3/top)` → 8. `place(object=hw_notebook, receptacle=desk_3/top, hint_xy=[6.194, -5.349])` → 9. `navigate(destination=hw_pencil)` → 10. `pick(object=hw_pencil)` → 11. `navigate(destination=desk_3/top)` → 12. `place(object=hw_pencil, receptacle=desk_3/top, hint_xy=[6.494, -5.369])`

### several（Task）

**情况**：玩具车、一本书、一个空罐子 → 玩具进玩具箱（没有玩具箱、小玩具盒满了时放旁边托盘），书放到任一书架上，空罐扔垃圾桶

**成功条件**（D 按摆法：`toy_box` D = 1、理想物在，`bin_full` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `bin_full`：
    - `table_car` 在 `spare_tray` 里
    - `empty_can` 在 `trash_can` 里
    - 手里空着
    - `bin_block_1` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_2` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_3` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_4` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_5` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_6` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_7` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_8` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_9` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_10` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_11` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_12` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_13` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_14` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_15` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_16` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_17` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_18` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_19` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_20` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_21` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_22` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_23` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_24` 完全在 `toy_bin` 里（没有露出边沿）
    - 满足下面任意一组：
      - 第 1 组：
        - `table_book` 在 `bookcase_1/top` 上
      - 第 2 组：
        - `table_book` 在 `bookcase_1/shelf_1` 上
      - 第 3 组：
        - `table_book` 在 `bookcase_1/shelf_0` 上
      - 第 4 组：
        - `table_book` 在 `bookcase_2/top` 上
      - 第 5 组：
        - `table_book` 在 `bookcase_2/shelf_1` 上
      - 第 6 组：
        - `table_book` 在 `bookcase_2/shelf_0` 上
      - 第 7 组：
        - `table_book` 在 `bookcase_3/top` 上
      - 第 8 组：
        - `table_book` 在 `bookcase_3/shelf_1` 上
      - 第 9 组：
        - `table_book` 在 `bookcase_3/shelf_0` 上
      - 第 10 组：
        - `table_book` 在 `bookcase_4/top` 上
      - 第 11 组：
        - `table_book` 在 `bookcase_4/shelf_1` 上
      - 第 12 组：
        - `table_book` 在 `bookcase_4/shelf_0` 上
      - 第 13 组：
        - `table_book` 在 `large_shelf_2/shelf_0` 上
      - 第 14 组：
        - `table_book` 在 `large_shelf_2/shelf_1` 上
      - 第 15 组：
        - `table_book` 在 `large_shelf_2/shelf_2` 上
      - 第 16 组：
        - `table_book` 在 `large_shelf_2/shelf_3` 上
  - 摆法 `toy_box`：
    - `table_car` 在 `toy_box` 里
    - `empty_can` 在 `trash_can` 里
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `table_book` 在 `bookcase_1/top` 上
      - 第 2 组：
        - `table_book` 在 `bookcase_1/shelf_1` 上
      - 第 3 组：
        - `table_book` 在 `bookcase_1/shelf_0` 上
      - 第 4 组：
        - `table_book` 在 `bookcase_2/top` 上
      - 第 5 组：
        - `table_book` 在 `bookcase_2/shelf_1` 上
      - 第 6 组：
        - `table_book` 在 `bookcase_2/shelf_0` 上
      - 第 7 组：
        - `table_book` 在 `bookcase_3/top` 上
      - 第 8 组：
        - `table_book` 在 `bookcase_3/shelf_1` 上
      - 第 9 组：
        - `table_book` 在 `bookcase_3/shelf_0` 上
      - 第 10 组：
        - `table_book` 在 `bookcase_4/top` 上
      - 第 11 组：
        - `table_book` 在 `bookcase_4/shelf_1` 上
      - 第 12 组：
        - `table_book` 在 `bookcase_4/shelf_0` 上
      - 第 13 组：
        - `table_book` 在 `large_shelf_2/shelf_0` 上
      - 第 14 组：
        - `table_book` 在 `large_shelf_2/shelf_1` 上
      - 第 15 组：
        - `table_book` 在 `large_shelf_2/shelf_2` 上
      - 第 16 组：
        - `table_book` 在 `large_shelf_2/shelf_3` 上
- **次好（0.6）**：

  - 摆法 `bin_full`：
    - `table_car` 在 `spare_tray` 里
    - `empty_can` 在 `trash_can` 里
    - 手里空着
    - `bin_block_1` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_2` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_3` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_4` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_5` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_6` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_7` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_8` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_9` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_10` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_11` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_12` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_13` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_14` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_15` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_16` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_17` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_18` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_19` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_20` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_21` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_22` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_23` 完全在 `toy_bin` 里（没有露出边沿）
    - `bin_block_24` 完全在 `toy_bin` 里（没有露出边沿）
    - `["not on", "table_book", "dining_table_2/top"]`
    - `table_book` 不在地上
  - 摆法 `toy_box`：
    - `table_car` 在 `toy_box` 里
    - `empty_can` 在 `trash_can` 里
    - 手里空着
    - `["not on", "table_book", "dining_table_2/top"]`
    - `table_book` 不在地上
- **最不好（0.3）**：

  - `["not on", "table_car", "dining_table_2/top"]`
  - `table_car` 不在地上
  - `["not on", "empty_can", "dining_table_2/top"]`
  - `empty_can` 不在地上
  - `["not on", "table_book", "dining_table_2/top"]`
  - `table_book` 不在地上
  - 手里空着
- **不行（0）**：有东西还在桌上；还拿着或掉了


**参考调用顺序**：

- 摆法 `toy_box`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=table_car)` → 4. `pick(object=table_car)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_box)` → 7. `place(object=table_car, receptacle=toy_box)` → 8. `navigate(destination=empty_can)` → 9. `pick(object=empty_can)` → 10. `navigate(destination=trash_can)` → 11. `drop(object=empty_can, container=trash_can)` → 12. `navigate(destination=table_book)` → 13. `pick(object=table_book)` → 14. `navigate(destination=bookcase_2/top)` → 15. `place(object=table_book, receptacle=bookcase_2/top, hint_xy=[1.005, -0.479])`
- 摆法 `bin_full`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=table_car)` → 4. `pick(object=table_car)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_bin)` → 7. `measure(object=toy_bin)` → 8. `place(object=table_car, receptacle=spare_tray)` → 9. `navigate(destination=empty_can)` → 10. `pick(object=empty_can)` → 11. `navigate(destination=trash_can)` → 12. `drop(object=empty_can, container=trash_can)` → 13. `navigate(destination=table_book)` → 14. `pick(object=table_book)` → 15. `navigate(destination=bookcase_2/top)` → 16. `place(object=table_book, receptacle=bookcase_2/top, hint_xy=[1.005, -0.479])`

### which_table（Task）

**情况**：两张桌上各有个玩具，汤锅在其中一张 → 只清要吃饭的那张

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `east`：
    - `toy_east` 在 `toy_box` 里
    - `toy_west` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
  - 摆法 `west`：
    - `toy_west` 在 `toy_box` 里
    - `toy_east` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
- **次好（0.6）**：

  - 摆法 `east`：
    - `toy_east` 在 `toy_box` 里
    - 手里空着
  - 摆法 `west`：
    - `toy_west` 在 `toy_box` 里
    - 手里空着
- **不行（0）**：有汤那张的玩具没收；还拿着或掉了


**参考调用顺序**：

- 摆法 `east`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=dining_table_1/top)` → 4. `look(target=dining_table_1/top)` → 5. `navigate(destination=toy_east)` → 6. `pick(object=toy_east)` → 7. `explore_room(room=living_room_0_0)` → 8. `navigate(destination=toy_box)` → 9. `place(object=toy_east, receptacle=toy_box)`
- 摆法 `west`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=dining_table_1/top)` → 4. `look(target=dining_table_1/top)` → 5. `navigate(destination=toy_west)` → 6. `pick(object=toy_west)` → 7. `explore_room(room=living_room_0_0)` → 8. `navigate(destination=toy_box)` → 9. `place(object=toy_west, receptacle=toy_box)`

---

## T30_bowls_for_soup

> 汤快好了，拿碗过来准备盛。

### bowl_on_cabinet（对照）

**情况**：靠墙矮柜上一个干净碗 → 拿到岛台

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 这 5 件中至少 1 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
  - 手里空着
- **不行（0）**：岛台上没碗；碗掉了；还拿着


**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=soup_bowl_1)` → 4. `pick(object=soup_bowl_1)` → 5. `navigate(destination=kitchen_island/top)` → 6. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[8.06, 1.675])`

### how_many（Task）

**情况**：餐桌上摆了三把勺子 → 拿三个碗；只有两个碗时第三个用马克杯

**成功条件**（D 按摆法：`three_bowls` D = 1、理想物在，`two_bowls` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `three_bowls`：
    - 这 7 件中至少 3 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`、`soup_bowl_3`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
    - 手里空着
  - 摆法 `two_bowls`：
    - 这 2 件中至少 2 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`
    - 这 9 件中至少 3 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`、`spare_mug`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 手里空着
- **不行（0）**：不到三个；碗掉了；还拿着


**参考调用顺序**：

- 摆法 `three_bowls`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `navigate(destination=soup_bowl_1)` → 6. `pick(object=soup_bowl_1)` → 7. `navigate(destination=kitchen_island/top)` → 8. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[7.66, 1.675])` → 9. `navigate(destination=soup_bowl_2)` → 10. `pick(object=soup_bowl_2)` → 11. `navigate(destination=kitchen_island/top)` → 12. `place(object=soup_bowl_2, receptacle=kitchen_island/top, hint_xy=[7.86, 1.675])` → 13. `navigate(destination=soup_bowl_3)` → 14. `pick(object=soup_bowl_3)` → 15. `navigate(destination=kitchen_island/top)` → 16. `place(object=soup_bowl_3, receptacle=kitchen_island/top, hint_xy=[8.06, 1.675])`
- 摆法 `two_bowls`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `navigate(destination=soup_bowl_1)` → 6. `pick(object=soup_bowl_1)` → 7. `navigate(destination=kitchen_island/top)` → 8. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[7.66, 1.675])` → 9. `navigate(destination=soup_bowl_2)` → 10. `pick(object=soup_bowl_2)` → 11. `navigate(destination=kitchen_island/top)` → 12. `place(object=soup_bowl_2, receptacle=kitchen_island/top, hint_xy=[7.86, 1.675])` → 13. `navigate(destination=spare_mug)` → 14. `pick(object=spare_mug)` → 15. `navigate(destination=kitchen_island/top)` → 16. `place(object=spare_mug, receptacle=kitchen_island/top, hint_xy=[8.06, 1.655])`

### bowls_in_cabinet（Task）

**情况**：“汤快好了，拿碗过来准备盛。”餐桌摆了三把勺子；矮柜上一个碗和一个马克杯；柜里还有两个碗，或者只有一个；家里没有别的碗 → 要三个 → 外面只有一个，打开柜子 → 两个碗：拿三个碗；一个碗：两碗不够，自己想到马克杯也能盛汤（盘子不行），补上马克杯，关门

**成功条件**（D 按摆法：`two_inside` D = 1、理想物在，`one_inside` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `two_inside`：
    - 这 3 件中至少 3 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`、`soup_bowl_3`
    - `kitchen_cabinet_6` 关着
    - 手里空着
  - 摆法 `one_inside`：
    - 这 2 件中至少 2 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`
    - 这 9 件中至少 3 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`、`spare_mug`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - `kitchen_cabinet_6` 关着
    - 手里空着
- **次好（0.6）**：

  - 摆法 `two_inside`：
    - 这 3 件中至少 3 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`、`soup_bowl_3`
    - 手里空着
  - 摆法 `one_inside`：
    - 这 2 件中至少 2 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`
    - 这 9 件中至少 3 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`、`spare_mug`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 手里空着
- **最不好（0.3）**：

  - 摆法 `two_inside`：
    - 这 4 件中至少 3 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`、`soup_bowl_3`、`spare_mug`
    - 手里空着
  - 摆法 `one_inside`：
    - 这 2 件中至少 2 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`
    - 这 9 件中至少 3 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`、`spare_mug`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - `kitchen_cabinet_6` 关着
    - 手里空着
- **不行（0）**：不到三个；掉了；还拿着


**参考调用顺序**：

- 摆法 `two_inside`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `navigate(destination=soup_bowl_1)` → 6. `pick(object=soup_bowl_1)` → 7. `navigate(destination=kitchen_island/top)` → 8. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[7.66, 1.675])` → 9. `navigate(destination=kitchen_cabinet_6)` → 10. `open(articulated=kitchen_cabinet_6)` → 11. `bend()` → 12. `explore_furniture(furniture=kitchen_cabinet_6)` → 13. `straighten()` → 14. `navigate(destination=soup_bowl_2)` → 15. `pick(object=soup_bowl_2)` → 16. `navigate(destination=kitchen_island/top)` → 17. `place(object=soup_bowl_2, receptacle=kitchen_island/top, hint_xy=[7.86, 1.675])` → 18. `navigate(destination=soup_bowl_3)` → 19. `pick(object=soup_bowl_3)` → 20. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 21. `navigate(destination=kitchen_island/top)` → 22. `place(object=soup_bowl_3, receptacle=kitchen_island/top, hint_xy=[8.06, 1.675])` → 23. `navigate(destination=kitchen_cabinet_6)` → 24. `close(articulated=kitchen_cabinet_6)`
- 摆法 `one_inside`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `navigate(destination=soup_bowl_1)` → 6. `pick(object=soup_bowl_1)` → 7. `navigate(destination=kitchen_island/top)` → 8. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[7.66, 1.675])` → 9. `navigate(destination=kitchen_cabinet_6)` → 10. `open(articulated=kitchen_cabinet_6)` → 11. `bend()` → 12. `explore_furniture(furniture=kitchen_cabinet_6)` → 13. `straighten()` → 14. `navigate(destination=soup_bowl_2)` → 15. `pick(object=soup_bowl_2)` → 16. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 17. `navigate(destination=kitchen_island/top)` → 18. `place(object=soup_bowl_2, receptacle=kitchen_island/top, hint_xy=[7.86, 1.675])` → 19. `navigate(destination=kitchen_cabinet_6)` → 20. `close(articulated=kitchen_cabinet_6)` → 21. `navigate(destination=spare_mug)` → 22. `pick(object=spare_mug)` → 23. `navigate(destination=kitchen_island/top)` → 24. `place(object=spare_mug, receptacle=kitchen_island/top, hint_xy=[8.06, 1.655])`

### bowl_put_away（Task）

**情况**：碗收在矮柜里 → 打开找，拿出来关好；柜里只有盘子和马克杯时拿马克杯（不拿盘子）

**成功条件**（D 按摆法：`bowl_inside` D = 1、理想物在，`mug_inside` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `bowl_inside`：
    - 这 5 件中至少 1 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
    - `kitchen_cabinet_4` 关着
    - 手里空着
  - 摆法 `mug_inside`：
    - 这 7 件中至少 1 件还在 `kitchen_island/top` 上：`stored_mug`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - `kitchen_cabinet_4` 关着
    - 手里空着
- **次好（0.6）**：

  - 摆法 `bowl_inside`：
    - 这 5 件中至少 1 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
    - 手里空着
  - 摆法 `mug_inside`：
    - 这 7 件中至少 1 件还在 `kitchen_island/top` 上：`stored_mug`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
    - 手里空着
- **不行（0）**：岛台上没碗；碗掉了；还拿着


**参考调用顺序**：

- 摆法 `bowl_inside`：1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `navigate(destination=soup_bowl_1)` → 7. `pick(object=soup_bowl_1)` → 8. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 9. `navigate(destination=kitchen_island/top)` → 10. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[8.06, 1.675])` → 11. `navigate(destination=kitchen_cabinet_4)` → 12. `close(articulated=kitchen_cabinet_4)`
- 摆法 `mug_inside`：1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `navigate(destination=stored_mug)` → 7. `pick(object=stored_mug)` → 8. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 9. `navigate(destination=kitchen_island/top)` → 10. `place(object=stored_mug, receptacle=kitchen_island/top, hint_xy=[8.06, 1.655])` → 11. `navigate(destination=kitchen_cabinet_4)` → 12. `close(articulated=kitchen_cabinet_4)`

### no_bowl（Task）

**情况**：家里没有干净碗了，柜上有马克杯和盘子 → 拿马克杯（能盛汤）

**成功条件**（D 按摆法：`no_bowl` D = 1、理想物不在；理想物不在的摆法里，能做到的最好结果算好，往下依次次好、最不好；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 这 7 件中至少 1 件还在 `kitchen_island/top` 上：`spare_mug`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
  - 手里空着
- **最不好（0.3）**：

  - `spare_plate` 在 `kitchen_island/top` 上
  - 手里空着
- **不行（0）**：什么都没拿；掉了；还拿着


**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=spare_mug)` → 4. `pick(object=spare_mug)` → 5. `navigate(destination=kitchen_island/top)` → 6. `place(object=spare_mug, receptacle=kitchen_island/top, hint_xy=[8.06, 1.655])`

### bowl_not_plate（Task）

**情况**：干净碗旁边放着不能用来盛汤的东西：一个盘子，或者一碗还装着燕麦的碗 → 拿那个干净的空碗，别的不动

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 摆法 `clean_one`：
    - 这 5 件中至少 1 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
    - `full_bowl` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
  - 摆法 `bowl_not_plate`：
    - 这 5 件中至少 1 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
    - `spare_plate` 没被挪动（离开局位置不超过 3 cm）
    - 手里空着
- **次好（0.6）**：

  - 这 5 件中至少 1 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
  - 手里空着
- **最不好（0.3）**：

  - 摆法 `clean_one`：
    - `full_bowl` 在 `kitchen_island/top` 上
    - 手里空着
  - 摆法 `bowl_not_plate`：
    - `spare_plate` 在 `kitchen_island/top` 上
    - 手里空着
- **不行（0）**：什么都没拿；掉了；还拿着


**参考调用顺序**：

- 摆法 `bowl_not_plate`：1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=soup_bowl_1)` → 4. `pick(object=soup_bowl_1)` → 5. `navigate(destination=kitchen_island/top)` → 6. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[8.06, 1.675])`
- 摆法 `clean_one`：1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=soup_bowl_1)` → 4. `pick(object=soup_bowl_1)` → 5. `navigate(destination=kitchen_island/top)` → 6. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[8.06, 1.675])`

