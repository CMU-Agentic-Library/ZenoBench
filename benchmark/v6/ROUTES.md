# v6 oracle reference routes

One line per layout of each variant (`!` expected to fail, `+` recovery step). Seeds: the variant's manifest in tasks.json.

## T01_book_to_dining_table

### Control

* `overhang_ready` (v5fix_overhang_ready, 6 steps): look(kitchen_island/top) navigate(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.5])

### Task-Level

* `which_book__living` (v6_which_book__living, 8 steps): look(kitchen_island/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.5])
* `which_book__bedroom` (v6_which_book__bedroom, 8 steps): look(kitchen_island/top) navigate(bookcase_2/top) look(bookcase_2/top) navigate(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.5])

### Action + Task

* `table_seats__seats_a` (v6_table_seats__seats_a, 7 steps): look(kitchen_island/top) navigate(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 7.059])
* `table_seats__seats_b` (v6_table_seats__seats_b, 7 steps): look(kitchen_island/top) navigate(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.138])
* `table_seats__seats_c` (v6_table_seats__seats_c, 7 steps): look(kitchen_island/top) navigate(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.35])
* `table_seats__seats_a_flat` (v6_table_seats__seats_a_flat, 8 steps): look(kitchen_island/top) navigate(paperback_book) expose(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 7.059])
* `table_seats__seats_b_flat` (v6_table_seats__seats_b_flat, 8 steps): look(kitchen_island/top) navigate(paperback_book) expose(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.138])
* `table_seats__seats_c_flat` (v6_table_seats__seats_c_flat, 8 steps): look(kitchen_island/top) navigate(paperback_book) expose(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.35])
* `which_table__near_a` (v6_which_table__near_a, 7 steps): look(kitchen_island/top) navigate(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 7.059])
* `which_table__near_b` (v6_which_table__near_b, 7 steps): look(kitchen_island/top) navigate(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.138])
* `which_table__far_a` (v6_which_table__far_a, 9 steps): look(kitchen_island/top) navigate(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) navigate(dining_table_1/top) look(dining_table_1/top) place(paperback_book,dining_table_1/top,[-7.607, 8.179])
* `which_table__far_b` (v6_which_table__far_b, 9 steps): look(kitchen_island/top) navigate(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) navigate(dining_table_1/top) look(dining_table_1/top) place(paperback_book,dining_table_1/top,[-7.607, 7.508])
* `which_table__near_a_flat` (v6_which_table__near_a_flat, 8 steps): look(kitchen_island/top) navigate(paperback_book) expose(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 7.059])
* `which_table__near_b_flat` (v6_which_table__near_b_flat, 8 steps): look(kitchen_island/top) navigate(paperback_book) expose(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.138])
* `which_table__far_a_flat` (v6_which_table__far_a_flat, 10 steps): look(kitchen_island/top) navigate(paperback_book) expose(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) navigate(dining_table_1/top) look(dining_table_1/top) place(paperback_book,dining_table_1/top,[-7.607, 8.179])
* `which_table__far_b_flat` (v6_which_table__far_b_flat, 10 steps): look(kitchen_island/top) navigate(paperback_book) expose(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) navigate(dining_table_1/top) look(dining_table_1/top) place(paperback_book,dining_table_1/top,[-7.607, 7.508])
* `no_room_fallback__seats_b` (v6_no_room_fallback__seats_b, 7 steps): look(kitchen_island/top) navigate(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.138])
* `no_room_fallback__seats_c` (v6_no_room_fallback__seats_c, 7 steps): look(kitchen_island/top) navigate(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.35])
* `no_room_fallback__full_a` (v6_no_room_fallback__full_a, 8 steps): look(kitchen_island/top) navigate(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) navigate(bookcase_2/top) place(paperback_book,bookcase_2/top,[1.15, -0.43])
* `no_room_fallback__seats_b_flat` (v6_no_room_fallback__seats_b_flat, 8 steps): look(kitchen_island/top) navigate(paperback_book) expose(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.138])
* `no_room_fallback__seats_c_flat` (v6_no_room_fallback__seats_c_flat, 8 steps): look(kitchen_island/top) navigate(paperback_book) expose(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.35])
* `no_room_fallback__full_a_flat` (v6_no_room_fallback__full_a_flat, 9 steps): look(kitchen_island/top) navigate(paperback_book) expose(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) navigate(bookcase_2/top) place(paperback_book,bookcase_2/top,[1.15, -0.43])
* `reader_seat__mug_1` (v6_reader_seat__mug_1, 7 steps): look(kitchen_island/top) navigate(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 5.69])
* `reader_seat__mug_2` (v6_reader_seat__mug_2, 7 steps): look(kitchen_island/top) navigate(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.428])
* `reader_seat__mug_3` (v6_reader_seat__mug_3, 7 steps): look(kitchen_island/top) navigate(paperback_book) +look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 7.094])
* `reader_seat__mug_1_flat` (v6_reader_seat__mug_1_flat, 8 steps): look(kitchen_island/top) navigate(paperback_book) expose(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 5.69])
* `reader_seat__mug_2_flat` (v6_reader_seat__mug_2_flat, 8 steps): look(kitchen_island/top) navigate(paperback_book) expose(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 6.428])
* `reader_seat__mug_3_flat` (v6_reader_seat__mug_3_flat, 8 steps): look(kitchen_island/top) navigate(paperback_book) expose(paperback_book) look(paperback_book) pick(paperback_book) navigate(dining_table_2/top) look(dining_table_2/top) place(paperback_book,dining_table_2/top,[3.72, 7.094])

## T02_stack_blocks

### Control

* `clear` (nominal, 6 steps): look(kitchen_island/top) navigate(wooden_block_b) pick(wooden_block_b) rotate(wooden_block_b,30) navigate(wooden_block_a) stack(wooden_block_b,wooden_block_a)

### Task-Level

