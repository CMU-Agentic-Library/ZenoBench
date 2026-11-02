# ZenoBench v6: task-level replanning suite (design stage)

v6 is the task-design layer on top of v5. It reads `benchmark/v5/tasks.json` and never writes it: every v5
variant, oracle route and episode hash is unchanged (FREEZE.json, 1,800 hashes checked by `validate_v6.py` and
the tests). v6 adds **58 new families** on 17 of the 20 base tasks and applies **one difficulty definition** to
all 238 formal families. What v6 is meant to measure: whether a planner replans correctly at the task level when
execution fails or constraints change, not cross-scene generalisation.

| | |
|---|---|
| base tasks | 20 (one house, existing assets only) |
| formal families | 238 = 180 v5 + 58 new (each with seeds 10-19, 2,380 episodes) |
| tiers | Easy 38, Medium 102, Hard 98 (`DESIGN_AUDIT.md`) |
| Hard core capabilities | DR 37, GD 24, SR 24, CL 23, PP 22 distinct designs, each on >= 9 tasks |
| baseline smoke | Retry planner: Medium 4/4 succeed, Hard 5/6 fail; the exception's claim withdrawn (T16) |
| static checks | 2,380 / 2,380 episodes |
| decision-diverse seeds | 57 families (43 of 98 Hard), covering substitute availability, capacity, occupancy, blocking relation, failure timing, item / resource location, failure mechanism |
| physics | 51 families PHYSICS_VALIDATED (v5 grid, 10/10); the rest STATIC_VALIDATED (`PHYSICS_TODO.md`) |

## Concepts

* **Family**: one design (challenge, capability hypothesis, control). Its **cases** are decision instances: a
  case changes a fact the plan depends on (which substitute exists and where, which closed place holds the item,
  where an event takes a resource, which object blocks the reach). Each case is a concrete variant
  `<family>__<case>` with its own configuration and oracle route; seeds 10-19 map to cases through a fixed-RNG,
  balanced manifest (`v6_families[fam]["seeds"]`). A v5 variant is a one-case family; 27 v5 families whose plan
  must find a resource get a **seed-extension** case (the resource in another known-valid place, the search and
  route change) next to the unchanged v5 variant.
* **Tiers** (`hypotheses.py`, the same rule for v5 and v6): **Easy** - the nominal plan works; **Medium** - one
  local adaptation (transient failure, search, a stated substitute, a constraint) without a core capability;
  **Hard** - at least one verified core capability and not solvable by retrying the control plan. 31 v5 labels
  change (configurations untouched): substitution / decoy / free-spot challenges become Medium, the broken
  microwave (stove instead) becomes Hard.
* **Capabilities**: DR dependency replanning, GD goal decomposition, SR strategy replacement, CL cross-level
  recovery, PP partial-progress preservation, AF alternative / fallback. A claim counts only when `hypotheses.py`
  verifies it: a declared cause exists, it blocks the control plan at the step the capability is about, and the
  oracle recovers that way. v6 families declare their hypotheses; v5 ones get proposals checked by the same rules.
* **Control**: the variant a family differs from in one factor (often its Medium transient-failure twin, e.g.
  `x6_m_grasp_block_a` vs `x6_cl_block_a_unholdable`), used both for the necessity check and for the analysis.
* **Status**: PHYSICS_VALIDATED (every manifest episode passed in simulation with the current hash and route),
  STATIC_VALIDATED (all static and capability checks pass), DESIGN_COMPLETE (specified, static not passing).

## Two tracks: Action-Level and Task-Level (`tracks.py`, `TRACKS.md`)

Every family is placed by what its episodes test (`v6_tracks` per task in `tasks.json`):

