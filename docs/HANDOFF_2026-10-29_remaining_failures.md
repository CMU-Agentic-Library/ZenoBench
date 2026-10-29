# Handoff 2026-10-29: the six routes still failing

Scope for the next session: fix the six episodes below. Everything else here is
context for that work.

## Where the benchmark stands

`benchmark/batches/v3_sticky_gt_one_variant.json` runs all 41 v3 tasks with one
nominal variation each (seed 10, `--planner scripted`, `--profile sticky/gt`).

| run | code | result |
|---|---|---|
| `benchmark/runs/v3_sticky_gt_1029` | 914d2a2 | 30/41 (7 of the failures were CUDA OOM from `--jobs 2`) |
| `benchmark/runs/v3_sticky_gt_1029b` | f25ed6b | 34/41, peak GPU 19.5 GB, no OOM, 42 min at `--jobs 2` |
| not yet run | f4907e2 | expected 35/41 (T20 fixed after 1029b) |

**Run a full batch before anything else**: f4907e2 changed the place pose of
every object, and only six place-heavy routes have been checked against it.

```bash
docker/run.sh '$ISAACLAB_PYTHON benchmark/run_episode.py \
  --batch benchmark/batches/v3_sticky_gt_one_variant.json --jobs 2 \
  --out benchmark/runs/<new>'
```

`--jobs 2` is safe at the current planner seeds (peak 19.5 GB of 24 GB,
measured). If `TRAJOPT_SEEDS` / `GRAPH_SEEDS` go back up, re-measure first.

## Fixed today (do not re-investigate)

* `7f8e131` edge pinch judged the lift by the object's bbox bottom, which a book
  pivoting on the desk edge barely moves - **T14**.
* `f25ed6b` `find_park` validated a park's unfold without the tilt constraint the
  execution plans with, so it picked parks whose constrained plan has no
  solution - **T11, T04, P15**.
* `f4907e2` `place()` replayed the grasp relation, putting down an object that
  rotated in the fingers at that angle - **T20**.

Two attributions that turned out to be **wrong**, recorded so they are not
repeated: T14 was not a regression from thinning book_red (at 7 cm the fingers
closed to 0.000 m - they never caught it), and T11 was not caused by 99a0a0d
(reverting the held-object spheres leaves it failing identically).

## The six remaining

Evidence is from `benchmark/runs/v3_sticky_gt_1029b` unless noted.

### P07_present_and_brace - mug ends at 77.8 deg
All 11 calls succeed; only `upright(mug)` fails. The route is
`brace_object(mug)` then `release_object(mug, hand=left)`, not `place()`, so
f4907e2's levelling does not cover it. `rest_R` (zeno_skills/sticky.py:98) is the
levelling helper to reuse.

### T20-style check first: is it tilted before the release?
The probe that settled T20 is worth repeating for any "ends up tilted" failure:
log `quat_R(rig.obj_pose(name)[1])[2, 2]` before and after the release. Tilt
present before the release means the hand put it down that way; tilt appearing
after means it toppled.

### P16_empty_mug - `pick cherry_tomato_1: not held (lift 0.001 m)`
`empty_container(mug -> handled_cooking_pot)` fails on the nested pick of a
cherry tomato. Reproduces identically across runs.

### P17_pour - `pour: 0/3 items reached handled_cooking_pot`
In 1029b `hover` passes and `pour` is the failing call; the older run's "no base
pose above handled_cooking_pot" is gone.

### P04_bottle - `upright_object(juice_bottle)` NO_PATH
"no policy path matches the bound nouns and robot state" with the bottle at
91.1 deg: there is no route for righting a bottle that is lying down.

### P05_flip_book - `flipped(paperback_book)` false (z dot -0.26)
Postcondition failure after `flip_object`. Flipped to passing once under the
halved planner seeds (31308ac), so it is marginal rather than deterministic.

### P14_restore_swap - `face kitchen_island/top: turning in place would hit furniture`
`look_target` refuses to turn. The route needs the robot to face the island
from where it stands.

## Triage 2026-10-29 (second pass): route bug vs grasp annotation vs capability

The five non-P07 failures were each checked against two questions - is the
oracle's step sequence wrong, and is the object's GT grasp annotation wrong.
Only P14 answered yes to either.

### P14 - route bug, fixed