* `crowded_use_another__tight_tv` (v6_crowded_use_another__tight_tv, 8 steps): look(kitchen_island/top) navigate(wooden_block_b) look(wooden_block_b) search(floor_block,living_room_0_0) navigate(floor_block) pick(floor_block) navigate(wooden_block_a) stack(floor_block,wooden_block_a)
* `crowded_use_another__tight_dining` (v6_crowded_use_another__tight_dining, 8 steps): look(kitchen_island/top) navigate(wooden_block_b) look(wooden_block_b) search(floor_block,dining_room_0_1) navigate(floor_block) pick(floor_block) navigate(wooden_block_a) stack(floor_block,wooden_block_a)
* `crowded_use_another__loose` (v6_crowded_use_another__loose, 6 steps): look(kitchen_island/top) navigate(wooden_block_b) pick(wooden_block_b) rotate(wooden_block_b,30) navigate(wooden_block_a) stack(wooden_block_b,wooden_block_a)
* `third_toy_elsewhere__duck` (v6_third_toy_elsewhere__duck, 11 steps): look(kitchen_island/top) navigate(wooden_block_b) pick(wooden_block_b) rotate(wooden_block_b,30) navigate(wooden_block_a) stack(wooden_block_b,wooden_block_a) +search(rubber_duck,dining_room_0_1) +navigate(rubber_duck) +pick(rubber_duck) +navigate(wooden_block_a) +stack(rubber_duck,wooden_block_b)
* `third_toy_elsewhere__toy_block` (v6_third_toy_elsewhere__toy_block, 11 steps): look(kitchen_island/top) navigate(wooden_block_b) pick(wooden_block_b) rotate(wooden_block_b,30) navigate(wooden_block_a) stack(wooden_block_b,wooden_block_a) +search(toy_block,kitchen_0_1) +navigate(toy_block) +pick(toy_block) +navigate(wooden_block_a) +stack(toy_block,wooden_block_b)
* `tower_for_kid__counter` (v6_tower_for_kid__counter, 16 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(dining_table_2/top) look(dining_table_2/top) place(wooden_block_a,dining_table_2/top,[3.7, 6.6]) search(wooden_block_b,living_room_0_0) navigate(wooden_block_b) pick(wooden_block_b) navigate(wooden_block_a) stack(wooden_block_b,wooden_block_a) search(floor_block,kitchen_0_1) navigate(floor_block) pick(floor_block) navigate(wooden_block_a) stack(floor_block,wooden_block_b)
* `tower_for_kid__study` (v6_tower_for_kid__study, 16 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(dining_table_2/top) look(dining_table_2/top) place(wooden_block_a,dining_table_2/top,[3.7, 6.6]) search(floor_block,living_room_0_0) navigate(floor_block) pick(floor_block) navigate(wooden_block_a) stack(floor_block,wooden_block_a) search(wooden_block_b,living_room_0_1) navigate(wooden_block_b) pick(wooden_block_b) navigate(wooden_block_a) stack(wooden_block_b,floor_block)
* `tower_for_kid_duck__counter` (v6_tower_for_kid_duck__counter, 16 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(dining_table_2/top) look(dining_table_2/top) place(wooden_block_a,dining_table_2/top,[3.7, 6.6]) search(wooden_block_b,living_room_0_0) navigate(wooden_block_b) pick(wooden_block_b) navigate(wooden_block_a) stack(wooden_block_b,wooden_block_a) search(rubber_duck,kitchen_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(wooden_block_a) stack(rubber_duck,wooden_block_b)
* `tower_for_kid_duck__study` (v6_tower_for_kid_duck__study, 16 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(dining_table_2/top) look(dining_table_2/top) place(wooden_block_a,dining_table_2/top,[3.7, 6.6]) search(wooden_block_b,living_room_0_1) navigate(wooden_block_b) pick(wooden_block_b) navigate(wooden_block_a) stack(wooden_block_b,wooden_block_a) search(rubber_duck,living_room_0_0) navigate(rubber_duck) pick(rubber_duck) navigate(wooden_block_a) stack(rubber_duck,wooden_block_b)

### Action + Task

* `block_put_away__in_4` (v6_block_put_away__in_4, 22 steps): look(kitchen_island/top) navigate(wooden_block_a) +pick(wooden_block_a) navigate(wooden_block_b) +stack(wooden_block_a,wooden_block_b) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(floor_block) pick(floor_block) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(wooden_block_a) stack(floor_block,wooden_block_a)
* `block_put_away__in_6` (v6_block_put_away__in_6, 22 steps): look(kitchen_island/top) navigate(wooden_block_a) +pick(wooden_block_a) navigate(wooden_block_b) +stack(wooden_block_a,wooden_block_b) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() close(kitchen_cabinet_4) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(floor_block) pick(floor_block) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(wooden_block_a) stack(floor_block,wooden_block_a)

## T03_utensils_one_container

### Control

* `large_only` (nominal, 10 steps): look(kitchen_island/top) look(tv_stand_2/top) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(wide_storage_bin) drop(breakfast_spoon,wide_storage_bin) navigate(rolling_pin) pick(rolling_pin) navigate(wide_storage_bin) place(rolling_pin,wide_storage_bin)

### Task-Level

* `small_bin_or_bedroom_bin__on_island` (v6_small_bin_or_bedroom_bin__on_island, 14 steps): look(kitchen_island/top) measure(small_storage_bin) measure(rolling_pin) search(wide_storage_bin,bedroom_0_1) navigate(bookcase_2/top) look(bookcase_2/top) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(wide_storage_bin) drop(breakfast_spoon,wide_storage_bin) navigate(rolling_pin) pick(rolling_pin) navigate(wide_storage_bin) place(rolling_pin,wide_storage_bin)
* `small_bin_or_bedroom_bin__beside_wide_bin` (v6_small_bin_or_bedroom_bin__beside_wide_bin, 14 steps): look(kitchen_island/top) search(wide_storage_bin,bedroom_0_1) navigate(bookcase_2/top) look(bookcase_2/top) measure(small_storage_bin) measure(rolling_pin) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(wide_storage_bin) drop(breakfast_spoon,wide_storage_bin) navigate(rolling_pin) pick(rolling_pin) navigate(wide_storage_bin) place(rolling_pin,wide_storage_bin)
* `which_bin_by_contents__toys_near` (v6_which_bin_by_contents__toys_near, 13 steps): look(kitchen_island/top) look(tv_stand_2/top) search(wide_storage_bin,bedroom_0_1) navigate(bookcase_2/top) look(bookcase_2/top) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(wide_storage_bin) drop(breakfast_spoon,wide_storage_bin) navigate(rolling_pin) pick(rolling_pin) navigate(wide_storage_bin) place(rolling_pin,wide_storage_bin)
* `which_bin_by_contents__tools_near` (v6_which_bin_by_contents__tools_near, 10 steps): look(kitchen_island/top) look(tv_stand_2/top) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(wide_storage_bin) drop(breakfast_spoon,wide_storage_bin) navigate(rolling_pin) pick(rolling_pin) navigate(wide_storage_bin) place(rolling_pin,wide_storage_bin)
* `no_bin_substitute__basket` (v6_no_bin_substitute__basket, 15 steps): look(kitchen_island/top) measure(rolling_pin) look(tv_stand_2/top) measure(small_storage_bin) search(storage_basket,bedroom_0_1) navigate(storage_basket) look(storage_basket) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(storage_basket) drop(breakfast_spoon,storage_basket) navigate(rolling_pin) pick(rolling_pin) navigate(storage_basket) place(rolling_pin,storage_basket)
* `no_bin_substitute__tray` (v6_no_bin_substitute__tray, 15 steps): look(kitchen_island/top) measure(rolling_pin) look(tv_stand_2/top) measure(small_storage_bin) search(serving_tray,living_room_0_1) navigate(serving_tray) look(serving_tray) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(serving_tray) place(breakfast_spoon,serving_tray) navigate(rolling_pin) pick(rolling_pin) navigate(serving_tray) place(rolling_pin,serving_tray)
* `utensils_apart__dining` (v6_utensils_apart__dining, 13 steps): look(kitchen_island/top) search(wide_storage_bin,bedroom_0_1) navigate(bookcase_2/top) look(bookcase_2/top) navigate(rolling_pin) pick(rolling_pin) navigate(wide_storage_bin) place(rolling_pin,wide_storage_bin) search(breakfast_spoon,dining_room_0_1) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(wide_storage_bin) drop(breakfast_spoon,wide_storage_bin)
* `utensils_apart__counter` (v6_utensils_apart__counter, 13 steps): look(kitchen_island/top) search(wide_storage_bin,bedroom_0_1) navigate(bookcase_2/top) look(bookcase_2/top) navigate(rolling_pin) pick(rolling_pin) navigate(wide_storage_bin) place(rolling_pin,wide_storage_bin) search(breakfast_spoon,kitchen_0_1) navigate(breakfast_spoon) pick(breakfast_spoon) navigate(wide_storage_bin) drop(breakfast_spoon,wide_storage_bin)

## T04_cup_or_mug_to_cabinet

### Control

* `cup_available` (nominal, 5 steps): look(kitchen_island/top) navigate(cup_counter_b) pick(cup_counter_b) navigate(kitchen_cabinet_6/top) place(cup_counter_b,kitchen_cabinet_6/top)

### Task-Level

* `no_cup` (alternative_mug, 7 steps): look(kitchen_island/top) count(cup) !search(cup) +navigate(mug) +pick(mug) navigate(kitchen_cabinet_6/top) place(mug,kitchen_cabinet_6/top)
* `no_cup_mug_away` (hard_count_search_mug, 8 steps): look(kitchen_island/top) count(cup) !search(cup) +search(mug,living_room_0_0) navigate(mug) pick(mug) navigate(kitchen_cabinet_6/top) place(mug,kitchen_cabinet_6/top)
* `no_cup_mug_away__alt_dining_table_2` (v6_no_cup_mug_away__alt_dining_table_2, 8 steps): look(kitchen_island/top) count(cup) !search(cup) +search(mug,dining_room_0_1) navigate(mug) pick(mug) navigate(kitchen_cabinet_6/top) place(mug,kitchen_cabinet_6/top)
* `clear_the_drinks_spot` (v6_clear_the_drinks_spot, 15 steps): look(kitchen_island/top) navigate(kitchen_cabinet_6/top) look(kitchen_cabinet_6/top) navigate(oatmeal) pick(oatmeal) navigate(kitchen_island/top) place(oatmeal,kitchen_island/top,[6.7, 1.84]) navigate(pot_lid) pick(pot_lid) navigate(kitchen_island/top) place(pot_lid,kitchen_island/top,[7.1, 1.85]) navigate(cup_counter_b) pick(cup_counter_b) navigate(kitchen_cabinet_6/top) place(cup_counter_b,kitchen_cabinet_6/top)
* `two_guests__dining` (v6_two_guests__dining, 10 steps): look(kitchen_island/top) navigate(cup_counter_b) pick(cup_counter_b) navigate(kitchen_cabinet_6/top) place(cup_counter_b,kitchen_cabinet_6/top,[3.36, 0.36]) search(mug,dining_room_0_1) navigate(mug) pick(mug) navigate(kitchen_cabinet_6/top) place(mug,kitchen_cabinet_6/top,[3.62, 0.36])
* `two_guests__study` (v6_two_guests__study, 10 steps): look(kitchen_island/top) navigate(cup_counter_b) pick(cup_counter_b) navigate(kitchen_cabinet_6/top) place(cup_counter_b,kitchen_cabinet_6/top,[3.36, 0.36]) search(mug,living_room_0_1) navigate(mug) pick(mug) navigate(kitchen_cabinet_6/top) place(mug,kitchen_cabinet_6/top,[3.62, 0.36])
* `x6_gd_cup_in_cabinets__cup_in_4` (v6_x6_gd_cup_in_cabinets__cup_in_4, 18 steps): look(kitchen_island/top) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(cup_counter_b) pick(cup_counter_b) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(kitchen_cabinet_6/top) place(cup_counter_b,kitchen_cabinet_6/top)
* `x6_gd_cup_in_cabinets__cup_in_6` (v6_x6_gd_cup_in_cabinets__cup_in_6, 18 steps): look(kitchen_island/top) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() close(kitchen_cabinet_4) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(cup_counter_b) pick(cup_counter_b) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(kitchen_cabinet_6/top) place(cup_counter_b,kitchen_cabinet_6/top)

## T05_pen_or_pencil_to_desk

### Control

* `e1_pencil_asked` (v5_e1_pencil_asked, 7 steps): navigate(bookcase_2/top) look(bookcase_2/top) +navigate(pencil) +pick(pencil) +present(pencil) navigate(desk_1/top) place(pencil,desk_1/top)

### Task-Level

* `no_pen_pencil_away` (v5fix_hard_search_pencil, 9 steps): navigate(bookcase_2/top) look(bookcase_2/top) !navigate(pen) +navigate(dining_table_2/top) +look(dining_table_2/top) navigate(pencil) pick(pencil) navigate(desk_1/top) place(pencil,desk_1/top)
* `check_desk_first__pen_on_desk` (v6_check_desk_first__pen_on_desk, 3 steps): navigate(desk_1/top) look(desk_1/top) identify(pen)
* `check_desk_first__pencil_on_desk` (v6_check_desk_first__pencil_on_desk, 8 steps): navigate(desk_1/top) look(desk_1/top) identify(pencil) search(pen,bedroom_0_1) navigate(pen) pick(pen) navigate(desk_1/top) place(pen,desk_1/top,[-0.3, -5.95])
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

## T06_block_destination_occupied

### Control

* `free` (nominal, 5 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(kitchen_cabinet_6/top) place(wooden_block_a,kitchen_cabinet_6/top)

### Task-Level

* `display_row__island_floor` (v6_display_row__island_floor, 14 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(kitchen_cabinet_6/top) place(wooden_block_a,kitchen_cabinet_6/top,[3.32, 0.45]) navigate(wooden_block_b) pick(wooden_block_b) navigate(kitchen_cabinet_6/top) place(wooden_block_b,kitchen_cabinet_6/top,[3.5, 0.45]) search(floor_block,living_room_0_0) navigate(floor_block) pick(floor_block) navigate(kitchen_cabinet_6/top) place(floor_block,kitchen_cabinet_6/top,[3.68, 0.45])
* `display_row__spread` (v6_display_row__spread, 15 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(kitchen_cabinet_6/top) place(wooden_block_a,kitchen_cabinet_6/top,[3.32, 0.45]) search(wooden_block_b,dining_room_0_1) navigate(wooden_block_b) pick(wooden_block_b) navigate(kitchen_cabinet_6/top) place(wooden_block_b,kitchen_cabinet_6/top,[3.5, 0.45]) search(floor_block,kitchen_0_1) navigate(floor_block) pick(floor_block) navigate(kitchen_cabinet_6/top) place(floor_block,kitchen_cabinet_6/top,[3.68, 0.45])
* `display_spot_or_tv__front_taken` (v6_display_spot_or_tv__front_taken, 6 steps): look(kitchen_island/top) look(kitchen_cabinet_6/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(tv_stand_2/top) place(wooden_block_a,tv_stand_2/top)
* `display_spot_or_tv__front_free` (v6_display_spot_or_tv__front_free, 6 steps): look(kitchen_island/top) look(kitchen_cabinet_6/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(kitchen_cabinet_6/top) place(wooden_block_a,kitchen_cabinet_6/top,[3.433, 0.465])
* `display_spot_or_tv__front_taken_block_away` (v6_display_spot_or_tv__front_taken_block_away, 7 steps): look(kitchen_island/top) look(kitchen_cabinet_6/top) search(wooden_block_a,dining_room_0_1) navigate(wooden_block_a) pick(wooden_block_a) navigate(tv_stand_2/top) place(wooden_block_a,tv_stand_2/top)
* `display_spot_or_tv__front_free_block_away` (v6_display_spot_or_tv__front_free_block_away, 7 steps): look(kitchen_island/top) look(kitchen_cabinet_6/top) search(wooden_block_a,bedroom_0_1) navigate(wooden_block_a) pick(wooden_block_a) navigate(kitchen_cabinet_6/top) place(wooden_block_a,kitchen_cabinet_6/top,[3.433, 0.465])
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
* `two_portions__dining` (v6_two_portions__dining, 21 steps): search(soup_pot,dining_room_0_1) navigate(soup_pot) pick(soup_pot) navigate(kitchen_stove/top) place(soup_pot,kitchen_stove/top,[8.41, 1.725]) press(kitchen_stove/power_button) navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_island/top) navigate(oatmeal_bowl) pick(oatmeal_bowl) navigate(kitchen_microwave/inside_floor) place(oatmeal_bowl,kitchen_microwave/inside_floor) close(kitchen_microwave) navigate(kitchen_microwave/start_button) press(kitchen_microwave/start_button) wait(25) stop(kitchen_microwave) close(kitchen_microwave) navigate(kitchen_stove) stop(kitchen_stove)
* `two_portions__counter` (v6_two_portions__counter, 21 steps): search(soup_pot,kitchen_0_1) navigate(soup_pot) pick(soup_pot) navigate(kitchen_stove/top) place(soup_pot,kitchen_stove/top,[8.41, 1.725]) press(kitchen_stove/power_button) navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_island/top) navigate(oatmeal_bowl) pick(oatmeal_bowl) navigate(kitchen_microwave/inside_floor) place(oatmeal_bowl,kitchen_microwave/inside_floor) close(kitchen_microwave) navigate(kitchen_microwave/start_button) press(kitchen_microwave/start_button) wait(25) stop(kitchen_microwave) close(kitchen_microwave) navigate(kitchen_stove) stop(kitchen_stove)

## T08_wipe_island

### Control

* `sponge_on_island` (nominal, 6 steps): look(kitchen_island/top) look(tv_stand_2/top) navigate(kitchen_sponge) pick(kitchen_sponge) wipe(kitchen_island/top,kitchen_sponge) place(kitchen_sponge,kitchen_island/top)

### Task-Level

* `far_sponge_tv` (hard_search_approach, 6 steps): +search(kitchen_sponge,living_room_0_0) navigate(kitchen_sponge) pick(kitchen_sponge) navigate(kitchen_island/top) wipe(kitchen_island/top,kitchen_sponge) place(kitchen_sponge,kitchen_island/top)
* `far_sponge_tv__alt_dining_table_2` (v6_far_sponge_tv__alt_dining_table_2, 6 steps): +search(kitchen_sponge,dining_room_0_1) navigate(kitchen_sponge) pick(kitchen_sponge) navigate(kitchen_island/top) wipe(kitchen_island/top,kitchen_sponge) place(kitchen_sponge,kitchen_island/top)
* `wipe_and_sort__blocks` (v6_wipe_and_sort__blocks, 15 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(toy_box) place(wooden_block_a,toy_box) navigate(wooden_block_b) pick(wooden_block_b) navigate(toy_box) place(wooden_block_b,toy_box) look(tv_stand_2/top) navigate(kitchen_sponge) pick(kitchen_sponge) navigate(kitchen_island/top) wipe(kitchen_island/top,kitchen_sponge) place(kitchen_sponge,kitchen_island/top)
* `wipe_and_sort__duck` (v6_wipe_and_sort__duck, 15 steps): look(kitchen_island/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(toy_box) place(wooden_block_a,toy_box) navigate(rubber_duck) pick(rubber_duck) navigate(toy_box) place(rubber_duck,toy_box) look(tv_stand_2/top) navigate(kitchen_sponge) pick(kitchen_sponge) navigate(kitchen_island/top) wipe(kitchen_island/top,kitchen_sponge) place(kitchen_sponge,kitchen_island/top)
* `return_sponge_home__dining` (v6_return_sponge_home__dining, 8 steps): look(kitchen_island/top) search(kitchen_sponge,dining_room_0_1) navigate(kitchen_sponge) pick(kitchen_sponge) navigate(kitchen_island/top) wipe(kitchen_island/top,kitchen_sponge) navigate(sponge_tray) place(kitchen_sponge,sponge_tray)
* `return_sponge_home__study` (v6_return_sponge_home__study, 8 steps): look(kitchen_island/top) search(kitchen_sponge,living_room_0_1) navigate(kitchen_sponge) pick(kitchen_sponge) navigate(kitchen_island/top) wipe(kitchen_island/top,kitchen_sponge) navigate(sponge_tray) place(kitchen_sponge,sponge_tray)
* `return_sponge_home__far_dining` (v6_return_sponge_home__far_dining, 8 steps): look(kitchen_island/top) search(kitchen_sponge,dining_room_0_0) navigate(kitchen_sponge) pick(kitchen_sponge) navigate(kitchen_island/top) wipe(kitchen_island/top,kitchen_sponge) navigate(sponge_tray) place(kitchen_sponge,sponge_tray)
* `which_surface__island` (v6_which_surface__island, 5 steps): look(kitchen_island/top) navigate(kitchen_sponge) pick(kitchen_sponge) wipe(kitchen_island/top,kitchen_sponge) place(kitchen_sponge,kitchen_island/top)
* `which_surface__dining` (v6_which_surface__dining, 9 steps): look(kitchen_island/top) navigate(kitchen_sponge) pick(kitchen_sponge) navigate(dining_table_2/top) look(dining_table_2/top) navigate(dining_table_2/top) wipe(dining_table_2/top,kitchen_sponge) navigate(kitchen_island/top) place(kitchen_sponge,kitchen_island/top)

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
* `guests_coming__can_mug_block` (v6_guests_coming__can_mug_block, 16 steps): look(kitchen_island/top) look(tv_stand_2/top) navigate(soda_can) pick(soda_can) lift(soda_can,0.95) navigate(trash_can) hover(soda_can,trash_can) drop(soda_can,trash_can) navigate(used_mug) pick(used_mug) navigate(kitchen_counter_2/top) place(used_mug,kitchen_counter_2/top) navigate(wooden_block_a) pick(wooden_block_a) navigate(toy_box) place(wooden_block_a,toy_box)
* `guests_coming__can_block` (v6_guests_coming__can_block, 12 steps): look(kitchen_island/top) look(tv_stand_2/top) navigate(soda_can) pick(soda_can) lift(soda_can,0.95) navigate(trash_can) hover(soda_can,trash_can) drop(soda_can,trash_can) navigate(wooden_block_a) pick(wooden_block_a) navigate(toy_box) place(wooden_block_a,toy_box)
* `guests_coming__can_mug` (v6_guests_coming__can_mug, 12 steps): look(kitchen_island/top) look(tv_stand_2/top) navigate(soda_can) pick(soda_can) lift(soda_can,0.95) navigate(trash_can) hover(soda_can,trash_can) drop(soda_can,trash_can) navigate(used_mug) pick(used_mug) navigate(kitchen_counter_2/top) place(used_mug,kitchen_counter_2/top)
* `x6_gd_can_put_away__in_cabinet` (v6_x6_gd_can_put_away__in_cabinet, 15 steps): navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_microwave/inside_floor) close(kitchen_microwave) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(soda_can) pick(soda_can) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(trash_can) drop(soda_can,trash_can)
* `x6_gd_can_put_away__in_microwave` (v6_x6_gd_can_put_away__in_microwave, 15 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_microwave/inside_floor) navigate(soda_can) pick(soda_can) retreat(kitchen_microwave,0.3) close(kitchen_microwave) navigate(trash_can) drop(soda_can,trash_can)
* `x6_gd_can_put_away__in_fridge` (v6_x6_gd_can_put_away__in_fridge, 21 steps): navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_microwave/inside_floor) close(kitchen_microwave) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(breakfast_fridge) open(breakfast_fridge) bend() explore_furniture(breakfast_fridge) straighten() navigate(soda_can) pick(soda_can) retreat(breakfast_fridge,0.3) close(breakfast_fridge) navigate(trash_can) drop(soda_can,trash_can)

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
* `bins_capacity__side_left_full` (v6_bins_capacity__side_left_full, 14 steps): navigate(bookcase_2/top) look(bookcase_2/top) measure(toy_bin_small) measure(toy_bin_small_2) explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(toy_bin_small_2) place(toy_car,toy_bin_small_2) search(rubber_duck,living_room_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(toy_bin_small_2) drop(rubber_duck,toy_bin_small_2)
* `bins_capacity__side_right_full` (v6_bins_capacity__side_right_full, 14 steps): navigate(bookcase_2/top) look(bookcase_2/top) measure(toy_bin_small_2) measure(toy_bin_small) explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(toy_bin_small) place(toy_car,toy_bin_small) search(rubber_duck,living_room_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(toy_bin_small) drop(rubber_duck,toy_bin_small)
* `bins_capacity__apart_full_on_tv` (v6_bins_capacity__apart_full_on_tv, 15 steps): navigate(tv_stand_2/top) look(tv_stand_2/top) measure(toy_bin_small) search(toy_bin_small_2,bedroom_0_1) measure(toy_bin_small_2) explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(toy_bin_small_2) place(toy_car,toy_bin_small_2) search(rubber_duck,living_room_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(toy_bin_small_2) drop(rubber_duck,toy_bin_small_2)
* `bins_capacity__apart_empty_on_desk` (v6_bins_capacity__apart_empty_on_desk, 15 steps): navigate(bookcase_2/top) look(bookcase_2/top) measure(toy_bin_small) search(toy_bin_small_2,living_room_0_1) measure(toy_bin_small_2) explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(toy_bin_small_2) place(toy_car,toy_bin_small_2) search(rubber_duck,living_room_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(toy_bin_small_2) drop(rubber_duck,toy_bin_small_2)
* `bins_capacity__half_bin_and_tray` (v6_bins_capacity__half_bin_and_tray, 14 steps): navigate(bookcase_2/top) look(bookcase_2/top) measure(toy_bin_small) measure(toy_tray) explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(toy_tray) place(toy_car,toy_tray) search(rubber_duck,living_room_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(toy_bin_small) drop(rubber_duck,toy_bin_small)
* `bins_capacity__half_bin_and_tray_duck_dining` (v6_bins_capacity__half_bin_and_tray_duck_dining, 14 steps): navigate(bookcase_2/top) look(bookcase_2/top) measure(toy_bin_small) measure(toy_tray) explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(toy_tray) place(toy_car,toy_tray) search(rubber_duck,dining_room_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(toy_bin_small) drop(rubber_duck,toy_bin_small)
* `find_all_toys__car_duck` (v6_find_all_toys__car_duck, 10 steps): explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) search(rubber_duck,living_room_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket)
* `find_all_toys__car_duck_bear` (v6_find_all_toys__car_duck_bear, 15 steps): explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) search(rubber_duck,bathroom_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket) search(teddy_bear,dining_room_0_1) navigate(teddy_bear) pick(teddy_bear) navigate(storage_basket) place(teddy_bear,storage_basket)
* `find_all_toys__all_four` (v6_find_all_toys__all_four, 20 steps): explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) search(rubber_duck,living_room_0_1) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket) search(teddy_bear,dining_room_0_1) navigate(teddy_bear) pick(teddy_bear) navigate(storage_basket) place(teddy_bear,storage_basket) search(stray_block,living_room_0_0) navigate(stray_block) pick(stray_block) navigate(storage_basket) place(stray_block,storage_basket)
* `castle_stays__tall_two_loose` (v6_castle_stays__tall_two_loose, 17 steps): explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket) navigate(loose_block_1) pick(loose_block_1) navigate(storage_basket) place(loose_block_1,storage_basket) navigate(loose_block_2) pick(loose_block_2) navigate(storage_basket) place(loose_block_2,storage_basket)
* `castle_stays__short_one_loose` (v6_castle_stays__short_one_loose, 13 steps): explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket) navigate(loose_block_1) pick(loose_block_1) navigate(storage_basket) place(loose_block_1,storage_basket)
* `castle_stays__tall_none_loose` (v6_castle_stays__tall_none_loose, 9 steps): explore_room(living_room_0_0) navigate(toy_car) pick(toy_car) navigate(storage_basket) place(toy_car,storage_basket) navigate(rubber_duck) pick(rubber_duck) navigate(storage_basket) place(rubber_duck,storage_basket)

## T13_breakfast_setup

### Control

* `dishes_on_tv_stand` (nominal, 11 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1]) navigate(cup) pick(cup) navigate(dining_table_2/top) place(cup,dining_table_2/top,[3.2, 7.4])

### Task-Level

* `no_cup` (alternative_mug, 13 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[3.05, 7.1]) !navigate(cup) +navigate(bookcase_2/top) +look(bookcase_2/top) +pick(mug) navigate(dining_table_2/top) place(mug,dining_table_2/top,[3.2, 7.4])
* `copy_the_setting__bowl_cup` (v6_copy_the_setting__bowl_cup, 12 steps): look(dining_table_2/top) measure(example_spoon) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[2.93, 7.49]) navigate(cup) pick(cup) navigate(dining_table_2/top) place(cup,dining_table_2/top,[3.1, 7.3])
* `copy_the_setting__plate_bowl_mug_left` (v6_copy_the_setting__plate_bowl_mug_left, 20 steps): look(dining_table_2/top) measure(example_spoon) navigate(kitchen_counter_2/top) look(kitchen_counter_2/top) navigate(plate_counter_a) pick(plate_counter_a) navigate(dining_table_2/top) place(plate_counter_a,dining_table_2/top,[2.93, 7.49]) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) stack(bowl,plate_counter_a) navigate(bookcase_2/top) look(bookcase_2/top) navigate(mug) pick(mug) navigate(dining_table_2/top) place(mug,dining_table_2/top,[3.1, 7.66])
* `copy_the_setting__no_cup` (v6_copy_the_setting__no_cup, 14 steps): look(dining_table_2/top) measure(example_spoon) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[2.93, 7.49]) navigate(bookcase_2/top) look(bookcase_2/top) navigate(mug) pick(mug) navigate(dining_table_2/top) place(mug,dining_table_2/top,[3.1, 7.3])
* `finish_the_table__adult_seat` (v6_finish_the_table__adult_seat, 13 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[2.93, 6.89]) navigate(bookcase_2/top) look(bookcase_2/top) navigate(mug) pick(mug) navigate(dining_table_2/top) place(mug,dining_table_2/top,[3.1, 6.7])
* `finish_the_table__kid_seat` (v6_finish_the_table__kid_seat, 13 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[2.93, 6.89]) navigate(kitchen_counter_2/top) look(kitchen_counter_2/top) navigate(kid_cup) pick(kid_cup) navigate(dining_table_2/top) place(kid_cup,dining_table_2/top,[3.1, 6.7])
* `finish_the_table__adult_and_kid` (v6_finish_the_table__adult_and_kid, 23 steps): look(dining_table_2/top) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(bowl) pick(bowl) navigate(dining_table_2/top) place(bowl,dining_table_2/top,[2.93, 6.89]) navigate(bookcase_2/top) look(bookcase_2/top) navigate(mug) pick(mug) navigate(dining_table_2/top) place(mug,dining_table_2/top,[3.1, 6.7]) navigate(bowl_2) pick(bowl_2) navigate(dining_table_2/top) place(bowl_2,dining_table_2/top,[2.93, 6.04]) navigate(kitchen_counter_2/top) look(kitchen_counter_2/top) navigate(kid_cup) pick(kid_cup) navigate(dining_table_2/top) place(kid_cup,dining_table_2/top,[3.1, 5.85])

## T15_book_face_up

### Control

* `book_free` (nominal, 3 steps): look(kitchen_island/top) navigate(paperback_book) flip(paperback_book)

### Task-Level

* `book_out_of_view` (explore_search_book, 3 steps): +search(paperback_book,living_room_0_0) navigate(paperback_book) flip(paperback_book)
* `flip_on_the_shelf__shelf_1` (v6_flip_on_the_shelf__shelf_1, 8 steps): search(paperback_book,bedroom_0_1) navigate(paperback_book) pick(paperback_book) navigate(bookcase_2/top) place(paperback_book,bookcase_2/top,[1.0, -0.45]) flip(paperback_book) pick(paperback_book) place(paperback_book,bookcase_2/shelf_1,[1.0, -0.44])
* `flip_on_the_shelf__shelf_0` (v6_flip_on_the_shelf__shelf_0, 8 steps): search(paperback_book,bedroom_0_1) navigate(paperback_book) pick(paperback_book) navigate(bookcase_2/top) place(paperback_book,bookcase_2/top,[1.0, -0.45]) flip(paperback_book) pick(paperback_book) place(paperback_book,bookcase_2/shelf_0,[1.0, -0.44])

## T16_rolling_pin_at_edge

### Control

* `pin_free` (nominal, 3 steps): look(kitchen_island/top) navigate(rolling_pin) roll(rolling_pin,0.12)

### Task-Level

* `pin_out_of_view` (explore_search_pin, 3 steps): +search(rolling_pin,living_room_0_0) navigate(rolling_pin) roll(rolling_pin,0.12)
* `everything_near_the_edge__pin_and_mug` (v6_everything_near_the_edge__pin_and_mug, 6 steps): look(kitchen_island/top) navigate(rolling_pin) roll(rolling_pin,0.12) navigate(edge_mug) pick(edge_mug) place(edge_mug,kitchen_island/top,[7.3, 1.8])
* `everything_near_the_edge__pin_and_bowl` (v6_everything_near_the_edge__pin_and_bowl, 6 steps): look(kitchen_island/top) navigate(rolling_pin) roll(rolling_pin,0.12) navigate(oatmeal) pick(oatmeal) place(oatmeal,kitchen_island/top,[7.3, 1.8])
* `everything_near_the_edge__pin_only` (v6_everything_near_the_edge__pin_only, 3 steps): look(kitchen_island/top) navigate(rolling_pin) roll(rolling_pin,0.12)

## T17_hide_and_seek_block

### Control

* `lid_off` (v5fix_lid_off, 5 steps): navigate(kitchen_stove/top) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) hide(wooden_block_b,handled_cooking_pot,pot_lid)

### Task-Level

* `h_task_lid_elsewhere` (v5_h_task_lid_elsewhere, 11 steps): navigate(kitchen_cabinet_6/top) look(kitchen_cabinet_6/top) navigate(pot_lid) pick(pot_lid) navigate(kitchen_stove/top) place(pot_lid,kitchen_stove/top,[8.715, 1.655]) navigate(handled_cooking_pot) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) hide(wooden_block_b,handled_cooking_pot,pot_lid)
* `hide_both__tv_stand` (v6_hide_both__tv_stand, 11 steps): navigate(kitchen_stove/top) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) hide(wooden_block_b,handled_cooking_pot,pot_lid) +search(floor_block,living_room_0_0) +navigate(handled_cooking_pot) +uncover(handled_cooking_pot) +navigate(floor_block) +look(floor_block) +hide(floor_block,handled_cooking_pot,pot_lid)
* `hide_both__dining` (v6_hide_both__dining, 11 steps): navigate(kitchen_stove/top) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) hide(wooden_block_b,handled_cooking_pot,pot_lid) +search(floor_block,dining_room_0_1) +navigate(handled_cooking_pot) +uncover(handled_cooking_pot) +navigate(floor_block) +look(floor_block) +hide(floor_block,handled_cooking_pot,pot_lid)
* `hide_somewhere__pot_ready` (v6_hide_somewhere__pot_ready, 5 steps): navigate(kitchen_stove/top) look(kitchen_stove/top) navigate(kitchen_island/top) look(kitchen_island/top) hide(wooden_block_b,handled_cooking_pot,pot_lid)
* `hide_somewhere__lid_away` (v6_hide_somewhere__lid_away, 10 steps): look(kitchen_island/top) navigate(kitchen_stove/top) look(kitchen_stove/top) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) navigate(wooden_block_b) pick(wooden_block_b) navigate(kitchen_cabinet_4) place(wooden_block_b,kitchen_cabinet_4/inside_shelf,[1.4, 0.42]) close(kitchen_cabinet_4)

