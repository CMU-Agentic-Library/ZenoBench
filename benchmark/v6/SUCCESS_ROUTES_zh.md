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

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `approach(target=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.5])`

### no_overhang（Action）

**情况**：书只探出 1.5 cm，夹不住 → 先把书推出边缘再抓

**成功条件**：

- `paperback_book` 在 `dining_table_2/top` 上
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `pick(object=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)`（补救） → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.5])`

### table_seats（Task）

**情况**：指令要求把书放在某位客人吃饭的位置旁边、和餐具留出空隙，但没说是哪个空位。餐桌东侧摆了三人份早餐（每个座位一个盘子或碗加一个杯子，另有两盒麦片），桌边有好几个空位：两套餐具之间的窄缝（放得下但会挨着餐具）、两盒麦片之间或桌子尽头的大空地（离座位远），还有一个座位旁边够宽的空位 → 看清桌面，自己判断哪个空位既在客人座位旁边、又放得下、和餐具留得出空隙，放在那里

**指令**：餐桌上已经给客人摆好了早餐。请把岛台上的书拿过去，放在某位客人吃饭的位置旁边，方便边吃边看；书和餐具之间要留出空隙，不要挨着。

**成功条件**：

- `paperback_book` 在 `dining_table_2/top` 上
- `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
- `paperback_book` 离其中至少一个不超过 15 cm：`bowl_side_table`、`plate_counter_a`、`plate_counter_b`
- `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
- `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
- 手里空着

**参考调用顺序**：

- 摆法 `seats_a`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `approach(target=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.059])`
- 摆法 `seats_b`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `approach(target=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.138])`
- 摆法 `seats_c`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `approach(target=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.779])`

### seat_slot_blocked（Action + Task）

**情况**：摆法同 table_seats（第一种），但座位旁那个宽空位中间放着一盒麦片，桌上没有合适的空位 → 先把书暂放在桌子南端，把麦片往桌子里面挪，再把书放进座位旁的空位

**指令**：餐桌上已经给客人摆好了早餐。请把岛台上的书拿过去，放在某位客人吃饭的位置旁边，方便边吃边看；书和餐具之间要留出空隙，不要挨着。

**成功条件**：

- `paperback_book` 在 `dining_table_2/top` 上
- `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
- `paperback_book` 离其中至少一个不超过 15 cm：`bowl_side_table`、`plate_counter_a`、`plate_counter_b`
- `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`spoon_target_table` 没被挪动（离开局位置不超过 3 cm）
- `clutter_cereal_b` 在 `dining_table_2/top` 上
- `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `approach(target=paperback_book)` → 4. `look(target=paperback_book)`（补救） → 5. `pick(object=paperback_book)` → 6. `navigate(destination=dining_table_2/top)` → 7. `look(target=dining_table_2/top)` → 8. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 5.67])` → 9. `pick(object=clutter_cereal_b)`（补救） → 10. `place(object=clutter_cereal_b, receptacle=dining_table_2/top, hint_xy=[3.4, 7.059])`（补救） → 11. `approach(target=paperback_book)`（补救） → 12. `look(target=paperback_book)`（补救） → 13. `pick(object=paperback_book)`（补救） → 14. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.059])`

### which_table（Action + Task）

**情况**：书平放在岛台上没探出边缘；家里有两张餐桌（近的在隔壁餐厅约 6 m，远的在西边另一间餐厅约 16 m），早餐只摆在其中一张上（三人份，和 table_seats 一样只有一个座位旁的合适空位），另一张上是孩子的积木和储物箱，桌边也有空位；指令只说放到客人吃饭的那张桌子上 → 原地把书推出边缘抓起，先到近桌看，没摆早餐就改去另一间餐厅，在摆了早餐的桌子上选座位旁的空位放下；放到另一张桌子上算失败

**指令**：客人正在吃早饭。把岛台上的书拿到他们吃饭的那张桌子上，放在某位客人的位置旁边，方便边吃边看；书和餐具之间要留出空隙，不要挨着。

**成功条件**：

- 摆法 `far_a`、`far_b`：
  - `paperback_book` 在 `dining_table_1/top` 上
  - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`spoon_target_table`
  - `paperback_book` 离其中至少一个不超过 15 cm：`bowl_side_table`、`plate_counter_a`、`plate_counter_b`
  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`spoon_target_table`、`wide_storage_bin`、`clutter_cereal_b`、`wooden_block_a`、`wooden_block_b` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a` 立着
  - 手里空着
- 摆法 `near_a`、`near_b`：
  - `paperback_book` 在 `dining_table_2/top` 上
  - `paperback_book` 离这些东西都至少 5 cm：`plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`
  - `paperback_book` 离其中至少一个不超过 15 cm：`bowl_side_table`、`plate_counter_a`、`plate_counter_b`
  - `plate_counter_a`、`plate_counter_b`、`bowl_side_table`、`cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b`、`spoon_target_table`、`wide_storage_bin`、`wooden_block_a`、`wooden_block_b` 没被挪动（离开局位置不超过 3 cm）
  - `cup_side_table`、`cup_counter_b`、`mug_dining_cabinet`、`clutter_cereal_a`、`clutter_cereal_b` 立着
  - 手里空着

**参考调用顺序**：

- 摆法 `near_a`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `pick(object=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)`（补救） → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 7.059])`
- 摆法 `near_b`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `pick(object=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)`（补救） → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.138])`
- 摆法 `far_a`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `pick(object=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)`（补救） → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `navigate(destination=dining_table_1/top)` → 10. `look(target=dining_table_1/top)` → 11. `place(object=paperback_book, receptacle=dining_table_1/top, hint_xy=[-7.607, 8.179])`
- 摆法 `far_b`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=paperback_book)` → 3. `pick(object=paperback_book)` → 4. `expose(object=paperback_book)` → 5. `look(target=paperback_book)`（补救） → 6. `pick(object=paperback_book)` → 7. `navigate(destination=dining_table_2/top)` → 8. `look(target=dining_table_2/top)` → 9. `navigate(destination=dining_table_1/top)` → 10. `look(target=dining_table_1/top)` → 11. `place(object=paperback_book, receptacle=dining_table_1/top, hint_xy=[-7.607, 7.508])`

### x6_dr_block_on_book__block（Action）

**情况**：书上压着积木 → 先拿开积木放在岛台上，再拿书

**成功条件**：

- `paperback_book` 在 `dining_table_2/top` 上
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)`（补救） → 3. `pick(object=wooden_block_a)`（补救） → 4. `place(object=wooden_block_a, receptacle=kitchen_island/top, hint_xy=[7.2, 1.85])`（补救） → 5. `navigate(destination=paperback_book)` → 6. `approach(target=paperback_book)` → 7. `look(target=paperback_book)`（补救） → 8. `pick(object=paperback_book)` → 9. `navigate(destination=dining_table_2/top)` → 10. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.5])`

### x6_dr_block_on_book__sponge（Action）

**情况**：书上压着海绵 → 先拿开海绵，再拿书

**成功条件**：

- `paperback_book` 在 `dining_table_2/top` 上
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=kitchen_sponge)`（补救） → 3. `pick(object=kitchen_sponge)`（补救） → 4. `place(object=kitchen_sponge, receptacle=kitchen_island/top, hint_xy=[7.2, 1.85])`（补救） → 5. `navigate(destination=paperback_book)` → 6. `approach(target=paperback_book)` → 7. `look(target=paperback_book)`（补救） → 8. `pick(object=paperback_book)` → 9. `navigate(destination=dining_table_2/top)` → 10. `place(object=paperback_book, receptacle=dining_table_2/top, hint_xy=[3.72, 6.5])`

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

### crowded（Action）

**情况**：B 被燕麦碗和擀面杖夹住（缝只有 3 mm），手指插不进去 → 先把 B 拨出来再抓

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `wooden_block_b` 叠在 `wooden_block_a` 上
  - 第 2 组：
    - `wooden_block_a` 叠在 `wooden_block_b` 上

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_b)` → 3. `pick(object=wooden_block_b)` → 4. `separate(object=wooden_block_b)` → 5. `look(target=wooden_block_b)`（补救） → 6. `pick(object=wooden_block_b)` → 7. `rotate(object=wooden_block_b, degrees=30)` → 8. `navigate(destination=wooden_block_a)` → 9. `approach(target=wooden_block_a)` → 10. `stack(object=wooden_block_b, base=wooden_block_a)`

### edge_base（Action）

**情况**：积木 A 在岛台边缘（悬出 5 mm），叠在它上面会倒 → 改为把 A 叠到 B 上

**指令**：请把两块木积木稳稳叠在岛台合适位置，不要碰倒其他物品。

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `wooden_block_b` 叠在 `wooden_block_a` 上
    - `wooden_block_a` 离台面边缘至少 5 cm
  - 第 2 组：
    - `wooden_block_a` 叠在 `wooden_block_b` 上
    - `wooden_block_b` 离台面边缘至少 5 cm

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)`（换做法） → 4. `navigate(destination=wooden_block_b)` → 5. `approach(target=wooden_block_b)` → 6. `stack(object=wooden_block_a, base=wooden_block_b)`（换做法）

### h_dynamic_base_moved_to_edge（Action）

