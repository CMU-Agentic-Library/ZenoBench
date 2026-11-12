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

**情况**：岛台上有一本书（不是要找的）；指令说客人昨晚在哪个房间看书（客厅看电视时，或卧室睡前），书就留在那里；另一个房间也有一本别的书 → 不拿眼前岛台上的书，去指令说的房间拿那本，送到餐桌；岛台上和另一个房间的书都不动

**指令**：客人想吃早饭时接着看昨晚在客厅读的那本书，帮忙拿到餐桌上。其他东西别动。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `paperback_book` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
  - `book_island`、`book_other` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- **最不好（0.3）**：

  - `paperback_book` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
  - 手里空着
- **不行（0）**：客人那本没到餐桌（拿错或没拿）；还拿在手里


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

**成功条件**（D = 1；以下各档都算成功，分数不同）：

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

**成功条件**（D = 1；以下各档都算成功，分数不同）：

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

**情况**：孩子想在餐桌上看积木塔；三块积木分散在岛台、客厅电视柜和另一间房的桌上（开局看不到）；餐桌上有储物箱、两盒麦片和勺子 → 找全三块，一只手往返三趟、安排先后；第一块放在餐桌上离边缘至少 5 cm、不贴着储物箱和麦片的空处当底座，再叠另外两块；桌上原有东西不动

**指令**：孩子想在餐桌上看积木塔。把家里三块积木都找到，在餐桌上叠成一座塔。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_b` 叠在 `wooden_block_a` 上
      - `floor_block` 叠在 `wooden_block_b` 上
      - `wooden_block_a` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
      - `wooden_block_a` 离台面边缘至少 5 cm
      - `wooden_block_a` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
    - 第 2 组：
      - `floor_block` 叠在 `wooden_block_a` 上
      - `wooden_block_b` 叠在 `floor_block` 上
      - `wooden_block_a` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
      - `wooden_block_a` 离台面边缘至少 5 cm
      - `wooden_block_a` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
    - 第 3 组：
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `floor_block` 叠在 `wooden_block_a` 上
      - `wooden_block_b` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
      - `wooden_block_b` 离台面边缘至少 5 cm
      - `wooden_block_b` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
    - 第 4 组：
      - `floor_block` 叠在 `wooden_block_b` 上
      - `wooden_block_a` 叠在 `floor_block` 上
      - `wooden_block_b` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
      - `wooden_block_b` 离台面边缘至少 5 cm
      - `wooden_block_b` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
    - 第 5 组：
      - `wooden_block_a` 叠在 `floor_block` 上
      - `wooden_block_b` 叠在 `wooden_block_a` 上
      - `floor_block` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
      - `floor_block` 离台面边缘至少 5 cm
      - `floor_block` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
    - 第 6 组：
      - `wooden_block_b` 叠在 `floor_block` 上
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `floor_block` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
      - `floor_block` 离台面边缘至少 5 cm
      - `floor_block` 离这些东西都至少 5 cm：`wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
- **最不好（0.3）**：

  - `wide_storage_bin`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_b` 叠在 `wooden_block_a` 上
      - `floor_block` 叠在 `wooden_block_b` 上
      - `wooden_block_a` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
    - 第 2 组：
      - `floor_block` 叠在 `wooden_block_a` 上
      - `wooden_block_b` 叠在 `floor_block` 上
      - `wooden_block_a` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
    - 第 3 组：
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `floor_block` 叠在 `wooden_block_a` 上
      - `wooden_block_b` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
    - 第 4 组：
      - `floor_block` 叠在 `wooden_block_b` 上
      - `wooden_block_a` 叠在 `floor_block` 上
      - `wooden_block_b` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
    - 第 5 组：
      - `wooden_block_a` 叠在 `floor_block` 上
      - `wooden_block_b` 叠在 `wooden_block_a` 上
      - `floor_block` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
    - 第 6 组：
      - `wooden_block_b` 叠在 `floor_block` 上
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `floor_block` 在其中任一处上：`dining_table_2/top`、`dining_table_1/top`
- **不行（0）**：只叠了两块（没找齐）；挪了桌上的东西；塔不在餐桌上；没叠上


**参考调用顺序**：

- 摆法 `counter`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=wooden_block_a, receptacle=dining_table_2/top, hint_xy=[3.7, 6.6])` → 8. `search(object=wooden_block_b, region=living_room_0_0)` → 9. `navigate(destination=wooden_block_b)` → 10. `pick(object=wooden_block_b)` → 11. `navigate(destination=wooden_block_a)` → 12. `stack(object=wooden_block_b, base=wooden_block_a)` → 13. `search(object=floor_block, region=kitchen_0_1)` → 14. `navigate(destination=floor_block)` → 15. `pick(object=floor_block)` → 16. `navigate(destination=wooden_block_a)` → 17. `stack(object=floor_block, base=wooden_block_b)`
- 摆法 `study`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `place(object=wooden_block_a, receptacle=dining_table_2/top, hint_xy=[3.7, 6.6])` → 8. `search(object=floor_block, region=living_room_0_0)` → 9. `navigate(destination=floor_block)` → 10. `pick(object=floor_block)` → 11. `navigate(destination=wooden_block_a)` → 12. `stack(object=floor_block, base=wooden_block_a)` → 13. `search(object=wooden_block_b, region=living_room_0_1)` → 14. `navigate(destination=wooden_block_b)` → 15. `pick(object=wooden_block_b)` → 16. `navigate(destination=wooden_block_a)` → 17. `stack(object=wooden_block_b, base=floor_block)`

### tower_for_kid_duck（Task）

**情况**：指令只说“孩子想在餐桌上看一座三层的塔，用他的玩具在餐桌上搭一座”；家里只有两块积木（岛台一块，电视柜或书房书桌一块），小黄鸭在别处 → 找到两块后发现不够三层，自己想到用别的玩具补；鸭子没有平顶，只能放最上面，所以最后拿；底座离桌边至少 5 cm、不贴着桌上的东西

**指令**：孩子想在餐桌上看一座三层的塔，用他的玩具在餐桌上搭一座。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

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

**情况**：“把三块积木在岛台上叠成一座塔。有一块我收进客厅靠墙的矮柜里了，找完把柜门关好”：岛台上两块，一块在边上不能当底座 → 原地把边上那块叠到另一块上（Action），再逐个打开矮柜找第三块，叠到最上面（Task），柜门都关好

**指令**：把三块积木在岛台上叠成一座塔。有一块我收进客厅靠墙的矮柜里了，找完把柜门关好。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **次好（0.6）**：

  - 手里空着
  - `kitchen_cabinet_4` 关着
  - `kitchen_cabinet_6` 关着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `floor_block` 叠在 `wooden_block_a` 上
      - `wooden_block_b` 在 `kitchen_island/top` 上
    - 第 2 组：
      - `floor_block` 叠在 `wooden_block_b` 上
      - `wooden_block_a` 叠在 `floor_block` 上
      - `wooden_block_b` 在 `kitchen_island/top` 上
    - 第 3 组：
      - `wooden_block_a` 叠在 `floor_block` 上
      - `wooden_block_b` 叠在 `wooden_block_a` 上
      - `floor_block` 在 `kitchen_island/top` 上
    - 第 4 组：
      - `wooden_block_b` 叠在 `floor_block` 上
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `floor_block` 在 `kitchen_island/top` 上
- **最不好（0.3）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `floor_block` 叠在 `wooden_block_a` 上
      - `wooden_block_b` 在 `kitchen_island/top` 上
    - 第 2 组：
      - `floor_block` 叠在 `wooden_block_b` 上
      - `wooden_block_a` 叠在 `floor_block` 上
      - `wooden_block_b` 在 `kitchen_island/top` 上
    - 第 3 组：
      - `wooden_block_a` 叠在 `floor_block` 上
      - `wooden_block_b` 叠在 `wooden_block_a` 上
      - `floor_block` 在 `kitchen_island/top` 上
    - 第 4 组：
      - `wooden_block_b` 叠在 `floor_block` 上
      - `wooden_block_a` 叠在 `wooden_block_b` 上
      - `floor_block` 在 `kitchen_island/top` 上
- **不行（0）**：只叠了两块（没找到第三块）；没叠上；积木掉了


**参考调用顺序**：

- 摆法 `in_4`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)`（换做法） → 5. `navigate(destination=wooden_block_b)` → 6. `stack(object=wooden_block_a, base=wooden_block_b)`（换做法） → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `close(articulated=kitchen_cabinet_6)` → 13. `navigate(destination=kitchen_cabinet_4)` → 14. `open(articulated=kitchen_cabinet_4)` → 15. `bend()` → 16. `explore_furniture(furniture=kitchen_cabinet_4)` → 17. `straighten()` → 18. `navigate(destination=floor_block)` → 19. `pick(object=floor_block)` → 20. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 21. `navigate(destination=wooden_block_a)` → 22. `stack(object=floor_block, base=wooden_block_a)` → 23. `navigate(destination=kitchen_cabinet_4)` → 24. `close(articulated=kitchen_cabinet_4)`
- 摆法 `in_6`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)`（换做法） → 5. `navigate(destination=wooden_block_b)` → 6. `stack(object=wooden_block_a, base=wooden_block_b)`（换做法） → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `close(articulated=kitchen_cabinet_4)` → 13. `navigate(destination=kitchen_cabinet_6)` → 14. `open(articulated=kitchen_cabinet_6)` → 15. `bend()` → 16. `explore_furniture(furniture=kitchen_cabinet_6)` → 17. `straighten()` → 18. `navigate(destination=floor_block)` → 19. `pick(object=floor_block)` → 20. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 21. `navigate(destination=wooden_block_a)` → 22. `stack(object=floor_block, base=wooden_block_a)` → 23. `navigate(destination=kitchen_cabinet_6)` → 24. `close(articulated=kitchen_cabinet_6)`

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

**情况**：岛台上餐具旁边有个小储物箱（22 × 17 cm），里面已经放了两块积木：勺子还放得下，22 cm 的擀面杖平放、斜放都放不进；宽储物箱在卧室矮书架上 → 看剩下的空间判断放不下，两样要放同一个容器，所以都拿去卧室的宽箱；小箱里的积木不动。小箱在岛台上时开局就在眼前，还没见到别的容器就得先排除它

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `rolling_pin` 在 `wide_storage_bin` 里
  - `breakfast_spoon` 在 `wide_storage_bin` 里
  - 手里空着
  - `small_bin_block_1` 在 `small_storage_bin` 里
  - `small_bin_block_2` 在 `small_storage_bin` 里
- **次好（0.6）**：

  - `rolling_pin` 在 `small_storage_bin` 里
  - `breakfast_spoon` 在 `small_storage_bin` 里
  - `small_bin_block_1` 在 `small_storage_bin` 里
  - `small_bin_block_2` 在 `small_storage_bin` 里
  - 手里空着
- **最不好（0.3）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `rolling_pin` 在 `wide_storage_bin` 里
      - `breakfast_spoon` 在 `wide_storage_bin` 里
    - 第 2 组：
      - `rolling_pin` 在 `small_storage_bin` 里
      - `breakfast_spoon` 在 `small_storage_bin` 里
- **不行（0）**：两样不在同一个容器；插进马克杯；只收了一样；把小箱子整个放进大箱子；还拿在手里


**参考调用顺序**：

- 摆法 `on_island`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `measure(object=small_storage_bin)` → 4. `measure(object=rolling_pin)` → 5. `search(object=wide_storage_bin, region=bedroom_0_1)` → 6. `navigate(destination=bookcase_2/top)` → 7. `look(target=bookcase_2/top)` → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=wide_storage_bin)` → 11. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 12. `navigate(destination=rolling_pin)` → 13. `pick(object=rolling_pin)` → 14. `navigate(destination=wide_storage_bin)` → 15. `place(object=rolling_pin, receptacle=wide_storage_bin)`
- 摆法 `beside_wide_bin`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=wide_storage_bin, region=bedroom_0_1)` → 4. `navigate(destination=bookcase_2/top)` → 5. `look(target=bookcase_2/top)` → 6. `measure(object=small_storage_bin)` → 7. `measure(object=rolling_pin)` → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=wide_storage_bin)` → 11. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 12. `navigate(destination=rolling_pin)` → 13. `pick(object=rolling_pin)` → 14. `navigate(destination=wide_storage_bin)` → 15. `place(object=rolling_pin, receptacle=wide_storage_bin)`

### which_bin_by_contents（Task）

**情况**：客厅电视柜和卧室矮书架上各有一个一样的宽箱：玩具箱里是孩子的两块积木，厨房用具箱里是两把勺子；指令说收进放厨房用具的那个箱子 → 往近的箱子里看，是玩具箱就去另一个房间找厨房用具箱，把两样都放进去；箱子里原有的东西不动

**指令**：烘焙结束了，把擀面杖和勺子一起收进放厨房用具的那个箱子里。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `rolling_pin` 在 `wide_storage_bin` 里
  - `breakfast_spoon` 在 `wide_storage_bin` 里
  - `toy_bin_block_1` 在 `toy_storage_bin` 里
  - `toy_bin_block_2` 在 `toy_storage_bin` 里
  - `spoon_counter` 在 `wide_storage_bin` 里
  - `spoon_side_table` 在 `wide_storage_bin` 里
  - 手里空着
- **次好（0.6）**：

  - `rolling_pin` 在 `wide_storage_bin` 里
  - `breakfast_spoon` 在 `wide_storage_bin` 里
  - 手里空着
- **最不好（0.3）**：

  - `rolling_pin` 在 `toy_storage_bin` 里
  - `breakfast_spoon` 在 `toy_storage_bin` 里
  - `toy_bin_block_1` 在 `toy_storage_bin` 里
  - `toy_bin_block_2` 在 `toy_storage_bin` 里
  - `spoon_counter` 在 `wide_storage_bin` 里
  - `spoon_side_table` 在 `wide_storage_bin` 里
  - 手里空着
- **不行（0）**：放进玩具箱且动了里面的积木或勺子；两样分在两个箱子；只收了一样；还拿着或掉了


**参考调用顺序**：

- 摆法 `toys_near`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `search(object=wide_storage_bin, region=bedroom_0_1)` → 6. `navigate(destination=bookcase_2/top)` → 7. `look(target=bookcase_2/top)` → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=wide_storage_bin)` → 11. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 12. `navigate(destination=rolling_pin)` → 13. `pick(object=rolling_pin)` → 14. `navigate(destination=wide_storage_bin)` → 15. `place(object=rolling_pin, receptacle=wide_storage_bin)`
- 摆法 `tools_near`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=breakfast_spoon)` → 6. `pick(object=breakfast_spoon)` → 7. `navigate(destination=wide_storage_bin)` → 8. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 9. `navigate(destination=rolling_pin)` → 10. `pick(object=rolling_pin)` → 11. `navigate(destination=wide_storage_bin)` → 12. `place(object=rolling_pin, receptacle=wide_storage_bin)`

### no_bin_substitute（Task）

**情况**：家里没有储物箱；电视柜上的小箱（22 × 17 cm，里面有两块积木）放不下 22 cm 的擀面杖；餐桌上的果篮够大但装着苹果和橙子；指令只说收进一个容器 → 排除小箱，不用果篮，去别的房间找替代品，两样都放进去

**指令**：烘焙结束了，把擀面杖和勺子一起收进一个容器里。

**成功条件**（D = 1；以下各档都算成功，分数不同）：

- **好（1.0）**：

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
- **次好（0.6）**：

  - 摆法 `tray`：
    - 手里空着
    - 满足下面任意一组：
      - 第 1 组：
        - `rolling_pin` 在 `serving_tray` 里
        - `breakfast_spoon` 在 `serving_tray` 里
      - 第 2 组：
        - `rolling_pin` 在 `small_storage_bin` 里
        - `breakfast_spoon` 在 `small_storage_bin` 里
        - `small_bin_block_1` 在 `small_storage_bin` 里
        - `small_bin_block_2` 在 `small_storage_bin` 里
        - `apple` 在 `fruit_basket` 里
        - `orange` 在 `fruit_basket` 里
  - 摆法 `basket`：
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
        - `apple` 在 `fruit_basket` 里
        - `orange` 在 `fruit_basket` 里
- **最不好（0.3）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `rolling_pin` 在 `small_storage_bin` 里
      - `breakfast_spoon` 在 `small_storage_bin` 里
    - 第 2 组：
      - `rolling_pin` 在 `fruit_basket` 里
      - `breakfast_spoon` 在 `fruit_basket` 里
- **不行（0）**：两样分在两个容器；只收了一样；放进柜子或抽屉；还拿着或掉了


**参考调用顺序**：

- 摆法 `basket`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `measure(object=rolling_pin)` → 4. `look(target=tv_stand_2/top)` → 5. `measure(object=small_storage_bin)` → 6. `explore_room(room=bedroom_0_1)` → 7. `navigate(destination=storage_basket)` → 8. `look(target=storage_basket)` → 9. `navigate(destination=breakfast_spoon)` → 10. `pick(object=breakfast_spoon)` → 11. `navigate(destination=storage_basket)` → 12. `drop(object=breakfast_spoon, container=storage_basket)` → 13. `navigate(destination=rolling_pin)` → 14. `pick(object=rolling_pin)` → 15. `navigate(destination=storage_basket)` → 16. `place(object=rolling_pin, receptacle=storage_basket)`
- 摆法 `tray`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `measure(object=rolling_pin)` → 4. `look(target=tv_stand_2/top)` → 5. `measure(object=small_storage_bin)` → 6. `search(object=serving_tray, region=living_room_0_1)` → 7. `navigate(destination=serving_tray)` → 8. `look(target=serving_tray)` → 9. `navigate(destination=breakfast_spoon)` → 10. `pick(object=breakfast_spoon)` → 11. `navigate(destination=serving_tray)` → 12. `place(object=breakfast_spoon, receptacle=serving_tray)` → 13. `navigate(destination=rolling_pin)` → 14. `pick(object=rolling_pin)` → 15. `navigate(destination=serving_tray)` → 16. `place(object=rolling_pin, receptacle=serving_tray)`

### utensils_apart（Task）

**情况**：擀面杖在岛台上，勺子落在了别的房间（开局看不到），宽箱在卧室矮书架上 → 找到箱子和勺子，一只手分两趟：先送擀面杖，再去拿勺子

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - `rolling_pin` 在 `wide_storage_bin` 里
  - `breakfast_spoon` 在 `wide_storage_bin` 里
  - 手里空着
- **不行（0）**：只收了一样（勺子没找到）；放进柜子、抽屉或随手放桌上；还拿着或掉了


**参考调用顺序**：

- 摆法 `dining`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=wide_storage_bin, region=bedroom_0_1)` → 4. `navigate(destination=bookcase_2/top)` → 5. `look(target=bookcase_2/top)` → 6. `navigate(destination=rolling_pin)` → 7. `pick(object=rolling_pin)` → 8. `navigate(destination=wide_storage_bin)` → 9. `place(object=rolling_pin, receptacle=wide_storage_bin)` → 10. `search(object=breakfast_spoon, region=dining_room_0_1)` → 11. `navigate(destination=breakfast_spoon)` → 12. `pick(object=breakfast_spoon)` → 13. `navigate(destination=wide_storage_bin)` → 14. `drop(object=breakfast_spoon, container=wide_storage_bin)`
- 摆法 `counter`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=wide_storage_bin, region=bedroom_0_1)` → 4. `navigate(destination=bookcase_2/top)` → 5. `look(target=bookcase_2/top)` → 6. `navigate(destination=rolling_pin)` → 7. `pick(object=rolling_pin)` → 8. `navigate(destination=wide_storage_bin)` → 9. `place(object=rolling_pin, receptacle=wide_storage_bin)` → 10. `search(object=breakfast_spoon, region=kitchen_0_1)` → 11. `navigate(destination=breakfast_spoon)` → 12. `pick(object=breakfast_spoon)` → 13. `navigate(destination=wide_storage_bin)` → 14. `drop(object=breakfast_spoon, container=wide_storage_bin)`

---

## T04_cup_or_mug_to_cabinet

> 有客人要来，在靠墙矮柜上的饮品角摆一个杯子。

### cup_available（对照）

**情况**：岛台上有杯子 → 拿到饮品角

**成功条件**（D = 0；以下各档都算成功，分数不同）：

- **好（1.0）**：

  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
      - `cup_counter_b` 立着
    - 第 2 组：
      - `mug` 在 `kitchen_cabinet_6/top` 上
      - `mug` 立着
    - 第 3 组：
      - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
      - `mug_dining_cabinet` 立着
    - 第 4 组：
      - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
      - `mug_shelf` 立着
    - 第 5 组：
      - `mug_counter` 在 `kitchen_cabinet_6/top` 上
      - `mug_counter` 立着
- **不行（0）**：杯子倒着或躺着；放到别的柜子、台面或餐桌；还拿着或掉了


**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=cup_counter_b)` → 4. `pick(object=cup_counter_b)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)`