## T18_check_cabinet_dishes

### Control

* `at_island` (nominal, 4 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) inspect(kitchen_cabinet_6) close(kitchen_cabinet_6)

### Task-Level

* `dishes_spread__in_cabinet_4` (v6_dishes_spread__in_cabinet_4, 8 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) inspect(kitchen_cabinet_6) close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) inspect(kitchen_cabinet_4) close(kitchen_cabinet_4)
* `dishes_spread__in_microwave` (v6_dishes_spread__in_microwave, 8 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) inspect(kitchen_cabinet_6) close(kitchen_cabinet_6) navigate(kitchen_microwave) open(kitchen_microwave) look(kitchen_microwave/inside_floor) close(kitchen_microwave)
* `enough_for_dinner__enough` (v6_enough_for_dinner__enough, 4 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) inspect(kitchen_cabinet_6) close(kitchen_cabinet_6)
* `enough_for_dinner__one_short` (v6_enough_for_dinner__one_short, 10 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) inspect(kitchen_cabinet_6) navigate(kitchen_cabinet_3/top) look(kitchen_cabinet_3/top) navigate(bowl_kitchen_cabinet) pick(bowl_kitchen_cabinet) navigate(kitchen_cabinet_6) place(bowl_kitchen_cabinet,kitchen_cabinet_6/inside_shelf,[3.685, 0.36]) close(kitchen_cabinet_6)
* `enough_for_dinner__two_short` (v6_enough_for_dinner__two_short, 16 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) inspect(kitchen_cabinet_6) navigate(kitchen_cabinet_3/top) look(kitchen_cabinet_3/top) navigate(bowl_kitchen_cabinet) pick(bowl_kitchen_cabinet) navigate(kitchen_cabinet_6) place(bowl_kitchen_cabinet,kitchen_cabinet_6/inside_shelf,[3.5, 0.36]) navigate(dining_table_1/top) look(dining_table_1/top) navigate(bowl_side_table) pick(bowl_side_table) navigate(kitchen_cabinet_6) place(bowl_side_table,kitchen_cabinet_6/inside_shelf,[3.685, 0.36]) close(kitchen_cabinet_6)

