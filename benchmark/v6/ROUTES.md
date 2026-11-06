# v6 oracle reference routes

One line per layout of each variant (`!` expected to fail, `+` recovery step). Seeds: the variant's manifest in tasks.json.

## T01_book_to_dining_table

### Control

* `overhang_ready` (v5fix_overhang_ready, 7 steps): look(kitchen_island/top) navigate(paperback_book) approach(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.5])

### Task-Level

* `table_seats__seats_a` (v6_table_seats__seats_a, 8 steps): look(kitchen_island/top) navigate(paperback_book) approach(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 7.059])
* `table_seats__seats_b` (v6_table_seats__seats_b, 8 steps): look(kitchen_island/top) navigate(paperback_book) approach(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.138])
* `table_seats__seats_c` (v6_table_seats__seats_c, 8 steps): look(kitchen_island/top) navigate(paperback_book) approach(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 7.779])
* `which_table__near_a` (v6_which_table__near_a, 8 steps): look(kitchen_island/top) navigate(paperback_book) approach(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 7.059])
* `which_table__near_b` (v6_which_table__near_b, 8 steps): look(kitchen_island/top) navigate(paperback_book) approach(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.138])
* `which_table__far_a` (v6_which_table__far_a, 10 steps): look(kitchen_island/top) navigate(paperback_book) approach(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) navigate(dining_table_1/top) look(dining_table_1/top) place(paperback_book,dining_table_1/top,[-7.607, 8.179])
* `which_table__far_b` (v6_which_table__far_b, 10 steps): look(kitchen_island/top) navigate(paperback_book) approach(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) navigate(dining_table_1/top) look(dining_table_1/top) place(paperback_book,dining_table_1/top,[-7.607, 7.508])
* `no_room_fallback__seats_b` (v6_no_room_fallback__seats_b, 8 steps): look(kitchen_island/top) navigate(paperback_book) approach(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.138])
* `no_room_fallback__seats_c` (v6_no_room_fallback__seats_c, 8 steps): look(kitchen_island/top) navigate(paperback_book) approach(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 7.779])
* `no_room_fallback__full_a` (v6_no_room_fallback__full_a, 9 steps): look(kitchen_island/top) navigate(paperback_book) approach(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) navigate(cell_shelf_4/top) place(paperback_book,cell_shelf_4/top,[4.3, 4.45])
* `reader_seat__mug_1` (v6_reader_seat__mug_1, 8 steps): look(kitchen_island/top) navigate(paperback_book) approach(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 5.69])
* `reader_seat__mug_2` (v6_reader_seat__mug_2, 8 steps): look(kitchen_island/top) navigate(paperback_book) approach(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.428])
* `reader_seat__mug_3` (v6_reader_seat__mug_3, 8 steps): look(kitchen_island/top) navigate(paperback_book) approach(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 7.094])
* `which_book__living` (v6_which_book__living, 9 steps): look(kitchen_island/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(paperback_book) approach(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.5])
* `which_book__bedroom` (v6_which_book__bedroom, 9 steps): look(kitchen_island/top) navigate(bookcase_2/top) look(bookcase_2/top) navigate(paperback_book) approach(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.5])

## T02_stack_blocks

### Control

* `clear` (nominal, 6 steps): look(kitchen_island/top) navigate(wooden_block_b) pick(wooden_block_b) rotate(wooden_block_b,30) navigate(wooden_block_a) stack(wooden_block_b,wooden_block_a)

### Task-Level