### no_cup（Task）

**情况**：家里没有杯子 → 用马克杯代替；马克杯不在眼前时先去找

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
    - `cup_counter_b` 立着
  - 第 2 组：
    - `mug` 在 `kitchen_cabinet_6/top` 上
    - `mug` 立着
  - 第 3 组：
    - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
    - `mug_dining_cabinet` 立着
  - 第 4 组：
    - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
    - `mug_shelf` 立着
  - 第 5 组：
    - `mug_counter` 在 `kitchen_cabinet_6/top` 上
    - `mug_counter` 立着

**参考调用顺序**：

- 摆法 `no_cup`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `count(category=cup)` → 4. `search(object=cup)` → 5. `navigate(destination=mug)`（换做法） → 6. `pick(object=mug)`（换做法） → 7. `navigate(destination=kitchen_cabinet_6/top)` → 8. `place(object=mug, receptacle=kitchen_cabinet_6/top)`
- 摆法 `no_cup_mug_away`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `count(category=cup)` → 4. `search(object=cup)` → 5. `search(object=mug, region=living_room_0_0)`（换做法） → 6. `navigate(destination=mug)` → 7. `pick(object=mug)` → 8. `navigate(destination=kitchen_cabinet_6/top)` → 9. `place(object=mug, receptacle=kitchen_cabinet_6/top)`
- 摆法 `alt_dining_table_2`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `count(category=cup)` → 4. `search(object=cup)` → 5. `search(object=mug, region=dining_room_0_1)`（换做法） → 6. `navigate(destination=mug)` → 7. `pick(object=mug)` → 8. `navigate(destination=kitchen_cabinet_6/top)` → 9. `place(object=mug, receptacle=kitchen_cabinet_6/top)`

### clear_the_drinks_spot（Task）

**情况**：早饭后燕麦碗和锅盖留在饮品角上，把柜顶占满了；指令是“早餐结束了，把靠墙矮柜上用过的餐厨用品收拾好，放上杯子，待会儿客人要来喝茶”，没点名是哪些东西、收到哪 → 认出碗和锅盖就是用过的餐厨用品，都收回厨房（岛台、灶台或厨房台面都算），再在腾出的地方放一个杯子

**指令**：早餐结束了，把靠墙矮柜上用过的餐厨用品收拾好，放上杯子，待会儿客人要来喝茶。

**成功条件**：

- `oatmeal` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
- `pot_lid` 在其中任一处上：`kitchen_island/top`、`kitchen_stove/top`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
- `oatmeal` 立着
- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
    - `cup_counter_b` 立着
  - 第 2 组：
    - `mug` 在 `kitchen_cabinet_6/top` 上
    - `mug` 立着
  - 第 3 组：
    - `mug_dining_cabinet` 在 `kitchen_cabinet_6/top` 上
    - `mug_dining_cabinet` 立着
  - 第 4 组：
    - `mug_shelf` 在 `kitchen_cabinet_6/top` 上
    - `mug_shelf` 立着
  - 第 5 组：
    - `mug_counter` 在 `kitchen_cabinet_6/top` 上
    - `mug_counter` 立着

**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `navigate(destination=oatmeal)` → 6. `pick(object=oatmeal)` → 7. `navigate(destination=kitchen_island/top)` → 8. `place(object=oatmeal, receptacle=kitchen_island/top, hint_xy=[6.7, 1.84])` → 9. `navigate(destination=pot_lid)` → 10. `pick(object=pot_lid)` → 11. `navigate(destination=kitchen_island/top)` → 12. `place(object=pot_lid, receptacle=kitchen_island/top, hint_xy=[7.1, 1.85])` → 13. `navigate(destination=cup_counter_b)` → 14. `pick(object=cup_counter_b)` → 15. `navigate(destination=kitchen_cabinet_6/top)` → 16. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)`

### two_guests（Task）

**情况**：“有两位客人要来，在饮品角摆两个杯子，两个别挨着”：家里只有一个杯子（岛台上），马克杯在别的房间（开局看不到） → 先放杯子，发现没有第二个，自己想到马克杯也是杯子，去别的房间找来补上

**指令**：有两位客人要来。在靠墙矮柜上的饮品角摆两个杯子，两个别挨着。

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

- 摆法 `dining`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=cup_counter_b)` → 4. `pick(object=cup_counter_b)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top, hint_xy=[3.342, 0.36])` → 7. `search(object=mug, region=dining_room_0_1)` → 8. `navigate(destination=mug)` → 9. `pick(object=mug)` → 10. `navigate(destination=kitchen_cabinet_6/top)` → 11. `place(object=mug, receptacle=kitchen_cabinet_6/top, hint_xy=[3.622, 0.38])`
- 摆法 `study`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=cup_counter_b)` → 4. `pick(object=cup_counter_b)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top, hint_xy=[3.342, 0.36])` → 7. `search(object=mug, region=living_room_0_1)` → 8. `navigate(destination=mug)` → 9. `pick(object=mug)` → 10. `navigate(destination=kitchen_cabinet_6/top)` → 11. `place(object=mug, receptacle=kitchen_cabinet_6/top, hint_xy=[3.622, 0.38])`

### x6_gd_cup_in_cabinets（Task）

**情况**：指令要一个不带把手的杯子，说这种杯子收在厨房的矮柜里；岛台上的马克杯就在眼前但有把手 → 不拿马克杯，逐个打开矮柜找杯子，找完关门

**指令**：有客人要来。在靠墙矮柜上的饮品角摆一个不带把手的杯子，这种杯子收在厨房的矮柜里。用完把柜门关好。

**成功条件**：

- `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
- `cup_counter_b` 立着
- 手里空着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

- 摆法 `cup_in_4`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_6)` → 4. `open(articulated=kitchen_cabinet_6)` → 5. `bend()` → 6. `explore_furniture(furniture=kitchen_cabinet_6)` → 7. `straighten()` → 8. `close(articulated=kitchen_cabinet_6)` → 9. `navigate(destination=kitchen_cabinet_4)` → 10. `open(articulated=kitchen_cabinet_4)` → 11. `bend()` → 12. `explore_furniture(furniture=kitchen_cabinet_4)` → 13. `straighten()` → 14. `navigate(destination=cup_counter_b)` → 15. `pick(object=cup_counter_b)` → 16. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 17. `navigate(destination=kitchen_cabinet_6/top)` → 18. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)` → 19. `navigate(destination=kitchen_cabinet_4)` → 20. `close(articulated=kitchen_cabinet_4)`
- 摆法 `cup_in_6`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_4)` → 4. `open(articulated=kitchen_cabinet_4)` → 5. `bend()` → 6. `explore_furniture(furniture=kitchen_cabinet_4)` → 7. `straighten()` → 8. `close(articulated=kitchen_cabinet_4)` → 9. `navigate(destination=kitchen_cabinet_6)` → 10. `open(articulated=kitchen_cabinet_6)` → 11. `bend()` → 12. `explore_furniture(furniture=kitchen_cabinet_6)` → 13. `straighten()` → 14. `navigate(destination=cup_counter_b)` → 15. `pick(object=cup_counter_b)` → 16. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 17. `navigate(destination=kitchen_cabinet_6/top)` → 18. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)` → 19. `navigate(destination=kitchen_cabinet_6)` → 20. `close(articulated=kitchen_cabinet_6)`

---

## T05_pen_or_pencil_to_desk

> 孩子写作业要用铅笔，拿一支铅笔到书房书桌上。

### e1_pencil_asked（对照）

**情况**：指令直接要铅笔，铅笔在卧室书架上 → 拿到书桌

**指令**：孩子做数学作业需要铅笔，请把铅笔拿到书房的书桌上。

**成功条件**：

- `pencil` 在 `desk_1/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `navigate(destination=pencil)`（换做法） → 4. `pick(object=pencil)`（换做法） → 5. `present(object=pencil)`（补救） → 6. `navigate(destination=desk_1/top)` → 7. `place(object=pencil, receptacle=desk_1/top)`

### no_pen_pencil_away（Task）

**情况**：要铅笔，铅笔在另一个房间的餐桌上 → 去找铅笔

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `pen` 在 `desk_1/top` 上
  - 第 2 组：
    - `pencil` 在 `desk_1/top` 上

**参考调用顺序**：

1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `navigate(destination=pen)` → 4. `navigate(destination=dining_table_2/top)`（补救） → 5. `look(target=dining_table_2/top)`（补救） → 6. `navigate(destination=pencil)` → 7. `pick(object=pencil)` → 8. `navigate(destination=desk_1/top)` → 9. `place(object=pencil, receptacle=desk_1/top)`

### check_desk_first（Task）

**情况**：指令要钢笔；书桌上已经有一支笔：要么就是钢笔，要么只是铅笔（钢笔在卧室书架上） → 先看书桌：是钢笔就停手（再拿一支算失败）；只有铅笔不算数，去拿钢笔，铅笔留在桌上

**指令**：孩子写作业要用钢笔，拿一支钢笔到书房书桌上。

**成功条件**：

- 摆法 `pen_on_desk`：
  - `pen` 在 `desk_1/top` 上
  - `pen` 没被挪动（离开局位置不超过 10 cm）
  - `pencil` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `pencil_on_desk`：
  - `pen` 在 `desk_1/top` 上
  - `pencil` 没被挪动（离开局位置不超过 10 cm）
  - 手里空着

**参考调用顺序**：

- 摆法 `pen_on_desk`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `identify(object=pen)`
- 摆法 `pencil_on_desk`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `identify(object=pencil)` → 4. `search(object=pen, region=bedroom_0_1)` → 5. `navigate(destination=pen)` → 6. `pick(object=pen)` → 7. `navigate(destination=desk_1/top)` → 8. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.168, -5.946])`

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

- 摆法 `two`：1. `search(object=pencil, region=bedroom_0_1)` → 2. `navigate(destination=pencil)` → 3. `pick(object=pencil)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pencil, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])` → 6. `search(object=pen, region=dining_room_0_1)` → 7. `navigate(destination=pen)` → 8. `pick(object=pen)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.908, -6.146])`
- 摆法 `three`：1. `search(object=pencil, region=bedroom_0_1)` → 2. `navigate(destination=pencil)` → 3. `pick(object=pencil)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pencil, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])` → 6. `search(object=pen, region=dining_room_0_1)` → 7. `navigate(destination=pen)` → 8. `pick(object=pen)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.908, -6.146])` → 11. `search(object=pencil_2, region=living_room_0_0)` → 12. `navigate(destination=pencil_2)` → 13. `pick(object=pencil_2)` → 14. `navigate(destination=desk_1/top)` → 15. `place(object=pencil_2, receptacle=desk_1/top, hint_xy=[-0.608, -6.146])`
- 摆法 `four`：1. `search(object=pencil, region=bedroom_0_1)` → 2. `navigate(destination=pencil)` → 3. `pick(object=pencil)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pencil, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])` → 6. `search(object=pen, region=dining_room_0_1)` → 7. `navigate(destination=pen)` → 8. `pick(object=pen)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.908, -6.146])` → 11. `search(object=pencil_2, region=living_room_0_0)` → 12. `navigate(destination=pencil_2)` → 13. `pick(object=pencil_2)` → 14. `navigate(destination=desk_1/top)` → 15. `place(object=pencil_2, receptacle=desk_1/top, hint_xy=[-0.608, -6.146])` → 16. `search(object=pen_2, region=kitchen_0_1)` → 17. `navigate(destination=pen_2)` → 18. `pick(object=pen_2)` → 19. `navigate(destination=desk_1/top)` → 20. `place(object=pen_2, receptacle=desk_1/top, hint_xy=[-0.168, -5.946])`

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

- 摆法 `single`：1. `search(object=pen, region=bedroom_0_1)` → 2. `navigate(destination=pen)` → 3. `pick(object=pen)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.908, -6.146])` → 6. `search(object=notebook_1, region=dining_room_0_1)` → 7. `navigate(destination=notebook_1)` → 8. `expose(object=notebook_1)` → 9. `look(target=notebook_1)` → 10. `pick(object=notebook_1)` → 11. `navigate(destination=desk_1/top)` → 12. `place(object=notebook_1, receptacle=desk_1/top, hint_xy=[-0.608, -6.166])`
- 摆法 `several`：1. `search(object=pen, region=bedroom_0_1)` → 2. `navigate(destination=pen)` → 3. `pick(object=pen)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.908, -6.146])` → 6. `search(object=notebook_2, region=living_room_0_0)` → 7. `navigate(destination=notebook_2)` → 8. `expose(object=notebook_2)` → 9. `look(target=notebook_2)` → 10. `pick(object=notebook_2)` → 11. `navigate(destination=desk_1/top)` → 12. `place(object=notebook_2, receptacle=desk_1/top, hint_xy=[-0.608, -6.166])`
- 摆法 `pencil_only`：1. `search(object=notebook_1, region=bedroom_0_1)` → 2. `navigate(destination=notebook_1)` → 3. `expose(object=notebook_1)` → 4. `look(target=notebook_1)` → 5. `pick(object=notebook_1)` → 6. `navigate(destination=desk_1/top)` → 7. `place(object=notebook_1, receptacle=desk_1/top, hint_xy=[-0.908, -6.166])` → 8. `search(object=pencil, region=dining_room_0_1)` → 9. `navigate(destination=pencil)` → 10. `pick(object=pencil)` → 11. `navigate(destination=desk_1/top)` → 12. `place(object=pencil, receptacle=desk_1/top, hint_xy=[-0.608, -6.146])`

### pens_per_notebook（Task）

**情况**：孩子们在书桌写作业，指令说桌上有几本作业本就拿几支笔，每本旁边放一支，不要多拿；家里有 4 支笔分散在不同房间 → 先数作业本，再拿正好那么多支，每本旁边放一支，其余的笔不动

**指令**：孩子们在书房书桌写作业，每人一本作业本。桌上有几本作业本，就拿几支笔（钢笔、铅笔都行）来，每本旁边放一支，不要多拿。

**成功条件**：

- 摆法 `notebooks_2`：
  - `hw_notebook_1` 离其中至少一个不超过 15 cm：`pencil`、`pen`、`pen_2`、`pencil_2`
  - `hw_notebook_2` 离其中至少一个不超过 15 cm：`pencil`、`pen`、`pen_2`、`pencil_2`
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
  - `hw_notebook_1` 离其中至少一个不超过 15 cm：`pencil`、`pen`、`pen_2`、`pencil_2`
  - `hw_notebook_2` 离其中至少一个不超过 15 cm：`pencil`、`pen`、`pen_2`、`pencil_2`
  - `hw_notebook_3` 离其中至少一个不超过 15 cm：`pencil`、`pen`、`pen_2`、`pencil_2`
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

- 摆法 `notebooks_2`：1. `search(object=pencil, region=bedroom_0_1)` → 2. `navigate(destination=pencil)` → 3. `pick(object=pencil)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pencil, receptacle=desk_1/top, hint_xy=[-0.85, -6.22])` → 6. `search(object=pen, region=bedroom_0_1)` → 7. `navigate(destination=pen)` → 8. `pick(object=pen)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.3, -6.22])`
- 摆法 `notebooks_3`：1. `search(object=pencil, region=bedroom_0_1)` → 2. `navigate(destination=pencil)` → 3. `pick(object=pencil)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pencil, receptacle=desk_1/top, hint_xy=[-1.0, -6.22])` → 6. `search(object=pen, region=bedroom_0_1)` → 7. `navigate(destination=pen)` → 8. `pick(object=pen)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.57, -6.22])` → 11. `search(object=pen_2, region=living_room_0_0)` → 12. `navigate(destination=pen_2)` → 13. `pick(object=pen_2)` → 14. `navigate(destination=desk_1/top)` → 15. `place(object=pen_2, receptacle=desk_1/top, hint_xy=[-0.14, -6.22])`

### errand_combined（Task）

**情况**：两件事：拿一支钢笔到书房书桌；书桌上有个用过的马克杯要拿回厨房台面；只有一只手 → 先拿钢笔到书桌，放下后顺手拿起马克杯送回厨房，比单独跑一趟省路

**指令**：孩子在书房书桌写作业要用钢笔，拿一支过去。另外，那张书桌上有个用过的马克杯，要拿回厨房台面。

**成功条件**：

- `pen` 在 `desk_1/top` 上
- `used_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`
- `used_mug` 立着
- 手里空着

**参考调用顺序**：

- 摆法 `pen_bedroom`：1. `search(object=pen, region=bedroom_0_1)` → 2. `navigate(destination=pen)` → 3. `pick(object=pen)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.748, -6.146])` → 6. `pick(object=used_mug)` → 7. `navigate(destination=kitchen_counter_2/top)` → 8. `place(object=used_mug, receptacle=kitchen_counter_2/top, hint_xy=[-0.144, 7.109])`
- 摆法 `pen_dining`：1. `search(object=pen, region=dining_room_0_1)` → 2. `navigate(destination=pen)` → 3. `pick(object=pen)` → 4. `navigate(destination=desk_1/top)` → 5. `place(object=pen, receptacle=desk_1/top, hint_xy=[-0.748, -6.146])` → 6. `pick(object=used_mug)` → 7. `navigate(destination=kitchen_counter_2/top)` → 8. `place(object=used_mug, receptacle=kitchen_counter_2/top, hint_xy=[-0.144, 7.109])`

### x6_gd_pen_or_pencil_cabinets（Task）

**情况**：指令要钢笔；两个矮柜里一个放钢笔、一个放铅笔 → 打开找到钢笔为止（铅笔不算），关好柜门

**指令**：孩子写作业要用钢笔，拿一支钢笔到书房书桌上。笔都收在厨房那两个矮柜里，拿完把柜门关好。

**成功条件**：

- `pen` 在 `desk_1/top` 上
- 手里空着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