**情况**：拿起 B 后有人把 A 推到岛台边 → 先把 B 放在空处，再把 A 叠到 B 上

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `wooden_block_b` 叠在 `wooden_block_a` 上
  - 第 2 组：
    - `wooden_block_a` 叠在 `wooden_block_b` 上

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_b)` → 3. `pick(object=wooden_block_b)` → 4. `navigate(destination=wooden_block_a)`（补救） → 5. `place(object=wooden_block_b, receptacle=kitchen_island/top, hint_xy=[7.0, 1.66])`（补救） → 6. `navigate(destination=wooden_block_a)`（补救） → 7. `pick(object=wooden_block_a)`（补救） → 8. `navigate(destination=wooden_block_b)`（补救） → 9. `approach(target=wooden_block_b)`（补救） → 10. `stack(object=wooden_block_a, base=wooden_block_b)`（补救）

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

- 摆法 `duck`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_b)` → 3. `pick(object=wooden_block_b)` → 4. `rotate(object=wooden_block_b, degrees=30)` → 5. `navigate(destination=wooden_block_a)` → 6. `stack(object=wooden_block_b, base=wooden_block_a)` → 7. `search(object=rubber_duck, region=dining_room_0_1)`（补救） → 8. `navigate(destination=rubber_duck)`（补救） → 9. `pick(object=rubber_duck)`（补救） → 10. `navigate(destination=wooden_block_a)`（补救） → 11. `approach(target=wooden_block_a)`（补救） → 12. `stack(object=rubber_duck, base=wooden_block_b)`（补救）
- 摆法 `toy_block`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_b)` → 3. `pick(object=wooden_block_b)` → 4. `rotate(object=wooden_block_b, degrees=30)` → 5. `navigate(destination=wooden_block_a)` → 6. `stack(object=wooden_block_b, base=wooden_block_a)` → 7. `search(object=toy_block, region=kitchen_0_1)`（补救） → 8. `navigate(destination=toy_block)`（补救） → 9. `pick(object=toy_block)`（补救） → 10. `navigate(destination=wooden_block_a)`（补救） → 11. `approach(target=wooden_block_a)`（补救） → 12. `stack(object=toy_block, base=wooden_block_b)`（补救）

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

- 摆法 `counter`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=dining_table_2/top)` → 5. `look(target=dining_table_2/top)` → 6. `place(object=wooden_block_a, receptacle=dining_table_2/top, hint_xy=[3.7, 6.6])` → 7. `search(object=wooden_block_b, region=living_room_0_0)` → 8. `navigate(destination=wooden_block_b)` → 9. `pick(object=wooden_block_b)` → 10. `navigate(destination=wooden_block_a)` → 11. `approach(target=wooden_block_a)` → 12. `stack(object=wooden_block_b, base=wooden_block_a)` → 13. `search(object=floor_block, region=kitchen_0_1)` → 14. `navigate(destination=floor_block)` → 15. `pick(object=floor_block)` → 16. `navigate(destination=wooden_block_a)` → 17. `approach(target=wooden_block_a)` → 18. `stack(object=floor_block, base=wooden_block_b)`
- 摆法 `study`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=dining_table_2/top)` → 5. `look(target=dining_table_2/top)` → 6. `place(object=wooden_block_a, receptacle=dining_table_2/top, hint_xy=[3.7, 6.6])` → 7. `search(object=floor_block, region=living_room_0_0)` → 8. `navigate(destination=floor_block)` → 9. `pick(object=floor_block)` → 10. `navigate(destination=wooden_block_a)` → 11. `approach(target=wooden_block_a)` → 12. `stack(object=floor_block, base=wooden_block_a)` → 13. `search(object=wooden_block_b, region=living_room_0_1)` → 14. `navigate(destination=wooden_block_b)` → 15. `pick(object=wooden_block_b)` → 16. `navigate(destination=wooden_block_a)` → 17. `approach(target=wooden_block_a)` → 18. `stack(object=wooden_block_b, base=floor_block)`

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

- 摆法 `counter`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=dining_table_2/top)` → 5. `look(target=dining_table_2/top)` → 6. `place(object=wooden_block_a, receptacle=dining_table_2/top, hint_xy=[3.7, 6.6])` → 7. `search(object=wooden_block_b, region=living_room_0_0)` → 8. `navigate(destination=wooden_block_b)` → 9. `pick(object=wooden_block_b)` → 10. `navigate(destination=wooden_block_a)` → 11. `approach(target=wooden_block_a)` → 12. `stack(object=wooden_block_b, base=wooden_block_a)` → 13. `search(object=rubber_duck, region=kitchen_0_1)` → 14. `navigate(destination=rubber_duck)` → 15. `pick(object=rubber_duck)` → 16. `navigate(destination=wooden_block_a)` → 17. `approach(target=wooden_block_a)` → 18. `stack(object=rubber_duck, base=wooden_block_b)`
- 摆法 `study`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=dining_table_2/top)` → 5. `look(target=dining_table_2/top)` → 6. `place(object=wooden_block_a, receptacle=dining_table_2/top, hint_xy=[3.7, 6.6])` → 7. `search(object=wooden_block_b, region=living_room_0_1)` → 8. `navigate(destination=wooden_block_b)` → 9. `pick(object=wooden_block_b)` → 10. `navigate(destination=wooden_block_a)` → 11. `approach(target=wooden_block_a)` → 12. `stack(object=wooden_block_b, base=wooden_block_a)` → 13. `search(object=rubber_duck, region=living_room_0_0)` → 14. `navigate(destination=rubber_duck)` → 15. `pick(object=rubber_duck)` → 16. `navigate(destination=wooden_block_a)` → 17. `approach(target=wooden_block_a)` → 18. `stack(object=rubber_duck, base=wooden_block_b)`

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

- 摆法 `in_4`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)`（换做法） → 4. `navigate(destination=wooden_block_b)` → 5. `approach(target=wooden_block_b)` → 6. `stack(object=wooden_block_a, base=wooden_block_b)`（换做法） → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `close(articulated=kitchen_cabinet_6)` → 13. `navigate(destination=kitchen_cabinet_4)` → 14. `open(articulated=kitchen_cabinet_4)` → 15. `bend()` → 16. `explore_furniture(furniture=kitchen_cabinet_4)` → 17. `straighten()` → 18. `navigate(destination=floor_block)` → 19. `pick(object=floor_block)` → 20. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 21. `close(articulated=kitchen_cabinet_4)` → 22. `navigate(destination=wooden_block_a)` → 23. `approach(target=wooden_block_a)` → 24. `stack(object=floor_block, base=wooden_block_a)`
- 摆法 `in_6`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)`（换做法） → 4. `navigate(destination=wooden_block_b)` → 5. `approach(target=wooden_block_b)` → 6. `stack(object=wooden_block_a, base=wooden_block_b)`（换做法） → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `close(articulated=kitchen_cabinet_4)` → 13. `navigate(destination=kitchen_cabinet_6)` → 14. `open(articulated=kitchen_cabinet_6)` → 15. `bend()` → 16. `explore_furniture(furniture=kitchen_cabinet_6)` → 17. `straighten()` → 18. `navigate(destination=floor_block)` → 19. `pick(object=floor_block)` → 20. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 21. `close(articulated=kitchen_cabinet_6)` → 22. `navigate(destination=wooden_block_a)` → 23. `approach(target=wooden_block_a)` → 24. `stack(object=floor_block, base=wooden_block_a)`

### x6_gd_tower_with_event（Action + Task）

**情况**：三块积木搭成一座塔，其中一块在岛台边上（不能当底座）；叠好两块后孩子把第三块拿走 → 找回第三块接着叠

**指令**：Tidy the toy blocks on the kitchen island: stack all three wooden blocks steadily into one tower on the island.

**成功条件**：

- 手里空着
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

- 摆法 `tv_stand`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)`（补救） → 3. `pick(object=wooden_block_a)`（补救） → 4. `navigate(destination=wooden_block_b)`（补救） → 5. `approach(target=wooden_block_b)`（补救） → 6. `stack(object=wooden_block_a, base=wooden_block_b)`（补救） → 7. `search(object=floor_block, region=living_room_0_0)`（补救） → 8. `navigate(destination=floor_block)`（补救） → 9. `pick(object=floor_block)`（补救） → 10. `navigate(destination=wooden_block_b)`（补救） → 11. `approach(target=wooden_block_b)`（补救） → 12. `stack(object=floor_block, base=wooden_block_a)`（补救）
- 摆法 `dining`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)`（补救） → 3. `pick(object=wooden_block_a)`（补救） → 4. `navigate(destination=wooden_block_b)`（补救） → 5. `approach(target=wooden_block_b)`（补救） → 6. `stack(object=wooden_block_a, base=wooden_block_b)`（补救） → 7. `search(object=floor_block, region=dining_room_0_1)`（补救） → 8. `navigate(destination=floor_block)`（补救） → 9. `pick(object=floor_block)`（补救） → 10. `navigate(destination=wooden_block_b)`（补救） → 11. `approach(target=wooden_block_b)`（补救） → 12. `stack(object=floor_block, base=wooden_block_a)`（补救）

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

1. `look(target=kitchen_island/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=breakfast_spoon)` → 4. `pick(object=breakfast_spoon)` → 5. `navigate(destination=wide_storage_bin)` → 6. `approach(target=wide_storage_bin)` → 7. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 8. `navigate(destination=rolling_pin)` → 9. `pick(object=rolling_pin)` → 10. `navigate(destination=wide_storage_bin)` → 11. `approach(target=wide_storage_bin)` → 12. `place(object=rolling_pin, receptacle=wide_storage_bin)`

### far_small_and_large（Task）

**情况**：同上，但机器人背对出发，要先找勺子

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

1. `search(object=breakfast_spoon, region=living_room_0_0)` → 2. `look(target=kitchen_island/top)` → 3. `navigate(destination=breakfast_spoon)` → 4. `pick(object=breakfast_spoon)` → 5. `navigate(destination=wide_storage_bin)` → 6. `approach(target=wide_storage_bin)` → 7. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 8. `navigate(destination=rolling_pin)` → 9. `pick(object=rolling_pin)` → 10. `navigate(destination=mug)` → 11. `place(object=rolling_pin, receptacle=mug)` → 12. `look(target=rolling_pin)`（补救） → 13. `lift(object=rolling_pin, height_m=1.04)` → 14. `retreat(obstacle=kitchen_island, distance_m=0.3)` → 15. `navigate(destination=wide_storage_bin)`（换做法） → 16. `approach(target=wide_storage_bin)` → 17. `place(object=rolling_pin, receptacle=wide_storage_bin)`（换做法）

### h_dynamic_pin_taken（Task）

**情况**：同上按尺寸选宽箱；勺子放进去后有人把擀面杖拿走 → 勺子不动，找回擀面杖放进去

**指令**：烘焙结束，请把擀面杖和勺子一起收进同一个合适容器，确保两件都完整放入。

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `rolling_pin` 完全在 `wide_storage_bin` 里（没有露出边沿）
    - `breakfast_spoon` 完全在 `wide_storage_bin` 里（没有露出边沿）
  - 第 2 组：
    - `rolling_pin` 完全在 `mug` 里（没有露出边沿）
    - `breakfast_spoon` 完全在 `mug` 里（没有露出边沿）
  - 第 3 组：
    - `rolling_pin` 完全在 `small_storage_bin` 里（没有露出边沿）
    - `breakfast_spoon` 完全在 `small_storage_bin` 里（没有露出边沿）

**参考调用顺序**：

- 摆法 `h_dynamic_pin_taken`：1. `look(target=kitchen_island/top)` → 2. `look(target=tv_stand_2/top)` → 3. `measure(object=mug)` → 4. `measure(object=small_storage_bin)` → 5. `measure(object=rolling_pin)` → 6. `navigate(destination=breakfast_spoon)` → 7. `pick(object=breakfast_spoon)` → 8. `navigate(destination=wide_storage_bin)` → 9. `approach(target=wide_storage_bin)` → 10. `drop(object=breakfast_spoon, container=wide_storage_bin)`（换做法） → 11. `search(object=rolling_pin, region=living_room_0_0)`（补救） → 12. `navigate(destination=rolling_pin)` → 13. `pick(object=rolling_pin)` → 14. `navigate(destination=wide_storage_bin)` → 15. `approach(target=wide_storage_bin)` → 16. `place(object=rolling_pin, receptacle=wide_storage_bin)`（换做法）
- 摆法 `alt_dining_table_2`：1. `look(target=kitchen_island/top)` → 2. `look(target=tv_stand_2/top)` → 3. `measure(object=mug)` → 4. `measure(object=small_storage_bin)` → 5. `measure(object=rolling_pin)` → 6. `navigate(destination=breakfast_spoon)` → 7. `pick(object=breakfast_spoon)` → 8. `navigate(destination=wide_storage_bin)` → 9. `approach(target=wide_storage_bin)` → 10. `drop(object=breakfast_spoon, container=wide_storage_bin)`（换做法） → 11. `search(object=rolling_pin, region=dining_room_0_1)`（补救） → 12. `navigate(destination=rolling_pin)` → 13. `pick(object=rolling_pin)` → 14. `navigate(destination=wide_storage_bin)` → 15. `approach(target=wide_storage_bin)` → 16. `place(object=rolling_pin, receptacle=wide_storage_bin)`（换做法）

### mug_or_bedroom_bin（Task）

**情况**：岛台上有个马克杯（口 8 cm），宽储物箱在卧室矮书架上 → 判断擀面杖放不进杯子，去卧室找到储物箱，把两样都拿过去

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

1. `look(target=kitchen_island/top)` → 2. `search(object=wide_storage_bin, region=bedroom_0_1)` → 3. `navigate(destination=bookcase_2/top)` → 4. `look(target=bookcase_2/top)` → 5. `navigate(destination=breakfast_spoon)` → 6. `pick(object=breakfast_spoon)` → 7. `navigate(destination=wide_storage_bin)` → 8. `approach(target=wide_storage_bin)` → 9. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 10. `navigate(destination=rolling_pin)` → 11. `pick(object=rolling_pin)` → 12. `navigate(destination=wide_storage_bin)` → 13. `approach(target=wide_storage_bin)` → 14. `place(object=rolling_pin, receptacle=wide_storage_bin)`

### three_containers_bedroom（Task）

**情况**：马克杯在岛台；小储物箱和宽储物箱并排放在卧室矮书架上 → 去卧室量尺寸，22 cm 的擀面杖只能放宽箱，把两样都拿过去

**指令**：烘焙结束，请把擀面杖和勺子一起收进同一个合适容器，确保两件都完整放入。

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `rolling_pin` 完全在 `wide_storage_bin` 里（没有露出边沿）
    - `breakfast_spoon` 完全在 `wide_storage_bin` 里（没有露出边沿）
  - 第 2 组：
    - `rolling_pin` 完全在 `mug` 里（没有露出边沿）
    - `breakfast_spoon` 完全在 `mug` 里（没有露出边沿）
  - 第 3 组：
    - `rolling_pin` 完全在 `small_storage_bin` 里（没有露出边沿）
    - `breakfast_spoon` 完全在 `small_storage_bin` 里（没有露出边沿）

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `search(object=wide_storage_bin, region=bedroom_0_1)` → 3. `navigate(destination=bookcase_2/top)` → 4. `look(target=bookcase_2/top)` → 5. `measure(object=mug)` → 6. `measure(object=small_storage_bin)` → 7. `measure(object=rolling_pin)` → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=wide_storage_bin)` → 11. `approach(target=wide_storage_bin)` → 12. `drop(object=breakfast_spoon, container=wide_storage_bin)` → 13. `navigate(destination=rolling_pin)` → 14. `pick(object=rolling_pin)` → 15. `navigate(destination=wide_storage_bin)` → 16. `approach(target=wide_storage_bin)` → 17. `place(object=rolling_pin, receptacle=wide_storage_bin)`

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

### x6_gd_cup_in_cabinets（Task）

**情况**：马克杯就在眼前，但更想要杯子；杯子收在两个关着的矮柜之一 → 逐个打开找，找完关门

**指令**：A guest is coming. Set out a cup at the drinks spot on the low wall cabinet; the cups are kept in the two low kitchen cabinets. If there is no cup, the mug on the island will do. Close the cabinets again.

**成功条件**：

- `cup_counter_b` 在 `kitchen_cabinet_6/top` 上
- `cup_counter_b` 立着
- 手里空着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

- 摆法 `cup_in_4`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=kitchen_cabinet_6)` → 3. `open(articulated=kitchen_cabinet_6)` → 4. `bend()` → 5. `explore_furniture(furniture=kitchen_cabinet_6)` → 6. `straighten()` → 7. `close(articulated=kitchen_cabinet_6)` → 8. `navigate(destination=kitchen_cabinet_4)` → 9. `open(articulated=kitchen_cabinet_4)` → 10. `bend()` → 11. `explore_furniture(furniture=kitchen_cabinet_4)` → 12. `straighten()` → 13. `navigate(destination=cup_counter_b)` → 14. `pick(object=cup_counter_b)` → 15. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 16. `close(articulated=kitchen_cabinet_4)` → 17. `navigate(destination=kitchen_cabinet_6/top)` → 18. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)`
- 摆法 `cup_in_6`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=kitchen_cabinet_4)` → 3. `open(articulated=kitchen_cabinet_4)` → 4. `bend()` → 5. `explore_furniture(furniture=kitchen_cabinet_4)` → 6. `straighten()` → 7. `close(articulated=kitchen_cabinet_4)` → 8. `navigate(destination=kitchen_cabinet_6)` → 9. `open(articulated=kitchen_cabinet_6)` → 10. `bend()` → 11. `explore_furniture(furniture=kitchen_cabinet_6)` → 12. `straighten()` → 13. `navigate(destination=cup_counter_b)` → 14. `pick(object=cup_counter_b)` → 15. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 16. `close(articulated=kitchen_cabinet_6)` → 17. `navigate(destination=kitchen_cabinet_6/top)` → 18. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)`

### x6_dr_spot_filled_dynamic__bowl（Task）

**情况**：拿起杯子后有人在饮品角放了锅盖和燕麦碗 → 先暂放杯子，挪走碗，再放杯子

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

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=cup_counter_b)` → 3. `pick(object=cup_counter_b)` → 4. `navigate(destination=kitchen_cabinet_6/top)` → 5. `look(target=kitchen_cabinet_6/top)`（补救） → 6. `navigate(destination=kitchen_cabinet_4/top)`（补救） → 7. `place(object=cup_counter_b, receptacle=kitchen_cabinet_4/top, hint_xy=[1.2, 0.42])`（补救） → 8. `navigate(destination=oatmeal)`（补救） → 9. `pick(object=oatmeal)`（补救） → 10. `navigate(destination=kitchen_cabinet_4/top)`（补救） → 11. `place(object=oatmeal, receptacle=kitchen_cabinet_4/top, hint_xy=[1.55, 0.42])`（补救） → 12. `navigate(destination=cup_counter_b)`（补救） → 13. `pick(object=cup_counter_b)`（补救） → 14. `navigate(destination=kitchen_cabinet_6/top)`（补救） → 15. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)`（补救）

