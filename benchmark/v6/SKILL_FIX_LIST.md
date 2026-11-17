# Skill Fix List (for the skill / physics owner)

Task design does not change skills; this list is what the v5 physics baseline (1,800 oracle episodes, `benchmark/v5/PHYSICS.json`) and the v6 reference routes need from them. No new skill interface is required: every v6 route uses existing contracts. Counts are calls in oracle episodes that were expected to succeed.

## 1. Failing skill uses in the v5 baseline (>= 3 failures)

| skill | object | ok | failed | fail rate | main causes | tasks | v6 variants also using it | example |
|---|---|---|---|---|---|---|---|---|
| pick | juice_bottle | 24 | 62 | 72% | grasp miss 58, articulation (door does not move) 3, IK / reach / base pose 1 | T20 | 0 | pick juice_bottle: not held (lift -0.001 m) |
| navigate | dining_table_2/top | 407 | 51 | 11% | carry slip 51 | T01 T13 T20 | 38 | carry: paperback_book slipped out of the hand while carrying it |
| navigate | bookcase_2/top | 377 | 49 | 12% | carry slip 49 | T11 T14 | 18 | carry: apple slipped out of the hand while carrying it |
| wipe | kitchen_island/top | 21 | 44 | 68% | IK / reach / base pose 23, carry slip 17, other 4 | T08 | 3 | wipe kitchen_island/top: no base pose reaches the strip (rejected: {'candidates': 3433, 'footprint': 197, 'travel_pose': 30, 'ik': 47, 'ride |
| pick | mug | 56 | 40 | 42% | grasp miss 40 | T04 T13 | 3 | pick mug: not held (lift 0.000 m) |
| open | kitchen_cabinet_4 | 0 | 38 | 100% | articulation (door does not move) 23, grasp miss 15 | T18 | 9 | open kitchen_cabinet_4: joint -0.000 -> -0.000, goal -1.400 |
| open | kitchen_cabinet_6 | 95 | 34 | 26% | grasp miss 26, IK / reach / base pose 6, articulation (door does not move) 2 | T05 T18 | 10 | grasp handle kitchen_cabinet_6: no finger contact |
| flip | paperback_book | 52 | 34 | 40% | IK / reach / base pose 13, other 11, placement result 7 | T15 | 0 | POSTCONDITION_FAILED: flipped(object=paperback_book) is false (z dot -0.38) |
| separate | wooden_block_b | 15 | 21 | 58% | other 15, perception / search 6 | T02 T17 | 0 | PRECONDITION_FAILED: hand_empty(hand=right) is false (right holds wooden_block_b); not grasp_clearance(object=wooden_block_b) is false (pinc |
| approach | soda_can | 20 | 20 | 50% | IK / reach / base pose 20 | T10 | 0 | approach soda_can: no base pose reaches it (rejected: {'candidates': 3432, 'out_of_reach': 44, 'footprint': 799, 'travel_pose': 112, 'ik': 4 |
| uncover | handled_cooking_pot | 31 | 19 | 38% | grasp miss 19 | T09 T17 | 0 | pick pot_lid: not held (lift 0.000 m) |
| pick | soda_can | 151 | 19 | 11% | IK / reach / base pose 10, grasp miss 9 | T10 T19 | 7 | pick soda_can: not held (lift -0.160 m) |
| place | mug | 29 | 18 | 38% | carry slip 16, other 1, placement result 1 | T04 T13 | 3 | carry: mug slipped out of the hand while carrying it |
| approach | kitchen_island/top | 43 | 17 | 28% | other 16, IK / reach / base pose 1 | T08 | 0 | approach kitchen_island/top: parked but IK fails at [7.564, 1.565, 0.96] |
| place | book_red | 8 | 17 | 68% | carry slip 7, placement result 5, IK / reach / base pose 3 | T14 | 5 | flat_turn: book_red slipped out of the hand while carrying it |
| drop | rubber_duck | 23 | 15 | 39% | carry slip 7, IK / reach / base pose 4, other 4 | T12 | 1 | no IK for drop_prelift |
| place | cup_counter_b | 27 | 14 | 34% | carry slip 10, placement result 3, other 1 | T04 | 3 | place_above: cup_counter_b slipped out of the hand while carrying it |
| pick | breakfast_spoon | 146 | 12 | 8% | grasp miss 12 | T03 T09 | 5 | pick breakfast_spoon: not held (lift -0.001 m) |
| hide | wooden_block_b | 35 | 12 | 26% | carry slip 6, placement result 3, grasp miss 2 | T17 | 1 | SUBSKILL_FAILED: fetch_object(object=wooden_block_b, receptacle=handled_cooking_pot): SUBSKILL_FAILED: pick_object(object=wooden_block_b): p |
| pick | wooden_block_b | 80 | 11 | 12% | grasp miss 10, IK / reach / base pose 1 | T02 T08 | 6 | pick wooden_block_b: not held (lift 0.000 m) |
| place | wooden_block_a | 127 | 10 | 7% | carry slip 10 | T06 T15 | 7 | carry_stand_up: wooden_block_a slipped out of the hand while carrying it |
| search | pot_lid | 0 | 10 | 100% | perception / search 10 | T17 | 0 | search pot_lid: not seen at ['kitchen_island', 'kitchen_stove', 'breakfast_fridge', 'tv_stand_2', 'kitchen_microwave', 'kitchen_cabinet_6',  |
| inspect |  | 78 | 10 | 11% | other 10 | T18 | 2 | inspect kitchen_cabinet_6: line of sight blocked (h 0, v -12 deg) |
| drop | foam_cube | 73 | 10 | 12% | IK / reach / base pose 10 | T19 | 2 | drop foam_cube: no base pose above wide_storage_bin (rejected: {'candidates': 3433, 'out_of_reach': 89, 'footprint': 990, 'travel_pose': 30, |
| regrasp | book_red | 0 | 10 | 100% | grasp miss 10 | T14 | 0 | edge pinch book_red: overhang only -0.026 m |
| navigate | kitchen_cabinet_6/top | 284 | 8 | 3% | carry slip 8 | T04 | 7 | carry: cup_counter_b slipped out of the hand while carrying it |
| pick | kitchen_sponge | 82 | 8 | 9% | grasp miss 8 | T08 | 3 | pick kitchen_sponge: not held (lift 0.000 m) |
| place | apple | 73 | 8 | 10% | IK / reach / base pose 8 | T11 | 1 | place_pre: no IK solution reaches apple from this base pose |
| look | desk_1/top | 150 | 8 | 5% | IK / reach / base pose 8 | T14 | 8 | face desk_1/top: turning in place would hit furniture |
| arrange |  | 2 | 8 | 80% | IK / reach / base pose 5, other 2, placement result 1 | T13 | 0 | SUBSKILL_FAILED: pick_object(object=cup): no IK for pick_lift |
| pick | oatmeal | 162 | 7 | 4% | other 7 | T07 | 1 | pick from cavity oatmeal: front approach missed by 0.163 m |
| pick | pencil | 50 | 7 | 12% | IK / reach / base pose 5, grasp miss 2 | T05 | 5 | joint move to pick_pre_far: no collision-free trajectory (MotionGenStatus.TRAJOPT_FAIL) |
| pick | pot_lid | 90 | 7 | 7% | grasp miss 7 | T17 | 2 | pick pot_lid: not held (lift 0.010 m) |
| place | rolling_pin | 72 | 6 | 8% | other 5, carry slip 1 | T03 | 4 | carry: rolling_pin slipped out of the hand while carrying it |
| place | oatmeal | 156 | 6 | 4% | other 4, IK / reach / base pose 1, placement result 1 | T04 T07 T16 | 1 | no IK for place_above |
| pick | bowl | 83 | 6 | 7% | grasp miss 6 | T13 | 2 | pick bowl: not held (lift 0.000 m) |
| expose | paperback_book | 25 | 5 | 17% | other 5 | T01 | 4 | slide to edge: centre of mass may leave the support |
| look | rolling_pin | 33 | 5 | 13% | IK / reach / base pose 3, perception / search 2 | T03 | 0 | NOT_FOUND: 'rolling_pin' is not visible at its last observed position |
| stir | handled_cooking_pot | 60 | 5 | 8% | carry slip 3, other 2 | T09 | 1 | left_carry: handled_cooking_pot slipped from the left hand |
| lift | rolling_pin | 3 | 4 | 57% | other 3, IK / reach / base pose 1 | T03 | 0 | PRECONDITION_FAILED: holding(hand=right, object=rolling_pin) is false (right holds None) |
| place | bowl | 79 | 4 | 5% | placement result 4 | T13 | 2 | place bowl: xy err 0.326 m, on support True (dining_table_2/top) |
| place | party_bowl_1 | 36 | 4 | 10% | other 3, IK / reach / base pose 1 | T20 | 0 | place party_bowl_1: container shifted 0.067 m before release |
| collect | handled_cooking_pot | 78 | 3 | 4% | other 2, IK / reach / base pose 1 | T09 | 1 | SUBSKILL_FAILED: fetch_object(object=cherry_tomato_2, receptacle=handled_cooking_pot): SUBSKILL_FAILED: place_object(object=cherry_tomato_2, |
| hover | soda_can | 26 | 3 | 10% | other 2, carry slip 1 | T10 | 4 | POSTCONDITION_FAILED: hovering_over(object=soda_can, target=trash_can) is false (xy 0.252 m, above by 0.343 m) |
| pick | rubber_duck | 86 | 3 | 3% | IK / reach / base pose 2, grasp miss 1 | T12 | 6 | pick rubber_duck: no reachable grasp from any base pose |
| place | cup | 27 | 3 | 10% | placement result 3 | T13 | 1 | place cup: xy err 0.058 m, on support False (bottom at (3.15, 7.45, 0.933)) |
| look | book_red | 57 | 3 | 5% | perception / search 3 | T14 | 0 | NOT_FOUND: 'book_red' is not visible at its last observed position |

## 2. Skill uses the v6 routes need that the v5 baseline never ran

| skill | object | variants |
|---|---|---|
| close | breakfast_fridge | T10/after_dinner_clear, T22/basket_in_use, T22/basket_out_of_reach, T22/by_kind, T22/eat_now, T22/not_shopping, T22/tray_elsewhere, T22/two_spots, T25/cold_one |
| close | kitchen_cabinet_4 | T02/block_put_away, T04/no_cup_in_cabinets, T04/x6_gd_cup_in_cabinets, T05/x6_gd_pen_or_pencil_cabinets, T12/where_his_cup_is, T17/no_pot, T18/door_stuck, T18/plate_not_bowl, T25/cups_for_two |
| drop | empty_can | T10/clear_table_for_dinner |
| drop | takeout_tray | T10/after_dinner_clear |
| expose | foil_takeout_tray | T07/vessel_decides_appliance |
| expose | glass_food_container | T07/vessel_decides_appliance |
| expose | notebook_1 | T05/homework_ready |
| expose | notebook_2 | T05/homework_ready |
| expose | steel_lunch_box | T07/vessel_decides_appliance |
| identify | pen | T05/check_desk_first |
| identify | pencil | T05/check_desk_first |
| lift | takeout_tray | T10/after_dinner_clear |
| measure | example_spoon | T13/copy_the_setting |
| measure | toy_bin_small_2 | T12/bins_capacity |
| open | breakfast_fridge | T10/after_dinner_clear, T22/basket_in_use, T22/basket_out_of_reach, T22/by_kind, T22/eat_now, T22/not_shopping, T22/tray_elsewhere, T22/two_spots, T25/cold_one |
| pick | blue_book | T14/whose_book |
| pick | bought_apple | T22/basket_in_use, T22/basket_out_of_reach, T22/by_kind, T22/tray_elsewhere, T22/two_spots |
| pick | bought_juice | T22/basket_in_use, T22/basket_out_of_reach, T22/by_kind, T22/eat_now, T22/not_shopping, T22/tray_elsewhere, T22/two_spots |
| pick | bought_snack | T22/by_kind, T22/eat_now, T22/two_spots |
| pick | bowl_2 | T13/finish_the_table |
| pick | cold_juice | T25/cold_one |
| pick | desk_mug | T14/homework_stays |
| pick | dinner_bowl_1 | T18/bowl_in_use, T18/door_stuck, T18/one_bowl, T18/plate_not_bowl |
| pick | dinner_bowl_2 | T18/door_stuck, T18/plate_not_bowl |
| pick | dinner_spoon_1 | T18/bowl_in_use, T18/door_stuck, T18/no_bowl, T18/one_bowl, T18/plate_not_bowl |
| pick | dinner_spoon_2 | T18/bowl_in_use, T18/door_stuck, T18/no_bowl, T18/one_bowl, T18/plate_not_bowl |
| pick | dropped_block | T23/belongs_on_floor, T23/by_kind, T23/no_toy_box, T23/toy_box_full |
| pick | dropped_spoon | T23/belongs_on_floor, T23/by_kind, T23/no_toy_box, T23/toy_box_full |
| pick | empty_can | T10/clear_table_for_dinner |
| pick | floor_block | T02/block_put_away, T02/crowded_use_another, T02/tower_for_kid |
| pick | foil_takeout_tray | T07/vessel_decides_appliance |
| pick | fruit_box | T11/fruit_plate_for_guests |
| pick | glass_box | T18/bowl_in_use, T18/no_bowl, T18/one_bowl |
| pick | glass_food_container | T07/vessel_decides_appliance |
| pick | green_book_case | T14/no_second_red_book |
| pick | guest_cup | T25/cold_one |
| pick | guest_juice | T25/cups_for_two, T25/little_guest |
| pick | handled_cooking_pot | T09/pot_in_use |
| pick | hw_notebook | T10/clear_table_for_dinner |
| pick | hw_pencil | T10/clear_table_for_dinner |
| pick | kid_book | T12/his_things_by_kind, T12/his_things_whose |
| pick | kid_cup | T12/cup_to_bedside, T12/where_his_cup_is, T25/little_guest |
| pick | kid_plastic_cup | T04/no_cup_in_cabinets |
| pick | kid_small_bowl | T13/finish_the_table |
| pick | kids_teddy | T12/bedtime_toy |
| pick | leftovers | T10/after_dinner_clear |
| pick | living_car | T12/his_room, T12/his_things_by_kind |
| pick | loose_block_1 | T12/castle_stays |
| pick | loose_block_2 | T12/castle_stays |
| pick | lunch_banana | T11/no_apple_for_kid |
| pick | lunch_orange | T11/fruit_plate_for_guests |
| pick | notebook_1 | T05/homework_ready |
| pick | notebook_2 | T05/homework_ready |
| pick | oatmeal_bowl | T07/two_portions, T07/vessel_decides_appliance |
| pick | paperback | T14/whose_book |
| pick | pen | T05/check_desk_first, T05/homework_ready, T05/no_pencil, T05/pens_for_two, T05/pens_per_notebook, T05/x6_gd_pen_or_pencil_cabinets |
| pick | pen_2 | T05/pens_per_notebook |
| pick | pencil_2 | T05/pens_per_notebook |
| pick | plate_counter_a | T13/copy_the_setting, T15/lid_in_use, T15/no_lid |
| pick | red_book_2 | T14/next_in_series |
| pick | school_apple | T16/box_in_use, T16/no_box |
| pick | snack_apple | T24/dinner_soon, T24/where_is_he |
| pick | snack_banana | T24/apple_in_use |
| pick | snack_orange | T24/apple_on_floor |
| pick | soda_drink | T20/juice_finished, T20/juice_in_use |
| pick | soup_pot | T07/two_portions, T07/vessel_decides_appliance |
| pick | spare_bowl | T16/box_in_use, T16/no_box |
| pick | spare_mug | T18/no_bowl, T18/one_bowl |
| pick | spare_sponge | T21/no_tissue, T21/tissue_in_use |
| pick | steel_lunch_box | T07/vessel_decides_appliance |
| pick | stock_cup_1 | T25/cups_for_two |
| pick | stock_cup_2 | T25/cups_for_two |
| pick | table_book | T10/clear_table_for_dinner |
| pick | table_car | T10/clear_table_for_dinner |
| pick | takeout_tray | T10/after_dinner_clear |
| pick | tissue | T21/the_kids_side, T21/which_table |
| pick | toy_block | T02/third_toy_elsewhere |
| pick | tray_book_1 | T22/tray_elsewhere |
| pick | tray_book_2 | T22/tray_elsewhere |
| pick | tray_book_3 | T22/tray_elsewhere |
| pick | tray_book_4 | T22/tray_elsewhere |
| pick | used_mug | T05/errand_combined, T10/after_dinner_clear, T10/guests_coming |
| place | blue_book | T14/whose_book |
| place | bought_apple | T22/basket_in_use, T22/basket_out_of_reach, T22/by_kind, T22/tray_elsewhere, T22/two_spots |
| place | bought_juice | T22/basket_in_use, T22/basket_out_of_reach, T22/by_kind, T22/eat_now, T22/not_shopping, T22/tray_elsewhere, T22/two_spots |
| place | bought_snack | T22/by_kind, T22/eat_now, T22/two_spots |
| place | bowl_2 | T13/finish_the_table |
| place | cold_juice | T25/cold_one |
| place | desk_mug | T14/homework_stays |
| place | dinner_bowl_1 | T18/bowl_in_use, T18/door_stuck, T18/one_bowl, T18/plate_not_bowl |
| place | dinner_bowl_2 | T18/door_stuck, T18/plate_not_bowl |
| place | dinner_spoon_1 | T18/bowl_in_use, T18/door_stuck, T18/no_bowl, T18/one_bowl, T18/plate_not_bowl |
| place | dinner_spoon_2 | T18/bowl_in_use, T18/door_stuck, T18/no_bowl, T18/one_bowl, T18/plate_not_bowl |
| place | dropped_block | T23/belongs_on_floor, T23/by_kind, T23/no_toy_box, T23/toy_box_full |
| place | dropped_spoon | T23/belongs_on_floor, T23/by_kind, T23/no_toy_box, T23/toy_box_full |
| place | foil_takeout_tray | T07/vessel_decides_appliance |
| place | fruit_box | T11/fruit_plate_for_guests |
| place | glass_box | T18/bowl_in_use, T18/no_bowl, T18/one_bowl |
| place | glass_food_container | T07/vessel_decides_appliance |
| place | green_book_case | T14/no_second_red_book |
| place | guest_cup | T25/cold_one |
| place | guest_juice | T25/cups_for_two, T25/little_guest |
| place | handled_cooking_pot | T09/pot_in_use |
| place | hw_notebook | T10/clear_table_for_dinner |
| place | hw_pencil | T10/clear_table_for_dinner |
| place | kid_book | T12/his_things_by_kind, T12/his_things_whose |
| place | kid_cup | T12/cup_to_bedside, T12/where_his_cup_is, T25/little_guest |
| place | kid_plastic_cup | T04/no_cup_in_cabinets |
| place | kid_small_bowl | T13/finish_the_table |
| place | kids_teddy | T12/bedtime_toy |
| place | leftovers | T10/after_dinner_clear |
| place | living_car | T12/his_room, T12/his_things_by_kind |
| place | loose_block_1 | T12/castle_stays |
| place | loose_block_2 | T12/castle_stays |
| place | lunch_banana | T11/no_apple_for_kid |
| place | lunch_orange | T11/fruit_plate_for_guests |
| place | notebook_1 | T05/homework_ready |
| place | notebook_2 | T05/homework_ready |
| place | oatmeal_bowl | T07/two_portions, T07/vessel_decides_appliance |
| place | paperback | T14/whose_book |
| place | pen | T05/check_desk_first, T05/homework_ready, T05/no_pencil, T05/pens_for_two, T05/pens_per_notebook, T05/x6_gd_pen_or_pencil_cabinets |
| place | pen_2 | T05/pens_per_notebook |
| place | pencil_2 | T05/pens_per_notebook |
| place | plate_counter_a | T13/copy_the_setting |
| place | red_book_2 | T14/next_in_series |
| place | school_apple | T16/box_in_use, T16/no_box |
| place | snack_apple | T24/dinner_soon, T24/where_is_he |
| place | snack_banana | T24/apple_in_use |
| place | snack_orange | T24/apple_on_floor |
| place | soda_drink | T20/juice_finished, T20/juice_in_use |
| place | soup_pot | T07/two_portions, T07/vessel_decides_appliance |
| place | spare_bowl | T16/box_in_use, T16/no_box |
| place | spare_mug | T18/no_bowl, T18/one_bowl |
| place | spare_sponge | T21/no_tissue, T21/tissue_in_use |
| place | steel_lunch_box | T07/vessel_decides_appliance |
| place | stock_cup_1 | T25/cups_for_two |
| place | stock_cup_2 | T25/cups_for_two |
| place | table_book | T10/clear_table_for_dinner |
| place | table_car | T10/clear_table_for_dinner |
| place | tissue | T21/the_kids_side, T21/which_table |
| place | tray_book_1 | T22/tray_elsewhere |
| place | tray_book_2 | T22/tray_elsewhere |
| place | tray_book_3 | T22/tray_elsewhere |
| place | tray_book_4 | T22/tray_elsewhere |
| place | used_mug | T05/errand_combined, T10/after_dinner_clear, T10/guests_coming |
| stack | bowl | T13/copy_the_setting |
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