## T19_recycling

### Control

* `bin_on_bookcase` (nominal, 13 steps): explore_room(living_room_0_0) navigate(tv_stand_2/top) look(tv_stand_2/top) navigate(soda_can) pick(soda_can) navigate(bookcase_2/top) look(bookcase_2/top) navigate(wide_storage_bin) drop(soda_can,wide_storage_bin) navigate(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)

### Task-Level

* `m_can_in_dining_room` (v5_m_can_in_dining_room, 14 steps): explore_room(living_room_0_0) navigate(tv_stand_2/top) look(tv_stand_2/top) +search(soda_can,dining_room_0_1) navigate(soda_can) pick(soda_can) navigate(bookcase_2/top) look(bookcase_2/top) navigate(wide_storage_bin) drop(soda_can,wide_storage_bin) navigate(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)
* `m_can_in_dining_room__alt_tv_stand_2` (v6_m_can_in_dining_room__alt_tv_stand_2, 14 steps): explore_room(living_room_0_0) navigate(tv_stand_2/top) look(tv_stand_2/top) +search(soda_can,living_room_0_0) navigate(soda_can) pick(soda_can) navigate(bookcase_2/top) look(bookcase_2/top) navigate(wide_storage_bin) drop(soda_can,wide_storage_bin) navigate(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)
* `lookalike_bin` (v5x_lookalike_bin, 16 steps): explore_room(living_room_0_0) navigate(tv_stand_2/top) look(tv_stand_2/top) +search(soda_can,dining_room_0_1) navigate(soda_can) pick(soda_can) navigate(bookcase_2/top) look(bookcase_2/top) +identify(wide_storage_bin) navigate(wide_storage_bin) drop(soda_can,wide_storage_bin) navigate(foam_cube) +touch(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)
* `lookalike_bin__alt_tv_stand_2` (v6_lookalike_bin__alt_tv_stand_2, 16 steps): explore_room(living_room_0_0) navigate(tv_stand_2/top) look(tv_stand_2/top) +search(soda_can,living_room_0_0) navigate(soda_can) pick(soda_can) navigate(bookcase_2/top) look(bookcase_2/top) +identify(wide_storage_bin) navigate(wide_storage_bin) drop(soda_can,wide_storage_bin) navigate(foam_cube) +touch(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)
* `x6_gd_can_put_away__in_4` (v6_x6_gd_can_put_away__in_4, 23 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(soda_can) pick(soda_can) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(bookcase_2/top) look(bookcase_2/top) navigate(wide_storage_bin) drop(soda_can,wide_storage_bin) navigate(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)
* `x6_gd_can_put_away__in_6` (v6_x6_gd_can_put_away__in_6, 23 steps): navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() close(kitchen_cabinet_4) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(soda_can) pick(soda_can) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(bookcase_2/top) look(bookcase_2/top) navigate(wide_storage_bin) drop(soda_can,wide_storage_bin) navigate(foam_cube) pick(foam_cube) navigate(wide_storage_bin) drop(foam_cube,wide_storage_bin)

## T20_juice_back_to_table

### Control

* `bottle_on_cabinet` (nominal, 6 steps): navigate(kitchen_cabinet_6/top) look(kitchen_cabinet_6/top) navigate(juice_bottle) pick(juice_bottle) navigate(dining_table_2/top) place(juice_bottle,dining_table_2/top,[3.0, 7.3])

### Task-Level

* `m_bottle_on_tv_stand` (v5_m_bottle_on_tv_stand, 5 steps): search(juice_bottle,living_room_0_0) navigate(juice_bottle) pick(juice_bottle) navigate(dining_table_2/top) place(juice_bottle,dining_table_2/top,[3.0, 7.3])
* `m_bottle_on_tv_stand__alt_bookcase_2` (v6_m_bottle_on_tv_stand__alt_bookcase_2, 5 steps): search(juice_bottle,bedroom_0_1) navigate(juice_bottle) pick(juice_bottle) navigate(dining_table_2/top) place(juice_bottle,dining_table_2/top,[3.0, 7.3])
* `x6_gd_bottle_put_away__in_cabinet_4` (v6_x6_gd_bottle_put_away__in_cabinet_4, 17 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(juice_bottle) pick(juice_bottle) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(dining_table_2/top) place(juice_bottle,dining_table_2/top,[3.0, 7.3])
* `x6_gd_bottle_put_away__in_cabinet_6` (v6_x6_gd_bottle_put_away__in_cabinet_6, 17 steps): navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() close(kitchen_cabinet_4) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(juice_bottle) pick(juice_bottle) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(dining_table_2/top) place(juice_bottle,dining_table_2/top,[3.0, 7.3])

## T14_shelve_the_book

### Control

* `e1_book_ready` (v5_e1_book_ready, 6 steps): navigate(desk_1/top) look(desk_1/top) navigate(book_red) pick(book_red) navigate(bookcase_2/top) place(book_red,bookcase_2/top)

### Task-Level

* `within_kids_reach__set_on_large_shelf_4` (v6_within_kids_reach__set_on_large_shelf_4, 6 steps): look(desk_1/top) explore_room(bedroom_0_1) navigate(book_red) pick(book_red) navigate(large_shelf_4/shelf_1) place(book_red,large_shelf_4/shelf_1,[3.7, -5.15])
* `within_kids_reach__set_on_large_shelf_5` (v6_within_kids_reach__set_on_large_shelf_5, 6 steps): look(desk_1/top) explore_room(bedroom_0_1) navigate(book_red) pick(book_red) navigate(large_shelf_5/shelf_1) place(book_red,large_shelf_5/shelf_1,[4.45, -0.35])
* `stack_them_stably__red_blue_paperback` (v6_stack_them_stably__red_blue_paperback, 13 steps): look(desk_1/top) navigate(book_red) pick(book_red) navigate(bookcase_2/top) place(book_red,bookcase_2/top,[1.0, -0.45]) navigate(desk_book_blue) pick(desk_book_blue) navigate(bookcase_2/top) stack(desk_book_blue,book_red) navigate(desk_paperback_book) pick(desk_paperback_book) navigate(bookcase_2/top) stack(desk_paperback_book,desk_book_blue)
* `stack_them_stably__green_paperback` (v6_stack_them_stably__green_paperback, 9 steps): look(desk_1/top) navigate(desk_book_green) pick(desk_book_green) navigate(bookcase_2/top) place(desk_book_green,bookcase_2/top,[1.0, -0.45]) navigate(desk_paperback_book) pick(desk_paperback_book) navigate(bookcase_2/top) stack(desk_paperback_book,desk_book_green)
* `stack_them_stably__blue_green_paperback` (v6_stack_them_stably__blue_green_paperback, 13 steps): look(desk_1/top) navigate(desk_book_green) pick(desk_book_green) navigate(bookcase_2/top) place(desk_book_green,bookcase_2/top,[1.0, -0.45]) navigate(desk_book_blue) pick(desk_book_blue) navigate(bookcase_2/top) stack(desk_book_blue,desk_book_green) navigate(desk_paperback_book) pick(desk_paperback_book) navigate(bookcase_2/top) stack(desk_paperback_book,desk_book_blue)
* `homework_stays` (v6_homework_stays, 9 steps): look(desk_1/top) navigate(book_red) pick(book_red) navigate(bookcase_2/top) place(book_red,bookcase_2/top) navigate(desk_mug) pick(desk_mug) navigate(kitchen_counter_2/top) place(desk_mug,kitchen_counter_2/top,[-0.3, 7.6])
* `whose_book__blue_book` (v6_whose_book__blue_book, 5 steps): look(desk_1/top) navigate(blue_book) pick(blue_book) navigate(bookcase_2/top) place(blue_book,bookcase_2/top,[1.0, -0.45])
* `whose_book__paperback` (v6_whose_book__paperback, 5 steps): look(desk_1/top) navigate(paperback) pick(paperback) navigate(large_shelf_2/shelf_2) place(paperback,large_shelf_2/shelf_2,[-1.86, -0.95])
* `whose_book__both` (v6_whose_book__both, 9 steps): look(desk_1/top) navigate(blue_book) pick(blue_book) navigate(bookcase_2/top) place(blue_book,bookcase_2/top,[1.0, -0.45]) navigate(paperback) pick(paperback) navigate(large_shelf_2/shelf_2) place(paperback,large_shelf_2/shelf_2,[-1.86, -0.95])
* `next_in_series__on_bookcase` (v6_next_in_series__on_bookcase, 10 steps): look(desk_1/top) navigate(book_red) pick(book_red) navigate(bookcase_2/top) place(book_red,bookcase_2/top,[1.0, -0.55]) look(bookcase_2/top) navigate(red_book_2) pick(red_book_2) navigate(desk_1/top) place(red_book_2,desk_1/top,[-0.8, -6.05])
* `next_in_series__on_other_bookcase` (v6_next_in_series__on_other_bookcase, 12 steps): look(desk_1/top) navigate(book_red) pick(book_red) navigate(bookcase_2/top) place(book_red,bookcase_2/top,[1.0, -0.55]) look(bookcase_2/top) search(red_book_2,bedroom_0_1) look(bookcase_3/top) navigate(red_book_2) pick(red_book_2) navigate(desk_1/top) place(red_book_2,desk_1/top,[-0.8, -6.05])
* `next_in_series__on_tall_shelf` (v6_next_in_series__on_tall_shelf, 12 steps): look(desk_1/top) navigate(book_red) pick(book_red) navigate(bookcase_2/top) place(book_red,bookcase_2/top,[1.0, -0.55]) look(bookcase_2/top) search(red_book_2,bedroom_0_1) look(large_shelf_4/shelf_1) navigate(red_book_2) pick(red_book_2) navigate(desk_1/top) place(red_book_2,desk_1/top,[-0.8, -6.05])

## T21_bring_tissues

### Control

* `tissue_on_tv_stand` (nominal, 4 steps): navigate(tissue) pick(tissue) navigate(dining_table_2/top) place(tissue,dining_table_2/top,[3.3, 6.65])

### Task-Level

* `tissue_out_of_view` (v6_tissue_out_of_view, 5 steps): search(tissue,living_room_0_1) navigate(tissue) pick(tissue) navigate(dining_table_2/top) place(tissue,dining_table_2/top,[3.3, 6.65])
* `which_table__east` (v6_which_table__east, 5 steps): navigate(tissue) pick(tissue) look(dining_table_1/top) navigate(dining_table_2/top) place(tissue,dining_table_2/top,[3.3, 6.65])
* `which_table__west` (v6_which_table__west, 5 steps): navigate(tissue) pick(tissue) look(dining_table_2/top) navigate(dining_table_1/top) place(tissue,dining_table_1/top,[-7.75, 7.4])
* `no_tissue` (v6_no_tissue, 5 steps): look(tv_stand_2/top) navigate(spare_sponge) pick(spare_sponge) navigate(dining_table_2/top) place(spare_sponge,dining_table_2/top,[3.3, 6.65])
* `tissue_put_away__in_4` (v6_tissue_put_away__in_4, 17 steps): navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() close(kitchen_cabinet_6) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(tissue) pick(tissue) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(dining_table_2/top) place(tissue,dining_table_2/top,[3.3, 6.65])
* `tissue_put_away__in_6` (v6_tissue_put_away__in_6, 17 steps): navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() close(kitchen_cabinet_4) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(tissue) pick(tissue) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(dining_table_2/top) place(tissue,dining_table_2/top,[3.3, 6.65])
* `the_kids_side__kid_north` (v6_the_kids_side__kid_north, 4 steps): navigate(tissue) pick(tissue) navigate(dining_table_2/top) place(tissue,dining_table_2/top,[3.1, 7.45])
* `the_kids_side__kid_south` (v6_the_kids_side__kid_south, 4 steps): navigate(tissue) pick(tissue) navigate(dining_table_2/top) place(tissue,dining_table_2/top,[3.1, 6.4])

## T22_put_away_shopping

### Control

* `juice_on_table` (nominal, 9 steps): navigate(breakfast_fridge) open(breakfast_fridge) navigate(dining_table_2/top) look(dining_table_2/top) navigate(bought_juice) pick(bought_juice) navigate(breakfast_fridge) place(bought_juice,breakfast_fridge/inside_shelf,[5.78, 3.18]) close(breakfast_fridge)

### Task-Level

* `by_kind` (v6_by_kind, 21 steps): navigate(breakfast_fridge) open(breakfast_fridge) navigate(dining_table_2/top) look(dining_table_2/top) navigate(bought_juice) pick(bought_juice) navigate(breakfast_fridge) place(bought_juice,breakfast_fridge/inside_shelf,[5.78, 3.18]) close(breakfast_fridge) navigate(bought_apple) pick(bought_apple) navigate(home_basket) place(bought_apple,home_basket) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) inspect(kitchen_cabinet_6) navigate(bought_snack) pick(bought_snack) navigate(kitchen_cabinet_6) place(bought_snack,kitchen_cabinet_6/inside_shelf,[3.6, 0.36]) close(kitchen_cabinet_6)
* `eat_now` (v6_eat_now, 13 steps): navigate(breakfast_fridge) open(breakfast_fridge) navigate(dining_table_2/top) look(dining_table_2/top) navigate(bought_juice) pick(bought_juice) navigate(breakfast_fridge) place(bought_juice,breakfast_fridge/inside_shelf,[5.78, 3.18]) close(breakfast_fridge) navigate(bought_snack) pick(bought_snack) navigate(desk_1/top) place(bought_snack,desk_1/top,[-1.1, -5.95])
* `not_shopping` (v6_not_shopping, 8 steps): look(dining_table_2/top) navigate(breakfast_fridge) open(breakfast_fridge) navigate(bought_juice) pick(bought_juice) navigate(breakfast_fridge) place(bought_juice,breakfast_fridge/inside_shelf,[5.78, 3.18]) close(breakfast_fridge)
* `two_spots` (v6_two_spots, 21 steps): look(dining_table_2/top) navigate(breakfast_fridge) open(breakfast_fridge) navigate(bought_juice) pick(bought_juice) navigate(breakfast_fridge) place(bought_juice,breakfast_fridge/inside_shelf,[5.78, 3.18]) close(breakfast_fridge) look(kitchen_island/top) navigate(bought_apple) pick(bought_apple) navigate(home_basket) place(bought_apple,home_basket) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) inspect(kitchen_cabinet_6) navigate(bought_snack) pick(bought_snack) navigate(kitchen_cabinet_6) place(bought_snack,kitchen_cabinet_6/inside_shelf,[3.6, 0.36]) close(kitchen_cabinet_6)