### x6_dr_spot_filled_dynamic__block（Task）

**情况**：同上，放的是积木 → 挪走积木再放杯子

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

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=cup_counter_b)` → 3. `pick(object=cup_counter_b)` → 4. `navigate(destination=kitchen_cabinet_6/top)` → 5. `look(target=kitchen_cabinet_6/top)`（补救） → 6. `navigate(destination=kitchen_cabinet_4/top)`（补救） → 7. `place(object=cup_counter_b, receptacle=kitchen_cabinet_4/top, hint_xy=[1.2, 0.42])`（补救） → 8. `navigate(destination=wooden_block_a)`（补救） → 9. `pick(object=wooden_block_a)`（补救） → 10. `navigate(destination=kitchen_cabinet_4/top)`（补救） → 11. `place(object=wooden_block_a, receptacle=kitchen_cabinet_4/top, hint_xy=[1.55, 0.42])`（补救） → 12. `navigate(destination=cup_counter_b)`（补救） → 13. `pick(object=cup_counter_b)`（补救） → 14. `navigate(destination=kitchen_cabinet_6/top)`（补救） → 15. `place(object=cup_counter_b, receptacle=kitchen_cabinet_6/top)`（补救）

### cup_taken_mug_in_living_room（Task）

**情况**：机器人看过之后有人把杯子拿走了，马克杯在客厅电视柜上，一开始看不到 → 去客厅找到马克杯拿过来

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

1. `look(target=kitchen_island/top)` → 2. `search(object=mug, region=living_room_0_0)` → 3. `navigate(destination=mug)` → 4. `pick(object=mug)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=mug, receptacle=kitchen_cabinet_6/top)`

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

### h_dynamic_pencil_taken（Action + Task）

**情况**：同上，开门后有人把铅笔拿走 → 关好柜门，再去找铅笔

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

- 摆法 `h_dynamic_pencil_taken`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `look(target=kitchen_cabinet_6/inside_shelf)` → 4. `navigate(destination=dining_table_2/top)`（补救） → 5. `look(target=dining_table_2/top)`（补救） → 6. `navigate(destination=kitchen_cabinet_6)`（补救） → 7. `close(articulated=kitchen_cabinet_6)`（补救） → 8. `navigate(destination=pencil)`（补救） → 9. `pick(object=pencil)`（补救） → 10. `navigate(destination=desk_1/top)`（补救） → 11. `place(object=pencil, receptacle=desk_1/top)`（补救）
- 摆法 `alt_tv_stand_2`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `look(target=kitchen_cabinet_6/inside_shelf)` → 4. `navigate(destination=tv_stand_2/top)`（补救） → 5. `look(target=tv_stand_2/top)`（补救） → 6. `navigate(destination=kitchen_cabinet_6)`（补救） → 7. `close(articulated=kitchen_cabinet_6)`（补救） → 8. `navigate(destination=pencil)`（补救） → 9. `pick(object=pencil)`（补救） → 10. `navigate(destination=desk_1/top)`（补救） → 11. `place(object=pencil, receptacle=desk_1/top)`（补救）

### x6_gd_pencil_other_cabinet（Task）

**情况**：指令说铅笔在靠墙矮柜里，其实在另一个矮柜 → 第一个找不到就去开第二个

**指令**：The kid needs something to write with for homework. Bring a pen to the study desk; if there is no pen, a pencil. The pencils are kept in the low wall cabinet; close it again afterwards.

**成功条件**：

- 手里空着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_4` 关着
- 满足下面任意一组：
  - 第 1 组：
    - `pen` 在 `desk_1/top` 上
  - 第 2 组：
    - `pencil` 在 `desk_1/top` 上

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=pencil)` → 13. `pick(object=pencil)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `close(articulated=kitchen_cabinet_4)` → 16. `navigate(destination=desk_1/top)` → 17. `place(object=pencil, receptacle=desk_1/top)`

### x6_gd_pen_or_pencil_cabinets（Task）

**情况**：两个矮柜里一个放钢笔、一个放铅笔 → 都打开看，优先拿钢笔，关好柜门

**指令**：The kid needs something to write with for homework. Bring a pen to the study desk; if there is no pen, a pencil. Pens and pencils are kept in the two low kitchen cabinets; close them again afterwards.

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

**情况**：矮柜顶被锅盖和燕麦碗占着，中间的缝太窄 → 改放电视柜

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

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=kitchen_cabinet_6/top)` → 5. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top)` → 6. `navigate(destination=tv_stand_2/top)`（换做法） → 7. `place(object=wooden_block_a, receptacle=tv_stand_2/top)`（换做法）

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

- 摆法 `occupied_block_away`：1. `look(target=kitchen_island/top)` → 2. `search(object=wooden_block_a, region=dining_room_0_1)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top)` → 7. `navigate(destination=tv_stand_2/top)`（换做法） → 8. `place(object=wooden_block_a, receptacle=tv_stand_2/top)`（换做法）
- 摆法 `alt_tv_stand_2`：1. `look(target=kitchen_island/top)` → 2. `search(object=wooden_block_a, region=living_room_0_0)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=kitchen_cabinet_6/top)` → 6. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top)` → 7. `navigate(destination=tv_stand_2/top)`（换做法） → 8. `place(object=wooden_block_a, receptacle=tv_stand_2/top)`（换做法）

### display_hidden（Task）

**情况**：矮柜前排立着麦片盒和果汁瓶，后面的空位从房间里看不到 → 不符合"看得清楚"，改放电视柜

**指令**：请把积木展示在靠墙矮柜或电视柜上一个醒目、稳定的位置。

**成功条件**：

- `clutter_cereal_a`、`clutter_cereal_b`、`juice_bottle`、`clutter_cereal_c` 立着
- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
    - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
    - `wooden_block_a` 离台面边缘至少 2 cm
  - 第 2 组：
    - `wooden_block_a` 在 `tv_stand_2/top` 上
    - `wooden_block_a` 从房间里看得见（前面没有更高的东西挡着）
    - `wooden_block_a` 离台面边缘至少 2 cm
  - 第 3 组：
    - `wooden_block_b` 在 `kitchen_cabinet_6/top` 上
    - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
    - `wooden_block_b` 离台面边缘至少 2 cm
  - 第 4 组：
    - `wooden_block_b` 在 `tv_stand_2/top` 上
    - `wooden_block_b` 从房间里看得见（前面没有更高的东西挡着）
    - `wooden_block_b` 离台面边缘至少 2 cm

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=wooden_block_a)` → 4. `pick(object=wooden_block_a)` → 5. `navigate(destination=tv_stand_2/top)`（换做法） → 6. `place(object=wooden_block_a, receptacle=tv_stand_2/top)`（换做法）

### h_dynamic_cabinet_filled（Task）

**情况**：拿起积木后有人把锅盖和燕麦碗放到柜顶 → 改放电视柜

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

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=kitchen_cabinet_6/top)` → 5. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top)` → 6. `navigate(destination=tv_stand_2/top)`（换做法） → 7. `place(object=wooden_block_a, receptacle=tv_stand_2/top)`（换做法）

### x6_gd_two_displays_event（Task）

**情况**：两块积木分别放矮柜和电视柜；第一块放好后孩子把另一块拿走 → 找回来放到电视柜

**指令**：Put both toy blocks on display: one on the low wall cabinet and one on the TV stand, so they can be seen from both rooms.

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `wooden_block_a` 在 `kitchen_cabinet_6/top` 上
    - `wooden_block_b` 在 `tv_stand_2/top` 上
  - 第 2 组：
    - `wooden_block_b` 在 `kitchen_cabinet_6/top` 上
    - `wooden_block_a` 在 `tv_stand_2/top` 上

**参考调用顺序**：

- 摆法 `dining`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=kitchen_cabinet_6/top)` → 5. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top)` → 6. `search(object=wooden_block_b, region=dining_room_0_1)`（补救） → 7. `navigate(destination=wooden_block_b)`（补救） → 8. `pick(object=wooden_block_b)`（补救） → 9. `navigate(destination=tv_stand_2/top)`（补救） → 10. `place(object=wooden_block_b, receptacle=tv_stand_2/top)`（补救）
- 摆法 `cabinet4`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `navigate(destination=kitchen_cabinet_6/top)` → 5. `place(object=wooden_block_a, receptacle=kitchen_cabinet_6/top)` → 6. `search(object=wooden_block_b)`（补救） → 7. `navigate(destination=wooden_block_b)`（补救） → 8. `pick(object=wooden_block_b)`（补救） → 9. `navigate(destination=tv_stand_2/top)`（补救） → 10. `place(object=wooden_block_b, receptacle=tv_stand_2/top)`（补救）

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

**情况**：微波炉转但不热 → 改用灶台

**成功条件**：

- `oatmeal` 温度至少 40 °C
- `kitchen_stove` 已经停止加热
- `kitchen_microwave` 关着
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=oatmeal)` → 3. `pick(object=oatmeal)` → 4. `navigate(destination=kitchen_stove/top)` → 5. `place(object=oatmeal, receptacle=kitchen_stove/top)` → 6. `heat(food=oatmeal, appliance=kitchen_stove, temp_c=40)`

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

### h_dynamic_door_opened（Action + Task）

**情况**：微波炉被锅占着，要用灶台；关上微波炉后有人又打开了门 → 最后再关一次

**指令**：请用合适方式把燕麦粥加热到至少 40°C，完成后关火并关好微波炉门。

**成功条件**：

- `oatmeal` 温度至少 40 °C
- `kitchen_stove` 已经停止加热
- `kitchen_microwave` 关着
- `handled_cooking_pot` 不在地上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_microwave/inside_floor)` → 4. `close(articulated=kitchen_microwave)` → 5. `look(target=kitchen_island/top)` → 6. `navigate(destination=oatmeal)` → 7. `pick(object=oatmeal)` → 8. `navigate(destination=kitchen_stove/top)`（换做法） → 9. `place(object=oatmeal, receptacle=kitchen_stove/top)`（换做法） → 10. `heat(food=oatmeal, appliance=kitchen_stove, temp_c=40)`（换做法） → 11. `navigate(destination=kitchen_microwave)`（补救） → 12. `close(articulated=kitchen_microwave)`（补救）

### x6_sr_microwave_taken（Task）

**情况**：机器人去拿碗时，有人把汤锅放进了开着的微波炉 → 关上门，改用灶台

**成功条件**：

- `oatmeal` 温度至少 40 °C
- `kitchen_stove` 已经停止加热
- `kitchen_microwave` 关着
- `handled_cooking_pot` 不在地上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_island/top)` → 4. `navigate(destination=oatmeal)` → 5. `pick(object=oatmeal)` → 6. `navigate(destination=kitchen_microwave/inside_floor)` → 7. `look(target=kitchen_microwave/inside_floor)`（补救） → 8. `close(articulated=kitchen_microwave)`（补救） → 9. `navigate(destination=kitchen_stove/top)`（补救） → 10. `place(object=oatmeal, receptacle=kitchen_stove/top)`（补救） → 11. `heat(food=oatmeal, appliance=kitchen_stove, temp_c=40)`（补救）

### x6_pp_door_opened_after_heat（Action）

**情况**：粥刚热好，有人打开微波炉门看 → 粥不用重热，只要再把门关上

**成功条件**：

- `oatmeal` 温度至少 40 °C
- `kitchen_stove` 已经停止加热
- `kitchen_microwave` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_island/top)` → 4. `navigate(destination=oatmeal)` → 5. `pick(object=oatmeal)` → 6. `navigate(destination=kitchen_microwave/inside_floor)` → 7. `place(object=oatmeal, receptacle=kitchen_microwave/inside_floor)` → 8. `close(articulated=kitchen_microwave)` → 9. `heat(food=oatmeal, appliance=kitchen_microwave, temp_c=40)` → 10. `close(articulated=kitchen_microwave)`（补救）

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

### sponge_on_tv_stand（Task）

**情况**：海绵在岛台后面的电视柜上 → 去那里拿

**成功条件**：

- `kitchen_island/top` 擦过
- `kitchen_sponge` 在 `kitchen_island/top` 上
- 手里空着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=kitchen_sponge)` → 4. `pick(object=kitchen_sponge)` → 5. `approach(target=kitchen_island/top)` → 6. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 7. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`

### far_sponge_tv（Task）

**情况**：从餐厅出发，海绵不在岛台 → 先找海绵

**成功条件**：

- `kitchen_island/top` 擦过
- `kitchen_sponge` 在 `kitchen_island/top` 上
- 手里空着

**参考调用顺序**：

- 摆法 `far_sponge_tv`：1. `search(object=kitchen_sponge, region=living_room_0_0)` → 2. `navigate(destination=kitchen_sponge)` → 3. `pick(object=kitchen_sponge)` → 4. `approach(target=kitchen_island/top)` → 5. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 6. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`
- 摆法 `alt_dining_table_2`：1. `search(object=kitchen_sponge, region=dining_room_0_1)` → 2. `navigate(destination=kitchen_sponge)` → 3. `pick(object=kitchen_sponge)` → 4. `approach(target=kitchen_island/top)` → 5. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 6. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`

### island_cluttered（Action）

**情况**：岛台前后两排摆满杂物 → 把要擦那一条上的东西挪开，擦完放回

**指令**：用海绵擦净厨房岛台，妥善处理并恢复台面物品，最后把海绵放回原处。

**成功条件**：

