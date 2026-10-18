# ZenoBench planning benchmark (observation-limited)

A small benchmark for an upper-level planner (a VLM) on top of the existing
70 SkillNodes.  Same low-level skills, same observation limits for every
planner; the question is whether the planner picks an effective recovery or
alternative from the execution feedback.

<!-- results:start -->
| Task | Route (kind) | Pass | Fail | Incomplete / violated |
|---|---|---|---|---|
| P01_body_and_gesture | nominal (nominal) | 1 | 0 | 0 |
| P02_perception | nominal (nominal) | 1 | 0 | 0 |
| P03_rolling_pin | nominal (nominal) | 1 | 0 | 0 |
| P04_bottle | nominal (nominal) | 0 | 1 | 0 |
| P05_flip_book | nominal (nominal) | 1 | 0 | 0 |
| P06_two_hands | nominal (nominal) | 0 | 1 | 0 |
| P07_present_and_brace | nominal (nominal) | 0 | 1 | 0 |
| P08_block_alignment | nominal (nominal) | 1 | 0 | 0 |
| P09_sweep_blocks | nominal (nominal) | 0 | 1 | 0 |
| P11_stove_cycle | nominal (nominal) | 1 | 0 | 0 |
| P12_cabinet | nominal (nominal) | 1 | 0 | 0 |
| P13_microwave_buttons | nominal (nominal) | 1 | 0 | 0 |
| P14_restore_swap | nominal (nominal) | 0 | 1 | 0 |
| P15_arrange_and_sort | nominal (nominal) | 1 | 0 | 0 |
| P16_empty_mug | nominal (nominal) | 0 | 1 | 0 |
| P17_pour | nominal (nominal) | 0 | 1 | 0 |
| P18_floor_pick | nominal (nominal) | 1 | 0 | 0 |
| P19_spoon_dip | nominal (nominal) | 1 | 0 | 0 |
| P20_hide_block | nominal (nominal) | 1 | 0 | 0 |
| P21_clear_cabinet | nominal (nominal) | 1 | 0 | 0 |
| P22_chill_oatmeal | nominal (nominal) | 1 | 0 | 0 |
| T01_book_to_dining_table | fallback_expose (fallback) | 2 | 0 | 0 |
| T01_book_to_dining_table | hard_search_expose (fallback) | 1 | 1 | 0 |
| T01_book_to_dining_table | nominal (nominal) | 2 | 0 | 0 |
| T02_stack_blocks | fallback_push (fallback) | 2 | 0 | 0 |
| T02_stack_blocks | fallback_separate (fallback) | 1 | 1 | 0 |
| T02_stack_blocks | hard_search_separate (fallback) | 1 | 1 | 0 |
| T02_stack_blocks | nominal (nominal) | 2 | 0 | 0 |
| T03_utensils_one_container | alternative_large_container (alternative) | 2 | 0 | 0 |
| T03_utensils_one_container | hard_search_alt_container (alternative) | 2 | 0 | 0 |
| T03_utensils_one_container | nominal (nominal) | 4 | 0 | 0 |
| T04_cup_or_mug_to_cabinet | alternative_mug (alternative) | 2 | 0 | 0 |
| T04_cup_or_mug_to_cabinet | hard_count_search_mug (alternative) | 2 | 0 | 0 |
| T04_cup_or_mug_to_cabinet | nominal (nominal) | 2 | 0 | 0 |
| T05_pen_or_pencil_to_desk | alternative_pencil (alternative) | 2 | 0 | 0 |
| T05_pen_or_pencil_to_desk | hard_search_pencil (alternative) | 2 | 0 | 0 |
| T06_block_destination_occupied | alternative_tv_stand (alternative) | 2 | 0 | 0 |
| T06_block_destination_occupied | hard_search_alt_support (alternative) | 2 | 0 | 0 |
| T06_block_destination_occupied | nominal (nominal) | 2 | 0 | 0 |
| T07_heat_oatmeal | alternative_stove (alternative) | 2 | 0 | 0 |
| T07_heat_oatmeal | hard_search_stove (alternative) | 2 | 0 | 0 |
| T07_heat_oatmeal | nominal (nominal) | 2 | 0 | 0 |
| T08_wipe_island | hard_search_approach (fallback) | 2 | 0 | 0 |
| T08_wipe_island | nominal (nominal) | 2 | 0 | 0 |
| T08_wipe_island | nominal_from_tv_stand (nominal) | 2 | 0 | 0 |
| T09_tomato_soup | fallback_uncover (fallback) | 2 | 0 | 0 |
| T09_tomato_soup | hard_uncover_search_spoon (fallback) | 2 | 0 | 0 |
| T09_tomato_soup | nominal (nominal) | 2 | 0 | 0 |
| T10_trash_the_can | hard_explore_search (fallback) | 2 | 0 | 0 |
| T10_trash_the_can | nominal (nominal) | 2 | 0 | 0 |
| T10_trash_the_can | search_first (fallback) | 2 | 0 | 0 |

