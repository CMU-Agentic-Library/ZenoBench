# v6 全部指令与成功条件（2026-11-24，放宽和指令修订后）

每个设计：布局、中英文指令、各得分档（分数 | 说明 | 条件简写）。条件取该设计第一个布局。指令修订见 `instructions_1124.py`。

## T01_book_to_dining_table

- 基础指令 EN：Bring the book on the island to the dining table to carry on reading over breakfast.
- 基础指令 中：把岛台上那本书拿到餐桌，吃早饭时接着看。

### T01 · overhang_ready（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the book already overhangs the island's front edge by about 6 cm

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the book on either dining table | on_any(paperback_book, [dining_table_2/top/dining_table_1/top]) |
| 0 | the book anywhere else (coffee table, island, counter, floor) or still held | |

### T01 · table_seats（布局 6 个）

- 指令 EN：Breakfast is set. Put the book from the island on the dining table so the guests can read while eating, without getting in the way of their meal. Leave everything else as it is.
- 指令 中：早餐摆好了，把岛台上的书在餐桌上放好，方便客人边吃边看，别影响用餐。其他东西别动。
- 场景：breakfast is set for three along the east edge of the dining table (a plate or bowl and a drink per seat, two cereal boxes); the edge has several free slots: one too narrow between two seats, one wide but at the far end beyond the cereal boxes, away from every seat, and one wide slot beside a seat; the west half of the table is empty
- 考察：spot_quality

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the wide slot beside a seat: easy to read while eating, 5 cm clear of the dishes, nothing moved | clear_of(paperback_book, [plate_counter_a/plate_counter_b/bowl_side_table/cup_side_table/cup_counter_b/mug_dining_cabinet/...], 0.05) & near_any(paperback_book, [bowl_side_table/plate_counter_a/plate_counter_b], 0.15) & on(paperback_book, dining_table_2/top); left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_counter_b, cup_side_table, mug_dining_cabinet, plate_counter_a, plate_counter_b ... |
| 0.6 | on the set table, clear of the dishes, nothing moved, but beside no seat (the far end or the west half): out of the way, the guest has to reach for it | clear_of(paperback_book, [plate_counter_a/plate_counter_b/bowl_side_table/cup_side_table/cup_counter_b/mug_dining_cabinet/...], 0.05) & on(paperback_book, dining_table_2/top); left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_counter_b, cup_side_table, mug_dining_cabinet, plate_counter_a, plate_counter_b ... |
| 0.3 | squeezed into the narrow slot against the dishes, though nothing moved | on(paperback_book, dining_table_2/top); left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_counter_b, cup_side_table, mug_dining_cabinet, plate_counter_a, plate_counter_b ... |
| 0 | on the other, unset dining table (dining_table_1); a dish moved or tipped to make room; anywhere else or still held | |

### T01 · which_table（布局 8 个）

- 指令 EN：The guests are having breakfast. Put the book from the island on their table so they can read while eating, without getting in the way of their meal. Leave everything else as it is.
- 指令 中：客人正在吃早饭，把岛台上的书放到他们桌上，方便边吃边看，别影响用餐。其他东西别动。
- 场景：the house has two dining tables, the near one (6 m) and one in the west dining room (16 m); breakfast for three is set on one of them, the other holds the kid's toys and the storage bin and has free edge slots too; the instruction does not say which table
- 考察：destination_unnamed, spot_quality

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the guests' table, the wide slot beside a seat, clear of the dishes, nothing moved | clear_of(paperback_book, [plate_counter_a/plate_counter_b/bowl_side_table/cup_side_table/cup_counter_b/mug_dining_cabinet/...], 0.05) & near_any(paperback_book, [bowl_side_table/plate_counter_a/plate_counter_b], 0.15) & on(paperback_book, dining_table_2/top); left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_counter_b, cup_side_table, mug_dining_cabinet, plate_counter_a, plate_counter_b ... |
| 0.6 | the guests' table, clear of the dishes, nothing moved, beside no seat | clear_of(paperback_book, [plate_counter_a/plate_counter_b/bowl_side_table/cup_side_table/cup_counter_b/mug_dining_cabinet/...], 0.05) & on(paperback_book, dining_table_2/top); left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_counter_b, cup_side_table, mug_dining_cabinet, plate_counter_a, plate_counter_b ... |
| 0.3 | the guests' table, squeezed against the dishes, nothing moved | one of: on(paperback_book, dining_table_2/top) // on(paperback_book, dining_table_1/top); left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_counter_b, cup_side_table, mug_dining_cabinet, plate_counter_a, plate_counter_b ... |
| 0 | the toy table (the wrong table); a dish moved or tipped; anywhere else or still held | |

### T01 · no_room_fallback（布局 6 个）