- 摆法 `pen_in_4`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=pen)` → 13. `pick(object=pen)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `navigate(destination=desk_1/top)` → 16. `place(object=pen, receptacle=desk_1/top)` → 17. `navigate(destination=kitchen_cabinet_4)` → 18. `close(articulated=kitchen_cabinet_4)`
- 摆法 `pen_in_6`：1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_4)` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=pen)` → 13. `pick(object=pen)` → 14. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 15. `navigate(destination=desk_1/top)` → 16. `place(object=pen, receptacle=desk_1/top)` → 17. `navigate(destination=kitchen_cabinet_6)` → 18. `close(articulated=kitchen_cabinet_6)`

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

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top)`

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

- 摆法 `island_floor`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top, hint_xy=[3.32, 0.45])` → 7. `square(object=wooden_block_a)` → 8. `navigate(destination=wooden_block_b)` → 9. `pick(object=wooden_block_b)` → 10. `navigate(destination=kitchen_cabinet_6/top)` → 11. `place(object=wooden_block_b, receptacle=kitchen_cabinet_6/top, hint_xy=[3.5, 0.45])` → 12. `square(object=wooden_block_b)` → 13. `explore_room(room=living_room_0_0)` → 14. `navigate(destination=floor_block)` → 15. `look(target=floor_block)` → 16. `pick(object=floor_block)` → 17. `navigate(destination=kitchen_cabinet_6/top)` → 18. `place(object=floor_block, receptacle=kitchen_cabinet_6/top, hint_xy=[3.68, 0.45])` → 19. `square(object=floor_block)`
- 摆法 `spread`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top, hint_xy=[3.32, 0.45])` → 7. `square(object=wooden_block_a)` → 8. `search(object=wooden_block_b, region=dining_room_0_1)` → 9. `navigate(destination=wooden_block_b)` → 10. `pick(object=wooden_block_b)` → 11. `navigate(destination=kitchen_cabinet_6/top)` → 12. `place(object=wooden_block_b, receptacle=kitchen_cabinet_6/top, hint_xy=[3.5, 0.45])` → 13. `square(object=wooden_block_b)` → 14. `search(object=floor_block, region=kitchen_0_1)` → 15. `navigate(destination=floor_block)` → 16. `pick(object=floor_block)` → 17. `navigate(destination=kitchen_cabinet_6/top)` → 18. `place(object=floor_block, receptacle=kitchen_cabinet_6/top, hint_xy=[3.68, 0.45])` → 19. `square(object=floor_block)`

### display_spot_or_tv（Task）

**情况**：“把积木摆出来展示，要从房间里看得见，最好摆在靠墙矮柜顶上。柜顶上的盒子和瓶子都别挪”：矮柜顶上立着三盒麦片和一瓶果汁 → 从房间里看柜顶：东西在后排、前面空着就摆矮柜前排（摆别处算失败）；东西占满前排，就另找一个看得见的地方（电视柜或另一个矮柜顶）；有的摆法积木不在眼前，要先找

**指令**：把积木摆出来展示，要从房间里看得见，最好摆在靠墙矮柜顶上。柜顶上的盒子和瓶子都别挪。

**成功条件**：

- 摆法 `front_free`、`front_free_block_away`：
  - `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
  - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
  - `wooden_block_a` 离台面边缘至少 2 cm
  - `clutter_cereal_a`、`clutter_cereal_b`、`juice_bottle`、`clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
  - `clutter_cereal_a`、`clutter_cereal_b`、`juice_bottle`、`clutter_cereal_c` 立着
  - 手里空着
- 摆法 `front_taken`、`front_taken_block_away`：
  - `clutter_cereal_a`、`clutter_cereal_b`、`juice_bottle`、`clutter_cereal_c` 没被挪动（离开局位置不超过 2 cm）
  - `clutter_cereal_a`、`clutter_cereal_b`、`juice_bottle`、`clutter_cereal_c` 立着
  - 手里空着
  - 满足下面任意一组：
    - 第 1 组：
      - `wooden_block_a` 在 `tv_stand_2/top` 上
      - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
      - `wooden_block_a` 离台面边缘至少 2 cm
    - 第 2 组：
      - `wooden_block_a` 在 `kitchen_cabinet_4/top` 上
      - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
      - `wooden_block_a` 离台面边缘至少 2 cm

**参考调用顺序**：

- 摆法 `front_taken`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `navigate(destination=wooden_block_a)` → 6. `pick(object=wooden_block_a)` → 7. `navigate(destination=tv_stand_2/top)` → 8. `place(object=wooden_block_a, receptacle=tv_stand_2/top)`
- 摆法 `front_free`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `navigate(destination=wooden_block_a)` → 6. `pick(object=wooden_block_a)` → 7. `navigate(destination=kitchen_cabinet_6/top)` → 8. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top, hint_xy=[3.433, 0.465])`
- 摆法 `front_taken_block_away`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `search(object=wooden_block_a, region=dining_room_0_1)` → 6. `navigate(destination=wooden_block_a)` → 7. `pick(object=wooden_block_a)` → 8. `navigate(destination=tv_stand_2/top)` → 9. `place(object=wooden_block_a, receptacle=tv_stand_2/top)`
- 摆法 `front_free_block_away`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_cabinet_6/top)` → 4. `look(target=kitchen_cabinet_6/top)` → 5. `search(object=wooden_block_a, region=bedroom_0_1)` → 6. `navigate(destination=wooden_block_a)` → 7. `pick(object=wooden_block_a)` → 8. `navigate(destination=kitchen_cabinet_6/top)` → 9. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top, hint_xy=[3.433, 0.465])`

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

- 摆法 `boxes_middle`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=bookcase_3/top)` → 7. `look(target=bookcase_3/top)` → 8. `place(object=wooden_block_a, receptacle=bookcase_3/top, hint_xy=[1.88, -4.88])`
- 摆法 `boxes_corner`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=bookcase_3/top)` → 7. `look(target=bookcase_3/top)` → 8. `place(object=wooden_block_a, receptacle=bookcase_3/top, hint_xy=[2.15, -4.74])`

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

**情况**：微波炉转但不热，指令里没说 → 先放进微波炉热，发现热不起来，再改用灶台；有的摆法燕麦粥不在原处，要先找

**成功条件**：

- `oatmeal` 温度至少 40 °C
- `kitchen_stove` 已经停止加热
- `kitchen_microwave` 关着
- 手里空着

**参考调用顺序**：

- 摆法 `microwave_broken`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `navigate(destination=oatmeal)` → 4. `pick(object=oatmeal)` → 5. `navigate(destination=kitchen_microwave/inside_floor)` → 6. `place(object=oatmeal, receptacle=kitchen_microwave/inside_floor)` → 7. `close(articulated=kitchen_microwave)` → 8. `heat(food=oatmeal, appliance=kitchen_microwave, temp_c=40)` → 9. `stop(appliance=kitchen_microwave)`（换做法） → 10. `pick(object=oatmeal)`（换做法） → 11. `navigate(destination=kitchen_stove/top)`（换做法） → 12. `place(object=oatmeal, receptacle=kitchen_stove/top)`（换做法） → 13. `heat(food=oatmeal, appliance=kitchen_stove, temp_c=40)`（换做法） → 14. `navigate(destination=kitchen_microwave)` → 15. `close(articulated=kitchen_microwave)`
- 摆法 `broken_oatmeal_away`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `search(object=oatmeal, region=living_room_0_0)` → 4. `navigate(destination=oatmeal)` → 5. `pick(object=oatmeal)` → 6. `navigate(destination=kitchen_microwave/inside_floor)` → 7. `place(object=oatmeal, receptacle=kitchen_microwave/inside_floor)` → 8. `close(articulated=kitchen_microwave)` → 9. `heat(food=oatmeal, appliance=kitchen_microwave, temp_c=40)` → 10. `stop(appliance=kitchen_microwave)`（换做法） → 11. `pick(object=oatmeal)`（换做法） → 12. `navigate(destination=kitchen_stove/top)`（换做法） → 13. `place(object=oatmeal, receptacle=kitchen_stove/top)`（换做法） → 14. `heat(food=oatmeal, appliance=kitchen_stove, temp_c=40)`（换做法） → 15. `navigate(destination=kitchen_microwave)` → 16. `close(articulated=kitchen_microwave)`
- 摆法 `alt_dining_table_2`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `search(object=oatmeal, region=dining_room_0_1)` → 4. `navigate(destination=oatmeal)` → 5. `pick(object=oatmeal)` → 6. `navigate(destination=kitchen_microwave/inside_floor)` → 7. `place(object=oatmeal, receptacle=kitchen_microwave/inside_floor)` → 8. `close(articulated=kitchen_microwave)` → 9. `heat(food=oatmeal, appliance=kitchen_microwave, temp_c=40)` → 10. `stop(appliance=kitchen_microwave)`（换做法） → 11. `pick(object=oatmeal)`（换做法） → 12. `navigate(destination=kitchen_stove/top)`（换做法） → 13. `place(object=oatmeal, receptacle=kitchen_stove/top)`（换做法） → 14. `heat(food=oatmeal, appliance=kitchen_stove, temp_c=40)`（换做法） → 15. `navigate(destination=kitchen_microwave)` → 16. `close(articulated=kitchen_microwave)`

### microwave_holds_pot（Task）

**情况**：微波炉里放着带盖的汤锅，放不下碗（指令和任务本身一样，没提汤锅） → 改用灶台，微波炉门关好

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
- 摆法 `in_pot`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=soup_pot, region=dining_room_0_1)` → 4. `navigate(destination=soup_pot)` → 5. `pick(object=soup_pot)` → 6. `navigate(destination=kitchen_stove/top)` → 7. `place(object=soup_pot, receptacle=kitchen_stove/top, hint_xy=[8.41, 1.725])` → 8. `heat(food=soup_pot, appliance=kitchen_stove, temp_c=40)`
- 摆法 `in_steel_box`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=steel_lunch_box)` → 4. `expose(object=steel_lunch_box)` → 5. `look(target=steel_lunch_box)` → 6. `pick(object=steel_lunch_box)` → 7. `navigate(destination=kitchen_stove/top)` → 8. `place(object=steel_lunch_box, receptacle=kitchen_stove/top, hint_xy=[8.4, 1.655])` → 9. `heat(food=steel_lunch_box, appliance=kitchen_stove, temp_c=40)`
- 摆法 `in_foil_tray`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=foil_takeout_tray)` → 4. `expose(object=foil_takeout_tray)` → 5. `look(target=foil_takeout_tray)` → 6. `pick(object=foil_takeout_tray)` → 7. `navigate(destination=kitchen_stove/top)` → 8. `place(object=foil_takeout_tray, receptacle=kitchen_stove/top, hint_xy=[8.4, 1.655])` → 9. `heat(food=foil_takeout_tray, appliance=kitchen_stove, temp_c=40)`

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

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=kitchen_sponge)` → 6. `pick(object=kitchen_sponge)` → 7. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 8. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`

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

- 摆法 `blocks`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=toy_box)` → 6. `place(object=wooden_block_a, receptacle=toy_box)` → 7. `navigate(destination=wooden_block_b)` → 8. `pick(object=wooden_block_b)` → 9. `navigate(destination=toy_box)` → 10. `place(object=wooden_block_b, receptacle=toy_box)` → 11. `look(target=tv_stand_2/top)` → 12. `navigate(destination=kitchen_sponge)` → 13. `pick(object=kitchen_sponge)` → 14. `navigate(destination=kitchen_island/top)` → 15. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 16. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`
- 摆法 `duck`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=toy_box)` → 6. `place(object=wooden_block_a, receptacle=toy_box)` → 7. `navigate(destination=rubber_duck)` → 8. `pick(object=rubber_duck)` → 9. `navigate(destination=toy_box)` → 10. `place(object=rubber_duck, receptacle=toy_box)` → 11. `look(target=tv_stand_2/top)` → 12. `navigate(destination=kitchen_sponge)` → 13. `pick(object=kitchen_sponge)` → 14. `navigate(destination=kitchen_island/top)` → 15. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 16. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`

### return_sponge_home（Task）

**情况**：有人用完海绵随手放在某张桌子上；指令说擦完把海绵收回平时放海绵的地方，但没说是哪里；客厅靠墙矮柜顶上有个浅托盘，里面放着一块备用海绵 → 找到海绵擦岛台，再把它放进那个托盘（放回原来的桌子或留在岛台上都算失败）

**指令**：有人用完海绵随手放在了某张桌子上。用它把厨房岛台擦一下，擦完把海绵收回平时放海绵的地方。

**成功条件**：

- `kitchen_island/top` 擦过
- `kitchen_sponge` 在 `sponge_tray` 里
- `spare_sponge` 在 `sponge_tray` 里
- 手里空着

**参考调用顺序**：

- 摆法 `dining`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=kitchen_sponge, region=dining_room_0_1)` → 4. `navigate(destination=kitchen_sponge)` → 5. `pick(object=kitchen_sponge)` → 6. `navigate(destination=kitchen_island/top)` → 7. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 8. `navigate(destination=sponge_tray)` → 9. `place(object=kitchen_sponge, receptacle=sponge_tray)`
- 摆法 `study`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=kitchen_sponge, region=living_room_0_1)` → 4. `navigate(destination=kitchen_sponge)` → 5. `pick(object=kitchen_sponge)` → 6. `navigate(destination=kitchen_island/top)` → 7. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 8. `navigate(destination=sponge_tray)` → 9. `place(object=kitchen_sponge, receptacle=sponge_tray)`
- 摆法 `far_dining`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=kitchen_sponge, region=dining_room_0_0)` → 4. `navigate(destination=kitchen_sponge)` → 5. `pick(object=kitchen_sponge)` → 6. `navigate(destination=kitchen_island/top)` → 7. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 8. `navigate(destination=sponge_tray)` → 9. `place(object=kitchen_sponge, receptacle=sponge_tray)`

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

- 摆法 `island`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_sponge)` → 4. `pick(object=kitchen_sponge)` → 5. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 6. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`
- 摆法 `dining`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_sponge)` → 4. `pick(object=kitchen_sponge)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `navigate(destination=dining_table_2/top)` → 8. `wipe(surface=dining_table_2/top, tool=kitchen_sponge)` → 9. `navigate(destination=kitchen_island/top)` → 10. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`

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

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 4. `navigate(destination=breakfast_spoon)` → 5. `pick(object=breakfast_spoon)` → 6. `navigate(destination=handled_cooking_pot)` → 7. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 8. `navigate(destination=kitchen_island/top)` → 9. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 10. `navigate(destination=pot_lid)` → 11. `pick(object=pot_lid)` → 12. `navigate(destination=handled_cooking_pot)` → 13. `cover(container=handled_cooking_pot, lid=pot_lid)` → 14. `navigate(destination=kitchen_stove)` → 15. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

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

- 摆法 `lid_on_spoon_away`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 4. `navigate(destination=handled_cooking_pot)` → 5. `uncover(container=handled_cooking_pot)` → 6. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 7. `search(object=breakfast_spoon, region=living_room_0_0)` → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=handled_cooking_pot)` → 11. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 12. `navigate(destination=kitchen_island/top)` → 13. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 14. `navigate(destination=pot_lid)` → 15. `pick(object=pot_lid)` → 16. `navigate(destination=handled_cooking_pot)` → 17. `cover(container=handled_cooking_pot, lid=pot_lid)` → 18. `navigate(destination=kitchen_stove)` → 19. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`
- 摆法 `alt_dining_table_2`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 4. `navigate(destination=handled_cooking_pot)` → 5. `uncover(container=handled_cooking_pot)` → 6. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 7. `search(object=breakfast_spoon, region=dining_room_0_1)` → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=handled_cooking_pot)` → 11. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 12. `navigate(destination=kitchen_island/top)` → 13. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 14. `navigate(destination=pot_lid)` → 15. `pick(object=pot_lid)` → 16. `navigate(destination=handled_cooking_pot)` → 17. `cover(container=handled_cooking_pot, lid=pot_lid)` → 18. `navigate(destination=kitchen_stove)` → 19. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

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

- 摆法 `in_use`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_stove/top)` → 4. `look(target=kitchen_stove/top)` → 5. `search(object=handled_cooking_pot, region=dining_room_0_1)` → 6. `navigate(destination=handled_cooking_pot)` → 7. `pick(object=handled_cooking_pot)` → 8. `navigate(destination=kitchen_stove/top)` → 9. `place(object=handled_cooking_pot, receptacle=kitchen_stove/top, hint_xy=[8.7, 1.725])` → 10. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 11. `navigate(destination=breakfast_spoon)` → 12. `pick(object=breakfast_spoon)` → 13. `navigate(destination=handled_cooking_pot)` → 14. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 15. `navigate(destination=kitchen_island/top)` → 16. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 17. `navigate(destination=pot_lid)` → 18. `pick(object=pot_lid)` → 19. `navigate(destination=handled_cooking_pot)` → 20. `cover(container=handled_cooking_pot, lid=pot_lid)` → 21. `navigate(destination=kitchen_stove)` → 22. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`
- 摆法 `free`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_stove/top)` → 4. `look(target=kitchen_stove/top)` → 5. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 6. `navigate(destination=breakfast_spoon)` → 7. `pick(object=breakfast_spoon)` → 8. `navigate(destination=handled_cooking_pot)` → 9. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 10. `navigate(destination=kitchen_island/top)` → 11. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 12. `navigate(destination=pot_lid)` → 13. `pick(object=pot_lid)` → 14. `navigate(destination=handled_cooking_pot)` → 15. `cover(container=handled_cooking_pot, lid=pot_lid)` → 16. `navigate(destination=kitchen_stove)` → 17. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

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

- 摆法 `in_fridge`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 4. `navigate(destination=breakfast_fridge)` → 5. `open(articulated=breakfast_fridge)` → 6. `bend()` → 7. `explore_furniture(furniture=breakfast_fridge)` → 8. `straighten()` → 9. `navigate(destination=fridge_tomato)` → 10. `pick(object=fridge_tomato)` → 11. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 12. `navigate(destination=handled_cooking_pot)` → 13. `drop(object=fridge_tomato, container=handled_cooking_pot)` → 14. `navigate(destination=breakfast_fridge)` → 15. `close(articulated=breakfast_fridge)` → 16. `navigate(destination=breakfast_spoon)` → 17. `pick(object=breakfast_spoon)` → 18. `navigate(destination=handled_cooking_pot)` → 19. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 20. `navigate(destination=kitchen_island/top)` → 21. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 22. `navigate(destination=pot_lid)` → 23. `pick(object=pot_lid)` → 24. `navigate(destination=handled_cooking_pot)` → 25. `cover(container=handled_cooking_pot, lid=pot_lid)` → 26. `navigate(destination=kitchen_stove)` → 27. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`
- 摆法 `on_island`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `collect(objects=[cherry_tomato_1, cherry_tomato_2, fridge_tomato], container=handled_cooking_pot)` → 4. `navigate(destination=breakfast_spoon)` → 5. `pick(object=breakfast_spoon)` → 6. `navigate(destination=handled_cooking_pot)` → 7. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 8. `navigate(destination=kitchen_island/top)` → 9. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 10. `navigate(destination=pot_lid)` → 11. `pick(object=pot_lid)` → 12. `navigate(destination=handled_cooking_pot)` → 13. `cover(container=handled_cooking_pot, lid=pot_lid)` → 14. `navigate(destination=kitchen_stove)` → 15. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

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

