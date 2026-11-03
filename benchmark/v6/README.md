# ZenoBench v6: Action-Level and Task-Level suite (design stage)

v6 is the task-design layer on top of v5. It reads `benchmark/v5/tasks.json` and never writes it: every v5
variant, oracle route and episode hash is unchanged (FREEZE.json, 1,800 hashes checked by `validate_v6.py` and
the tests). v6 adds **58 new families** on 17 of the 20 base tasks and splits all 238 families into two tracks.

| | |
|---|---|
| base tasks | 20 (one house, 10 rooms, existing assets only) |
| families | 238 = 180 v5 + 58 new (each with seeds 10-19, 2,380 episodes) |
| tracks | Action-Level 100 families, Task-Level 152, controls 38 (`TRACKS.md`) |
| static checks | 2,380 / 2,380 episodes |
| physics | 51 families PHYSICS_VALIDATED (v5 grid, 10/10); the rest STATIC_VALIDATED (`PHYSICS_TODO.md`) |

## Concepts

* **Family**: one design (challenge, control). Its **cases** are decision instances: a case changes a fact the
  plan depends on (which substitute exists and where, which closed place holds the item, where an event takes a
  resource, which object blocks the reach). Each case is a concrete variant `<family>__<case>` with its own
  configuration and oracle route; seeds 10-19 map to cases through a fixed-RNG, balanced manifest
  (`v6_families[fam]["seeds"]`). A v5 variant is a one-case family; 27 v5 families whose plan must find a
  resource get a **seed-extension** case (the resource in another place, the search and route change).
* **Control**: the variant a family differs from in one factor (`v6_families[fam]["control"]`; for a v5 family
  the task's first nominal variant). Used for GAP.
* **Status**: PHYSICS_VALIDATED (every manifest episode passed in simulation with the current hash and route),
  STATIC_VALIDATED (all static checks pass), DESIGN_COMPLETE (specified, static not passing).

## Two tracks: Action-Level and Task-Level (`tracks.py`, `TRACKS.md`)

The split reads only a variant's configuration (`tracks.content`):

| track | content | runs with | families | episodes |
|---|---|---|---|---|
| **Action-Level** | a transient action failure (grasp miss, slip, placement miss, IK refusal: a retry or re-approach fixes it), or a blocked action fixed by a local repair of the same object, then the same call (`LOCAL_CONDITIONS`: a flat book pushed over the edge, a crowded block pulled apart) | scripted recovery route, physical skills, `benchmark` profile (no GT); the skill layer's score | 100 | 1,000 |
| **Task-Level** | anything that makes the plan itself change: a task-level failure, a dynamic event, an action failure no retry fixes, any other scene condition (search, absent object, lid on, closed door, capacity ...), a changed goal | any task planner on GT skills (`sticky_snap/gt`); oracle route replayed for validation | 152 | 1,520 |
| controls | neither: the nominal plan works | both tracks | 38 | |

Action-Level subcategories name the failure mechanism: AL-IK 54, AL-GRASP 30, AL-SLIP 5, AL-PLACE 1,
AL-COMPOUND 10. Task-Level families are listed per task, with timing (35 have a dynamic event, the rest act
on the initial scene).

A family with both kinds of content (62) is in both: the full variant in Action-Level, its **task
projection** (`<vid>__tl`: the transient action failures removed, and in the route each call they failed with
its local repair up to the successful retry) in Task-Level. 10 projections equal another family's
configuration and are merged into it. A repair that changes another object's or a container's state (move an
obstacle, take a lid off, open a door) is Task-Level.

Per-track metrics (`track_metrics.py`, definitions in its docstring):

* **Action-Level**: ASR (route success), LRR (local recovery rate per injected failure or blocked call, also
  per mechanism), RC (repair calls), NSR (success of the calls no failure targeted), CDR (collateral drops),
  FIV (failure injection validity).
* **Task-Level**: TSR (goal success, also per timing), RRSR (success after a failure or event), PAR (success
  when the planner avoided a declared failure), FRR (futile repeats of a call that fails for a persistent
  reason), PE (plan efficiency), GAP (control TSR minus family TSR), stop reasons.

Status: the split is static (`validate_v6.py` checks every family is in the tracks its content calls for and
every projection on its seeds). Action-Level metrics were dry-run on the v5 physics grid
(`EVALUATION_TRACKS.md`); Task-Level on a GT-skill smoke run.

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
python benchmark/v6/track_metrics.py --runs <run dir> --md benchmark/v6/EVALUATION_TRACKS.md
python -m pytest -q benchmark/v6/tests failure_injection
$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json \
    --batch benchmark/v6/batches/physics_v6_new.json --jobs 2 --out benchmark/runs/v6_physics --no-eval
```

## Files

* `TRACKS.md` - the two tracks, counts per task, every family's track.
* `variant_cards.json` - per concrete variant: instruction, initial conditions, failure triggers, goal, tracks,
  control, oracle route, challenge / rationale, success criteria.
* `ROUTES.md` - every oracle reference route, by track. `SKILL_FIX_LIST.md` - for the skill owner.
  `PHYSICS_TODO.md` + `batches/` - what still needs simulation.