* `crowded_use_another__tight_tv` (v6_crowded_use_another__tight_tv, 9 steps): look(kitchen_island/top) navigate(wooden_block_b) look(wooden_block_b) search(floor_block,living_room_0_0) navigate(floor_block) pick(floor_block) navigate(wooden_block_a) approach(wooden_block_a) stack(floor_block,wooden_block_a)
* `crowded_use_another__tight_dining` (v6_crowded_use_another__tight_dining, 9 steps): look(kitchen_island/top) navigate(wooden_block_b) look(wooden_block_b) search(floor_block,dining_room_0_1) navigate(floor_block) pick(floor_block) navigate(wooden_block_a) approach(wooden_block_a) stack(floor_block,wooden_block_a)
* `crowded_use_another__loose` (v6_crowded_use_another__loose, 7 steps): look(kitchen_island/top) navigate(wooden_block_b) pick(wooden_block_b) rotate(wooden_block_b,30) navigate(wooden_block_a) approach(wooden_block_a) stack(wooden_block_b,wooden_block_a)
* `third_toy_elsewhere__duck` (v6_third_toy_elsewhere__duck, 12 steps): look(kitchen_island/top) navigate(wooden_block_b) pick(wooden_block_b) rotate(wooden_block_b,30) navigate(wooden_block_a) stack(wooden_block_b,wooden_block_a) +search(rubber_duck,dining_room_0_1) +navigate(rubber_duck) +pick(rubber_duck) +navigate(wooden_block_a) +approach(wooden_block_a) +stack(rubber_duck,wooden_block_b)
* `third_toy_elsewhere__toy_block` (v6_third_toy_elsewhere__toy_block, 12 steps): look(kitchen_island/top) navigate(wooden_block_b) pick(wooden_block_b) rotate(wooden_block_b,30) navigate(wooden_block_a) stack(wooden_block_b,wooden_block_a) +search(toy_block,kitchen_0_1) +navigate(toy_block) +pick(toy_block) +navigate(wooden_block_a) +approach(wooden_block_a) +stack(toy_block,wooden_block_b)
* `tower_for_kid__counter` (v6_tower_for_kid__counter, 18 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(dining_table_2/top) look(dining_table_2/top) place(wooden_block_a,dining_table_2/top,[3.7, 6.6]) search(wooden_block_b,living_room_0_0) navigate(wooden_block_b) pick(wooden_block_b) navigate(wooden_block_a) approach(wooden_block_a) stack(wooden_block_b,wooden_block_a) search(floor_block,kitchen_0_1) navigate(floor_block) pick(floor_block) navigate(wooden_block_a) approach(wooden_block_a) stack(floor_block,wooden_block_b)
* `tower_for_kid__study` (v6_tower_for_kid__study, 18 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(dining_table_2/top) look(dining_table_2/top) place(wooden_block_a,dining_table_2/top,[3.7, 6.6]) search(floor_block,living_room_0_0) navigate(floor_block) pick(floor_block) navigate(wooden_block_a) approach(wooden_block_a) stack(floor_block,wooden_block_a) search(wooden_block_b,living_room_0_1) navigate(wooden_block_b) pick(wooden_block_b) navigate(wooden_block_a) approach(wooden_block_a) stack(wooden_block_b,floor_block)
* `tower_for_kid_duck__counter` (v6_tower_for_kid_duck__counter, 18 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(dining_table_2/top) look(dining_table_2/top) place(wooden_block_a,dining_table_2/top,[3.7, 6.6]) search(wooden_block_b,living_room_0_0) navigate(wooden_block_b) pick(wooden_block_b) navigate(wooden_block_a) approach(wooden_block_a) stack(wooden_block_b,wooden_block_a) search(rubber_duck,kitchen_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(wooden_block_a) approach(wooden_block_a) stack(rubber_duck,wooden_block_b)
* `tower_for_kid_duck__study` (v6_tower_for_kid_duck__study, 18 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(dining_table_2/top) look(dining_table_2/top) place(wooden_block_a,dining_table_2/top,[3.7, 6.6]) search(wooden_block_b,living_room_0_1) navigate(wooden_block_b) pick(wooden_block_b) navigate(wooden_block_a) approach(wooden_block_a) stack(wooden_block_b,wooden_block_a) search(rubber_duck,living_room_0_0) navigate(rubber_duck) pick(rubber_duck) navigate(wooden_block_a) approach(wooden_block_a) stack(rubber_duck,wooden_block_b)

### Action + Task

* `block_put_away__in_4` (v6_block_put_away__in_4, 24 steps): look(kitchen_island/top) navigate(wooden_block_a) +pick(wooden_block_a) navigate(wooden_block_b) approach(wooden_block_b) +stack(wooden_block_a,wooden_block_b) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(floor_block) pick(floor_block) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(wooden_block_a) approach(wooden_block_a) stack(floor_block,wooden_block_a)
* `block_put_away__in_6` (v6_block_put_away__in_6, 24 steps): look(kitchen_island/top) navigate(wooden_block_a) +pick(wooden_block_a) navigate(wooden_block_b) approach(wooden_block_b) +stack(wooden_block_a,wooden_block_b) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() close(kitchen_cabinet_4) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(floor_block) pick(floor_block) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(wooden_block_a) approach(wooden_block_a) stack(floor_block,wooden_block_a)

## T03_utensils_one_container

### Control

* `large_only` (nominal, 12 steps): look(kitchen_island/top) look(tv_stand_2/top) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(wide_storage_bin) approach(wide_storage_bin) drop(breakfast_spoon,wide_storage_bin) navigate(rolling_pin) pick(rolling_pin) navigate(wide_storage_bin) approach(wide_storage_bin) place(rolling_pin,wide_storage_bin)

### Task-Level

* `small_bin_or_bedroom_bin` (v6_small_bin_or_bedroom_bin, 16 steps): look(kitchen_island/top) measure(small_storage_bin) measure(rolling_pin) search(wide_storage_bin,bedroom_0_1) navigate(bookcase_2/top) look(bookcase_2/top) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(wide_storage_bin) approach(wide_storage_bin) drop(breakfast_spoon,wide_storage_bin) navigate(rolling_pin) pick(rolling_pin) navigate(wide_storage_bin) approach(wide_storage_bin) place(rolling_pin,wide_storage_bin)
* `three_containers_bedroom` (v6_three_containers_bedroom, 16 steps): look(kitchen_island/top) search(wide_storage_bin,bedroom_0_1) navigate(bookcase_2/top) look(bookcase_2/top) measure(small_storage_bin) measure(rolling_pin) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(wide_storage_bin) approach(wide_storage_bin) drop(breakfast_spoon,wide_storage_bin) navigate(rolling_pin) pick(rolling_pin) navigate(wide_storage_bin) approach(wide_storage_bin) place(rolling_pin,wide_storage_bin)
* `which_bin_by_contents__toys_near` (v6_which_bin_by_contents__toys_near, 15 steps): look(kitchen_island/top) look(tv_stand_2/top) search(wide_storage_bin,bedroom_0_1) navigate(bookcase_2/top) look(bookcase_2/top) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(wide_storage_bin) approach(wide_storage_bin) drop(breakfast_spoon,wide_storage_bin) navigate(rolling_pin) pick(rolling_pin) navigate(wide_storage_bin) approach(wide_storage_bin) place(rolling_pin,wide_storage_bin)
* `which_bin_by_contents__tools_near` (v6_which_bin_by_contents__tools_near, 12 steps): look(kitchen_island/top) look(tv_stand_2/top) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(wide_storage_bin) approach(wide_storage_bin) drop(breakfast_spoon,wide_storage_bin) navigate(rolling_pin) pick(rolling_pin) navigate(wide_storage_bin) approach(wide_storage_bin) place(rolling_pin,wide_storage_bin)
* `no_bin_substitute__basket` (v6_no_bin_substitute__basket, 17 steps): look(kitchen_island/top) measure(rolling_pin) look(tv_stand_2/top) measure(small_storage_bin) search(storage_basket,bedroom_0_1) navigate(storage_basket) look(storage_basket) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(storage_basket) approach(storage_basket) drop(breakfast_spoon,storage_basket) navigate(rolling_pin) pick(rolling_pin) navigate(storage_basket) approach(storage_basket) place(rolling_pin,storage_basket)
* `no_bin_substitute__tray` (v6_no_bin_substitute__tray, 17 steps): look(kitchen_island/top) measure(rolling_pin) look(tv_stand_2/top) measure(small_storage_bin) search(serving_tray,living_room_0_1) navigate(serving_tray) look(serving_tray) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(serving_tray) approach(serving_tray) place(breakfast_spoon,serving_tray) navigate(rolling_pin) pick(rolling_pin) navigate(serving_tray) approach(serving_tray) place(rolling_pin,serving_tray)
* `utensils_apart__dining` (v6_utensils_apart__dining, 15 steps): look(kitchen_island/top) search(wide_storage_bin,bedroom_0_1) navigate(bookcase_2/top) look(bookcase_2/top) navigate(rolling_pin) pick(rolling_pin) navigate(wide_storage_bin) approach(wide_storage_bin) place(rolling_pin,wide_storage_bin) search(breakfast_spoon,dining_room_0_1) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(wide_storage_bin) approach(wide_storage_bin) drop(breakfast_spoon,wide_storage_bin)
* `utensils_apart__counter` (v6_utensils_apart__counter, 15 steps): look(kitchen_island/top) search(wide_storage_bin,bedroom_0_1) navigate(bookcase_2/top) look(bookcase_2/top) navigate(rolling_pin) pick(rolling_pin) navigate(wide_storage_bin) approach(wide_storage_bin) place(rolling_pin,wide_storage_bin) search(breakfast_spoon,kitchen_0_1) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(wide_storage_bin) approach(wide_storage_bin) drop(breakfast_spoon,wide_storage_bin)

## T04_cup_or_mug_to_cabinet

### Control

* `cup_available` (nominal, 5 steps): look(kitchen_island/top) navigate(cup_counter_b) pick(cup_counter_b) navigate(kitchen_cabinet_6/top) place(cup_counter_b,kitchen_cabinet_6/top)

### Task-Level

* `no_cup` (alternative_mug, 7 steps): look(kitchen_island/top) count(cup) !search(cup) +navigate(mug) +pick(mug) navigate(kitchen_cabinet_6/top) place(mug,kitchen_cabinet_6/top)
* `no_cup_mug_away` (hard_count_search_mug, 8 steps): look(kitchen_island/top) count(cup) !search(cup) +search(mug,living_room_0_0) navigate(mug) pick(mug) navigate(kitchen_cabinet_6/top) place(mug,kitchen_cabinet_6/top)
* `no_cup_mug_away__alt_dining_table_2` (v6_no_cup_mug_away__alt_dining_table_2, 8 steps): look(kitchen_island/top) count(cup) !search(cup) +search(mug,dining_room_0_1) navigate(mug) pick(mug) navigate(kitchen_cabinet_6/top) place(mug,kitchen_cabinet_6/top)
* `h_task_spot_taken` (v5_h_task_spot_taken, 11 steps): look(kitchen_island/top) navigate(kitchen_cabinet_6/top) look(kitchen_cabinet_6/top) navigate(oatmeal) pick(oatmeal) navigate(kitchen_cabinet_4/top) place(oatmeal,kitchen_cabinet_4/top) navigate(cup_counter_b) pick(cup_counter_b) navigate(kitchen_cabinet_6/top) place(cup_counter_b,kitchen_cabinet_6/top)
* `two_guests__dining` (v6_two_guests__dining, 10 steps): look(kitchen_island/top) navigate(cup_counter_b) pick(cup_counter_b) navigate(kitchen_cabinet_6/top) place(cup_counter_b,kitchen_cabinet_6/top,[3.36, 0.36]) search(mug,dining_room_0_1) navigate(mug) pick(mug) navigate(kitchen_cabinet_6/top) place(mug,kitchen_cabinet_6/top,[3.62, 0.36])
* `two_guests__study` (v6_two_guests__study, 10 steps): look(kitchen_island/top) navigate(cup_counter_b) pick(cup_counter_b) navigate(kitchen_cabinet_6/top) place(cup_counter_b,kitchen_cabinet_6/top,[3.36, 0.36]) search(mug,living_room_0_1) navigate(mug) pick(mug) navigate(kitchen_cabinet_6/top) place(mug,kitchen_cabinet_6/top,[3.62, 0.36])
* `hot_tea_mug__dining` (v6_hot_tea_mug__dining, 6 steps): look(kitchen_island/top) search(mug,dining_room_0_1) navigate(mug) pick(mug) navigate(kitchen_cabinet_6/top) place(mug,kitchen_cabinet_6/top)
* `hot_tea_mug__study` (v6_hot_tea_mug__study, 6 steps): look(kitchen_island/top) search(mug,living_room_0_1) navigate(mug) pick(mug) navigate(kitchen_cabinet_6/top) place(mug,kitchen_cabinet_6/top)
* `x6_gd_cup_in_cabinets__cup_in_4` (v6_x6_gd_cup_in_cabinets__cup_in_4, 18 steps): look(kitchen_island/top) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(cup_counter_b) pick(cup_counter_b) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(kitchen_cabinet_6/top) place(cup_counter_b,kitchen_cabinet_6/top)
* `x6_gd_cup_in_cabinets__cup_in_6` (v6_x6_gd_cup_in_cabinets__cup_in_6, 18 steps): look(kitchen_island/top) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() close(kitchen_cabinet_4) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(cup_counter_b) pick(cup_counter_b) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(kitchen_cabinet_6/top) place(cup_counter_b,kitchen_cabinet_6/top)

## T05_pen_or_pencil_to_desk

### Control

* `e1_pencil_asked` (v5_e1_pencil_asked, 7 steps): navigate(bookcase_2/top) look(bookcase_2/top) +navigate(pencil) +pick(pencil) +present(pencil) navigate(desk_1/top) place(pencil,desk_1/top)

### Task-Level

* `no_pen_pencil_away` (v5fix_hard_search_pencil, 9 steps): navigate(bookcase_2/top) look(bookcase_2/top) !navigate(pen) +navigate(dining_table_2/top) +look(dining_table_2/top) navigate(pencil) pick(pencil) navigate(desk_1/top) place(pencil,desk_1/top)
* `check_desk_first__pen_on_desk` (v6_check_desk_first__pen_on_desk, 3 steps): navigate(desk_1/top) look(desk_1/top) identify(pen)
* `check_desk_first__pencil_on_desk` (v6_check_desk_first__pencil_on_desk, 3 steps): navigate(desk_1/top) look(desk_1/top) identify(pencil)
* `all_pens__two` (v6_all_pens__two, 10 steps): search(pencil,bedroom_0_1) navigate(pencil) pick(pencil) navigate(desk_1/top) place(pencil,desk_1/top,[-1.2, -5.95]) search(pen,dining_room_0_1) navigate(pen) pick(pen) navigate(desk_1/top) place(pen,desk_1/top,[-0.9, -5.95])
* `all_pens__three` (v6_all_pens__three, 15 steps): search(pencil,bedroom_0_1) navigate(pencil) pick(pencil) navigate(desk_1/top) place(pencil,desk_1/top,[-1.2, -5.95]) search(pen,dining_room_0_1) navigate(pen) pick(pen) navigate(desk_1/top) place(pen,desk_1/top,[-0.9, -5.95]) search(pencil_2,living_room_0_0) navigate(pencil_2) pick(pencil_2) navigate(desk_1/top) place(pencil_2,desk_1/top,[-0.6, -5.95])
* `all_pens__four` (v6_all_pens__four, 20 steps): search(pencil,bedroom_0_1) navigate(pencil) pick(pencil) navigate(desk_1/top) place(pencil,desk_1/top,[-1.2, -5.95]) search(pen,dining_room_0_1) navigate(pen) pick(pen) navigate(desk_1/top) place(pen,desk_1/top,[-0.9, -5.95]) search(pencil_2,living_room_0_0) navigate(pencil_2) pick(pencil_2) navigate(desk_1/top) place(pencil_2,desk_1/top,[-0.6, -5.95]) search(pen_2,kitchen_0_1) navigate(pen_2) pick(pen_2) navigate(desk_1/top) place(pen_2,desk_1/top,[-0.3, -5.95])
* `homework_ready__single` (v6_homework_ready__single, 12 steps): search(pen,bedroom_0_1) navigate(pen) pick(pen) navigate(desk_1/top) place(pen,desk_1/top,[-0.9, -5.95]) search(notebook_1,dining_room_0_1) navigate(notebook_1) expose(notebook_1) look(notebook_1) pick(notebook_1) navigate(desk_1/top) place(notebook_1,desk_1/top,[-0.6, -5.95])
* `homework_ready__several` (v6_homework_ready__several, 12 steps): search(pen,bedroom_0_1) navigate(pen) pick(pen) navigate(desk_1/top) place(pen,desk_1/top,[-0.9, -5.95]) search(notebook_2,living_room_0_0) navigate(notebook_2) expose(notebook_2) look(notebook_2) pick(notebook_2) navigate(desk_1/top) place(notebook_2,desk_1/top,[-0.6, -5.95])
* `homework_ready__pencil_only` (v6_homework_ready__pencil_only, 12 steps): search(notebook_1,bedroom_0_1) navigate(notebook_1) expose(notebook_1) look(notebook_1) pick(notebook_1) navigate(desk_1/top) place(notebook_1,desk_1/top,[-0.9, -5.95]) search(pencil,dining_room_0_1) navigate(pencil) pick(pencil) navigate(desk_1/top) place(pencil,desk_1/top,[-0.6, -5.95])
* `pens_per_notebook__notebooks_2` (v6_pens_per_notebook__notebooks_2, 10 steps): search(pencil,bedroom_0_1) navigate(pencil) pick(pencil) navigate(desk_1/top) place(pencil,desk_1/top,[-0.85, -5.92]) search(pen,bedroom_0_1) navigate(pen) pick(pen) navigate(desk_1/top) place(pen,desk_1/top,[-0.3, -5.92])
* `pens_per_notebook__notebooks_3` (v6_pens_per_notebook__notebooks_3, 15 steps): search(pencil,bedroom_0_1) navigate(pencil) pick(pencil) navigate(desk_1/top) place(pencil,desk_1/top,[-1.0, -5.92]) search(pen,bedroom_0_1) navigate(pen) pick(pen) navigate(desk_1/top) place(pen,desk_1/top,[-0.57, -5.92]) search(pen_2,living_room_0_0) navigate(pen_2) pick(pen_2) navigate(desk_1/top) place(pen_2,desk_1/top,[-0.14, -5.92])
* `errand_combined__pen_bedroom` (v6_errand_combined__pen_bedroom, 8 steps): search(pen,bedroom_0_1) navigate(pen) pick(pen) navigate(desk_1/top) place(pen,desk_1/top,[-0.75, -5.95]) pick(used_mug) navigate(kitchen_counter_2/top) place(used_mug,kitchen_counter_2/top,[-0.15, 7.3])
* `errand_combined__pen_dining` (v6_errand_combined__pen_dining, 8 steps): search(pen,dining_room_0_1) navigate(pen) pick(pen) navigate(desk_1/top) place(pen,desk_1/top,[-0.75, -5.95]) pick(used_mug) navigate(kitchen_counter_2/top) place(used_mug,kitchen_counter_2/top,[-0.15, 7.3])
* `x6_gd_pen_or_pencil_cabinets__pen_in_4` (v6_x6_gd_pen_or_pencil_cabinets__pen_in_4, 17 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(pen) pick(pen) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(desk_1/top) place(pen,desk_1/top)
* `x6_gd_pen_or_pencil_cabinets__pen_in_6` (v6_x6_gd_pen_or_pencil_cabinets__pen_in_6, 17 steps): navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() close(kitchen_cabinet_4) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(pen) pick(pen) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(desk_1/top) place(pen,desk_1/top)

### Action + Task

* `h_task_pencil_in_cabinet` (v5_h_task_pencil_in_cabinet, 11 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) +bend() +explore_furniture(kitchen_cabinet_6) +straighten() navigate(pencil) pick(pencil) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(desk_1/top) place(pencil,desk_1/top)

## T06_block_destination_occupied

### Control

* `free` (nominal, 5 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(kitchen_cabinet_6/top) place(wooden_block_a,kitchen_cabinet_6/top)

### Task-Level

* `occupied` (v6_occupied, 6 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) look(kitchen_cabinet_6/top) +navigate(tv_stand_2/top) +place(wooden_block_a,tv_stand_2/top)
* `occupied_block_away` (v6_occupied_block_away, 7 steps): look(kitchen_island/top) +search(wooden_block_a,dining_room_0_1) navigate(wooden_block_a) pick(wooden_block_a) look(kitchen_cabinet_6/top) +navigate(tv_stand_2/top) +place(wooden_block_a,tv_stand_2/top)
* `occupied_block_away__alt_tv_stand_2` (v6_occupied_block_away__alt_tv_stand_2, 7 steps): look(kitchen_island/top) +search(wooden_block_a,living_room_0_0) navigate(wooden_block_a) pick(wooden_block_a) look(kitchen_cabinet_6/top) +navigate(tv_stand_2/top) +place(wooden_block_a,tv_stand_2/top)
* `display_row__island_floor` (v6_display_row__island_floor, 14 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(kitchen_cabinet_6/top) place(wooden_block_a,kitchen_cabinet_6/top,[3.32, 0.45]) navigate(wooden_block_b) pick(wooden_block_b) navigate(kitchen_cabinet_6/top) place(wooden_block_b,kitchen_cabinet_6/top,[3.5, 0.45]) search(floor_block,living_room_0_0) navigate(floor_block) pick(floor_block) navigate(kitchen_cabinet_6/top) place(floor_block,kitchen_cabinet_6/top,[3.68, 0.45])
* `display_row__spread` (v6_display_row__spread, 15 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(kitchen_cabinet_6/top) place(wooden_block_a,kitchen_cabinet_6/top,[3.32, 0.45]) search(wooden_block_b,dining_room_0_1) navigate(wooden_block_b) pick(wooden_block_b) navigate(kitchen_cabinet_6/top) place(wooden_block_b,kitchen_cabinet_6/top,[3.5, 0.45]) search(floor_block,kitchen_0_1) navigate(floor_block) pick(floor_block) navigate(kitchen_cabinet_6/top) place(floor_block,kitchen_cabinet_6/top,[3.68, 0.45])
* `display_spot_or_tv__front_taken` (v6_display_spot_or_tv__front_taken, 6 steps): look(kitchen_island/top) look(kitchen_cabinet_6/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(tv_stand_2/top) place(wooden_block_a,tv_stand_2/top)
* `display_spot_or_tv__front_free` (v6_display_spot_or_tv__front_free, 6 steps): look(kitchen_island/top) look(kitchen_cabinet_6/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(kitchen_cabinet_6/top) place(wooden_block_a,kitchen_cabinet_6/top,[3.433, 0.465])
* `seen_from_bed__boxes_middle` (v6_seen_from_bed__boxes_middle, 7 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) explore_room(bedroom_0_1) navigate(bookcase_3/top) look(bookcase_3/top) place(wooden_block_a,bookcase_3/top,[1.88, -4.88])
* `seen_from_bed__boxes_corner` (v6_seen_from_bed__boxes_corner, 7 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) explore_room(bedroom_0_1) navigate(bookcase_3/top) look(bookcase_3/top) place(wooden_block_a,bookcase_3/top,[2.15, -4.74])

## T07_heat_oatmeal

### Control

* `microwave_works` (nominal, 9 steps): navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_island/top) navigate(oatmeal) pick(oatmeal) navigate(kitchen_microwave/inside_floor) place(oatmeal,kitchen_microwave/inside_floor) close(kitchen_microwave) heat(oatmeal,kitchen_microwave,40)

### Task-Level

* `microwave_broken` (v6_microwave_broken, 15 steps): navigate(kitchen_microwave) open(kitchen_microwave) navigate(oatmeal) pick(oatmeal) navigate(kitchen_microwave/inside_floor) place(oatmeal,kitchen_microwave/inside_floor) close(kitchen_microwave) !heat(oatmeal,kitchen_microwave,40) +stop(kitchen_microwave) +pick(oatmeal) +navigate(kitchen_stove/top) +place(oatmeal,kitchen_stove/top) +heat(oatmeal,kitchen_stove,40) navigate(kitchen_microwave) close(kitchen_microwave)
* `broken_oatmeal_away` (hard_search_stove, 16 steps): navigate(kitchen_microwave) open(kitchen_microwave) +search(oatmeal,living_room_0_0) navigate(oatmeal) pick(oatmeal) navigate(kitchen_microwave/inside_floor) place(oatmeal,kitchen_microwave/inside_floor) close(kitchen_microwave) !heat(oatmeal,kitchen_microwave,40) +stop(kitchen_microwave) +pick(oatmeal) +navigate(kitchen_stove/top) +place(oatmeal,kitchen_stove/top) +heat(oatmeal,kitchen_stove,40) navigate(kitchen_microwave) close(kitchen_microwave)
* `broken_oatmeal_away__alt_dining_table_2` (v6_broken_oatmeal_away__alt_dining_table_2, 16 steps): navigate(kitchen_microwave) open(kitchen_microwave) +search(oatmeal,dining_room_0_1) navigate(oatmeal) pick(oatmeal) navigate(kitchen_microwave/inside_floor) place(oatmeal,kitchen_microwave/inside_floor) close(kitchen_microwave) !heat(oatmeal,kitchen_microwave,40) +stop(kitchen_microwave) +pick(oatmeal) +navigate(kitchen_stove/top) +place(oatmeal,kitchen_stove/top) +heat(oatmeal,kitchen_stove,40) navigate(kitchen_microwave) close(kitchen_microwave)
* `microwave_holds_pot` (hard_stove_instead, 10 steps): navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_microwave/inside_floor) close(kitchen_microwave) look(kitchen_island/top) navigate(oatmeal) pick(oatmeal) +navigate(kitchen_stove/top) +place(oatmeal,kitchen_stove/top) +heat(oatmeal,kitchen_stove,40)
* `vessel_decides_appliance__in_ceramic_bowl` (v6_vessel_decides_appliance__in_ceramic_bowl, 9 steps): navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_island/top) navigate(oatmeal_bowl) pick(oatmeal_bowl) navigate(kitchen_microwave/inside_floor) place(oatmeal_bowl,kitchen_microwave/inside_floor) close(kitchen_microwave) heat(oatmeal_bowl,kitchen_microwave,40)
* `vessel_decides_appliance__in_glass_box` (v6_vessel_decides_appliance__in_glass_box, 11 steps): navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_island/top) navigate(glass_food_container) expose(glass_food_container) look(glass_food_container) pick(glass_food_container) navigate(kitchen_microwave/inside_floor) place(glass_food_container,kitchen_microwave/inside_floor) close(kitchen_microwave) heat(glass_food_container,kitchen_microwave,40)
* `vessel_decides_appliance__in_pot` (v6_vessel_decides_appliance__in_pot, 7 steps): look(kitchen_island/top) search(soup_pot,dining_room_0_1) navigate(soup_pot) pick(soup_pot) navigate(kitchen_stove/top) place(soup_pot,kitchen_stove/top,[8.41, 1.725]) heat(soup_pot,kitchen_stove,40)
* `vessel_decides_appliance__in_steel_box` (v6_vessel_decides_appliance__in_steel_box, 8 steps): look(kitchen_island/top) navigate(steel_lunch_box) expose(steel_lunch_box) look(steel_lunch_box) pick(steel_lunch_box) navigate(kitchen_stove/top) place(steel_lunch_box,kitchen_stove/top,[8.41, 1.725]) heat(steel_lunch_box,kitchen_stove,40)
* `vessel_decides_appliance__in_foil_tray` (v6_vessel_decides_appliance__in_foil_tray, 8 steps): look(kitchen_island/top) navigate(foil_takeout_tray) expose(foil_takeout_tray) look(foil_takeout_tray) pick(foil_takeout_tray) navigate(kitchen_stove/top) place(foil_takeout_tray,kitchen_stove/top,[8.41, 1.725]) heat(foil_takeout_tray,kitchen_stove,40)
* `two_portions__dining` (v6_two_portions__dining, 21 steps): search(soup_pot,dining_room_0_1) navigate(soup_pot) pick(soup_pot) navigate(kitchen_stove/top) place(soup_pot,kitchen_stove/top,[8.41, 1.725]) press(kitchen_stove/power_button) navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_island/top) navigate(oatmeal_bowl) pick(oatmeal_bowl) navigate(kitchen_microwave/inside_floor) place(oatmeal_bowl,kitchen_microwave/inside_floor) close(kitchen_microwave) approach(kitchen_microwave/start_button) press(kitchen_microwave/start_button) wait(25) stop(kitchen_microwave) close(kitchen_microwave) navigate(kitchen_stove) stop(kitchen_stove)
* `two_portions__counter` (v6_two_portions__counter, 21 steps): search(soup_pot,kitchen_0_1) navigate(soup_pot) pick(soup_pot) navigate(kitchen_stove/top) place(soup_pot,kitchen_stove/top,[8.41, 1.725]) press(kitchen_stove/power_button) navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_island/top) navigate(oatmeal_bowl) pick(oatmeal_bowl) navigate(kitchen_microwave/inside_floor) place(oatmeal_bowl,kitchen_microwave/inside_floor) close(kitchen_microwave) approach(kitchen_microwave/start_button) press(kitchen_microwave/start_button) wait(25) stop(kitchen_microwave) close(kitchen_microwave) navigate(kitchen_stove) stop(kitchen_stove)

## T08_wipe_island

### Control

* `sponge_on_island` (nominal, 6 steps): look(kitchen_island/top) look(tv_stand_2/top) navigate(kitchen_sponge) pick(kitchen_sponge) wipe(kitchen_island/top,kitchen_sponge) place(kitchen_sponge,kitchen_island/top)

### Task-Level

* `far_sponge_tv` (hard_search_approach, 6 steps): +search(kitchen_sponge,living_room_0_0) navigate(kitchen_sponge) pick(kitchen_sponge) approach(kitchen_island/top) wipe(kitchen_island/top,kitchen_sponge) place(kitchen_sponge,kitchen_island/top)
* `far_sponge_tv__alt_dining_table_2` (v6_far_sponge_tv__alt_dining_table_2, 7 steps): +search(kitchen_sponge,dining_room_0_1) navigate(kitchen_sponge) pick(kitchen_sponge) navigate(kitchen_island/top) approach(kitchen_island/top) wipe(kitchen_island/top,kitchen_sponge) place(kitchen_sponge,kitchen_island/top)
* `wipe_and_sort__blocks` (v6_wipe_and_sort__blocks, 17 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(toy_box) approach(toy_box) place(wooden_block_a,toy_box) navigate(wooden_block_b) pick(wooden_block_b) navigate(toy_box) approach(toy_box) place(wooden_block_b,toy_box) look(tv_stand_2/top) navigate(kitchen_sponge) pick(kitchen_sponge) approach(kitchen_island/top) wipe(kitchen_island/top,kitchen_sponge) place(kitchen_sponge,kitchen_island/top)
* `wipe_and_sort__duck` (v6_wipe_and_sort__duck, 17 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(toy_box) approach(toy_box) place(wooden_block_a,toy_box) navigate(rubber_duck) pick(rubber_duck) navigate(toy_box) approach(toy_box) place(rubber_duck,toy_box) look(tv_stand_2/top) navigate(kitchen_sponge) pick(kitchen_sponge) approach(kitchen_island/top) wipe(kitchen_island/top,kitchen_sponge) place(kitchen_sponge,kitchen_island/top)
* `return_sponge_home__dining` (v6_return_sponge_home__dining, 10 steps): look(kitchen_island/top) search(kitchen_sponge,dining_room_0_1) navigate(kitchen_sponge) pick(kitchen_sponge) navigate(kitchen_island/top) approach(kitchen_island/top) wipe(kitchen_island/top,kitchen_sponge) navigate(sponge_tray) approach(sponge_tray) place(kitchen_sponge,sponge_tray)
* `return_sponge_home__study` (v6_return_sponge_home__study, 10 steps): look(kitchen_island/top) search(kitchen_sponge,living_room_0_1) navigate(kitchen_sponge) pick(kitchen_sponge) navigate(kitchen_island/top) approach(kitchen_island/top) wipe(kitchen_island/top,kitchen_sponge) navigate(sponge_tray) approach(sponge_tray) place(kitchen_sponge,sponge_tray)
* `return_sponge_home__far_dining` (v6_return_sponge_home__far_dining, 10 steps): look(kitchen_island/top) search(kitchen_sponge,dining_room_0_0) navigate(kitchen_sponge) pick(kitchen_sponge) navigate(kitchen_island/top) approach(kitchen_island/top) wipe(kitchen_island/top,kitchen_sponge) navigate(sponge_tray) approach(sponge_tray) place(kitchen_sponge,sponge_tray)
* `which_surface__island` (v6_which_surface__island, 5 steps): look(kitchen_island/top) navigate(kitchen_sponge) pick(kitchen_sponge) wipe(kitchen_island/top,kitchen_sponge) place(kitchen_sponge,kitchen_island/top)
* `which_surface__dining` (v6_which_surface__dining, 9 steps): look(kitchen_island/top) navigate(kitchen_sponge) pick(kitchen_sponge) navigate(dining_table_2/top) look(dining_table_2/top) approach(dining_table_2/top) wipe(dining_table_2/top,kitchen_sponge) navigate(kitchen_island/top) place(kitchen_sponge,kitchen_island/top)

## T09_tomato_soup

### Control

* `lid_off` (nominal, 14 steps): look(kitchen_island/top) collect(['cherry_tomato_1', 'cherry_tomato_2'],handled_cooking_pot) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(handled_cooking_pot) stir(handled_cooking_pot,breakfast_spoon) navigate(kitchen_island/top) place(breakfast_spoon,kitchen_island/top) navigate(pot_lid) pick(pot_lid) navigate(handled_cooking_pot) cover(handled_cooking_pot,pot_lid) navigate(kitchen_stove) heat(cherry_tomato_1,kitchen_stove,60)

### Task-Level

* `pot_in_use__in_use` (v6_pot_in_use__in_use, 20 steps): look(kitchen_island/top) look(kitchen_stove/top) search(handled_cooking_pot,dining_room_0_1) navigate(handled_cooking_pot) pick(handled_cooking_pot) navigate(kitchen_stove/top) place(handled_cooking_pot,kitchen_stove/top,[8.7, 1.725]) collect(['cherry_tomato_1', 'cherry_tomato_2'],handled_cooking_pot) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(handled_cooking_pot) stir(handled_cooking_pot,breakfast_spoon) navigate(kitchen_island/top) place(breakfast_spoon,kitchen_island/top) navigate(pot_lid) pick(pot_lid) navigate(handled_cooking_pot) cover(handled_cooking_pot,pot_lid) navigate(kitchen_stove) heat(cherry_tomato_1,kitchen_stove,60)
* `pot_in_use__free` (v6_pot_in_use__free, 15 steps): look(kitchen_island/top) look(kitchen_stove/top) collect(['cherry_tomato_1', 'cherry_tomato_2'],handled_cooking_pot) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(handled_cooking_pot) stir(handled_cooking_pot,breakfast_spoon) navigate(kitchen_island/top) place(breakfast_spoon,kitchen_island/top) navigate(pot_lid) pick(pot_lid) navigate(handled_cooking_pot) cover(handled_cooking_pot,pot_lid) navigate(kitchen_stove) heat(cherry_tomato_1,kitchen_stove,60)
* `x6_gd_tomato_elsewhere__dining` (v6_x6_gd_tomato_elsewhere__dining, 19 steps): look(kitchen_island/top) +collect(['cherry_tomato_1'],handled_cooking_pot) +search(cherry_tomato_2,dining_room_0_1) +navigate(cherry_tomato_2) +pick(cherry_tomato_2) +navigate(handled_cooking_pot) +drop(cherry_tomato_2,handled_cooking_pot) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(handled_cooking_pot) stir(handled_cooking_pot,breakfast_spoon) navigate(kitchen_island/top) place(breakfast_spoon,kitchen_island/top) navigate(pot_lid) pick(pot_lid) navigate(handled_cooking_pot) cover(handled_cooking_pot,pot_lid) navigate(kitchen_stove) heat(cherry_tomato_1,kitchen_stove,60)
* `x6_gd_tomato_elsewhere__cabinet6` (v6_x6_gd_tomato_elsewhere__cabinet6, 19 steps): look(kitchen_island/top) +collect(['cherry_tomato_1'],handled_cooking_pot) +search(cherry_tomato_2,living_room_0_0) +navigate(cherry_tomato_2) +pick(cherry_tomato_2) +navigate(handled_cooking_pot) +drop(cherry_tomato_2,handled_cooking_pot) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(handled_cooking_pot) stir(handled_cooking_pot,breakfast_spoon) navigate(kitchen_island/top) place(breakfast_spoon,kitchen_island/top) navigate(pot_lid) pick(pot_lid) navigate(handled_cooking_pot) cover(handled_cooking_pot,pot_lid) navigate(kitchen_stove) heat(cherry_tomato_1,kitchen_stove,60)
* `pot_in_dining_room` (v6_pot_in_dining_room, 22 steps): look(kitchen_island/top) look(kitchen_stove/top) search(handled_cooking_pot,dining_room_0_1) navigate(handled_cooking_pot) pick(handled_cooking_pot) navigate(kitchen_stove/top) place(handled_cooking_pot,kitchen_stove/top,[8.41, 1.725]) +navigate(cherry_tomato_1) +sweep(['cherry_tomato_1', 'cherry_tomato_2'],0.12) +collect(['cherry_tomato_1', 'cherry_tomato_2'],handled_cooking_pot) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(handled_cooking_pot) stir(handled_cooking_pot,breakfast_spoon) navigate(kitchen_island/top) place(breakfast_spoon,kitchen_island/top) navigate(pot_lid) pick(pot_lid) navigate(handled_cooking_pot) cover(handled_cooking_pot,pot_lid) navigate(kitchen_stove) heat(cherry_tomato_1,kitchen_stove,60)

### Action + Task

* `lid_on_spoon_away` (hard_uncover_search_spoon, 18 steps): look(kitchen_island/top) !collect(['cherry_tomato_1', 'cherry_tomato_2'],handled_cooking_pot) navigate(handled_cooking_pot) +uncover(handled_cooking_pot) collect(['cherry_tomato_1', 'cherry_tomato_2'],handled_cooking_pot) +search(breakfast_spoon,living_room_0_0) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(handled_cooking_pot) stir(handled_cooking_pot,breakfast_spoon) navigate(kitchen_island/top) place(breakfast_spoon,kitchen_island/top) navigate(pot_lid) pick(pot_lid) navigate(handled_cooking_pot) cover(handled_cooking_pot,pot_lid) navigate(kitchen_stove) heat(cherry_tomato_1,kitchen_stove,60)
* `lid_on_spoon_away__alt_dining_table_2` (v6_lid_on_spoon_away__alt_dining_table_2, 18 steps): look(kitchen_island/top) !collect(['cherry_tomato_1', 'cherry_tomato_2'],handled_cooking_pot) navigate(handled_cooking_pot) +uncover(handled_cooking_pot) collect(['cherry_tomato_1', 'cherry_tomato_2'],handled_cooking_pot) +search(breakfast_spoon,dining_room_0_1) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(handled_cooking_pot) stir(handled_cooking_pot,breakfast_spoon) navigate(kitchen_island/top) place(breakfast_spoon,kitchen_island/top) navigate(pot_lid) pick(pot_lid) navigate(handled_cooking_pot) cover(handled_cooking_pot,pot_lid) navigate(kitchen_stove) heat(cherry_tomato_1,kitchen_stove,60)
* `tomato_in_fridge__in_fridge` (v6_tomato_in_fridge__in_fridge, 25 steps): look(kitchen_island/top) collect(['cherry_tomato_1', 'cherry_tomato_2'],handled_cooking_pot) navigate(breakfast_fridge) open(breakfast_fridge) bend() explore_furniture(breakfast_fridge) straighten() navigate(fridge_tomato) pick(fridge_tomato) retreat(breakfast_fridge,0.3) close(breakfast_fridge) navigate(handled_cooking_pot) drop(fridge_tomato,handled_cooking_pot) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(handled_cooking_pot) stir(handled_cooking_pot,breakfast_spoon) navigate(kitchen_island/top) place(breakfast_spoon,kitchen_island/top) navigate(pot_lid) pick(pot_lid) navigate(handled_cooking_pot) cover(handled_cooking_pot,pot_lid) navigate(kitchen_stove) heat(cherry_tomato_1,kitchen_stove,60)
* `tomato_in_fridge__on_island` (v6_tomato_in_fridge__on_island, 14 steps): look(kitchen_island/top) collect(['cherry_tomato_1', 'cherry_tomato_2', 'fridge_tomato'],handled_cooking_pot) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(handled_cooking_pot) stir(handled_cooking_pot,breakfast_spoon) navigate(kitchen_island/top) place(breakfast_spoon,kitchen_island/top) navigate(pot_lid) pick(pot_lid) navigate(handled_cooking_pot) cover(handled_cooking_pot,pot_lid) navigate(kitchen_stove) heat(cherry_tomato_1,kitchen_stove,60)

## T10_trash_the_can

### Control

* `can_on_island` (nominal, 8 steps): look(kitchen_island/top) explore_room(living_room_0_0) navigate(soda_can) pick(soda_can) lift(soda_can,0.95) navigate(trash_can) hover(soda_can,trash_can) drop(soda_can,trash_can)

### Task-Level

* `can_in_dining_room` (search_first, 8 steps): look(kitchen_island/top) explore_room(living_room_0_0) !pick(soda_can) +search(soda_can,dining_room_0_1) navigate(soda_can) pick(soda_can) navigate(trash_can) drop(soda_can,trash_can)
* `can_in_dining_room__alt_tv_stand_2` (v6_can_in_dining_room__alt_tv_stand_2, 8 steps): look(kitchen_island/top) explore_room(living_room_0_0) !pick(soda_can) +search(soda_can,living_room_0_0) navigate(soda_can) pick(soda_can) navigate(trash_can) drop(soda_can,trash_can)
* `keep_kids_can__kid_desk` (v6_keep_kids_can__kid_desk, 8 steps): look(kitchen_island/top) search(kids_can,living_room_0_1) navigate(soda_can) pick(soda_can) lift(soda_can,0.95) navigate(trash_can) hover(soda_can,trash_can) drop(soda_can,trash_can)
* `keep_kids_can__kid_island` (v6_keep_kids_can__kid_island, 8 steps): look(kitchen_island/top) search(soda_can,living_room_0_1) navigate(soda_can) pick(soda_can) lift(soda_can,0.95) navigate(trash_can) hover(soda_can,trash_can) drop(soda_can,trash_can)
* `trash_moved__dining` (v6_trash_moved__dining, 8 steps): look(kitchen_island/top) navigate(soda_can) pick(soda_can) lift(soda_can,0.95) search(trash_can,dining_room_0_1) navigate(trash_can) hover(soda_can,trash_can) drop(soda_can,trash_can)
* `trash_moved__bathroom` (v6_trash_moved__bathroom, 8 steps): look(kitchen_island/top) navigate(soda_can) pick(soda_can) lift(soda_can,0.95) search(trash_can,bathroom_0_1) navigate(trash_can) hover(soda_can,trash_can) drop(soda_can,trash_can)
* `after_dinner_clear__rubbish_leftovers` (v6_after_dinner_clear__rubbish_leftovers, 20 steps): look(dining_table_2/top) navigate(soda_can) pick(soda_can) lift(soda_can,0.95) navigate(trash_can) hover(soda_can,trash_can) drop(soda_can,trash_can) navigate(takeout_tray) pick(takeout_tray) lift(takeout_tray,0.95) navigate(trash_can) drop(takeout_tray,trash_can) navigate(breakfast_fridge) open(breakfast_fridge) navigate(leftovers) pick(leftovers) navigate(breakfast_fridge) place(leftovers,breakfast_fridge/inside_shelf) retreat(breakfast_fridge,0.3) close(breakfast_fridge)
* `after_dinner_clear__leftovers_mug` (v6_after_dinner_clear__leftovers_mug, 19 steps): look(dining_table_2/top) navigate(soda_can) pick(soda_can) lift(soda_can,0.95) navigate(trash_can) hover(soda_can,trash_can) drop(soda_can,trash_can) navigate(breakfast_fridge) open(breakfast_fridge) navigate(leftovers) pick(leftovers) navigate(breakfast_fridge) place(leftovers,breakfast_fridge/inside_shelf) retreat(breakfast_fridge,0.3) close(breakfast_fridge) navigate(used_mug) pick(used_mug) navigate(kitchen_counter_2/top) place(used_mug,kitchen_counter_2/top)
* `after_dinner_clear__rubbish_mug` (v6_after_dinner_clear__rubbish_mug, 16 steps): look(dining_table_2/top) navigate(soda_can) pick(soda_can) lift(soda_can,0.95) navigate(trash_can) hover(soda_can,trash_can) drop(soda_can,trash_can) navigate(takeout_tray) pick(takeout_tray) lift(takeout_tray,0.95) navigate(trash_can) drop(takeout_tray,trash_can) navigate(used_mug) pick(used_mug) navigate(kitchen_counter_2/top) place(used_mug,kitchen_counter_2/top)
* `guests_coming__can_mug_block` (v6_guests_coming__can_mug_block, 17 steps): look(kitchen_island/top) look(tv_stand_2/top) navigate(soda_can) pick(soda_can) lift(soda_can,0.95) navigate(trash_can) hover(soda_can,trash_can) drop(soda_can,trash_can) navigate(used_mug) pick(used_mug) navigate(kitchen_counter_2/top) place(used_mug,kitchen_counter_2/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(toy_box) approach(toy_box) place(wooden_block_a,toy_box)
* `guests_coming__can_block` (v6_guests_coming__can_block, 13 steps): look(kitchen_island/top) look(tv_stand_2/top) navigate(soda_can) pick(soda_can) lift(soda_can,0.95) navigate(trash_can) hover(soda_can,trash_can) drop(soda_can,trash_can) navigate(wooden_block_a) pick(wooden_block_a) navigate(toy_box) approach(toy_box) place(wooden_block_a,toy_box)
* `guests_coming__can_mug` (v6_guests_coming__can_mug, 12 steps): look(kitchen_island/top) look(tv_stand_2/top) navigate(soda_can) pick(soda_can) lift(soda_can,0.95) navigate(trash_can) hover(soda_can,trash_can) drop(soda_can,trash_can) navigate(used_mug) pick(used_mug) navigate(kitchen_counter_2/top) place(used_mug,kitchen_counter_2/top)
* `x6_gd_can_put_away__in_cabinet` (v6_x6_gd_can_put_away__in_cabinet, 15 steps): navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_microwave/inside_floor) close(kitchen_microwave) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(soda_can) pick(soda_can) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(trash_can) drop(soda_can,trash_can)
* `x6_gd_can_put_away__in_microwave` (v6_x6_gd_can_put_away__in_microwave, 15 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_microwave/inside_floor) navigate(soda_can) pick(soda_can) retreat(kitchen_microwave,0.3) close(kitchen_microwave) navigate(trash_can) drop(soda_can,trash_can)

## T11_collect_fruits

### Control

* `fruits_on_table` (nominal, 7 steps): navigate(dining_table_2/top) look(dining_table_2/top) navigate(apple) pick(apple) navigate(bookcase_2/top) look(bookcase_2/top) place(apple,fruit_basket)

### Task-Level

* `basket_missing` (alternative_tray, 11 steps): navigate(dining_table_2/top) look(dining_table_2/top) navigate(apple) pick(apple) navigate(bookcase_2/top) look(bookcase_2/top) !place(apple,fruit_basket) +navigate(desk_1/top) +look(desk_1/top) +navigate(serving_tray) +place(apple,serving_tray)
* `basket_gone_bowl_there` (v5x_basket_gone_bowl_there, 11 steps): navigate(dining_table_2/top) look(dining_table_2/top) navigate(apple) pick(apple) navigate(bookcase_2/top) look(bookcase_2/top) +identify(bowl_kitchen_cabinet) +navigate(desk_1/top) +look(desk_1/top) +navigate(serving_tray) +place(apple,serving_tray)
* `leave_one_for_kid__apple_orange` (v6_leave_one_for_kid__apple_orange, 10 steps): look(dining_table_2/top) search(fruit_basket,bedroom_0_1) navigate(apple) pick(apple) navigate(desk_1/top) place(apple,desk_1/top,[-0.9, -6.0]) navigate(lunch_orange) pick(lunch_orange) navigate(bookcase_2/top) place(lunch_orange,fruit_basket)
* `leave_one_for_kid__orange_banana` (v6_leave_one_for_kid__orange_banana, 10 steps): look(dining_table_2/top) search(fruit_basket,bedroom_0_1) navigate(lunch_banana) pick(lunch_banana) navigate(desk_1/top) place(lunch_banana,desk_1/top,[-0.9, -6.0]) navigate(lunch_orange) pick(lunch_orange) navigate(bookcase_2/top) place(lunch_orange,fruit_basket)
* `leave_one_for_kid__all_three` (v6_leave_one_for_kid__all_three, 14 steps): look(dining_table_2/top) search(fruit_basket,bedroom_0_1) navigate(apple) pick(apple) navigate(desk_1/top) place(apple,desk_1/top,[-0.9, -6.0]) navigate(lunch_orange) pick(lunch_orange) navigate(bookcase_2/top) place(lunch_orange,fruit_basket) navigate(lunch_banana) pick(lunch_banana) navigate(bookcase_2/top) place(lunch_banana,fruit_basket)
* `fruit_plate_for_guests__tray_in_study` (v6_fruit_plate_for_guests__tray_in_study, 14 steps): look(dining_table_2/top) search(fruit_tray,living_room_0_1) navigate(fruit_tray) pick(fruit_tray) navigate(tv_stand_2/top) place(fruit_tray,tv_stand_2/top,[7.5, 0.36]) navigate(apple) pick(apple) navigate(fruit_tray) place(apple,fruit_tray) navigate(lunch_orange) pick(lunch_orange) navigate(fruit_tray) place(lunch_orange,fruit_tray)
* `fruit_plate_for_guests__tray_by_table` (v6_fruit_plate_for_guests__tray_by_table, 14 steps): look(dining_table_2/top) search(fruit_tray,dining_room_0_1) navigate(fruit_tray) pick(fruit_tray) navigate(tv_stand_2/top) place(fruit_tray,tv_stand_2/top,[7.5, 0.36]) navigate(apple) pick(apple) navigate(fruit_tray) place(apple,fruit_tray) navigate(lunch_orange) pick(lunch_orange) navigate(fruit_tray) place(lunch_orange,fruit_tray)

## T12_tidy_toys

### Control

* `toys_out` (v5x_toys_out, 11 steps): explore_room(bedroom_0_1) explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket) +nod()

### Task-Level

* `duck_in_study` (explore_search_duck, 12 steps): explore_room(bedroom_0_1) explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) !navigate(rubber_duck) +search(rubber_duck,living_room_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket)
* `duck_in_study__alt_dining_table_2` (v6_duck_in_study__alt_dining_table_2, 12 steps): explore_room(bedroom_0_1) explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) !navigate(rubber_duck) +search(rubber_duck,dining_room_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket)
* `toys_everywhere` (hard_allocate_by_size, 14 steps): navigate(bookcase_2/top) look(bookcase_2/top) measure(toy_bin_small) measure(toy_tray) explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(toy_tray) place(toy_car,toy_tray) +search(rubber_duck,living_room_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(toy_bin_small) drop(rubber_duck,toy_bin_small)
* `toys_everywhere__alt_dining_table_2` (v6_toys_everywhere__alt_dining_table_2, 14 steps): navigate(bookcase_2/top) look(bookcase_2/top) measure(toy_bin_small) measure(toy_tray) explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(toy_tray) place(toy_car,toy_tray) +search(rubber_duck,dining_room_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(toy_bin_small) drop(rubber_duck,toy_bin_small)
* `find_all_toys__car_duck` (v6_find_all_toys__car_duck, 10 steps): explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) search(rubber_duck,living_room_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket)
* `find_all_toys__car_duck_bear` (v6_find_all_toys__car_duck_bear, 15 steps): explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) search(rubber_duck,bathroom_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket) search(teddy_bear,dining_room_0_1) navigate(teddy_bear) pick(teddy_bear) navigate(storage_basket) place(teddy_bear,storage_basket)
* `find_all_toys__all_four` (v6_find_all_toys__all_four, 20 steps): explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) search(rubber_duck,living_room_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket) search(teddy_bear,dining_room_0_1) navigate(teddy_bear) pick(teddy_bear) navigate(storage_basket) place(teddy_bear,storage_basket) search(stray_block,living_room_0_0) navigate(stray_block) pick(stray_block) navigate(storage_basket) place(stray_block,storage_basket)
* `castle_stays__tall_two_loose` (v6_castle_stays__tall_two_loose, 17 steps): explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket) navigate(loose_block_1) pick(loose_block_1) navigate(storage_basket) place(loose_block_1,storage_basket) navigate(loose_block_2) pick(loose_block_2) navigate(storage_basket) place(loose_block_2,storage_basket)
* `castle_stays__short_one_loose` (v6_castle_stays__short_one_loose, 13 steps): explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket) navigate(loose_block_1) pick(loose_block_1) navigate(storage_basket) place(loose_block_1,storage_basket)
* `castle_stays__tall_none_loose` (v6_castle_stays__tall_none_loose, 9 steps): explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket)