- `kitchen_island/top` 擦过
- `kitchen_sponge` 在 `tv_stand_2/top` 上
- 手里空着
- `rolling_pin`、`wooden_block_a`、`soda_can`、`wooden_block_b`、`mug`、`oatmeal`、`paperback_book`、`breakfast_spoon`、`juice_bottle` 没被挪动（离开局位置不超过 12 cm）
- `soda_can`、`mug`、`juice_bottle`、`oatmeal` 立着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_b)` → 3. `pick(object=wooden_block_b)` → 4. `navigate(destination=tv_stand_2/top)` → 5. `place(object=wooden_block_b, receptacle=tv_stand_2/top, hint_xy=[7.14, 0.44])` → 6. `look(target=tv_stand_2/top)` → 7. `navigate(destination=kitchen_sponge)` → 8. `pick(object=kitchen_sponge)` → 9. `approach(target=kitchen_island/top)` → 10. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 11. `navigate(destination=tv_stand_2/top)` → 12. `place(object=kitchen_sponge, receptacle=tv_stand_2/top)` → 13. `navigate(destination=wooden_block_b)` → 14. `pick(object=wooden_block_b)` → 15. `navigate(destination=kitchen_island/top)` → 16. `place(object=wooden_block_b, receptacle=kitchen_island/top, hint_xy=[7.8, 1.62])`

### h_dynamic_sponge_taken（Action + Task）

**情况**：岛台杂乱要先挪开；有人把海绵拿走 → 找海绵

**指令**：用海绵擦净厨房岛台，妥善处理并恢复台面物品，最后把海绵放回原处。

**成功条件**：

- `kitchen_island/top` 擦过
- `kitchen_sponge` 在 `tv_stand_2/top` 上
- 手里空着
- `rolling_pin`、`wooden_block_a`、`soda_can`、`wooden_block_b`、`mug`、`oatmeal`、`paperback_book`、`breakfast_spoon`、`juice_bottle` 没被挪动（离开局位置不超过 12 cm）
- `soda_can`、`mug`、`juice_bottle`、`oatmeal` 立着

**参考调用顺序**：

- 摆法 `h_dynamic_sponge_taken`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_b)` → 3. `pick(object=wooden_block_b)` → 4. `navigate(destination=tv_stand_2/top)` → 5. `place(object=wooden_block_b, receptacle=tv_stand_2/top, hint_xy=[7.14, 0.44])` → 6. `look(target=tv_stand_2/top)` → 7. `search(object=kitchen_sponge, region=living_room_0_0)`（补救） → 8. `navigate(destination=kitchen_sponge)` → 9. `pick(object=kitchen_sponge)` → 10. `navigate(destination=kitchen_island/top)`（补救） → 11. `approach(target=kitchen_island/top)` → 12. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 13. `navigate(destination=tv_stand_2/top)` → 14. `place(object=kitchen_sponge, receptacle=tv_stand_2/top)` → 15. `navigate(destination=wooden_block_b)` → 16. `pick(object=wooden_block_b)` → 17. `navigate(destination=kitchen_island/top)` → 18. `place(object=wooden_block_b, receptacle=kitchen_island/top, hint_xy=[7.8, 1.62])`
- 摆法 `alt_dining_table_2`：1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_b)` → 3. `pick(object=wooden_block_b)` → 4. `navigate(destination=tv_stand_2/top)` → 5. `place(object=wooden_block_b, receptacle=tv_stand_2/top, hint_xy=[7.14, 0.44])` → 6. `look(target=tv_stand_2/top)` → 7. `search(object=kitchen_sponge, region=dining_room_0_1)`（补救） → 8. `navigate(destination=kitchen_sponge)` → 9. `pick(object=kitchen_sponge)` → 10. `navigate(destination=kitchen_island/top)`（补救） → 11. `approach(target=kitchen_island/top)` → 12. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 13. `navigate(destination=tv_stand_2/top)` → 14. `place(object=kitchen_sponge, receptacle=tv_stand_2/top)` → 15. `navigate(destination=wooden_block_b)` → 16. `pick(object=wooden_block_b)` → 17. `navigate(destination=kitchen_island/top)` → 18. `place(object=wooden_block_b, receptacle=kitchen_island/top, hint_xy=[7.8, 1.62])`

### x6_pp_sponge_taken_after_wipe（Task）

**情况**：擦完放回海绵后有人把它拿走 → 不用重擦，找回海绵放回岛台

**成功条件**：

- `kitchen_island/top` 擦过
- `kitchen_sponge` 在 `kitchen_island/top` 上
- 手里空着

**参考调用顺序**：

- 摆法 `tv_stand`：1. `look(target=kitchen_island/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=kitchen_sponge)` → 4. `pick(object=kitchen_sponge)` → 5. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 6. `place(object=kitchen_sponge, receptacle=kitchen_island/top)` → 7. `look(target=kitchen_island/top)`（补救） → 8. `search(object=kitchen_sponge)`（补救） → 9. `look(target=tv_stand_2/top)`（补救） → 10. `navigate(destination=kitchen_sponge)`（补救） → 11. `pick(object=kitchen_sponge)`（补救） → 12. `navigate(destination=kitchen_island/top)`（补救） → 13. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`（补救）
- 摆法 `cabinet6`：1. `look(target=kitchen_island/top)` → 2. `look(target=tv_stand_2/top)` → 3. `navigate(destination=kitchen_sponge)` → 4. `pick(object=kitchen_sponge)` → 5. `wipe(surface=kitchen_island/top, tool=kitchen_sponge)` → 6. `place(object=kitchen_sponge, receptacle=kitchen_island/top)` → 7. `look(target=kitchen_island/top)`（补救） → 8. `search(object=kitchen_sponge)`（补救） → 9. `look(target=kitchen_cabinet_6/top)`（补救） → 10. `navigate(destination=kitchen_sponge)`（补救） → 11. `pick(object=kitchen_sponge)`（补救） → 12. `navigate(destination=kitchen_island/top)`（补救） → 13. `place(object=kitchen_sponge, receptacle=kitchen_island/top)`（补救）

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

### lid_on（Action）

**情况**：锅盖盖着 → 先揭盖再放番茄

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

1. `look(target=kitchen_island/top)` → 2. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 3. `navigate(destination=handled_cooking_pot)` → 4. `uncover(container=handled_cooking_pot)` → 5. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 6. `navigate(destination=breakfast_spoon)` → 7. `pick(object=breakfast_spoon)` → 8. `navigate(destination=handled_cooking_pot)` → 9. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 10. `navigate(destination=kitchen_island/top)` → 11. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 12. `navigate(destination=pot_lid)` → 13. `pick(object=pot_lid)` → 14. `navigate(destination=handled_cooking_pot)` → 15. `cover(container=handled_cooking_pot, lid=pot_lid)` → 16. `navigate(destination=kitchen_stove)` → 17. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

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

### h_dynamic_spoon_taken（Task）

**情况**：放番茄时有人把勺子拿走 → 找勺子

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

- 摆法 `h_dynamic_spoon_taken`：1. `look(target=kitchen_island/top)` → 2. `look(target=kitchen_stove/top)` → 3. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)`（换做法） → 4. `search(object=breakfast_spoon, region=living_room_0_0)`（补救） → 5. `navigate(destination=breakfast_spoon)` → 6. `pick(object=breakfast_spoon)` → 7. `navigate(destination=handled_cooking_pot)` → 8. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 9. `navigate(destination=kitchen_island/top)` → 10. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 11. `navigate(destination=pot_lid)` → 12. `pick(object=pot_lid)` → 13. `navigate(destination=handled_cooking_pot)` → 14. `cover(container=handled_cooking_pot, lid=pot_lid)` → 15. `navigate(destination=kitchen_stove)` → 16. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`
- 摆法 `alt_dining_table_2`：1. `look(target=kitchen_island/top)` → 2. `look(target=kitchen_stove/top)` → 3. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)`（换做法） → 4. `search(object=breakfast_spoon, region=dining_room_0_1)`（补救） → 5. `navigate(destination=breakfast_spoon)` → 6. `pick(object=breakfast_spoon)` → 7. `navigate(destination=handled_cooking_pot)` → 8. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 9. `navigate(destination=kitchen_island/top)` → 10. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 11. `navigate(destination=pot_lid)` → 12. `pick(object=pot_lid)` → 13. `navigate(destination=handled_cooking_pot)` → 14. `cover(container=handled_cooking_pot, lid=pot_lid)` → 15. `navigate(destination=kitchen_stove)` → 16. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

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

### x6_pp_lid_taken_after_stir（Task）

**情况**：搅完后有人把锅盖拿走 → 找回锅盖盖上，前面的步骤不用重做

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

- 摆法 `cabinet4`：1. `look(target=kitchen_island/top)` → 2. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 3. `navigate(destination=breakfast_spoon)` → 4. `pick(object=breakfast_spoon)` → 5. `navigate(destination=handled_cooking_pot)` → 6. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 7. `navigate(destination=kitchen_island/top)` → 8. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 9. `look(target=kitchen_stove/top)`（补救） → 10. `search(object=pot_lid)`（补救） → 11. `navigate(destination=pot_lid)` → 12. `pick(object=pot_lid)` → 13. `navigate(destination=handled_cooking_pot)` → 14. `cover(container=handled_cooking_pot, lid=pot_lid)` → 15. `navigate(destination=kitchen_stove)` → 16. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`
- 摆法 `dining`：1. `look(target=kitchen_island/top)` → 2. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 3. `navigate(destination=breakfast_spoon)` → 4. `pick(object=breakfast_spoon)` → 5. `navigate(destination=handled_cooking_pot)` → 6. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 7. `navigate(destination=kitchen_island/top)` → 8. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 9. `look(target=kitchen_stove/top)`（补救） → 10. `search(object=pot_lid, region=dining_room_0_1)`（补救） → 11. `navigate(destination=pot_lid)` → 12. `pick(object=pot_lid)` → 13. `navigate(destination=handled_cooking_pot)` → 14. `cover(container=handled_cooking_pot, lid=pot_lid)` → 15. `navigate(destination=kitchen_stove)` → 16. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

### x6_pp_tomato_taken_out__tomato2（Action）

**情况**：番茄放进锅后孩子拿出 2 号放回岛台 → 只把这一颗放回去

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

1. `look(target=kitchen_island/top)` → 2. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 3. `look(target=kitchen_island/top)`（补救） → 4. `navigate(destination=cherry_tomato_2)`（补救） → 5. `pick(object=cherry_tomato_2)`（补救） → 6. `navigate(destination=handled_cooking_pot)`（补救） → 7. `drop(object=cherry_tomato_2, container=handled_cooking_pot)`（补救） → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=handled_cooking_pot)` → 11. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 12. `navigate(destination=kitchen_island/top)` → 13. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 14. `navigate(destination=pot_lid)` → 15. `pick(object=pot_lid)` → 16. `navigate(destination=handled_cooking_pot)` → 17. `cover(container=handled_cooking_pot, lid=pot_lid)` → 18. `navigate(destination=kitchen_stove)` → 19. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

### x6_pp_tomato_taken_out__tomato1（Action）

**情况**：同上，拿出的是 1 号

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

1. `look(target=kitchen_island/top)` → 2. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 3. `look(target=kitchen_island/top)`（补救） → 4. `navigate(destination=cherry_tomato_1)`（补救） → 5. `pick(object=cherry_tomato_1)`（补救） → 6. `navigate(destination=handled_cooking_pot)`（补救） → 7. `drop(object=cherry_tomato_1, container=handled_cooking_pot)`（补救） → 8. `navigate(destination=breakfast_spoon)` → 9. `pick(object=breakfast_spoon)` → 10. `navigate(destination=handled_cooking_pot)` → 11. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 12. `navigate(destination=kitchen_island/top)` → 13. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 14. `navigate(destination=pot_lid)` → 15. `pick(object=pot_lid)` → 16. `navigate(destination=handled_cooking_pot)` → 17. `cover(container=handled_cooking_pot, lid=pot_lid)` → 18. `navigate(destination=kitchen_stove)` → 19. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

### x6_pp_tomato_taken_out__tomato2_after_stir（Action）

**情况**：搅完之后孩子才拿出 2 号 → 放回去，接着做

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

1. `look(target=kitchen_island/top)` → 2. `collect(objects=[cherry_tomato_1, cherry_tomato_2], container=handled_cooking_pot)` → 3. `navigate(destination=breakfast_spoon)` → 4. `pick(object=breakfast_spoon)` → 5. `navigate(destination=handled_cooking_pot)` → 6. `stir(container=handled_cooking_pot, tool=breakfast_spoon)` → 7. `navigate(destination=kitchen_island/top)` → 8. `place(object=breakfast_spoon, receptacle=kitchen_island/top)` → 9. `look(target=kitchen_island/top)`（补救） → 10. `navigate(destination=cherry_tomato_2)`（补救） → 11. `pick(object=cherry_tomato_2)`（补救） → 12. `navigate(destination=handled_cooking_pot)`（补救） → 13. `drop(object=cherry_tomato_2, container=handled_cooking_pot)`（补救） → 14. `navigate(destination=pot_lid)` → 15. `pick(object=pot_lid)` → 16. `navigate(destination=handled_cooking_pot)` → 17. `cover(container=handled_cooking_pot, lid=pot_lid)` → 18. `navigate(destination=kitchen_stove)` → 19. `heat(food=cherry_tomato_1, appliance=kitchen_stove, temp_c=60)`

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

### far_can_far（Task）

**情况**：从餐厅出发，罐子在别的房间 → 先找

**成功条件**：

- `soda_can` 在 `trash_can` 里
- 手里空着

**参考调用顺序**：

- 摆法 `far_can_far`：1. `pick(object=soda_can)` → 2. `search(object=soda_can, region=living_room_0_0)` → 3. `explore_room(room=living_room_0_0)` → 4. `navigate(destination=soda_can)` → 5. `pick(object=soda_can)` → 6. `navigate(destination=trash_can)` → 7. `drop(object=soda_can, container=trash_can)`
- 摆法 `alt_dining_table_2`：1. `pick(object=soda_can)` → 2. `search(object=soda_can, region=dining_room_0_1)` → 3. `explore_room(room=living_room_0_0)` → 4. `navigate(destination=soda_can)` → 5. `pick(object=soda_can)` → 6. `navigate(destination=trash_can)` → 7. `drop(object=soda_can, container=trash_can)`

### h_task_can_in_microwave（Action）

**情况**：罐子在关着的微波炉里 → 开门拿出、关门，再扔

**指令**：有人把空汽水罐落在微波炉里了。请把它扔进垃圾桶，并把微波炉门关好。

**成功条件**：

- `soda_can` 在 `trash_can` 里
- 手里空着
- `kitchen_microwave` 关着

**参考调用顺序**：

1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_microwave/inside_floor)` → 4. `navigate(destination=soda_can)` → 5. `pick(object=soda_can)` → 6. `retreat(obstacle=kitchen_microwave, distance_m=0.3)` → 7. `close(articulated=kitchen_microwave)` → 8. `navigate(destination=trash_can)` → 9. `drop(object=soda_can, container=trash_can)`