- 指令 EN：Put the book from the island on the dining table so the guests can read while eating, without getting in the way of their meal; if there really is no suitable place, put it away on a bookcase for now. Leave everything else as it is.
- 指令 中：把岛台上的书在餐桌上放好，方便客人边吃边看，别影响用餐；实在没合适的位置，就先收进书柜。其他东西别动。
- 场景：breakfast is set for three as in table_seats; in one layout of three a cereal box stands in the one wide slot beside a seat, so no slot is both beside a seat and clear of the tableware; the instruction forbids moving the tableware and the cereal and names a fallback place
- 考察：spot_quality, infeasible_fallback

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | a slot beside a seat: there, clear of the dishes, nothing moved; no such slot (full_*): a bookcase, the fallback the instruction names (any bookcase, any shelf) | clear_of(paperback_book, [plate_counter_a/plate_counter_b/bowl_side_table/cup_side_table/cup_counter_b/mug_dining_cabinet/...], 0.05) & near_any(paperback_book, [bowl_side_table/plate_counter_a/plate_counter_b], 0.15) & on(paperback_book, dining_table_2/top); left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_counter_b, cup_side_table, mug_dining_cabinet, plate_counter_a, plate_counter_b ... |
| 0.6 | on the set table, clear of the dishes, nothing moved, beside no seat (with no suitable slot: the instruction's fallback skipped, the meal not disturbed) | clear_of(paperback_book, [plate_counter_a/plate_counter_b/bowl_side_table/cup_side_table/cup_counter_b/mug_dining_cabinet/...], 0.05) & on(paperback_book, dining_table_2/top); left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_counter_b, cup_side_table, mug_dining_cabinet, plate_counter_a, plate_counter_b ... |
| 0.3 | squeezed against the dishes or the cereal, nothing moved; or, with a suitable slot free, put away in a bookcase (gave up too early) | one of: on(paperback_book, dining_table_2/top) // on(paperback_book, bookcase_1/top) // on(paperback_book, bookcase_1/shelf_1) // on(paperback_book, bookcase_1/shelf_0) // ... 9 more ways; left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_counter_b, cup_side_table, mug_dining_cabinet, plate_counter_a, plate_counter_b ... |
| 0 | a dish or the cereal moved or tipped to make room; anywhere else or still held | |

### T01 · reader_seat（布局 6 个）

- 指令 EN：The guest drinking coffee from a mug wants to read the book on the island over breakfast. Set it on the dining table for them without getting in the way of their meal. Leave everything else as it is.
- 指令 中：用马克杯喝咖啡的客人想边吃早饭边看岛台上那本书，帮他在餐桌上放好，别影响用餐。其他东西别动。
- 场景：three seats, each a plate or bowl with its drink, and a wide free slot beside every seat; one seat has a coffee mug (with a handle), the other two a cup without one; the instruction says the guest drinks coffee from the mug with a handle, not which seat that is
- 考察：referent_clue, spot_quality

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | beside the seat with the mug, clear of the dishes, nothing moved | clear_of(paperback_book, [plate_counter_a/plate_counter_b/bowl_side_table/cup_side_table/cup_counter_b/mug_dining_cabinet/...], 0.05) & near_any(paperback_book, [plate_counter_a/mug_dining_cabinet], 0.15) & not near_any(paperback_book, [bowl_side_table/plate_counter_b], 0.15) & on(paperback_book, dining_table_2/top); left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_counter_b, cup_side_table, mug_dining_cabinet, plate_counter_a, plate_counter_b ... |
| 0.6 | on the table, clear of the dishes, nothing moved, beside no seat: the reader not found, but a neutral spot anyone can reach | clear_of(paperback_book, [plate_counter_a/plate_counter_b/bowl_side_table/cup_side_table/cup_counter_b/mug_dining_cabinet/...], 0.05) & not near_any(paperback_book, [bowl_side_table/plate_counter_a/plate_counter_b], 0.15) & on(paperback_book, dining_table_2/top); left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_counter_b, cup_side_table, mug_dining_cabinet, plate_counter_a, plate_counter_b ... |
| 0.3 | on the table, nothing moved, but beside another guest (the wrong reader) or against the dishes | on(paperback_book, dining_table_2/top); left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_counter_b, cup_side_table, mug_dining_cabinet, plate_counter_a, plate_counter_b ... |
| 0 | a dish moved or tipped; anywhere else (the other dining table too) or still held | |

### T01 · which_book（布局 2 个）

- 指令 EN（which_book__living）：The guest wants to carry on over breakfast with the book they were leafing through while watching TV last night. Bring it to the dining table.
- 指令 中（which_book__living）：客人想吃早饭时接着看昨晚看电视时翻的那本书，帮忙拿到餐桌上。
- 指令 EN（which_book__bedroom）：The guest wants to carry on over breakfast with the book they read before going to sleep last night. Bring it to the dining table.
- 指令 中（which_book__bedroom）：客人想吃早饭时接着看昨晚睡前读的那本书，帮忙拿到餐桌上。
- 场景：a book lies on the island; the guest's book is in the room they read in last night (on the TV stand in the living room, or on the bookcase in the bedroom), and the other room has a third book; the instruction names only what the guest was doing (watching TV, or before going to sleep), not the room
- 考察：referent_clue, item_out_of_view, unsuitable_at_hand

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | only the guest's book on a dining table, the other two untouched | on_any(paperback_book, [dining_table_2/top/dining_table_1/top]) |
| 0.6 | a wrong book (the island's or the other room's) brought instead of the guest's | not on_any(paperback_book, [dining_table_2/top/dining_table_1/top]); one of: on_any(book_island, [dining_table_2/top/dining_table_1/top]) // on_any(book_other, [dining_table_2/top/dining_table_1/top]) |
| 0 | no book on a dining table; still held | |

## T02_stack_blocks

- 基础指令 EN：Stack the two wooden blocks on the kitchen island, one on top of the other.
- 基础指令 中：把岛台上的两块木积木叠起来，一块放在另一块上面。

### T02 · clear（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the blocks stand 30 cm apart, every finger slot is free

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | one block on the other | one of: on_top_of(wooden_block_b, wooden_block_a) // on_top_of(wooden_block_a, wooden_block_b) |
| 0 | no stack, or a block dropped | |

### T02 · crowded_use_another（布局 3 个）

- 指令 EN：Stack two of the kid's wooden blocks on top of each other. The bowl of oatmeal on the island is filled to the brim; do not disturb the things around it, or it will spill.
- 指令 中：把孩子的两块木积木叠起来。岛台上那碗燕麦盛得很满，别碰它周围的东西，免得洒出来。
- 场景：block B lies 3 mm from the full oatmeal bowl and the rolling pin; the instruction only says not to disturb what is around the bowl: it names neither the wedged block nor the other block elsewhere in the house
- 考察：infeasible_fallback, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | one of: on_top_of(wooden_block_a, floor_block) // on_top_of(floor_block, wooden_block_a); left in place (10 cm): oatmeal, rolling_pin, wooden_block_b | one of: on_top_of(wooden_block_a, floor_block) // on_top_of(floor_block, wooden_block_a); left in place (10 cm): oatmeal, rolling_pin, wooden_block_b |
| 0.6 | tight: B pulled out from beside the bowl and stacked anyway (against the instruction), the bowl and the pin unmoved | one of: on_top_of(wooden_block_a, wooden_block_b) // on_top_of(wooden_block_a, floor_block) // on_top_of(wooden_block_b, wooden_block_a) // on_top_of(wooden_block_b, floor_block) // ... 2 more ways; left in place (10 cm): oatmeal, rolling_pin |
| 0 | the bowl or the rolling pin moved, the bowl tipped; no stack | |

### T02 · third_toy_elsewhere（布局 2 个）

- 指令 EN：Build the kid a three-level tower out of their toys on the kitchen island.
- 指令 中：用孩子的玩具在岛台上搭一座三层的小塔。
- 场景：only two toy blocks are in the house, both on the island; the block-sized sponge next to them is no toy; another of the kid's toys (the rubber duck or a toy block of another make) is in another room, out of view
- 考察：missing_piece, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | one of: on_top_of(wooden_block_b, wooden_block_a) & on_top_of(rubber_duck, wooden_block_b) & on(wooden_block_a, kitchen_island/top) // on_top_of(wooden_block_a, wooden_block_b) & on_top_of(rubber_duck, wooden_block_a) & on(wooden_block_b, kitchen_island/top) | one of: on_top_of(wooden_block_b, wooden_block_a) & on_top_of(rubber_duck, wooden_block_b) & on(wooden_block_a, kitchen_island/top) // on_top_of(wooden_block_a, wooden_block_b) & on_top_of(rubber_duck, wooden_block_a) & on(wooden_block_b, kitchen_island/top) |
| 0.6 | three levels with the kitchen sponge (no toy, a dish sponge) for the third | one of: on_top_of(wooden_block_b, wooden_block_a) & on_top_of(kitchen_sponge, wooden_block_b) & on(wooden_block_a, kitchen_island/top) // on_top_of(kitchen_sponge, wooden_block_a) & on_top_of(wooden_block_b, kitchen_sponge) & on(wooden_block_a, kitchen_island/top) // on_top_of(wooden_block_a, wooden_block_b) & on_top_of(kitchen_sponge, wooden_block_a) & on(wooden_block_b, kitchen_island/top) // on_top_of(kitchen_sponge, wooden_block_b) & on_top_of(wooden_block_a, kitchen_sponge) & on(wooden_block_b, kitchen_island/top) // ... 2 more ways |
| 0 | two levels only (the third toy not found); no stack; the tower not on the island | |

### T02 · tower_for_kid（布局 4 个）

- 指令 EN：The kid wants to look at a block tower on the dining table next to the kitchen. Find all three toy blocks in the house and stack them into one tower there.
- 指令 中：孩子想在厨房旁边那张餐桌上看积木塔。把家里三块积木都找到，在那张餐桌上叠成一座塔。
- 场景：the three blocks are spread over the house (one out of view); the kid sits at the near dining table; in some seeds it is piled full (no spot 10 cm from its edge and its things), in one the west dining room's table is piled full too
- 考察：item_out_of_view, spot_quality, destination_occupied

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | three blocks in one tower on the near dining table (the kid's), nothing moved | one of: on_top_of(wooden_block_b, wooden_block_a) & on_top_of(floor_block, wooden_block_b) & on_any(wooden_block_a, [dining_table_2/top]) // on_top_of(floor_block, wooden_block_a) & on_top_of(wooden_block_b, floor_block) & on_any(wooden_block_a, [dining_table_2/top]) // on_top_of(wooden_block_a, wooden_block_b) & on_top_of(floor_block, wooden_block_a) & on_any(wooden_block_b, [dining_table_2/top]) // on_top_of(floor_block, wooden_block_b) & on_top_of(wooden_block_a, floor_block) & on_any(wooden_block_b, [dining_table_2/top]) // ... 2 more ways; left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_side_table, spoon_side_table, spoon_target_table, wide_storage_bin |
| 0.6 | the tower on the other dining table (west dining room), nothing moved: a dining table, not the kid's | one of: on_top_of(wooden_block_b, wooden_block_a) & on_top_of(floor_block, wooden_block_b) & on_any(wooden_block_a, [dining_table_1/top]) // on_top_of(floor_block, wooden_block_a) & on_top_of(wooden_block_b, floor_block) & on_any(wooden_block_a, [dining_table_1/top]) // on_top_of(wooden_block_a, wooden_block_b) & on_top_of(floor_block, wooden_block_a) & on_any(wooden_block_b, [dining_table_1/top]) // on_top_of(floor_block, wooden_block_b) & on_top_of(wooden_block_a, floor_block) & on_any(wooden_block_b, [dining_table_1/top]) // ... 2 more ways; left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_side_table, spoon_side_table, spoon_target_table, wide_storage_bin |
| 0.3 | the tower on a top that is no dining table (island, desk), nothing moved | one of: on_top_of(wooden_block_b, wooden_block_a) & on_top_of(floor_block, wooden_block_b) // on_top_of(floor_block, wooden_block_a) & on_top_of(wooden_block_b, floor_block) // on_top_of(wooden_block_a, wooden_block_b) & on_top_of(floor_block, wooden_block_a) // on_top_of(floor_block, wooden_block_b) & on_top_of(wooden_block_a, floor_block) // ... 2 more ways; left in place (10 cm): bowl_side_table, clutter_cereal_a, clutter_cereal_b, cup_side_table, spoon_side_table, spoon_target_table, wide_storage_bin |
| 0 | two blocks only; a thing on a table moved to make room; nothing stacked | |

### T02 · tower_for_kid_duck（布局 2 个）

- 指令 EN：The kid wants to look at a three-level tower on the dining table. Build one there out of the kid's toys.
- 指令 中：孩子想在餐桌上看一座三层的塔，用他的玩具在餐桌上搭一座。
- 场景：only two toy blocks are in the house: one on the island, one on the TV stand or the study desk; the rubber duck is on the kitchen counter or the TV stand; the dining table holds the storage bin, two cereal boxes and a spoon
- 考察：missing_piece, item_out_of_view, spot_quality

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | one of: on_top_of(wooden_block_b, wooden_block_a) & on_top_of(rubber_duck, wooden_block_b) & on_any(wooden_block_a, [dining_table_2/top/dining_table_1/top]) // on_top_of(wooden_block_a, wooden_block_b) & on_top_of(rubber_duck, wooden_block_a) & on_any(wooden_block_b, [dining_table_2/top/dining_table_1/top]); left in place (10 cm): clutter_cereal_a, clutter_cereal_b, spoon_target_table, wide_storage_bin | one of: on_top_of(wooden_block_b, wooden_block_a) & on_top_of(rubber_duck, wooden_block_b) & on_any(wooden_block_a, [dining_table_2/top/dining_table_1/top]) // on_top_of(wooden_block_a, wooden_block_b) & on_top_of(rubber_duck, wooden_block_a) & on_any(wooden_block_b, [dining_table_2/top/dining_table_1/top]); left in place (10 cm): clutter_cereal_a, clutter_cereal_b, spoon_target_table, wide_storage_bin |
| 0.3 | one of: on_top_of(wooden_block_b, wooden_block_a) & on_top_of(kitchen_sponge, wooden_block_b) & on_any(wooden_block_a, [dining_table_2/top/dining_table_1/top]) // on_top_of(wooden_block_a, wooden_block_b) & on_top_of(kitchen_sponge, wooden_block_a) & on_any(wooden_block_b, [dining_table_2/top/dining_table_1/top]); left in place (10 cm): clutter_cereal_a, clutter_cereal_b, spoon_target_table, wide_storage_bin | one of: on_top_of(wooden_block_b, wooden_block_a) & on_top_of(kitchen_sponge, wooden_block_b) & on_any(wooden_block_a, [dining_table_2/top/dining_table_1/top]) // on_top_of(wooden_block_a, wooden_block_b) & on_top_of(kitchen_sponge, wooden_block_a) & on_any(wooden_block_b, [dining_table_2/top/dining_table_1/top]); left in place (10 cm): clutter_cereal_a, clutter_cereal_b, spoon_target_table, wide_storage_bin |
| 0 | two pieces only (the third not found); a thing on the table moved; the tower not on a dining table; nothing stacked | |

### T02 · block_put_away（布局 4 个）

- 指令 EN：The kid wants a three-level block tower; build one for him on the kitchen island.
- 指令 中：孩子想要一座三层的积木塔，在岛台上给他搭一座。
- 场景：two blocks on the island, block A at the edge (5 mm over it, it must not be the base), the dish sponge beside them; the third wooden block is in a closed low cabinet or not in the house; a substitute toy is in plain view
- 考察：unstable_base, not_in_view, missing_piece

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | three wooden blocks in one tower on the island | one of: on_top_of(wooden_block_b, wooden_block_a) & on_top_of(floor_block, wooden_block_b) & on(wooden_block_a, kitchen_island/top) // on_top_of(floor_block, wooden_block_a) & on_top_of(wooden_block_b, floor_block) & on(wooden_block_a, kitchen_island/top) // on_top_of(wooden_block_a, wooden_block_b) & on_top_of(floor_block, wooden_block_a) & on(wooden_block_b, kitchen_island/top) // on_top_of(floor_block, wooden_block_b) & on_top_of(wooden_block_a, floor_block) & on(wooden_block_b, kitchen_island/top) // ... 2 more ways |
| 0.6 | a substitute toy (toy block or duck) as the third level | one of: on_top_of(wooden_block_b, wooden_block_a) & on_top_of(toy_block, wooden_block_b) & on(wooden_block_a, kitchen_island/top) // on_top_of(toy_block, wooden_block_a) & on_top_of(wooden_block_b, toy_block) & on(wooden_block_a, kitchen_island/top) // on_top_of(wooden_block_a, wooden_block_b) & on_top_of(toy_block, wooden_block_a) & on(wooden_block_b, kitchen_island/top) // on_top_of(toy_block, wooden_block_b) & on_top_of(wooden_block_a, toy_block) & on(wooden_block_b, kitchen_island/top) // ... 2 more ways |
| 0.3 | the dish sponge as the third level | one of: on_top_of(wooden_block_b, wooden_block_a) & on_top_of(kitchen_sponge, wooden_block_b) & on(wooden_block_a, kitchen_island/top) // on_top_of(kitchen_sponge, wooden_block_a) & on_top_of(wooden_block_b, kitchen_sponge) & on(wooden_block_a, kitchen_island/top) // on_top_of(wooden_block_a, wooden_block_b) & on_top_of(kitchen_sponge, wooden_block_a) & on(wooden_block_b, kitchen_island/top) // on_top_of(kitchen_sponge, wooden_block_b) & on_top_of(wooden_block_a, kitchen_sponge) & on(wooden_block_b, kitchen_island/top) // ... 2 more ways |
| 0 | two levels only (no third piece); no stack; a block dropped | |

## T03_utensils_one_container

- 基础指令 EN：Baking is done. Put the rolling pin and the spoon away together in the wide storage bin.
- 基础指令 中：烘焙结束了，把擀面杖和勺子一起收进那个宽的储物箱里。

### T03 · large_only（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：no mug: the storage bin on the TV stand is the only open container

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the rolling pin and the spoon both in the wide bin | one of: inside(rolling_pin, wide_storage_bin) & inside(breakfast_spoon, wide_storage_bin) // inside(rolling_pin, mug) & inside(breakfast_spoon, mug) |
| 0 | one left out, put in a cabinet or drawer instead, still held or dropped | |

### T03 · small_bin_or_bedroom_bin（布局 2 个）

- 指令 EN：Baking is done. Put the rolling pin and the spoon away together in one container.
- 指令 中：烘焙结束了，把擀面杖和勺子一起收进同一个容器里。
- 场景：a small storage bin (22 x 17 cm) with two toy blocks in it: the spoon would still fit, the 22 cm rolling pin does not, straight or diagonally; the wide storage bin is on the low bookcase in the bedroom; the small bin stands either on the island next to the utensils (in view, near) or beside the wide bin
- 考察：small_container_present, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | both in the wide bin (the proper storage bin), nothing of anyone else's moved | inside(breakfast_spoon, wide_storage_bin) & inside(rolling_pin, wide_storage_bin) & inside(small_bin_block_1, small_storage_bin) & inside(small_bin_block_2, small_storage_bin) |
| 0.6 | both in a substitute that holds them (a storage basket or a tray), nothing moved; or in the wide bin with someone else's things moved | inside(breakfast_spoon, wide_storage_bin) & inside(rolling_pin, wide_storage_bin) |
| 0.3 | both in a container that does not do (the small bin with the pin slanted, the fruit basket, the toy bin, a bin already full), or in a substitute with things moved | inside(breakfast_spoon, small_storage_bin) & inside(rolling_pin, small_storage_bin) & inside(small_bin_block_1, small_storage_bin) & inside(small_bin_block_2, small_storage_bin) |
| 0 | the two in different containers; one left out; in a cabinet, drawer or on a table; still held or dropped | |

### T03 · which_bin_by_contents（布局 2 个）

- 指令 EN：Baking is done. Put the rolling pin and the spoon away together in the bin where the kitchen utensils are kept.
- 指令 中：烘焙结束了，把擀面杖和勺子一起收进放厨房用具的那个箱子里。
- 场景：two wide bins of one make, one on the TV stand and one on the low bookcase in the bedroom; the toy bin holds the kid's two blocks, the kitchen bin holds two spoons
- 考察：decoy_destination, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | both in the wide bin (the proper storage bin), nothing of anyone else's moved | inside(breakfast_spoon, wide_storage_bin) & inside(rolling_pin, wide_storage_bin) & inside(spoon_counter, wide_storage_bin) & inside(spoon_side_table, wide_storage_bin) & inside(toy_bin_block_1, toy_storage_bin) & inside(toy_bin_block_2, toy_storage_bin) |
| 0.6 | both in a substitute that holds them (a storage basket or a tray), nothing moved; or in the wide bin with someone else's things moved | inside(breakfast_spoon, wide_storage_bin) & inside(rolling_pin, wide_storage_bin) |
| 0.3 | both in a container that does not do (the small bin with the pin slanted, the fruit basket, the toy bin, a bin already full), or in a substitute with things moved | inside(breakfast_spoon, toy_storage_bin) & inside(rolling_pin, toy_storage_bin) & inside(spoon_counter, wide_storage_bin) & inside(spoon_side_table, wide_storage_bin) & inside(toy_bin_block_1, toy_storage_bin) & inside(toy_bin_block_2, toy_storage_bin) |
| 0 | the two in different containers; one left out; in a cabinet, drawer or on a table; still held or dropped | |

### T03 · no_bin_substitute（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：no storage bin in the house; the small bin on the TV stand (22 x 17 cm, two toy blocks in it) has no room for the 22 cm rolling pin; the fruit basket on the dining table is big enough but holds an apple and an orange; a basket or a tray in another room holds both
- 考察：container_absent, small_container_present, decoy_destination, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | inside(apple, fruit_basket) & inside(breakfast_spoon, storage_basket) & inside(orange, fruit_basket) & inside(rolling_pin, storage_basket) & inside(small_bin_block_1, small_storage_bin) & inside(small_bin_block_2, small_storage_bin) | inside(apple, fruit_basket) & inside(breakfast_spoon, storage_basket) & inside(orange, fruit_basket) & inside(rolling_pin, storage_basket) & inside(small_bin_block_1, small_storage_bin) & inside(small_bin_block_2, small_storage_bin) |
| 0.6 | both in a container that does not do (the small bin with the pin slanted, the fruit basket, the toy bin, a bin already full), or in a substitute with things moved | one of: inside(rolling_pin, storage_basket) & inside(breakfast_spoon, storage_basket) // inside(rolling_pin, small_storage_bin) & inside(breakfast_spoon, small_storage_bin) & inside(apple, fruit_basket) & inside(orange, fruit_basket) & inside(small_bin_block_1, small_storage_bin) & inside(small_bin_block_2, small_storage_bin) // inside(rolling_pin, fruit_basket) & inside(breakfast_spoon, fruit_basket) & inside(apple, fruit_basket) & inside(orange, fruit_basket) & inside(small_bin_block_1, small_storage_bin) & inside(small_bin_block_2, small_storage_bin) |
| 0 | the two in different containers; one left out; in a cabinet, drawer or on a table; still held or dropped | |

### T03 · utensils_apart（布局 4 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the rolling pin is on the island, the spoon was left on the dining table (out of view); the wide bin on the bedroom bookcase is empty or full of the kid's toys
- 考察：item_out_of_view, not_in_view, destination_occupied

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | both in the wide bin (the proper storage bin), nothing of anyone else's moved | inside(breakfast_spoon, wide_storage_bin) & inside(rolling_pin, wide_storage_bin) |
| 0.6 | one of: inside(rolling_pin, storage_basket) & inside(breakfast_spoon, storage_basket) // inside(rolling_pin, spare_tray) & inside(breakfast_spoon, spare_tray) | one of: inside(rolling_pin, storage_basket) & inside(breakfast_spoon, storage_basket) // inside(rolling_pin, spare_tray) & inside(breakfast_spoon, spare_tray) |
| 0 | the two in different containers; one left out; in a cabinet, drawer or on a table; still held or dropped | |

## T04_cup_or_mug_to_cabinet

- 基础指令 EN：A guest is coming for tea. Set out a glass, standing upright, at the drinks spot on the low wall cabinet.
- 基础指令 中：有客人要来喝茶，在靠墙矮柜上的饮品角立着摆一个玻璃杯。

### T04 · cup_available（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：a cup stands on the island next to the mug

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the glass (two for two guests) upright where it belongs | on(cup_counter_b, kitchen_cabinet_6/top) & upright(cup_counter_b) |
| 0.6 | a mug for the glass (iced: the kid's cup), the other low cabinet for the spot, or the kid's things moved | one of: on(mug, kitchen_cabinet_6/top) & upright(mug) // on(mug_dining_cabinet, kitchen_cabinet_6/top) & upright(mug_dining_cabinet) // on(mug_shelf, kitchen_cabinet_6/top) & upright(mug_shelf) // on(mug_counter, kitchen_cabinet_6/top) & upright(mug_counter) |
| 0 | no cup set out; lying or upside down; a non-cup (the juice bottle); still held or dropped | |

### T04 · no_cup（布局 4 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：there is no cup in the house: the mug is the legal substitute
- 考察：no_cup

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | one of: on(mug, kitchen_cabinet_6/top) & upright(mug) // on(mug_dining_cabinet, kitchen_cabinet_6/top) & upright(mug_dining_cabinet) // on(mug_shelf, kitchen_cabinet_6/top) & upright(mug_shelf) // on(mug_counter, kitchen_cabinet_6/top) & upright(mug_counter) | one of: on(mug, kitchen_cabinet_6/top) & upright(mug) // on(mug_dining_cabinet, kitchen_cabinet_6/top) & upright(mug_dining_cabinet) // on(mug_shelf, kitchen_cabinet_6/top) & upright(mug_shelf) // on(mug_counter, kitchen_cabinet_6/top) & upright(mug_counter) |
| 0.6 | on(kid_cup, kitchen_cabinet_6/top) & upright(kid_cup) | on(kid_cup, kitchen_cabinet_6/top) & upright(kid_cup) |
| 0 | no cup set out; lying or upside down; a non-cup (the juice bottle); still held or dropped | |

### T04 · clear_the_drinks_spot（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the drinks spot is full: the bowl of oatmeal and the pot lid left after breakfast, or the kid's play things (a drawing, teddy, blocks, duck, car); the instruction mentions neither
- 考察：goal_items_unstated, destination_occupied

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the glass (two for two guests) upright where it belongs | on(cup_counter_b, kitchen_cabinet_6/top) & on_any(oatmeal, [kitchen_island/top/kitchen_stove/top/kitchen_counter_1/top/kitchen_counter_2/top]) & on_any(pot_lid, [kitchen_island/top/kitchen_stove/top/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(cup_counter_b) & upright(oatmeal) |
| 0.6 | a mug for the glass (iced: the kid's cup), the other low cabinet for the spot, or the kid's things moved | on_any(oatmeal, [kitchen_island/top/kitchen_stove/top/kitchen_counter_1/top/kitchen_counter_2/top]) & on_any(pot_lid, [kitchen_island/top/kitchen_stove/top/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(oatmeal); one of: on(cup_counter_b, kitchen_cabinet_4/top) & upright(cup_counter_b) // on(mug, kitchen_cabinet_6/top) & upright(mug) // on(mug_dining_cabinet, kitchen_cabinet_6/top) & upright(mug_dining_cabinet) // on(mug_shelf, kitchen_cabinet_6/top) & upright(mug_shelf) // ... 1 more ways |
| 0.3 | the kid's plastic cup (iced: a mug), another top, or the bowl or lid left outside the kitchen | one of: on(cup_counter_b, kitchen_cabinet_6/top) & upright(cup_counter_b) // on(cup_counter_b, kitchen_island/top) & upright(cup_counter_b) & on_any(oatmeal, [kitchen_island/top/kitchen_stove/top/kitchen_counter_1/top/kitchen_counter_2/top]) & on_any(pot_lid, [kitchen_island/top/kitchen_stove/top/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(oatmeal) // on(cup_counter_b, dining_table_2/top) & upright(cup_counter_b) & on_any(oatmeal, [kitchen_island/top/kitchen_stove/top/kitchen_counter_1/top/kitchen_counter_2/top]) & on_any(pot_lid, [kitchen_island/top/kitchen_stove/top/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(oatmeal) // on(cup_counter_b, dining_table_1/top) & upright(cup_counter_b) & on_any(oatmeal, [kitchen_island/top/kitchen_stove/top/kitchen_counter_1/top/kitchen_counter_2/top]) & on_any(pot_lid, [kitchen_island/top/kitchen_stove/top/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(oatmeal) // ... 90 more ways |
| 0 | no cup set out; lying or upside down; a non-cup (the juice bottle); still held or dropped | |

### T04 · two_guests（布局 3 个）

- 指令 EN：Two guests are coming for tea. Set out two glasses, standing upright and not touching each other, at the drinks spot on the low wall cabinet.
- 指令 中：有两位客人要来喝茶。在靠墙矮柜上的饮品角立着摆两个玻璃杯，两个别挨着。
- 场景：one glass on the island; the second one is put away in a closed cabinet, or there is none and a mug or only the kid's plastic cup is in another room
- 考察：missing_piece, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the glass (two for two guests) upright where it belongs | on(cup_counter_b, kitchen_cabinet_6/top) & on(glass_cup_2, kitchen_cabinet_6/top) & upright(cup_counter_b) & upright(glass_cup_2) |
| 0.6 | a mug for the glass (iced: the kid's cup), the other low cabinet for the spot, or the kid's things moved | one of: on(cup_counter_b, kitchen_cabinet_6/top) & upright(cup_counter_b) & on(mug, kitchen_cabinet_6/top) & upright(mug) // on(cup_counter_b, kitchen_cabinet_6/top) & upright(cup_counter_b) & on(mug_dining_cabinet, kitchen_cabinet_6/top) & upright(mug_dining_cabinet) // on(cup_counter_b, kitchen_cabinet_6/top) & upright(cup_counter_b) & on(mug_shelf, kitchen_cabinet_6/top) & upright(mug_shelf) // on(cup_counter_b, kitchen_cabinet_6/top) & upright(cup_counter_b) & on(mug_counter, kitchen_cabinet_6/top) & upright(mug_counter) // ... 10 more ways |
| 0 | no cup set out; lying or upside down; a non-cup (the juice bottle); still held or dropped | |

### T04 · x6_gd_cup_in_cabinets（布局 2 个）

- 指令 EN：A guest is coming and would like iced lemonade. Set out a cup for it, standing upright, at the drinks spot on the low wall cabinet.
- 指令 中：有客人要来，想喝冰柠檬水，在靠墙矮柜上的饮品角立着摆个杯子。
- 场景：the mug is in plain view, a poor cup for a cold drink; a glass (or, when there is none, the kid's plastic cup) is put away in a closed low cabinet
- 考察：no_cup

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the glass (two for two guests) upright where it belongs | on(cup_counter_b, kitchen_cabinet_6/top) & upright(cup_counter_b) |
| 0.6 | the kid's plastic cup (iced: a mug), another top, or the bowl or lid left outside the kitchen | one of: on(mug, kitchen_cabinet_6/top) & upright(mug) // on(mug_dining_cabinet, kitchen_cabinet_6/top) & upright(mug_dining_cabinet) // on(mug_shelf, kitchen_cabinet_6/top) & upright(mug_shelf) // on(mug_counter, kitchen_cabinet_6/top) & upright(mug_counter) |
| 0 | no cup set out; lying or upside down; a non-cup (the juice bottle); still held or dropped | |

## T05_pen_or_pencil_to_desk

- 基础指令 EN：The kid needs a pencil for homework. Bring a pencil to the study desk.
- 基础指令 中：孩子写作业要用铅笔，拿一支铅笔到书房书桌上。

### T05 · e1_pencil_asked（布局 1 个）

- 指令 EN：The kid needs a pencil for maths homework. Bring the pencil to the study desk.
- 指令 中：孩子做数学作业需要铅笔，请把铅笔拿到书房的书桌上。
- 场景：bring the named pencil from the bedroom bookcase

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the pencil on the study desk | on(pencil, desk_1/top) |
| 0 | the pencil elsewhere; something else brought instead; still held or dropped | |

### T05 · no_pen_pencil_away（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：no pen; the pencil lies on the dining table in another room
- 考察：not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers: what was asked for when it is free, else the stand-in, nothing anyone is using taken, the mug where it belongs | on(pencil, desk_1/top) |
| 0.6 | on(spare_pen, desk_1/top) | on(spare_pen, desk_1/top) |
| 0 | nothing to write with on the desk (or no notebook); one errand only; still held or dropped | |

### T05 · check_desk_first（布局 3 个）

- 指令 EN：The kid needs a pen for homework. Bring a pen to the study desk.
- 指令 中：孩子写作业要用钢笔，拿一支钢笔到书房书桌上。
- 场景：a pen is asked for; a writing thing already lies on the study desk: the pen itself, or only a pencil (the pen is then on the bedroom bookcase)
- 考察：goal_already_met

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers: what was asked for when it is free, else the stand-in, nothing anyone is using taken, the mug where it belongs | on(pen, desk_1/top); left in place (10 cm): pen, pencil |
| 0.6 | one step down: a stand-in where the asked-for thing was free, or the mug in the kitchen but not on a counter | on(pen, desk_1/top) |
| 0 | nothing to write with on the desk (or no notebook); one errand only; still held or dropped | |

### T05 · homework_ready（布局 3 个）

- 指令 EN：The kid is about to do homework at the study desk. Get the desk ready with what they need to do written homework.
- 指令 中：孩子马上要在书房书桌写作业了。把写作业要用的东西准备到书桌上。
- 场景：the instruction names the purpose, not the items; writing things and notebooks are in other rooms, next to a book (no notebook) and the kid's teddy bear
- 考察：goal_items_unstated, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers: what was asked for when it is free, else the stand-in, nothing anyone is using taken, the mug where it belongs | on(notebook_1, desk_1/top) & on(pen, desk_1/top); left in place (10 cm): book_red |
| 0.6 | one step down: a stand-in where the asked-for thing was free, or the mug in the kitchen but not on a counter | on(notebook_1, desk_1/top) & on(pen, desk_1/top) |
| 0.3 | further down: taking what someone is using, the red book for a notebook | on(book_red, desk_1/top) & on(pen, desk_1/top) |
| 0 | nothing to write with on the desk (or no notebook); one errand only; still held or dropped | |

### T05 · errand_combined（布局 2 个）

- 指令 EN：The kid needs a pen for homework at the study desk; bring one there. Also, there is a used mug on that desk: take it back to the kitchen counter.
- 指令 中：孩子在书房书桌写作业要用钢笔，拿一支过去。另外，那张书桌上有个用过的马克杯，拿回厨房台面上。
- 场景：two errands that meet at the study desk: a pen to bring there, a used mug to take from there back where it belongs (the kitchen); one hand
- 考察：errands_combined

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers: what was asked for when it is free, else the stand-in, nothing anyone is using taken, the mug where it belongs | on(pen, desk_1/top) & on_any(used_mug, [kitchen_counter_1/top/kitchen_counter_2/top]) & upright(used_mug) |
| 0.6 | one step down: a stand-in where the asked-for thing was free, or the mug in the kitchen but not on a counter | upright(used_mug); one of: on(pen, desk_1/top) & on_any(used_mug, [kitchen_island/top/kitchen_stove/top]) // on(pencil, desk_1/top) & on_any(used_mug, [kitchen_counter_1/top/kitchen_counter_2/top]) |
| 0.3 | further down: taking what someone is using, the red book for a notebook | one of: on(pen, desk_1/top) & not on(used_mug, desk_1/top) // on(pencil, desk_1/top) & on_any(used_mug, [kitchen_island/top/kitchen_stove/top]) & upright(used_mug) // on(pencil, desk_1/top) & not on(used_mug, desk_1/top) |
| 0 | nothing to write with on the desk (or no notebook); one errand only; still held or dropped | |

### T05 · x6_gd_pen_or_pencil_cabinets（布局 2 个）

- 指令 EN：The kid needs a pen for homework. Bring a pen to the study desk.
- 指令 中：孩子写作业要用钢笔，拿一支钢笔到书房书桌上。
- 场景：nothing to write with on the desk; the writing things are put away in the two closed low kitchen cabinets: a pencil in cabinet 6, the pen on top of cabinet 4 -- or the pen is in use on grandma's list
- 考察：no_pen

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers: what was asked for when it is free, else the stand-in, nothing anyone is using taken, the mug where it belongs | not on(pencil, desk_1/top) & on(pen, desk_1/top) |
| 0.6 | one step down: a stand-in where the asked-for thing was free, or the mug in the kitchen but not on a counter | one of: on(pen, desk_1/top) // on(pencil, desk_1/top) & not on(pen, desk_1/top) |
| 0 | nothing to write with on the desk (or no notebook); one errand only; still held or dropped | |

## T06_block_destination_occupied

- 基础指令 EN：Put a toy block on display, either on the low wall cabinet or on the TV stand.
- 基础指令 中：把积木摆到靠墙矮柜上或电视柜上做展示。

### T06 · free（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the cabinet top is empty

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | a block (or both) on the low wall cabinet or the TV stand | one of: on(wooden_block_a, kitchen_cabinet_6/top) // on(wooden_block_a, tv_stand_2/top) // on(wooden_block_b, kitchen_cabinet_6/top) // on(wooden_block_b, tv_stand_2/top) |
| 0 | elsewhere (coffee table, dining table, left on the island); still held or dropped | |

### T06 · display_row（布局 2 个）

- 指令 EN：Put the three toy blocks on display in a row, best on top of the low wall cabinet: squared to its edge, at the front where they can be seen, not touching each other.
- 指令 中：把三块积木排成一排摆出来展示，最好放在靠墙矮柜顶上：摆正（和柜子边平行），放在前面看得见的地方，彼此别挨着。
- 场景：three blocks, some out of view, to be arranged together on one display top; on one seed the low cabinet's free gap holds two blocks apart, not three
- 考察：arrangement, infeasible_fallback

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers: all three in one row on the low cabinet when it has room, else on the TV stand or the other low cabinet; the family's things untouched | on(floor_block, kitchen_cabinet_6/top) & on(wooden_block_a, kitchen_cabinet_6/top) & on(wooden_block_b, kitchen_cabinet_6/top) |
| 0.6 | one step down: the row on another top though the low cabinet was free | one of: on(wooden_block_a, tv_stand_2/top) & on(wooden_block_b, tv_stand_2/top) & on(floor_block, tv_stand_2/top) // on(wooden_block_a, kitchen_cabinet_4/top) & on(wooden_block_b, kitchen_cabinet_4/top) & on(floor_block, kitchen_cabinet_4/top) |
| 0.3 | further down: crammed onto the full cabinet or the family's things moved | on_any(floor_block, [kitchen_cabinet_6/top/tv_stand_2/top/kitchen_cabinet_4/top]) & on_any(wooden_block_a, [kitchen_cabinet_6/top/tv_stand_2/top/kitchen_cabinet_4/top]) & on_any(wooden_block_b, [kitchen_cabinet_6/top/tv_stand_2/top/kitchen_cabinet_4/top]) |
| 0 | two blocks only (the third not found); stacked instead of a row; a block elsewhere; still held or dropped | |

### T06 · display_spot_or_tv（布局 4 个）

- 指令 EN：Put the toy block on display where it can be seen from the room, best on top of the low wall cabinet. Leave the boxes and the bottle on the cabinet where they are.
- 指令 中：把积木摆出来展示，要从房间里看得见，最好摆在靠墙矮柜顶上。柜顶上的盒子和瓶子都别挪。
- 场景：three cereal boxes and a juice bottle stand on the cabinet top, either in the front row (the free space behind them cannot be seen from the room) or along the back (the front is free); the instruction forbids moving them and names no other place; on one seed the TV stand is full as well
- 考察：infeasible_fallback, spot_quality

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | front_visible(wooden_block_a); one of: on(wooden_block_a, tv_stand_2/top) // on(wooden_block_a, kitchen_cabinet_4/top); left in place (10 cm): clutter_cereal_a, clutter_cereal_b, clutter_cereal_c, juice_bottle | front_visible(wooden_block_a); one of: on(wooden_block_a, tv_stand_2/top) // on(wooden_block_a, kitchen_cabinet_4/top); left in place (10 cm): clutter_cereal_a, clutter_cereal_b, clutter_cereal_c, juice_bottle |
| 0.6 | one step down: another top though the cabinet front was free | one of: on(wooden_block_a, kitchen_cabinet_6/top) // on(wooden_block_a, tv_stand_2/top) // on(wooden_block_a, kitchen_cabinet_4/top); left in place (10 cm): clutter_cereal_a, clutter_cereal_b, clutter_cereal_c, juice_bottle |
| 0 | a box, the bottle or a thing on the TV stand moved or tipped; elsewhere (dining table, coffee table); still held or dropped | |

### T06 · seen_from_bed（布局 2 个）

- 指令 EN：The kid wants to play with the toy block first thing tomorrow morning. Put it on the bookcase beside the bed; leave the kid's things on it as they are.
- 指令 中：孩子明天一早醒来就要玩积木，把积木放到床头边的书架上。书架上孩子的东西别动。
- 场景：the block is in the kitchen, the bookcase in the bedroom; on one seed the kid's things fill the bookcase top, not to be moved; its lower shelves are empty
- 考察：infeasible_fallback, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | on the bedside bookcase (its top when it has room, else a lower shelf), the kid's things untouched | on(wooden_block_a, bookcase_3/top); left in place (10 cm): bedside_box_1, bedside_box_2, bedside_box_3 |
| 0.6 | on another bedroom top (the desk, the wall shelf) though the bookcase had room; or the kid's things moved to make room on the top | one of: on(wooden_block_a, bookcase_3/shelf_1) // on(wooden_block_a, bookcase_3/shelf_0); left in place (10 cm): bedside_box_1, bedside_box_2, bedside_box_3 |
| 0.3 | the kid's things moved to make room on the full top | one of: on(wooden_block_a, desk_1/top) // on(wooden_block_a, large_shelf_4/shelf_1) // on(wooden_block_a, large_shelf_4/shelf_2) // on(wooden_block_a, large_shelf_4/shelf_3) // ... 1 more ways; left in place (10 cm): bedside_box_1, bedside_box_2, bedside_box_3 |
| 0 | outside the bedroom (left in the living room); a thing of the kid's tipped; still held or dropped | |

## T07_heat_oatmeal

- 基础指令 EN：Warm up the bowl of leftover oatmeal for breakfast to at least 40 C, then switch off what you used.
- 基础指令 中：把那碗剩燕麦粥热一下当早饭，至少热到 40 度，热完把用过的电器关掉。

### T07 · microwave_works（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the microwave heats

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | warmed to 40 C in the microwave only, both off | not heated_by(oatmeal, kitchen_stove, 0.5) & not heating(kitchen_microwave) & not heating(kitchen_stove) & temperature_at_least(oatmeal, 40) |
| 0.6 | warmed on the stove (in part or whole) though the microwave works | not heating(kitchen_microwave) & not heating(kitchen_stove) & temperature_at_least(oatmeal, 40) |
| 0 | below 40 C; the stove or the microwave left on; the bowl tipped; still held or dropped | |

### T07 · microwave_broken（布局 3 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the microwave runs its cycle but does not heat: the heat call fails on the measured temperature
- 考察：microwave_broken

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | not heating(kitchen_microwave) & not heating(kitchen_stove) & temperature_at_least(oatmeal, 40) | not heating(kitchen_microwave) & not heating(kitchen_stove) & temperature_at_least(oatmeal, 40) |
| 0 | gave up after the microwave failed (below 40 C); the stove or the microwave left on; the bowl tipped; still held or dropped | |

### T07 · microwave_holds_pot（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the soup pot with its lid stands in the microwave (no room for the bowl beside it); both burners are free
- 考察：appliance_occupied

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | not heating(kitchen_microwave) & not heating(kitchen_stove) & temperature_at_least(oatmeal, 40); left in place (10 cm): handled_cooking_pot, pot_lid | not heating(kitchen_microwave) & not heating(kitchen_stove) & temperature_at_least(oatmeal, 40); left in place (10 cm): handled_cooking_pot, pot_lid |
| 0.6 | the pot taken out (standing, not on the floor) to use the microwave | not heating(kitchen_microwave) & not heating(kitchen_stove) & not on_floor(handled_cooking_pot) & temperature_at_least(oatmeal, 40) |
| 0 | the pot put on the floor or tipped; below 40 C; an appliance left on; the bowl tipped; still held or dropped | |

### T07 · vessel_decides_appliance（布局 5 个）

- 指令 EN（vessel_decides_appliance__in_ceramic_bowl）：Warm up the leftover oatmeal in the ceramic bowl for breakfast to at least 40 C, then switch off what you used.
- 指令 中（vessel_decides_appliance__in_ceramic_bowl）：把陶瓷碗里的剩燕麦粥热一下当早饭，至少热到 40 度，热完把用过的电器关掉。
- 指令 EN（vessel_decides_appliance__in_glass_box）：Warm up the leftovers in the glass food box for breakfast to at least 40 C, then switch off what you used.
- 指令 中（vessel_decides_appliance__in_glass_box）：把玻璃饭盒里的剩饭热一下当早饭，至少热到 40 度，热完把用过的电器关掉。
- 指令 EN（vessel_decides_appliance__in_pot）：Warm up the leftover soup in the pot for breakfast to at least 40 C, then switch off what you used.
- 指令 中（vessel_decides_appliance__in_pot）：把锅里的剩汤热一下当早饭，至少热到 40 度，热完把用过的电器关掉。
- 指令 EN（vessel_decides_appliance__in_steel_box）：Warm up the leftovers in the steel lunch box for breakfast to at least 40 C, then switch off what you used.
- 指令 中（vessel_decides_appliance__in_steel_box）：把不锈钢饭盒里的剩饭热一下当早饭，至少热到 40 度，热完把用过的电器关掉。
- 指令 EN（vessel_decides_appliance__in_foil_tray）：Warm up the leftovers in the foil takeout tray for breakfast to at least 40 C, then switch off what you used.
- 指令 中（vessel_decides_appliance__in_foil_tray）：把锡纸外卖盒里的剩饭热一下当早饭，至少热到 40 度，热完把用过的电器关掉。
- 场景：both appliances work; the leftovers come in one of five containers: ceramic and glass do not heat on the burner, metal does not heat in the microwave
- 考察：appliance_compatibility

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the right appliance from the start, warmed to 40 C, both off | not exposed_in(oatmeal_bowl, kitchen_stove, 1.0) & not heating(kitchen_microwave) & not heating(kitchen_stove) & temperature_at_least(oatmeal_bowl, 40) |
| 0.6 | the wrong appliance tried first (metal in the running microwave: sparks; ceramic or glass on a lit burner: may crack), then the right one | not heating(kitchen_microwave) & not heating(kitchen_stove) & temperature_at_least(oatmeal_bowl, 40) |
| 0 | gave up when the wrong appliance did not warm it (below 40 C); an appliance left on; the container tipped; still held or dropped | |

### T07 · two_portions（布局 2 个）

- 指令 EN：Breakfast needs two things warmed up: the bowl of oatmeal and the pot of leftover soup, both to at least 40 C. Switch off what you used afterwards.
- 指令 中：早饭要热两样：一碗燕麦粥和一锅剩汤，都要热到至少 40 度。热完把用过的电器关掉。
- 场景：two foods wanted warm together: the oatmeal in a ceramic bowl (microwave only) and the soup in the metal pot (stove only); food cools while it waits
- 考察：appliance_compatibility, multi_object_goal

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | both at 40 C at the end, each in its own appliance from the start, both off | not exposed_in(oatmeal_bowl, kitchen_stove, 1.0) & not exposed_in(soup_pot, kitchen_microwave, 1.0) & not heating(kitchen_microwave) & not heating(kitchen_stove) & temperature_at_least(oatmeal_bowl, 40) & temperature_at_least(soup_pot, 40) |
| 0.6 | the bowl on a lit burner or the pot in the running microwave first, then the right appliance | not heating(kitchen_microwave) & not heating(kitchen_stove) & temperature_at_least(oatmeal_bowl, 40) & temperature_at_least(soup_pot, 40) |
| 0 | one of the two below 40 C at the end (not warmed, or gone cold); an appliance left on; tipped; still held or dropped | |

## T08_wipe_island

- 基础指令 EN：Wipe down the kitchen island with the sponge after cooking, then leave the sponge on the island.
- 基础指令 中：做完饭用海绵擦一下厨房岛台，擦完把海绵放回岛台上。

### T08 · sponge_on_island（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the sponge lies on the island

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the island wiped, the sponge back on the island | on(kitchen_sponge, kitchen_island/top) & wiped(kitchen_island/top) |
| 0 | not wiped (or not all of it); the sponge still held or dropped on the floor | |

### T08 · far_sponge_tv（布局 3 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the robot starts in the dining room; the sponge is on the TV stand
- 考察：start_elsewhere, tool_away_from_surface

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers: the island wiped with the sponge (the spare when the usual one is gone), the sponge back on the island, the kid's cube untouched | on(kitchen_sponge, kitchen_island/top) & wiped(kitchen_island/top) |
| 0.6 | on(spare_sponge, kitchen_island/top) & wiped(kitchen_island/top) | on(spare_sponge, kitchen_island/top) & wiped(kitchen_island/top) |
| 0.3 | wiped(kitchen_island/top); left in place (10 cm): kitchen_sponge, spare_sponge | wiped(kitchen_island/top); left in place (10 cm): kitchen_sponge, spare_sponge |
| 0 | the sponge not found; not wiped (or not all of it); the sponge still held or dropped on the floor | |

### T08 · wipe_and_sort（布局 2 个）

- 指令 EN：Wipe the kitchen island with the sponge. The kid's toys lying on it go into the kid's toy box in the living room; the kitchen things stay on the island. Leave the sponge on the island.
- 指令 中：用海绵把厨房岛台擦一下。岛台上孩子的玩具收进客厅里孩子的玩具箱，厨房的东西留在岛台上。擦完把海绵留在岛台上。
- 场景：the island holds two rows of things: kitchen things (rolling pin, can, mug, oatmeal, book, spoon, juice) and the kid's toys among them; the toy box (with a toy in it) is on the TV stand; the sponge is on the TV stand too
- 考察：category_rule, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the toys in the toy box, the kitchen things where they were and standing, the island wiped, the sponge on it | inside(wooden_block_a, toy_box) & inside(wooden_block_b, toy_box) & on(kitchen_sponge, kitchen_island/top) & wiped(kitchen_island/top); left in place (10 cm): breakfast_spoon, juice_bottle, mug, oatmeal, paperback_book, rolling_pin, soda_can |
| 0.6 | all done, but the sponge left elsewhere, or kitchen things shifted on the island (still on it, standing) | inside(wooden_block_a, toy_box) & inside(wooden_block_b, toy_box) & not on_floor(kitchen_sponge) & on(breakfast_spoon, kitchen_island/top) & on(juice_bottle, kitchen_island/top) & on(kitchen_sponge, kitchen_island/top) & on(mug, kitchen_island/top) & on(oatmeal, kitchen_island/top) & on(paperback_book, kitchen_island/top) & on(rolling_pin, kitchen_island/top) & on(soda_can, kitchen_island/top) & upright(juice_bottle) & upright(mug) & upright(oatmeal) & upright(soda_can) & wiped(kitchen_island/top) |
| 0.3 | the toys off the island but not in the box, or a kitchen thing put in the box or taken off the island too (sorted wrong) | not on(wooden_block_a, kitchen_island/top) & not on(wooden_block_b, kitchen_island/top) & not on_floor(kitchen_sponge) & on(kitchen_sponge, kitchen_island/top) & wiped(kitchen_island/top) |
| 0 | a toy left on the island; not wiped (or not all of it); the can, mug, oatmeal or juice tipped; the sponge still held or dropped on the floor | |

### T08 · return_sponge_home（布局 3 个）

- 指令 EN：Someone used the sponge and left it lying on a table somewhere. Wipe down the kitchen island with it, then put the sponge away where it is normally kept.
- 指令 中：有人用完海绵随手放在了某张桌子上。用它把厨房岛台擦一下，擦完把海绵收回平时放海绵的地方。
- 场景：the sponge lies on a table, out of view; where sponges are kept is not said: a shallow tray on the low wall cabinet holds the spare sponge
- 考察：storage_place, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the island wiped, the sponge in the tray, the spare sponge still in it | inside(kitchen_sponge, sponge_tray) & wiped(kitchen_island/top) |
| 0.6 | the island wiped, the sponge left in the kitchen (island, a counter, the stove) but not in the tray; or in the tray with the spare knocked out | on_any(kitchen_sponge, [kitchen_island/top/kitchen_counter_1/top/kitchen_counter_2/top/kitchen_stove/top]) & wiped(kitchen_island/top) |
| 0.3 | the island wiped, the sponge back on the table it was found on or elsewhere outside the kitchen | not on_floor(kitchen_sponge) & wiped(kitchen_island/top) |
| 0 | the sponge not found; not wiped (or not all of it); the sponge still held or dropped on the floor | |

### T08 · which_surface（布局 2 个）

- 指令 EN：Breakfast was eaten either at the kitchen island or at the dining table. Wipe the one that was used with the sponge; the other one is clean, leave it. Leave the sponge on the island.
- 指令 中：早饭是在岛台或者餐桌上吃的。用海绵把吃过饭的那个擦一下；另一个是干净的，别擦。擦完把海绵留在岛台上。
- 场景：one of the two surfaces has the used bowl of oatmeal, the spoon and the rolling pin on it, the other has no dishes; the instruction names both and not which
- 考察：referent_clue

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | only the used surface wiped, the sponge on the island | not wiped(dining_table_2/top) & on(kitchen_sponge, kitchen_island/top) & wiped(kitchen_island/top) |
| 0.6 | both wiped (the clean one too, against "leave it") | not on_floor(kitchen_sponge) & on(kitchen_sponge, kitchen_island/top) & wiped(kitchen_island/top) |
| 0.3 | on(kitchen_sponge, kitchen_island/top) & wiped(dining_table_2/top) | on(kitchen_sponge, kitchen_island/top) & wiped(dining_table_2/top) |
| 0 | only the clean one wiped; neither wiped; the sponge still held or dropped on the floor | |

## T09_tomato_soup

- 基础指令 EN：Make tomato soup for lunch: put the cherry tomatoes into the pot, stir them, cover the pot and heat the soup to 60 C. Turn the stove off afterwards.
- 基础指令 中：午饭做个番茄汤：把小番茄放进锅里，搅一搅，盖上锅盖，加热到 60 度，然后关火。

### T09 · lid_off（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the lid lies on the stove beside the pot (where uncover sets it aside)

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the tomatoes in the pot at 60 C, stirred, the lid on, the stove off | covered(handled_cooking_pot, pot_lid) & inside(cherry_tomato_1, handled_cooking_pot) & inside(cherry_tomato_2, handled_cooking_pot) & not heating(kitchen_stove) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60) |
| 0 | one tomato only; below 60 C; the stove left on; a tomato out of the pot; still held or dropped | |

### T09 · lid_on_spoon_away（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the lid is on the pot and the spoon was left on the low wall cabinet
- 考察：lid_on, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers (what is asked for when it is there, else the stand-in: the plate for the lid, the second pot, the fridge's tomato, the big tomato): the tomatoes in the pot at 60 C, stirred, covered, the stove off | covered(handled_cooking_pot, pot_lid) & inside(cherry_tomato_1, handled_cooking_pot) & inside(cherry_tomato_2, handled_cooking_pot) & not heating(kitchen_stove) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60) |
| 0.6 | inside(cherry_tomato_1, handled_cooking_pot) & inside(cherry_tomato_2, handled_cooking_pot) & not heating(kitchen_stove) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60); one of: covered(handled_cooking_pot, lid_plate) // covered(handled_cooking_pot, plate_counter_a) // covered(handled_cooking_pot, plate_counter_b) // covered(handled_cooking_pot, plate_dining_cabinet) // ... 1 more ways | inside(cherry_tomato_1, handled_cooking_pot) & inside(cherry_tomato_2, handled_cooking_pot) & not heating(kitchen_stove) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60); one of: covered(handled_cooking_pot, lid_plate) // covered(handled_cooking_pot, plate_counter_a) // covered(handled_cooking_pot, plate_counter_b) // covered(handled_cooking_pot, plate_dining_cabinet) // ... 1 more ways |
| 0.3 | covered(handled_cooking_pot, cover_book) & inside(cherry_tomato_1, handled_cooking_pot) & inside(cherry_tomato_2, handled_cooking_pot) & not heating(kitchen_stove) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60) | covered(handled_cooking_pot, cover_book) & inside(cherry_tomato_1, handled_cooking_pot) & inside(cherry_tomato_2, handled_cooking_pot) & not heating(kitchen_stove) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60) |
| 0 | one tomato only; below 60 C; the stove left on; a tomato out of the pot; still held or dropped | |

### T09 · pot_in_use（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：a pot full of yesterday's tomato soup may stand on the stove's left burner; the empty cooking pot is then on the dining table next door; the instruction only says 'the pot on the stove'
- 考察：resource_in_use, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | covered(handled_cooking_pot, pot_lid) & inside(cherry_tomato_1, handled_cooking_pot) & inside(cherry_tomato_2, handled_cooking_pot) & not heating(kitchen_stove) & not inside(cherry_tomato_1, soup_pot) & not inside(cherry_tomato_2, soup_pot) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60); left in place (10 cm): soup_pot | covered(handled_cooking_pot, pot_lid) & inside(cherry_tomato_1, handled_cooking_pot) & inside(cherry_tomato_2, handled_cooking_pot) & not heating(kitchen_stove) & not inside(cherry_tomato_1, soup_pot) & not inside(cherry_tomato_2, soup_pot) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60); left in place (10 cm): soup_pot |
| 0.6 | the soup in the empty pot, but the full pot moved off its burner | covered(handled_cooking_pot, pot_lid) & inside(cherry_tomato_1, handled_cooking_pot) & inside(cherry_tomato_2, handled_cooking_pot) & not heating(kitchen_stove) & not inside(cherry_tomato_1, soup_pot) & not inside(cherry_tomato_2, soup_pot) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60) |
| 0.3 | the tomatoes cooked in yesterday's soup | covered(handled_cooking_pot, pot_lid) & inside(cherry_tomato_1, soup_pot) & inside(cherry_tomato_2, soup_pot) & not heating(kitchen_stove) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60) |
| 0 | the full pot tipped; one tomato only; below 60 C; the stove left on; still held or dropped | |

### T09 · tomato_in_fridge（布局 2 个）

- 指令 EN：Make tomato soup for lunch with three cherry tomatoes: put them into the pot, stir, cover the pot and heat the soup to 60 C. Turn the stove off afterwards.
- 指令 中：午饭用三颗小番茄做番茄汤：放进锅里，搅一搅，盖上锅盖，加热到 60 度，然后关火。
- 场景：the soup needs three tomatoes; two are on the island; the third is kept in the closed fridge (the instruction does not say where it is)
- 考察：storage_place, not_in_view, closed_fridge

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers (what is asked for when it is there, else the stand-in: the plate for the lid, the second pot, the fridge's tomato, the big tomato): the tomatoes in the pot at 60 C, stirred, covered, the stove off | covered(handled_cooking_pot, pot_lid) & inside(cherry_tomato_1, handled_cooking_pot) & inside(cherry_tomato_2, handled_cooking_pot) & inside(fridge_tomato, handled_cooking_pot) & not heating(kitchen_stove) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60) & temperature_at_least(fridge_tomato, 60) |
| 0.6 | covered(handled_cooking_pot, pot_lid) & inside(big_tomato, handled_cooking_pot) & inside(cherry_tomato_1, handled_cooking_pot) & inside(cherry_tomato_2, handled_cooking_pot) & not heating(kitchen_stove) & stirred(handled_cooking_pot) & temperature_at_least(big_tomato, 60) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60) | covered(handled_cooking_pot, pot_lid) & inside(big_tomato, handled_cooking_pot) & inside(cherry_tomato_1, handled_cooking_pot) & inside(cherry_tomato_2, handled_cooking_pot) & not heating(kitchen_stove) & stirred(handled_cooking_pot) & temperature_at_least(big_tomato, 60) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60) |
| 0 | two tomatoes only (the third not found); the apple in the soup; below 60 C; the stove left on; a tomato out of the pot; still held or dropped | |

### T09 · x6_gd_tomato_elsewhere（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：one cherry tomato is on the island, the other is on the dining table: left there, or on someone's lunch plate

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers (what is asked for when it is there, else the stand-in: the plate for the lid, the second pot, the fridge's tomato, the big tomato): the tomatoes in the pot at 60 C, stirred, covered, the stove off | covered(handled_cooking_pot, pot_lid) & inside(cherry_tomato_1, handled_cooking_pot) & inside(cherry_tomato_2, handled_cooking_pot) & not heating(kitchen_stove) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60); left in place (10 cm): plate_tomato |
| 0.3 | covered(handled_cooking_pot, pot_lid) & inside(cherry_tomato_1, handled_cooking_pot) & inside(plate_tomato, handled_cooking_pot) & not heating(kitchen_stove) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(plate_tomato, 60) | covered(handled_cooking_pot, pot_lid) & inside(cherry_tomato_1, handled_cooking_pot) & inside(plate_tomato, handled_cooking_pot) & not heating(kitchen_stove) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(plate_tomato, 60) |
| 0 | one tomato only (the other not found); below 60 C; the stove left on; a tomato out of the pot; still held or dropped | |

### T09 · pot_in_dining_room（布局 2 个）

- 指令 EN：Make tomato soup for lunch: put the cherry tomatoes into the pot, stir them, cover the pot and heat the soup to 60 C. Turn the stove off afterwards.
- 指令 中：午饭做个番茄汤：把小番茄放进锅里，搅一搅，盖上锅盖，加热到 60 度，然后关火。
- 场景：the pot is not on the stove (its lid is): it stands on the dining table in the next room, or it is gone and a second pot of the same kind stands on the island
- 考察：missing_piece, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers (what is asked for when it is there, else the stand-in: the plate for the lid, the second pot, the fridge's tomato, the big tomato): the tomatoes in the pot at 60 C, stirred, covered, the stove off | covered(handled_cooking_pot, pot_lid) & inside(cherry_tomato_1, handled_cooking_pot) & inside(cherry_tomato_2, handled_cooking_pot) & not heating(kitchen_stove) & stirred(handled_cooking_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60) |
| 0.6 | covered(spare_pot, pot_lid) & inside(cherry_tomato_1, spare_pot) & inside(cherry_tomato_2, spare_pot) & not heating(kitchen_stove) & stirred(spare_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60) | covered(spare_pot, pot_lid) & inside(cherry_tomato_1, spare_pot) & inside(cherry_tomato_2, spare_pot) & not heating(kitchen_stove) & stirred(spare_pot) & temperature_at_least(cherry_tomato_1, 60) & temperature_at_least(cherry_tomato_2, 60) |
| 0 | the pot not found; a bowl or a mug used for the pot; one tomato only; below 60 C; the stove left on; still held or dropped | |

## T10_trash_the_can

- 基础指令 EN：Someone left an empty soda can lying around. Throw it into the trash can.
- 基础指令 中：有人随手放了个空易拉罐，把它扔进垃圾桶。

### T10 · can_on_island（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the can stands on the island

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the can in the trash can | inside(soda_can, trash_can) |
| 0 | the can not in the trash can (another bin, left out); still held or dropped | |

### T10 · can_in_dining_room（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the can stands on the dining table in the next room, out of sight

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the can found and in the trash can | inside(soda_can, trash_can) |
| 0 | the can not in the trash can (another bin, left out); still held or dropped | |

### T10 · keep_kids_can（布局 2 个）

- 指令 EN：Throw the finished soda can into the trash can. Leave the one the kid is drinking from while doing homework.
- 指令 中：把喝完的易拉罐扔进垃圾桶。孩子一边写作业一边喝的那罐别扔。
- 场景：two identical cans: one stands among the kid's homework things (a notebook and a pencil), the other on its own; one of them is on the island, the other on the study desk
- 考察：referent_clue, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the drunk can in the trash, the kid's can and homework untouched | inside(soda_can, trash_can); left in place (10 cm): craft_notebook, craft_pencil, kids_can |
| 0.6 | the right can thrown away, but the kid's can, notebook or pencil moved off its place | inside(soda_can, trash_can) & not inside(kids_can, trash_can) |
| 0 | the kid's can thrown away or tipped; the other can not in the trash; still held or dropped | |

### T10 · trash_moved（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the can is on the island; the trash can is not in its usual place (the dining room), or it is there but stuffed full, with snack cartons over its rim; a second trash can stands in the bathroom
- 考察：destination_unnamed, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the can in the trash can that has room: the moved one (dining room); when the one by the island is full, the bathroom's, the full one untouched | inside(soda_can, trash_can) |
| 0.6 | inside(soda_can, bathroom_trash) | inside(soda_can, bathroom_trash) |
| 0 | the can not in a trash can (left on the full one, another bin, left out); still held or dropped | |

### T10 · after_dinner_clear（布局 3 个）

- 指令 EN：Dinner is over; clear the dining table: rubbish goes in the trash can, leftover food in the fridge, used dishes back to the kitchen counter. The cereal boxes stay on the table.
- 指令 中：晚饭吃完了，把餐桌收拾干净：垃圾扔进垃圾桶，剩饭剩菜放进冰箱，用过的餐具拿回厨房台面。麦片盒留在桌上。
- 场景：the dining table holds an empty soda can, and two of: an empty foil takeout tray, a glass box with leftover rice, a used mug; the instruction names the kinds, not the objects
- 考察：disposal_by_state, multi_object_goal

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | rubbish in the trash, leftovers in the fridge, the mug to the kitchen, the cereal untouched | inside(soda_can, kitchen_trash) & inside(takeout_tray, kitchen_trash) & on(leftovers, breakfast_fridge/inside_shelf); left in place (10 cm): clutter_cereal_a, clutter_cereal_b |
| 0.6 | everything where it goes, but the cereal moved | inside(soda_can, kitchen_trash) & inside(takeout_tray, kitchen_trash) & on(leftovers, breakfast_fridge/inside_shelf) |
| 0.3 | the leftovers left on a kitchen surface, not in the fridge | inside(soda_can, kitchen_trash) & inside(takeout_tray, kitchen_trash) & on_any(leftovers, [breakfast_fridge/inside_shelf/kitchen_island/top/kitchen_counter_1/top/kitchen_counter_2/top/kitchen_stove/top]) |
| 0 | an item left on the table or put in a wrong kind of place (leftovers in the trash, the mug in the trash); the mug tipped; still held or dropped | |

### T10 · guests_coming（布局 3 个）

- 指令 EN：Guests arrive in ten minutes; make the living room presentable. Put whatever is lying about where it belongs (rubbish in the trash can, dishes to the kitchen, toys in the toy box), and leave things that belong where they are.
- 指令 中：客人十分钟后到，把客厅收拾得能见人：乱放的东西各回各处（垃圾扔进垃圾桶，餐具拿回厨房，玩具放进玩具箱），本来就该在那儿的东西别动。
- 场景：in the living room an empty can and a used mug stand on the TV stand and a toy block lies on the floor (two or three of them); the island's rolling pin and sponge belong there
- 考察：goal_items_unstated, multi_object_goal

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the can in the trash, the mug to the kitchen, the block in the toy box, the island's things untouched | inside(soda_can, trash_can) & inside(wooden_block_a, toy_box) & on_any(used_mug, [kitchen_counter_1/top/kitchen_counter_2/top/kitchen_island/top]) & upright(used_mug); left in place (10 cm): kitchen_sponge, rolling_pin |
| 0.6 | all put back, but the rolling pin or the sponge on the island moved (they belong there) | inside(soda_can, trash_can) & inside(wooden_block_a, toy_box) & on_any(used_mug, [kitchen_counter_1/top/kitchen_counter_2/top/kitchen_island/top]) & upright(used_mug) |
| 0.3 | the can in the trash, but the mug or the block only taken off the TV stand / floor, not to its place | inside(soda_can, trash_can) & not on(used_mug, tv_stand_2/top) & not on_floor(used_mug) & not on_floor(wooden_block_a) |
| 0 | the can not in the trash; something left lying about; the mug tipped; still held or dropped | |

### T10 · x6_gd_can_put_away（布局 2 个）

- 指令 EN：An empty soda can was put away in the kitchen by mistake. Find it and throw it into the trash can.
- 指令 中：厨房里有个空易拉罐被人误收起来了，找出来扔进垃圾桶。
- 场景：the can was put away behind a door in the kitchen (the microwave, the wall cabinet or the fridge); the instruction names none of them

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the empty can found and in the trash, the unopened can in the fridge untouched | inside(soda_can, trash_can); left in place (10 cm): fridge_soda |
| 0.3 | inside(fridge_soda, trash_can) & inside(soda_can, trash_can) | inside(fridge_soda, trash_can) & inside(soda_can, trash_can) |
| 0 | the empty can not found or not in the trash (only the fridge's can thrown); still held or dropped | |

## T11_collect_fruits

- 基础指令 EN：Lunch is over and the apple is still on the dining table. Put it away in the fruit basket.
- 基础指令 中：午饭吃完了，苹果还在餐桌上，把它收进果篮里。

### T11 · fruits_on_table（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the apple on the dining table, the basket on the bedroom bookcase

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the apple in the fruit basket | inside(apple, fruit_basket) |
| 0.6 | the apple on the serving tray though the basket is there | one of: inside(apple, serving_tray) // on_any(apple, [kitchen_cabinet_1/inside_shelf/kitchen_cabinet_1/inside_bottom/kitchen_cabinet_2/inside_shelf/kitchen_cabinet_2/inside_bottom/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_4/inside_bottom/...]) |
| 0 | the apple left on the table or put elsewhere; still held or dropped | |

### T11 · basket_missing（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：no fruit basket on the bookcase: the serving tray on the study desk
- 考察：container_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | one of: inside(apple, fruit_basket) // inside(apple, serving_tray) // on_any(apple, [kitchen_cabinet_1/inside_shelf/kitchen_cabinet_1/inside_bottom/kitchen_cabinet_2/inside_shelf/kitchen_cabinet_2/inside_bottom/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_4/inside_bottom/...]) | one of: inside(apple, fruit_basket) // inside(apple, serving_tray) // on_any(apple, [kitchen_cabinet_1/inside_shelf/kitchen_cabinet_1/inside_bottom/kitchen_cabinet_2/inside_shelf/kitchen_cabinet_2/inside_bottom/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_4/inside_bottom/...]) |
| 0.6 | inside(apple, used_bowl) | inside(apple, used_bowl) |
| 0 | the apple left on the table or put elsewhere; still held or dropped | |

### T11 · leave_one_for_kid（布局 3 个）

- 指令 EN：Lunch is over. Put the fruit on the table away, but leave one for the kid doing homework in the study as a snack. The kid doesn't like oranges.
- 指令 中：午饭吃完了，把桌上的水果收起来，给在书房写作业的孩子留一个当点心。孩子不爱吃橙子。
- 场景：two or three fruits on the dining table; the instruction names neither the basket nor the desk, and which fruit is the snack follows from the kid's dislike
- 考察：storage_place, preference_allocation, multi_object_goal

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | a fruit the kid likes on the study desk, the rest in the fruit basket | inside(lunch_orange, fruit_basket) & on(apple, desk_1/top) |
| 0.6 | the right fruit to the kid, the rest put away somewhere other than the basket | not on(lunch_orange, dining_table_2/top) & not on_floor(lunch_orange) & on(apple, desk_1/top) |
| 0.3 | the orange (the kid does not like it) to the kid, the rest in the basket | inside(apple, fruit_basket) & on(lunch_orange, desk_1/top) |
| 0 | nothing for the kid; fruit left on the table; still held or dropped | |

### T11 · fruit_plate_for_guests（布局 2 个）

- 指令 EN：The guests are watching TV in the living room. Bring them the apple and the orange from the dining table on a tray, and leave the tray on the TV stand in front of them.
- 指令 中：客人在客厅看电视，把餐桌上的苹果和橙子放在托盘上端过去，托盘放在他们面前的电视柜上。
- 场景：the apple and an orange on the dining table, a small tray elsewhere; the tray is to end in front of the guests with the fruit on it
- 考察：subgoal_order, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers: a free tray (the small one when it is empty, else the serving tray) with the apple and the orange in front of the guests, the kid's homework untouched | inside(apple, fruit_tray) & inside(lunch_orange, fruit_tray) & on_any(fruit_tray, [tv_stand_2/top/tv_stand_1/top]) |
| 0.6 | the fruit carried without a tray | on_any(apple, [tv_stand_2/top/tv_stand_1/top]) & on_any(lunch_orange, [tv_stand_2/top/tv_stand_1/top]) |
| 0 | nothing brought to the guests; fruit dropped; still held | |

## T12_tidy_toys

- 基础指令 EN：It is nearly bedtime. Put the kid's toys away in the storage basket.
- 基础指令 中：快到睡觉时间了，把孩子的玩具收进收纳篮里。

### T12 · toys_out（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the car on the living-room floor, the duck on the TV stand

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the car and the duck in the storage basket | inside(rubber_duck, storage_basket) & inside(toy_car, storage_basket) |
| 0 | a toy left out; the basket tipped; still held or dropped | |

### T12 · duck_in_study（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the duck was left on the study desk

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | both toys in the basket, the duck found | inside(rubber_duck, storage_basket) & inside(toy_car, storage_basket) |
| 0 | a toy left out; the basket tipped; still held or dropped | |

### T12 · bins_capacity（布局 6 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：no storage basket; two small bins, one already full of toy blocks (two layers), the other empty; they stand side by side or in different rooms; the car on the living-room floor, the duck on the study desk
- 考察：joint_capacity

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | fully_inside(stored_block_1, toy_bin_small) & fully_inside(stored_block_10, toy_bin_small) & fully_inside(stored_block_11, toy_bin_small) & fully_inside(stored_block_12, toy_bin_small) & fully_inside(stored_block_13, toy_bin_small) & fully_inside(stored_block_14, toy_bin_small) & fully_inside(stored_block_15, toy_bin_small) & fully_inside(stored_block_16, toy_bin_small) & fully_inside(stored_block_17, toy_bin_small) & fully_inside(stored_block_18, toy_bin_small) & fully_inside(stored_block_19, toy_bin_small) & fully_inside(stored_block_2, toy_bin_small) & fully_inside(stored_block_20, toy_bin_small) & fully_inside(stored_block_21, toy_bin_small) & fully_inside(stored_block_22, toy_bin_small) & fully_inside(stored_block_23, toy_bin_small) & fully_inside(stored_block_24, toy_bin_small) & fully_inside(stored_block_3, toy_bin_small) & fully_inside(stored_block_4, toy_bin_small) & fully_inside(stored_block_5, toy_bin_small) & fully_inside(stored_block_6, toy_bin_small) & fully_inside(stored_block_7, toy_bin_small) & fully_inside(stored_block_8, toy_bin_small) & fully_inside(stored_block_9, toy_bin_small) & inside(rubber_duck, toy_bin_small_2) & inside(toy_car, toy_bin_small_2) | fully_inside(stored_block_1, toy_bin_small) & fully_inside(stored_block_10, toy_bin_small) & fully_inside(stored_block_11, toy_bin_small) & fully_inside(stored_block_12, toy_bin_small) & fully_inside(stored_block_13, toy_bin_small) & fully_inside(stored_block_14, toy_bin_small) & fully_inside(stored_block_15, toy_bin_small) & fully_inside(stored_block_16, toy_bin_small) & fully_inside(stored_block_17, toy_bin_small) & fully_inside(stored_block_18, toy_bin_small) & fully_inside(stored_block_19, toy_bin_small) & fully_inside(stored_block_2, toy_bin_small) & fully_inside(stored_block_20, toy_bin_small) & fully_inside(stored_block_21, toy_bin_small) & fully_inside(stored_block_22, toy_bin_small) & fully_inside(stored_block_23, toy_bin_small) & fully_inside(stored_block_24, toy_bin_small) & fully_inside(stored_block_3, toy_bin_small) & fully_inside(stored_block_4, toy_bin_small) & fully_inside(stored_block_5, toy_bin_small) & fully_inside(stored_block_6, toy_bin_small) & fully_inside(stored_block_7, toy_bin_small) & fully_inside(stored_block_8, toy_bin_small) & fully_inside(stored_block_9, toy_bin_small) & inside(rubber_duck, toy_bin_small_2) & inside(toy_car, toy_bin_small_2) |
| 0.6 | the toys split between the bins or pressed onto the full one, its blocks still all inside | fully_inside(stored_block_1, toy_bin_small) & fully_inside(stored_block_10, toy_bin_small) & fully_inside(stored_block_11, toy_bin_small) & fully_inside(stored_block_12, toy_bin_small) & fully_inside(stored_block_13, toy_bin_small) & fully_inside(stored_block_14, toy_bin_small) & fully_inside(stored_block_15, toy_bin_small) & fully_inside(stored_block_16, toy_bin_small) & fully_inside(stored_block_17, toy_bin_small) & fully_inside(stored_block_18, toy_bin_small) & fully_inside(stored_block_19, toy_bin_small) & fully_inside(stored_block_2, toy_bin_small) & fully_inside(stored_block_20, toy_bin_small) & fully_inside(stored_block_21, toy_bin_small) & fully_inside(stored_block_22, toy_bin_small) & fully_inside(stored_block_23, toy_bin_small) & fully_inside(stored_block_24, toy_bin_small) & fully_inside(stored_block_3, toy_bin_small) & fully_inside(stored_block_4, toy_bin_small) & fully_inside(stored_block_5, toy_bin_small) & fully_inside(stored_block_6, toy_bin_small) & fully_inside(stored_block_7, toy_bin_small) & fully_inside(stored_block_8, toy_bin_small) & fully_inside(stored_block_9, toy_bin_small); one of: inside(toy_car, toy_bin_small) & inside(rubber_duck, toy_bin_small) // inside(toy_car, toy_bin_small) & inside(rubber_duck, toy_bin_small_2) // inside(toy_car, toy_bin_small_2) & inside(rubber_duck, toy_bin_small) |
| 0.3 | the toys in the bins, but blocks pushed out of the full bin | one of: inside(toy_car, toy_bin_small) & inside(rubber_duck, toy_bin_small) // inside(toy_car, toy_bin_small) & inside(rubber_duck, toy_bin_small_2) // inside(toy_car, toy_bin_small_2) & inside(rubber_duck, toy_bin_small) // inside(toy_car, toy_bin_small_2) & inside(rubber_duck, toy_bin_small_2) |
| 0 | a toy left out; a bin tipped; still held or dropped | |

### T12 · castle_stays（布局 3 个）

- 指令 EN：It is nearly bedtime. Put the kid's toys away in the storage basket. Don't take apart the block castle the kid built; the kid wants to keep building it tomorrow.
- 指令 中：快到睡觉时间了，把孩子的玩具收进收纳篮里。他搭的积木城堡别拆，明天还要接着搭。
- 场景：a tower of identical wooden blocks on the living-room floor, loose blocks of the same kind beside it, the car and the duck
- 考察：relational_exception, multi_object_goal

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the car, the duck and the loose blocks in the basket, the castle untouched | inside(loose_block_1, storage_basket) & inside(loose_block_2, storage_basket) & inside(rubber_duck, storage_basket) & inside(toy_car, storage_basket) & on_top_of(castle_block_2, castle_block_1) & on_top_of(castle_block_3, castle_block_2); left in place (10 cm): castle_block_1, castle_block_2, castle_block_3 |
| 0.6 | the castle moved off its place, or the loose blocks left beside it | inside(rubber_duck, storage_basket) & inside(toy_car, storage_basket) & on_top_of(castle_block_2, castle_block_1) & on_top_of(castle_block_3, castle_block_2) |
| 0 | the castle left taken apart or knocked down; the car or the duck left out; still held or dropped | |

## T13_breakfast_setup

- 基础指令 EN：Breakfast is soon. Set a place at the dining table: a bowl, a cup and a spoon, standing together.
- 基础指令 中：快吃早饭了，在餐桌上摆一份餐具：碗、杯子和勺子，立着摆在一起。

### T13 · dishes_on_tv_stand（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：bowl and cup on the living-room TV stand, the spoon on the dining table

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | bowl, cup and spoon together on the dining table, upright | one of: on(bowl, dining_table_2/top) & upright(bowl) & on(cup, dining_table_2/top) & upright(cup) & grouped([bowl/cup/spoon], dining_table_2/top, 0.5) // on(bowl, dining_table_1/top) & upright(bowl) & on(cup, dining_table_1/top) & upright(cup) & grouped([bowl/cup/spoon], dining_table_1/top, 0.5) // on(bowl, dining_table_2/top) & upright(bowl) & on(cup_counter_b, dining_table_2/top) & upright(cup_counter_b) & grouped([bowl/cup_counter_b/spoon], dining_table_2/top, 0.5) // on(bowl, dining_table_1/top) & upright(bowl) & on(cup_counter_b, dining_table_1/top) & upright(cup_counter_b) & grouped([bowl/cup_counter_b/spoon], dining_table_1/top, 0.5) // ... 28 more ways |
| 0.6 | the mug for the cup though the cup is there | one of: on(bowl, dining_table_2/top) & upright(bowl) & on(mug, dining_table_2/top) & upright(mug) & grouped([bowl/mug/spoon], dining_table_2/top, 0.5) // on(bowl, dining_table_1/top) & upright(bowl) & on(mug, dining_table_1/top) & upright(mug) & grouped([bowl/mug/spoon], dining_table_1/top, 0.5) // on(bowl, dining_table_2/top) & upright(bowl) & on(mug_counter, dining_table_2/top) & upright(mug_counter) & grouped([bowl/mug_counter/spoon], dining_table_2/top, 0.5) // on(bowl, dining_table_1/top) & upright(bowl) & on(mug_counter, dining_table_1/top) & upright(mug_counter) & grouped([bowl/mug_counter/spoon], dining_table_1/top, 0.5) // ... 32 more ways |
| 0 | a piece missing; tipped; still held or dropped | |

### T13 · no_cup（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：no cup in the house: the mug on the bedroom bookcase
- 考察：no_cup

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | one of: on(bowl, dining_table_2/top) & upright(bowl) & on(cup, dining_table_2/top) & upright(cup) & grouped([bowl/cup/spoon], dining_table_2/top, 0.5) // on(bowl, dining_table_1/top) & upright(bowl) & on(cup, dining_table_1/top) & upright(cup) & grouped([bowl/cup/spoon], dining_table_1/top, 0.5) // on(bowl, dining_table_2/top) & upright(bowl) & on(cup_counter_b, dining_table_2/top) & upright(cup_counter_b) & grouped([bowl/cup_counter_b/spoon], dining_table_2/top, 0.5) // on(bowl, dining_table_1/top) & upright(bowl) & on(cup_counter_b, dining_table_1/top) & upright(cup_counter_b) & grouped([bowl/cup_counter_b/spoon], dining_table_1/top, 0.5) // ... 64 more ways | one of: on(bowl, dining_table_2/top) & upright(bowl) & on(cup, dining_table_2/top) & upright(cup) & grouped([bowl/cup/spoon], dining_table_2/top, 0.5) // on(bowl, dining_table_1/top) & upright(bowl) & on(cup, dining_table_1/top) & upright(cup) & grouped([bowl/cup/spoon], dining_table_1/top, 0.5) // on(bowl, dining_table_2/top) & upright(bowl) & on(cup_counter_b, dining_table_2/top) & upright(cup_counter_b) & grouped([bowl/cup_counter_b/spoon], dining_table_2/top, 0.5) // on(bowl, dining_table_1/top) & upright(bowl) & on(cup_counter_b, dining_table_1/top) & upright(cup_counter_b) & grouped([bowl/cup_counter_b/spoon], dining_table_1/top, 0.5) // ... 64 more ways |
| 0.6 | upright(kid_cup); one of: on(bowl, dining_table_2/top) & upright(bowl) & on(kid_cup, dining_table_2/top) & grouped([bowl/kid_cup/spoon], dining_table_2/top, 0.5) // on(bowl, dining_table_1/top) & upright(bowl) & on(kid_cup, dining_table_1/top) & grouped([bowl/kid_cup/spoon], dining_table_1/top, 0.5) // on(bowl_dining_cabinet, dining_table_2/top) & upright(bowl_dining_cabinet) & on(kid_cup, dining_table_2/top) & grouped([bowl_dining_cabinet/kid_cup/spoon], dining_table_2/top, 0.5) // on(bowl_dining_cabinet, dining_table_1/top) & upright(bowl_dining_cabinet) & on(kid_cup, dining_table_1/top) & grouped([bowl_dining_cabinet/kid_cup/spoon], dining_table_1/top, 0.5) // ... 5 more ways | upright(kid_cup); one of: on(bowl, dining_table_2/top) & upright(bowl) & on(kid_cup, dining_table_2/top) & grouped([bowl/kid_cup/spoon], dining_table_2/top, 0.5) // on(bowl, dining_table_1/top) & upright(bowl) & on(kid_cup, dining_table_1/top) & grouped([bowl/kid_cup/spoon], dining_table_1/top, 0.5) // on(bowl_dining_cabinet, dining_table_2/top) & upright(bowl_dining_cabinet) & on(kid_cup, dining_table_2/top) & grouped([bowl_dining_cabinet/kid_cup/spoon], dining_table_2/top, 0.5) // on(bowl_dining_cabinet, dining_table_1/top) & upright(bowl_dining_cabinet) & on(kid_cup, dining_table_1/top) & grouped([bowl_dining_cabinet/kid_cup/spoon], dining_table_1/top, 0.5) // ... 5 more ways |
| 0 | a piece missing; tipped; still held or dropped | |

### T13 · copy_the_setting（布局 3 个）

- 指令 EN：Set the other place, at the second spoon, the same way as the place that is already set.
- 指令 中：照着桌上摆好的那份，在另一把勺子那里也摆一份。
- 场景：one place is set across the table; the other has only its spoon; the instruction does not say what to bring
- 考察：goal_by_example

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the same things, laid out as in the set place, by the other spoon; the set place untouched | same_arrangement([bowl/cup], [example_bowl/example_cup], spoon, example_spoon, [1.0/0.0], [-1.0/0.0], 0.12); one of: upright(bowl) & upright(cup) // upright(bowl) & upright(cup_counter_b) // upright(bowl) & upright(cup_kitchen_cabinet) // upright(bowl) & upright(cup_side_table) // ... 16 more ways |
| 0.6 | same_arrangement([bowl/mug], [example_bowl/example_cup], spoon, example_spoon, [1.0/0.0], [-1.0/0.0], 0.12); one of: upright(bowl) & upright(mug) // upright(bowl) & upright(mug_counter) // upright(bowl) & upright(mug_dining_cabinet) // upright(bowl) & upright(mug_shelf) // ... 16 more ways | same_arrangement([bowl/mug], [example_bowl/example_cup], spoon, example_spoon, [1.0/0.0], [-1.0/0.0], 0.12); one of: upright(bowl) & upright(mug) // upright(bowl) & upright(mug_counter) // upright(bowl) & upright(mug_dining_cabinet) // upright(bowl) & upright(mug_shelf) // ... 16 more ways |
| 0.3 | same_arrangement([bowl/kid_cup], [example_bowl/example_cup], spoon, example_spoon, [1.0/0.0], [-1.0/0.0], 0.12) & upright(kid_cup); one of: upright(bowl) // upright(bowl_dining_cabinet) // upright(bowl_inside_kitchen_cabinet) // upright(bowl_kitchen_cabinet) // ... 1 more ways | same_arrangement([bowl/kid_cup], [example_bowl/example_cup], spoon, example_spoon, [1.0/0.0], [-1.0/0.0], 0.12) & upright(kid_cup); one of: upright(bowl) // upright(bowl_dining_cabinet) // upright(bowl_inside_kitchen_cabinet) // upright(bowl_kitchen_cabinet) // ... 1 more ways |
| 0 | a piece missing; the wrong place; tipped; still held or dropped | |

### T13 · finish_the_table（布局 3 个）

- 指令 EN：Set the rest of the places at the table.
- 指令 中：把桌上剩下的位子也摆好。
- 场景：three places are set: two adults' with a bowl and a mug, the kid's with a bowl, a plastic cup and a toy beside it; the empty places have a spoon, a kid's one also a toy car
- 考察：rule_induction, referent_clue

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | each empty place set like its kind (adult: bowl and mug; kid: bowl and plastic cup), the set places untouched | not near_any(w_mid_spoon, [kid_cup], 0.25); one of: near_any(w_mid_spoon, [bowl/bowl_2], 0.12) & near_any(w_mid_spoon, [mug/mug_2], 0.12) // near_any(w_mid_spoon, [bowl/bowl_2], 0.12) & near_any(w_mid_spoon, [mug_counter/mug_2], 0.12) // near_any(w_mid_spoon, [bowl/bowl_2], 0.12) & near_any(w_mid_spoon, [mug_dining_cabinet/mug_2], 0.12) // near_any(w_mid_spoon, [bowl/bowl_2], 0.12) & near_any(w_mid_spoon, [mug_shelf/mug_2], 0.12) // ... 16 more ways; left in place (10 cm): e_mid_bowl, e_mid_drink, e_mid_spoon, e_mid_toy, e_north_bowl, e_north_drink, e_north_spoon, w_north_bowl ... |
| 0.6 | the empty places set right, but something of the set places moved off its place | not near_any(w_mid_spoon, [kid_cup], 0.25); one of: near_any(w_mid_spoon, [bowl/bowl_2], 0.12) & near_any(w_mid_spoon, [mug/mug_2], 0.12) // near_any(w_mid_spoon, [bowl/bowl_2], 0.12) & near_any(w_mid_spoon, [mug_counter/mug_2], 0.12) // near_any(w_mid_spoon, [bowl/bowl_2], 0.12) & near_any(w_mid_spoon, [mug_dining_cabinet/mug_2], 0.12) // near_any(w_mid_spoon, [bowl/bowl_2], 0.12) & near_any(w_mid_spoon, [mug_shelf/mug_2], 0.12) // ... 16 more ways |
| 0.3 | a bowl and a drink at each empty place, but the wrong drink (a mug at the kid's, the plastic cup at an adult's) | one of: near_any(w_mid_spoon, [bowl/bowl_2], 0.12) & near_any(w_mid_spoon, [mug/mug_2/kid_cup], 0.12) // near_any(w_mid_spoon, [bowl/bowl_2], 0.12) & near_any(w_mid_spoon, [mug_counter/mug_2/kid_cup], 0.12) // near_any(w_mid_spoon, [bowl/bowl_2], 0.12) & near_any(w_mid_spoon, [mug_dining_cabinet/mug_2/kid_cup], 0.12) // near_any(w_mid_spoon, [bowl/bowl_2], 0.12) & near_any(w_mid_spoon, [mug_shelf/mug_2/kid_cup], 0.12) // ... 16 more ways |
| 0 | an empty place left unset or half set; tipped; still held or dropped | |

## T15_cover_the_pot

- 基础指令 EN：The soup will sit a while before we eat. Cover the pot of soup on the stove with its lid.
- 基础指令 中：汤要放一会儿再吃，用锅盖把灶台上的汤锅盖好。

### T15 · lid_by_pot（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the pot on the left burner, its lid on the island beside the stove

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the pot covered with its lid | covered(handled_cooking_pot, pot_lid) |
| 0 | the pot not covered; the lid dropped or still held | |

### T15 · lid_elsewhere（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the lid is not by the stove: it lies on the dining table, out of view -- free, or covering a bowl of oatmeal someone has not finished
- 考察：not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers: the lid when it is free, else a plate from the counter (the lid left on the stew or on someone's bowl) | covered(handled_cooking_pot, pot_lid) |
| 0.6 | one of: covered(handled_cooking_pot, plate_counter_a) // covered(handled_cooking_pot, plate_dining_cabinet) // covered(handled_cooking_pot, plate_inside_kitchen_cabinet) // covered(handled_cooking_pot, plate_counter_b) | one of: covered(handled_cooking_pot, plate_counter_a) // covered(handled_cooking_pot, plate_dining_cabinet) // covered(handled_cooking_pot, plate_inside_kitchen_cabinet) // covered(handled_cooking_pot, plate_counter_b) |
| 0.3 | covered(handled_cooking_pot, cover_book) | covered(handled_cooking_pot, cover_book) |
| 0 | the pot not covered; the lid not found; someone's bowl tipped; still held | |

### T15 · no_lid（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：there is no pot lid in the house; plates stand on the kitchen counter; a book lies on the island
- 考察：resource_absent, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | one of: covered(handled_cooking_pot, plate_counter_a) // covered(handled_cooking_pot, plate_dining_cabinet) // covered(handled_cooking_pot, plate_inside_kitchen_cabinet) // covered(handled_cooking_pot, plate_counter_b) | one of: covered(handled_cooking_pot, plate_counter_a) // covered(handled_cooking_pot, plate_dining_cabinet) // covered(handled_cooking_pot, plate_inside_kitchen_cabinet) // covered(handled_cooking_pot, plate_counter_b) |
| 0.6 | the pot covered with the book, or the lid taken off the stew | covered(handled_cooking_pot, cover_book) |
| 0 | the pot not covered; still held or dropped | |

### T15 · lid_in_use（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the lid is on the other pot (a stew on the right burner); plates stand on the kitchen counter
- 考察：resource_in_use, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | covered(stew_pot, pot_lid) & upright(stew_pot); one of: covered(handled_cooking_pot, plate_counter_a) // covered(handled_cooking_pot, plate_dining_cabinet) // covered(handled_cooking_pot, plate_inside_kitchen_cabinet) // covered(handled_cooking_pot, plate_counter_b) | covered(stew_pot, pot_lid) & upright(stew_pot); one of: covered(handled_cooking_pot, plate_counter_a) // covered(handled_cooking_pot, plate_dining_cabinet) // covered(handled_cooking_pot, plate_inside_kitchen_cabinet) // covered(handled_cooking_pot, plate_counter_b) |
| 0.6 | the pot covered with the book, or the lid taken off the stew | covered(handled_cooking_pot, pot_lid) |
| 0 | the soup not covered; the stew pot tipped; still held or dropped | |

## T16_pack_snack_box

- 基础指令 EN：The kid takes some fruit to school tomorrow. Put an apple into his snack box and leave the box on his study desk.
- 基础指令 中：孩子明天上学要带水果，把一个苹果装进他的零食盒，再把零食盒放到书房书桌上。

### T16 · box_on_counter（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the snack box on the kitchen counter, the apple on the dining table

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the apple in the snack box on his desk | inside(school_apple, snack_box) & on(snack_box, desk_1/top) |
| 0 | the apple not in the box on the desk; still held or dropped | |

### T16 · box_in_cabinet（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the snack box was put away in the low wall cabinet (kitchen cabinet 6), behind its door; or it stands on the counter already full of snacks
- 考察：item_put_away, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers: the apple in the snack box on his desk when the box is free, else in the bowl, the box's contents untouched | inside(school_apple, snack_box) & on(snack_box, desk_1/top) |
| 0.6 | one of: inside(school_apple, spare_bowl) & on(spare_bowl, desk_1/top) // inside(school_apple, bowl_dining_cabinet) & on(bowl_dining_cabinet, desk_1/top) // inside(school_apple, bowl_kitchen_cabinet) & on(bowl_kitchen_cabinet, desk_1/top) // inside(school_apple, bowl_side_table) & on(bowl_side_table, desk_1/top) | one of: inside(school_apple, spare_bowl) & on(spare_bowl, desk_1/top) // inside(school_apple, bowl_dining_cabinet) & on(bowl_dining_cabinet, desk_1/top) // inside(school_apple, bowl_kitchen_cabinet) & on(bowl_kitchen_cabinet, desk_1/top) // inside(school_apple, bowl_side_table) & on(bowl_side_table, desk_1/top) |
| 0 | the box not found; the apple not packed on the desk; still held or dropped | |

### T16 · no_box（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：there is no snack box in the house; a bowl on the kitchen counter, a big storage bin on the TV stand
- 考察：resource_absent, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | one of: inside(school_apple, spare_bowl) & on(spare_bowl, desk_1/top) // inside(school_apple, bowl_dining_cabinet) & on(bowl_dining_cabinet, desk_1/top) // inside(school_apple, bowl_inside_kitchen_cabinet) & on(bowl_inside_kitchen_cabinet, desk_1/top) // inside(school_apple, bowl_kitchen_cabinet) & on(bowl_kitchen_cabinet, desk_1/top) // ... 1 more ways | one of: inside(school_apple, spare_bowl) & on(spare_bowl, desk_1/top) // inside(school_apple, bowl_dining_cabinet) & on(bowl_dining_cabinet, desk_1/top) // inside(school_apple, bowl_inside_kitchen_cabinet) & on(bowl_inside_kitchen_cabinet, desk_1/top) // inside(school_apple, bowl_kitchen_cabinet) & on(bowl_kitchen_cabinet, desk_1/top) // ... 1 more ways |
| 0.6 | the apple in the big storage bin, or squeezed into the box on top of his things | inside(school_apple, big_bin) |
| 0 | the apple not packed; still held or dropped | |

### T16 · box_in_use（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the snack box on the counter holds the kid's crayons (two pencils) and a toy block; a bowl stands next to it
- 考察：resource_in_use

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | inside(box_block, snack_box) & inside(box_crayon_1, snack_box) & inside(box_crayon_2, snack_box); one of: inside(school_apple, spare_bowl) & on(spare_bowl, desk_1/top) // inside(school_apple, bowl_dining_cabinet) & on(bowl_dining_cabinet, desk_1/top) // inside(school_apple, bowl_inside_kitchen_cabinet) & on(bowl_inside_kitchen_cabinet, desk_1/top) // inside(school_apple, bowl_kitchen_cabinet) & on(bowl_kitchen_cabinet, desk_1/top) // ... 1 more ways | inside(box_block, snack_box) & inside(box_crayon_1, snack_box) & inside(box_crayon_2, snack_box); one of: inside(school_apple, spare_bowl) & on(spare_bowl, desk_1/top) // inside(school_apple, bowl_dining_cabinet) & on(bowl_dining_cabinet, desk_1/top) // inside(school_apple, bowl_inside_kitchen_cabinet) & on(bowl_inside_kitchen_cabinet, desk_1/top) // inside(school_apple, bowl_kitchen_cabinet) & on(bowl_kitchen_cabinet, desk_1/top) // ... 1 more ways |
| 0.6 | the apple in the big storage bin, or squeezed into the box on top of his things | inside(box_block, snack_box) & inside(box_crayon_1, snack_box) & inside(box_crayon_2, snack_box) & inside(school_apple, snack_box) & on(snack_box, desk_1/top) |
| 0 | his things taken out of the box; the apple not packed; still held or dropped | |

## T17_hide_and_seek_block

- 基础指令 EN：We are playing hide-and-seek with the kid's toy block: hide the wooden block in the empty pot on the stove and put the lid on so they cannot see it.
- 基础指令 中：陪孩子玩藏东西的游戏：把木积木藏进灶台上的空锅里，再盖好锅盖，别让孩子一眼看到。

### T17 · lid_off（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the lid lies on the stove beside the pot

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | hidden in the pot on the stove, the lid on | covered(handled_cooking_pot, pot_lid) & hidden(wooden_block_b) |
| 0.6 | hidden out of sight elsewhere (not in an appliance), not in the covered pot | hidden(wooden_block_b) & not on(wooden_block_b, breakfast_fridge/inside_shelf) & not on(wooden_block_b, kitchen_microwave/inside_floor) |
| 0 | a block in plain sight; hidden in the microwave or the fridge; still held | |

### T17 · h_task_lid_elsewhere（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the pot's lid was left on the wall cabinet: fetch it to the stove first, then hide

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers: hidden in the empty pot under its lid (a plate when the lid is on the stew); with no lid at hand anywhere out of sight but not in an appliance | covered(handled_cooking_pot, pot_lid) & hidden(wooden_block_b) |
| 0.6 | hidden out of sight elsewhere (not an appliance); or the lid taken off the stew | hidden(wooden_block_b) & not on(wooden_block_b, breakfast_fridge/inside_shelf) & not on(wooden_block_b, kitchen_microwave/inside_floor) |
| 0 | a block in plain sight; hidden in the microwave or the fridge; the stew tipped; still held | |

### T17 · hide_both（布局 2 个）

- 指令 EN：We are playing hide-and-seek with the kid's toy blocks: hide both wooden blocks in the empty pot on the stove and put the lid on so they cannot see them.
- 指令 中：我们在和孩子玩捉迷藏，藏的是他的玩具积木：把两块木积木都藏进灶上那个空锅里，再盖上锅盖，别让孩子看见。
- 场景：one block on the island, the other in another room; one pot, one lid; on one seed a second pot on the stove holds soup
- 考察：multi_object_goal, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers: hidden in the empty pot under its lid (a plate when the lid is on the stew); with no lid at hand anywhere out of sight but not in an appliance | covered(handled_cooking_pot, pot_lid) & hidden(floor_block) & hidden(wooden_block_b) |
| 0.6 | hidden out of sight elsewhere (not an appliance); or the lid taken off the stew | hidden(floor_block) & hidden(wooden_block_b) & not on(floor_block, breakfast_fridge/inside_shelf) & not on(floor_block, kitchen_microwave/inside_floor) & not on(wooden_block_b, breakfast_fridge/inside_shelf) & not on(wooden_block_b, kitchen_microwave/inside_floor) |
| 0 | a block in plain sight; hidden in the microwave or the fridge; still held | |

### T17 · hide_somewhere（布局 2 个）

- 指令 EN：We are playing hide-and-seek with the kid: hide the wooden block where the kid cannot see it at a glance. Not inside an appliance, that is dangerous.
- 指令 中：陪孩子玩捉迷藏，把木积木藏到孩子一眼看不到的地方。别藏进电器里，危险。
- 场景：the instruction names no hiding place, only rules out appliances (the microwave and the fridge would hide the block too); the pot on the stove hides it when its lid is at hand
- 考察：storage_place

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the best the seed offers: hidden in the empty pot under its lid (a plate when the lid is on the stew); with no lid at hand anywhere out of sight but not in an appliance | covered(handled_cooking_pot, pot_lid) & inside(wooden_block_b, handled_cooking_pot) & not on(wooden_block_b, breakfast_fridge/inside_shelf) & not on(wooden_block_b, kitchen_microwave/inside_floor) |
| 0.6 | hidden out of sight elsewhere (not an appliance); or the lid taken off the stew | hidden(wooden_block_b) & not on(wooden_block_b, breakfast_fridge/inside_shelf) & not on(wooden_block_b, kitchen_microwave/inside_floor) |
| 0 | in plain sight; in the microwave or the fridge (dangerous, ruled out); still held | |

## T18_set_out_bowls

- 基础指令 EN：Dinner is soon. Take two clean bowls from the low wall cabinet to the dining table, with a spoon by each.
- 基础指令 中：快吃晚饭了，从靠墙矮柜里拿两只干净的碗摆到餐桌上，每只碗配一把勺子。

### T18 · bowls_in_cabinet（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：two clean bowls in the low wall cabinet, two spoons on the kitchen counter

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | two bowls from the low wall cabinet and two spoons on the dining table | one of: on(dinner_bowl_1, dining_table_2/top) & on(dinner_bowl_2, dining_table_2/top) & on(dinner_spoon_1, dining_table_2/top) & on(dinner_spoon_2, dining_table_2/top) // on(dinner_bowl_1, dining_table_1/top) & on(dinner_bowl_2, dining_table_1/top) & on(dinner_spoon_1, dining_table_1/top) & on(dinner_spoon_2, dining_table_1/top) |
| 0 | fewer than two bowls or spoons on the table; a bowl dropped; still held | |

### T18 · bowls_apart（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：one clean bowl in the low wall cabinet, the other in the other low cabinet (kitchen cabinet 4)

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | both bowls found (the second in the other cabinet) and set with the spoons | one of: on(dinner_bowl_1, dining_table_2/top) & on(dinner_bowl_2, dining_table_2/top) & on(dinner_spoon_1, dining_table_2/top) & on(dinner_spoon_2, dining_table_2/top) // on(dinner_bowl_1, dining_table_1/top) & on(dinner_bowl_2, dining_table_1/top) & on(dinner_spoon_1, dining_table_1/top) & on(dinner_spoon_2, dining_table_1/top) |
| 0 | fewer than two bowls or spoons on the table; a bowl dropped; still held | |

### T18 · one_bowl（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：only one clean bowl in the cabinet; a glass food box and the plates on the kitchen counter
- 考察：resource_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | one of: on(dinner_bowl_1, dining_table_2/top) & on(glass_box, dining_table_2/top) & on(dinner_spoon_1, dining_table_2/top) & on(dinner_spoon_2, dining_table_2/top) // on(dinner_bowl_1, dining_table_1/top) & on(glass_box, dining_table_1/top) & on(dinner_spoon_1, dining_table_1/top) & on(dinner_spoon_2, dining_table_1/top) // on(dinner_bowl_1, dining_table_2/top) & on(bowl_dining_cabinet, dining_table_2/top) & on(dinner_spoon_1, dining_table_2/top) & on(dinner_spoon_2, dining_table_2/top) // on(dinner_bowl_1, dining_table_1/top) & on(bowl_dining_cabinet, dining_table_1/top) & on(dinner_spoon_1, dining_table_1/top) & on(dinner_spoon_2, dining_table_1/top) // ... 3 more ways | one of: on(dinner_bowl_1, dining_table_2/top) & on(glass_box, dining_table_2/top) & on(dinner_spoon_1, dining_table_2/top) & on(dinner_spoon_2, dining_table_2/top) // on(dinner_bowl_1, dining_table_1/top) & on(glass_box, dining_table_1/top) & on(dinner_spoon_1, dining_table_1/top) & on(dinner_spoon_2, dining_table_1/top) // on(dinner_bowl_1, dining_table_2/top) & on(bowl_dining_cabinet, dining_table_2/top) & on(dinner_spoon_1, dining_table_2/top) & on(dinner_spoon_2, dining_table_2/top) // on(dinner_bowl_1, dining_table_1/top) & on(bowl_dining_cabinet, dining_table_1/top) & on(dinner_spoon_1, dining_table_1/top) & on(dinner_spoon_2, dining_table_1/top) // ... 3 more ways |
| 0.6 | a plate as the second (soup spills) | one of: on(dinner_bowl_1, dining_table_2/top) & on_any(plate_counter_a, [dining_table_2/top]) // on(dinner_bowl_1, dining_table_1/top) & on_any(plate_counter_a, [dining_table_1/top]) |
| 0 | only one bowl on the table; a bowl dropped; still held | |

### T18 · bowl_in_use（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：two bowls in the cabinet, but one holds leftover cherry tomatoes; a glass food box on the counter
- 考察：resource_in_use

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | inside(left_tomato_1, dinner_bowl_2) & inside(left_tomato_2, dinner_bowl_2) & on(dinner_bowl_2, kitchen_cabinet_6/inside_shelf); one of: on(dinner_bowl_1, dining_table_2/top) & on(glass_box, dining_table_2/top) & on(dinner_spoon_1, dining_table_2/top) & on(dinner_spoon_2, dining_table_2/top) // on(dinner_bowl_1, dining_table_1/top) & on(glass_box, dining_table_1/top) & on(dinner_spoon_1, dining_table_1/top) & on(dinner_spoon_2, dining_table_1/top) // on(dinner_bowl_1, dining_table_2/top) & on(bowl_dining_cabinet, dining_table_2/top) & on(dinner_spoon_1, dining_table_2/top) & on(dinner_spoon_2, dining_table_2/top) // on(dinner_bowl_1, dining_table_1/top) & on(bowl_dining_cabinet, dining_table_1/top) & on(dinner_spoon_1, dining_table_1/top) & on(dinner_spoon_2, dining_table_1/top) // ... 3 more ways | inside(left_tomato_1, dinner_bowl_2) & inside(left_tomato_2, dinner_bowl_2) & on(dinner_bowl_2, kitchen_cabinet_6/inside_shelf); one of: on(dinner_bowl_1, dining_table_2/top) & on(glass_box, dining_table_2/top) & on(dinner_spoon_1, dining_table_2/top) & on(dinner_spoon_2, dining_table_2/top) // on(dinner_bowl_1, dining_table_1/top) & on(glass_box, dining_table_1/top) & on(dinner_spoon_1, dining_table_1/top) & on(dinner_spoon_2, dining_table_1/top) // on(dinner_bowl_1, dining_table_2/top) & on(bowl_dining_cabinet, dining_table_2/top) & on(dinner_spoon_1, dining_table_2/top) & on(dinner_spoon_2, dining_table_2/top) // on(dinner_bowl_1, dining_table_1/top) & on(bowl_dining_cabinet, dining_table_1/top) & on(dinner_spoon_1, dining_table_1/top) & on(dinner_spoon_2, dining_table_1/top) // ... 3 more ways |
| 0.6 | the bowl with the leftover tomatoes put on the table too | one of: on(dinner_bowl_1, dining_table_2/top) & on(dinner_bowl_2, dining_table_2/top) // on(dinner_bowl_1, dining_table_1/top) & on(dinner_bowl_2, dining_table_1/top) |
| 0 | the leftovers tipped out; fewer than two on the table; still held | |

### T18 · door_stuck（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the low wall cabinet's door is stuck and does not open (locked_articulated, to be supported in sim); the other low cabinet also holds two clean bowls
- 考察：appliance_failure

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | one of: on(dinner_bowl_1, dining_table_2/top) & on(dinner_bowl_2, dining_table_2/top) & on(dinner_spoon_1, dining_table_2/top) & on(dinner_spoon_2, dining_table_2/top) // on(dinner_bowl_1, dining_table_1/top) & on(dinner_bowl_2, dining_table_1/top) & on(dinner_spoon_1, dining_table_1/top) & on(dinner_spoon_2, dining_table_1/top) | one of: on(dinner_bowl_1, dining_table_2/top) & on(dinner_bowl_2, dining_table_2/top) & on(dinner_spoon_1, dining_table_2/top) & on(dinner_spoon_2, dining_table_2/top) // on(dinner_bowl_1, dining_table_1/top) & on(dinner_bowl_2, dining_table_1/top) & on(dinner_spoon_1, dining_table_1/top) & on(dinner_spoon_2, dining_table_1/top) |
| 0 | fewer than two bowls or spoons on the table; still held | |

## T19_recycling

- 基础指令 EN：Movie night is over. Put what goes to recycling into the recycling bin.
- 基础指令 中：电影看完了，把该回收的东西放进回收箱。

### T19 · bin_on_bookcase（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：can on the TV stand, cube on the floor, the bin on the bedroom low bookcase

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the can and the cube in the recycling bin | inside(foam_cube, wide_storage_bin) & inside(soda_can, wide_storage_bin) |
| 0 | the can or the cube not in the recycling bin; still held or dropped | |

### T19 · m_can_in_dining_room（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the can was left on the dining table, out of view: search it
- 考察：not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the finished can and the cube in the recycling bin, what is in use or unopened left alone | inside(foam_cube, wide_storage_bin) & inside(soda_can, wide_storage_bin); left in place (10 cm): seat_can |
| 0.3 | inside(foam_cube, wide_storage_bin) & inside(seat_can, wide_storage_bin) & inside(soda_can, wide_storage_bin) | inside(foam_cube, wide_storage_bin) & inside(seat_can, wide_storage_bin) & inside(soda_can, wide_storage_bin) |
| 0 | the can or the cube not in the recycling bin; still held or dropped | |

### T19 · lookalike_bin（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the can was left on the dining table (out of view); a look-alike wide storage bin with toy blocks in it stands on the living-room cabinet by the bedroom door; the recycling bin with a used plastic cup in it is on the bedroom bookcase
- 考察：decoy_destination, item_out_of_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | both in the recycling bin (the one with the used plastic cup) | inside(foam_cube, wide_storage_bin) & inside(soda_can, wide_storage_bin) |
| 0.6 | both in the look-alike toy bin, its blocks untouched | inside(foam_cube, toy_storage_bin) & inside(soda_can, toy_storage_bin) & inside(toy_block_in_bin_1, toy_storage_bin) & inside(toy_block_in_bin_2, toy_storage_bin) |
| 0 | split between the bins; the toy bin's blocks taken out; one left out; still held or dropped | |

### T19 · x6_gd_can_put_away（布局 2 个）

- 指令 EN：Movie night is over. Put what goes to recycling into the recycling bin.
- 指令 中：电影看完了，把该回收的东西放进回收箱。
- 场景：the can was put away in a low kitchen cabinet; on one seed the other cabinet holds an unopened juice bottle (plastic, but full); the cube on the floor

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the finished can and the cube in the recycling bin, what is in use or unopened left alone | inside(foam_cube, wide_storage_bin) & inside(soda_can, wide_storage_bin); left in place (10 cm): full_juice |
| 0.3 | inside(foam_cube, wide_storage_bin) & inside(full_juice, wide_storage_bin) & inside(soda_can, wide_storage_bin) | inside(foam_cube, wide_storage_bin) & inside(full_juice, wide_storage_bin) & inside(soda_can, wide_storage_bin) |
| 0 | the can or the cube not in the recycling bin; still held or dropped | |

## T20_juice_back_to_table

- 基础指令 EN：Someone took the juice bottle off the breakfast table and left it somewhere. Put it back on the dining table, standing up.
- 基础指令 中：有人把早餐桌上的果汁瓶拿走随手放下了。把它放回餐桌上，立着放。

### T20 · bottle_on_cabinet（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the bottle on the low wall cabinet top

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the bottle standing on the breakfast table | upright(juice_bottle); one of: on(juice_bottle, dining_table_2/top) // on(juice_bottle, dining_table_1/top) |
| 0 | the bottle not on the breakfast table; still held or dropped | |

### T20 · m_bottle_on_tv_stand（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the bottle is on the TV stand in the living room, out of the first view: search it
- 考察：not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the breakfast bottle standing on the dining table, the bottle in use and the stock left alone | upright(juice_bottle); one of: on(juice_bottle, dining_table_2/top) // on(juice_bottle, dining_table_1/top) |
| 0.6 | upright(living_juice); one of: on(living_juice, dining_table_2/top) // on(living_juice, dining_table_1/top) | upright(living_juice); one of: on(living_juice, dining_table_2/top) // on(living_juice, dining_table_1/top) |
| 0 | no bottle back on the breakfast table; still held or dropped | |

### T20 · x6_gd_bottle_put_away（布局 2 个）

- 指令 EN：Someone took the juice bottle off the breakfast table and left it somewhere. Put it back on the dining table, standing up.
- 指令 中：有人把早餐桌上的果汁瓶拿走随手放下了。把它放回餐桌上，立着放。
- 场景：the breakfast bottle was put down casually on one top, alone and askew; three new bottles of the same juice stand in a neat row on another
- 考察：referent_clue

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the breakfast bottle standing on the dining table, the bottle in use and the stock left alone | upright(juice_bottle); one of: on(juice_bottle, dining_table_2/top) // on(juice_bottle, dining_table_1/top); left in place (10 cm): stock_juice_1, stock_juice_2, stock_juice_3 |
| 0.6 | another bottle brought instead (the one in use, one from the stock) | upright(juice_bottle); one of: on(stock_juice_1, dining_table_2/top) & upright(stock_juice_1) // on(stock_juice_1, dining_table_1/top) & upright(stock_juice_1) // on(stock_juice_2, dining_table_2/top) & upright(stock_juice_2) // on(stock_juice_2, dining_table_1/top) & upright(stock_juice_2) // ... 2 more ways |
| 0.3 | the stock moved off its place | upright(juice_bottle); one of: on(juice_bottle, dining_table_2/top) // on(juice_bottle, dining_table_1/top) |
| 0 | the bottle not on the breakfast table; still held or dropped | |

## T14_shelve_the_book

- 基础指令 EN：The kid finished reading. Put the book back on his bookcase.
- 基础指令 中：孩子看完书了，帮他把书放回他的书架上。

### T14 · e1_book_ready（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the book already overhangs the desk's front edge: pick it and shelve it

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the book on the kid's bookcase | on_any(book_red, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0]) |
| 0.6 | the book on another bookcase or shelf | on_any(book_red, [bookcase_1/top/bookcase_1/shelf_1/bookcase_1/shelf_0/bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/...]) |
| 0 | the book left on the desk or elsewhere; still held or dropped | |

### T14 · within_kids_reach（布局 2 个）

- 指令 EN：The kid finished reading. Put the book away for him; he wants to read it again tomorrow on his own.
- 指令 中：孩子看完书了，帮他把书收好。他明天还想自己拿来接着看。
- 场景：the red book belongs with its set on a high shelf in the bedroom, out of the kid's reach
- 考察：agent_ability

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the book on a shelf the kid reaches | not on(book_red, large_shelf_4/shelf_4) & not on(book_red, large_shelf_5/shelf_3) & not on_floor(book_red); one of: on(book_red, bookcase_2/top) // on(book_red, bookcase_2/shelf_1) // on(book_red, bookcase_2/shelf_0) // on(book_red, bookcase_3/top) // ... 7 more ways |
| 0.6 | the book back with its set on the high shelf, out of the kid's reach | on_any(book_red, [bookcase_1/top/bookcase_1/shelf_1/bookcase_1/shelf_0/bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/...]) |
| 0 | the book left on the desk, on the floor or elsewhere; still held or dropped | |

### T14 · homework_stays（布局 1 个）

- 指令 EN：The kid finished reading. Tidy up his desk and put each thing where it belongs best; he will go on with his homework tomorrow.
- 指令 中：孩子看完书了，把他的书桌收拾一下，东西都放到最合适的地方。作业他明天还要接着写。
- 场景：the desk holds the finished book, a used mug and the open homework with its pencil
- 考察：category_rule, multi_object_goal

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the book shelved, the mug on a kitchen counter, the homework and its pencil untouched | on_any(book_red, [bookcase_1/top/bookcase_1/shelf_1/bookcase_1/shelf_0/bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/...]) & on_any(desk_mug, [kitchen_counter_1/top/kitchen_counter_2/top]) & upright(desk_mug); left in place (10 cm): homework, hw_pencil |
| 0.6 | the book shelved, the mug in the kitchen but not on a counter (island, stove) | on_any(book_red, [bookcase_1/top/bookcase_1/shelf_1/bookcase_1/shelf_0/bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/...]) & on_any(desk_mug, [kitchen_island/top/kitchen_counter_1/top/kitchen_counter_2/top/kitchen_stove/top]) & upright(desk_mug); left in place (10 cm): homework, hw_pencil |
| 0 | the book or the mug left on the desk; the mug tipped; still held or dropped | |

### T14 · whose_book（布局 3 个）

- 指令 EN：Put the books from the study desk on the shelves with books of the same kind.
- 指令 中：把书房书桌上的书收好，放到摆着同类书的书架上。
- 场景：blue hardcovers stand on the bookcase in the bedroom, paperbacks on the living-room shelf; the desk holds one or both kinds
- 考察：storage_place, referent_clue

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | each book on the shelf with its kind, the shelved books untouched | on_any(blue_book, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0]); left in place (10 cm): blue_shelved_1, blue_shelved_2, paperback_shelved_1, paperback_shelved_2 |
| 0.6 | each book with its kind, but shelved books moved off its place | on_any(blue_book, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0]) |
| 0.3 | the books shelved, but on the other kind's shelf | on_any(blue_book, [bookcase_1/top/bookcase_1/shelf_1/bookcase_1/shelf_0/bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/...]) |
| 0 | a book left on the desk or elsewhere; still held or dropped | |

### T14 · next_in_series（布局 3 个）

- 指令 EN：The kid finished the red book. Put it back on his bookcase, and bring the other book of the same set to his desk for tomorrow.
- 指令 中：孩子看完这本红书了，收回他的书架，再把同一套的另一本拿到书桌上，他明天看。
- 场景：the set is told by its red cover; the other book stands among books of other covers, on the kid's bookcase or another shelf in the bedroom
- 考察：referent_clue, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the red book back on his bookcase, the other red one on the desk, the other books untouched | on(red_book_2, desk_1/top) & on_any(book_red, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0]); left in place (10 cm): blue_book_case, paperback_shelf |
| 0.6 | the right book on the desk, but the red one on another shelf or other books moved off its place | on(red_book_2, desk_1/top) & on_any(book_red, [bookcase_1/top/bookcase_1/shelf_1/bookcase_1/shelf_0/bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/...]) |
| 0.3 | the red one shelved, but a book of another cover brought to the desk | on_any(book_red, [bookcase_1/top/bookcase_1/shelf_1/bookcase_1/shelf_0/bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/...]); one of: on(blue_book_case, desk_1/top) // on(green_book_case, desk_1/top) // on(paperback_shelf, desk_1/top) |
| 0 | the next book not brought (none on the desk); the red book left out; still held or dropped | |

## T21_bring_tissues

- 基础指令 EN：Some soup got spilled at the dining table. Bring the tissues there and leave them on the table.
- 基础指令 中：餐桌上洒了点汤，把纸巾拿过去放在桌上。

### T21 · tissue_on_tv_stand（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the tissue box on the TV stand, a bowl of soup on the dining table

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the tissues on the dining table | one of: on(tissue, dining_table_2/top) // on(tissue, dining_table_1/top) |
| 0 | nothing to wipe with on the table; still held or dropped | |

### T21 · which_table（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：two dining tables; a bowl of soup stands on one of them, the other is bare
- 考察：destination_unnamed

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the tissues on the table with the soup | on(tissue, dining_table_2/top) |
| 0.3 | on(tissue, dining_table_1/top) | on(tissue, dining_table_1/top) |
| 0 | the tissues on the bare table; nothing to wipe with on the table; still held or dropped | |

### T21 · no_tissue（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：there are no tissues in the house; a dry kitchen sponge lies on the island
- 考察：resource_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | one of: on(spare_sponge, dining_table_2/top) // on(spare_sponge, dining_table_1/top) | one of: on(spare_sponge, dining_table_2/top) // on(spare_sponge, dining_table_1/top) |
| 0 | nothing to wipe with on the table; still held or dropped | |

### T21 · the_kids_side（布局 2 个）

- 指令 EN：The kid spilled some soup at the dining table. Bring the tissues there and put them on the kid's side of the table.
- 指令 中：孩子吃饭把汤洒了，把纸巾拿过去，放在孩子那一边。
- 场景：two places at the table: the kid's (a plastic cup) and a grown-up's (a mug)
- 考察：referent_clue

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the tissues on the kid's side | near_any(tissue, [kid_bowl/kid_cup], 0.15) & not near_any(tissue, [adult_bowl/adult_mug], 0.25) & on(tissue, dining_table_2/top) |
| 0.6 | on the table, between the two places (by no one) | not near_any(tissue, [adult_bowl/adult_mug], 0.25) & on(tissue, dining_table_2/top) |
| 0.3 | on the table, on the grown-up's side | on(tissue, dining_table_2/top) |
| 0 | the tissues not on the table; still held or dropped | |

## T22_put_away_shopping

- 基础指令 EN：I just got back from the shop and left the shopping on the dining table. Please put it away in the kitchen.
- 基础指令 中：我刚买东西回来，放在餐桌上了，帮我收到厨房里。

### T22 · juice_on_table（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：a bottle of juice from the shop on the dining table

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the juice standing in the fridge, a cabinet or on a counter | on_any(bought_juice, [breakfast_fridge/inside_shelf/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(bought_juice) |
| 0 | an item left on the table or not put away; the juice lying; still held or dropped | |

### T22 · by_kind（布局 1 个）

- 指令 EN：I just got back from the shop; the juice, an apple and some snacks are on the dining table. Put each where things of its kind are kept, and close any door you open.
- 指令 中：我刚买东西回来，果汁、苹果和零食都在餐桌上。每样都收到平时放同类东西的地方，开过的门记得关上。
- 场景：juice, an apple and a box of snacks on the table; the fruit basket is on the island, the snacks are kept in the low wall cabinet (an opened box is already there)
- 考察：storage_place, multi_object_goal

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | apple in the fruit basket, the snacks in the cabinet with the opened box, the juice away | inside(bought_apple, home_basket) & on(bought_snack, kitchen_cabinet_6/inside_shelf) & on_any(bought_juice, [breakfast_fridge/inside_shelf/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(bought_juice) |
| 0.6 | each in a kitchen storage place but not with its kind (the apple in a cabinet, the snacks in the basket or the other cabinet) | on_any(bought_juice, [breakfast_fridge/inside_shelf/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(bought_juice); one of: inside(bought_apple, home_basket) & inside(bought_snack, home_basket) // inside(bought_apple, home_basket) & on(bought_snack, kitchen_cabinet_4/inside_shelf) // on(bought_apple, kitchen_cabinet_6/inside_shelf) & inside(bought_snack, home_basket) // on(bought_apple, kitchen_cabinet_6/inside_shelf) & on(bought_snack, kitchen_cabinet_6/inside_shelf) // ... 4 more ways |
| 0 | an item left on the table or not put away; the juice lying; still held or dropped | |

### T22 · eat_now（布局 2 个）

- 指令 EN：I just got back from the shop and left the shopping on the dining table. Please put it away. The kid says he wants the snacks now; he is doing homework in the study.
- 指令 中：我刚买东西回来，放在餐桌上了，帮我收好。孩子说零食现在就要吃，他在书房写作业。
- 场景：juice and a box of snacks; the kid doing homework in the study wants the snacks now; on one seed his homework covers the desk but for one small corner
- 考察：preference_allocation

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the snacks on his desk where they leave his homework as it is (the free corner when the homework covers the desk), the juice away | on(bought_snack, desk_1/top) & on_any(bought_juice, [breakfast_fridge/inside_shelf/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(bought_juice) |
| 0.6 | the snacks on top of his homework, or put away in the kitchen (he wanted them now) | on_any(bought_juice, [breakfast_fridge/inside_shelf/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf/kitchen_counter_1/top/kitchen_counter_2/top]) & on_any(bought_snack, [breakfast_fridge/inside_shelf/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf/kitchen_counter_1/top/kitchen_counter_2/top/kitchen_island/top]) & upright(bought_juice) |
| 0 | the snacks left on the dining table; the juice not put away or lying; still held or dropped | |

### T22 · not_shopping（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the juice from the shop, and the kid's toy car and picture book on the same table
- 考察：goal_items_unstated

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the juice away, the kid's car and book left on the table | on_any(bought_juice, [breakfast_fridge/inside_shelf/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(bought_juice); left in place (10 cm): table_book, table_car |
| 0.6 | the juice away, but the kid's car or book moved too (not shopping) | on_any(bought_juice, [breakfast_fridge/inside_shelf/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(bought_juice) |
| 0 | an item left on the table or not put away; the juice lying; still held or dropped | |

### T22 · two_spots（布局 1 个）

- 指令 EN：I just got back from the shop with two bags and unpacked them in two different places. Put everything I bought away.
- 指令 中：我刚买东西回来，两袋东西拆开放在了两个不同的地方，买的东西都帮我收好。
- 场景：the juice on the dining table; a second bag was emptied on the island: an apple and a box of snacks there, the basket next to them
- 考察：goal_items_unstated, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | apple in the fruit basket, the snacks in the cabinet with the opened box, the juice away | inside(bought_apple, home_basket) & on(bought_snack, kitchen_cabinet_6/inside_shelf) & on_any(bought_juice, [breakfast_fridge/inside_shelf/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(bought_juice) |
| 0.6 | each in a kitchen storage place but not with its kind (the apple in a cabinet, the snacks in the basket or the other cabinet) | on_any(bought_juice, [breakfast_fridge/inside_shelf/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(bought_juice); one of: inside(bought_apple, home_basket) & inside(bought_snack, home_basket) // inside(bought_apple, home_basket) & on(bought_snack, kitchen_cabinet_4/inside_shelf) // on(bought_apple, kitchen_cabinet_6/inside_shelf) & inside(bought_snack, home_basket) // on(bought_apple, kitchen_cabinet_6/inside_shelf) & on(bought_snack, kitchen_cabinet_6/inside_shelf) // ... 4 more ways |
| 0 | an item left on the table or not put away; the juice lying; still held or dropped | |

### T22 · tray_elsewhere（布局 3 个）

- 指令 EN：I just got back from the shop and left the juice and an apple on the dining table. Put them away; fruit usually goes in the fruit basket.
- 指令 中：我刚买东西回来，果汁和苹果放在餐桌上了，帮我收好。水果平时放在果篮里。
- 场景：juice and an apple on the dining table; no fruit basket; a serving tray on the table in the west dining room: with an orange in it, or with four books lying flat over its floor
- 考察：container_absent, not_in_view, destination_full, dependent_decisions

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | not on_floor(west_tray) & on_any(bought_juice, [breakfast_fridge/inside_shelf/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(bought_juice); one of: fully_inside(bought_apple, west_tray) // on_any(bought_apple, [breakfast_fridge/inside_shelf/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf]) | not on_floor(west_tray) & on_any(bought_juice, [breakfast_fridge/inside_shelf/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf/kitchen_counter_1/top/kitchen_counter_2/top]) & upright(bought_juice); one of: fully_inside(bought_apple, west_tray) // on_any(bought_apple, [breakfast_fridge/inside_shelf/kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf]) |
| 0 | an item left on the table or not put away; the juice lying; still held or dropped | |

## T23_pick_up_dropped

- 基础指令 EN：Something fell on the floor. Please pick it up and put it where it belongs.
- 基础指令 中：地上掉了东西，帮忙捡起来放好。

### T23 · spoon_on_floor（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：a spoon on the kitchen floor; the spoons are kept on the kitchen counter

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the spoon on a kitchen counter or the island | on_any(dropped_spoon, [kitchen_counter_2/top/kitchen_counter_1/top/kitchen_island/top]) |
| 0 | a dropped thing left on the floor or put in a wrong kind of place; still held | |

### T23 · by_kind（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：a spoon and a toy block on the kitchen floor; the kid's toys are kept in the toy box, or in a small bin already full of blocks
- 考察：storage_place, multi_object_goal

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the spoon to the kitchen, the block with the toys: the toy box, or the tray beside the full toy bin | inside(dropped_block, toy_box) & on_any(dropped_spoon, [kitchen_counter_2/top/kitchen_counter_1/top/kitchen_island/top]) |
| 0.6 | the blocks taken out of the full bin to fit this one | not on_floor(dropped_block) & on_any(dropped_spoon, [kitchen_counter_2/top/kitchen_counter_1/top/kitchen_island/top]) |
| 0 | a dropped thing left on the floor; still held | |

### T23 · belongs_on_floor（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the kid's toy block fell on the kitchen floor beside the waste bin and the laundry basket, which live on the floor; no toy box, or his toy bin full
- 考察：goal_items_unstated, container_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | inside(dropped_block, spare_tray) & on_floor(kitchen_bin) & on_floor(laundry_basket); left in place (10 cm): kitchen_bin, laundry_basket | inside(dropped_block, spare_tray) & on_floor(kitchen_bin) & on_floor(laundry_basket); left in place (10 cm): kitchen_bin, laundry_basket |
| 0.6 | the bin or the basket moved off its place; or the blocks taken out of the full bin to fit this one | inside(dropped_block, spare_tray); one of: on_floor(kitchen_bin) & on_floor(laundry_basket); left in place (10 cm): kitchen_bin, laundry_basket |
| 0.3 | the block in the laundry basket, or the bin or the basket lifted off the floor | one of: inside(dropped_block, spare_tray) // inside(dropped_block, laundry_basket) & on_floor(kitchen_bin) & on_floor(laundry_basket) // inside(dropped_block, laundry_basket); left in place (10 cm): kitchen_bin, laundry_basket |
| 0 | the block left on the floor or not in a container; still held | |

### T23 · dropped_out_of_view（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the dropped thing slid into the dining room next door, out of view; the small kitchen's counter is covered with dishes (no room; or only room for small things)
- 考察：not_in_view, storage_place

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | on_any(dropped_spoon, [kitchen_counter_1/top/kitchen_island/top]) | on_any(dropped_spoon, [kitchen_counter_1/top/kitchen_island/top]) |
| 0.6 | on the small kitchen's counter after moving dishes to make room | clear_of(dropped_spoon, [counter_bowl_1/counter_bowl_10/counter_bowl_2/counter_bowl_3/counter_bowl_4/counter_bowl_5/...], 0.0) & on(dropped_spoon, kitchen_counter_2/top) |
| 0.3 | on the counter on top of the dishes | on(dropped_spoon, kitchen_counter_2/top) |
| 0 | not found; left on the floor; still held or dropped | |

### T23 · only_this_room（布局 2 个）

- 指令 EN：Something fell on the kitchen floor. Please pick it up and put it where it belongs.
- 指令 中：厨房地上掉了东西，帮忙捡起来放好。
- 场景：the kid's plastic cup on the kitchen floor (his cups are kept on low cabinet 4), the kid's toy car on the living-room floor
- 考察：referent_clue, storage_place

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the cup with his cups in cabinet 4 -- or, the cabinet full, in the other low cabinet or on a worktop;, the car left | on(dropped_cup, kitchen_cabinet_4/top); left in place (10 cm): living_car |
| 0.6 | the cup elsewhere in the kitchen though his cabinet has room; or squeezed into the full cabinet | one of: on_any(dropped_cup, [kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf/kitchen_cabinet_6/top]) // on_any(dropped_cup, [kitchen_counter_2/top/kitchen_counter_1/top/kitchen_island/top]); left in place (10 cm): living_car |
| 0.3 | the living-room car picked up too (not in the kitchen) | one of: on(dropped_cup, kitchen_cabinet_4/top) // on_any(dropped_cup, [kitchen_cabinet_4/inside_shelf/kitchen_cabinet_6/inside_shelf/kitchen_cabinet_6/top]) // on_any(dropped_cup, [kitchen_counter_2/top/kitchen_counter_1/top/kitchen_island/top]) |
| 0 | the cup left on the floor or out of the kitchen's places; still held | |

### T23 · dropped_in_two_rooms（布局 2 个）

- 指令 EN：Some things fell on the floor around the house. Please pick them up and put them where they belong.
- 指令 中：家里地上掉了些东西，帮忙捡起来放好。
- 场景：a spoon on the kitchen floor, and the kid's teddy bear on the study floor; his bookcase in the bedroom has room, or is full on every level
- 考察：goal_items_unstated, not_in_view, storage_place

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the spoon to the kitchen, the book on his bookcase -- or, the bookcase full, on another bookcase or a desk, his books left as they are | on_any(dropped_bear, [bookcase_2/shelf_0/bookcase_2/shelf_1/bookcase_2/top/mattress_1/top]) & on_any(dropped_spoon, [kitchen_counter_2/top/kitchen_counter_1/top/kitchen_island/top]) |
| 0.6 | the book on another bookcase or a desk though his has room; or pushed into his full bookcase | on_any(dropped_bear, [bookcase_1/shelf_0/bookcase_1/shelf_1/bookcase_1/top/bookcase_3/shelf_0/bookcase_3/shelf_1/bookcase_3/top/...]) & on_any(dropped_spoon, [kitchen_counter_2/top/kitchen_counter_1/top/kitchen_island/top]) |
| 0.3 | the book off the floor but on a table or a kitchen top | not on_floor(dropped_bear) & on_any(dropped_spoon, [kitchen_counter_2/top/kitchen_counter_1/top/kitchen_island/top]) |
| 0 | a dropped thing left on the floor; still held | |

## T24_snack_for_kid

- 基础指令 EN：The kid is doing homework at the study desk and is hungry. Bring him something to eat and put it on his desk.
- 基础指令 中：孩子在书房书桌写作业饿了，给他拿点吃的，放到他书桌上。

### T24 · apple_on_table（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：an apple on the dining table, the kid's homework on the study desk

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the apple on the study desk | on(snack_apple, desk_1/top) |
| 0 | nothing to eat on the kid's desk; still held or dropped | |

### T24 · no_apples_for_him（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：an apple on the dining table: free, or on someone's plate at a place where someone is eating
- 考察：resource_in_use

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | something nobody is eating on the desk: the apple when free, else the banana from the basket, someone's plate left alone | on(snack_apple, desk_1/top) |
| 0.6 | on(snack_banana, desk_1/top) | on(snack_banana, desk_1/top) |
| 0 | nothing to eat on the kid's desk; still held or dropped | |

### T24 · dinner_soon（布局 2 个）

- 指令 EN：The kid is doing homework at the study desk and is hungry. Bring him something to eat and put it on his desk; dinner is in half an hour.
- 指令 中：孩子在书房书桌写作业饿了，给他拿点吃的放到他书桌上。还有半小时就吃晚饭了。
- 场景：a fruit and a box of snacks on the table; dinner is in half an hour
- 考察：preference_allocation

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the fruit on the desk, not the snacks | not on(snack_box, desk_1/top) & on(snack_apple, desk_1/top) |
| 0.6 | the fruit and the snacks | on(snack_apple, desk_1/top) |
| 0.3 | the snacks only (dinner in half an hour) | on(snack_box, desk_1/top) |
| 0 | nothing to eat on the kid's desk; still held or dropped | |

### T24 · fruit_out_of_view（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：no food on the dining table; the fruit basket is on the bedroom bookcase, with an apple in it or empty
- 考察：not_in_view, resource_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the fruit found (the apple in the basket, else the banana) on the desk | on(snack_apple, desk_1/top) |
| 0.6 | the empty fruit basket brought instead | on(home_basket, desk_1/top) |
| 0 | nothing to eat on the kid's desk; still held or dropped | |

### T24 · where_is_he（布局 2 个）

- 指令 EN：The kid is doing homework and is hungry. Bring him something to eat and put it on the desk where he is doing his homework.
- 指令 中：孩子写作业饿了，给他拿点吃的，放到他写作业的那张书桌上。
- 场景：the kid's open homework lies on one of two desks; the instruction does not say which room
- 考察：referent_clue

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the snack on the desk with the homework | on(snack_apple, desk_1/top) |
| 0.3 | on_any(snack_apple, [desk_3/top/bookcase_4/top]) | on_any(snack_apple, [desk_3/top/bookcase_4/top]) |
| 0 | on the other desk; nothing to eat on the kid's desk; still held or dropped | |

### T24 · two_kids（布局 3 个）

- 指令 EN：The kids are doing homework and are hungry. Bring them something to eat: one thing for each, put by their homework.
- 指令 中：孩子们在写作业，饿了，给他们拿点吃的：每人一样，放在各自的作业旁边。
- 场景：two kids' homework, on the study desk and on the bedroom desk; two things to eat on the table (two fruits, or one fruit and a box of snacks); the bedroom desk may be all homework
- 考察：count_from_scene, multi_object_goal

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | one thing to eat by each kid's homework, not on it: on his desk, or on the bookcase beside a desk that has no room | one of: on(snack_apple, desk_1/top) & clear_of(snack_apple, [homework], 0.0) & on(snack_banana, desk_3/top) & clear_of(snack_banana, [homework_3], 0.0) // on(snack_banana, desk_1/top) & clear_of(snack_banana, [homework], 0.0) & on(snack_apple, desk_3/top) & clear_of(snack_apple, [homework_3], 0.0) |
| 0.6 | one of them set on the homework, or on the bookcase beside a desk with room | one of: on(snack_apple, desk_1/top) & clear_of(snack_apple, [homework], 0.0) & on(snack_banana, bookcase_4/top) // on(snack_apple, desk_1/top) & clear_of(snack_apple, [homework], 0.0) & on(snack_banana, desk_3/top) // on(snack_apple, desk_1/top) & on(snack_banana, desk_3/top) & clear_of(snack_banana, [homework_3], 0.0) // on(snack_banana, desk_1/top) & clear_of(snack_banana, [homework], 0.0) & on(snack_apple, bookcase_4/top) // ... 2 more ways |
| 0.3 | both a step down, or both to the same kid | one of: on(snack_apple, desk_1/top) & on(snack_banana, bookcase_4/top) // on(snack_apple, desk_1/top) & on(snack_banana, desk_3/top) // on(snack_banana, desk_1/top) & on(snack_apple, bookcase_4/top) // on(snack_banana, desk_1/top) & on(snack_apple, desk_3/top) // ... 2 more ways |
| 0 | a kid gets nothing and a thing left on the table; still held or dropped | |

## T25_drink_for_guest

- 基础指令 EN：A guest is sitting in the living room. Bring him the juice and a cup, and put them on the TV stand in front of him.
- 基础指令 中：客人在客厅坐着，给他拿果汁和一个杯子，放到他面前的电视柜上。

### T25 · drink_on_island（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：a bottle of juice and a cup on the kitchen island; the guest sits in the living room

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the juice and a cup (or a mug) by the guest | upright(guest_juice); one of: on(guest_juice, tv_stand_2/top) & count_on_at_least([guest_cup/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], tv_stand_2/top, 1) // on(guest_juice, tv_stand_1/top) & count_on_at_least([guest_cup/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], tv_stand_1/top, 1) |
| 0 | no drink or no cup by the guest; the juice lying; still held or dropped | |

### T25 · cup_elsewhere（布局 3 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the juice on the island, no cup there; a cup on the kitchen counter in the small kitchen (maybe holding the kid's blocks), or no ordinary cup at all; mugs in the dining room
- 考察：not_in_view, resource_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the juice and a cup fit to drink from by the guest: the counter's cup, or a mug when the only cup holds the kid's blocks (that cup left alone) | upright(guest_juice); one of: on(guest_juice, tv_stand_2/top) & count_on_at_least([cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/mug_counter], tv_stand_2/top, 1) // on(guest_juice, tv_stand_1/top) & count_on_at_least([cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/mug_counter], tv_stand_1/top, 1) |
| 0 | no drink or no cup by the guest; the juice lying; still held or dropped | |

### T25 · cold_one（布局 2 个）

- 指令 EN：It's a hot day. A guest is sitting in the living room; bring him something to drink and a cup, and put them on the TV stand in front of him.
- 指令 中：天很热，客人在客厅坐着，给他拿点喝的和一个杯子，放到他面前的电视柜上。
- 场景：a bottle on the island at room temperature; in the fridge another juice or (no juice) a can of soda; it is a hot day
- 考察：preference_allocation, resource_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the cold juice from the fridge and a cup by the guest, the warm bottle left | upright(cold_juice); one of: on(cold_juice, tv_stand_2/top) & count_on_at_least([guest_cup/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], tv_stand_2/top, 1) // on(cold_juice, tv_stand_1/top) & count_on_at_least([guest_cup/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], tv_stand_1/top, 1) |
| 0.6 | the room-temperature bottle brought on a hot day | upright(guest_juice); one of: on(guest_juice, tv_stand_2/top) & count_on_at_least([guest_cup/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], tv_stand_2/top, 1) // on(guest_juice, tv_stand_1/top) & count_on_at_least([guest_cup/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], tv_stand_1/top, 1) |
| 0 | no drink or no cup by the guest; the juice lying; still held or dropped | |

### T25 · drink_in_fridge（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：a cup on the island, nothing to drink out; the juice (or, no juice, a can of soda) is in the fridge
- 考察：storage_place, not_in_view, resource_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the juice from the fridge and a cup by the guest | upright(cold_juice); one of: on(cold_juice, tv_stand_2/top) & count_on_at_least([guest_cup/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], tv_stand_2/top, 1) // on(cold_juice, tv_stand_1/top) & count_on_at_least([guest_cup/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], tv_stand_1/top, 1) |
| 0.6 | upright(cold_soda); one of: on(cold_soda, tv_stand_2/top) & count_on_at_least([guest_cup/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], tv_stand_2/top, 1) // on(cold_soda, tv_stand_1/top) & count_on_at_least([guest_cup/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], tv_stand_1/top, 1) | upright(cold_soda); one of: on(cold_soda, tv_stand_2/top) & count_on_at_least([guest_cup/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], tv_stand_2/top, 1) // on(cold_soda, tv_stand_1/top) & count_on_at_least([guest_cup/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], tv_stand_1/top, 1) |
| 0 | no drink or no cup by the guest; the juice lying; still held or dropped | |

### T25 · cups_for_two（布局 4 个）

- 指令 EN：Two guests are sitting in the living room. Get the drink and the cups ready for them, one cup each, ordinary cups where possible; what is already on their table need not be brought again.
- 指令 中：两位客人在客厅，给他们准备好饮料和杯子，每人一个杯子，尽量用普通杯子；桌上已有的不用重复拿。
- 场景：two guests; the juice on the island; by the guests none, one or two cups; on the small kitchen's counter one or two cups; the house's only other cups are mugs in the dining room
- 考察：count_from_scene, not_in_view, resource_absent, dependent_decisions

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | two plain cups by the guests in all (the ones there kept), none extra | count_on_at_least([tv_cup_1/stock_cup_1/mug_dining_cabinet/mug_shelf/mug_counter], tv_stand_2/top, 2) & count_on_at_least([tv_cup_1/stock_cup_1], tv_stand_2/top, 2) & count_on_at_most([tv_cup_1/stock_cup_1/mug_dining_cabinet/mug_shelf/mug_counter], tv_stand_2/top, 2) & on(guest_juice, tv_stand_2/top) & upright(guest_juice) |
| 0.6 | two in all, but a mug used though a plain cup was on the kitchen counter (user 11-12), or the cups already there moved | count_on_at_least([tv_cup_1/stock_cup_1/mug_dining_cabinet/mug_shelf/mug_counter], tv_stand_2/top, 2) & count_on_at_most([tv_cup_1/stock_cup_1/mug_dining_cabinet/mug_shelf/mug_counter], tv_stand_2/top, 2) & on(guest_juice, tv_stand_2/top) & upright(guest_juice) |
| 0 | fewer than two cups; no juice; the juice lying; still held or dropped | |

### T25 · two_guests（布局 2 个）

- 指令 EN：Two guests are sitting in the living room. Bring them the juice and a cup each, and put them on the TV stand in front of them.
- 指令 中：两位客人在客厅坐着，给他们拿果汁，每人一个杯子，放到他们面前的电视柜上。
- 场景：two guests; one bottle of juice and two cups on the island, or one cup and no other ordinary cup
- 考察：count_from_scene, multi_object_goal, resource_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the juice and two cups by the guests | upright(guest_juice); one of: on(guest_juice, tv_stand_2/top) & count_on_at_least([guest_cup/guest_cup_2/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/...], tv_stand_2/top, 2) // on(guest_juice, tv_stand_1/top) & count_on_at_least([guest_cup/guest_cup_2/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/...], tv_stand_1/top, 2) |
| 0 | only one cup; no drink or no cup by the guest; the juice lying; still held or dropped | |

### T25 · little_guest（布局 1 个）

- 指令 EN：A little girl is visiting and sitting in the living room. Bring her some juice and a cup, and put them on the TV stand in front of her.
- 指令 中：来了个小朋友，在客厅坐着，给她拿果汁和一个杯子，放到她面前的电视柜上。
- 场景：the guest is a small child; a china cup and a plastic cup on the island
- 考察：preference_allocation

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the juice and the plastic cup for the child | upright(guest_juice); one of: on(guest_juice, tv_stand_2/top) & count_on_at_least([kid_cup], tv_stand_2/top, 1) // on(guest_juice, tv_stand_1/top) & count_on_at_least([kid_cup], tv_stand_1/top, 1); left in place (10 cm): guest_cup |
| 0.6 | the plastic cup, and the china cup brought too | upright(guest_juice); one of: on(guest_juice, tv_stand_2/top) & count_on_at_least([kid_cup], tv_stand_2/top, 1) // on(guest_juice, tv_stand_1/top) & count_on_at_least([kid_cup], tv_stand_1/top, 1) |
| 0.3 | the china cup only (breakable, for a small child) | upright(guest_juice); one of: on(guest_juice, tv_stand_2/top) & on(guest_cup, tv_stand_2/top) // on(guest_juice, tv_stand_1/top) & on(guest_cup, tv_stand_1/top) |
| 0 | no drink or no cup by the guest; the juice lying; still held or dropped | |

## T26_kids_things_to_room

- 基础指令 EN：Take the things the kid left in the living room back to his room: toys into his toy basket, books onto his bookcase.
- 基础指令 中：把孩子落在客厅的东西拿回他房间：玩具放进他的玩具筐，书放到他的书架上。

### T26 · car_in_living_room（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the kid's toy car on the living-room floor; his toy basket is in his bedroom

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the car in his toy basket | inside(living_car, kids_basket) |
| 0 | a thing of his left in the living room or put elsewhere; still held or dropped | |

### T26 · whose（布局 2 个）

- 指令 EN：Take the things the kid left in the living room back to his room.
- 指令 中：把孩子落在客厅的东西拿回他房间。
- 场景：a picture book like the ones on the kid's bookcase and a grown-up's novel on the TV stand; his bookcase may be full
- 考察：referent_clue, storage_place

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | his picture book to his bookcase (the one by his bed when his is full), the novel left | on_any(kid_book, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0]); left in place (10 cm): adult_novel |
| 0.6 | his book in his room but not on a bookcase, or the books on the full one moved, or the grown-up's novel taken too | on_any(kid_book, [bookcase_3/top/bookcase_3/shelf_1/bookcase_3/shelf_0]); left in place (10 cm): adult_novel |
| 0.3 | two of those slips | one of: on_any(kid_book, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0]) // on_any(kid_book, [bookcase_3/top/bookcase_3/shelf_1/bookcase_3/shelf_0]) |
| 0 | a thing of his left in the living room or put elsewhere; still held or dropped | |

### T26 · scattered（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the car on the floor, the duck on the TV stand, a block on the island; his toys kept in the basket, or (no basket) in a small bin
- 考察：goal_items_unstated, multi_object_goal, container_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | all three in what holds his toys (the basket; or, no basket, his toy bin) | inside(living_block, kids_basket) & inside(living_car, kids_basket) & inside(living_duck, kids_basket) |
| 0.6 | inside(living_block, kids_toy_bin) & inside(living_car, kids_toy_bin) & inside(living_duck, kids_toy_bin) | inside(living_block, kids_toy_bin) & inside(living_car, kids_toy_bin) & inside(living_duck, kids_toy_bin) |
| 0.3 | on_any(living_block, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/bookcase_3/top/bookcase_3/shelf_1/bookcase_3/shelf_0/...]) & on_any(living_car, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/bookcase_3/top/bookcase_3/shelf_1/bookcase_3/shelf_0/...]) & on_any(living_duck, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/bookcase_3/top/bookcase_3/shelf_1/bookcase_3/shelf_0/...]) | on_any(living_block, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/bookcase_3/top/bookcase_3/shelf_1/bookcase_3/shelf_0/...]) & on_any(living_car, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/bookcase_3/top/bookcase_3/shelf_1/bookcase_3/shelf_0/...]) & on_any(living_duck, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/bookcase_3/top/bookcase_3/shelf_1/bookcase_3/shelf_0/...]) |
| 0 | a thing of his left in the living room or put elsewhere; still held or dropped | |

### T26 · where_in_room（布局 2 个）

- 指令 EN：Take the things the kid left in the living room back to his room.
- 指令 中：把孩子落在客厅的东西拿回他房间。
- 场景：the car and one of his picture books in the living room; in his room the toy basket, or only a waste bin on the floor
- 考察：storage_place, multi_object_goal, container_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the car in the toy basket (no basket: onto his bookcase), the book on his bookcase | inside(living_car, kids_basket) & on_any(kid_book, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/bookcase_3/top/bookcase_3/shelf_1/bookcase_3/shelf_0]) |
| 0.6 | one of them in the wrong spot in his room (the car on a shelf with the basket there, the book in the basket or on other furniture) | one of: inside(living_car, kids_basket) & inside(kid_book, kids_basket) // on_any(living_car, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/bookcase_3/top/bookcase_3/shelf_1/bookcase_3/shelf_0]) & on_any(kid_book, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/bookcase_3/top/bookcase_3/shelf_1/bookcase_3/shelf_0]) |
| 0.3 | both a step down, or one into the waste bin | inside(kid_book, kids_basket) & on_any(living_car, [bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0/bookcase_3/top/bookcase_3/shelf_1/bookcase_3/shelf_0]) |
| 0 | a thing of his left in the living room or put elsewhere; still held or dropped | |

### T26 · bear_to_bed（布局 2 个）

- 指令 EN：The kid is going to bed. Take the things he left in the living room back to his room.
- 指令 中：孩子要睡觉了，把他落在客厅的东西拿回他房间。
- 场景：his teddy bear on the TV stand; it is bedtime; the top of the bookcase by his bed free or covered
- 考察：storage_place

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the teddy on his bed or the bookcase by it (a lower level when its top is covered) | on_any(living_bear, [mattress_1/top/bookcase_3/top]) |
| 0.6 | the teddy in the toy basket, on his other bookcase, or the books on the top moved | one of: on_any(living_bear, [bookcase_3/shelf_1/bookcase_3/shelf_0/bookcase_2/top/bookcase_2/shelf_1/bookcase_2/shelf_0]) // inside(living_bear, kids_basket) |
| 0 | a thing of his left in the living room or put elsewhere; still held or dropped | |

### T26 · two_bedrooms（布局 2 个）

- 指令 EN：Take the things the kid left in the living room back to his room.
- 指令 中：把孩子落在客厅的东西拿回他房间。
- 场景：two bedrooms; his is the one with the toy basket
- 考察：referent_clue, not_in_view

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the car in the basket in his room | inside(living_car, kids_basket) |
| 0.3 | in_room(living_car, bedroom_0_0) | in_room(living_car, bedroom_0_0) |
| 0 | the other bedroom; a thing of his left in the living room or put elsewhere; still held or dropped | |

## T27_leftovers_to_fridge

- 基础指令 EN：Dinner is over. Put the leftovers in the fridge.
- 基础指令 中：晚饭吃完了，把剩菜收进冰箱。

### T27 · rice_on_table（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：a glass box of leftover rice on the dining table

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | every leftover in the fridge | on(leftover_rice, breakfast_fridge/inside_shelf) |
| 0 | a leftover not in the fridge; a dish tipped; still held or dropped | |

### T27 · which_is_leftover（布局 3 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the box of rice and an empty takeout tray on the table
- 考察：disposal_by_state

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | only the rice in the fridge, the rest left (empty tray, fruit and cereal, the bowl someone eats from) | not on(empty_tray, breakfast_fridge/inside_shelf) & on(leftover_rice, breakfast_fridge/inside_shelf) |
| 0.6 | the rice in the fridge, but something that is not a leftover moved or put in too | on(leftover_rice, breakfast_fridge/inside_shelf) |
| 0 | a leftover not in the fridge; a dish tipped; still held or dropped; the bowl someone eats from tipped | |

### T27 · two_leftovers（布局 3 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the box of rice on the table, and soup: left over in a lunch box on the table or the stove, or a pot still being eaten from at a place
- 考察：goal_items_unstated, multi_object_goal

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the leftovers in the fridge (the soup too, unless someone is eating it) | on(leftover_rice, breakfast_fridge/inside_shelf); left in place (10 cm): eating_bowl, leftover_soup |
| 0.6 | the soup taken from someone eating | on(leftover_rice, breakfast_fridge/inside_shelf) |
| 0 | a leftover not in the fridge; tipped; still held or dropped | |

### T27 · fridge_out_of_view（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the robot starts in the dining room; the fridge stands in the open kitchen, out of view; its shelf free, or half taken by what is stored there
- 考察：not_in_view, storage_place

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the rice in the fridge's free part, the stored food left | on(leftover_rice, breakfast_fridge/inside_shelf) |
| 0 | the rice not in the fridge; tipped; still held or dropped | |

## T28_cup_to_bedside

- 基础指令 EN：The kid is going to bed. Bring his cup to his bedside and leave it standing up.
- 基础指令 中：孩子要睡了，把他的水杯拿到床边，立着放好。

### T28 · cup_on_counter（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the kid's plastic cup on the kitchen counter; his bed has the teddy bear on it

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | his cup standing by his bed | on_any(kid_cup, [bookcase_3/top/desk_1/top]) & upright(kid_cup) |
| 0 | the cup not by his bed; the cup lying; still held or dropped | |

### T28 · which_bed（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：two bedrooms with a bed each; his teddy bear lies on his
- 考察：referent_clue

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | his cup by the bed with his teddy | on_any(kid_cup, [bookcase_3/top/desk_1/top]) & upright(kid_cup) |
| 0.3 | on(kid_cup, cell_shelf_2/top) & upright(kid_cup) | on(kid_cup, cell_shelf_2/top) & upright(kid_cup) |
| 0 | the other bed; the cup not by his bed; the cup lying; still held or dropped | |

### T28 · where_his_cup_is（布局 3 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：on the counter a china cup and a mug, and his plastic cup with them, or not (then it is in the low cabinet)
- 考察：referent_clue, item_put_away, dependent_decisions, resource_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | his cup by his bed (with no cup of his, a cup of the house), the rest left | on_any(kid_cup, [bookcase_3/top/desk_1/top]) & upright(kid_cup) |
| 0.6 | a cup that is not his though his is there | one of: on_any(cup_counter_b, [bookcase_3/top/desk_1/top]) & upright(cup_counter_b) // on_any(counter_mug, [bookcase_3/top/desk_1/top]) & upright(counter_mug) |
| 0 | no cup by his bed; lying; still held or dropped | |

### T28 · cup_out_of_view（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the cup was left on the dining table, out of view; the bookcase top by his bed free or covered
- 考察：not_in_view, storage_place

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | his cup found and by his bed (a lower level or the desk when the top is covered) | on_any(kid_cup, [bookcase_3/top]) & upright(kid_cup) |
| 0.6 | the books on the top moved to make room | on_any(kid_cup, [bookcase_3/shelf_1/bookcase_3/shelf_0/desk_1/top]) & upright(kid_cup) |
| 0 | no cup by his bed; lying; still held or dropped | |

### T28 · already_there（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：a cup already stands by his bed: his own, or a china one that is not his
- 考察：goal_already_met, referent_clue

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | seen it is already there and left it | on_any(kid_cup, [bookcase_3/top/desk_1/top]) |
| 0 | the cup taken away from his bed; still held or dropped | |

## T29_clear_table_for_dinner

- 基础指令 EN：Dinner is about to start. Take away what doesn't belong on the dining table and put each thing where it belongs: toys in the toy box, rubbish in the trash can, books on a bookshelf, homework on the study desk.
- 基础指令 中：要吃饭了，把餐桌上不该放的东西拿走，各放到该放的地方：玩具放进玩具箱，垃圾扔进垃圾桶，书放到书架上，作业放到书房书桌上。

### T29 · car_on_table（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the kid's toy car on the dining table; his toy box in the living room

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the toy car in his toy box | inside(table_car, toy_box) |
| 0.6 | the car off the table but not in the toy box | not on(table_car, dining_table_2/top) & not on_floor(table_car) |
| 0 | the thing left on the table; a setting piece tipped; still held or dropped | |

### T29 · belongs_on_table（布局 3 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the toy car, and a bowl and a spoon set for the meal; the toy box in the living room, or none
- 考察：category_rule, container_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | what does not belong taken away, the bowl and spoon set for the meal left (nothing at all if nothing to clear) | inside(table_car, toy_box); left in place (10 cm): set_bowl, set_spoon |
| 0.6 | the same, but the setting moved off its place on the table | inside(table_car, toy_box) & on(set_bowl, dining_table_2/top) & on(set_spoon, dining_table_2/top) |
| 0.3 | the set bowl or spoon taken off the table too | inside(table_car, toy_box) |
| 0 | the thing left on the table; a setting piece tipped; still held or dropped | |

### T29 · homework_on_table（布局 2 个）

- 指令 EN：Dinner is about to start. Take away what doesn't belong on the dining table.
- 指令 中：要吃饭了，把餐桌上不该放的东西拿走。
- 场景：the kid's notebook and pencil on the dining table; the study desk free, or covered with books
- 考察：storage_place, multi_object_goal

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the homework on a free desk (the study desk; covered: his own desk or bookcase) | on(hw_notebook, desk_1/top) & on(hw_pencil, desk_1/top) |
| 0.6 | on top of the books on the covered desk, or the books moved | not on(hw_notebook, dining_table_2/top) & not on(hw_pencil, dining_table_2/top) & not on_floor(hw_notebook) & not on_floor(hw_pencil) |
| 0 | homework left on the table; still held or dropped | |

### T29 · several（布局 2 个）

- 指令 EN：Dinner is about to start. Take away what doesn't belong on the dining table.
- 指令 中：要吃饭了，把餐桌上不该放的东西拿走。
- 场景：the toy car, a paperback and an empty soda can on the table; the toy box, or only a full toy bin
- 考察：category_rule, multi_object_goal, storage_place

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the car in the toy box, the can in the trash, the book on a bookcase or shelf | inside(empty_can, trash_can) & inside(table_car, toy_box); one of: on(table_book, bookcase_1/top) // on(table_book, bookcase_1/shelf_1) // on(table_book, bookcase_1/shelf_0) // on(table_book, bookcase_2/top) // ... 12 more ways |
| 0.6 | the car and the can in place, the book off the table but not shelved | inside(empty_can, trash_can) & inside(table_car, toy_box) & not on(table_book, dining_table_2/top) & not on_floor(table_book) |
| 0.3 | everything off the table, but not each to its place | not on(empty_can, dining_table_2/top) & not on(table_book, dining_table_2/top) & not on(table_car, dining_table_2/top) & not on_floor(empty_can) & not on_floor(table_book) & not on_floor(table_car) |
| 0 | the thing left on the table; a setting piece tipped; still held or dropped | |

### T29 · which_table（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：a toy on each dining table; the pot of soup stands on one of them
- 考察：destination_unnamed

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the toy on the table with the soup to the toy box, the other table's toy left | inside(toy_east, toy_box); left in place (10 cm): toy_west |
| 0.6 | the meal table cleared, and the other table's toy put away too | inside(toy_east, toy_box) |
| 0.3 | inside(toy_west, toy_box) | inside(toy_west, toy_box) |
| 0 | the meal table's toy left there; still held or dropped | |

## T30_bowls_for_soup

- 基础指令 EN：The soup is almost ready. Bring a clean bowl to the kitchen island next to the stove for serving it.
- 基础指令 中：汤快好了，拿一只干净的碗放到灶台旁边的岛台上准备盛汤。

### T30 · bowl_on_cabinet（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：the soup cooking in the pot on the stove; a clean bowl on the low wall cabinet

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | a clean bowl on the island by the stove | one of: count_on_at_least([soup_bowl_1/bowl_dining_cabinet/bowl_kitchen_cabinet/bowl_side_table/bowl_inside_kitchen_cabinet], kitchen_island/top, 1) // count_on_at_least([soup_bowl_1/bowl_dining_cabinet/bowl_kitchen_cabinet/bowl_side_table/bowl_inside_kitchen_cabinet], dining_table_2/top, 1) |
| 0 | fewer bowls than needed on the island; a bowl dropped; still held | |

### T30 · how_many（布局 2 个）

- 指令 EN：The soup is almost ready. Bring clean bowls to the kitchen island next to the stove for serving it.
- 指令 中：汤快好了，拿几只干净的碗放到灶台旁边的岛台上准备盛汤。
- 场景：three spoons laid out at the dining table; three clean bowls on the cabinet, or two and a mug (the house has no other bowl)
- 考察：count_from_scene, multi_object_goal, resource_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | three bowls on the island (three spoons at the table) | one of: count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/bowl_dining_cabinet/bowl_kitchen_cabinet/bowl_side_table/...], kitchen_island/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/bowl_dining_cabinet/bowl_kitchen_cabinet/bowl_side_table/...], dining_table_1/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/bowl_dining_cabinet/bowl_kitchen_cabinet/bowl_side_table/...], dining_table_2/top, 3) |
| 0.6 | one of: count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug], kitchen_island/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug], dining_table_1/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug], dining_table_2/top, 3) | one of: count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug], kitchen_island/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug], dining_table_1/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug], dining_table_2/top, 3) |
| 0.3 | one of: count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug/plate_counter_a/plate_counter_b], kitchen_island/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug/plate_counter_a/plate_counter_b], dining_table_1/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug/plate_counter_a/plate_counter_b], dining_table_2/top, 3) | one of: count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug/plate_counter_a/plate_counter_b], kitchen_island/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug/plate_counter_a/plate_counter_b], dining_table_1/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug/plate_counter_a/plate_counter_b], dining_table_2/top, 3) |
| 0 | fewer bowls than needed on the island; a bowl dropped; still held | |