`restore` parks the base wherever its own place search lands (7.551, 2.298 -
behind the island) and the route then calls `look(kitchen_island/top)` from
there: a 105 deg turn in place, which the clearance check refuses. `look` has no
path that drives; every other route in the benchmark navigates before it looks
(`P14` was the only `look` after a composite skill that relocates the base).

Fixed in `benchmark/define_tasks.py` by inserting `navigate(kitchen_island/top)`
before the second look; `benchmark/tasks.json` and `benchmark/v3/tasks.json`
regenerated. Verified in `benchmark/runs/p14_navigate_fix`: the look passes and
the route reaches `swap`, two calls further than before.

**P14 still fails**, now for two reasons that are neither a route bug nor a
grasp annotation, so they were left alone:

* `swap` dies on `pick_object(soda_can)`: `MotionGenStatus.GRAPH_FAIL` at
  `pick_pre` ("Start or End state in collision") from park (8.05, 1.162, 165).
* Even a clean `swap` cannot satisfy the goal. `positions_swapped` compares to
  the **episode start** (6 cm tolerance), but `restore` only guarantees
  `at_initial_place`, which checks the *support*, not the spot: contract_061
  calls `policy_015` with no hint, so the block came back 0.49 m from where it
  started, and `swap` then copies that drifted xy onto the can. A fix would be
  an `initial_xy` noun attribute (the episode's `annotation.json` already
  carries the exact start position) passed as `hint` in contract_061, plus
  tightening `at_initial_place` to check xy. Not done - it changes `restore`
  everywhere.

### P04 - contract coverage gap, not the annotation

`contract_044:upright` has exactly one path, gated on
`object.grasp_types contains top_pinch`, and `juice_bottle` is annotated
`side_pinch` only. That annotation is right: `contract_043:tip` describes itself
as laying down "a carton or bottle that is too tall to top-pinch", and T20 picks
the bottle through the pick contract's `annotation_dispatch` path every run. So
`tip` and `upright` are declared alternatives of each other while `upright`
cannot undo `tip` on the one object class `tip` exists for.

Candidate fix (not applied): a second path in contract_044 gated on `side_pinch`
with `policy_061` (annotation dispatch) in place of `policy_010`, then the same
`policy_054` / `policy_015`. `UprightObjectPolicy` itself is grasp-agnostic - it
only wants a right-only grasp - so this is a contract edit plus a sim check.

### P16 - the hand cannot enter the mug

The scene's mug is 9.3 cm across and 12 cm tall (rim at z 0.98) with the three
tomatoes resting on its floor at z 0.884. `empty`'s first path
(`pick_each_inside`, `when: []`, so it always wins) reaches in with the top
pinch. The arm never arrives: `pick_pre` lands with `tcp_err 0.081 m`,
`pick_grasp` with `tcp_err 0.128 m` and `q_err 0.57` on one joint - the hand is
held off by contact - and the fingers then close on nothing (0.000 m).

The annotation is not the problem: T09_tomato_soup picks the same tomatoes with
the same `top_pinch` grasp and passes, and its scene definition deliberately
*moves them out of the mug* onto the island first. The alternative path
`pour_out` would not help either - that is exactly P17.

### P17 - the wrist cannot tilt the mug far enough

`pour` plans a 40 deg tilt, walks it up, and stops: `pour_tilt_limit deg 80,
reason "no IK for pour_tilt"`. Measured cup tilt topped out at 55.9 deg, and the
three tomatoes never left the mug. contract_059 already records the limit:
"Pouring loose solids needs the cup past ~90 deg, which the arm cannot reach
over the stove". Route and grasp are both fine; this is reach.

### P05 - the flip arc runs out of IK

`flip_arc_limit deg 100.0, reason "no IK for flip_arc"`, then
`flip_withdraw_short` and twice `flip_finish_push_short`, both "no IK". The book
is released at ~90 deg and settles on edge (`up_z -0.257`). Route and grasp are
both fine; this is reach, and it is the marginal one - it passed once already.

## Useful machinery

* GPU memory per call: `/data/zenobench/scratch/mem_probe/instrumentation.patch`
  (`git apply`) prints torch reserved/allocated after every contract call.
* Tilt probe: see the snippet above; `place_level` / `place_level_dropped` events
  already record which hand-object relation each place used.
* Videos: add `"video": true` to the batch entries; `run.mp4` lands in each
  episode directory. Extract frames with ffmpeg inside the container, writing to
  a mounted path (`/data/zenobench/...`, not the container's `/tmp`).