SkillNode coverage in these runs: **65/70** (details: RESULTS.md).
<!-- results:end -->

## What the planner gets

`benchmark/session.py: LimitedSession` is the only entry for planners.

| Input | Source |
|---|---|
| first-person RGB image | Malo head camera (`make_rig(first_person=True)`), saved per call |
| visible objects | GT-assisted detector: frustum, 5 m range, static line of sight **and** dynamic occlusion (closed doors/drawers, lids, container walls, other objects) |
| observation cache | last seen pose / support / container / tick of every object ever seen |
| known static places | rooms, furniture, supports, doors, appliances, buttons of the floor plan |
| execution feedback | action, success, error code + message, measured pre/postconditions, outputs; unobserved names masked as `<unobserved>`; no bound GT nouns, no relation-graph recovery hints |

Permission rules (`benchmark/observation.py: GatedRunner`), applied to every
call - top level and every nested Contract inside multi-object skills:

* an object argument must be observed (or held); a hidden object and a name
  that does not exist get the **same** refusal and nothing moves;
* contact skills need the **manipulated** object (pick, push, stir, the lid
  of cover, ...) in the **current** view or in the hand - pick never tracks an
  object that left the view; a destination (place on / into, stack on) only
  needs to be observed, its pose comes from the observation cache;