### T30 · bowls_in_cabinet（布局 2 个）

- 指令 EN：The soup is almost ready. Bring clean bowls to the kitchen island next to the stove for serving it.
- 指令 中：汤快好了，拿几只干净的碗放到灶台旁边的岛台上准备盛汤。
- 场景：three spoons laid out at the dining table; one bowl and a mug on the low cabinet; inside it two more bowls, or only one; the house has no other bowl
- 考察：count_from_scene, item_put_away, resource_absent, dependent_decisions

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | three for the three spoons: bowls (a mug only when the bowls run out) | one of: count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3], kitchen_island/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3], dining_table_1/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3], dining_table_2/top, 3) |
| 0.6 | the mug used though a third bowl was in the cabinet | one of: count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug], kitchen_island/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug], dining_table_1/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/spare_mug], dining_table_2/top, 3) |
| 0.3 | one of: count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/plate_counter_a/plate_counter_b], kitchen_island/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/plate_counter_a/plate_counter_b], dining_table_1/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/plate_counter_a/plate_counter_b], dining_table_2/top, 3) | one of: count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/plate_counter_a/plate_counter_b], kitchen_island/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/plate_counter_a/plate_counter_b], dining_table_1/top, 3) // count_on_at_least([soup_bowl_1/soup_bowl_2/soup_bowl_3/plate_counter_a/plate_counter_b], dining_table_2/top, 3) |
| 0 | fewer than three; dropped; still held | |