- 摆法 `dining`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `collect(objects=[cherry_tomato_1], container=handled_cooking_pot)`（补救） → 4. `search(object=cherry_tomato_2, region=dining_room_0_1)`（补救） → 5. `navigate(destination=cherry_tomato_2)`（补救） → 6. `pick(object=cherry_tomato_2)`（补救） → 7. `navigate(destination=handled_cooking_pot)`（补救） → 8. `drop(object=cherry_tomato_2, container=handled_cooking_pot)`（补救） → 9. `navigate(destination=breakfast_spoon)` → 10. `pick(object=breakfast_spoon)` → 11. `navigate(destination=handled_cooking_pot)` → 12. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 13. `navigate(destination=kitchen_island/top)` → 14. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 15. `navigate(destination=pot_lid)` → 16. `pick(object=pot_lid)` → 17. `navigate(destination=handled_cooking_pot)` → 18. `cover(container=handled_cooking_pot, lid=pot_lid)` → 19. `navigate(destination=kitchen_stove)` → 20. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`
- 摆法 `cabinet6`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `collect(objects=[cherry_tomato_1], container=handled_cooking_pot)`（补救） → 4. `search(object=cherry_tomato_2, region=living_room_0_0)`（补救） → 5. `navigate(destination=cherry_tomato_2)`（补救） → 6. `pick(object=cherry_tomato_2)`（补救） → 7. `navigate(destination=handled_cooking_pot)`（补救） → 8. `drop(object=cherry_tomato_2, container=handled_cooking_pot)`（补救） → 9. `navigate(destination=breakfast_spoon)` → 10. `pick(object=breakfast_spoon)` → 11. `navigate(destination=handled_cooking_pot)` → 12. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 13. `navigate(destination=kitchen_island/top)` → 14. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 15. `navigate(destination=pot_lid)` → 16. `pick(object=pot_lid)` → 17. `navigate(destination=handled_cooking_pot)` → 18. `cover(container=handled_cooking_pot, lid=pot_lid)` → 19. `navigate(destination=kitchen_stove)` → 20. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

### pot_in_dining_room（Task）

**情况**：番茄旁边有碗和马克杯，锅却不在灶上，而在隔壁餐厅的餐桌上（锅盖在灶上）；指令和任务本身一样 → 不能就近用碗或杯，要去餐厅把锅拿回炉眼上，再做汤

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

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_stove/top)` → 4. `look(target=kitchen_stove/top)` → 5. `search(object=handled_cooking_pot, region=dining_room_0_1)` → 6. `navigate(destination=handled_cooking_pot)` → 7. `pick(object=handled_cooking_pot)` → 8. `navigate(destination=kitchen_stove/top)` → 9. `place(object=handled_cooking_pot, receptacle=kitchen_stove/top, hint_xy=[8.41, 1.725])` → 10. `navigate(destination=cherry_tomato_1)`（补救） → 11. `sweep(objects=[cherry_tomato_1, cherry_tomato_2], radius_m=0.12)`（补救） → 12. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)`（换做法） → 13. `navigate(destination=breakfast_spoon)` → 14. `pick(object=breakfast_spoon)` → 15. `navigate(destination=handled_cooking_pot)` → 16. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 17. `navigate(destination=kitchen_island/top)` → 18. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 19. `navigate(destination=pot_lid)` → 20. `pick(object=pot_lid)` → 21. `navigate(destination=handled_cooking_pot)` → 22. `cover(container=handled_cooking_pot, lid=pot_lid)` → 23. `navigate(destination=kitchen_stove)` → 24. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

---

## T10_trash_the_can

> 有人随手放了个空易拉罐，把它扔进垃圾桶。

### can_on_island（对照）

**情况**：罐子在岛台 → 扔掉

**成功条件**：

- `soda_can` 在 `trash_can` 里
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `explore_room(room=living_room_0_0)` → 4. `navigate(destination=soda_can)` → 5. `pick(object=soda_can)` → 6. `lift(object=soda_can, height_m=0.95)` → 7. `navigate(destination=trash_can)` → 8. `hover(object=soda_can, target=trash_can)` → 9. `drop(object=soda_can, container=trash_can)`

### can_in_dining_room（Task）

**情况**：罐子在隔壁看不到的地方 → 先找

**成功条件**：

- `soda_can` 在 `trash_can` 里
- 手里空着

**参考调用顺序**：

- 摆法 `can_in_dining_room`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `explore_room(room=living_room_0_0)` → 4. `pick(object=soda_can)` → 5. `search(object=soda_can, region=dining_room_0_1)` → 6. `navigate(destination=soda_can)` → 7. `pick(object=soda_can)` → 8. `navigate(destination=trash_can)` → 9. `drop(object=soda_can, container=trash_can)`
- 摆法 `alt_tv_stand_2`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `explore_room(room=living_room_0_0)` → 4. `pick(object=soda_can)` → 5. `search(object=soda_can, region=living_room_0_0)` → 6. `navigate(destination=soda_can)` → 7. `pick(object=soda_can)` → 8. `navigate(destination=trash_can)` → 9. `drop(object=soda_can, container=trash_can)`

### keep_kids_can（Task）

**情况**：两个一样的易拉罐：一个和作业本、铅笔摆在一起（孩子一边写作业一边喝的），另一个单独放着；指令说孩子写作业时喝的那罐别扔 → 从罐子周围的东西认出孩子的，只扔另一个（扔了孩子的算失败）

**指令**：把喝完的易拉罐扔进垃圾桶。孩子一边写作业一边喝的那罐别扔。

**成功条件**：

- `soda_can` 在 `trash_can` 里
- 手里空着
- `kids_can`、`craft_notebook`、`craft_pencil` 没被挪动（离开局位置不超过 3 cm）
- `kids_can` 立着

**参考调用顺序**：

- 摆法 `kid_desk`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=kids_can, region=living_room_0_1)` → 4. `navigate(destination=soda_can)` → 5. `pick(object=soda_can)` → 6. `lift(object=soda_can, height_m=0.95)` → 7. `navigate(destination=trash_can)` → 8. `hover(object=soda_can, target=trash_can)` → 9. `drop(object=soda_can, container=trash_can)`
- 摆法 `kid_island`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `search(object=soda_can, region=living_room_0_1)` → 4. `navigate(destination=soda_can)` → 5. `pick(object=soda_can)` → 6. `lift(object=soda_can, height_m=0.95)` → 7. `navigate(destination=trash_can)` → 8. `hover(object=soda_can, target=trash_can)` → 9. `drop(object=soda_can, container=trash_can)`

### trash_moved（Task）

**情况**：罐子在岛台上，但垃圾桶今天不在岛台旁边的老地方 → 拿起罐子去找垃圾桶（找的是目的地，不是东西）

**成功条件**：

- `soda_can` 在 `trash_can` 里
- 手里空着

**参考调用顺序**：

- 摆法 `dining`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=soda_can)` → 4. `pick(object=soda_can)` → 5. `lift(object=soda_can, height_m=0.95)` → 6. `explore_room(room=dining_room_0_1)` → 7. `navigate(destination=trash_can)` → 8. `hover(object=soda_can, target=trash_can)` → 9. `drop(object=soda_can, container=trash_can)`
- 摆法 `bathroom`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=soda_can)` → 4. `pick(object=soda_can)` → 5. `lift(object=soda_can, height_m=0.95)` → 6. `explore_room(room=bathroom_0_1)` → 7. `navigate(destination=trash_can)` → 8. `hover(object=soda_can, target=trash_can)` → 9. `drop(object=soda_can, container=trash_can)`

### after_dinner_clear（Task）

**情况**：“晚饭吃完了，把餐桌收拾干净，每样东西拿到它该去的地方。麦片盒留在桌上”：桌上有空易拉罐，以及空铝箔外卖盒、装剩饭的玻璃盒、用过的马克杯中的两样 → 按每样东西是什么、什么状态决定去处：空罐和空外卖盒扔垃圾桶，剩饭进冰箱，杯子回厨房台面或岛台；一只手，先开冰箱门再拿剩饭，放好关门

**指令**：晚饭吃完了，把餐桌收拾干净，每样东西拿到它该去的地方。麦片盒留在桌上。

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

**参考调用顺序**：

- 摆法 `rubbish_leftovers`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=soda_can)` → 4. `pick(object=soda_can)` → 5. `lift(object=soda_can, height_m=0.95)` → 6. `navigate(destination=trash_can)` → 7. `hover(object=soda_can, target=trash_can)` → 8. `drop(object=soda_can, container=trash_can)` → 9. `navigate(destination=takeout_tray)` → 10. `pick(object=takeout_tray)` → 11. `lift(object=takeout_tray, height_m=0.95)` → 12. `navigate(destination=trash_can)` → 13. `drop(object=takeout_tray, container=trash_can)` → 14. `navigate(destination=breakfast_fridge)` → 15. `open(articulated=breakfast_fridge)` → 16. `navigate(destination=leftovers)` → 17. `pick(object=leftovers)` → 18. `navigate(destination=breakfast_fridge)` → 19. `place(object=leftovers, receptacle=breakfast_fridge/inside_shelf)` → 20. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 21. `close(articulated=breakfast_fridge)`
- 摆法 `leftovers_mug`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=soda_can)` → 4. `pick(object=soda_can)` → 5. `lift(object=soda_can, height_m=0.95)` → 6. `navigate(destination=trash_can)` → 7. `hover(object=soda_can, target=trash_can)` → 8. `drop(object=soda_can, container=trash_can)` → 9. `navigate(destination=breakfast_fridge)` → 10. `open(articulated=breakfast_fridge)` → 11. `navigate(destination=leftovers)` → 12. `pick(object=leftovers)` → 13. `navigate(destination=breakfast_fridge)` → 14. `place(object=leftovers, receptacle=breakfast_fridge/inside_shelf)` → 15. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 16. `close(articulated=breakfast_fridge)` → 17. `navigate(destination=used_mug)` → 18. `pick(object=used_mug)` → 19. `navigate(destination=kitchen_counter_2/top)` → 20. `place(object=used_mug, receptacle=kitchen_counter_2/top)`
- 摆法 `rubbish_mug`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=soda_can)` → 4. `pick(object=soda_can)` → 5. `lift(object=soda_can, height_m=0.95)` → 6. `navigate(destination=trash_can)` → 7. `hover(object=soda_can, target=trash_can)` → 8. `drop(object=soda_can, container=trash_can)` → 9. `navigate(destination=takeout_tray)` → 10. `pick(object=takeout_tray)` → 11. `lift(object=takeout_tray, height_m=0.95)` → 12. `navigate(destination=trash_can)` → 13. `drop(object=takeout_tray, container=trash_can)` → 14. `navigate(destination=used_mug)` → 15. `pick(object=used_mug)` → 16. `navigate(destination=kitchen_counter_2/top)` → 17. `place(object=used_mug, receptacle=kitchen_counter_2/top)`

### guests_coming（Task）

**情况**：“客人十分钟后到，把客厅收拾得能见人：乱放的东西各回各处，本来就该在那儿的东西别动”：客厅里散着空罐、用过的马克杯（电视柜上）、孩子的积木（地上）中的两三样；岛台上的擀面杖和海绵本来就该在那 → 找出乱放的，各送回该去的地方（垃圾桶、厨房台面或岛台、玩具箱）

**指令**：客人十分钟后到，把客厅收拾得能见人：乱放的东西各回各处，本来就该在那儿的东西别动。

**成功条件**：

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

**参考调用顺序**：

- 摆法 `can_mug_block`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `lift(object=soda_can, height_m=0.95)` → 8. `navigate(destination=trash_can)` → 9. `hover(object=soda_can, target=trash_can)` → 10. `drop(object=soda_can, container=trash_can)` → 11. `navigate(destination=used_mug)` → 12. `pick(object=used_mug)` → 13. `navigate(destination=kitchen_counter_2/top)` → 14. `place(object=used_mug, receptacle=kitchen_counter_2/top)` → 15. `navigate(destination=wooden_block_a)` → 16. `look(target=wooden_block_a)` → 17. `pick(object=wooden_block_a)` → 18. `navigate(destination=toy_box)` → 19. `place(object=wooden_block_a, receptacle=toy_box)`
- 摆法 `can_block`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `lift(object=soda_can, height_m=0.95)` → 8. `navigate(destination=trash_can)` → 9. `hover(object=soda_can, target=trash_can)` → 10. `drop(object=soda_can, container=trash_can)` → 11. `navigate(destination=wooden_block_a)` → 12. `look(target=wooden_block_a)` → 13. `pick(object=wooden_block_a)` → 14. `navigate(destination=toy_box)` → 15. `place(object=wooden_block_a, receptacle=toy_box)`
- 摆法 `can_mug`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `lift(object=soda_can, height_m=0.95)` → 8. `navigate(destination=trash_can)` → 9. `hover(object=soda_can, target=trash_can)` → 10. `drop(object=soda_can, container=trash_can)` → 11. `navigate(destination=used_mug)` → 12. `pick(object=used_mug)` → 13. `navigate(destination=kitchen_counter_2/top)` → 14. `place(object=used_mug, receptacle=kitchen_counter_2/top)`

### x6_gd_can_put_away（Task）

**情况**：指令只说空易拉罐在厨房里被误收起来了、要开门才能找到；它在靠墙矮柜、微波炉或冰箱里 → 逐个打开找，扔进垃圾桶，打开的门都关好

**指令**：厨房里有个空易拉罐被误收起来了，要打开门才能找到。找出来扔进垃圾桶，最后把打开的门关好。

**成功条件**：

- `soda_can` 在 `trash_can` 里
- 手里空着
- `kitchen_microwave` 关着
- `kitchen_cabinet_6` 关着
- `breakfast_fridge` 关着

**参考调用顺序**：

- 摆法 `in_cabinet`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_microwave/inside_floor)` → 4. `close(articulated=kitchen_microwave)` → 5. `navigate(destination=kitchen_cabinet_6)` → 6. `open(articulated=kitchen_cabinet_6)` → 7. `bend()` → 8. `explore_furniture(furniture=kitchen_cabinet_6)` → 9. `straighten()` → 10. `navigate(destination=soda_can)` → 11. `pick(object=soda_can)` → 12. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 13. `navigate(destination=trash_can)` → 14. `drop(object=soda_can, container=trash_can)` → 15. `navigate(destination=kitchen_cabinet_6)` → 16. `close(articulated=kitchen_cabinet_6)`
- 摆法 `in_microwave`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_microwave)` → 8. `open(articulated=kitchen_microwave)` → 9. `look(target=kitchen_microwave/inside_floor)` → 10. `navigate(destination=soda_can)` → 11. `pick(object=soda_can)` → 12. `retreat(obstacle=kitchen_microwave, distance_m=0.3)` → 13. `close(articulated=kitchen_microwave)` → 14. `navigate(destination=trash_can)` → 15. `drop(object=soda_can, container=trash_can)`
- 摆法 `in_fridge`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_microwave/inside_floor)` → 4. `close(articulated=kitchen_microwave)` → 5. `navigate(destination=kitchen_cabinet_6)` → 6. `open(articulated=kitchen_cabinet_6)` → 7. `bend()` → 8. `explore_furniture(furniture=kitchen_cabinet_6)` → 9. `straighten()` → 10. `close(articulated=kitchen_cabinet_6)` → 11. `navigate(destination=breakfast_fridge)` → 12. `open(articulated=breakfast_fridge)` → 13. `bend()` → 14. `explore_furniture(furniture=breakfast_fridge)` → 15. `straighten()` → 16. `navigate(destination=soda_can)` → 17. `pick(object=soda_can)` → 18. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 19. `navigate(destination=trash_can)` → 20. `drop(object=soda_can, container=trash_can)` → 21. `navigate(destination=breakfast_fridge)` → 22. `close(articulated=breakfast_fridge)`

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

**情况**：书架上没有果篮 → 自己找另一个能装水果的东西：书房书桌上的托盘；有的摆法果篮原位置放着一个用过的早餐碗，那不是放水果的

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `apple` 在 `fruit_basket` 里
  - 第 2 组：
    - `apple` 在 `serving_tray` 里

**参考调用顺序**：

- 摆法 `basket_missing`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=apple)` → 4. `pick(object=apple)` → 5. `navigate(destination=bookcase_2/top)` → 6. `look(target=bookcase_2/top)` → 7. `place(object=apple, receptacle=fruit_basket)` → 8. `navigate(destination=desk_1/top)`（换做法） → 9. `look(target=desk_1/top)`（换做法） → 10. `navigate(destination=serving_tray)`（换做法） → 11. `place(object=apple, receptacle=serving_tray)`（换做法）
- 摆法 `basket_gone_bowl_there`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=apple)` → 4. `pick(object=apple)` → 5. `navigate(destination=bookcase_2/top)` → 6. `look(target=bookcase_2/top)` → 7. `identify(object=bowl_kitchen_cabinet)`（补救） → 8. `navigate(destination=desk_1/top)`（换做法） → 9. `look(target=desk_1/top)`（换做法） → 10. `navigate(destination=serving_tray)`（换做法） → 11. `place(object=apple, receptacle=serving_tray)`（换做法）

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

- 摆法 `apple_orange`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `search(object=fruit_basket, region=bedroom_0_1)` → 4. `navigate(destination=apple)` → 5. `pick(object=apple)` → 6. `navigate(destination=desk_1/top)` → 7. `place(object=apple, receptacle=desk_1/top, hint_xy=[-0.908, -6.166])` → 8. `navigate(destination=lunch_orange)` → 9. `pick(object=lunch_orange)` → 10. `navigate(destination=bookcase_2/top)` → 11. `place(object=lunch_orange, receptacle=fruit_basket)`
- 摆法 `orange_banana`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `search(object=fruit_basket, region=bedroom_0_1)` → 4. `navigate(destination=lunch_banana)` → 5. `pick(object=lunch_banana)` → 6. `navigate(destination=desk_1/top)` → 7. `place(object=lunch_banana, receptacle=desk_1/top, hint_xy=[-0.908, -6.186])` → 8. `navigate(destination=lunch_orange)` → 9. `pick(object=lunch_orange)` → 10. `navigate(destination=bookcase_2/top)` → 11. `place(object=lunch_orange, receptacle=fruit_basket)`
- 摆法 `all_three`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `search(object=fruit_basket, region=bedroom_0_1)` → 4. `navigate(destination=apple)` → 5. `pick(object=apple)` → 6. `navigate(destination=desk_1/top)` → 7. `place(object=apple, receptacle=desk_1/top, hint_xy=[-0.908, -6.166])` → 8. `navigate(destination=lunch_orange)` → 9. `pick(object=lunch_orange)` → 10. `navigate(destination=bookcase_2/top)` → 11. `place(object=lunch_orange, receptacle=fruit_basket)` → 12. `navigate(destination=lunch_banana)` → 13. `pick(object=lunch_banana)` → 14. `navigate(destination=bookcase_2/top)` → 15. `place(object=lunch_banana, receptacle=fruit_basket)`

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

- 摆法 `tray_in_study`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `search(object=fruit_tray, region=living_room_0_1)` → 4. `navigate(destination=fruit_tray)` → 5. `pick(object=fruit_tray)` → 6. `navigate(destination=tv_stand_2/top)` → 7. `place(object=fruit_tray, receptacle=tv_stand_2/top, hint_xy=[7.5, 0.36])` → 8. `navigate(destination=apple)` → 9. `pick(object=apple)` → 10. `navigate(destination=fruit_tray)` → 11. `place(object=apple, receptacle=fruit_tray)` → 12. `navigate(destination=lunch_orange)` → 13. `pick(object=lunch_orange)` → 14. `navigate(destination=fruit_tray)` → 15. `place(object=lunch_orange, receptacle=fruit_tray)`
- 摆法 `tray_by_table`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `search(object=fruit_tray, region=dining_room_0_1)` → 4. `navigate(destination=fruit_tray)` → 5. `pick(object=fruit_tray)` → 6. `navigate(destination=tv_stand_2/top)` → 7. `place(object=fruit_tray, receptacle=tv_stand_2/top, hint_xy=[7.5, 0.36])` → 8. `navigate(destination=apple)` → 9. `pick(object=apple)` → 10. `navigate(destination=fruit_tray)` → 11. `place(object=apple, receptacle=fruit_tray)` → 12. `navigate(destination=lunch_orange)` → 13. `pick(object=lunch_orange)` → 14. `navigate(destination=fruit_tray)` → 15. `place(object=lunch_orange, receptacle=fruit_tray)`

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