## T13_breakfast_setup

### Control

* `dishes_on_tv_stand` (nominal, 11 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1]) navigate(cup) pick(cup) navigate(dining_table_2/top) place(cup,dining_table_2/top,[3.2, 7.4])

### Action-Level

* `x6_pp_spoon_moved__early` (v6_x6_pp_spoon_moved__early, 16 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1]) +look(dining_table_2/top) +navigate(spoon) +pick(spoon) +navigate(dining_table_2/top) +place(spoon,dining_table_2/top,[2.98, 7.46]) navigate(cup) pick(cup) navigate(dining_table_2/top) place(cup,dining_table_2/top,[3.2, 7.4])
* `x6_pp_spoon_moved__table_end` (v6_x6_pp_spoon_moved__table_end, 16 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1]) navigate(cup) pick(cup) navigate(dining_table_2/top) place(cup,dining_table_2/top,[3.2, 7.4]) +look(dining_table_2/top) +navigate(spoon) +pick(spoon) +navigate(dining_table_2/top) +place(spoon,dining_table_2/top,[2.98, 7.46])

### Task-Level

* `no_cup` (alternative_mug, 13 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1]) !navigate(cup) +navigate(bookcase_2/top) +look(bookcase_2/top) +pick(mug) navigate(dining_table_2/top) place(mug,dining_table_2/top,[3.2, 7.4])
* `bowl_on_cabinet` (explore_search_bowl, 13 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(cup) pick(cup) navigate(dining_table_2/top) place(cup,dining_table_2/top,[3.2, 7.4]) !navigate(bowl) +search(bowl,living_room_0_0) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1])
* `bowl_on_cabinet__alt_dining_table_2` (v6_bowl_on_cabinet__alt_dining_table_2, 13 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(cup) pick(cup) navigate(dining_table_2/top) place(cup,dining_table_2/top,[3.2, 7.4]) !navigate(bowl) +search(bowl,dining_room_0_1) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1])
* `no_cup_bowl_on_cabinet` (hard_search_bowl_mug, 15 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) !navigate(bowl) +search(bowl,living_room_0_0) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1]) !navigate(cup) +navigate(bookcase_2/top) +look(bookcase_2/top) +pick(mug) navigate(dining_table_2/top) place(mug,dining_table_2/top,[3.2, 7.4])
* `no_cup_bowl_on_cabinet__alt_dining_table_2` (v6_no_cup_bowl_on_cabinet__alt_dining_table_2, 15 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) !navigate(bowl) +search(bowl,dining_room_0_1) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1]) !navigate(cup) +navigate(bookcase_2/top) +look(bookcase_2/top) +pick(mug) navigate(dining_table_2/top) place(mug,dining_table_2/top,[3.2, 7.4])
* `x6_pp_spoon_moved__tv_stand` (v6_x6_pp_spoon_moved__tv_stand, 17 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1]) navigate(cup) pick(cup) navigate(dining_table_2/top) place(cup,dining_table_2/top,[3.2, 7.4]) +look(dining_table_2/top) +search(spoon,living_room_0_0) +navigate(spoon) +pick(spoon) +navigate(dining_table_2/top) +place(spoon,dining_table_2/top,[2.98, 7.46])
* `x6_gd_bowl_put_away__in_cabinet` (v6_x6_gd_bowl_put_away__in_cabinet, 22 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_microwave/inside_floor) close(kitchen_microwave) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(bowl) pick(bowl) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1]) navigate(cup) pick(cup) navigate(dining_table_2/top) place(cup,dining_table_2/top,[3.2, 7.4])
* `x6_gd_bowl_put_away__in_microwave` (v6_x6_gd_bowl_put_away__in_microwave, 22 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_microwave/inside_floor) navigate(bowl) pick(bowl) retreat(kitchen_microwave,0.3) close(kitchen_microwave) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1]) navigate(cup) pick(cup) navigate(dining_table_2/top) place(cup,dining_table_2/top,[3.2, 7.4])
* `x6_gd_two_settings__cabinet6` (v6_x6_gd_two_settings__cabinet6, 20 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1]) navigate(cup) pick(cup) navigate(dining_table_2/top) place(cup,dining_table_2/top,[3.2, 7.4]) +navigate(bowl_kitchen_cabinet) +pick(bowl_kitchen_cabinet) +navigate(dining_table_2/top) +place(bowl_kitchen_cabinet,dining_table_2/top,[3.7, 7.12]) +search(mug,living_room_0_0) +navigate(mug) +pick(mug) +navigate(dining_table_2/top) +place(mug,dining_table_2/top,[3.62, 7.62])
* `x6_gd_two_settings__cabinet4` (v6_x6_gd_two_settings__cabinet4, 20 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1]) navigate(cup) pick(cup) navigate(dining_table_2/top) place(cup,dining_table_2/top,[3.2, 7.4]) +navigate(bowl_kitchen_cabinet) +pick(bowl_kitchen_cabinet) +navigate(dining_table_2/top) +place(bowl_kitchen_cabinet,dining_table_2/top,[3.7, 7.12]) +search(mug) +navigate(mug) +pick(mug) +navigate(dining_table_2/top) +place(mug,dining_table_2/top,[3.62, 7.62])