### h_dynamic_can_moved（Action + Task）

**情况**：同上，开门后有人把罐子拿走 → 关好门，去找罐子

**指令**：有人把空汽水罐落在微波炉里了。请把它扔进垃圾桶，并把微波炉门关好。

**成功条件**：

- `soda_can` 在 `trash_can` 里
- 手里空着
- `kitchen_microwave` 关着

**参考调用顺序**：

- 摆法 `h_dynamic_can_moved`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_microwave/inside_floor)` → 4. `search(object=soda_can, region=dining_room_0_1)`（补救） → 5. `navigate(destination=kitchen_microwave)`（补救） → 6. `close(articulated=kitchen_microwave)`（补救） → 7. `navigate(destination=soda_can)`（补救） → 8. `pick(object=soda_can)`（补救） → 9. `navigate(destination=trash_can)`（补救） → 10. `drop(object=soda_can, container=trash_can)`（补救）
- 摆法 `alt_tv_stand_2`：1. `navigate(destination=kitchen_microwave)` → 2. `open(articulated=kitchen_microwave)` → 3. `look(target=kitchen_microwave/inside_floor)` → 4. `search(object=soda_can, region=living_room_0_0)`（补救） → 5. `navigate(destination=kitchen_microwave)`（补救） → 6. `close(articulated=kitchen_microwave)`（补救） → 7. `navigate(destination=soda_can)`（补救） → 8. `pick(object=soda_can)`（补救） → 9. `navigate(destination=trash_can)`（补救） → 10. `drop(object=soda_can, container=trash_can)`（补救）

### x6_gd_can_put_away（Task）

**情况**：罐子被收进了关着门的微波炉或靠墙柜 → 逐个打开找

**指令**：Someone put the empty soda can away in the microwave or in the low wall cabinet instead of throwing it out. Throw it into the trash can, and close whatever you open.

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

> 午饭吃完了，苹果还在餐桌上。把它收进卧室矮书架上的果篮里；果篮不在的话，就放进书桌上的托盘里。

### fruits_on_table（对照）

**情况**：苹果在餐桌，果篮在书架 → 放进果篮

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

**情况**：书架上没有果篮 → 放书桌上的托盘

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

**情况**：果篮不在，原位置放着一个碗 → 认出那不是果篮，放托盘

**指令**：请把餐桌上的苹果放进卧室书架的果篮；若果篮不在，就放进书桌的托盘。

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `apple` 在 `fruit_basket` 里
  - 第 2 组：
    - `apple` 在 `serving_tray` 里

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=apple)` → 4. `pick(object=apple)` → 5. `navigate(destination=bookcase_2/top)` → 6. `look(target=bookcase_2/top)` → 7. `identify(object=bowl_kitchen_cabinet)`（补救） → 8. `navigate(destination=desk_1/top)`（换做法） → 9. `look(target=desk_1/top)`（换做法） → 10. `navigate(destination=serving_tray)`（换做法） → 11. `place(object=apple, receptacle=serving_tray)`（换做法）

### h_dynamic_basket_taken（Task）

**情况**：拿苹果时有人把果篮拿走 → 放托盘

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `apple` 在 `fruit_basket` 里
  - 第 2 组：
    - `apple` 在 `serving_tray` 里

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=apple)` → 4. `pick(object=apple)` → 5. `navigate(destination=bookcase_2/top)` → 6. `look(target=bookcase_2/top)` → 7. `navigate(destination=desk_1/top)`（换做法） → 8. `look(target=desk_1/top)`（换做法） → 9. `navigate(destination=serving_tray)`（换做法） → 10. `place(object=apple, receptacle=serving_tray)`（换做法）

### x6_gd_fruits_event（Task）

**情况**：两个水果、没有果篮（用托盘）；苹果放好后孩子把橙子拿到电视柜 → 找回橙子放进托盘

**指令**：Lunch is over and the apple and the orange are still on the dining table. Put them into the fruit basket on the low bookcase in the bedroom; if the basket is not there, the serving tray on the study desk will do.

**成功条件**：

- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `apple` 在 `fruit_basket` 里
    - `orange_2` 在 `fruit_basket` 里
  - 第 2 组：
    - `apple` 在 `fruit_basket` 里
    - `orange_2` 在 `serving_tray` 里
  - 第 3 组：
    - `apple` 在 `serving_tray` 里
    - `orange_2` 在 `fruit_basket` 里
  - 第 4 组：
    - `apple` 在 `serving_tray` 里
    - `orange_2` 在 `serving_tray` 里

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=apple)` → 4. `pick(object=apple)` → 5. `navigate(destination=bookcase_2/top)` → 6. `look(target=bookcase_2/top)` → 7. `navigate(destination=desk_1/top)`（补救） → 8. `look(target=desk_1/top)`（补救） → 9. `navigate(destination=serving_tray)`（补救） → 10. `place(object=apple, receptacle=serving_tray)`（补救） → 11. `search(object=orange_2, region=living_room_0_0)`（补救） → 12. `navigate(destination=orange_2)`（补救） → 13. `pick(object=orange_2)`（补救） → 14. `navigate(destination=serving_tray)`（补救） → 15. `place(object=orange_2, receptacle=serving_tray)`（补救）

---

## T12_tidy_toys

> 快到睡觉时间了，把孩子的玩具小车和小黄鸭收进卧室的储物筐里。

### toys_out（对照）

**情况**：小车在客厅地上，鸭子在电视柜 → 都放进筐

**成功条件**：

- `toy_car` 在 `storage_basket` 里
- `rubber_duck` 在 `storage_basket` 里
- `storage_basket` 立着
- 手里空着

**参考调用顺序**：

1. `explore_room(room=bedroom_0_1)` → 2. `explore_room(room=living_room_0_0)` → 3. `navigate(destination=toy_car)` → 4. `pick(object=toy_car)` → 5. `navigate(destination=storage_basket)` → 6. `place(object=toy_car, receptacle=storage_basket)` → 7. `navigate(destination=rubber_duck)` → 8. `pick(object=rubber_duck)` → 9. `navigate(destination=storage_basket)` → 10. `place(object=rubber_duck, receptacle=storage_basket)` → 11. `nod()`（补救）

### duck_in_study（Task）

**情况**：鸭子落在别处 → 找鸭子

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

**指令**：快睡觉了，请把房间里分散的玩具全部收好，放入卧室合适的储物容器。

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

### h_dynamic_duck_taken（Task）

**情况**：没有筐，要按尺寸分配；小车放好后孩子把鸭子拿走 → 小车不动，找鸭子

**指令**：快睡觉了，请把房间里分散的玩具全部收好，放入卧室合适的储物容器。

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

- 摆法 `h_dynamic_duck_taken`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `measure(object=toy_tray)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_car)` → 7. `pick(object=toy_car)` → 8. `navigate(destination=toy_tray)` → 9. `place(object=toy_car, receptacle=toy_tray)` → 10. `navigate(destination=dining_table_2/top)`（补救） → 11. `look(target=dining_table_2/top)`（补救） → 12. `navigate(destination=rubber_duck)` → 13. `pick(object=rubber_duck)` → 14. `navigate(destination=toy_bin_small)` → 15. `drop(object=rubber_duck, container=toy_bin_small)`
- 摆法 `alt_tv_stand_2`：1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `measure(object=toy_bin_small)` → 4. `measure(object=toy_tray)` → 5. `explore_room(room=living_room_0_0)` → 6. `navigate(destination=toy_car)` → 7. `pick(object=toy_car)` → 8. `navigate(destination=toy_tray)` → 9. `place(object=toy_car, receptacle=toy_tray)` → 10. `navigate(destination=tv_stand_2/top)`（补救） → 11. `look(target=tv_stand_2/top)`（补救） → 12. `navigate(destination=rubber_duck)` → 13. `pick(object=rubber_duck)` → 14. `navigate(destination=toy_bin_small)` → 15. `drop(object=rubber_duck, container=toy_bin_small)`

### x6_gd_bins_capacity（Task）

**情况**：没有筐，书架上有两个小箱，其中一个已经半满 → 判断哪个还装得下，分开放

**指令**：It is nearly bedtime. Put the kid's toy car and rubber duck away into the two small toy bins on the bedroom bookcase, each toy completely inside a bin.

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

### x6_pp_duck_moved（Task）

**情况**：小车放进筐后孩子把鸭子拿到别的房间 → 小车不动，找鸭子

**成功条件**：

- `toy_car` 在 `storage_basket` 里
- `rubber_duck` 在 `storage_basket` 里
- `storage_basket` 立着
- 手里空着

**参考调用顺序**：

- 摆法 `dining`：1. `explore_room(room=bedroom_0_1)` → 2. `explore_room(room=living_room_0_0)` → 3. `navigate(destination=toy_car)` → 4. `pick(object=toy_car)` → 5. `navigate(destination=storage_basket)` → 6. `place(object=toy_car, receptacle=storage_basket)` → 7. `search(object=rubber_duck, region=dining_room_0_1)`（补救） → 8. `navigate(destination=rubber_duck)` → 9. `pick(object=rubber_duck)` → 10. `navigate(destination=storage_basket)` → 11. `place(object=rubber_duck, receptacle=storage_basket)` → 12. `nod()`（补救）
- 摆法 `study`：1. `explore_room(room=bedroom_0_1)` → 2. `explore_room(room=living_room_0_0)` → 3. `navigate(destination=toy_car)` → 4. `pick(object=toy_car)` → 5. `navigate(destination=storage_basket)` → 6. `place(object=toy_car, receptacle=storage_basket)` → 7. `search(object=rubber_duck, region=living_room_0_1)`（补救） → 8. `navigate(destination=rubber_duck)` → 9. `pick(object=rubber_duck)` → 10. `navigate(destination=storage_basket)` → 11. `place(object=rubber_duck, receptacle=storage_basket)` → 12. `nod()`（补救）

---

## T13_breakfast_setup

> 摆早餐：餐桌上已经放好勺子了，拿一个碗和一个杯子过来，放在勺子旁边。没有杯子的话用马克杯也行。

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

### bowl_on_cabinet（Task）

**情况**：碗不在原处，一开始看不到 → 找碗

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

- 摆法 `bowl_on_cabinet`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=cup)` → 5. `pick(object=cup)` → 6. `navigate(destination=dining_table_2/top)` → 7. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[3.2, 7.4])` → 8. `navigate(destination=bowl)` → 9. `search(object=bowl, region=living_room_0_0)` → 10. `navigate(destination=bowl)` → 11. `pick(object=bowl)` → 12. `navigate(destination=dining_table_2/top)` → 13. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.05, 7.1])`
- 摆法 `alt_dining_table_2`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=cup)` → 5. `pick(object=cup)` → 6. `navigate(destination=dining_table_2/top)` → 7. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[3.2, 7.4])` → 8. `navigate(destination=bowl)` → 9. `search(object=bowl, region=dining_room_0_1)` → 10. `navigate(destination=bowl)` → 11. `pick(object=bowl)` → 12. `navigate(destination=dining_table_2/top)` → 13. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.05, 7.1])`

### no_cup_bowl_on_cabinet（Task）

**情况**：没杯子（用马克杯），碗也不在原处 → 找碗、换马克杯

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

- 摆法 `no_cup_bowl_on_cabinet`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=bowl)` → 5. `search(object=bowl, region=living_room_0_0)` → 6. `navigate(destination=bowl)` → 7. `pick(object=bowl)` → 8. `navigate(destination=dining_table_2/top)` → 9. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.05, 7.1])` → 10. `navigate(destination=cup)` → 11. `navigate(destination=bookcase_2/top)`（换做法） → 12. `look(target=bookcase_2/top)`（换做法） → 13. `pick(object=mug)`（换做法） → 14. `navigate(destination=dining_table_2/top)` → 15. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[3.2, 7.4])`
- 摆法 `alt_dining_table_2`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=bowl)` → 5. `search(object=bowl, region=dining_room_0_1)` → 6. `navigate(destination=bowl)` → 7. `pick(object=bowl)` → 8. `navigate(destination=dining_table_2/top)` → 9. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.05, 7.1])` → 10. `navigate(destination=cup)` → 11. `navigate(destination=bookcase_2/top)`（换做法） → 12. `look(target=bookcase_2/top)`（换做法） → 13. `pick(object=mug)`（换做法） → 14. `navigate(destination=dining_table_2/top)` → 15. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[3.2, 7.4])`

### no_cup_spoon_boxed_in（Action + Task）

**情况**：没杯子（用马克杯）；勺子被麦片盒和盘子围住，旁边放不下 → 先把勺子挪到有空的地方，再摆碗和马克杯

**指令**：请在餐桌已有的勺子旁摆好碗和杯子；没有 Cup 可用 Mug，保证摆放合理。

**成功条件**：