1. `explore_room(room=bedroom_0_1)` → 2. `explore_room(room=living_room_0_0)` → 3. `navigate(destination=toy_car)` → 4. `look(target=toy_car)` → 5. `pick(object=toy_car)` → 6. `navigate(destination=storage_basket)` → 7. `place(object=toy_car, receptacle=storage_basket)` → 8. `navigate(destination=rubber_duck)` → 9. `pick(object=rubber_duck)` → 10. `navigate(destination=storage_basket)` → 11. `place(object=rubber_duck, receptacle=storage_basket)` → 12. `nod()`（补救）

### duck_in_study（Task）

**情况**：鸭子落在别处，开局看不到 → 找鸭子

**成功条件**：

- `toy_car` 在 `storage_basket` 里
- `rubber_duck` 在 `storage_basket` 里
- `storage_basket` 立着
- 手里空着

**参考调用顺序**：

- 摆法 `duck_in_study`：1. `explore_room(room=bedroom_0_1)` → 2. `explore_room(room=living_room_0_0)` → 3. `navigate(destination=toy_car)` → 4. `look(target=toy_car)` → 5. `pick(object=toy_car)` → 6. `navigate(destination=storage_basket)` → 7. `place(object=toy_car, receptacle=storage_basket)` → 8. `navigate(destination=rubber_duck)` → 9. `search(object=rubber_duck, region=living_room_0_1)` → 10. `navigate(destination=rubber_duck)` → 11. `pick(object=rubber_duck)` → 12. `navigate(destination=storage_basket)` → 13. `place(object=rubber_duck, receptacle=storage_basket)`
- 摆法 `alt_dining_table_2`：1. `explore_room(room=bedroom_0_1)` → 2. `explore_room(room=living_room_0_0)` → 3. `navigate(destination=toy_car)` → 4. `look(target=toy_car)` → 5. `pick(object=toy_car)` → 6. `navigate(destination=storage_basket)` → 7. `place(object=toy_car, receptacle=storage_basket)` → 8. `navigate(destination=rubber_duck)` → 9. `search(object=rubber_duck, region=dining_room_0_1)` → 10. `navigate(destination=rubber_duck)` → 11. `pick(object=rubber_duck)` → 12. `navigate(destination=storage_basket)` → 13. `place(object=rubber_duck, receptacle=storage_basket)`

### bins_capacity（Task）

**情况**：没有储物筐，只有放不下所有玩具的容器：要么两个小箱（一个已经装满积木，一个空着，有时并排放在卧室书架上，有时分在不同房间），要么一个装了半箱积木的小箱和一个浅托盘（鸭子还不在原处） → 看每个容器还剩多少地方，把小车和鸭子分到放得下的地方，空箱或鸭子不在眼前就去找；箱子里原有的积木不动

**成功条件**：

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

**参考调用顺序**：

- 摆法 `side_left_full`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `measure(object=toy_bin_small_2)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_car)` → 7. `look(target=toy_car)` → 8. `pick(object=toy_car)` → 9. `navigate(destination=toy_bin_small_2)` → 10. `place(object=toy_car, receptacle=toy_bin_small_2)` → 11. `search(object=rubber_duck, region=living_room_0_1)` → 12. `navigate(destination=rubber_duck)` → 13. `pick(object=rubber_duck)` → 14. `navigate(destination=toy_bin_small_2)` → 15. `drop(object=rubber_duck, container=toy_bin_small_2)`
- 摆法 `side_right_full`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small_2)` → 4. `measure(object=toy_bin_small)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_car)` → 7. `look(target=toy_car)` → 8. `pick(object=toy_car)` → 9. `navigate(destination=toy_bin_small)` → 10. `place(object=toy_car, receptacle=toy_bin_small)` → 11. `search(object=rubber_duck, region=living_room_0_1)` → 12. `navigate(destination=rubber_duck)` → 13. `pick(object=rubber_duck)` → 14. `navigate(destination=toy_bin_small)` → 15. `drop(object=rubber_duck, container=toy_bin_small)`
- 摆法 `apart_full_on_tv`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `search(object=toy_bin_small_2, region=bedroom_0_1)` → 5. `measure(object=toy_bin_small_2)` → 6. `explore_room(room=living_room_0_0)` → 7. `navigate(destination=toy_car)` → 8. `look(target=toy_car)` → 9. `pick(object=toy_car)` → 10. `navigate(destination=toy_bin_small_2)` → 11. `place(object=toy_car, receptacle=toy_bin_small_2)` → 12. `search(object=rubber_duck, region=living_room_0_1)` → 13. `navigate(destination=rubber_duck)` → 14. `pick(object=rubber_duck)` → 15. `navigate(destination=toy_bin_small_2)` → 16. `drop(object=rubber_duck, container=toy_bin_small_2)`
- 摆法 `apart_empty_on_desk`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `search(object=toy_bin_small_2, region=living_room_0_1)` → 5. `measure(object=toy_bin_small_2)` → 6. `explore_room(room=living_room_0_0)` → 7. `navigate(destination=toy_car)` → 8. `look(target=toy_car)` → 9. `pick(object=toy_car)` → 10. `navigate(destination=toy_bin_small_2)` → 11. `place(object=toy_car, receptacle=toy_bin_small_2)` → 12. `search(object=rubber_duck, region=living_room_0_1)` → 13. `navigate(destination=rubber_duck)` → 14. `pick(object=rubber_duck)` → 15. `navigate(destination=toy_bin_small_2)` → 16. `drop(object=rubber_duck, container=toy_bin_small_2)`
- 摆法 `half_bin_and_tray`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `measure(object=toy_tray)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_car)` → 7. `look(target=toy_car)` → 8. `pick(object=toy_car)` → 9. `navigate(destination=toy_tray)` → 10. `place(object=toy_car, receptacle=toy_tray)` → 11. `search(object=rubber_duck, region=living_room_0_1)` → 12. `navigate(destination=rubber_duck)` → 13. `pick(object=rubber_duck)` → 14. `navigate(destination=toy_bin_small)` → 15. `drop(object=rubber_duck, container=toy_bin_small)`
- 摆法 `half_bin_and_tray_duck_dining`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `measure(object=toy_tray)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_car)` → 7. `look(target=toy_car)` → 8. `pick(object=toy_car)` → 9. `navigate(destination=toy_tray)` → 10. `place(object=toy_car, receptacle=toy_tray)` → 11. `search(object=rubber_duck, region=dining_room_0_1)` → 12. `navigate(destination=rubber_duck)` → 13. `pick(object=rubber_duck)` → 14. `navigate(destination=toy_bin_small)` → 15. `drop(object=rubber_duck, container=toy_bin_small)`

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

- 摆法 `car_duck`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `look(target=toy_car)` → 4. `pick(object=toy_car)` → 5. `navigate(destination=storage_basket)` → 6. `place(object=toy_car, receptacle=storage_basket)` → 7. `search(object=rubber_duck, region=living_room_0_1)` → 8. `navigate(destination=rubber_duck)` → 9. `pick(object=rubber_duck)` → 10. `navigate(destination=storage_basket)` → 11. `place(object=rubber_duck, receptacle=storage_basket)`
- 摆法 `car_duck_bear`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `look(target=toy_car)` → 4. `pick(object=toy_car)` → 5. `navigate(destination=storage_basket)` → 6. `place(object=toy_car, receptacle=storage_basket)` → 7. `search(object=rubber_duck, region=bathroom_0_1)` → 8. `navigate(destination=rubber_duck)` → 9. `pick(object=rubber_duck)` → 10. `navigate(destination=storage_basket)` → 11. `place(object=rubber_duck, receptacle=storage_basket)` → 12. `search(object=teddy_bear, region=dining_room_0_1)` → 13. `navigate(destination=teddy_bear)` → 14. `pick(object=teddy_bear)` → 15. `navigate(destination=storage_basket)` → 16. `place(object=teddy_bear, receptacle=storage_basket)`
- 摆法 `all_four`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `look(target=toy_car)` → 4. `pick(object=toy_car)` → 5. `navigate(destination=storage_basket)` → 6. `place(object=toy_car, receptacle=storage_basket)` → 7. `search(object=rubber_duck, region=living_room_0_1)` → 8. `navigate(destination=rubber_duck)` → 9. `pick(object=rubber_duck)` → 10. `navigate(destination=storage_basket)` → 11. `place(object=rubber_duck, receptacle=storage_basket)` → 12. `search(object=teddy_bear, region=dining_room_0_1)` → 13. `navigate(destination=teddy_bear)` → 14. `pick(object=teddy_bear)` → 15. `navigate(destination=storage_basket)` → 16. `place(object=teddy_bear, receptacle=storage_basket)` → 17. `search(object=stray_block, region=living_room_0_0)` → 18. `navigate(destination=stray_block)` → 19. `pick(object=stray_block)` → 20. `navigate(destination=storage_basket)` → 21. `place(object=stray_block, receptacle=storage_basket)`

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

- 摆法 `tall_two_loose`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `look(target=toy_car)` → 4. `pick(object=toy_car)` → 5. `navigate(destination=storage_basket)` → 6. `place(object=toy_car, receptacle=storage_basket)` → 7. `navigate(destination=rubber_duck)` → 8. `pick(object=rubber_duck)` → 9. `navigate(destination=storage_basket)` → 10. `place(object=rubber_duck, receptacle=storage_basket)` → 11. `navigate(destination=loose_block_1)` → 12. `look(target=loose_block_1)` → 13. `pick(object=loose_block_1)` → 14. `navigate(destination=storage_basket)` → 15. `place(object=loose_block_1, receptacle=storage_basket)` → 16. `navigate(destination=loose_block_2)` → 17. `look(target=loose_block_2)` → 18. `pick(object=loose_block_2)` → 19. `navigate(destination=storage_basket)` → 20. `place(object=loose_block_2, receptacle=storage_basket)`
- 摆法 `short_one_loose`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `look(target=toy_car)` → 4. `pick(object=toy_car)` → 5. `navigate(destination=storage_basket)` → 6. `place(object=toy_car, receptacle=storage_basket)` → 7. `navigate(destination=rubber_duck)` → 8. `pick(object=rubber_duck)` → 9. `navigate(destination=storage_basket)` → 10. `place(object=rubber_duck, receptacle=storage_basket)` → 11. `navigate(destination=loose_block_1)` → 12. `look(target=loose_block_1)` → 13. `pick(object=loose_block_1)` → 14. `navigate(destination=storage_basket)` → 15. `place(object=loose_block_1, receptacle=storage_basket)`
- 摆法 `tall_none_loose`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=toy_car)` → 3. `look(target=toy_car)` → 4. `pick(object=toy_car)` → 5. `navigate(destination=storage_basket)` → 6. `place(object=toy_car, receptacle=storage_basket)` → 7. `navigate(destination=rubber_duck)` → 8. `pick(object=rubber_duck)` → 9. `navigate(destination=storage_basket)` → 10. `place(object=rubber_duck, receptacle=storage_basket)`

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

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=bowl)` → 6. `pick(object=bowl)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.948, 7.095])` → 9. `navigate(destination=cup)` → 10. `pick(object=cup)` → 11. `navigate(destination=dining_table_2/top)` → 12. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[2.928, 7.295])`

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

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=bowl)` → 6. `pick(object=bowl)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.948, 7.095])` → 9. `navigate(destination=cup)` → 10. `navigate(destination=bookcase_2/top)`（换做法） → 11. `look(target=bookcase_2/top)`（换做法） → 12. `pick(object=mug)`（换做法） → 13. `navigate(destination=dining_table_2/top)` → 14. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[2.928, 7.295])`

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

- 摆法 `bowl_cup`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `measure(object=example_spoon)` → 4. `navigate(destination=tv_stand_2/top)` → 5. `look(target=tv_stand_2/top)` → 6. `navigate(destination=bowl)` → 7. `pick(object=bowl)` → 8. `navigate(destination=dining_table_2/top)` → 9. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.89, 7.49])` → 10. `navigate(destination=cup)` → 11. `pick(object=cup)` → 12. `navigate(destination=dining_table_2/top)` → 13. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[2.89, 7.15])`
- 摆法 `plate_bowl_mug_left`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `measure(object=example_spoon)` → 4. `navigate(destination=kitchen_counter_2/top)` → 5. `look(target=kitchen_counter_2/top)` → 6. `navigate(destination=plate_counter_a)` → 7. `pick(object=plate_counter_a)` → 8. `navigate(destination=dining_table_2/top)` → 9. `place(object=plate_counter_a, receptacle=dining_table_2/top, hint_xy=[2.89, 7.49])` → 10. `navigate(destination=tv_stand_2/top)` → 11. `look(target=tv_stand_2/top)` → 12. `navigate(destination=bowl)` → 13. `pick(object=bowl)` → 14. `navigate(destination=dining_table_2/top)` → 15. `stack(object=bowl, base=plate_counter_a)` → 16. `navigate(destination=bookcase_2/top)` → 17. `look(target=bookcase_2/top)` → 18. `navigate(destination=mug)` → 19. `pick(object=mug)` → 20. `navigate(destination=dining_table_2/top)` → 21. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[2.89, 7.68])`
- 摆法 `no_cup`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `measure(object=example_spoon)` → 4. `navigate(destination=tv_stand_2/top)` → 5. `look(target=tv_stand_2/top)` → 6. `navigate(destination=bowl)` → 7. `pick(object=bowl)` → 8. `navigate(destination=dining_table_2/top)` → 9. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.89, 7.49])` → 10. `navigate(destination=bookcase_2/top)` → 11. `look(target=bookcase_2/top)` → 12. `navigate(destination=mug)` → 13. `pick(object=mug)` → 14. `navigate(destination=dining_table_2/top)` → 15. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[2.89, 7.15])`

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

- 摆法 `adult_seat`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=bowl)` → 6. `pick(object=bowl)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.89, 6.89])` → 9. `navigate(destination=bookcase_2/top)` → 10. `look(target=bookcase_2/top)` → 11. `navigate(destination=mug)` → 12. `pick(object=mug)` → 13. `navigate(destination=dining_table_2/top)` → 14. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[2.89, 6.55])`
- 摆法 `kid_seat`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=bowl)` → 6. `pick(object=bowl)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.89, 6.89])` → 9. `navigate(destination=kitchen_counter_2/top)` → 10. `look(target=kitchen_counter_2/top)` → 11. `navigate(destination=kid_cup)` → 12. `pick(object=kid_cup)` → 13. `navigate(destination=dining_table_2/top)` → 14. `place(object=kid_cup, receptacle=dining_table_2/top, hint_xy=[2.89, 6.55])`
- 摆法 `adult_and_kid`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=tv_stand_2/top)` → 4. `look(target=tv_stand_2/top)` → 5. `navigate(destination=bowl)` → 6. `pick(object=bowl)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[2.89, 6.89])` → 9. `navigate(destination=bookcase_2/top)` → 10. `look(target=bookcase_2/top)` → 11. `navigate(destination=mug)` → 12. `pick(object=mug)` → 13. `navigate(destination=dining_table_2/top)` → 14. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[2.89, 6.55])` → 15. `navigate(destination=bowl_2)` → 16. `pick(object=bowl_2)` → 17. `navigate(destination=dining_table_2/top)` → 18. `place(object=bowl_2, receptacle=dining_table_2/top, hint_xy=[2.89, 6.04])` → 19. `navigate(destination=kitchen_counter_2/top)` → 20. `look(target=kitchen_counter_2/top)` → 21. `navigate(destination=kid_cup)` → 22. `pick(object=kid_cup)` → 23. `navigate(destination=dining_table_2/top)` → 24. `place(object=kid_cup, receptacle=dining_table_2/top, hint_xy=[2.89, 5.7])`

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

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=paperback_book)` → 4. `flip(object=paperback_book)`

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

**指令**：卧室书架里有本平装书封面朝下放着，帮我翻正，仍放在原来那一层。

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

- 摆法 `shelf_1`：1. `search(object=paperback_book, region=bedroom_0_1)` → 2. `navigate(destination=paperback_book)` → 3. `pick(object=paperback_book)` → 4. `navigate(destination=bookcase_2/top)` → 5. `place(object=paperback_book, receptacle=bookcase_2/top, hint_xy=[1.005, -0.479])` → 6. `flip(object=paperback_book)` → 7. `pick(object=paperback_book)` → 8. `place(object=paperback_book, receptacle=bookcase_2/shelf_1, hint_xy=[1.0, -0.44])`
- 摆法 `shelf_0`：1. `search(object=paperback_book, region=bedroom_0_1)` → 2. `navigate(destination=paperback_book)` → 3. `pick(object=paperback_book)` → 4. `navigate(destination=bookcase_2/top)` → 5. `place(object=paperback_book, receptacle=bookcase_2/top, hint_xy=[1.005, -0.479])` → 6. `flip(object=paperback_book)` → 7. `pick(object=paperback_book)` → 8. `place(object=paperback_book, receptacle=bookcase_2/shelf_0, hint_xy=[1.0, -0.44])`

---

## T16_rolling_pin_at_edge

> 准备包饺子了，擀面杖滚到岛台前沿快掉下去了，把它往里滚回去，别让它掉下来。

### pin_free（对照）

**情况**：擀面杖后面有空 → 直接往里滚

**成功条件**：

- `rolling_pin` 滚过
- `rolling_pin` 在 `kitchen_island/top` 上
- `rolling_pin` 离台面边缘至少 6 cm
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=rolling_pin)` → 4. `roll(object=rolling_pin, distance_m=0.12)`

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