### Action + Task

* `no_cup_spoon_boxed_in` (hard_move_the_setting, 17 steps): navigate(dining_table_2/top) look(dining_table_2/top) navigate(spoon) pick(spoon) navigate(dining_table_2/top) place(spoon,dining_table_2/top,[3.02, 6.61]) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.0, 6.44]) +navigate(bookcase_2/top) +look(bookcase_2/top) +pick(mug) navigate(dining_table_2/top) place(mug,dining_table_2/top,[3.0, 6.78])
* `h_dynamic_mug_taken` (v5_h_dynamic_mug_taken, 17 steps): navigate(dining_table_2/top) look(dining_table_2/top) navigate(spoon) pick(spoon) navigate(dining_table_2/top) place(spoon,dining_table_2/top,[3.02, 6.61]) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.0, 6.47]) +search(mug,living_room_0_0) +navigate(mug) +pick(mug) navigate(dining_table_2/top) place(mug,dining_table_2/top,[3.0, 6.74])
* `h_dynamic_mug_taken__alt_dining_table_2` (v6_h_dynamic_mug_taken__alt_dining_table_2, 17 steps): navigate(dining_table_2/top) look(dining_table_2/top) navigate(spoon) pick(spoon) navigate(dining_table_2/top) place(spoon,dining_table_2/top,[3.02, 6.61]) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.0, 6.47]) +search(mug,dining_room_0_1) +navigate(mug) +pick(mug) navigate(dining_table_2/top) place(mug,dining_table_2/top,[3.0, 6.74])

