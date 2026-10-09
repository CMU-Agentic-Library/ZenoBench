# Known limitations (verification round 30)

Round 30 ran all 35 scenarios on one code version. 65 of the 70 verbs and 97 of the 120 policy paths passed physically in Isaac Sim ([STATUS](../skill_library/verification/STATUS.md)).

The verbs below were not verified physically. Each one still has its GT contract, its pre- and postconditions and its verifier. A failed run returns a precise error and a `replan_request` to the caller.

| Verb | Scenario | What happens | Cause |
|---|---|---|---|
| `pour` | `k_soup_stove` | The cup tilts, but the tomatoes stay inside. | **Reach.** Loose items leave a near-vertical cup only past ~90 deg of tilt. From a rim pinch, no base pose lets the arm tilt a cup past ~57 deg over the stove (offline park search, and runs). **Grip.** A sideways tilt turns the cup about the pinch's closing axis, and the cup swings in the pads. The low lip then drifts next to the gripper, and the tomatoes caught on the hand (video, round 25). A shallow bowl did not help. |
| `empty`, `hide` | `k_empty_hide` | `empty` now takes the items out one by one (`pick_each_inside`). The top pinch of a 2.8 cm cherry tomato inside the 9 cm mug did not hold (`lift 0.000 m`; same in the `empty_mug` rollout). `hide` follows `empty` in this scenario, so it was not reached; the `hide_block` rollout runs `hide` end to end and passes. | The fingers enter the mug's narrow opening beside a ~3 cm item. |
| `chill` | `k_fridge_chill` | The fridge is opened and the can is carried in. The can ends on the shelf, but lying on its side (tilt 88.6 deg, `xy err 0.119 m`). | No straight entry from the carry pose. The joint-space entry beside the open door brushes the door frame and knocks the can over. The pre-shape fallback (back out, shape the arm, drive in) found no collision-free joint path. |
| `sort` | `k_arrange_sort` | `arrange` passes. `sort` fails when picking block B (`not held`), because the block was knocked over before the grasp. | `arrange` left the block 3.4 cm from the island edge, and driving along the counter knocked it. The planner now keeps spots 4 cm in from counter edges; the rerun with this fix still failed at `fetch(wooden_block_b)`. |

The two-handed `pick` path (`r_bimanual_box`) also does not pass: the bin is pushed 3–5 cm while both hands slide onto its grip bars. `pick` itself passes on its other paths.

## Whole-task rollouts

16 of the 35 planner-generated task subgraphs ran end to end with their task goal holding on GT state (README, section "Whole-task rollouts"). The failures are physical steps inside long chains:

- An object slipped from the hand while carrying it (`collect_fruits`, `desk_prep`).
- The fridge door did not move from the park used in these tasks (`heat_breakfast`, `heat_breakfast_combo`), although `open` passes from the park in `k_fridge_chill`.
- No reachable spot or joint path near a container or the microwave (`recycle_and_store`, `heat_can_in_microwave`, `sort_items`, `wipe_island`).
- A grasp did not hold (`organize_utility_items`, `swap_blocks`, `clear_tv_stand`, `empty_mug`).
- A placement landed off target (`stack_blocks`, `chill_drink`, `cook_tomato_soup`).

The run was not on one frozen code version. During the run, two fixes went in, and scenarios started afterwards used them:

- Plans now navigate to the object itself before `pick`, not to its support. The earlier plan left a book 1.34 m away on a large desk.
- The tight-park margin went from 0.26 to 0.15 m. `shelve_books` failed with "no base path" before this change and was not rerun.

A third fix corrected the rollout goal check, which lacked the start-state snapshot (`KeyError: 'before'`). `flip_book` and `swap_blocks` were rerun with it, and both failed on physical steps.

## Lessons recorded in the code

These are fixes that made other verbs pass. Each is commented where it lives.

| Problem | Fix |
|---|---|
| The left gripper's left finger had no pad collider. | Pad colliders on all four fingers (`zeno_skills/physics.py`). |
| A base path ignored furniture near its start and goal. | Near a tight start or goal park the base centre keeps 0.15 m from every box (`zeno_skills/planner.py`); 0.26 m blocked parks in narrow aisles. |
| Turning away from an open door brushed it closed. | The robot reverses out first (`skills.navigate`). |
| A held object rode a large IK-branch jump. | Joint-distance checks on vertical moves and staging moves. |
| A lying bottle had no stage pose for the wrist turn. | The upright staging search also tries hand yaws, and the bottle is set down straight from the turn. |
| A compact travel tuck was tried. | It put picks on other IK branches and was reverted (`COMPACT_TUCK` is kept for reference). |