- 摆法 `pin_and_mug`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=rolling_pin)` → 4. `roll(object=rolling_pin, distance_m=0.12)` → 5. `navigate(destination=edge_mug)` → 6. `pick(object=edge_mug)` → 7. `place(object=edge_mug, receptacle=kitchen_island/top, hint_xy=[7.3, 1.855])`
- 摆法 `pin_and_bowl`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=rolling_pin)` → 4. `roll(object=rolling_pin, distance_m=0.12)` → 5. `navigate(destination=oatmeal)` → 6. `pick(object=oatmeal)` → 7. `place(object=oatmeal, receptacle=kitchen_island/top, hint_xy=[7.14, 1.835])`
- 摆法 `pin_only`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=rolling_pin)` → 4. `roll(object=rolling_pin, distance_m=0.12)`

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

### hide_somewhere（Task）

**情况**：指令只说“把木积木藏到孩子一眼看不到的地方，别藏进电器里，危险”，没说藏哪 → 自己挑能藏住又不是电器的地方：锅盖在手边就藏进灶上的锅里盖好；锅盖被收到靠墙柜上了，就藏进矮柜里关好门（藏进微波炉或冰箱算失败）

**指令**：陪孩子玩捉迷藏，把木积木藏到孩子一眼看不到的地方。别藏进电器里，危险。

**成功条件**：

- `wooden_block_b` 藏好了（从房间里看不到）
- `["not on", "wooden_block_b", "kitchen_microwave/inside_floor"]`
- `["not on", "wooden_block_b", "breakfast_fridge/inside_shelf"]`
- 手里空着

**参考调用顺序**：

- 摆法 `pot_ready`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)`
- 摆法 `lid_away`：1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=kitchen_stove/top)` → 4. `look(target=kitchen_stove/top)` → 5. `navigate(destination=kitchen_cabinet_4)` → 6. `open(articulated=kitchen_cabinet_4)` → 7. `navigate(destination=wooden_block_b)` → 8. `pick(object=wooden_block_b)` → 9. `navigate(destination=kitchen_cabinet_4)` → 10. `place(object=wooden_block_b, receptacle=kitchen_cabinet_4/inside_shelf, hint_xy=[1.4, 0.42])` → 11. `close(articulated=kitchen_cabinet_4)`

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

### dishes_spread（Task）

**情况**：“奶奶想知道晚饭还有没有干净的盘子和碗。去厨房带门的地方看一看，看完把门都关好”：盘子在靠墙矮柜里，碗不在 → 看到盘子还不够，继续开别的门找碗（另一个矮柜或微波炉），每扇门都关好

**指令**：奶奶想知道晚饭还有没有干净的盘子和碗。去厨房带门的地方看一看，看完把门都关好。

**成功条件**：

- 看到过 `plate_inside_kitchen_cabinet`
- 看到过 `bowl_inside_kitchen_cabinet`
- `kitchen_cabinet_6` 关着
- `kitchen_microwave` 关着
- 手里空着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

- 摆法 `in_cabinet_4`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `inspect(receptacle=kitchen_cabinet_6)` → 4. `close(articulated=kitchen_cabinet_6)` → 5. `navigate(destination=kitchen_cabinet_4)` → 6. `open(articulated=kitchen_cabinet_4)` → 7. `inspect(receptacle=kitchen_cabinet_4)` → 8. `close(articulated=kitchen_cabinet_4)`
- 摆法 `in_microwave`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `inspect(receptacle=kitchen_cabinet_6)` → 4. `close(articulated=kitchen_cabinet_6)` → 5. `navigate(destination=kitchen_microwave)` → 6. `open(articulated=kitchen_microwave)` → 7. `look(target=kitchen_microwave/inside_floor)` → 8. `close(articulated=kitchen_microwave)`

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

1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=soda_can)` → 5. `pick(object=soda_can)` → 6. `navigate(destination=bookcase_2/top)` → 7. `look(target=bookcase_2/top)` → 8. `navigate(destination=wide_storage_bin)` → 9. `drop(object=soda_can, container=wide_storage_bin)` → 10. `navigate(destination=foam_cube)` → 11. `look(target=foam_cube)` → 12. `pick(object=foam_cube)` → 13. `navigate(destination=wide_storage_bin)` → 14. `drop(object=foam_cube, container=wide_storage_bin)`

### m_can_in_dining_room（Task）

**情况**：罐子不在原处，看不到 → 先找

**成功条件**：

- `soda_can` 在 `wide_storage_bin` 里
- `foam_cube` 在 `wide_storage_bin` 里
- 手里空着

**参考调用顺序**：

- 摆法 `m_can_in_dining_room`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=dining_room_0_1)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `navigate(destination=wide_storage_bin)` → 10. `drop(object=soda_can, container=wide_storage_bin)` → 11. `navigate(destination=foam_cube)` → 12. `look(target=foam_cube)` → 13. `pick(object=foam_cube)` → 14. `navigate(destination=wide_storage_bin)` → 15. `drop(object=foam_cube, container=wide_storage_bin)`
- 摆法 `alt_tv_stand_2`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=living_room_0_0)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `navigate(destination=wide_storage_bin)` → 10. `drop(object=soda_can, container=wide_storage_bin)` → 11. `navigate(destination=foam_cube)` → 12. `look(target=foam_cube)` → 13. `pick(object=foam_cube)` → 14. `navigate(destination=wide_storage_bin)` → 15. `drop(object=foam_cube, container=wide_storage_bin)`

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

**情况**：“电影看完了，把该回收的东西放进回收箱。有人把空易拉罐收进了厨房的矮柜里，找完把柜门关好”：泡沫块在客厅地上 → 逐个打开矮柜找罐子，两样都放进回收箱（书架上装回收的那个）

**指令**：电影看完了，把该回收的东西放进回收箱。有人把空易拉罐收进了厨房的矮柜里，找完把柜门关好。

**成功条件**：

- `soda_can` 在 `wide_storage_bin` 里
- `foam_cube` 在 `wide_storage_bin` 里
- 手里空着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

- 摆法 `in_4`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=soda_can)` → 13. `pick(object=soda_can)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `navigate(destination=bookcase_2/top)` → 16. `look(target=bookcase_2/top)` → 17. `navigate(destination=wide_storage_bin)` → 18. `drop(object=soda_can, container=wide_storage_bin)` → 19. `navigate(destination=kitchen_cabinet_4)` → 20. `close(articulated=kitchen_cabinet_4)` → 21. `navigate(destination=foam_cube)` → 22. `look(target=foam_cube)` → 23. `pick(object=foam_cube)` → 24. `navigate(destination=wide_storage_bin)` → 25. `drop(object=foam_cube, container=wide_storage_bin)`
- 摆法 `in_6`：1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_4)` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=soda_can)` → 13. `pick(object=soda_can)` → 14. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 15. `navigate(destination=bookcase_2/top)` → 16. `look(target=bookcase_2/top)` → 17. `navigate(destination=wide_storage_bin)` → 18. `drop(object=soda_can, container=wide_storage_bin)` → 19. `navigate(destination=kitchen_cabinet_6)` → 20. `close(articulated=kitchen_cabinet_6)` → 21. `navigate(destination=foam_cube)` → 22. `look(target=foam_cube)` → 23. `pick(object=foam_cube)` → 24. `navigate(destination=wide_storage_bin)` → 25. `drop(object=foam_cube, container=wide_storage_bin)`

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

1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=juice_bottle)` → 4. `pick(object=juice_bottle)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[2.948, 7.295])`

### m_bottle_on_tv_stand（Task）

**情况**：瓶子在客厅看不到的地方 → 先找

**成功条件**：

- `juice_bottle` 在 `dining_table_2/top` 上
- `juice_bottle` 立着
- 手里空着

**参考调用顺序**：

- 摆法 `m_bottle_on_tv_stand`：1. `search(object=juice_bottle, region=living_room_0_0)` → 2. `navigate(destination=juice_bottle)` → 3. `pick(object=juice_bottle)` → 4. `navigate(destination=dining_table_2/top)` → 5. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[2.948, 7.295])`
- 摆法 `alt_bookcase_2`：1. `search(object=juice_bottle, region=bedroom_0_1)` → 2. `navigate(destination=juice_bottle)` → 3. `pick(object=juice_bottle)` → 4. `navigate(destination=dining_table_2/top)` → 5. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[2.948, 7.295])`

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

- 摆法 `in_cabinet_4`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=juice_bottle)` → 13. `pick(object=juice_bottle)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `navigate(destination=dining_table_2/top)` → 16. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[2.948, 7.295])` → 17. `navigate(destination=kitchen_cabinet_4)` → 18. `close(articulated=kitchen_cabinet_4)`
- 摆法 `in_cabinet_6`：1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_4)` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=juice_bottle)` → 13. `pick(object=juice_bottle)` → 14. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 15. `navigate(destination=dining_table_2/top)` → 16. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[2.948, 7.295])` → 17. `navigate(destination=kitchen_cabinet_6)` → 18. `close(articulated=kitchen_cabinet_6)`

---

## T14_shelve_the_book

> 孩子看完书了，帮他把书收好。

### e1_book_ready（对照）

**情况**：红书在书房书桌上 → 放回他卧室的书架（任一层都算）

**成功条件**：

- `book_red` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
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

- 摆法 `set_on_large_shelf_4`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `explore_room(room=bedroom_0_1)` → 4. `navigate(destination=book_red)` → 5. `pick(object=book_red)` → 6. `navigate(destination=large_shelf_4/shelf_1)` → 7. `place(object=book_red, receptacle=large_shelf_4/shelf_1, hint_xy=[3.7, -5.15])`
- 摆法 `set_on_large_shelf_5`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `explore_room(room=bedroom_0_1)` → 4. `navigate(destination=book_red)` → 5. `pick(object=book_red)` → 6. `navigate(destination=large_shelf_5/shelf_1)` → 7. `place(object=book_red, receptacle=large_shelf_5/shelf_1, hint_xy=[4.45, -0.35])`

### stack_them_stably（Task）

**情况**：“把书桌上的书都收到他卧室的书架上，摞成一摞，大的放下面，小的放上面”：两三本大小不同的书 → 比较书的大小，按从大到小的顺序摞

**指令**：孩子看完书了，把书桌上的书都收到他卧室的书架上，摞成一摞，大的放下面，小的放上面。

**成功条件**：

- 摆法 `red_blue_paperback`：
  - `book_red` 在其中任一处上：`bookcase_2/top`、`bookcase_3/top`
  - `desk_book_blue` 叠在 `book_red` 上
  - `desk_paperback_book` 叠在 `desk_book_blue` 上
  - 手里空着
- 摆法 `blue_green_paperback`：
  - `desk_book_green` 在其中任一处上：`bookcase_2/top`、`bookcase_3/top`
  - `desk_book_blue` 叠在 `desk_book_green` 上
  - `desk_paperback_book` 叠在 `desk_book_blue` 上
  - 手里空着
- 摆法 `green_paperback`：
  - `desk_book_green` 在其中任一处上：`bookcase_2/top`、`bookcase_3/top`
  - `desk_paperback_book` 叠在 `desk_book_green` 上
  - 手里空着

**参考调用顺序**：

- 摆法 `red_blue_paperback`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=book_red)` → 4. `pick(object=book_red)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=book_red, receptacle=bookcase_2/top, hint_xy=[1.005, -0.459])` → 7. `navigate(destination=desk_book_blue)` → 8. `pick(object=desk_book_blue)` → 9. `navigate(destination=bookcase_2/top)` → 10. `stack(object=desk_book_blue, base=book_red)` → 11. `navigate(destination=desk_paperback_book)` → 12. `pick(object=desk_paperback_book)` → 13. `navigate(destination=bookcase_2/top)` → 14. `stack(object=desk_paperback_book, base=desk_book_blue)`
- 摆法 `green_paperback`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=desk_book_green)` → 4. `pick(object=desk_book_green)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=desk_book_green, receptacle=bookcase_2/top, hint_xy=[1.0, -0.45])` → 7. `navigate(destination=desk_paperback_book)` → 8. `pick(object=desk_paperback_book)` → 9. `navigate(destination=bookcase_2/top)` → 10. `stack(object=desk_paperback_book, base=desk_book_green)`
- 摆法 `blue_green_paperback`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=desk_book_green)` → 4. `pick(object=desk_book_green)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=desk_book_green, receptacle=bookcase_2/top, hint_xy=[1.0, -0.45])` → 7. `navigate(destination=desk_book_blue)` → 8. `pick(object=desk_book_blue)` → 9. `navigate(destination=bookcase_2/top)` → 10. `stack(object=desk_book_blue, base=desk_book_green)` → 11. `navigate(destination=desk_paperback_book)` → 12. `pick(object=desk_paperback_book)` → 13. `navigate(destination=bookcase_2/top)` → 14. `stack(object=desk_paperback_book, base=desk_book_blue)`

### homework_stays（Task）

**情况**：“把书桌收拾一下，东西都放到最合适的地方，作业他明天还要接着写”：书桌上有看完的书、用过的马克杯、摊开的作业本和铅笔 → 书放回书柜（家里任一书柜、任一层都算），杯子拿回厨房（两个厨房台面都算），作业原样不动（过程要求：整局不拿起作业本和铅笔）

**指令**：孩子看完书了，把他的书桌收拾一下，东西都放到最合适的地方。作业他明天还要接着写。

**成功条件**：

- `book_red` 在其中任一处上：`bookcase_1/top`、`bookcase_1/shelf_1`、`bookcase_1/shelf_0`、`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`、`bookcase_4/top`、`bookcase_4/shelf_1`、`bookcase_4/shelf_0`
- `desk_mug` 在其中任一处上：`kitchen_counter_1/top`、`kitchen_counter_2/top`
- `desk_mug` 立着
- `homework`、`hw_pencil` 没被挪动（离开局位置不超过 3 cm）
- 过程要求：整局都没拿起过 `homework`、`hw_pencil`（拆了再搭回去不算）
- 手里空着

**参考调用顺序**：

1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=book_red)` → 4. `pick(object=book_red)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=book_red, receptacle=bookcase_2/top)` → 7. `navigate(destination=desk_mug)` → 8. `pick(object=desk_mug)` → 9. `navigate(destination=kitchen_counter_2/top)` → 10. `place(object=desk_mug, receptacle=kitchen_counter_2/top, hint_xy=[-0.384, 7.609])`

### whose_book（Task）

**情况**：“把书房书桌上的书收好，放到摆着同类书的书架上”：卧室书柜上摆着蓝色精装书，客厅书架上摆着平装书；书桌上有其中一类或两类 → 看每本书是哪一类，放到摆着同类书的那个书架上

**指令**：把书房书桌上的书收好，放到摆着同类书的书架上。

**成功条件**：

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

**参考调用顺序**：

- 摆法 `blue_book`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=blue_book)` → 4. `pick(object=blue_book)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=blue_book, receptacle=bookcase_2/top, hint_xy=[1.0, -0.5])`
- 摆法 `paperback`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=paperback)` → 4. `pick(object=paperback)` → 5. `navigate(destination=large_shelf_2/shelf_2)` → 6. `place(object=paperback, receptacle=large_shelf_2/shelf_2, hint_xy=[-1.86, -0.95])`
- 摆法 `both`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=blue_book)` → 4. `pick(object=blue_book)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=blue_book, receptacle=bookcase_2/top, hint_xy=[1.0, -0.5])` → 7. `navigate(destination=paperback)` → 8. `pick(object=paperback)` → 9. `navigate(destination=large_shelf_2/shelf_2)` → 10. `place(object=paperback, receptacle=large_shelf_2/shelf_2, hint_xy=[-1.86, -0.95])`

### next_in_series（Task）

**情况**：“红书收回书架，再把同一套的另一本拿到书桌上”：另一本红封面的书混在别的书里 → 两个方向的子目标；按封面认出同一套，找遍书架

**指令**：孩子看完这本红书了，收回他的书架，再把同一套的另一本拿到书桌上，他明天看。

**成功条件**：

- `book_red` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`
- `red_book_2` 在 `desk_1/top` 上
- `blue_book_case`、`paperback_shelf` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

- 摆法 `on_bookcase`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=book_red)` → 4. `pick(object=book_red)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=book_red, receptacle=bookcase_2/top, hint_xy=[1.0, -0.55])` → 7. `look(target=bookcase_2/top)` → 8. `navigate(destination=red_book_2)` → 9. `pick(object=red_book_2)` → 10. `navigate(destination=desk_1/top)` → 11. `place(object=red_book_2, receptacle=desk_1/top, hint_xy=[-0.808, -6.166])`
- 摆法 `on_other_bookcase`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=book_red)` → 4. `pick(object=book_red)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=book_red, receptacle=bookcase_2/top, hint_xy=[1.0, -0.55])` → 7. `look(target=bookcase_2/top)` → 8. `search(object=red_book_2, region=bedroom_0_1)` → 9. `look(target=bookcase_3/top)` → 10. `navigate(destination=red_book_2)` → 11. `pick(object=red_book_2)` → 12. `navigate(destination=desk_1/top)` → 13. `place(object=red_book_2, receptacle=desk_1/top, hint_xy=[-0.808, -6.166])`
- 摆法 `on_tall_shelf`：1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=book_red)` → 4. `pick(object=book_red)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=book_red, receptacle=bookcase_2/top, hint_xy=[1.0, -0.55])` → 7. `look(target=bookcase_2/top)` → 8. `search(object=red_book_2, region=bedroom_0_1)` → 9. `look(target=large_shelf_4/shelf_1)` → 10. `navigate(destination=red_book_2)` → 11. `pick(object=red_book_2)` → 12. `navigate(destination=desk_1/top)` → 13. `place(object=red_book_2, receptacle=desk_1/top, hint_xy=[-0.808, -6.166])`

---

## T21_bring_tissues

> 餐桌上洒了点汤，拿点擦的东西过去。

### tissue_on_tv_stand（对照）

**情况**：纸巾盒在电视柜，餐桌上有碗汤 → 拿到餐桌

**成功条件**：

- `tissue` 在 `dining_table_2/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=tissue)` → 4. `pick(object=tissue)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[2.928, 6.655])`

### tissue_out_of_view（Task）

**情况**：纸巾盒不在常放的地方，在书房书桌上 → 先找

**成功条件**：

- `tissue` 在 `dining_table_2/top` 上
- 手里空着

**参考调用顺序**：

1. `search(object=tissue, region=living_room_0_1)` → 2. `navigate(destination=tissue)` → 3. `pick(object=tissue)` → 4. `navigate(destination=dining_table_2/top)` → 5. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[2.928, 6.655])`

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

- 摆法 `east`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=tissue)` → 4. `pick(object=tissue)` → 5. `navigate(destination=dining_table_1/top)` → 6. `look(target=dining_table_1/top)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[2.928, 6.655])`
- 摆法 `west`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=tissue)` → 4. `pick(object=tissue)` → 5. `navigate(destination=dining_table_2/top)` → 6. `look(target=dining_table_2/top)` → 7. `navigate(destination=dining_table_1/top)` → 8. `place(object=tissue, receptacle=dining_table_1/top, hint_xy=[-7.621, 7.409])`

### no_tissue（Task）

**情况**：家里没有纸巾，岛台上有块干海绵 → 拿海绵代替

**指令**：餐桌上洒了点汤，拿个能擦的用具过去。

**成功条件**：

- `spare_sponge` 在 `dining_table_2/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=spare_sponge)` → 4. `pick(object=spare_sponge)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=spare_sponge, receptacle=dining_table_2/top, hint_xy=[2.928, 6.655])`

### tissue_put_away（Task）

**情况**：纸巾收在两个矮柜之一 → 逐个打开找，拿出来后关好门

**指令**：餐桌上洒了点汤，拿点擦的东西过去。纸巾收在柜子里了，拿完把柜门关好。

**成功条件**：

- `tissue` 在 `dining_table_2/top` 上
- `kitchen_cabinet_4` 关着
- `kitchen_cabinet_6` 关着
- 手里空着

**参考调用顺序**：

- 摆法 `in_4`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=tissue)` → 13. `pick(object=tissue)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `navigate(destination=dining_table_2/top)` → 16. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[2.928, 6.655])` → 17. `navigate(destination=kitchen_cabinet_4)` → 18. `close(articulated=kitchen_cabinet_4)`
- 摆法 `in_6`：1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_4)` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=tissue)` → 13. `pick(object=tissue)` → 14. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 15. `navigate(destination=dining_table_2/top)` → 16. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[2.928, 6.655])` → 17. `navigate(destination=kitchen_cabinet_6)` → 18. `close(articulated=kitchen_cabinet_6)`

### the_kids_side（Task）

**情况**：“孩子吃饭把汤洒了，拿点擦的东西过去，放在孩子那一边”：桌上一份有塑料杯（孩子的），一份有马克杯（大人的） → 放到孩子那份旁边

**指令**：孩子吃饭把汤洒了，拿点擦的东西过去，放在孩子那一边。

**成功条件**：

- `tissue` 在 `dining_table_2/top` 上
- `tissue` 离其中至少一个不超过 15 cm：`kid_bowl`、`kid_cup`
- `tissue` 离这些都超过 25 cm：`adult_bowl`、`adult_mug`
- 手里空着

**参考调用顺序**：

- 摆法 `kid_north`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=tissue)` → 4. `pick(object=tissue)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[3.708, 7.555])`
- 摆法 `kid_south`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=tissue)` → 4. `pick(object=tissue)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=tissue, receptacle=dining_table_2/top, hint_xy=[3.708, 6.295])`

---

## T22_put_away_shopping

> 我刚买东西回来，放在餐桌上了，帮我收好。

### juice_on_table（对照）

**情况**：餐桌上一瓶果汁 → 放进冰箱，关门

**成功条件**：

- `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
- `bought_juice` 立着
- `breakfast_fridge` 关着
- `kitchen_cabinet_4` 关着
- `kitchen_cabinet_6` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)`

### by_kind（Task）

**情况**：果汁、苹果、零食盒 → 果汁进冰箱；苹果和零食放进岛台上的果篮或矮柜里都算（参考路线：苹果进果篮，零食进已有一盒零食的矮柜），柜门关好

**指令**：我刚买东西回来，果汁、苹果和零食都在餐桌上。每样都收到平时放同类东西的地方，开过的门记得关上。

**成功条件**：

- `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
- `bought_juice` 立着
- `breakfast_fridge` 关着
- `kitchen_cabinet_4` 关着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_4` 关着
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

**参考调用顺序**：

1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)` → 10. `navigate(destination=bought_apple)` → 11. `pick(object=bought_apple)` → 12. `navigate(destination=home_basket)` → 13. `place(object=bought_apple, receptacle=home_basket)` → 14. `navigate(destination=kitchen_cabinet_6)` → 15. `open(articulated=kitchen_cabinet_6)` → 16. `inspect(receptacle=kitchen_cabinet_6)` → 17. `navigate(destination=bought_snack)` → 18. `pick(object=bought_snack)` → 19. `navigate(destination=kitchen_cabinet_6)` → 20. `place(object=bought_snack, receptacle=kitchen_cabinet_6/inside_shelf, hint_xy=[3.6, 0.36])` → 21. `close(articulated=kitchen_cabinet_6)`