## T15_book_face_up

### Control

* `book_free` (nominal, 3 steps): look(kitchen_island/top) navigate(paperback_book) flip(paperback_book)

### Action-Level

* `h_task_block_on_book` (v5_h_task_block_on_book, 6 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) place(wooden_block_a,kitchen_island/top,[7.2, 1.85]) navigate(paperback_book) flip(paperback_book)
* `h_dynamic_book_moved` (v5_h_dynamic_book_moved, 10 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) place(wooden_block_a,kitchen_island/top,[7.2, 1.85]) +look(kitchen_island/top) +navigate(wooden_block_a) +pick(wooden_block_a) +place(wooden_block_a,kitchen_island/top,[7.3, 1.85]) navigate(paperback_book) flip(paperback_book)

### Task-Level

* `book_out_of_view` (explore_search_book, 3 steps): +search(paperback_book,living_room_0_0) navigate(paperback_book) flip(paperback_book)

## T16_rolling_pin_at_edge

### Control

* `pin_free` (nominal, 3 steps): look(kitchen_island/top) navigate(rolling_pin) roll(rolling_pin,0.12)

### Action-Level

* `h_task_bowl_behind` (v5_h_task_bowl_behind, 5 steps): look(kitchen_island/top) navigate(oatmeal) +push(oatmeal,[0.0, 1.0],0.15) navigate(rolling_pin) roll(rolling_pin,0.12)
* `h_dynamic_bowl_put_behind` (v5_h_dynamic_bowl_put_behind, 7 steps): +look(kitchen_island/top) +look(oatmeal) navigate(oatmeal) pick(oatmeal) place(oatmeal,kitchen_island/top,[7.3, 1.85]) navigate(rolling_pin) roll(rolling_pin,0.12)