- `bowl` 在 `dining_table_2/top` 上
- `bowl` 立着
- `spoon` 在 `dining_table_2/top` 上
- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `cup` 在 `dining_table_2/top` 上
    - `cup` 立着
    - bowl、cup、spoon 在 `dining_table_2/top` 上摆在一起（彼此不超过 40 cm）
  - 第 2 组：
    - `mug` 在 `dining_table_2/top` 上
    - `mug` 立着
    - bowl、mug、spoon 在 `dining_table_2/top` 上摆在一起（彼此不超过 40 cm）

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=spoon)` → 4. `pick(object=spoon)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=spoon, receptacle=dining_table_2/top, hint_xy=[3.02, 6.61])` → 7. `navigate(destination=tv_stand_2/top)` → 8. `look(target=tv_stand_2/top)` → 9. `navigate(destination=bowl)` → 10. `pick(object=bowl)` → 11. `navigate(destination=dining_table_2/top)` → 12. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.0, 6.44])` → 13. `navigate(destination=bookcase_2/top)`（换做法） → 14. `look(target=bookcase_2/top)`（换做法） → 15. `pick(object=mug)`（换做法） → 16. `navigate(destination=dining_table_2/top)` → 17. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[3.0, 6.78])`

### h_dynamic_mug_taken（Action + Task）

**情况**：勺子被围住要先挪；碗摆好后有人把马克杯拿走 → 已摆好的不动，找马克杯

**指令**：请在餐桌已有的勺子旁摆好碗和杯子；没有 Cup 可用 Mug，保证摆放合理。

**成功条件**：

- `bowl` 在 `dining_table_2/top` 上
- `bowl` 立着
- `spoon` 在 `dining_table_2/top` 上
- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - `cup` 在 `dining_table_2/top` 上
    - `cup` 立着
    - bowl、cup、spoon 在 `dining_table_2/top` 上摆在一起（彼此不超过 40 cm）
  - 第 2 组：
    - `mug` 在 `dining_table_2/top` 上
    - `mug` 立着
    - bowl、mug、spoon 在 `dining_table_2/top` 上摆在一起（彼此不超过 40 cm）

**参考调用顺序**：

- 摆法 `h_dynamic_mug_taken`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=spoon)` → 4. `pick(object=spoon)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=spoon, receptacle=dining_table_2/top, hint_xy=[3.02, 6.61])` → 7. `navigate(destination=tv_stand_2/top)` → 8. `look(target=tv_stand_2/top)` → 9. `navigate(destination=bowl)` → 10. `pick(object=bowl)` → 11. `navigate(destination=dining_table_2/top)` → 12. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.0, 6.47])` → 13. `search(object=mug, region=living_room_0_0)`（补救） → 14. `navigate(destination=mug)`（补救） → 15. `pick(object=mug)`（换做法） → 16. `navigate(destination=dining_table_2/top)` → 17. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[3.0, 6.74])`
- 摆法 `alt_dining_table_2`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=spoon)` → 4. `pick(object=spoon)` → 5. `navigate(destination=dining_table_2/top)` → 6. `place(object=spoon, receptacle=dining_table_2/top, hint_xy=[3.02, 6.61])` → 7. `navigate(destination=tv_stand_2/top)` → 8. `look(target=tv_stand_2/top)` → 9. `navigate(destination=bowl)` → 10. `pick(object=bowl)` → 11. `navigate(destination=dining_table_2/top)` → 12. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.0, 6.47])` → 13. `search(object=mug, region=dining_room_0_1)`（补救） → 14. `navigate(destination=mug)`（补救） → 15. `pick(object=mug)`（换做法） → 16. `navigate(destination=dining_table_2/top)` → 17. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[3.0, 6.74])`

### x6_pp_spoon_moved__early（Action）

**情况**：碗刚摆好，孩子就把勺子挪到桌子另一头 → 把勺子挪回来，再摆杯子

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

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=bowl)` → 5. `pick(object=bowl)` → 6. `navigate(destination=dining_table_2/top)` → 7. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.05, 7.1])` → 8. `look(target=dining_table_2/top)`（补救） → 9. `navigate(destination=spoon)`（补救） → 10. `pick(object=spoon)`（补救） → 11. `navigate(destination=dining_table_2/top)`（补救） → 12. `place(object=spoon, receptacle=dining_table_2/top, hint_xy=[2.98, 7.46])`（补救） → 13. `navigate(destination=cup)` → 14. `pick(object=cup)` → 15. `navigate(destination=dining_table_2/top)` → 16. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[3.2, 7.4])`

### x6_pp_spoon_moved__table_end（Action）

**情况**：杯子摆好后，勺子被挪到桌子另一头 → 把勺子拿回来

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

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=bowl)` → 5. `pick(object=bowl)` → 6. `navigate(destination=dining_table_2/top)` → 7. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.05, 7.1])` → 8. `navigate(destination=cup)` → 9. `pick(object=cup)` → 10. `navigate(destination=dining_table_2/top)` → 11. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[3.2, 7.4])` → 12. `look(target=dining_table_2/top)`（补救） → 13. `navigate(destination=spoon)`（补救） → 14. `pick(object=spoon)`（补救） → 15. `navigate(destination=dining_table_2/top)`（补救） → 16. `place(object=spoon, receptacle=dining_table_2/top, hint_xy=[2.98, 7.46])`（补救）

### x6_pp_spoon_moved__tv_stand（Task）

**情况**：杯子摆好后，勺子被拿到电视柜 → 找勺子拿回来

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

1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=bowl)` → 5. `pick(object=bowl)` → 6. `navigate(destination=dining_table_2/top)` → 7. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.05, 7.1])` → 8. `navigate(destination=cup)` → 9. `pick(object=cup)` → 10. `navigate(destination=dining_table_2/top)` → 11. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[3.2, 7.4])` → 12. `look(target=dining_table_2/top)`（补救） → 13. `search(object=spoon, region=living_room_0_0)`（补救） → 14. `navigate(destination=spoon)`（补救） → 15. `pick(object=spoon)`（补救） → 16. `navigate(destination=dining_table_2/top)`（补救） → 17. `place(object=spoon, receptacle=dining_table_2/top, hint_xy=[2.98, 7.46])`（补救）

### x6_gd_bowl_put_away（Task）

**情况**：外面没有碗，干净的碗收在靠墙柜或微波炉里 → 逐个打开找

**指令**：Set the dining table for breakfast. The spoon is already there; bring a bowl and a cup and put them next to it. A mug is fine if there is no cup. The clean bowls were put away in the low wall cabinet or the microwave; close whatever you open.

**成功条件**：

- `bowl` 在 `dining_table_2/top` 上
- `bowl` 立着
- 手里空着
- `kitchen_cabinet_6` 关着
- `kitchen_microwave` 关着
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

- 摆法 `in_cabinet`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=kitchen_microwave)` → 5. `open(articulated=kitchen_microwave)` → 6. `look(target=kitchen_microwave/inside_floor)` → 7. `close(articulated=kitchen_microwave)` → 8. `navigate(destination=kitchen_cabinet_6)` → 9. `open(articulated=kitchen_cabinet_6)` → 10. `bend()` → 11. `explore_furniture(furniture=kitchen_cabinet_6)` → 12. `straighten()` → 13. `navigate(destination=bowl)` → 14. `pick(object=bowl)` → 15. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 16. `close(articulated=kitchen_cabinet_6)` → 17. `navigate(destination=dining_table_2/top)` → 18. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.05, 7.1])` → 19. `navigate(destination=cup)` → 20. `pick(object=cup)` → 21. `navigate(destination=dining_table_2/top)` → 22. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[3.2, 7.4])`
- 摆法 `in_microwave`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=kitchen_cabinet_6)` → 5. `open(articulated=kitchen_cabinet_6)` → 6. `bend()` → 7. `explore_furniture(furniture=kitchen_cabinet_6)` → 8. `straighten()` → 9. `close(articulated=kitchen_cabinet_6)` → 10. `navigate(destination=kitchen_microwave)` → 11. `open(articulated=kitchen_microwave)` → 12. `look(target=kitchen_microwave/inside_floor)` → 13. `navigate(destination=bowl)` → 14. `pick(object=bowl)` → 15. `retreat(obstacle=kitchen_microwave, distance_m=0.3)` → 16. `close(articulated=kitchen_microwave)` → 17. `navigate(destination=dining_table_2/top)` → 18. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.05, 7.1])` → 19. `navigate(destination=cup)` → 20. `pick(object=cup)` → 21. `navigate(destination=dining_table_2/top)` → 22. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[3.2, 7.4])`

### x6_gd_two_settings（Task）

**情况**：摆两份：电视柜上有两个碗、一个杯子和马克杯；第一份摆好后有人把马克杯拿走 → 找马克杯摆第二份

**指令**：Set two breakfast places at the dining table: next to each spoon, a bowl and a cup (a mug is fine where there is no cup).

**成功条件**：

- `bowl` 在 `dining_table_2/top` 上
- `bowl_kitchen_cabinet` 在 `dining_table_2/top` 上
- `bowl`、`bowl_kitchen_cabinet` 立着
- 手里空着
- 满足下面任意一组：
  - 第 1 组：
    - bowl、cup、spoon 在 `dining_table_2/top` 上摆在一起（彼此不超过 50 cm）
    - bowl_kitchen_cabinet、mug、spoon_target_table 在 `dining_table_2/top` 上摆在一起（彼此不超过 50 cm）
    - `cup` 立着
    - `mug` 立着
  - 第 2 组：
    - bowl、mug、spoon 在 `dining_table_2/top` 上摆在一起（彼此不超过 50 cm）
    - bowl_kitchen_cabinet、cup、spoon_target_table 在 `dining_table_2/top` 上摆在一起（彼此不超过 50 cm）
    - `mug` 立着
    - `cup` 立着
  - 第 3 组：
    - bowl_kitchen_cabinet、cup、spoon 在 `dining_table_2/top` 上摆在一起（彼此不超过 50 cm）
    - bowl、mug、spoon_target_table 在 `dining_table_2/top` 上摆在一起（彼此不超过 50 cm）
    - `cup` 立着
    - `mug` 立着
  - 第 4 组：
    - bowl_kitchen_cabinet、mug、spoon 在 `dining_table_2/top` 上摆在一起（彼此不超过 50 cm）
    - bowl、cup、spoon_target_table 在 `dining_table_2/top` 上摆在一起（彼此不超过 50 cm）
    - `mug` 立着
    - `cup` 立着

**参考调用顺序**：

- 摆法 `cabinet6`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=bowl)` → 5. `pick(object=bowl)` → 6. `navigate(destination=dining_table_2/top)` → 7. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.05, 7.1])` → 8. `navigate(destination=cup)` → 9. `pick(object=cup)` → 10. `navigate(destination=dining_table_2/top)` → 11. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[3.2, 7.4])` → 12. `navigate(destination=bowl_kitchen_cabinet)`（补救） → 13. `pick(object=bowl_kitchen_cabinet)`（补救） → 14. `navigate(destination=dining_table_2/top)`（补救） → 15. `place(object=bowl_kitchen_cabinet, receptacle=dining_table_2/top, hint_xy=[3.7, 7.12])`（补救） → 16. `search(object=mug, region=living_room_0_0)`（补救） → 17. `navigate(destination=mug)`（补救） → 18. `pick(object=mug)`（补救） → 19. `navigate(destination=dining_table_2/top)`（补救） → 20. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[3.62, 7.62])`（补救）
- 摆法 `cabinet4`：1. `look(target=dining_table_2/top)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=bowl)` → 5. `pick(object=bowl)` → 6. `navigate(destination=dining_table_2/top)` → 7. `place(object=bowl, receptacle=dining_table_2/top, hint_xy=[3.05, 7.1])` → 8. `navigate(destination=cup)` → 9. `pick(object=cup)` → 10. `navigate(destination=dining_table_2/top)` → 11. `place(object=cup, receptacle=dining_table_2/top, hint_xy=[3.2, 7.4])` → 12. `navigate(destination=bowl_kitchen_cabinet)`（补救） → 13. `pick(object=bowl_kitchen_cabinet)`（补救） → 14. `navigate(destination=dining_table_2/top)`（补救） → 15. `place(object=bowl_kitchen_cabinet, receptacle=dining_table_2/top, hint_xy=[3.7, 7.12])`（补救） → 16. `search(object=mug)`（补救） → 17. `navigate(destination=mug)`（补救） → 18. `pick(object=mug)`（补救） → 19. `navigate(destination=dining_table_2/top)`（补救） → 20. `place(object=mug, receptacle=dining_table_2/top, hint_xy=[3.62, 7.62])`（补救）

---

## T15_book_face_up

> 有人把平装书扣在厨房岛台上了，书脊都快压弯了。帮忙把它翻过来正面朝上，还放在岛台上，他还没看完。

### book_free（对照）

**情况**：书周围有空 → 直接翻

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

### h_task_block_on_book（Action）

**情况**：书上压着积木 → 拿开积木放在岛台上，再翻书

**成功条件**：

- `paperback_book` 翻过面
- `paperback_book` 在 `kitchen_island/top` 上
- 手里空着
- `wooden_block_a` 在 `kitchen_island/top` 上

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `place(object=wooden_block_a, receptacle=kitchen_island/top, hint_xy=[7.2, 1.85])` → 5. `navigate(destination=paperback_book)` → 6. `flip(object=paperback_book)`

### h_dynamic_book_moved（Action）

**情况**：拿开积木后孩子又放回去 → 再拿开一次，再翻

**成功条件**：