### eat_now（Task）

**情况**：“孩子说零食现在就要吃，他在书房写作业” → 零食送书桌，果汁进冰箱

**指令**：我刚买东西回来，放在餐桌上了，帮我收好。孩子说零食现在就要吃，他在书房写作业。

**成功条件**：

- `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
- `bought_juice` 立着
- `breakfast_fridge` 关着
- `kitchen_cabinet_4` 关着
- `kitchen_cabinet_6` 关着
- `bought_snack` 在 `desk_1/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)` → 10. `navigate(destination=bought_snack)` → 11. `pick(object=bought_snack)` → 12. `navigate(destination=desk_1/top)` → 13. `place(object=bought_snack, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`

### not_shopping（Task）

**情况**：桌上还有孩子的小车和绘本 → 不是买的，不动

**成功条件**：

- `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
- `bought_juice` 立着
- `breakfast_fridge` 关着
- `kitchen_cabinet_4` 关着
- `kitchen_cabinet_6` 关着
- `table_car`、`table_book` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)`

### two_spots（Task）

**情况**：买的东西分在餐桌和岛台两处 → 都找到；果汁进冰箱，苹果和零食放进果篮或矮柜都算，柜门关好

**指令**：我刚买东西回来，两袋东西拆开放在了两个不同的地方，买的东西都帮我收好。

**成功条件**：

- `bought_juice` 在其中任一处上：`breakfast_fridge/inside_shelf`、`kitchen_cabinet_4/inside_shelf`、`kitchen_cabinet_6/inside_shelf`、`kitchen_counter_1/top`、`kitchen_counter_2/top`
- `bought_juice` 立着
- `breakfast_fridge` 关着
- `kitchen_cabinet_4` 关着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_4` 关着
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

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)` → 10. `look(target=kitchen_island/top)` → 11. `navigate(destination=bought_apple)` → 12. `pick(object=bought_apple)` → 13. `navigate(destination=home_basket)` → 14. `place(object=bought_apple, receptacle=home_basket)` → 15. `navigate(destination=kitchen_cabinet_6)` → 16. `open(articulated=kitchen_cabinet_6)` → 17. `inspect(receptacle=kitchen_cabinet_6)` → 18. `navigate(destination=bought_snack)` → 19. `pick(object=bought_snack)` → 20. `navigate(destination=kitchen_cabinet_6)` → 21. `place(object=bought_snack, receptacle=kitchen_cabinet_6/inside_shelf, hint_xy=[3.6, 0.36])` → 22. `close(articulated=kitchen_cabinet_6)`

### tray_elsewhere（Action + Task）

**情况**：果汁和苹果在餐桌上，果篮不在；有的摆法岛台上就有托盘（直接用）；其余摆法西边餐厅的桌上有个托盘，到了才看得到上面是什么：一个橙子，或者四本书平铺占满了托盘 → 果篮没有 → 找别的能装水果的（另一个房间的托盘）→ 有橙子：苹果直接放进去（水果可以放一起，不用挪）；被书占满：先把书放回那个房间的书架（任何书架都算），再放苹果；果汁进冰箱。挪书属于“目的地被占”（A），去别的房间找替代容器是独立的 Task 要求，所以是 A+T

**指令**：我刚买东西回来，果汁和苹果放在餐桌上了，帮我收好。水果平时放在果篮里。

**成功条件**：

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

**参考调用顺序**：

- 摆法 `orange_in_it`：1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)` → 10. `search(object=west_tray, region=dining_room_0_0)` → 11. `look(target=west_tray)` → 12. `navigate(destination=bought_apple)` → 13. `pick(object=bought_apple)` → 14. `navigate(destination=west_tray)` → 15. `place(object=bought_apple, receptacle=west_tray)`
- 摆法 `books_on_it`：1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)` → 10. `search(object=west_tray, region=dining_room_0_0)` → 11. `look(target=west_tray)` → 12. `navigate(destination=tray_book_1)` → 13. `pick(object=tray_book_1)` → 14. `navigate(destination=bookcase_1/top)` → 15. `place(object=tray_book_1, receptacle=bookcase_1/top, hint_xy=[-9.569, 6.528])` → 16. `navigate(destination=tray_book_2)` → 17. `pick(object=tray_book_2)` → 18. `navigate(destination=bookcase_1/top)` → 19. `place(object=tray_book_2, receptacle=bookcase_1/top, hint_xy=[-9.59, 6.82])` → 20. `navigate(destination=tray_book_3)` → 21. `pick(object=tray_book_3)` → 22. `navigate(destination=bookcase_1/shelf_1)` → 23. `place(object=tray_book_3, receptacle=bookcase_1/shelf_1, hint_xy=[-9.59, 6.52])` → 24. `navigate(destination=tray_book_4)` → 25. `pick(object=tray_book_4)` → 26. `navigate(destination=bookcase_1/shelf_1)` → 27. `place(object=tray_book_4, receptacle=bookcase_1/shelf_1, hint_xy=[-9.59, 6.82])` → 28. `navigate(destination=bought_apple)` → 29. `pick(object=bought_apple)` → 30. `navigate(destination=west_tray)` → 31. `place(object=bought_apple, receptacle=west_tray)`
- 摆法 `basket_missing`：1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=dining_table_2/top)` → 4. `look(target=dining_table_2/top)` → 5. `navigate(destination=bought_juice)` → 6. `pick(object=bought_juice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=bought_juice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)` → 10. `navigate(destination=bought_apple)` → 11. `pick(object=bought_apple)` → 12. `navigate(destination=fruit_tray)` → 13. `place(object=bought_apple, receptacle=fruit_tray)`

---

## T23_pick_up_dropped

> 地上掉了东西，帮忙捡起来放好。

### spoon_on_floor（对照）

**情况**：厨房地上一把勺子 → 放回厨房台面（勺子都放在那）

**成功条件**：

- `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=dropped_spoon)` → 4. `look(target=dropped_spoon)` → 5. `pick(object=dropped_spoon)` → 6. `navigate(destination=kitchen_counter_2/top)` → 7. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.364, 7.609])`

### by_kind（Task）

**情况**：地上有勺子和一块积木 → 勺子回台面，积木进客厅的玩具箱

**成功条件**：

- `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
- `dropped_block` 在 `toy_box` 里
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=dropped_spoon)` → 4. `look(target=dropped_spoon)` → 5. `pick(object=dropped_spoon)` → 6. `navigate(destination=kitchen_counter_2/top)` → 7. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.364, 7.609])` → 8. `navigate(destination=dropped_block)` → 9. `look(target=dropped_block)` → 10. `pick(object=dropped_block)` → 11. `explore_room(room=living_room_0_0)` → 12. `navigate(destination=toy_box)` → 13. `place(object=dropped_block, receptacle=toy_box)`

### belongs_on_floor（Task）

**情况**：勺子旁边还有垃圾桶、洗衣筐 → 它们本来就在地上，不动

**成功条件**：

- `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
- `kitchen_bin`、`laundry_basket` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=dropped_spoon)` → 4. `look(target=dropped_spoon)` → 5. `pick(object=dropped_spoon)` → 6. `navigate(destination=kitchen_counter_2/top)` → 7. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.364, 7.609])`

### dropped_out_of_view（Task）

**情况**：勺子滑到隔壁餐厅地上，看不到 → 找一圈

**成功条件**：

- `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `explore_room(room=dining_room_0_1)` → 4. `navigate(destination=dropped_spoon)` → 5. `look(target=dropped_spoon)` → 6. `pick(object=dropped_spoon)` → 7. `navigate(destination=kitchen_counter_2/top)` → 8. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.364, 7.609])`

### only_this_room（Task）

**情况**：“厨房地上掉了东西”：客厅地上也有小车 → 只捡厨房的

**指令**：厨房地上掉了东西，帮忙捡起来放好。

**成功条件**：

- `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
- `living_car` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=dropped_spoon)` → 4. `look(target=dropped_spoon)` → 5. `pick(object=dropped_spoon)` → 6. `navigate(destination=kitchen_counter_2/top)` → 7. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.364, 7.609])`

### dropped_in_two_rooms（Task）

**情况**：“家里地上掉了些东西”：厨房一把勺子，书房书桌下一支铅笔 → 都找到，勺子放回厨房台面或岛台，铅笔放回书桌

**指令**：家里地上掉了些东西，帮忙捡起来放好。

**成功条件**：

- `dropped_spoon` 在其中任一处上：`kitchen_counter_2/top`、`kitchen_counter_1/top`、`kitchen_island/top`
- `dropped_pencil` 在其中任一处上：`desk_1/top`、`desk_3/top`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=dropped_spoon)` → 4. `look(target=dropped_spoon)` → 5. `pick(object=dropped_spoon)` → 6. `navigate(destination=kitchen_counter_2/top)` → 7. `place(object=dropped_spoon, receptacle=kitchen_counter_2/top, hint_xy=[-0.364, 7.609])` → 8. `explore_room(room=living_room_0_1)` → 9. `navigate(destination=dropped_pencil)` → 10. `look(target=dropped_pencil)` → 11. `pick(object=dropped_pencil)` → 12. `navigate(destination=desk_1/top)` → 13. `place(object=dropped_pencil, receptacle=desk_1/top, hint_xy=[-1.048, -6.146])`

---

## T24_snack_for_kid

> 孩子在书房写作业饿了，给他拿点吃的。

### apple_on_table（对照）

**情况**：餐桌上有苹果 → 送到书房书桌

**成功条件**：

- `snack_apple` 在 `desk_1/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`

### no_apples_for_him（Task）

**情况**：“他不爱吃苹果”：苹果和香蕉 → 拿香蕉

**指令**：孩子在书房写作业饿了，给他拿点吃的。他不爱吃苹果。

**成功条件**：

- `snack_banana` 在 `desk_1/top` 上
- `["not on", "snack_apple", "desk_1/top"]`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_banana)` → 4. `pick(object=snack_banana)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=snack_banana, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`

### dinner_soon（Task）

**情况**：“还有半小时就吃晚饭了”：苹果和零食盒 → 拿苹果，零食别送过去

**指令**：孩子在书房写作业饿了，给他拿点吃的。还有半小时就吃晚饭了。

**成功条件**：

- `snack_apple` 在 `desk_1/top` 上
- `["not on", "snack_box", "desk_1/top"]`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`

### fruit_out_of_view（Task）

**情况**：餐桌上没吃的，果篮在卧室书架上 → 找到果篮拿苹果

**成功条件**：

- `snack_apple` 在 `desk_1/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `search(object=home_basket, region=bedroom_0_1)` → 4. `navigate(destination=bookcase_2/top)` → 5. `look(target=bookcase_2/top)` → 6. `navigate(destination=snack_apple)` → 7. `pick(object=snack_apple)` → 8. `navigate(destination=desk_1/top)` → 9. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`

### where_is_he（Task）

**情况**：指令不说在哪：作业本摊在书房书桌或卧室书桌上 → 送到有作业的那张

**指令**：孩子写作业饿了，给他拿点吃的。

**成功条件**：

- 摆法 `study`：
  - `snack_apple` 在 `desk_1/top` 上
  - 手里空着
- 摆法 `bedroom`：
  - `snack_apple` 在其中任一处上：`desk_3/top`、`bookcase_4/top`
  - 手里空着

**参考调用顺序**：

- 摆法 `study`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_3/top)` → 6. `look(target=desk_3/top)` → 7. `navigate(destination=desk_1/top)` → 8. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])`
- 摆法 `bedroom`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_1/top)` → 6. `look(target=desk_1/top)` → 7. `navigate(destination=desk_3/top)` → 8. `place(object=snack_apple, receptacle=desk_3/top, hint_xy=[6.194, -5.349])`

### two_kids（Task）

**情况**：“孩子们在写作业”：两张书桌都有作业，苹果和香蕉 → 一人一个

**指令**：孩子们在写作业，饿了，给他们拿点吃的。

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `snack_apple` 在 `desk_1/top` 上
    - `snack_banana` 在其中任一处上：`desk_3/top`、`bookcase_4/top`
  - 第 2 组：
    - `snack_banana` 在 `desk_1/top` 上
    - `snack_apple` 在其中任一处上：`desk_3/top`、`bookcase_4/top`

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=snack_apple)` → 4. `pick(object=snack_apple)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=snack_apple, receptacle=desk_1/top, hint_xy=[-1.248, -5.946])` → 7. `navigate(destination=snack_banana)` → 8. `pick(object=snack_banana)` → 9. `navigate(destination=desk_3/top)` → 10. `place(object=snack_banana, receptacle=desk_3/top, hint_xy=[6.194, -5.329])`

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

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 7. `navigate(destination=guest_cup)` → 8. `pick(object=guest_cup)` → 9. `navigate(destination=tv_stand_2/top)` → 10. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])`

### cup_elsewhere（Task）

**情况**：岛台上只有果汁 → 想到要配杯子，去小厨房台面找

**成功条件**：

- `guest_juice` 在 `tv_stand_2/top` 上
- `guest_juice` 立着
- 这 6 件中至少 1 件还在 `tv_stand_2/top` 上：`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 7. `search(object=cup_counter_b, region=kitchen_0_1)` → 8. `navigate(destination=cup_counter_b)` → 9. `pick(object=cup_counter_b)` → 10. `navigate(destination=tv_stand_2/top)` → 11. `place(object=cup_counter_b, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])`

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

1. `navigate(destination=breakfast_fridge)` → 2. `open(articulated=breakfast_fridge)` → 3. `navigate(destination=breakfast_fridge/inside_shelf)` → 4. `look(target=breakfast_fridge/inside_shelf)` → 5. `navigate(destination=cold_juice)` → 6. `pick(object=cold_juice)` → 7. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 8. `navigate(destination=tv_stand_2/top)` → 9. `place(object=cold_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 10. `navigate(destination=breakfast_fridge)` → 11. `close(articulated=breakfast_fridge)` → 12. `navigate(destination=guest_cup)` → 13. `pick(object=guest_cup)` → 14. `navigate(destination=tv_stand_2/top)` → 15. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])`

### drink_in_fridge（Task）

**情况**：外面没有饮料 → 想到饮料在冰箱里

**成功条件**：

- `cold_juice` 在 `tv_stand_2/top` 上
- `cold_juice` 立着
- 这 7 件中至少 1 件还在 `tv_stand_2/top` 上：`guest_cup`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
- `breakfast_fridge` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=breakfast_fridge/inside_shelf)` → 6. `look(target=breakfast_fridge/inside_shelf)` → 7. `navigate(destination=cold_juice)` → 8. `pick(object=cold_juice)` → 9. `retreat(obstacle=breakfast_fridge, distance_m=0.3)` → 10. `navigate(destination=tv_stand_2/top)` → 11. `place(object=cold_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 12. `navigate(destination=breakfast_fridge)` → 13. `close(articulated=breakfast_fridge)` → 14. `navigate(destination=guest_cup)` → 15. `pick(object=guest_cup)` → 16. `navigate(destination=tv_stand_2/top)` → 17. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])`

### cups_for_two（Task）

**情况**：“两位客人在客厅，给他们准备好饮料和杯子，每人一个杯子，尽量用普通杯子；桌上已有的不用重复拿。”客人桌上已有 0–2 个杯子，关着的矮柜里有 1–2 个普通杯，家里别的杯子只有餐厅的马克杯 → 先看桌上缺几个 → 再开柜看库存：够就补普通杯；不够就拿柜里的，再去餐厅拿马克杯补齐；已经齐了就只送饮料。最后正好两个杯子，原有的不动，柜门关好

**指令**：两位客人在客厅，给他们准备好饮料和杯子，每人一个杯子，尽量用普通杯子；桌上已有的不用重复拿。

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

- 摆法 `one_there`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=stock_cup_1)` → 13. `pick(object=stock_cup_1)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `navigate(destination=tv_stand_2/top)` → 16. `place(object=stock_cup_1, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])` → 17. `navigate(destination=kitchen_cabinet_4)` → 18. `close(articulated=kitchen_cabinet_4)`
- 摆法 `none_one_inside`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=stock_cup_1)` → 13. `pick(object=stock_cup_1)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `navigate(destination=tv_stand_2/top)` → 16. `place(object=stock_cup_1, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])` → 17. `navigate(destination=kitchen_cabinet_4)` → 18. `close(articulated=kitchen_cabinet_4)` → 19. `search(object=mug_shelf, region=dining_room_0_1)` → 20. `navigate(destination=mug_shelf)` → 21. `pick(object=mug_shelf)` → 22. `navigate(destination=tv_stand_2/top)` → 23. `place(object=mug_shelf, receptacle=tv_stand_2/top, hint_xy=[7.044, 0.371])`
- 摆法 `none_two_inside`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=stock_cup_1)` → 13. `pick(object=stock_cup_1)` → 14. `navigate(destination=tv_stand_2/top)` → 15. `place(object=stock_cup_1, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])` → 16. `navigate(destination=stock_cup_2)` → 17. `pick(object=stock_cup_2)` → 18. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 19. `navigate(destination=tv_stand_2/top)` → 20. `place(object=stock_cup_2, receptacle=tv_stand_2/top, hint_xy=[7.044, 0.371])` → 21. `navigate(destination=kitchen_cabinet_4)` → 22. `close(articulated=kitchen_cabinet_4)`
- 摆法 `two_there`：1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])`