### Action + Task

* `tray_elsewhere__orange_in_it` (v6_tray_elsewhere__orange_in_it, 15 steps): navigate(breakfast_fridge) open(breakfast_fridge) navigate(dining_table_2/top) look(dining_table_2/top) navigate(bought_juice) pick(bought_juice) navigate(breakfast_fridge) place(bought_juice,breakfast_fridge/inside_shelf,[5.78, 3.18]) close(breakfast_fridge) search(west_tray,dining_room_0_0) look(west_tray) navigate(bought_apple) pick(bought_apple) navigate(west_tray) place(bought_apple,west_tray)
* `tray_elsewhere__books_on_it` (v6_tray_elsewhere__books_on_it, 31 steps): navigate(breakfast_fridge) open(breakfast_fridge) navigate(dining_table_2/top) look(dining_table_2/top) navigate(bought_juice) pick(bought_juice) navigate(breakfast_fridge) place(bought_juice,breakfast_fridge/inside_shelf,[5.78, 3.18]) close(breakfast_fridge) search(west_tray,dining_room_0_0) look(west_tray) navigate(tray_book_1) pick(tray_book_1) navigate(bookcase_1/top) place(tray_book_1,bookcase_1/top,[-9.59, 6.52]) navigate(tray_book_2) pick(tray_book_2) navigate(bookcase_1/top) place(tray_book_2,bookcase_1/top,[-9.59, 6.819999999999999]) navigate(tray_book_3) pick(tray_book_3) navigate(bookcase_1/shelf_1) place(tray_book_3,bookcase_1/shelf_1,[-9.59, 6.52]) navigate(tray_book_4) pick(tray_book_4) navigate(bookcase_1/shelf_1) place(tray_book_4,bookcase_1/shelf_1,[-9.59, 6.819999999999999]) navigate(bought_apple) pick(bought_apple) navigate(west_tray) place(bought_apple,west_tray)
* `basket_missing` (v6_basket_missing, 13 steps): navigate(breakfast_fridge) open(breakfast_fridge) navigate(dining_table_2/top) look(dining_table_2/top) navigate(bought_juice) pick(bought_juice) navigate(breakfast_fridge) place(bought_juice,breakfast_fridge/inside_shelf,[5.78, 3.18]) close(breakfast_fridge) navigate(bought_apple) pick(bought_apple) navigate(fruit_tray) place(bought_apple,fruit_tray)