- `paperback_book` 翻过面
- `paperback_book` 在 `kitchen_island/top` 上
- 手里空着
- `wooden_block_a` 在 `kitchen_island/top` 上

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=wooden_block_a)` → 3. `pick(object=wooden_block_a)` → 4. `place(object=wooden_block_a, receptacle=kitchen_island/top, hint_xy=[7.2, 1.85])` → 5. `look(target=kitchen_island/top)`（补救） → 6. `navigate(destination=wooden_block_a)`（补救） → 7. `pick(object=wooden_block_a)`（补救） → 8. `place(object=wooden_block_a, receptacle=kitchen_island/top, hint_xy=[7.3, 1.85])`（补救） → 9. `navigate(destination=paperback_book)` → 10. `flip(object=paperback_book)`

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

### h_task_bowl_behind（Action）

**情况**：燕麦碗挡在滚动路径上 → 先挪开碗再滚

**成功条件**：

- `rolling_pin` 滚过
- `rolling_pin` 在 `kitchen_island/top` 上
- `rolling_pin` 离台面边缘至少 6 cm
- 手里空着
- `oatmeal` 在 `kitchen_island/top` 上
- `oatmeal` 立着

**参考调用顺序**：

1. `look(target=kitchen_island/top)` → 2. `navigate(destination=oatmeal)` → 3. `push(object=oatmeal, direction_xy=[0.0, 1.0], distance_m=0.15)`（补救） → 4. `navigate(destination=rolling_pin)` → 5. `roll(object=rolling_pin, distance_m=0.12)`

### h_dynamic_bowl_put_behind（Action）

**情况**：机器人看过之后有人把碗推到路径上 → 挪开碗再滚

**成功条件**：

- `rolling_pin` 滚过
- `rolling_pin` 在 `kitchen_island/top` 上
- `rolling_pin` 离台面边缘至少 6 cm
- 手里空着
- `oatmeal` 在 `kitchen_island/top` 上
- `oatmeal` 立着

**参考调用顺序**：

1. `look(target=kitchen_island/top)`（补救） → 2. `look(target=oatmeal)`（补救） → 3. `navigate(destination=oatmeal)` → 4. `pick(object=oatmeal)` → 5. `place(object=oatmeal, receptacle=kitchen_island/top, hint_xy=[7.3, 1.85])` → 6. `navigate(destination=rolling_pin)` → 7. `roll(object=rolling_pin, distance_m=0.12)`

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

### lid_on（Action）

**情况**：锅盖盖着 → 先揭盖再藏

**成功条件**：

- `wooden_block_b` 藏好了（从房间里看不到）
- `handled_cooking_pot` 盖着 `pot_lid`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)` → 6. `navigate(destination=handled_cooking_pot)` → 7. `uncover(container=handled_cooking_pot)` → 8. `navigate(destination=kitchen_island/top)` → 9. `look(target=kitchen_island/top)` → 10. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)`

### block_crowded（Action）

**情况**：积木被碗和擀面杖夹住 → 先拨出来再拿

**成功条件**：

- `wooden_block_b` 藏好了（从房间里看不到）
- `handled_cooking_pot` 盖着 `pot_lid`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)` → 6. `navigate(destination=wooden_block_b)` → 7. `separate(object=wooden_block_b)` → 8. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)`

### lid_on_crowded（Action）

**情况**：锅盖盖着，积木也被夹住 → 揭盖，拨出积木，再藏

**成功条件**：

- `wooden_block_b` 藏好了（从房间里看不到）
- `handled_cooking_pot` 盖着 `pot_lid`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)` → 6. `navigate(destination=handled_cooking_pot)` → 7. `uncover(container=handled_cooking_pot)` → 8. `navigate(destination=kitchen_island/top)` → 9. `look(target=kitchen_island/top)` → 10. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)` → 11. `navigate(destination=wooden_block_b)` → 12. `separate(object=wooden_block_b)` → 13. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)`

### h_task_lid_elsewhere（Task）

**情况**：锅盖在靠墙柜上 → 先把锅盖拿到灶台，再藏

**成功条件**：

- `wooden_block_b` 藏好了（从房间里看不到）
- `handled_cooking_pot` 盖着 `pot_lid`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=pot_lid)` → 4. `pick(object=pot_lid)` → 5. `navigate(destination=kitchen_stove/top)` → 6. `place(object=pot_lid, receptacle=kitchen_stove/top, hint_xy=[8.715, 1.655])` → 7. `navigate(destination=handled_cooking_pot)` → 8. `look(target=kitchen_stove/top)` → 9. `navigate(destination=kitchen_island/top)` → 10. `look(target=kitchen_island/top)` → 11. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)`

### h_dynamic_lid_put_on（Action + Task）

**情况**：锅盖在别处要先拿来；机器人找积木时有人把盖子盖回锅上 → 再揭开

**成功条件**：

- `wooden_block_b` 藏好了（从房间里看不到）
- `handled_cooking_pot` 盖着 `pot_lid`
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6/top)` → 2. `look(target=kitchen_cabinet_6/top)` → 3. `navigate(destination=pot_lid)` → 4. `pick(object=pot_lid)` → 5. `navigate(destination=kitchen_stove/top)` → 6. `place(object=pot_lid, receptacle=kitchen_stove/top, hint_xy=[8.715, 1.655])` → 7. `navigate(destination=handled_cooking_pot)` → 8. `look(target=kitchen_stove/top)` → 9. `navigate(destination=kitchen_island/top)` → 10. `look(target=kitchen_island/top)` → 11. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)` → 12. `navigate(destination=handled_cooking_pot)`（补救） → 13. `uncover(container=handled_cooking_pot)`（补救） → 14. `navigate(destination=kitchen_island/top)`（补救） → 15. `look(target=kitchen_island/top)`（补救） → 16. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)`（补救）

### x6_pp_lid_lifted（Task）

**情况**：藏好后有人偷看，把锅盖放到了别处 → 找回锅盖盖上，积木不用重藏

**成功条件**：

- `wooden_block_b` 藏好了（从房间里看不到）
- `handled_cooking_pot` 盖着 `pot_lid`
- 手里空着

**参考调用顺序**：

- 摆法 `cabinet4`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)` → 6. `look(target=kitchen_stove/top)`（补救） → 7. `search(object=pot_lid)`（补救） → 8. `navigate(destination=pot_lid)`（补救） → 9. `pick(object=pot_lid)`（补救） → 10. `navigate(destination=handled_cooking_pot)`（补救） → 11. `cover(container=handled_cooking_pot, lid=pot_lid)`（补救）
- 摆法 `dining`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)` → 6. `look(target=kitchen_stove/top)`（补救） → 7. `search(object=pot_lid, region=dining_room_0_1)`（补救） → 8. `navigate(destination=pot_lid)`（补救） → 9. `pick(object=pot_lid)`（补救） → 10. `navigate(destination=handled_cooking_pot)`（补救） → 11. `cover(container=handled_cooking_pot, lid=pot_lid)`（补救）

### x6_gd_hide_both_event（Task）

**情况**：两块积木藏进同一个锅；第一块藏好后孩子把另一块拿走 → 找到再藏

**指令**：We are playing hide-and-seek with the kid's toy blocks: hide both wooden blocks in the empty pot on the stove and put the lid on so they cannot see them.

**成功条件**：

- `wooden_block_b` 藏好了（从房间里看不到）
- `floor_block` 藏好了（从房间里看不到）
- `handled_cooking_pot` 盖着 `pot_lid`
- 手里空着

**参考调用顺序**：

- 摆法 `tv_stand`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)` → 6. `search(object=floor_block, region=living_room_0_0)`（补救） → 7. `navigate(destination=handled_cooking_pot)`（补救） → 8. `uncover(container=handled_cooking_pot)`（补救） → 9. `navigate(destination=floor_block)`（补救） → 10. `look(target=floor_block)`（补救） → 11. `hide(object=floor_block, receptacle=handled_cooking_pot, lid=pot_lid)`（补救）
- 摆法 `dining`：1. `navigate(destination=kitchen_stove/top)` → 2. `look(target=kitchen_stove/top)` → 3. `navigate(destination=kitchen_island/top)` → 4. `look(target=kitchen_island/top)` → 5. `hide(object=wooden_block_b, receptacle=handled_cooking_pot, lid=pot_lid)` → 6. `search(object=floor_block, region=dining_room_0_1)`（补救） → 7. `navigate(destination=handled_cooking_pot)`（补救） → 8. `uncover(container=handled_cooking_pot)`（补救） → 9. `navigate(destination=floor_block)`（补救） → 10. `look(target=floor_block)`（补救） → 11. `hide(object=floor_block, receptacle=handled_cooking_pot, lid=pot_lid)`（补救）

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

### m_door_left_open（Action）

**情况**：柜门本来就开着 → 不用开，直接看，然后关上

**成功条件**：

- 看到过 `plate_inside_kitchen_cabinet`
- 看到过 `bowl_inside_kitchen_cabinet`
- `kitchen_cabinet_6` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6)` → 2. `inspect(receptacle=kitchen_cabinet_6)` → 3. `close(articulated=kitchen_cabinet_6)`

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

### h_dynamic_door_closed（Action + Task）

**情况**：同上；刚开门就有人把门推上 → 再开一次

**指令**：奶奶想知道矮墙柜里还有没有干净的盘子和碗做晚饭用。请看一下柜子里面，看完把柜门关好。

**成功条件**：

- 看到过 `plate_inside_kitchen_cabinet`
- 看到过 `bowl_inside_kitchen_cabinet`
- `kitchen_cabinet_6` 关着
- 手里空着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `inspect(receptacle=kitchen_cabinet_6)` → 4. `open(articulated=kitchen_cabinet_6)`（补救） → 5. `inspect(receptacle=kitchen_cabinet_6)`（补救） → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `inspect(receptacle=kitchen_cabinet_4)` → 10. `close(articulated=kitchen_cabinet_4)`

### x6_gd_bowl_elsewhere__two_places（Task）

**情况**：盘子在靠墙柜，碗在微波炉里 → 两处都查

**指令**：Grandma wants to know whether there is still a clean plate and bowl for dinner, in the low wall cabinet or the microwave. Have a look and close every door properly afterwards.

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

**指令**：Grandma wants to know whether there is still a clean plate and bowl for dinner somewhere in the low kitchen cabinets or the microwave. Have a look and close every door properly afterwards.

**成功条件**：

- 看到过 `plate_inside_kitchen_cabinet`
- 看到过 `bowl_inside_kitchen_cabinet`
- `kitchen_cabinet_6` 关着
- `kitchen_microwave` 关着
- 手里空着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `inspect(receptacle=kitchen_cabinet_6)` → 4. `close(articulated=kitchen_cabinet_6)` → 5. `navigate(destination=kitchen_cabinet_4)` → 6. `open(articulated=kitchen_cabinet_4)` → 7. `inspect(receptacle=kitchen_cabinet_4)` → 8. `close(articulated=kitchen_cabinet_4)` → 9. `navigate(destination=kitchen_microwave)` → 10. `open(articulated=kitchen_microwave)` → 11. `look(target=kitchen_microwave/inside_floor)` → 12. `close(articulated=kitchen_microwave)`

### x6_pp_door_reopened（Action）

**情况**：关好后有人又把门打开 → 再关一次，不用重看

**成功条件**：

- 看到过 `plate_inside_kitchen_cabinet`
- 看到过 `bowl_inside_kitchen_cabinet`
- `kitchen_cabinet_6` 关着
- 手里空着

**参考调用顺序**：

1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `inspect(receptacle=kitchen_cabinet_6)` → 4. `close(articulated=kitchen_cabinet_6)` → 5. `close(articulated=kitchen_cabinet_6)`（补救）

---

## T19_recycling

> 电影看完了，空易拉罐还在电视柜上，快递里的泡沫块掉在客厅地上。把它们都放进平时当回收箱用的宽储物箱，它一般在卧室的矮书架上。

### bin_on_bookcase（对照）

**情况**：都在原处 → 两样都放进回收箱

**成功条件**：

- `soda_can` 在 `wide_storage_bin` 里
- `foam_cube` 在 `wide_storage_bin` 里
- 手里空着

**参考调用顺序**：

1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `navigate(destination=soda_can)` → 5. `pick(object=soda_can)` → 6. `navigate(destination=bookcase_2/top)` → 7. `look(target=bookcase_2/top)` → 8. `navigate(destination=wide_storage_bin)` → 9. `approach(target=wide_storage_bin)` → 10. `drop(object=soda_can, container=wide_storage_bin)` → 11. `navigate(destination=foam_cube)` → 12. `pick(object=foam_cube)` → 13. `navigate(destination=wide_storage_bin)` → 14. `drop(object=foam_cube, container=wide_storage_bin)`

### m_can_in_dining_room（Task）

**情况**：罐子不在原处，看不到 → 先找

**成功条件**：

- `soda_can` 在 `wide_storage_bin` 里
- `foam_cube` 在 `wide_storage_bin` 里
- 手里空着

**参考调用顺序**：

- 摆法 `m_can_in_dining_room`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=dining_room_0_1)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `navigate(destination=wide_storage_bin)` → 10. `approach(target=wide_storage_bin)` → 11. `drop(object=soda_can, container=wide_storage_bin)` → 12. `navigate(destination=foam_cube)` → 13. `pick(object=foam_cube)` → 14. `navigate(destination=wide_storage_bin)` → 15. `drop(object=foam_cube, container=wide_storage_bin)`
- 摆法 `alt_tv_stand_2`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=living_room_0_0)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `navigate(destination=wide_storage_bin)` → 10. `approach(target=wide_storage_bin)` → 11. `drop(object=soda_can, container=wide_storage_bin)` → 12. `navigate(destination=foam_cube)` → 13. `pick(object=foam_cube)` → 14. `navigate(destination=wide_storage_bin)` → 15. `drop(object=foam_cube, container=wide_storage_bin)`

### lookalike_bin（Task）

**情况**：罐子不在原处；客厅还有个一模一样、装着积木的箱子 → 认准书架上那个（里面有塑料杯）

**指令**：把易拉罐和泡沫块送到卧室矮书架附近用于回收的宽储物箱中。

**成功条件**：

- `soda_can` 在 `wide_storage_bin` 里
- `foam_cube` 在 `wide_storage_bin` 里
- 手里空着

**参考调用顺序**：

- 摆法 `lookalike_bin`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=dining_room_0_1)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `identify(object=wide_storage_bin)`（补救） → 10. `navigate(destination=wide_storage_bin)` → 11. `approach(target=wide_storage_bin)` → 12. `drop(object=soda_can, container=wide_storage_bin)` → 13. `navigate(destination=foam_cube)` → 14. `touch(object=foam_cube)`（补救） → 15. `pick(object=foam_cube)` → 16. `navigate(destination=wide_storage_bin)` → 17. `drop(object=foam_cube, container=wide_storage_bin)`
- 摆法 `alt_tv_stand_2`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=living_room_0_0)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `identify(object=wide_storage_bin)`（补救） → 10. `navigate(destination=wide_storage_bin)` → 11. `approach(target=wide_storage_bin)` → 12. `drop(object=soda_can, container=wide_storage_bin)` → 13. `navigate(destination=foam_cube)` → 14. `touch(object=foam_cube)`（补救） → 15. `pick(object=foam_cube)` → 16. `navigate(destination=wide_storage_bin)` → 17. `drop(object=foam_cube, container=wide_storage_bin)`

### h_dynamic_cube_moved（Task）

**情况**：要认准回收箱；罐子放好后有人把泡沫块拿走 → 罐子不动，找泡沫块

**指令**：把易拉罐和泡沫块送到卧室矮书架附近用于回收的宽储物箱中。

**成功条件**：

- `soda_can` 在 `wide_storage_bin` 里
- `foam_cube` 在 `wide_storage_bin` 里
- 手里空着

**参考调用顺序**：

- 摆法 `h_dynamic_cube_moved`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=tv_stand_2/top)` → 3. `look(target=tv_stand_2/top)` → 4. `search(object=soda_can, region=dining_room_0_1)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `navigate(destination=wide_storage_bin)` → 10. `approach(target=wide_storage_bin)` → 11. `drop(object=soda_can, container=wide_storage_bin)` → 12. `search(object=foam_cube, region=living_room_0_0)`（补救） → 13. `navigate(destination=foam_cube)` → 14. `pick(object=foam_cube)` → 15. `navigate(destination=wide_storage_bin)` → 16. `drop(object=foam_cube, container=wide_storage_bin)`
- 摆法 `alt_kitchen_cabinet_6`：1. `explore_room(room=living_room_0_0)` → 2. `navigate(destination=kitchen_cabinet_6/top)` → 3. `look(target=kitchen_cabinet_6/top)` → 4. `search(object=soda_can, region=dining_room_0_1)` → 5. `navigate(destination=soda_can)` → 6. `pick(object=soda_can)` → 7. `navigate(destination=bookcase_2/top)` → 8. `look(target=bookcase_2/top)` → 9. `navigate(destination=wide_storage_bin)` → 10. `approach(target=wide_storage_bin)` → 11. `drop(object=soda_can, container=wide_storage_bin)` → 12. `search(object=foam_cube, region=living_room_0_0)`（补救） → 13. `navigate(destination=foam_cube)` → 14. `pick(object=foam_cube)` → 15. `navigate(destination=wide_storage_bin)` → 16. `drop(object=foam_cube, container=wide_storage_bin)`

### x6_gd_can_put_away（Task）

**情况**：罐子在两个关着的矮柜之一 → 逐个找

**指令**：Movie night is over. Someone put the empty soda can away in one of the low kitchen cabinets, and the foam packing cube from the delivery lies on the living-room floor; take both to the wide storage bin we use for recycling, on the low bookcase in the bedroom. Close the cabinets again.

**成功条件**：

- `soda_can` 在 `wide_storage_bin` 里
- `foam_cube` 在 `wide_storage_bin` 里
- 手里空着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

- 摆法 `in_4`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=soda_can)` → 13. `pick(object=soda_can)` → 14. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 15. `close(articulated=kitchen_cabinet_4)` → 16. `navigate(destination=bookcase_2/top)` → 17. `look(target=bookcase_2/top)` → 18. `navigate(destination=wide_storage_bin)` → 19. `approach(target=wide_storage_bin)` → 20. `drop(object=soda_can, container=wide_storage_bin)` → 21. `navigate(destination=foam_cube)` → 22. `pick(object=foam_cube)` → 23. `navigate(destination=wide_storage_bin)` → 24. `drop(object=foam_cube, container=wide_storage_bin)`
- 摆法 `in_6`：1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_4)` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=soda_can)` → 13. `pick(object=soda_can)` → 14. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 15. `close(articulated=kitchen_cabinet_6)` → 16. `navigate(destination=bookcase_2/top)` → 17. `look(target=bookcase_2/top)` → 18. `navigate(destination=wide_storage_bin)` → 19. `approach(target=wide_storage_bin)` → 20. `drop(object=soda_can, container=wide_storage_bin)` → 21. `navigate(destination=foam_cube)` → 22. `pick(object=foam_cube)` → 23. `navigate(destination=wide_storage_bin)` → 24. `drop(object=foam_cube, container=wide_storage_bin)`

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