### two_guests（Task）

**情况**：“两位客人” → 两个杯子

**指令**：两位客人在客厅坐着，给他们拿点喝的。

**成功条件**：

- `guest_juice` 在 `tv_stand_2/top` 上
- `guest_juice` 立着
- 这 8 件中至少 2 件还在 `tv_stand_2/top` 上：`guest_cup`、`guest_cup_2`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 7. `navigate(destination=guest_cup)` → 8. `pick(object=guest_cup)` → 9. `navigate(destination=tv_stand_2/top)` → 10. `place(object=guest_cup, receptacle=tv_stand_2/top, hint_xy=[7.544, 0.371])` → 11. `navigate(destination=guest_cup_2)` → 12. `pick(object=guest_cup_2)` → 13. `navigate(destination=tv_stand_2/top)` → 14. `place(object=guest_cup_2, receptacle=tv_stand_2/top, hint_xy=[7.804, 0.371])`

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

1. `navigate(destination=kitchen_island/top)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=guest_juice)` → 4. `pick(object=guest_juice)` → 5. `navigate(destination=tv_stand_2/top)` → 6. `place(object=guest_juice, receptacle=tv_stand_2/top, hint_xy=[7.3, 0.36])` → 7. `navigate(destination=kid_cup)` → 8. `pick(object=kid_cup)` → 9. `navigate(destination=tv_stand_2/top)` → 10. `place(object=kid_cup, receptacle=tv_stand_2/top, hint_xy=[7.55, 0.36])`

---

## T26_kids_things_to_room

> 把孩子落在客厅的东西拿回他房间。

### car_in_living_room（对照）

**情况**：小车在客厅地上 → 放进他卧室的玩具筐

**成功条件**：

- `living_car` 在 `kids_basket` 里
- 手里空着

**参考调用顺序**：

1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `look(target=living_car)` → 4. `pick(object=living_car)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=kids_basket)` → 7. `place(object=living_car, receptacle=kids_basket)`

### whose（Task）

**情况**：电视柜上有一本和他书架上一样的蓝色精装书，还有一本大人的平装书 → 只拿他的那本，放到他房间的书架上（两个书架、任一层都算），平装书不动

**成功条件**：

- `kid_book` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
- `adult_novel` 没被挪动（离开局位置不超过 3 cm）
- 手里空着

**参考调用顺序**：

1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=kid_book)` → 4. `pick(object=kid_book)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=kid_book, receptacle=bookcase_2/top, hint_xy=[1.12, -0.43])`

### scattered（Task）

**情况**：小车在地上、鸭子在电视柜、积木在岛台 → 都找到放进筐

**成功条件**：

- `living_car` 在 `kids_basket` 里
- `living_duck` 在 `kids_basket` 里
- `living_block` 在 `kids_basket` 里
- 手里空着

**参考调用顺序**：

1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `look(target=living_car)` → 4. `pick(object=living_car)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=kids_basket)` → 7. `place(object=living_car, receptacle=kids_basket)` → 8. `navigate(destination=living_duck)` → 9. `pick(object=living_duck)` → 10. `navigate(destination=kids_basket)` → 11. `place(object=living_duck, receptacle=kids_basket)` → 12. `navigate(destination=living_block)` → 13. `pick(object=living_block)` → 14. `navigate(destination=kids_basket)` → 15. `place(object=living_block, receptacle=kids_basket)`

### where_in_room（Task）

**情况**：小车和他的一本书 → 小车进筐，书放到他房间的书架上（两个书架、任一层都算）

**成功条件**：

- `living_car` 在 `kids_basket` 里
- `kid_book` 在其中任一处上：`bookcase_2/top`、`bookcase_2/shelf_1`、`bookcase_2/shelf_0`、`bookcase_3/top`、`bookcase_3/shelf_1`、`bookcase_3/shelf_0`
- 手里空着

**参考调用顺序**：

1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `look(target=living_car)` → 4. `pick(object=living_car)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=kids_basket)` → 7. `place(object=living_car, receptacle=kids_basket)` → 8. `navigate(destination=kid_book)` → 9. `pick(object=kid_book)` → 10. `navigate(destination=bookcase_2/top)` → 11. `place(object=kid_book, receptacle=bookcase_2/top, hint_xy=[1.12, -0.43])`

### bear_to_bed（Task）

**情况**：“孩子要睡觉了”：小熊在电视柜 → 放到他床上或床头书架上，不放筐里

**指令**：孩子要睡觉了，把他落在客厅的东西拿回他房间。

**成功条件**：

- `living_bear` 在其中任一处上：`mattress_1/top`、`bookcase_3/top`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=tv_stand_2/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=living_bear)` → 4. `pick(object=living_bear)` → 5. `navigate(destination=bookcase_3/top)` → 6. `place(object=living_bear, receptacle=bookcase_3/top, hint_xy=[2.1, -4.78])`

### two_bedrooms（Task）

**情况**：两间卧室，有他玩具筐的那间是他的 → 认出来，把小车放进去

**成功条件**：

- `living_car` 在 `kids_basket` 里
- 手里空着

**参考调用顺序**：

- 摆法 `room_east`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `look(target=living_car)` → 4. `pick(object=living_car)` → 5. `explore_room(room=bedroom_0_1)` → 6. `navigate(destination=kids_basket)` → 7. `place(object=living_car, receptacle=kids_basket)`
- 摆法 `room_south`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=living_car)` → 3. `look(target=living_car)` → 4. `pick(object=living_car)` → 5. `explore_room(room=bedroom_0_0)` → 6. `navigate(destination=kids_basket)` → 7. `place(object=living_car, receptacle=kids_basket)`

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

**情况**：桌上除了剩饭还有不该进冰箱的东西：一个空外卖盒，或者果篮和麦片盒，或者一碗有人还在吃的燕麦（勺子摆在碗前） → 只把剩饭收进冰箱；空外卖盒、果篮、麦片都不进冰箱，正在吃的那碗不收也不拿起来（过程要求）

**成功条件**：

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

**参考调用顺序**：

- 摆法 `which_is_leftover`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=leftover_rice)` → 6. `pick(object=leftover_rice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)`
- 摆法 `fruit_stays_out`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=leftover_rice)` → 6. `pick(object=leftover_rice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)`
- 摆法 `still_eating`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=leftover_rice)` → 6. `pick(object=leftover_rice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `close(articulated=breakfast_fridge)`

### two_leftovers（Task）

**情况**：剩饭和一锅剩汤 → 都收（汤可能还在灶上，不在桌上）

**成功条件**：

- `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
- `breakfast_fridge` 关着
- `leftover_soup` 在 `breakfast_fridge/inside_shelf` 上
- `leftover_soup` 立着
- 手里空着

**参考调用顺序**：

- 摆法 `soup_on_table`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=breakfast_fridge)` → 4. `open(articulated=breakfast_fridge)` → 5. `navigate(destination=leftover_rice)` → 6. `pick(object=leftover_rice)` → 7. `navigate(destination=breakfast_fridge)` → 8. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 9. `navigate(destination=leftover_soup)` → 10. `pick(object=leftover_soup)` → 11. `navigate(destination=breakfast_fridge)` → 12. `place(object=leftover_soup, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.98, 3.18])` → 13. `close(articulated=breakfast_fridge)`
- 摆法 `soup_on_stove`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=kitchen_stove/top)` → 4. `look(target=kitchen_stove/top)` → 5. `navigate(destination=breakfast_fridge)` → 6. `open(articulated=breakfast_fridge)` → 7. `navigate(destination=leftover_rice)` → 8. `pick(object=leftover_rice)` → 9. `navigate(destination=breakfast_fridge)` → 10. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 11. `navigate(destination=leftover_soup)` → 12. `pick(object=leftover_soup)` → 13. `navigate(destination=breakfast_fridge)` → 14. `place(object=leftover_soup, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.98, 3.18])` → 15. `close(articulated=breakfast_fridge)`

### fridge_out_of_view（Task）

**情况**：从餐厅出发，看不到冰箱 → 先找到冰箱

**成功条件**：

- `leftover_rice` 在 `breakfast_fridge/inside_shelf` 上
- `breakfast_fridge` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `explore_room(room=living_room_0_0)` → 4. `navigate(destination=breakfast_fridge)` → 5. `open(articulated=breakfast_fridge)` → 6. `navigate(destination=leftover_rice)` → 7. `pick(object=leftover_rice)` → 8. `navigate(destination=breakfast_fridge)` → 9. `place(object=leftover_rice, receptacle=breakfast_fridge/inside_shelf, hint_xy=[5.78, 3.18])` → 10. `close(articulated=breakfast_fridge)`

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

1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=kid_cup)` → 4. `pick(object=kid_cup)` → 5. `navigate(destination=bookcase_3/top)` → 6. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.093, -4.837])`

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

- 摆法 `east`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=kid_cup)` → 4. `pick(object=kid_cup)` → 5. `navigate(destination=mattress_2/top)` → 6. `look(target=mattress_2/top)` → 7. `navigate(destination=bookcase_3/top)` → 8. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.093, -4.837])`
- 摆法 `south`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=kid_cup)` → 4. `pick(object=kid_cup)` → 5. `navigate(destination=mattress_1/top)` → 6. `look(target=mattress_1/top)` → 7. `navigate(destination=cell_shelf_2/top)` → 8. `place(object=kid_cup, receptacle=cell_shelf_2/top, hint_xy=[1.491, -10.846])`

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

- 摆法 `on_counter`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=kid_cup)` → 4. `pick(object=kid_cup)` → 5. `navigate(destination=bookcase_3/top)` → 6. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.093, -4.837])`
- 摆法 `in_cabinet`：1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `navigate(destination=kitchen_cabinet_4)` → 4. `open(articulated=kitchen_cabinet_4)` → 5. `bend()` → 6. `explore_furniture(furniture=kitchen_cabinet_4)` → 7. `straighten()` → 8. `navigate(destination=kid_cup)` → 9. `pick(object=kid_cup)` → 10. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 11. `navigate(destination=bookcase_3/top)` → 12. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.093, -4.837])` → 13. `navigate(destination=kitchen_cabinet_4)` → 14. `close(articulated=kitchen_cabinet_4)`

### cup_out_of_view（Task）

**情况**：杯子落在餐桌上，看不到 → 先找

**成功条件**：

- `kid_cup` 在其中任一处上：`bookcase_3/top`、`desk_1/top`
- `kid_cup` 立着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_counter_2/top)` → 2. `look(target=kitchen_counter_2/top)` → 3. `search(object=kid_cup, region=dining_room_0_1)` → 4. `navigate(destination=kid_cup)` → 5. `pick(object=kid_cup)` → 6. `navigate(destination=bookcase_3/top)` → 7. `place(object=kid_cup, receptacle=bookcase_3/top, hint_xy=[2.093, -4.837])`

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

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=table_car)` → 4. `pick(object=table_car)` → 5. `navigate(destination=toy_box)` → 6. `place(object=table_car, receptacle=toy_box)`

### belongs_on_table（Task）

**情况**：桌上摆着碗和勺子（吃饭用的），有时还有一辆玩具车 → 吃饭用的留下，有玩具就拿回玩具箱，没有就什么都不用做

**成功条件**：

- 摆法 `belongs_on_table`：
  - `table_car` 在 `toy_box` 里
  - `set_bowl`、`set_spoon` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `nothing_to_clear`：
  - `set_bowl`、`set_spoon` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着

**参考调用顺序**：

- 摆法 `belongs_on_table`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=table_car)` → 4. `pick(object=table_car)` → 5. `navigate(destination=toy_box)` → 6. `place(object=table_car, receptacle=toy_box)`
- 摆法 `nothing_to_clear`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)`

### homework_on_table（Task）

**情况**：作业本和铅笔 → 拿回书房书桌

**成功条件**：

- `hw_notebook` 在 `desk_1/top` 上
- `hw_pencil` 在 `desk_1/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=hw_notebook)` → 4. `pick(object=hw_notebook)` → 5. `navigate(destination=desk_1/top)` → 6. `place(object=hw_notebook, receptacle=desk_1/top, hint_xy=[-0.708, -6.166])` → 7. `navigate(destination=hw_pencil)` → 8. `pick(object=hw_pencil)` → 9. `navigate(destination=desk_1/top)` → 10. `place(object=hw_pencil, receptacle=desk_1/top, hint_xy=[-0.188, -5.946])`

### several（Task）

**情况**：玩具车、一本书、一个空罐子 → 玩具进玩具箱，书放到任一书架上，空罐扔垃圾桶

**成功条件**：

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

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=table_car)` → 4. `pick(object=table_car)` → 5. `navigate(destination=toy_box)` → 6. `place(object=table_car, receptacle=toy_box)` → 7. `navigate(destination=empty_can)` → 8. `pick(object=empty_can)` → 9. `navigate(destination=trash_can)` → 10. `drop(object=empty_can, container=trash_can)` → 11. `navigate(destination=table_book)` → 12. `pick(object=table_book)` → 13. `navigate(destination=bookcase_2/top)` → 14. `place(object=table_book, receptacle=bookcase_2/top, hint_xy=[1.005, -0.479])`

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

- 摆法 `east`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=dining_table_1/top)` → 4. `look(target=dining_table_1/top)` → 5. `navigate(destination=toy_east)` → 6. `pick(object=toy_east)` → 7. `navigate(destination=toy_box)` → 8. `place(object=toy_east, receptacle=toy_box)`
- 摆法 `west`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=dining_table_1/top)` → 4. `look(target=dining_table_1/top)` → 5. `navigate(destination=toy_west)` → 6. `pick(object=toy_west)` → 7. `navigate(destination=toy_box)` → 8. `place(object=toy_west, receptacle=toy_box)`

---

## T30_bowls_for_soup

> 汤快好了，拿碗过来准备盛。

### bowl_on_cabinet（对照）

**情况**：靠墙矮柜上一个干净碗 → 拿到岛台

**成功条件**：

- 这 5 件中至少 1 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=soup_bowl_1)` → 4. `pick(object=soup_bowl_1)` → 5. `navigate(destination=kitchen_island/top)` → 6. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[8.06, 1.675])`

### how_many（Task）

**情况**：餐桌上摆了三把勺子 → 拿三个碗

**成功条件**：

- 这 7 件中至少 3 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`soup_bowl_2`、`soup_bowl_3`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=soup_bowl_1)` → 4. `pick(object=soup_bowl_1)` → 5. `navigate(destination=kitchen_island/top)` → 6. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[7.66, 1.675])` → 7. `navigate(destination=soup_bowl_2)` → 8. `pick(object=soup_bowl_2)` → 9. `navigate(destination=kitchen_island/top)` → 10. `place(object=soup_bowl_2, receptacle=kitchen_island/top, hint_xy=[7.86, 1.675])` → 11. `navigate(destination=soup_bowl_3)` → 12. `pick(object=soup_bowl_3)` → 13. `navigate(destination=kitchen_island/top)` → 14. `place(object=soup_bowl_3, receptacle=kitchen_island/top, hint_xy=[8.06, 1.675])`

### bowls_in_cabinet（Task）

**情况**：“汤快好了，拿碗过来准备盛。”餐桌摆了三把勺子；矮柜上一个碗和一个马克杯；柜里还有两个碗，或者只有一个；家里没有别的碗 → 要三个 → 外面只有一个，打开柜子 → 两个碗：拿三个碗；一个碗：两碗不够，自己想到马克杯也能盛汤（盘子不行），补上马克杯，关门

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

- 摆法 `two_inside`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=soup_bowl_1)` → 4. `pick(object=soup_bowl_1)` → 5. `navigate(destination=kitchen_island/top)` → 6. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[7.66, 1.675])` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=soup_bowl_2)` → 13. `pick(object=soup_bowl_2)` → 14. `navigate(destination=kitchen_island/top)` → 15. `place(object=soup_bowl_2, receptacle=kitchen_island/top, hint_xy=[7.86, 1.675])` → 16. `navigate(destination=soup_bowl_3)` → 17. `pick(object=soup_bowl_3)` → 18. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 19. `navigate(destination=kitchen_island/top)` → 20. `place(object=soup_bowl_3, receptacle=kitchen_island/top, hint_xy=[8.06, 1.675])` → 21. `navigate(destination=kitchen_cabinet_6)` → 22. `close(articulated=kitchen_cabinet_6)`
- 摆法 `one_inside`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=soup_bowl_1)` → 4. `pick(object=soup_bowl_1)` → 5. `navigate(destination=kitchen_island/top)` → 6. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[7.66, 1.675])` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=soup_bowl_2)` → 13. `pick(object=soup_bowl_2)` → 14. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 15. `navigate(destination=kitchen_island/top)` → 16. `place(object=soup_bowl_2, receptacle=kitchen_island/top, hint_xy=[7.86, 1.675])` → 17. `navigate(destination=kitchen_cabinet_6)` → 18. `close(articulated=kitchen_cabinet_6)` → 19. `navigate(destination=spare_mug)` → 20. `pick(object=spare_mug)` → 21. `navigate(destination=kitchen_island/top)` → 22. `place(object=spare_mug, receptacle=kitchen_island/top, hint_xy=[8.06, 1.655])`

### bowl_put_away（Task）

**情况**：碗收在矮柜里 → 打开找，拿出来关好

**成功条件**：

- 这 5 件中至少 1 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
- `kitchen_cabinet_4` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `navigate(destination=soup_bowl_1)` → 7. `pick(object=soup_bowl_1)` → 8. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 9. `navigate(destination=kitchen_island/top)` → 10. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[8.06, 1.675])` → 11. `navigate(destination=kitchen_cabinet_4)` → 12. `close(articulated=kitchen_cabinet_4)`

### no_bowl（Task）

**情况**：家里没有干净碗了，柜上有马克杯和盘子 → 拿马克杯（能盛汤）

**成功条件**：

- 这 7 件中至少 1 件还在 `kitchen_island/top` 上：`spare_mug`、`cup_counter_b`、`cup_kitchen_cabinet`、`cup_side_table`、`mug_dining_cabinet`、`mug_shelf`、`mug_counter`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=spare_mug)` → 4. `pick(object=spare_mug)` → 5. `navigate(destination=kitchen_island/top)` → 6. `place(object=spare_mug, receptacle=kitchen_island/top, hint_xy=[8.06, 1.655])`

### bowl_not_plate（Task）

**情况**：干净碗旁边放着不能用来盛汤的东西：一个盘子，或者一碗还装着燕麦的碗 → 拿那个干净的空碗，别的不动

**成功条件**：

- 摆法 `clean_one`：
  - 这 5 件中至少 1 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
  - `full_bowl` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着
- 摆法 `bowl_not_plate`：
  - 这 5 件中至少 1 件还在 `kitchen_island/top` 上：`soup_bowl_1`、`bowl_dining_cabinet`、`bowl_kitchen_cabinet`、`bowl_side_table`、`bowl_inside_kitchen_cabinet`
  - `spare_plate` 没被挪动（离开局位置不超过 3 cm）
  - 手里空着

**参考调用顺序**：

- 摆法 `bowl_not_plate`：1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=soup_bowl_1)` → 4. `pick(object=soup_bowl_1)` → 5. `navigate(destination=kitchen_island/top)` → 6. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[8.06, 1.675])`
- 摆法 `clean_one`：1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=soup_bowl_1)` → 4. `pick(object=soup_bowl_1)` → 5. `navigate(destination=kitchen_island/top)` → 6. `place(object=soup_bowl_1, receptacle=kitchen_island/top, hint_xy=[8.06, 1.675])`