* navigate / approach to an object drive to its **cached** pose (a moved,
  unseen object's GT pose is never used); look-type skills at a stale object
  glance at the cached pose first;
* support/container lists inside clear / empty contain observed objects only;
* search takes any name; for a non-existent name it runs the same static sweep
  and returns the same failure as for a hidden object;
* explore picks viewpoints from the static layout and computes coverage over
  static supports only (`rig.static_explore`).

Navigation keeps the GT map and collision checking for safe low-level planning.

No automatic recovery in this interface: no nested repair (`auto_repair=False`),
no slide-to-edge inside pick (`skip_steps`), no pick -> push fallback, no
door "retry from another park" (`rig.auto_recovery=False`).  The feasibility
estimates `grasp_clearance` and `edge_overhang` are advisory (recorded, the
action is attempted), so an infeasible pick fails *physically*.  The original
behaviour stays the default of `SkillContractRunner`; `tools/verify_skills.py`
(GT runner) is the trusted physical acceptance entry and is unchanged.

## Tasks

`benchmark/define_tasks.py` -> `benchmark/tasks.json`.  One fixed base scene
per task + a local overlay (remove objects, re-place existing objects on their
supports; the house layout never changes).  The seed picks a condition
variant (does the fallback / alternative condition hold?) and removes a random
subset of distractors.  Instructions state the goal only - no object
positions, no order, no recovery.

Each task has three difficulty tiers (`--difficulty easy|medium|hard`, or an
explicit `--variant`): **easy** - no failure / alternative condition holds;
**medium** - one condition (the pick fails, the destination is full, the
preferred object or appliance is not available, the object is not in view);
**hard** - a condition combined with a second one (the robot starts in another
room or facing away, the object or tool is out of view).  The instruction is
the same in all tiers; only the scene tells which recovery is needed.

| Task | Instruction (short) | easy | medium (condition -> declared route) | hard (conditions -> declared route) |
|---|---|---|---|---|
| T01 | Bring the paperback from the kitchen island to the dining table. | book overhangs the island edge | no overhang -> **fallback** Pick fails -> Expose -> Pick | starts in the dining room + no overhang -> Search, Pick fails -> Expose -> Pick |
| T02 | Stack one wooden block on the other. | blocks free | block B boxed in by a bowl and the rolling pin -> **fallback** Pick fails -> Separate -> Pick; **fallback** Pick fails -> Push -> Pick | starts at the wall cabinet facing away + boxed in -> Search, Pick fails -> Push -> Pick |
| T03 | Put the rolling pin and the spoon away together in one container. | only the storage bin | a mug as well -> **alternative** the pin does not fit the mug -> lift, retreat -> storage bin | starts facing away + mug -> Search, then the same alternative |
| T04 | Set out a cup on the low wall cabinet; a mug if there is no cup. | cup on the island | no cup -> **alternative** Count 0, Search fails -> mug | no cup + mug on the TV stand -> Count, Search fails -> Search mug -> mug |
| T05 | Bring a pen to the study desk; a pencil if there is no pen. | (pen route is diagnostic: the pen slips 4/4) | no pen -> **alternative** navigate to the pen refused -> pencil | no pen + pencil in the dining room -> Search pencil -> pencil |
| T06 | Put a toy block on display on the wall cabinet or the TV stand. | cabinet top free | top full -> **alternative** Place fails -> TV stand | top full + block in the dining room -> Search, Place fails -> TV stand |
| T07 | Warm the oatmeal to >= 40 C; stove off, microwave closed afterwards. | microwave works | microwave does not heat -> **alternative** Heat fails -> Stop, take out -> stove | broken + oatmeal on the wall cabinet -> Search, then the same alternative |
| T08 | Wipe the kitchen island with the sponge, leave the sponge there. | sponge on the island | sponge on the TV stand -> fetch it, Approach the island, Wipe | starts in the dining room + sponge away -> Search, Approach, Wipe |
| T09 | Tomato soup: tomatoes into the pot, stir, cover, heat to 60 C, stove off. | lid off | lid on -> **fallback** Collect refused -> Uncover -> Collect | lid on + spoon on the TV stand -> Uncover, Search spoon |
| T10 | Throw the empty soda can into the trash can. | can on the island | can in the dining room -> **fallback** Pick refused (not observed) -> Search | starts in the dining room + can on the TV stand -> Pick refused -> Search -> Explore for the trash can |

Seeds also remove a random subset of each task's distractors, so the views
differ between episodes of the same variant.  Routes that were tried and
failed physically are kept as `diagnostics` in `tasks.json` (T05 pen, T06
Clear-then-place, T08's former fridge task) and are not part of the formal list.

Fallback = a real failure, then an auxiliary skill repairs the state and the
same action is retried.  Alternative = another legal object, skill or
destination reaches the same goal.  They are recorded separately (`kind`).

P01-P18 are single-scene probes for SkillNodes that do not fit the ten tasks
without being inserted mechanically (gestures, posture, perception, contact
skills on the rolling pin / bottle / book, two-hand skills, wipe, stove and
microwave buttons, cabinet, multi-object skills).  They use the same
interface; the probe runner issues an explicit `look(object)` when a contact
skill is refused with NOT_IN_VIEW (recorded as its own call).

## Running

```bash
export ISAACLAB_PYTHON=~/miniforge3/envs/isaaclab/bin/python
python benchmark/define_tasks.py                 # tasks.json
python benchmark/check_layouts.py                # static overlay check (no simulator)
python -m pytest benchmark/tests -q              # permission tests (stub rig)
$ISAACLAB_PYTHON benchmark/tests/sim_permissions.py          # permission tests in Isaac Sim

# one episode (scripted route = physical feasibility proof, not a planner result)
$ISAACLAB_PYTHON benchmark/run_episode.py --task T01_book_to_dining_table --seed 0 --route fallback_expose
# an episode by tier: the seed picks among the tier's variants
$ISAACLAB_PYTHON benchmark/run_episode.py --task T07_heat_oatmeal --seed 5 --difficulty hard --route hard_search_stove
# planner baselines
$ISAACLAB_PYTHON benchmark/run_episode.py --task T07_heat_oatmeal --seed 2 --planner fixed --variant microwave_broken
$ISAACLAB_PYTHON benchmark/run_episode.py --task T07_heat_oatmeal --seed 2 --planner retry --variant microwave_broken
$ISAACLAB_PYTHON benchmark/run_episode.py --task T07_heat_oatmeal --seed 3 --planner oracle --variant microwave_broken
# a closed-loop planner (the VLM goes here; see benchmark/planners.py)
$ISAACLAB_PYTHON benchmark/run_episode.py --task T07_heat_oatmeal --planner recovery --policy mypkg.planner:MyPlanner

# acceptance rounds (at most two Isaac processes)
python benchmark/make_batches.py
python benchmark/run_episode.py --batch benchmark/batches/accept.json --jobs 2 --out benchmark/runs/accept
python benchmark/report.py --runs benchmark/runs/accept
```

Every episode directory keeps `config.json` (task, variant, seed, overlay,
removed distractors, git commit + diff hash), `annotation.json` (the episode
scene), `calls.jsonl` (every call, feedback, state summary), `images/`
(first-person image after every top-level call) and `result.json` (goal
atoms, dropped objects, observation cache, gate log, last 300 events).

Task Success = every GT goal atom holds at the end, a scripted route ran to its last step, no watched object ended on
the floor, and (scripted routes) every step marked `"expect": "fail"` really
failed.  Skill Success is per call (`feedback.success`).  A run that crashed
or timed out is *incomplete*, never a physical failure.

Step roles in a route: `failure` (the call expected to fail), `recovery` / `alternative` / `retry_after_recovery`, and `unwind` (only undoes the failed call's side effect, e.g. lift the rolling pin out of the mug and back away).  The GT oracle skips `expect: fail` and `unwind` steps.

## Changes to existing code

Behind flags (defaults unchanged) except three local skill fixes that change the default behaviour: the
upright waist of the edge pinch at table height and the open-hand clear after a failed top pinch
(`skills.py`), and the closed-loop `lift` (`policies/navigation.py`).  Regression of the skill library's own
scenarios with these defaults (`tools/verify_skills.py --all`): in progress, results to follow.

| File | Change |
|---|---|
| `zeno_skills/perception.py` | `dynamic_occluder()`; used by `project_to_head_camera` only when `rig.occlusion` |
| `zeno_skills/skill_runtime.py` | `SkillContractRunner(auto_repair=True, advisory=(), skip_steps=None)` |
| `zeno_skills/skills.py` | `rig.auto_recovery` (default True): pick -> push fallback, slide-to-edge inside `pick_flat`, door retry from another park; `_edge_pinch(attempt=)`; edge pinch keeps the waist upright at table height (as `_pick_pinch` does), fixing a chest-into-counter stall seen 4/4 times; a failed top pinch ends with the hand open and 8 cm higher (fingers closed beside a crowding bowl stopped at 5 mm and the next push could not make its fist, 3/4) |
| `zeno_skills/policies/navigation.py` | `lift` (carry_height_adjust) repeats the vertical move on the measured object bottom, up to 3 times while the object keeps rising: a rolling pin caught in a mug after a failed place lagged the hand by 4-5 cm and one move fell short (4/4); the verifier (bottom >= target - 2 cm) is unchanged |
| `zeno_skills/policies/perceive.py` | `rig.static_explore`: explore coverage over static supports only; `rig.observer` hook in `record_view` |
