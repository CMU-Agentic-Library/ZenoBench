# Skill Fix List (for the skill / physics owner)

Task design does not change skills; this list is what the v5 physics baseline (1,800 oracle episodes, `benchmark/v5/PHYSICS.json`) and the v6 reference routes need from them. No new skill interface is required: every v6 route uses existing contracts. Counts are calls in oracle episodes that were expected to succeed.

## 1. Failing skill uses in the v5 baseline (>= 3 failures)

| skill | object | ok | failed | fail rate | main causes | tasks | v6 families also using it | example |
|---|---|---|---|---|---|---|---|---|
| pick | juice_bottle | 24 | 62 | 72% | grasp miss 58, articulation (door does not move) 3, IK / reach / base pose 1 | T20 | 2 | pick juice_bottle: not held (lift -0.001 m) |
| navigate | dining_table_2/top | 407 | 51 | 11% | carry slip 51 | T01 T13 T20 | 13 | carry: paperback_book slipped out of the hand while carrying it |
| navigate | bookcase_2/top | 377 | 49 | 12% | carry slip 49 | T11 T14 | 10 | carry: apple slipped out of the hand while carrying it |
| wipe | kitchen_island/top | 21 | 44 | 68% | IK / reach / base pose 23, carry slip 17, other 4 | T08 | 1 | wipe kitchen_island/top: no base pose reaches the strip (rejected: {'candidates': 3433, 'footprint': 197, 'travel_pose': 30, 'ik': 47, 'ride |
| pick | mug | 56 | 40 | 42% | grasp miss 40 | T04 T13 | 3 | pick mug: not held (lift 0.000 m) |
| open | kitchen_cabinet_4 | 0 | 38 | 100% | articulation (door does not move) 23, grasp miss 15 | T18 | 5 | open kitchen_cabinet_4: joint -0.000 -> -0.000, goal -1.400 |
| open | kitchen_cabinet_6 | 95 | 34 | 26% | grasp miss 26, IK / reach / base pose 6, articulation (door does not move) 2 | T05 T18 | 8 | grasp handle kitchen_cabinet_6: no finger contact |
| flip | paperback_book | 52 | 34 | 40% | IK / reach / base pose 13, other 11, placement result 7 | T15 | 0 | POSTCONDITION_FAILED: flipped(object=paperback_book) is false (z dot -0.38) |
| separate | wooden_block_b | 15 | 21 | 58% | other 15, perception / search 6 | T02 T17 | 0 | PRECONDITION_FAILED: hand_empty(hand=right) is false (right holds wooden_block_b); not grasp_clearance(object=wooden_block_b) is false (pinc |
| approach | soda_can | 20 | 20 | 50% | IK / reach / base pose 20 | T10 | 1 | approach soda_can: no base pose reaches it (rejected: {'candidates': 3432, 'out_of_reach': 44, 'footprint': 799, 'travel_pose': 112, 'ik': 4 |
| uncover | handled_cooking_pot | 31 | 19 | 38% | grasp miss 19 | T09 T17 | 1 | pick pot_lid: not held (lift 0.000 m) |
| pick | soda_can | 151 | 19 | 11% | IK / reach / base pose 10, grasp miss 9 | T10 T19 | 5 | pick soda_can: not held (lift -0.160 m) |
| place | mug | 29 | 18 | 38% | carry slip 16, other 1, placement result 1 | T04 T13 | 3 | carry: mug slipped out of the hand while carrying it |
| approach | kitchen_island/top | 43 | 17 | 28% | other 16, IK / reach / base pose 1 | T08 | 0 | approach kitchen_island/top: parked but IK fails at [7.564, 1.565, 0.96] |
| place | book_red | 8 | 17 | 68% | carry slip 7, placement result 5, IK / reach / base pose 3 | T14 | 2 | flat_turn: book_red slipped out of the hand while carrying it |
| drop | rubber_duck | 23 | 15 | 39% | carry slip 7, IK / reach / base pose 4, other 4 | T12 | 0 | no IK for drop_prelift |
| place | cup_counter_b | 27 | 14 | 34% | carry slip 10, placement result 3, other 1 | T04 | 2 | place_above: cup_counter_b slipped out of the hand while carrying it |
| pick | breakfast_spoon | 146 | 12 | 8% | grasp miss 12 | T03 T09 | 5 | pick breakfast_spoon: not held (lift -0.001 m) |
| hide | wooden_block_b | 35 | 12 | 26% | carry slip 6, placement result 3, grasp miss 2 | T17 | 3 | SUBSKILL_FAILED: fetch_object(object=wooden_block_b, receptacle=handled_cooking_pot): SUBSKILL_FAILED: pick_object(object=wooden_block_b): p |
| pick | wooden_block_b | 80 | 11 | 12% | grasp miss 10, IK / reach / base pose 1 | T02 T08 | 4 | pick wooden_block_b: not held (lift 0.000 m) |
| place | wooden_block_a | 127 | 10 | 7% | carry slip 10 | T06 T15 | 5 | carry_stand_up: wooden_block_a slipped out of the hand while carrying it |
| search | pot_lid | 0 | 10 | 100% | perception / search 10 | T17 | 2 | search pot_lid: not seen at ['kitchen_island', 'kitchen_stove', 'breakfast_fridge', 'tv_stand_2', 'kitchen_microwave', 'kitchen_cabinet_6',  |
| inspect |  | 78 | 10 | 11% | other 10 | T18 | 2 | inspect kitchen_cabinet_6: line of sight blocked (h 0, v -12 deg) |
| drop | foam_cube | 73 | 10 | 12% | IK / reach / base pose 10 | T19 | 1 | drop foam_cube: no base pose above wide_storage_bin (rejected: {'candidates': 3433, 'out_of_reach': 89, 'footprint': 990, 'travel_pose': 30, |
| regrasp | book_red | 0 | 10 | 100% | grasp miss 10 | T14 | 0 | edge pinch book_red: overhang only -0.026 m |
| navigate | kitchen_cabinet_6/top | 284 | 8 | 3% | carry slip 8 | T04 | 9 | carry: cup_counter_b slipped out of the hand while carrying it |
| pick | kitchen_sponge | 82 | 8 | 9% | grasp miss 8 | T08 | 2 | pick kitchen_sponge: not held (lift 0.000 m) |
| place | apple | 73 | 8 | 10% | IK / reach / base pose 8 | T11 | 3 | place_pre: no IK solution reaches apple from this base pose |
| look | desk_1/top | 150 | 8 | 5% | IK / reach / base pose 8 | T14 | 4 | face desk_1/top: turning in place would hit furniture |
| arrange |  | 2 | 8 | 80% | IK / reach / base pose 5, other 2, placement result 1 | T13 | 0 | SUBSKILL_FAILED: pick_object(object=cup): no IK for pick_lift |
| pick | oatmeal | 162 | 7 | 4% | other 7 | T07 | 5 | pick from cavity oatmeal: front approach missed by 0.163 m |
| pick | pencil | 50 | 7 | 12% | IK / reach / base pose 5, grasp miss 2 | T05 | 2 | joint move to pick_pre_far: no collision-free trajectory (MotionGenStatus.TRAJOPT_FAIL) |
| pick | pot_lid | 90 | 7 | 7% | grasp miss 7 | T17 | 8 | pick pot_lid: not held (lift 0.010 m) |
| place | rolling_pin | 72 | 6 | 8% | other 5, carry slip 1 | T03 | 0 | carry: rolling_pin slipped out of the hand while carrying it |
| place | oatmeal | 156 | 6 | 4% | other 4, IK / reach / base pose 1, placement result 1 | T04 T07 T16 | 5 | no IK for place_above |
| pick | bowl | 83 | 6 | 7% | grasp miss 6 | T13 | 5 | pick bowl: not held (lift 0.000 m) |
| expose | paperback_book | 25 | 5 | 17% | other 5 | T01 | 1 | slide to edge: centre of mass may leave the support |
| look | rolling_pin | 33 | 5 | 13% | IK / reach / base pose 3, perception / search 2 | T03 | 0 | NOT_FOUND: 'rolling_pin' is not visible at its last observed position |
| stir | handled_cooking_pot | 60 | 5 | 8% | carry slip 3, other 2 | T09 | 6 | left_carry: handled_cooking_pot slipped from the left hand |
| lift | rolling_pin | 3 | 4 | 57% | other 3, IK / reach / base pose 1 | T03 | 0 | PRECONDITION_FAILED: holding(hand=right, object=rolling_pin) is false (right holds None) |
| place | bowl | 79 | 4 | 5% | placement result 4 | T13 | 5 | place bowl: xy err 0.326 m, on support True (dining_table_2/top) |
| place | party_bowl_1 | 36 | 4 | 10% | other 3, IK / reach / base pose 1 | T20 | 0 | place party_bowl_1: container shifted 0.067 m before release |
| collect | handled_cooking_pot | 78 | 3 | 4% | other 2, IK / reach / base pose 1 | T09 | 5 | SUBSKILL_FAILED: fetch_object(object=cherry_tomato_2, receptacle=handled_cooking_pot): SUBSKILL_FAILED: place_object(object=cherry_tomato_2, |
| hover | soda_can | 26 | 3 | 10% | other 2, carry slip 1 | T10 | 2 | POSTCONDITION_FAILED: hovering_over(object=soda_can, target=trash_can) is false (xy 0.252 m, above by 0.343 m) |
| pick | rubber_duck | 86 | 3 | 3% | IK / reach / base pose 2, grasp miss 1 | T12 | 2 | pick rubber_duck: no reachable grasp from any base pose |
| place | cup | 27 | 3 | 10% | placement result 3 | T13 | 4 | place cup: xy err 0.058 m, on support False (bottom at (3.15, 7.45, 0.933)) |
| look | book_red | 57 | 3 | 5% | perception / search 3 | T14 | 2 | NOT_FOUND: 'book_red' is not visible at its last observed position |

## 2. Skill uses the v6 routes need that the v5 baseline never ran

| skill | object | families |
|---|---|---|
| approach | apple | T11/x6_cl_apple_rolls_out, T11/x6_m_apple_rolls_out_once |
| approach | bowl | T13/x6_cl_cup_slips |
| approach | cup | T13/x6_cl_cup_slips, T13/x6_m_slip_cup |
| approach | desk_1/top | T05/x6_cl_pen_unholdable |
| approach | kitchen_cabinet_6/top | T06/x6_cl_cabinet_unreachable, T06/x6_m_ik_place_cabinet |
| approach | kitchen_microwave | T07/x6_cl_microwave_door_stuck, T07/x6_m_ik_open_microwave |
| approach | mug | T04/x6_cl_cup_unusable |
| approach | trash_can | T10/x6_m_ik_drop, T10/x6_sr_drop_refused |
| close | kitchen_cabinet_4 | T04/x6_gd_cup_in_cabinets, T05/x6_gd_pen_or_pencil_cabinets, T05/x6_gd_pencil_other_cabinet, T18/x6_gd_bowl_elsewhere, T20/x6_gd_bottle_put_away |
| drop | cherry_tomato_1 | T09/x6_pp_tomato_taken_out, T09/x6_sr_collect_refused |
| drop | cherry_tomato_2 | T09/x6_gd_tomato_elsewhere, T09/x6_pp_tomato_taken_out, T09/x6_sr_collect_refused |
| drop | wooden_block_b | T17/x6_sr_hide_refused |
| hide | floor_block | T17/x6_gd_hide_both_event |
| pick | bowl_kitchen_cabinet | T13/x6_gd_two_settings, T20/x6_cl_bottle_behind_mug |
| pick | cherry_tomato_1 | T09/x6_pp_tomato_taken_out, T09/x6_sr_collect_refused |
| pick | cherry_tomato_2 | T09/x6_gd_tomato_elsewhere, T09/x6_pp_tomato_taken_out, T09/x6_sr_collect_refused |
| pick | floor_block | T02/x6_gd_tower_with_event |
| pick | mug_counter | T20/x6_cl_bottle_behind_mug |
| pick | orange_2 | T11/x6_gd_fruits_event |
| pick | pen | T05/x6_gd_pen_or_pencil_cabinets |
| pick | spoon_kitchen_cabinet | T09/x6_cl_spoon_unholdable |
| pick | spoon_target_table | T09/x6_cl_spoon_unholdable |
| pick:both | book_red | T14/x6_sr_two_hand_carry |
| pick:both | paperback_book | T01/x6_sr_two_hand_carry |
| place | bowl_kitchen_cabinet | T13/x6_gd_two_settings, T20/x6_cl_bottle_behind_mug |
| place | foam_cube | T19/x6_sr_cube_drop_refused |
| place | mug_counter | T20/x6_cl_bottle_behind_mug |
| place | orange_2 | T11/x6_gd_fruits_event |
| place | pen | T05/x6_gd_pen_or_pencil_cabinets |
| place | soda_can | T10/x6_sr_drop_refused |
| place | spoon_kitchen_cabinet | T09/x6_cl_spoon_unholdable |
| place | spoon_target_table | T09/x6_cl_spoon_unholdable |
| rotate | wooden_block_a | T02/x6_cl_block_b_unholdable |
| stack | floor_block | T02/x6_gd_tower_with_event |

## 3. Priorities

1. **Low cabinet doors** (`open` / `close` / `explore_furniture` on kitchen_cabinet_4 and _6): every v5 cabinet Hard was 0/10; v6 inspection families (T04, T05, T10, T13, T18, T20) depend on them.
2. **Grasp of tall / round / rimmed objects**: juice bottle (side pinch knocks it over), mug and bowl rim pinches (T13, T20), cup carry.
3. **Book carry**: one-handed slip of paperback / red book (T01, T14); v6 adds the two-handed carry (`pick(hands=both)` then `navigate`) as the strategy-replacement route - it needs to work physically.
4. **Wipe reach** (T08) and **pick from inside the microwave cavity** (T10 v5 Hards 0/10; v6 `x6_gd_can_put_away__in_microwave`, `x6_gd_bowl_put_away__in_microwave`).
5. **Search of small objects** on the dining table (smoke run: `search wooden_block_b` did not see the block on the dining table in T06) and of the pot lid (v5: `search pot_lid` 0/10 in T17).
6. **Bimanual flat pick** (`pick(hands=both)`, zeno_skills/policies/bimanual.py): it needs the book's long side (half length >= 9 cm) along an overhanging edge; the T01 / T14 books overhang with the short side (yaw 90), so the two-handed carry of `x6_sr_two_hand_carry` stops there (smoke runs v6_smoke3/4, after the injected slips and the slip restore worked). Either accept short-edge overhangs or provide a re-orientation the route can call.
7. **Apple pick from the bookcase top** after it rolled out of the basket (T11 `x6_cl_apple_rolls_out`, smoke: `not held`).
8. New primitive uses: cherry-tomato `pick` + `drop` into the pot (T09 split), `place` into the trash can (T10) and of the foam cube into the bin (T19), `drop` + `cover` instead of `hide` (T17), three-block `stack` (T02).

