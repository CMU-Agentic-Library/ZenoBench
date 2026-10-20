# ZenoBench benchmark v3

v3 extends the v2 planning benchmark ([../README.md](../README.md), `benchmark/tasks.json`). It adds condition
variants, a fixed 10-seed evaluation grid and an explicitly enumerated matrix. v2 stays in place unchanged,
together with its evidence (`benchmark/RESULTS.md`, `benchmark/EVALUATION.md`). **v2 runs do not count as v3
evidence.** Every v3 episode records its own configuration hash. Only a run whose hash matches the current one
counts.

The robot, the 70 SkillNodes, the contracts, the policies, the observation gate and the house layout are the same
as in v2. Auto-recovery stays off, and every recovery is a call that the planner chooses.

## Files

| File | Written by | Content |
|---|---|---|
| `tasks.json` | `python benchmark/define_tasks_v3.py` | v3 registry: tasks, variants (conditions), routes, oracle map, condition registry, `not_adopted` |
| `matrix.json`, `MATRIX.md` | `python benchmark/matrix.py` | every (task, variant, seed) with its generated configuration and hash; counts |
| `batches/smoke.json` | `matrix.py` | the first seed (10) of every declared route × variant: one chain before ten seeds |
| `batches/routes.json` | `matrix.py` | every declared route × variant × seeds 10–19 (route acceptance) |
| `batches/eval.json` | `matrix.py` | task × variant × seed × planner (`fixed`, `retry`, `oracle`, + `recovery` with `--policy`) for the conditions whose route acceptance is **stable** (`--all`: every registered condition) |
| `conditions.json`, `RESULTS.md` | `python benchmark/conditions.py --runs DIR...` | route acceptance per condition, from scripted runs with a matching hash |
| `EVALUATION.md`, `metrics.json` | `python benchmark/evaluate.py --tasks benchmark/v3/tasks.json --runs DIR --md benchmark/v3/EVALUATION.md --json benchmark/v3/metrics.json` | planner metrics |

New conditions are debugged in `benchmark/v3_candidates.py`, which generates a research file:
`python benchmark/define_tasks_v3.py --candidates OUT.json`. A task's conditions move into
`define_tasks_v3.EXT` / `NEW_TASKS` (and therefore into `tasks.json`) when:

* a new task has run its complete Normal route;
* every new recovery route has been verified on 1–2 representative seeds (more for contact-geometry-sensitive
  conditions such as 3 mm gaps): the expected failure really happens in physics, the explicit recovery or
  alternative chosen by the upper level runs, and the original task is completed in full.

Such a condition is **preliminary**. The remaining seeds keep their generated configuration and stay unrun until a
later stability round; reaching 10/10 is not required to register a condition. Conditions whose failure does not
happen, or whose recovery cannot complete the task, are recorded under the task's `not_adopted` with the evidence.

## Conditions, seeds and the matrix

* **One condition = one `variant_id`.** A condition is never defined by a seed. Medium has one condition tag,
  hard has two, easy has none (checked by `tests/test_matrix.py`). The registry gives each tag a *condition type*
  and the *decision* it requires:
  * `explore`: search, look or explore only, no physical repair;
  * `fallback`: a real failure, then an auxiliary skill, then a retry;
  * `alternative`: another legal object, destination, appliance or tool.
* **Seeds 10–19** are used for every easy, medium and hard condition and every planner. Each planner gets the
  identical configuration of (task, variant, seed).
* **What a seed changes**:
  * which removable distractors are removed (as in v2);
  * where a variant declares a safe range (`vary`), a rigid shift of an object group, and the robot start
    (x ± 0.1 m and heading ± 10° around the default start, or heading only around an explicit start).

  A group moves together, so the gaps, overhangs and contacts that make a condition hold stay exactly as declared.
* **Configuration hash**: `scene.config_hash` is computed over the base scene, the removed objects, the moved
  objects, the start and the thermal settings. Task, variant and seed labels are excluded. Two seeds with the
  same hash are physical repeats of one scene, not two scenes; `MATRIX.md` gives the distinct configurations for
  each condition. A configuration is reproducible; the physics trajectory is not guaranteed to be bit-identical.
* **The matrix is enumerated.** `run_episode.py --difficulty` (the seed picks a variant within one tier) stays for
  single episodes, but the matrix never samples.
* Every episode records:
  * the task file path and its sha1;
  * `benchmark_version` and the configuration hash;
  * the full generated configuration;
  * the code version (commit plus hash of the tracked diff);
  * task, variant, difficulty and seed.