## T23_pick_up_dropped

### Control

* `spoon_on_floor` (nominal, 5 steps): look(kitchen_counter_2/top) navigate(dropped_spoon) pick(dropped_spoon) navigate(kitchen_counter_2/top) place(dropped_spoon,kitchen_counter_2/top,[-0.1, 7.6])

### Task-Level

* `by_kind` (v6_by_kind, 10 steps): look(kitchen_counter_2/top) navigate(dropped_spoon) pick(dropped_spoon) navigate(kitchen_counter_2/top) place(dropped_spoon,kitchen_counter_2/top,[-0.1, 7.6]) navigate(dropped_block) pick(dropped_block) explore_room(living_room_0_0) navigate(toy_box) place(dropped_block,toy_box)
* `belongs_on_floor` (v6_belongs_on_floor, 5 steps): look(kitchen_counter_2/top) navigate(dropped_spoon) pick(dropped_spoon) navigate(kitchen_counter_2/top) place(dropped_spoon,kitchen_counter_2/top,[-0.1, 7.6])
* `dropped_out_of_view` (v6_dropped_out_of_view, 6 steps): look(kitchen_counter_2/top) search(dropped_spoon,dining_room_0_1) navigate(dropped_spoon) pick(dropped_spoon) navigate(kitchen_counter_2/top) place(dropped_spoon,kitchen_counter_2/top,[-0.1, 7.6])
* `only_this_room` (v6_only_this_room, 5 steps): look(kitchen_counter_2/top) navigate(dropped_spoon) pick(dropped_spoon) navigate(kitchen_counter_2/top) place(dropped_spoon,kitchen_counter_2/top,[-0.1, 7.6])
* `dropped_in_two_rooms` (v6_dropped_in_two_rooms, 10 steps): look(kitchen_counter_2/top) navigate(dropped_spoon) pick(dropped_spoon) navigate(kitchen_counter_2/top) place(dropped_spoon,kitchen_counter_2/top,[-0.1, 7.6]) search(dropped_pencil,living_room_0_1) navigate(dropped_pencil) pick(dropped_pencil) navigate(desk_1/top) place(dropped_pencil,desk_1/top,[-1.05, -5.95])