### Task-Level

* `pin_out_of_view` (explore_search_pin, 3 steps): +search(rolling_pin,living_room_0_0) navigate(rolling_pin) roll(rolling_pin,0.12)

## T17_hide_and_seek_block

### Control

* `lid_off` (v5fix_lid_off, 5 steps): navigate(kitchen_stove/top) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) hide(wooden_block_b,handled_cooking_pot,pot_lid)

### Action-Level

* `lid_on` (v5fix_lid_on, 10 steps): navigate(kitchen_stove/top) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) !hide(wooden_block_b,handled_cooking_pot,pot_lid) navigate(handled_cooking_pot) +uncover(handled_cooking_pot) navigate(kitchen_island/top) look(kitchen_island/top) hide(wooden_block_b,handled_cooking_pot,pot_lid)
* `block_crowded` (v5fix_block_crowded, 8 steps): navigate(kitchen_stove/top) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) !hide(wooden_block_b,handled_cooking_pot,pot_lid) navigate(wooden_block_b) +separate(wooden_block_b) hide(wooden_block_b,handled_cooking_pot,pot_lid)
* `lid_on_crowded` (v5fix_lid_on_crowded, 13 steps): navigate(kitchen_stove/top) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) !hide(wooden_block_b,handled_cooking_pot,pot_lid) navigate(handled_cooking_pot) +uncover(handled_cooking_pot) navigate(kitchen_island/top) look(kitchen_island/top) !hide(wooden_block_b,handled_cooking_pot,pot_lid) navigate(wooden_block_b) +separate(wooden_block_b) hide(wooden_block_b,handled_cooking_pot,pot_lid)