## Counting

Documents report these quantities separately and never merge them:

| Quantity | Meaning |
|---|---|
| Tasks | registered tasks |
| Conditions | registered (task, variant) pairs; *graded* = easy / medium / hard |
| Seeds | 10 per condition |
| Episodes | conditions × seeds, per planner (generated, not run) |
| Episodes run | episodes with a result whose hash matches |
| Physically passed | episodes run whose chain ran to its end, whose expected failures failed, whose GT goal holds and in which nothing dropped |

A generated configuration is never a physical success. Each condition has one status, taken from its best
declared route:

| Status | Meaning |
|---|---|
| **stable** | 10/10 seeds |
| **preliminary** | every run passed, fewer than 10 seeds run |
| **unstable** | some seeds passed |
| **failing** | runs exist, none passed |
| **unverified** | no counted run |

Scripted routes show feasibility only. They are not evidence that an agent recovered on its own.

`evaluate.py` gives two equal-weight means next to the plain SR:

* `SR_task`: the mean of the per-task SRs;
* `SR_cond`: the mean of the per-(task, variant) SRs.

It groups by `task`, `tier`, `ctype` (condition type) or `condition`. In `ctype` grouping an episode is counted
in each of its types, so those groups overlap. Precondition refusals (`pre`) and physical execution failures
(`exec`) are counted apart, as in v2.

## Status

<!-- v3status:start -->
Stage 1 (registry, seeds, hash, matrix, counting) is complete. `tasks.json` holds 17 tasks and 48 variants (47 graded)
on seeds 10–19: the 10 v2 tasks with their 30 v2 variants, plus T11–T18 with 18 new conditions (267 distinct
configurations in the matrix). Route acceptance ([RESULTS.md](RESULTS.md), `python benchmark/conditions.py --runs
benchmark/runs/v3_normal benchmark/runs/v3_round2 ... benchmark/runs/v3_round7`): 21 route episodes run,
21 passed; 18 conditions are **preliminary** (every new condition, 1–2 seeds each), 29 are **unverified** (the v2
variants have not been run on v3 configurations yet). Preliminary means feasible on the seeds run, not stable.

| Task | Household goal | Conditions (route, seeds passed) |
|---|---|---|
| T11 collect the fruit | lunch is over: the apple from the dining table into the fruit basket on the bedroom bookcase | easy (nominal, s10); basket missing → serving tray on the study desk (alternative, s10) |
| T12 tidy the toys | bedtime: toy car and rubber duck into the bedroom storage basket | easy (nominal, s10); duck left on the study desk (search, s10) |
| T13 set the breakfast table | bowl and cup from the TV stand next to the spoon on the dining table (a mug if there is no cup) | easy (nominal, s10); no cup → mug from the bookcase (alternative, s10 s11); bowl on the low wall cabinet (search, s10); both (s10) |
| T15 book face up | turn the face-down paperback on the island face up, leave it there | easy (nominal, s10); start elsewhere (search, s10) |
| T16 rolling pin at the edge | roll the pin back from the island's front edge (and see it rolls) | easy (nominal, s10); start elsewhere (search, s10) |
| T17 hide and seek | hide the toy block in the pot and put the lid on | easy (s10); lid on (Uncover, s10); block boxed in (Separate, s10 s11); lid on + boxed in (s10 s11); far start + lid on (s10) |
| T18 check the cabinet | look into the low wall cabinet for a plate and a bowl, close the door | easy (nominal, s10) |

Conditions tried and dropped, with the evidence, are listed under each task's `not_adopted` (MATRIX.md lists them),
among them: flip with the path to the edge blocked (flip sweeps the book and the pin off the island), roll with a bowl
behind the pin (the pin pushes the bowl aside), taking the bowl out of the cabinet (no reachable grasp), the orange
in T11 (slips out of the grasp while carried), the bowl on the bedroom bookcase or the study desk in T13 (pick not
held / slipped while carried). The T17 far start first failed (s10, `v3_round2`) because the route navigated to the
pot before it had been seen; the route now goes to the stove top and looks (s10, `v3_round3`, pass). In T13 the place spots were moved twice: the bowl at x 2.93 was knocked when the arm left the table (no_cup, `v3_round5`) and a cup spot at x 3.25 was out of reach (`v3_round6`); bowl 3.05 and cup 3.20 pass (`v3_round7`). T14 (homework desk) was dropped (`v3_candidates.DROPPED_TASKS`: the notebook edge pinch did not hold).
<!-- v3status:end -->