| track | tests | runs with | families | episodes | subcategories |
|---|---|---|---|---|---|
| **Action-Level** | local recovery from transient action failures | scripted recovery route, physical skills, `benchmark` profile (no GT); the skill layer's score, not a task planner's | 92 | 920 | AL-IK 56, AL-GRASP 22, AL-SLIP 5, AL-PLACE 1, AL-COMPOUND 8 |
| **Task-Level** | goal-preserving task-level replanning | any task planner on GT skills (`sticky_snap/gt`); oracle route replayed for validation | 155 (Hard 92, Medium 63) | 1,550 | Hard: TL-DR 27, TL-GD 18, TL-SR 20, TL-CL 13, TL-PP 14; Medium: TL-SUB 31, TL-PRE 18, TL-SEARCH 14 |
| controls | the nominal plan works | both tracks | 38 Easy | | |

A family with both kinds of content (the v5 Action / Mixed Hards, x6 families with an extra transient
failure; 57) is in both: the full variant in Action-Level, its **task projection** (`<vid>__tl`: the transient
action failures removed, and in the route each call they failed with its local repair up to the successful
retry) in Task-Level, re-audited by the same checker. All 41 Hard projections stay Hard; 10 projections equal
another family's configuration and are merged into it. Persistent action failures stay in Task-Level: no
retry fixes them, so they are task-level facts (TL-CL).

Per-track metrics (`track_metrics.py`, definitions in its docstring):

* **Action-Level**: ASR (route success), LRR (local recovery rate per injected failure, also per mechanism),
  RC (repair calls), NSR (success of the calls no failure targeted), CDR (collateral drops), FIV (failure
  injection validity).
* **Task-Level**: TSR (goal success, also per subcategory / tier / timing), RRSR (success after a failure or
  event), PAR (success when the planner avoided a declared failure), FRR (futile repeats of a call that fails
  for a persistent reason), PPR (no redo of preserved work, TL-PP), PE (plan efficiency), GAP (control TSR minus
  family TSR), stop reasons.

Status: the split is static (`validate_v6.py` checks every projection on its seeds). Action-Level metrics were
dry-run on the v5 physics grid (`EVALUATION_TRACKS.md`); Task-Level on a GT-skill smoke run.

## New failure-injection features (failure_injection/)

Persistent grasp / slip / placement / IK failures (a retry cannot help), `until_moved` (an IK / grasp refusal that
ends when a named obstruction is moved), one-handed slips (a two-handed carry is spared), IK refusals pinned to a
destination (the substitute stays reachable), and a slip that falls back onto the support it was picked from.

## Commands

```bash
python benchmark/v6/define_tasks_v6.py     # tasks.json (catalog + capability audit); --check: up to date?
python benchmark/v6/validate_v6.py         # STATIC.json: per-episode static checks, v5 hashes, manifests
python benchmark/v6/report_v6.py           # DESIGN_AUDIT.md, design_audit.json, variant_cards.json,
                                           # capability_hypotheses.json, ROUTES.md, SKILL_FIX_LIST.md, PHYSICS_TODO.md
python benchmark/v6/tracks.py              # TRACKS.md, batches/track_task_scripted.json, track_action_scripted.json
python benchmark/v6/track_metrics.py --runs <run dir> --md benchmark/v6/EVALUATION_TRACKS.md
python -m pytest -q benchmark/v6/tests failure_injection
$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json \
    --batch benchmark/v6/batches/physics_v6_new.json --jobs 2 --out benchmark/runs/v6_physics --no-eval
```

## Files

* `DESIGN_AUDIT.md` - scale, capability coverage and diversity, difficulty audit, seed diversity, duplication,
  conference-level checklist, the full family matrix.
* `variant_cards.json` - per concrete variant: instruction, initial conditions, failure triggers, goal, verified
  capabilities with evidence, control, oracle route, challenge / rationale, success criteria.
* `capability_hypotheses.json` - per family: expected outcome of the oracle, a fixed-plan and a retry planner,
  and what a task-level replanner needs; a Hard family a retry planner solves falsifies its label.
* `ROUTES.md` - every oracle reference route. `SKILL_FIX_LIST.md` - for the skill owner.
  `PHYSICS_TODO.md` + `batches/` - what still needs simulation.