### Task-Level

* `h_task_lid_elsewhere` (v5_h_task_lid_elsewhere, 11 steps): navigate(kitchen_cabinet_6/top) look(kitchen_cabinet_6/top) navigate(pot_lid) pick(pot_lid) navigate(kitchen_stove/top) place(pot_lid,kitchen_stove/top,[8.715, 1.655]) navigate(handled_cooking_pot) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) hide(wooden_block_b,handled_cooking_pot,pot_lid)
* `x6_pp_lid_lifted__cabinet4` (v6_x6_pp_lid_lifted__cabinet4, 11 steps): navigate(kitchen_stove/top) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) hide(wooden_block_b,handled_cooking_pot,pot_lid) +look(kitchen_stove/top) +search(pot_lid) +navigate(pot_lid) +pick(pot_lid) +navigate(handled_cooking_pot) +cover(handled_cooking_pot,pot_lid)
* `x6_pp_lid_lifted__dining` (v6_x6_pp_lid_lifted__dining, 11 steps): navigate(kitchen_stove/top) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) hide(wooden_block_b,handled_cooking_pot,pot_lid) +look(kitchen_stove/top) +search(pot_lid,dining_room_0_1) +navigate(pot_lid) +pick(pot_lid) +navigate(handled_cooking_pot) +cover(handled_cooking_pot,pot_lid)
* `x6_gd_hide_both_event__tv_stand` (v6_x6_gd_hide_both_event__tv_stand, 11 steps): navigate(kitchen_stove/top) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) hide(wooden_block_b,handled_cooking_pot,pot_lid) +search(floor_block,living_room_0_0) +navigate(handled_cooking_pot) +uncover(handled_cooking_pot) +navigate(floor_block) +look(floor_block) +hide(floor_block,handled_cooking_pot,pot_lid)
* `x6_gd_hide_both_event__dining` (v6_x6_gd_hide_both_event__dining, 11 steps): navigate(kitchen_stove/top) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) hide(wooden_block_b,handled_cooking_pot,pot_lid) +search(floor_block,dining_room_0_1) +navigate(handled_cooking_pot) +uncover(handled_cooking_pot) +navigate(floor_block) +look(floor_block) +hide(floor_block,handled_cooking_pot,pot_lid)

### Action + Task

* `h_dynamic_lid_put_on` (v5_h_dynamic_lid_put_on, 16 steps): navigate(kitchen_cabinet_6/top) look(kitchen_cabinet_6/top) navigate(pot_lid) pick(pot_lid) navigate(kitchen_stove/top) place(pot_lid,kitchen_stove/top,[8.715, 1.655]) navigate(handled_cooking_pot) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) !hide(wooden_block_b,handled_cooking_pot,pot_lid) +navigate(handled_cooking_pot) +uncover(handled_cooking_pot) +navigate(kitchen_island/top) +look(kitchen_island/top) +hide(wooden_block_b,handled_cooking_pot,pot_lid)

## T18_check_cabinet_dishes

### Control

* `at_island` (nominal, 4 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) inspect(kitchen_cabinet_6) close(kitchen_cabinet_6)

### Action-Level

* `m_door_left_open` (v5_m_door_left_open, 3 steps): navigate(kitchen_cabinet_6) inspect(kitchen_cabinet_6) close(kitchen_cabinet_6)
* `x6_pp_door_reopened` (v6_x6_pp_door_reopened, 5 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) inspect(kitchen_cabinet_6) close(kitchen_cabinet_6) +close(kitchen_cabinet_6)

### Task-Level

* `h_task_two_cabinets` (v5_h_task_two_cabinets, 8 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) inspect(kitchen_cabinet_6) close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) inspect(kitchen_cabinet_4) close(kitchen_cabinet_4)
* `x6_gd_bowl_elsewhere__two_places` (v6_x6_gd_bowl_elsewhere__two_places, 8 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) inspect(kitchen_cabinet_6) close(kitchen_cabinet_6) navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_microwave/inside_floor) close(kitchen_microwave)
* `x6_gd_bowl_elsewhere__three_places` (v6_x6_gd_bowl_elsewhere__three_places, 12 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) inspect(kitchen_cabinet_6) close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) inspect(kitchen_cabinet_4) close(kitchen_cabinet_4) navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_microwave/inside_floor) close(kitchen_microwave)