### T30 · bowl_put_away（布局 2 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：no bowl out; the low cabinet holds the clean bowl, or only a plate and a mug
- 考察：item_put_away, resource_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | a bowl from the cabinet on the island | one of: count_on_at_least([soup_bowl_1/bowl_dining_cabinet/bowl_kitchen_cabinet/bowl_side_table/bowl_inside_kitchen_cabinet], kitchen_island/top, 1) // count_on_at_least([soup_bowl_1/bowl_dining_cabinet/bowl_kitchen_cabinet/bowl_side_table/bowl_inside_kitchen_cabinet], dining_table_2/top, 1) |
| 0.6 | one of: count_on_at_least([stored_mug], kitchen_island/top, 1) // count_on_at_least([stored_mug], dining_table_1/top, 1) // count_on_at_least([stored_mug], dining_table_2/top, 1) | one of: count_on_at_least([stored_mug], kitchen_island/top, 1) // count_on_at_least([stored_mug], dining_table_1/top, 1) // count_on_at_least([stored_mug], dining_table_2/top, 1) |
| 0.3 | one of: count_on_at_least([plate_counter_a/plate_counter_b], kitchen_island/top, 1) // count_on_at_least([plate_counter_a/plate_counter_b], dining_table_1/top, 1) // count_on_at_least([plate_counter_a/plate_counter_b], dining_table_2/top, 1) | one of: count_on_at_least([plate_counter_a/plate_counter_b], kitchen_island/top, 1) // count_on_at_least([plate_counter_a/plate_counter_b], dining_table_1/top, 1) // count_on_at_least([plate_counter_a/plate_counter_b], dining_table_2/top, 1) |
| 0 | fewer bowls than needed on the island; a bowl dropped; still held | |

