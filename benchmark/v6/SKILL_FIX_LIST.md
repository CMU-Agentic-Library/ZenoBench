# Skill Fix List (for the skill / physics owner)

Task design does not change skills; this list is what the v5 physics baseline (1,800 oracle episodes, `benchmark/v5/PHYSICS.json`) and the v6 reference routes need from them. No new skill interface is required: every v6 route uses existing contracts. Counts are calls in oracle episodes that were expected to succeed.

## 1. Failing skill uses in the v5 baseline (>= 3 failures)

| skill | object | ok | failed | fail rate | main causes | tasks | v6 variants also using it | example |
|---|---|---|---|---|---|---|---|---|
| pick | juice_bottle | 24 | 62 | 72% | grasp miss 58, articulation (door does not move) 3, IK / reach / base pose 1 | T20 | 1 | pick juice_bottle: not held (lift -0.001 m) |
| navigate | dining_table_2/top | 407 | 51 | 11% | carry slip 51 | T01 T13 T20 | 18 | carry: paperback_book slipped out of the hand while carrying it |
| navigate | bookcase_2/top | 377 | 49 | 12% | carry slip 49 | T11 T14 | 16 | carry: apple slipped out of the hand while carrying it |
| wipe | kitchen_island/top | 21 | 44 | 68% | IK / reach / base pose 23, carry slip 17, other 4 | T08 | 3 | wipe kitchen_island/top: no base pose reaches the strip (rejected: {'candidates': 3433, 'footprint': 197, 'travel_pose': 30, 'ik': 47, 'ride |
| pick | mug | 56 | 40 | 42% | grasp miss 40 | T04 T13 | 4 | pick mug: not held (lift 0.000 m) |
| open | kitchen_cabinet_4 | 0 | 38 | 100% | articulation (door does not move) 23, grasp miss 15 | T18 | 12 | open kitchen_cabinet_4: joint -0.000 -> -0.000, goal -1.400 |
| open | kitchen_cabinet_6 | 95 | 34 | 26% | grasp miss 26, IK / reach / base pose 6, articulation (door does not move) 2 | T05 T18 | 13 | grasp handle kitchen_cabinet_6: no finger contact |
| flip | paperback_book | 52 | 34 | 40% | IK / reach / base pose 13, other 11, placement result 7 | T15 | 1 | POSTCONDITION_FAILED: flipped(object=paperback_book) is false (z dot -0.38) |
| separate | wooden_block_b | 15 | 21 | 58% | other 15, perception / search 6 | T02 T17 | 0 | PRECONDITION_FAILED: hand_empty(hand=right) is false (right holds wooden_block_b); not grasp_clearance(object=wooden_block_b) is false (pinc |
| approach | soda_can | 20 | 20 | 50% | IK / reach / base pose 20 | T10 | 0 | approach soda_can: no base pose reaches it (rejected: {'candidates': 3432, 'out_of_reach': 44, 'footprint': 799, 'travel_pose': 112, 'ik': 4 |
| uncover | handled_cooking_pot | 31 | 19 | 38% | grasp miss 19 | T09 T17 | 1 | pick pot_lid: not held (lift 0.000 m) |
| pick | soda_can | 151 | 19 | 11% | IK / reach / base pose 10, grasp miss 9 | T10 T19 | 6 | pick soda_can: not held (lift -0.160 m) |
| place | mug | 29 | 18 | 38% | carry slip 16, other 1, placement result 1 | T04 T13 | 4 | carry: mug slipped out of the hand while carrying it |
| approach | kitchen_island/top | 43 | 17 | 28% | other 16, IK / reach / base pose 1 | T08 | 2 | approach kitchen_island/top: parked but IK fails at [7.564, 1.565, 0.96] |
| place | book_red | 8 | 17 | 68% | carry slip 7, placement result 5, IK / reach / base pose 3 | T14 | 4 | flat_turn: book_red slipped out of the hand while carrying it |
| drop | rubber_duck | 23 | 15 | 39% | carry slip 7, IK / reach / base pose 4, other 4 | T12 | 1 | no IK for drop_prelift |
| place | cup_counter_b | 27 | 14 | 34% | carry slip 10, placement result 3, other 1 | T04 | 3 | place_above: cup_counter_b slipped out of the hand while carrying it |
| pick | breakfast_spoon | 146 | 12 | 8% | grasp miss 12 | T03 T09 | 9 | pick breakfast_spoon: not held (lift -0.001 m) |
| hide | wooden_block_b | 35 | 12 | 26% | carry slip 6, placement result 3, grasp miss 2 | T17 | 1 | SUBSKILL_FAILED: fetch_object(object=wooden_block_b, receptacle=handled_cooking_pot): SUBSKILL_FAILED: pick_object(object=wooden_block_b): p |
| pick | wooden_block_b | 80 | 11 | 12% | grasp miss 10, IK / reach / base pose 1 | T02 T08 | 7 | pick wooden_block_b: not held (lift 0.000 m) |
| place | wooden_block_a | 127 | 10 | 7% | carry slip 10 | T06 T15 | 7 | carry_stand_up: wooden_block_a slipped out of the hand while carrying it |
| search | pot_lid | 0 | 10 | 100% | perception / search 10 | T17 | 0 | search pot_lid: not seen at ['kitchen_island', 'kitchen_stove', 'breakfast_fridge', 'tv_stand_2', 'kitchen_microwave', 'kitchen_cabinet_6',  |
| inspect |  | 78 | 10 | 11% | other 10 | T18 | 5 | inspect kitchen_cabinet_6: line of sight blocked (h 0, v -12 deg) |
| drop | foam_cube | 73 | 10 | 12% | IK / reach / base pose 10 | T19 | 1 | drop foam_cube: no base pose above wide_storage_bin (rejected: {'candidates': 3433, 'out_of_reach': 89, 'footprint': 990, 'travel_pose': 30, |
| regrasp | book_red | 0 | 10 | 100% | grasp miss 10 | T14 | 0 | edge pinch book_red: overhang only -0.026 m |
| navigate | kitchen_cabinet_6/top | 284 | 8 | 3% | carry slip 8 | T04 | 5 | carry: cup_counter_b slipped out of the hand while carrying it |
| pick | kitchen_sponge | 82 | 8 | 9% | grasp miss 8 | T08 | 3 | pick kitchen_sponge: not held (lift 0.000 m) |
| place | apple | 73 | 8 | 10% | IK / reach / base pose 8 | T11 | 2 | place_pre: no IK solution reaches apple from this base pose |
| look | desk_1/top | 150 | 8 | 5% | IK / reach / base pose 8 | T14 | 7 | face desk_1/top: turning in place would hit furniture |
| arrange |  | 2 | 8 | 80% | IK / reach / base pose 5, other 2, placement result 1 | T13 | 0 | SUBSKILL_FAILED: pick_object(object=cup): no IK for pick_lift |
| pick | oatmeal | 162 | 7 | 4% | other 7 | T07 | 1 | pick from cavity oatmeal: front approach missed by 0.163 m |
| pick | pencil | 50 | 7 | 12% | IK / reach / base pose 5, grasp miss 2 | T05 | 3 | joint move to pick_pre_far: no collision-free trajectory (MotionGenStatus.TRAJOPT_FAIL) |
| pick | pot_lid | 90 | 7 | 7% | grasp miss 7 | T17 | 4 | pick pot_lid: not held (lift 0.010 m) |
| place | rolling_pin | 72 | 6 | 8% | other 5, carry slip 1 | T03 | 5 | carry: rolling_pin slipped out of the hand while carrying it |
| place | oatmeal | 156 | 6 | 4% | other 4, IK / reach / base pose 1, placement result 1 | T04 T07 T16 | 1 | no IK for place_above |
| pick | bowl | 83 | 6 | 7% | grasp miss 6 | T13 | 2 | pick bowl: not held (lift 0.000 m) |
| expose | paperback_book | 25 | 5 | 17% | other 5 | T01 | 0 | slide to edge: centre of mass may leave the support |
| look | rolling_pin | 33 | 5 | 13% | IK / reach / base pose 3, perception / search 2 | T03 | 0 | NOT_FOUND: 'rolling_pin' is not visible at its last observed position |
| stir | handled_cooking_pot | 60 | 5 | 8% | carry slip 3, other 2 | T09 | 4 | left_carry: handled_cooking_pot slipped from the left hand |
| lift | rolling_pin | 3 | 4 | 57% | other 3, IK / reach / base pose 1 | T03 | 0 | PRECONDITION_FAILED: holding(hand=right, object=rolling_pin) is false (right holds None) |
| place | bowl | 79 | 4 | 5% | placement result 4 | T13 | 2 | place bowl: xy err 0.326 m, on support True (dining_table_2/top) |
| place | party_bowl_1 | 36 | 4 | 10% | other 3, IK / reach / base pose 1 | T20 | 0 | place party_bowl_1: container shifted 0.067 m before release |
| collect | handled_cooking_pot | 78 | 3 | 4% | other 2, IK / reach / base pose 1 | T09 | 4 | SUBSKILL_FAILED: fetch_object(object=cherry_tomato_2, receptacle=handled_cooking_pot): SUBSKILL_FAILED: place_object(object=cherry_tomato_2, |
| hover | soda_can | 26 | 3 | 10% | other 2, carry slip 1 | T10 | 4 | POSTCONDITION_FAILED: hovering_over(object=soda_can, target=trash_can) is false (xy 0.252 m, above by 0.343 m) |
| pick | rubber_duck | 86 | 3 | 3% | IK / reach / base pose 2, grasp miss 1 | T12 | 6 | pick rubber_duck: no reachable grasp from any base pose |
| place | cup | 27 | 3 | 10% | placement result 3 | T13 | 1 | place cup: xy err 0.058 m, on support False (bottom at (3.15, 7.45, 0.933)) |
| look | book_red | 57 | 3 | 5% | perception / search 3 | T14 | 0 | NOT_FOUND: 'book_red' is not visible at its last observed position |

## 2. Skill uses the v6 routes need that the v5 baseline never ran

| skill | object | variants |
|---|---|---|
| approach | serving_tray | T03/no_bin_substitute |
| approach | sponge_tray | T08/return_sponge_home |
| approach | toy_box | T08/wipe_and_sort, T10/guests_coming |
| close | breakfast_fridge | T09/tomato_in_fridge, T10/after_dinner_clear, T22/basket_missing, T22/by_kind, T22/eat_now, T22/not_shopping, T22/two_spots, T25/cold_one, T25/drink_in_fridge, T27/fridge_out_of_view, T27/fruit_stays_out, T27/still_eating, T27/two_leftovers, T27/which_is_leftover |
| close | kitchen_cabinet_4 | T02/block_put_away, T04/x6_gd_cup_in_cabinets, T05/x6_gd_pen_or_pencil_cabinets, T17/new_spot_this_time, T18/x6_gd_bowl_elsewhere__three_places, T19/x6_gd_can_put_away, T20/x6_gd_bottle_put_away, T21/no_tissue_sponge_away, T21/tissue_put_away, T28/cup_put_away, T28/his_cup_put_away, T30/bowl_put_away |
| drop | cherry_tomato_2 | T09/x6_gd_tomato_elsewhere |
| drop | empty_can | T29/several |
| drop | fridge_tomato | T09/tomato_in_fridge |
| drop | takeout_tray | T10/after_dinner_clear |
| expose | foil_takeout_tray | T07/vessel_decides_appliance |
| expose | glass_food_container | T07/vessel_decides_appliance |
| expose | notebook_1 | T05/homework_ready |
| expose | notebook_2 | T05/homework_ready |
| expose | steel_lunch_box | T07/vessel_decides_appliance |
| hide | floor_block | T17/hide_both |
| identify | pen | T05/check_desk_first |
| identify | pencil | T05/check_desk_first |
| lift | takeout_tray | T10/after_dinner_clear |
| measure | example_spoon | T13/copy_the_setting |
| measure | toy_bin_small_2 | T12/bins_capacity |
| open | breakfast_fridge | T09/tomato_in_fridge, T10/after_dinner_clear, T22/basket_missing, T22/by_kind, T22/eat_now, T22/not_shopping, T22/two_spots, T25/cold_one, T25/drink_in_fridge, T27/fridge_out_of_view, T27/fruit_stays_out, T27/still_eating, T27/two_leftovers, T27/which_is_leftover |
| pick | bought_apple | T22/basket_missing, T22/by_kind, T22/two_spots |
| pick | bought_juice | T22/basket_missing, T22/by_kind, T22/eat_now, T22/not_shopping, T22/two_spots |
| pick | bought_snack | T22/by_kind, T22/eat_now, T22/two_spots |
| pick | bowl_2 | T13/finish_the_table |
| pick | bowl_inside_kitchen_cabinet | T30/not_enough_bowls |
| pick | bowl_kitchen_cabinet | T18/enough_for_dinner, T30/not_enough_bowls |
| pick | bowl_side_table | T18/enough_for_dinner |
| pick | cherry_tomato_2 | T09/x6_gd_tomato_elsewhere |
| pick | cold_juice | T25/cold_one, T25/drink_in_fridge |
| pick | desk_book_blue | T14/stack_them_stably |
| pick | desk_book_green | T14/stack_them_stably |
| pick | desk_mug | T14/homework_stays |
| pick | desk_paperback_book | T14/stack_them_stably |
| pick | dropped_block | T23/by_kind |
| pick | dropped_pencil | T23/dropped_in_two_rooms |
| pick | dropped_spoon | T23/belongs_on_floor, T23/by_kind, T23/dropped_in_two_rooms, T23/dropped_out_of_view, T23/only_this_room |
| pick | edge_mug | T16/everything_near_the_edge |
| pick | empty_can | T29/several |
| pick | floor_block | T02/block_put_away, T02/crowded_use_another, T02/tower_for_kid, T06/display_row |
| pick | foil_takeout_tray | T07/vessel_decides_appliance |
| pick | fridge_tomato | T09/tomato_in_fridge |
| pick | fruit_tray | T11/fruit_plate_for_guests |
| pick | glass_food_container | T07/vessel_decides_appliance |
| pick | guest_cup | T25/cold_one, T25/drink_in_fridge, T25/two_guests |
| pick | guest_cup_2 | T25/two_guests |
| pick | guest_juice | T25/cup_elsewhere, T25/little_guest, T25/two_guests |
| pick | handled_cooking_pot | T09/pot_in_dining_room, T09/pot_in_use |
| pick | hw_notebook | T29/homework_on_table |
| pick | hw_pencil | T29/homework_on_table |
| pick | kid_book | T26/where_in_room, T26/whose |
| pick | kid_cup | T13/finish_the_table, T25/little_guest, T28/cup_out_of_view, T28/cup_put_away, T28/his_cup_put_away, T28/which_bed, T28/which_cup |
| pick | leftover_rice | T27/fridge_out_of_view, T27/fruit_stays_out, T27/still_eating, T27/two_leftovers, T27/which_is_leftover |
| pick | leftover_soup | T27/two_leftovers |
| pick | leftovers | T10/after_dinner_clear |
| pick | living_bear | T26/bear_to_bed |
| pick | living_block | T26/scattered |
| pick | living_car | T26/scattered, T26/two_bedrooms, T26/where_in_room |
| pick | living_duck | T26/scattered |
| pick | loose_block_1 | T12/castle_stays |
| pick | loose_block_2 | T12/castle_stays |
| pick | lunch_banana | T11/leave_one_for_kid |
| pick | lunch_orange | T11/fruit_plate_for_guests, T11/leave_one_for_kid |
| pick | notebook_1 | T05/homework_ready |
| pick | notebook_2 | T05/homework_ready |
| pick | novel | T14/whose_book |
| pick | oatmeal_bowl | T07/two_portions, T07/vessel_decides_appliance |
| pick | pen | T05/all_pens, T05/errand_combined, T05/homework_ready, T05/pens_per_notebook, T05/x6_gd_pen_or_pencil_cabinets |
| pick | pen_2 | T05/all_pens, T05/pens_per_notebook |
| pick | pencil_2 | T05/all_pens |
| pick | picture_book | T14/whose_book |
| pick | plate_counter_a | T13/copy_the_setting |
| pick | red_book_2 | T14/next_in_series |
| pick | snack_apple | T24/dinner_soon, T24/fruit_out_of_view, T24/two_kids, T24/where_is_he |
| pick | snack_banana | T24/no_apples_for_him, T24/two_kids |
| pick | soup_bowl_1 | T30/bowl_not_plate, T30/bowl_put_away, T30/clean_one, T30/how_many, T30/not_enough_bowls |
| pick | soup_bowl_2 | T30/how_many |
| pick | soup_bowl_3 | T30/how_many |
| pick | soup_pot | T07/two_portions, T07/vessel_decides_appliance |
| pick | spare_mug | T30/no_bowl |
| pick | spare_sponge | T21/no_tissue, T21/no_tissue_sponge_away |
| pick | steel_lunch_box | T07/vessel_decides_appliance |
| pick | stray_block | T12/find_all_toys |
| pick | table_book | T29/several |
| pick | table_car | T29/belongs_on_table, T29/several |
| pick | takeout_tray | T10/after_dinner_clear |
| pick | teddy_bear | T12/find_all_toys |
| pick | tissue | T21/the_kids_side, T21/tissue_out_of_view, T21/tissue_put_away, T21/which_table |
| pick | toy_block | T02/third_toy_elsewhere |
| pick | toy_east | T29/which_table |
| pick | toy_west | T29/which_table |
| pick | used_mug | T05/errand_combined, T10/after_dinner_clear, T10/guests_coming |
| place | bought_apple | T22/basket_missing, T22/by_kind, T22/two_spots |
| place | bought_juice | T22/basket_missing, T22/by_kind, T22/eat_now, T22/not_shopping, T22/two_spots |
| place | bought_snack | T22/by_kind, T22/eat_now, T22/two_spots |
| place | bowl_2 | T13/finish_the_table |
| place | bowl_inside_kitchen_cabinet | T30/not_enough_bowls |
| place | bowl_kitchen_cabinet | T18/enough_for_dinner, T30/not_enough_bowls |
| place | bowl_side_table | T18/enough_for_dinner |
| place | cold_juice | T25/cold_one, T25/drink_in_fridge |
| place | desk_book_green | T14/stack_them_stably |
| place | desk_mug | T14/homework_stays |
| place | dropped_block | T23/by_kind |
| place | dropped_pencil | T23/dropped_in_two_rooms |
| place | dropped_spoon | T23/belongs_on_floor, T23/by_kind, T23/dropped_in_two_rooms, T23/dropped_out_of_view, T23/only_this_room |
| place | edge_mug | T16/everything_near_the_edge |
| place | floor_block | T06/display_row |
| place | foil_takeout_tray | T07/vessel_decides_appliance |
| place | fruit_tray | T11/fruit_plate_for_guests |
| place | glass_food_container | T07/vessel_decides_appliance |
| place | guest_cup | T25/cold_one, T25/drink_in_fridge, T25/two_guests |
| place | guest_cup_2 | T25/two_guests |
| place | guest_juice | T25/cup_elsewhere, T25/little_guest, T25/two_guests |
| place | handled_cooking_pot | T09/pot_in_dining_room, T09/pot_in_use |
| place | hw_notebook | T29/homework_on_table |
| place | hw_pencil | T29/homework_on_table |
| place | kid_book | T26/where_in_room, T26/whose |
| place | kid_cup | T13/finish_the_table, T25/little_guest, T28/cup_out_of_view, T28/cup_put_away, T28/his_cup_put_away, T28/which_bed, T28/which_cup |
| place | leftover_rice | T27/fridge_out_of_view, T27/fruit_stays_out, T27/still_eating, T27/two_leftovers, T27/which_is_leftover |
| place | leftover_soup | T27/two_leftovers |
| place | leftovers | T10/after_dinner_clear |
| place | living_bear | T26/bear_to_bed |
| place | living_block | T26/scattered |
| place | living_car | T26/scattered, T26/two_bedrooms, T26/where_in_room |
| place | living_duck | T26/scattered |
| place | loose_block_1 | T12/castle_stays |
| place | loose_block_2 | T12/castle_stays |
| place | lunch_banana | T11/leave_one_for_kid |
| place | lunch_orange | T11/fruit_plate_for_guests, T11/leave_one_for_kid |
| place | notebook_1 | T05/homework_ready |
| place | notebook_2 | T05/homework_ready |
| place | novel | T14/whose_book |
| place | oatmeal_bowl | T07/two_portions, T07/vessel_decides_appliance |
| place | pen | T05/all_pens, T05/errand_combined, T05/homework_ready, T05/pens_per_notebook, T05/x6_gd_pen_or_pencil_cabinets |
| place | pen_2 | T05/all_pens, T05/pens_per_notebook |
| place | pencil_2 | T05/all_pens |
| place | picture_book | T14/whose_book |
| place | plate_counter_a | T13/copy_the_setting |
| place | red_book_2 | T14/next_in_series |
| place | snack_apple | T24/dinner_soon, T24/fruit_out_of_view, T24/two_kids, T24/where_is_he |
| place | snack_banana | T24/no_apples_for_him, T24/two_kids |
| place | soup_bowl_1 | T30/bowl_not_plate, T30/bowl_put_away, T30/clean_one, T30/how_many, T30/not_enough_bowls |
| place | soup_bowl_2 | T30/how_many |
| place | soup_bowl_3 | T30/how_many |
| place | soup_pot | T07/two_portions, T07/vessel_decides_appliance |
| place | spare_mug | T30/no_bowl |
| place | spare_sponge | T21/no_tissue, T21/no_tissue_sponge_away |
| place | steel_lunch_box | T07/vessel_decides_appliance |
| place | stray_block | T12/find_all_toys |
| place | table_book | T29/several |
| place | table_car | T29/belongs_on_table, T29/several |
| place | teddy_bear | T12/find_all_toys |
| place | tissue | T21/the_kids_side, T21/tissue_out_of_view, T21/tissue_put_away, T21/which_table |
| place | toy_east | T29/which_table |
| place | toy_west | T29/which_table |
| place | used_mug | T05/errand_combined, T10/after_dinner_clear, T10/guests_coming |
| stack | bowl | T13/copy_the_setting |
| stack | desk_book_blue | T14/stack_them_stably |
| stack | desk_paperback_book | T14/stack_them_stably |
| stack | floor_block | T02/block_put_away, T02/crowded_use_another, T02/tower_for_kid |
| stack | rubber_duck | T02/third_toy_elsewhere, T02/tower_for_kid_duck |
| stack | toy_block | T02/third_toy_elsewhere |
| wipe | dining_table_2/top | T08/which_surface |

## 3. Priorities

1. **Low cabinet doors** (`open` / `close` / `explore_furniture` on kitchen_cabinet_4 and _6): every v5 cabinet Hard was 0/10; v6 inspection variants (T04, T05, T10, T13, T18, T20) depend on them.
2. **Grasp of tall / round / rimmed objects**: juice bottle (side pinch knocks it over), mug and bowl rim pinches (T13, T20), cup carry.
3. **Book carry**: one-handed slip of paperback / red book (T01, T14); v6 adds the two-handed carry (`pick(hands=both)` then `navigate`) as the strategy-replacement route - it needs to work physically.
4. **Wipe reach** (T08) and **pick from inside the microwave cavity** (T10 v5 Hards 0/10; v6 `x6_gd_can_put_away__in_microwave`, `x6_gd_bowl_put_away__in_microwave`).
5. **Search of small objects** on the dining table (smoke run: `search wooden_block_b` did not see the block on the dining table in T06) and of the pot lid (v5: `search pot_lid` 0/10 in T17).
6. **Bimanual flat pick** (`pick(hands=both)`, zeno_skills/policies/bimanual.py): it needs the book's long side (half length >= 9 cm) along an overhanging edge; the T01 / T14 books overhang with the short side (yaw 90), so the two-handed carry of `x6_sr_two_hand_carry` stops there (smoke runs v6_smoke3/4, after the injected slips and the slip restore worked). Either accept short-edge overhangs or provide a re-orientation the route can call.
7. **Apple pick from the bookcase top** after it rolled out of the basket (T11 `x6_cl_apple_rolls_out`, smoke: `not held`).
8. **From the oracle smoke of the 40 new variants without a known blocker** (benchmark/runs/v6_smoke_free, one episode each; 18 pass end to end after two route fixes): `search` misses the object (floor block, wooden block, rubber duck, mug: 5), grasp `not held` (apple on the bookcase, orange, oatmeal bowl, pot lid: 5), carry slips of the paperback / mug (4), `look` / `face` blocked or the object out of the frustum (4), no IK for `hover_above` (T10) and the microwave button press (T07), placement off the support (spoon on the island), and the T12 two-bin capacity episode ending with a toy not fully inside.
9. New primitive uses: cherry-tomato `pick` + `drop` into the pot (T09 split), `place` into the trash can (T10) and of the foam cube into the bin (T19), `drop` + `cover` instead of `hide` (T17), three-block `stack` (T02).