### Action + Task

* `h_dynamic_door_closed` (v5_h_dynamic_door_closed, 10 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) !inspect(kitchen_cabinet_6) +open(kitchen_cabinet_6) +inspect(kitchen_cabinet_6) close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) inspect(kitchen_cabinet_4) close(kitchen_cabinet_4)

## T19_recycling

### Control

* `bin_on_bookcase` (nominal, 14 steps): explore_room(living_room_0_0) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(soda_can) pick(soda_can) navigate(bookcase_2/top) look(bookcase_2/top) navigate(wide_storage_bin) approach(wide_storage_bin) drop(soda_can,wide_storage_bin) navigate(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)

### Task-Level

* `m_can_in_dining_room` (v5_m_can_in_dining_room, 15 steps): explore_room(living_room_0_0) navigate(tv_stand_2/top) look(tv_stand_2/top) +search(soda_can,dining_room_0_1) navigate(soda_can) pick(soda_can) navigate(bookcase_2/top) look(bookcase_2/top) navigate(wide_storage_bin) approach(wide_storage_bin) drop(soda_can,wide_storage_bin) navigate(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)
* `m_can_in_dining_room__alt_tv_stand_2` (v6_m_can_in_dining_room__alt_tv_stand_2, 15 steps): explore_room(living_room_0_0) navigate(tv_stand_2/top) look(tv_stand_2/top) +search(soda_can,living_room_0_0) navigate(soda_can) pick(soda_can) navigate(bookcase_2/top) look(bookcase_2/top) navigate(wide_storage_bin) approach(wide_storage_bin) drop(soda_can,wide_storage_bin) navigate(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)
* `lookalike_bin` (v5x_lookalike_bin, 17 steps): explore_room(living_room_0_0) navigate(tv_stand_2/top) look(tv_stand_2/top) +search(soda_can,dining_room_0_1) navigate(soda_can) pick(soda_can) navigate(bookcase_2/top) look(bookcase_2/top) +identify(wide_storage_bin) navigate(wide_storage_bin) approach(wide_storage_bin) drop(soda_can,wide_storage_bin) navigate(foam_cube) +touch(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)
* `lookalike_bin__alt_tv_stand_2` (v6_lookalike_bin__alt_tv_stand_2, 17 steps): explore_room(living_room_0_0) navigate(tv_stand_2/top) look(tv_stand_2/top) +search(soda_can,living_room_0_0) navigate(soda_can) pick(soda_can) navigate(bookcase_2/top) look(bookcase_2/top) +identify(wide_storage_bin) navigate(wide_storage_bin) approach(wide_storage_bin) drop(soda_can,wide_storage_bin) navigate(foam_cube) +touch(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)
* `h_dynamic_cube_moved` (v5_h_dynamic_cube_moved, 16 steps): explore_room(living_room_0_0) navigate(tv_stand_2/top) look(tv_stand_2/top) +search(soda_can,dining_room_0_1) navigate(soda_can) pick(soda_can) navigate(bookcase_2/top) look(bookcase_2/top) navigate(wide_storage_bin) approach(wide_storage_bin) drop(soda_can,wide_storage_bin) +search(foam_cube,living_room_0_0) navigate(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)
* `h_dynamic_cube_moved__alt_kitchen_cabinet_6` (v6_h_dynamic_cube_moved__alt_kitchen_cabinet_6, 16 steps): explore_room(living_room_0_0) navigate(kitchen_cabinet_6/top) look(kitchen_cabinet_6/top) +search(soda_can,dining_room_0_1) navigate(soda_can) pick(soda_can) navigate(bookcase_2/top) look(bookcase_2/top) navigate(wide_storage_bin) approach(wide_storage_bin) drop(soda_can,wide_storage_bin) +search(foam_cube,living_room_0_0) navigate(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)
* `x6_gd_can_put_away__in_4` (v6_x6_gd_can_put_away__in_4, 24 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(soda_can) pick(soda_can) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(bookcase_2/top) look(bookcase_2/top) navigate(wide_storage_bin) approach(wide_storage_bin) drop(soda_can,wide_storage_bin) navigate(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)
* `x6_gd_can_put_away__in_6` (v6_x6_gd_can_put_away__in_6, 24 steps): navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() close(kitchen_cabinet_4) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(soda_can) pick(soda_can) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(bookcase_2/top) look(bookcase_2/top) navigate(wide_storage_bin) approach(wide_storage_bin) drop(soda_can,wide_storage_bin) navigate(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)

## T20_juice_back_to_table

### Control

* `bottle_on_cabinet` (nominal, 6 steps): navigate(kitchen_cabinet_6/top) look(kitchen_cabinet_6/top) navigate(juice_bottle) pick(juice_bottle) navigate(dining_table_2/top) place(juice_bottle,dining_table_2/top,[3.0, 7.3])

### Action-Level

* `table_full` (v5fix_table_full, 14 steps): navigate(dining_table_2/top) look(dining_table_2/top) navigate(party_bowl_1) approach(party_bowl_1) +look(party_bowl_1) pick(party_bowl_1) place(party_bowl_1,buffet_tray_11) navigate(tv_stand_2/top) navigate(kitchen_cabinet_6/top) look(kitchen_cabinet_6/top) navigate(juice_bottle) pick(juice_bottle) navigate(dining_table_2/top) place(juice_bottle,dining_table_2/top,[2.945, 7.765])

### Task-Level

* `m_bottle_on_tv_stand` (v5_m_bottle_on_tv_stand, 5 steps): search(juice_bottle,living_room_0_0) navigate(juice_bottle) pick(juice_bottle) navigate(dining_table_2/top) place(juice_bottle,dining_table_2/top,[3.0, 7.3])
* `m_bottle_on_tv_stand__alt_dining_table_2` (v6_m_bottle_on_tv_stand__alt_dining_table_2, 5 steps): search(juice_bottle,dining_room_0_1) navigate(juice_bottle) pick(juice_bottle) navigate(dining_table_2/top) place(juice_bottle,dining_table_2/top,[3.0, 7.3])
* `x6_gd_bottle_put_away__in_cabinet_4` (v6_x6_gd_bottle_put_away__in_cabinet_4, 17 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(juice_bottle) pick(juice_bottle) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(dining_table_2/top) place(juice_bottle,dining_table_2/top,[3.0, 7.3])
* `x6_gd_bottle_put_away__in_cabinet_6` (v6_x6_gd_bottle_put_away__in_cabinet_6, 17 steps): navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() close(kitchen_cabinet_4) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(juice_bottle) pick(juice_bottle) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(dining_table_2/top) place(juice_bottle,dining_table_2/top,[3.0, 7.3])

### Action + Task

* `h_dynamic_bottle_taken` (v5_h_dynamic_bottle_taken, 15 steps): navigate(dining_table_2/top) look(dining_table_2/top) navigate(party_bowl_1) approach(party_bowl_1) +look(party_bowl_1) pick(party_bowl_1) place(party_bowl_1,buffet_tray_11) navigate(tv_stand_2/top) navigate(kitchen_cabinet_6/top) look(kitchen_cabinet_6/top) +search(juice_bottle,living_room_0_0) navigate(juice_bottle) pick(juice_bottle) navigate(dining_table_2/top) place(juice_bottle,dining_table_2/top,[2.945, 7.765])
* `h_dynamic_bottle_taken__alt_kitchen_cabinet_4` (v6_h_dynamic_bottle_taken__alt_kitchen_cabinet_4, 15 steps): navigate(dining_table_2/top) look(dining_table_2/top) navigate(party_bowl_1) approach(party_bowl_1) +look(party_bowl_1) pick(party_bowl_1) place(party_bowl_1,buffet_tray_11) navigate(kitchen_cabinet_4/top) navigate(kitchen_cabinet_6/top) look(kitchen_cabinet_6/top) +search(juice_bottle) navigate(juice_bottle) pick(juice_bottle) navigate(dining_table_2/top) place(juice_bottle,dining_table_2/top,[2.945, 7.765])

## T14_shelve_the_book

### Control

* `e1_book_ready` (v5_e1_book_ready, 6 steps): navigate(desk_1/top) look(desk_1/top) navigate(book_red) pick(book_red) navigate(bookcase_2/top) place(book_red,bookcase_2/top)

### Action-Level

* `book_on_desk` (v5fix_book_on_desk, 8 steps): navigate(desk_1/top) look(desk_1/top) navigate(book_red) expose(book_red) +look(book_red) pick(book_red) navigate(bookcase_2/top) place(book_red,bookcase_2/top)
* `shelf_taken` (v5fix_shelf_taken, 13 steps): navigate(bookcase_2/top) look(bookcase_2/top) navigate(mug_shelf) pick(mug_shelf) place(mug_shelf,bookcase_2/top,[0.79, -0.31]) navigate(desk_1/top) look(desk_1/top) navigate(book_red) expose(book_red) +look(desk_1/top) pick(book_red) navigate(bookcase_2/top) place(book_red,bookcase_2/top)
* `h_dynamic_shelf_taken` (v5_h_dynamic_shelf_taken, 15 steps): navigate(desk_1/top) look(desk_1/top) +navigate(bookcase_2/top) +look(bookcase_2/top) +navigate(mug_shelf) +pick(mug_shelf) +place(mug_shelf,bookcase_2/top,[0.79, -0.31]) +navigate(desk_1/top) +look(desk_1/top) +navigate(book_red) +expose(book_red) +look(book_red) +pick(book_red) +navigate(bookcase_2/top) +place(book_red,bookcase_2/top)

### Task-Level

* `x6_gd_book_put_away__in_4` (v6_x6_gd_book_put_away__in_4, 19 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(book_red) expose(book_red) +look(book_red) pick(book_red) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(bookcase_2/top) place(book_red,bookcase_2/top)
* `x6_gd_book_put_away__in_6` (v6_x6_gd_book_put_away__in_6, 19 steps): navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() close(kitchen_cabinet_4) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(book_red) expose(book_red) +look(book_red) pick(book_red) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(bookcase_2/top) place(book_red,bookcase_2/top)