### T30 · no_bowl（布局 1 个）

- 指令 EN：（基础指令）
- 指令 中：（基础指令）
- 场景：no clean bowl anywhere; a mug and a plate on the cabinet
- 考察：resource_absent

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | one of: count_on_at_least([spare_mug/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], kitchen_island/top, 1) // count_on_at_least([spare_mug/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], dining_table_2/top, 1) | one of: count_on_at_least([spare_mug/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], kitchen_island/top, 1) // count_on_at_least([spare_mug/cup_counter_b/cup_kitchen_cabinet/cup_side_table/mug_dining_cabinet/mug_shelf/...], dining_table_2/top, 1) |
| 0.6 | the plate brought (soup does not stay on it) | one of: on(spare_plate, kitchen_island/top) // on(spare_plate, dining_table_1/top) // on(spare_plate, dining_table_2/top) |
| 0 | nothing brought; dropped; still held | |

### T30 · bowl_not_plate（布局 2 个）

- 指令 EN：The soup is almost ready. Bring a bowl to the kitchen island next to the stove for serving it.
- 指令 中：汤快好了，拿一只碗放到灶台旁边的岛台上准备盛汤。
- 场景：a plate and a bowl on the cabinet
- 考察：referent_clue

| 分数 | 说明 | 条件 |
|---|---|---|
| 1.0 | the clean bowl on the island, the plate (or the full bowl) left | one of: count_on_at_least([soup_bowl_1/bowl_dining_cabinet/bowl_kitchen_cabinet/bowl_side_table/bowl_inside_kitchen_cabinet], kitchen_island/top, 1) // count_on_at_least([soup_bowl_1/bowl_dining_cabinet/bowl_kitchen_cabinet/bowl_side_table/bowl_inside_kitchen_cabinet], dining_table_2/top, 1); left in place (10 cm): spare_plate |
| 0.6 | the clean bowl, and the plate or the full bowl brought too | one of: count_on_at_least([soup_bowl_1/bowl_dining_cabinet/bowl_kitchen_cabinet/bowl_side_table/bowl_inside_kitchen_cabinet], kitchen_island/top, 1) // count_on_at_least([soup_bowl_1/bowl_dining_cabinet/bowl_kitchen_cabinet/bowl_side_table/bowl_inside_kitchen_cabinet], dining_table_2/top, 1) |
| 0.3 | only the plate, or only the bowl still full of oatmeal | one of: on(spare_plate, kitchen_island/top) // on(spare_plate, dining_table_1/top) // on(spare_plate, dining_table_2/top) |
| 0 | nothing brought; dropped; still held | |