### table_full（Action）

**情况**：餐桌被托盘、盘子、碗摆满 → 先把一个碗挪到托盘上腾位置，再放瓶子

**指令**：找到果汁瓶，确保它直立放回餐桌；必要时先为桌面其他物品腾出空间。

**成功条件**：

- `juice_bottle` 在 `dining_table_2/top` 上
- `juice_bottle` 立着
- 手里空着
- 这 16 件中至少 14 件还在 `dining_table_2/top` 上：`buffet_tray_1`、`buffet_tray_2`、`party_plate_3`、`party_plate_4`、`party_plate_5`、`buffet_tray_6`、`buffet_tray_7`、`party_plate_8`、`party_plate_9`、`party_plate_10`、`buffet_tray_11`、`buffet_tray_12`、`party_bowl_1`、`party_bowl_2`、`party_bowl_3`、`party_bowl_4`

**参考调用顺序**：

1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=party_bowl_1)` → 4. `approach(target=party_bowl_1)` → 5. `look(target=party_bowl_1)`（补救） → 6. `pick(object=party_bowl_1)` → 7. `place(object=party_bowl_1, receptacle=buffet_tray_11)` → 8. `navigate(destination=tv_stand_2/top)` → 9. `navigate(destination=kitchen_cabinet_6/top)` → 10. `look(target=kitchen_cabinet_6/top)` → 11. `navigate(destination=juice_bottle)` → 12. `pick(object=juice_bottle)` → 13. `navigate(destination=dining_table_2/top)` → 14. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[2.945, 7.765])`

### h_dynamic_bottle_taken（Action + Task）

**情况**：餐桌满要先腾位置；看到瓶子后有人把它拿走 → 找瓶子

**指令**：找到果汁瓶，确保它直立放回餐桌；必要时先为桌面其他物品腾出空间。

**成功条件**：

- `juice_bottle` 在 `dining_table_2/top` 上
- `juice_bottle` 立着
- 手里空着
- 这 16 件中至少 14 件还在 `dining_table_2/top` 上：`buffet_tray_1`、`buffet_tray_2`、`party_plate_3`、`party_plate_4`、`party_plate_5`、`buffet_tray_6`、`buffet_tray_7`、`party_plate_8`、`party_plate_9`、`party_plate_10`、`buffet_tray_11`、`buffet_tray_12`、`party_bowl_1`、`party_bowl_2`、`party_bowl_3`、`party_bowl_4`

**参考调用顺序**：

- 摆法 `h_dynamic_bottle_taken`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=party_bowl_1)` → 4. `approach(target=party_bowl_1)` → 5. `look(target=party_bowl_1)`（补救） → 6. `pick(object=party_bowl_1)` → 7. `place(object=party_bowl_1, receptacle=buffet_tray_11)` → 8. `navigate(destination=tv_stand_2/top)` → 9. `navigate(destination=kitchen_cabinet_6/top)` → 10. `look(target=kitchen_cabinet_6/top)` → 11. `search(object=juice_bottle, region=living_room_0_0)`（补救） → 12. `navigate(destination=juice_bottle)` → 13. `pick(object=juice_bottle)` → 14. `navigate(destination=dining_table_2/top)` → 15. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[2.945, 7.765])`
- 摆法 `alt_kitchen_cabinet_4`：1. `navigate(destination=dining_table_2/top)` → 2. `look(target=dining_table_2/top)` → 3. `navigate(destination=party_bowl_1)` → 4. `approach(target=party_bowl_1)` → 5. `look(target=party_bowl_1)`（补救） → 6. `pick(object=party_bowl_1)` → 7. `place(object=party_bowl_1, receptacle=buffet_tray_11)` → 8. `navigate(destination=kitchen_cabinet_4/top)` → 9. `navigate(destination=kitchen_cabinet_6/top)` → 10. `look(target=kitchen_cabinet_6/top)` → 11. `search(object=juice_bottle)`（补救） → 12. `navigate(destination=juice_bottle)` → 13. `pick(object=juice_bottle)` → 14. `navigate(destination=dining_table_2/top)` → 15. `place(object=juice_bottle, receptacle=dining_table_2/top, hint_xy=[2.945, 7.765])`

### x6_gd_bottle_put_away（Task）

**情况**：瓶子被收进了两个矮柜之一 → 逐个找

**指令**：Someone put the juice bottle away in one of the low kitchen cabinets. Put it back on the dining table, standing up, and close the cabinets again.

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

> 孩子看完书，把红色的书留在了书桌上。把它放回卧室的矮书架上。

### e1_book_ready（对照）

**情况**：书已经探出书桌边缘 → 拿起放回书架

**成功条件**：

- `book_red` 在 `bookcase_2/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=book_red)` → 4. `pick(object=book_red)` → 5. `navigate(destination=bookcase_2/top)` → 6. `place(object=book_red, receptacle=bookcase_2/top)`

### book_on_desk（Action）

**情况**：书平放在书桌上 → 先推出边缘再抓

**成功条件**：

- `book_red` 在 `bookcase_2/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=book_red)` → 4. `expose(object=book_red)` → 5. `look(target=book_red)`（补救） → 6. `pick(object=book_red)` → 7. `navigate(destination=bookcase_2/top)` → 8. `place(object=book_red, receptacle=bookcase_2/top)`

### shelf_taken（Action）

**情况**：书平放（要推出边缘）；书架顶被马克杯和鸭子占了 → 先挪开马克杯腾地方

**指令**：把红书放回卧室矮书架，并妥善处理原有占位物。

**成功条件**：

- `book_red` 在 `bookcase_2/top` 上
- 手里空着
- `mug_shelf` 立着
- `mug_shelf` 不在地上
- `shelf_blocker` 不在地上

**参考调用顺序**：

1. `navigate(destination=bookcase_2/top)` → 2. `look(target=bookcase_2/top)` → 3. `navigate(destination=mug_shelf)` → 4. `pick(object=mug_shelf)` → 5. `place(object=mug_shelf, receptacle=bookcase_2/top, hint_xy=[0.79, -0.31])` → 6. `navigate(destination=desk_1/top)` → 7. `look(target=desk_1/top)` → 8. `navigate(destination=book_red)` → 9. `expose(object=book_red)` → 10. `look(target=desk_1/top)`（补救） → 11. `pick(object=book_red)` → 12. `navigate(destination=bookcase_2/top)` → 13. `place(object=book_red, receptacle=bookcase_2/top)`

### h_dynamic_shelf_taken（Action）

**情况**：机器人在书桌那边时，有人在书架上放了马克杯和鸭子 → 挪开马克杯再放书

**成功条件**：

- `book_red` 在 `bookcase_2/top` 上
- 手里空着

**参考调用顺序**：

1. `navigate(destination=desk_1/top)` → 2. `look(target=desk_1/top)` → 3. `navigate(destination=bookcase_2/top)`（补救） → 4. `look(target=bookcase_2/top)`（补救） → 5. `navigate(destination=mug_shelf)`（补救） → 6. `pick(object=mug_shelf)`（补救） → 7. `place(object=mug_shelf, receptacle=bookcase_2/top, hint_xy=[0.79, -0.31])`（补救） → 8. `navigate(destination=desk_1/top)`（补救） → 9. `look(target=desk_1/top)`（补救） → 10. `navigate(destination=book_red)`（补救） → 11. `expose(object=book_red)`（补救） → 12. `look(target=book_red)`（补救） → 13. `pick(object=book_red)`（补救） → 14. `navigate(destination=bookcase_2/top)`（补救） → 15. `place(object=book_red, receptacle=bookcase_2/top)`（补救）

### x6_gd_book_put_away（Task）

**情况**：红书被收进了两个矮柜之一 → 逐个找，拿出来（要推出边缘）

**指令**：The kid put the red book away in one of the low kitchen cabinets instead of the bookcase. Put it back on the low bookcase in the bedroom, and close the cabinets again.

**成功条件**：

- `book_red` 在 `bookcase_2/top` 上
- 手里空着
- `kitchen_cabinet_6` 关着
- `kitchen_cabinet_4` 关着

**参考调用顺序**：

- 摆法 `in_4`：1. `navigate(destination=kitchen_cabinet_6)` → 2. `open(articulated=kitchen_cabinet_6)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_6)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_6)` → 7. `navigate(destination=kitchen_cabinet_4)` → 8. `open(articulated=kitchen_cabinet_4)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_4)` → 11. `straighten()` → 12. `navigate(destination=book_red)` → 13. `expose(object=book_red)` → 14. `look(target=book_red)`（补救） → 15. `pick(object=book_red)` → 16. `retreat(obstacle=kitchen_cabinet_4, distance_m=0.3)` → 17. `close(articulated=kitchen_cabinet_4)` → 18. `navigate(destination=bookcase_2/top)` → 19. `place(object=book_red, receptacle=bookcase_2/top)`
- 摆法 `in_6`：1. `navigate(destination=kitchen_cabinet_4)` → 2. `open(articulated=kitchen_cabinet_4)` → 3. `bend()` → 4. `explore_furniture(furniture=kitchen_cabinet_4)` → 5. `straighten()` → 6. `close(articulated=kitchen_cabinet_4)` → 7. `navigate(destination=kitchen_cabinet_6)` → 8. `open(articulated=kitchen_cabinet_6)` → 9. `bend()` → 10. `explore_furniture(furniture=kitchen_cabinet_6)` → 11. `straighten()` → 12. `navigate(destination=book_red)` → 13. `expose(object=book_red)` → 14. `look(target=book_red)`（补救） → 15. `pick(object=book_red)` → 16. `retreat(obstacle=kitchen_cabinet_6, distance_m=0.3)` → 17. `close(articulated=kitchen_cabinet_6)` → 18. `navigate(destination=bookcase_2/top)` → 19. `place(object=book_red, receptacle=bookcase_2/top)`