## T24_snack_for_kid

### Control

* `apple_on_table` (nominal, 6 steps): navigate(dining_table_2/top) look(dining_table_2/top) navigate(snack_apple) pick(snack_apple) navigate(desk_1/top) place(snack_apple,desk_1/top,[-1.1, -5.95])

### Task-Level

* `no_apples_for_him` (v6_no_apples_for_him, 5 steps): look(dining_table_2/top) navigate(snack_banana) pick(snack_banana) navigate(desk_1/top) place(snack_banana,desk_1/top,[-1.1, -5.95])
* `dinner_soon` (v6_dinner_soon, 5 steps): look(dining_table_2/top) navigate(snack_apple) pick(snack_apple) navigate(desk_1/top) place(snack_apple,desk_1/top,[-1.1, -5.95])
* `fruit_out_of_view` (v6_fruit_out_of_view, 8 steps): look(dining_table_2/top) search(home_basket,bedroom_0_1) navigate(bookcase_2/top) look(bookcase_2/top) navigate(snack_apple) pick(snack_apple) navigate(desk_1/top) place(snack_apple,desk_1/top,[-1.1, -5.95])
* `where_is_he__study` (v6_where_is_he__study, 7 steps): navigate(dining_table_2/top) look(dining_table_2/top) navigate(snack_apple) pick(snack_apple) look(desk_3/top) navigate(desk_1/top) place(snack_apple,desk_1/top,[-1.1, -5.95])
* `where_is_he__bedroom` (v6_where_is_he__bedroom, 7 steps): navigate(dining_table_2/top) look(dining_table_2/top) navigate(snack_apple) pick(snack_apple) look(desk_1/top) navigate(desk_3/top) place(snack_apple,desk_3/top,[6.2, -5.5])
* `two_kids` (v6_two_kids, 10 steps): navigate(dining_table_2/top) look(dining_table_2/top) navigate(snack_apple) pick(snack_apple) navigate(desk_1/top) place(snack_apple,desk_1/top,[-1.1, -5.95]) navigate(snack_banana) pick(snack_banana) navigate(desk_3/top) place(snack_banana,desk_3/top,[6.2, -5.5])

## T25_drink_for_guest

### Control

* `drink_on_island` (nominal, 8 steps): navigate(guest_juice) pick(guest_juice) navigate(tv_stand_2/top) place(guest_juice,tv_stand_2/top,[7.3, 0.36]) navigate(guest_cup) pick(guest_cup) navigate(tv_stand_2/top) place(guest_cup,tv_stand_2/top,[7.55, 0.36])

### Task-Level

* `cup_elsewhere` (v6_cup_elsewhere, 9 steps): navigate(guest_juice) pick(guest_juice) navigate(tv_stand_2/top) place(guest_juice,tv_stand_2/top,[7.3, 0.36]) search(cup_counter_b,kitchen_0_1) navigate(cup_counter_b) pick(cup_counter_b) navigate(tv_stand_2/top) place(cup_counter_b,tv_stand_2/top,[7.55, 0.36])
* `cold_one` (v6_cold_one, 14 steps): navigate(breakfast_fridge) open(breakfast_fridge) navigate(breakfast_fridge/inside_shelf) look(breakfast_fridge/inside_shelf) navigate(cold_juice) pick(cold_juice) retreat(breakfast_fridge,0.3) close(breakfast_fridge) navigate(tv_stand_2/top) place(cold_juice,tv_stand_2/top,[7.3, 0.36]) navigate(guest_cup) pick(guest_cup) navigate(tv_stand_2/top) place(guest_cup,tv_stand_2/top,[7.55, 0.36])
* `drink_in_fridge` (v6_drink_in_fridge, 15 steps): look(kitchen_island/top) navigate(breakfast_fridge) open(breakfast_fridge) navigate(breakfast_fridge/inside_shelf) look(breakfast_fridge/inside_shelf) navigate(cold_juice) pick(cold_juice) retreat(breakfast_fridge,0.3) close(breakfast_fridge) navigate(tv_stand_2/top) place(cold_juice,tv_stand_2/top,[7.3, 0.36]) navigate(guest_cup) pick(guest_cup) navigate(tv_stand_2/top) place(guest_cup,tv_stand_2/top,[7.55, 0.36])
* `cups_for_two__one_there` (v6_cups_for_two__one_there, 16 steps): look(tv_stand_2/top) navigate(guest_juice) pick(guest_juice) navigate(tv_stand_2/top) place(guest_juice,tv_stand_2/top,[7.3, 0.36]) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(stock_cup_1) pick(stock_cup_1) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(tv_stand_2/top) place(stock_cup_1,tv_stand_2/top,[7.55, 0.36])
* `cups_for_two__none_one_inside` (v6_cups_for_two__none_one_inside, 21 steps): look(tv_stand_2/top) navigate(guest_juice) pick(guest_juice) navigate(tv_stand_2/top) place(guest_juice,tv_stand_2/top,[7.3, 0.36]) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(stock_cup_1) pick(stock_cup_1) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(tv_stand_2/top) place(stock_cup_1,tv_stand_2/top,[7.55, 0.36]) search(mug_shelf,dining_room_0_1) navigate(mug_shelf) pick(mug_shelf) navigate(tv_stand_2/top) place(mug_shelf,tv_stand_2/top,[7.05, 0.36])
* `cups_for_two__none_two_inside` (v6_cups_for_two__none_two_inside, 20 steps): look(tv_stand_2/top) navigate(guest_juice) pick(guest_juice) navigate(tv_stand_2/top) place(guest_juice,tv_stand_2/top,[7.3, 0.36]) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(stock_cup_1) pick(stock_cup_1) navigate(tv_stand_2/top) place(stock_cup_1,tv_stand_2/top,[7.55, 0.36]) navigate(stock_cup_2) pick(stock_cup_2) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(tv_stand_2/top) place(stock_cup_2,tv_stand_2/top,[7.05, 0.36])
* `cups_for_two__two_there` (v6_cups_for_two__two_there, 5 steps): look(tv_stand_2/top) navigate(guest_juice) pick(guest_juice) navigate(tv_stand_2/top) place(guest_juice,tv_stand_2/top,[7.3, 0.36])
* `two_guests` (v6_two_guests, 12 steps): navigate(guest_juice) pick(guest_juice) navigate(tv_stand_2/top) place(guest_juice,tv_stand_2/top,[7.3, 0.36]) navigate(guest_cup) pick(guest_cup) navigate(tv_stand_2/top) place(guest_cup,tv_stand_2/top,[7.55, 0.36]) navigate(guest_cup_2) pick(guest_cup_2) navigate(tv_stand_2/top) place(guest_cup_2,tv_stand_2/top,[7.8, 0.36])
* `little_guest` (v6_little_guest, 8 steps): navigate(guest_juice) pick(guest_juice) navigate(tv_stand_2/top) place(guest_juice,tv_stand_2/top,[7.3, 0.36]) navigate(kid_cup) pick(kid_cup) navigate(tv_stand_2/top) place(kid_cup,tv_stand_2/top,[7.55, 0.36])

## T26_kids_things_to_room

### Control

* `car_in_living_room` (nominal, 6 steps): explore_room(living_room_0_0) navigate(living_car) pick(living_car) explore_room(bedroom_0_1) navigate(kids_basket) place(living_car,kids_basket)

### Task-Level

* `whose` (v6_whose, 5 steps): look(tv_stand_2/top) navigate(kid_book) pick(kid_book) navigate(bookcase_2/top) place(kid_book,bookcase_2/top,[1.12, -0.43])
* `scattered` (v6_scattered, 14 steps): explore_room(living_room_0_0) navigate(living_car) pick(living_car) explore_room(bedroom_0_1) navigate(kids_basket) place(living_car,kids_basket) navigate(living_duck) pick(living_duck) navigate(kids_basket) place(living_duck,kids_basket) navigate(living_block) pick(living_block) navigate(kids_basket) place(living_block,kids_basket)
* `where_in_room` (v6_where_in_room, 10 steps): explore_room(living_room_0_0) navigate(living_car) pick(living_car) explore_room(bedroom_0_1) navigate(kids_basket) place(living_car,kids_basket) navigate(kid_book) pick(kid_book) navigate(bookcase_2/top) place(kid_book,bookcase_2/top,[1.12, -0.43])
* `bear_to_bed` (v6_bear_to_bed, 5 steps): look(tv_stand_2/top) navigate(living_bear) pick(living_bear) navigate(mattress_1/top) place(living_bear,mattress_1/top,[0.0, -4.0])
* `two_bedrooms__room_east` (v6_two_bedrooms__room_east, 5 steps): navigate(living_car) pick(living_car) search(kids_basket,bedroom_0_1) navigate(kids_basket) place(living_car,kids_basket)
* `two_bedrooms__room_south` (v6_two_bedrooms__room_south, 5 steps): navigate(living_car) pick(living_car) search(kids_basket,bedroom_0_0) navigate(kids_basket) place(living_car,kids_basket)

## T27_leftovers_to_fridge

