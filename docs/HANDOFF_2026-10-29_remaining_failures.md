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

### P16_empty_mug - `pick cherry_tomato_1: not held (lift 0.000 m)`
`empty_container(mug -> handled_cooking_pot)` fails on the nested pick of a
cherry tomato. Reproduces identically across runs.

### P17_pour - `hover mug: no base pose above handled_cooking_pot`
`find_park` rejects all 3433 candidates: footprint 1479, out_of_reach 348,
ik 150. A park-search problem, same family as f25ed6b but a different gate.

### P04_bottle - `upright_object(juice_bottle)` NO_PATH
"no policy path matches the bound nouns and robot state" with the bottle at
91.1 deg: there is no route for righting a bottle that is lying down.

### P05_flip_book - `flipped(paperback_book)` false (z dot -0.26)
Postcondition failure after `flip_object`. Flipped to passing once under the
halved planner seeds (31308ac), so it is marginal rather than deterministic.

### P14_restore_swap - `face kitchen_island/top: turning in place would hit furniture`
`look_target` refuses to turn. The route needs the robot to face the island
from where it stands.

## Useful machinery

* GPU memory per call: `/data/zenobench/scratch/mem_probe/instrumentation.patch`
  (`git apply`) prints torch reserved/allocated after every contract call.
* Tilt probe: see the snippet above; `place_level` / `place_level_dropped` events
  already record which hand-object relation each place used.
* Videos: add `"video": true` to the batch entries; `run.mp4` lands in each
  episode directory. Extract frames with ffmpeg inside the container, writing to
  a mounted path (`/data/zenobench/...`, not the container's `/tmp`).
