# ZenoBench v6: task design in four categories (design stage)

v6 is the task-design layer on top of v5. It reads `benchmark/v5/tasks.json` and never writes it. v6 adds new
variants on 17 of the 20 base tasks, removes every injected action failure, and
puts each variant in one of four categories.

| | |
|---|---|
| base tasks | 20 (one house, 10 rooms, existing assets only) |
| variants | 128; each runs seeds 10-19 (1,280 episodes) |
| categories | control 20 (one per task), Action-Level 28, Task-Level 65, Action + Task 15 (`TRACKS.md`) |
| static checks | 1,280 / 1,280 episodes |
| physics | 25 variants PHYSICS_VALIDATED (v5 grid, 10/10, unchanged configuration); the rest STATIC_VALIDATED |

## Definitions

An episode is **task + variant + seed**.

* **Variant** = the task design: which dynamic events happen, which scene conditions hold (an
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

## Four categories (`tracks.py`, `TRACKS.md`)

Each variant contains the fallback its category is about; the category reads only the configuration
(`tracks.content`).

| category | the variant needs | variants | episodes |
|---|---|---|---|
| **Control** | nothing: the nominal plan works (the reference for the others) | 20 | 200 |
| **Action-Level** | a short fallback at the work spot, a few skills combined, then the plan goes on: expose a flat book before the pick, separate a crowded block, take the lid off, clear what lies on the target or open the door first, move clutter off the work strip, clear a full destination, move the base in from the edge (`LOCAL_CONDITIONS`, `local_failure`); also a dynamic event put right at the work spot: a book pushed back, a tomato taken out of the pot, a door opened again (`event_is_local`) | 28 | 280 |
| **Task-Level** | a longer-horizon change of plan: a substitute, a search in another place or room, a capacity split, another destination / appliance / cookware, an object an event takes elsewhere | 65 | 650 |
| **Action + Task** | both | 15 | 150 |

**No injected action failures, anywhere.** No IK refusal, grasp miss, slip or placement miss is forced on a
call, once or every time. Every challenge comes from the scene (an absent or hidden object, a lid on, a closed
door, a full destination, a book flat on the table ...) or from a dynamic event (someone moves an object).
`tracks.strip_injected` removes the v5 ones from every inherited variant and its route; a variant built on a
failure that never goes away (another object or procedure because an action never succeeds) is dropped, one
left with nothing is dropped, and one variant is kept per design (`tracks.design_key`: conditions, failures,
goal, instruction and the objects handled; not where things stand or where the robot starts, which is the
seed's part). `v6_dropped` per task says why each v5 variant left. The v6 design source has no such variants.
An initial resource / destination / capacity failure next to a scene condition only restates that condition
(`declares_condition`).

A goal of a variant's own (close the door again, leave the block on the island) states how a fallback ends and
does not by itself make a variant Task-Level.

Status: static (`validate_v6.py` checks that no injected failure is left and every category matches its
content). Evaluation metrics are not defined yet.

## Commands

```bash
python benchmark/v6/define_tasks_v6.py     # tasks.json (catalog + tracks); --check: up to date?
python benchmark/v6/validate_v6.py         # STATIC.json: per-episode static checks, v5 hashes, manifests
python benchmark/v6/report_v6.py           # variant_cards.json, ROUTES.md, SKILL_FIX_LIST.md, PHYSICS_TODO.md
python benchmark/v6/tracks.py              # TRACKS.md, batches/category_*.json
python -m pytest -q benchmark/v6/tests failure_injection
$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json \
    --batch benchmark/v6/batches/physics_v6_new.json --jobs 2 --out benchmark/runs/v6_physics --no-eval
```

## Files

* `VARIANTS_zh.md` - every variant in plain Chinese: the situation, what the robot does, what the seed chooses.
* `TRACKS.md` - the four categories, counts per task, every variant with its local fallback and longer-horizon change.
* `variant_cards.json` - per concrete variant: instruction, initial conditions, failure triggers, goal, tracks,
  control, oracle route, challenge / rationale, success criteria.
* `ROUTES.md` - every oracle reference route, by track. `SKILL_FIX_LIST.md` - for the skill owner.
  `PHYSICS_TODO.md` + `batches/` - what still needs simulation.