### Control

* `rice_on_table` (nominal, 9 steps): navigate(breakfast_fridge) open(breakfast_fridge) navigate(dining_table_2/top) look(dining_table_2/top) navigate(leftover_rice) pick(leftover_rice) navigate(breakfast_fridge) place(leftover_rice,breakfast_fridge/inside_shelf,[5.78, 3.18]) close(breakfast_fridge)

### Task-Level

* `which_is_leftover` (v6_which_is_leftover, 8 steps): look(dining_table_2/top) navigate(breakfast_fridge) open(breakfast_fridge) navigate(leftover_rice) pick(leftover_rice) navigate(breakfast_fridge) place(leftover_rice,breakfast_fridge/inside_shelf,[5.78, 3.18]) close(breakfast_fridge)
* `fruit_stays_out` (v6_fruit_stays_out, 8 steps): look(dining_table_2/top) navigate(breakfast_fridge) open(breakfast_fridge) navigate(leftover_rice) pick(leftover_rice) navigate(breakfast_fridge) place(leftover_rice,breakfast_fridge/inside_shelf,[5.78, 3.18]) close(breakfast_fridge)
* `still_eating` (v6_still_eating, 8 steps): look(dining_table_2/top) navigate(breakfast_fridge) open(breakfast_fridge) navigate(leftover_rice) pick(leftover_rice) navigate(breakfast_fridge) place(leftover_rice,breakfast_fridge/inside_shelf,[5.78, 3.18]) close(breakfast_fridge)
* `two_leftovers__soup_on_table` (v6_two_leftovers__soup_on_table, 12 steps): look(dining_table_2/top) navigate(breakfast_fridge) open(breakfast_fridge) navigate(leftover_rice) pick(leftover_rice) navigate(breakfast_fridge) place(leftover_rice,breakfast_fridge/inside_shelf,[5.78, 3.18]) navigate(leftover_soup) pick(leftover_soup) navigate(breakfast_fridge) place(leftover_soup,breakfast_fridge/inside_shelf,[5.98, 3.18]) close(breakfast_fridge)
* `two_leftovers__soup_on_stove` (v6_two_leftovers__soup_on_stove, 13 steps): look(dining_table_2/top) look(kitchen_stove/top) navigate(breakfast_fridge) open(breakfast_fridge) navigate(leftover_rice) pick(leftover_rice) navigate(breakfast_fridge) place(leftover_rice,breakfast_fridge/inside_shelf,[5.78, 3.18]) navigate(leftover_soup) pick(leftover_soup) navigate(breakfast_fridge) place(leftover_soup,breakfast_fridge/inside_shelf,[5.98, 3.18]) close(breakfast_fridge)
* `fridge_out_of_view` (v6_fridge_out_of_view, 9 steps): look(dining_table_2/top) explore_room(living_room_0_0) navigate(breakfast_fridge) open(breakfast_fridge) navigate(leftover_rice) pick(leftover_rice) navigate(breakfast_fridge) place(leftover_rice,breakfast_fridge/inside_shelf,[5.78, 3.18]) close(breakfast_fridge)

## T28_cup_to_bedside

### Control

* `cup_on_counter` (nominal, 6 steps): navigate(kitchen_counter_2/top) look(kitchen_counter_2/top) navigate(kid_cup) pick(kid_cup) navigate(bookcase_3/top) place(kid_cup,bookcase_3/top,[2.1, -4.88])

### Task-Level

* `which_bed__east` (v6_which_bed__east, 7 steps): navigate(kitchen_counter_2/top) look(kitchen_counter_2/top) navigate(kid_cup) pick(kid_cup) look(mattress_2/top) navigate(bookcase_3/top) place(kid_cup,bookcase_3/top,[2.1, -4.88])
* `which_bed__south` (v6_which_bed__south, 7 steps): navigate(kitchen_counter_2/top) look(kitchen_counter_2/top) navigate(kid_cup) pick(kid_cup) look(mattress_1/top) navigate(cell_shelf_2/top) place(kid_cup,cell_shelf_2/top,[1.42, -10.8])
* `where_his_cup_is__on_counter` (v6_where_his_cup_is__on_counter, 5 steps): look(kitchen_counter_2/top) navigate(kid_cup) pick(kid_cup) navigate(bookcase_3/top) place(kid_cup,bookcase_3/top,[2.1, -4.88])
* `where_his_cup_is__in_cabinet` (v6_where_his_cup_is__in_cabinet, 12 steps): look(kitchen_counter_2/top) navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(kid_cup) pick(kid_cup) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(bookcase_3/top) place(kid_cup,bookcase_3/top,[2.1, -4.88])
* `cup_out_of_view` (v6_cup_out_of_view, 6 steps): look(kitchen_counter_2/top) search(kid_cup,dining_room_0_1) navigate(kid_cup) pick(kid_cup) navigate(bookcase_3/top) place(kid_cup,bookcase_3/top,[2.1, -4.88])
* `already_there` (v6_already_there, 2 steps): navigate(bookcase_3/top) look(bookcase_3/top)

## T29_clear_table_for_dinner

### Control

* `car_on_table` (nominal, 5 steps): look(dining_table_2/top) navigate(table_car) pick(table_car) navigate(toy_box) place(table_car,toy_box)

### Task-Level

* `belongs_on_table` (v6_belongs_on_table, 5 steps): look(dining_table_2/top) navigate(table_car) pick(table_car) navigate(toy_box) place(table_car,toy_box)
* `nothing_to_clear` (v6_nothing_to_clear, 2 steps): navigate(dining_table_2/top) look(dining_table_2/top)
* `homework_on_table` (v6_homework_on_table, 9 steps): look(dining_table_2/top) navigate(hw_notebook) pick(hw_notebook) navigate(desk_1/top) place(hw_notebook,desk_1/top,[-0.7, -5.95]) navigate(hw_pencil) pick(hw_pencil) navigate(desk_1/top) place(hw_pencil,desk_1/top,[-0.35, -5.95])
* `several` (v6_several, 13 steps): look(dining_table_2/top) navigate(table_car) pick(table_car) navigate(toy_box) place(table_car,toy_box) navigate(empty_can) pick(empty_can) navigate(trash_can) drop(empty_can,trash_can) navigate(table_book) pick(table_book) navigate(bookcase_2/top) place(table_book,bookcase_2/top,[1.0, -0.43])
* `which_table__east` (v6_which_table__east, 6 steps): look(dining_table_2/top) look(dining_table_1/top) navigate(toy_east) pick(toy_east) navigate(toy_box) place(toy_east,toy_box)
* `which_table__west` (v6_which_table__west, 6 steps): look(dining_table_2/top) look(dining_table_1/top) navigate(toy_west) pick(toy_west) navigate(toy_box) place(toy_west,toy_box)

## T30_bowls_for_soup

### Control

* `bowl_on_cabinet` (nominal, 4 steps): navigate(soup_bowl_1) pick(soup_bowl_1) navigate(kitchen_island/top) place(soup_bowl_1,kitchen_island/top,[8.05, 1.75])

### Task-Level

* `how_many` (v6_how_many, 13 steps): look(dining_table_2/top) navigate(soup_bowl_1) pick(soup_bowl_1) navigate(kitchen_island/top) place(soup_bowl_1,kitchen_island/top,[7.65, 1.75]) navigate(soup_bowl_2) pick(soup_bowl_2) navigate(kitchen_island/top) place(soup_bowl_2,kitchen_island/top,[7.85, 1.75]) navigate(soup_bowl_3) pick(soup_bowl_3) navigate(kitchen_island/top) place(soup_bowl_3,kitchen_island/top,[8.05, 1.75])
* `bowls_in_cabinet__two_inside` (v6_bowls_in_cabinet__two_inside, 20 steps): look(dining_table_2/top) navigate(soup_bowl_1) pick(soup_bowl_1) navigate(kitchen_island/top) place(soup_bowl_1,kitchen_island/top,[7.65, 1.75]) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(soup_bowl_2) pick(soup_bowl_2) navigate(kitchen_island/top) place(soup_bowl_2,kitchen_island/top,[7.85, 1.75]) navigate(soup_bowl_3) pick(soup_bowl_3) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(kitchen_island/top) place(soup_bowl_3,kitchen_island/top,[8.05, 1.75])
* `bowls_in_cabinet__one_inside` (v6_bowls_in_cabinet__one_inside, 20 steps): look(dining_table_2/top) navigate(soup_bowl_1) pick(soup_bowl_1) navigate(kitchen_island/top) place(soup_bowl_1,kitchen_island/top,[7.65, 1.75]) navigate(kitchen_cabinet_6) open(kitchen_cabinet_6) bend() explore_furniture(kitchen_cabinet_6) straighten() navigate(soup_bowl_2) pick(soup_bowl_2) retreat(kitchen_cabinet_6,0.3) close(kitchen_cabinet_6) navigate(kitchen_island/top) place(soup_bowl_2,kitchen_island/top,[7.85, 1.75]) navigate(spare_mug) pick(spare_mug) navigate(kitchen_island/top) place(spare_mug,kitchen_island/top,[8.05, 1.75])
* `bowl_put_away` (v6_bowl_put_away, 11 steps): navigate(kitchen_cabinet_4) open(kitchen_cabinet_4) bend() explore_furniture(kitchen_cabinet_4) straighten() navigate(soup_bowl_1) pick(soup_bowl_1) retreat(kitchen_cabinet_4,0.3) close(kitchen_cabinet_4) navigate(kitchen_island/top) place(soup_bowl_1,kitchen_island/top,[8.05, 1.75])
* `no_bowl` (v6_no_bowl, 5 steps): look(kitchen_cabinet_6/top) navigate(spare_mug) pick(spare_mug) navigate(kitchen_island/top) place(spare_mug,kitchen_island/top,[8.05, 1.75])
* `bowl_not_plate` (v6_bowl_not_plate, 5 steps): look(kitchen_cabinet_6/top) navigate(soup_bowl_1) pick(soup_bowl_1) navigate(kitchen_island/top) place(soup_bowl_1,kitchen_island/top,[8.05, 1.75])
* `clean_one` (v6_clean_one, 5 steps): look(kitchen_cabinet_6/top) navigate(soup_bowl_1) pick(soup_bowl_1) navigate(kitchen_island/top) place(soup_bowl_1,kitchen_island/top,[8.05, 1.75])
