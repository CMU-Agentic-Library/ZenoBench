# ZenoBench v6: Action-Level and Task-Level suite (design stage)

v6 is the task-design layer on top of v5. It reads `benchmark/v5/tasks.json` and never writes it: every v5
variant, oracle route and episode hash is unchanged (FREEZE.json, 1,800 hashes checked by `validate_v6.py` and
the tests). v6 adds 69 new variants on 17 of the 20 base tasks and splits all 249 variants into two tracks.

| | |
|---|---|
| base tasks | 20 (one house, 10 rooms, existing assets only) |
| variants | 249 = 180 v5 + 69 new; each runs seeds 10-19 (2,490 episodes) |
| tracks | Action-Level 103 variants, Task-Level 163, controls 38 (`TRACKS.md`) |
| static checks | 2,490 / 2,490 episodes |
| physics | 51 variants PHYSICS_VALIDATED (v5 grid, 10/10); the rest STATIC_VALIDATED (`PHYSICS_TODO.md`) |

## Definitions

An episode is **task + variant + seed**.

* **Variant** = the task design: which failures and events are injected, which scene conditions hold (an
  absent object and its substitute, a lid on the pot, a book with something on it, a taken destination, an item
  in another room, the start room), which goal. Two variants differ in what the planner has to do.
  (`v6_variants[vid]` in `tasks.json`.)
* **Seed** (10-19, ten per variant) = the layout of that design:
  - where the objects stand and where the robot starts (a small seeded shift of the task objects on their
    supports and of the start pose, `vary`), and which removable distractors are left out;
  - for a variant with several **layouts** (48 variants), which one: the same design with the resource,
    substitute or item in another place, or an event taking it elsewhere (e.g. the cup in cabinet 4 or in
    cabinet 6). The seeds are spread over the layouts by a fixed-RNG, balanced manifest
    (`v6_variants[vid]["seeds"]`); each layout has its own configuration and oracle route (`variants[<layout>]`).
* **Control**: the variant this one differs from in one factor (`v6_variants[vid]["control"]`; for a v5
  variant the task's first nominal one).
* **Status**: PHYSICS_VALIDATED (every seed passed in simulation with the current hash and route),
  STATIC_VALIDATED (all static checks pass), DESIGN_COMPLETE (specified, static not passing).

Earlier multi-case families whose cases differed in the design, not only in place (which object lies on the
book, which failure mechanism, which subgoal the event undoes, how many places the instruction names), are
one variant per case (`SPLIT` in `define_tasks_v6.py`).

## Two tracks: Action-Level and Task-Level (`tracks.py`, `TRACKS.md`)

The split reads only a variant's configuration (`tracks.content`):

| track | content | runs with | variants | episodes |
|---|---|---|---|---|
| **Action-Level** | a transient action failure (grasp miss, slip, placement miss, IK refusal: a retry or re-approach fixes it), or a blocked action fixed by a local repair of the same object, then the same call (`LOCAL_CONDITIONS`: a flat book pushed over the edge, a crowded block pulled apart) | scripted recovery route, physical skills, `benchmark` profile (no GT); the skill layer's score | 103 | 1,030 |
| **Task-Level** | anything that makes the plan itself change: a task-level failure, a dynamic event, an action failure no retry fixes, any other scene condition (search, absent object, lid on, closed door, capacity ...), a changed goal | any task planner on GT skills (`sticky_snap/gt`); oracle route replayed for validation | 163 | 1,630 |
| controls | neither: the nominal plan works | both tracks | 38 | |

Action-Level subcategories name the failure mechanism: AL-IK 57, AL-GRASP 31, AL-SLIP 5, AL-PLACE 1,
AL-COMPOUND 9. Task-Level variants are listed per task, with timing (40 have a dynamic event, the rest act
on the initial scene).

A variant with both kinds of content (65) is in both: the full variant in Action-Level, its **task
projection** (`<vid>__tl`: the transient action failures removed, and in the route each call they failed with
its local repair up to the successful retry) in Task-Level. 10 projections equal another variant's
configuration and are merged into it. A repair that changes another object's or a container's state (move an
obstacle, take a lid off, open a door) is Task-Level.

Status: the split is static (`validate_v6.py` checks every variant is in the tracks its content calls for and
every projection on its seeds). Evaluation metrics are not defined yet.

## New failure-injection features (failure_injection/)

Persistent grasp / slip / placement / IK failures (a retry cannot help), `until_moved` (an IK / grasp refusal that
ends when a named obstruction is moved), one-handed slips (a two-handed carry is spared), IK refusals pinned to a
destination (the substitute stays reachable), and a slip that falls back onto the support it was picked from.

## Commands

```bash
python benchmark/v6/define_tasks_v6.py     # tasks.json (catalog + tracks); --check: up to date?
python benchmark/v6/validate_v6.py         # STATIC.json: per-episode static checks, v5 hashes, manifests
python benchmark/v6/report_v6.py           # variant_cards.json, ROUTES.md, SKILL_FIX_LIST.md, PHYSICS_TODO.md
python benchmark/v6/tracks.py              # TRACKS.md, batches/track_task_scripted.json, track_action_scripted.json
python -m pytest -q benchmark/v6/tests failure_injection
$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json \
    --batch benchmark/v6/batches/physics_v6_new.json --jobs 2 --out benchmark/runs/v6_physics --no-eval
```

## Files

* `TRACKS.md` - the two tracks, counts per task, every variant's track.
* `variant_cards.json` - per concrete variant: instruction, initial conditions, failure triggers, goal, tracks,
  control, oracle route, challenge / rationale, success criteria.
* `ROUTES.md` - every oracle reference route, by track. `SKILL_FIX_LIST.md` - for the skill owner.
  `PHYSICS_TODO.md` + `batches/` - what still needs simulation.
