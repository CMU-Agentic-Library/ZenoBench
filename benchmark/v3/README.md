# ZenoBench benchmark v3

v3 extends the v2 planning benchmark ([../README.md](../README.md), `benchmark/tasks.json`). It adds condition
variants, a fixed 10-seed evaluation grid and an explicitly enumerated matrix. v2 stays in place unchanged,
together with its evidence (`benchmark/RESULTS.md`, `benchmark/EVALUATION.md`). **v2 runs do not count as v3
evidence.** Every v3 episode records its own configuration hash. Only a run whose hash matches the current one
counts.

The robot, the SkillNodes, the contracts, the policies, the observation gate and the house layout are the same
as in v2, except that `explore` is split into `explore_room` and `explore_furniture` (71 SkillNodes). Auto-recovery
stays off, and every recovery is a call that the planner chooses.

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
  * `explore`: search, look, explore_room or explore_furniture only, no physical repair;
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
`tasks.json` holds 20 tasks and 51 variants (50 graded: easy 18, medium 19, hard 13; 1 diagnostic) on seeds
10–19, 500 episodes per planner over 272 distinct configurations: the 10 v2 tasks with their 30 v2 variants,
T11–T18, and T14, T19 and T20 (added 2026-10-21).

**Route acceptance** ([RESULTS.md](RESULTS.md)): every declared route × variant × seed 10–19 ran as a scripted
chain on the v3 configurations (`benchmark/runs/v3_accept_01` … `v3_accept_11`, batches in `batches/accept_*.json`;
earlier passing debug rounds `v3_normal`, `v3_round2` … `v3_round13` count where the hash matches). 520 route
episodes counted, 514 passed physically. **48 conditions are stable (10/10), 2 are unstable**; none is preliminary
or unverified any more. The 6 failed episodes, all low-level execution failures, logs kept:

| Condition | Route | Passed | Failed seeds |
|---|---|---|---|
| T01 `far_no_overhang` (hard) | hard_search_expose | 8/10 | s12, s19: the book slipped out of the hand while it was placed on the dining table |
| T03 `far_small_and_large` (hard) | hard_search_alt_container | 9/10 | s13 |
| T03 `small_and_large` (medium) | alternative_large_container | 7/10 | s13, s14, s15 |

T03 `small_and_large` is stable through its nominal route (10/10); its alternative route is not. In the T03 failures
the rolling pin stays caught on the mug rim after the refused place (hand blocked 7–9 cm above the support instead of
4–6 cm), so the unwind lift stops at 0.96–0.98 m instead of 1.04 m. An `approach` to the mug before the place changed
the park pose (75° → 105°) but not the outcome (s13–s15 failed again, `v3_round13`) and was reverted. One T10
`far_can_far` s19 episode timed out (`v3_accept_10`, planner overflow warnings); the rerun passed
(`v3_rerun_t10_s19`); both logs are kept.

**Evaluation report** ([EVALUATION.md](EVALUATION.md), `metrics.json`; per-episode facts in `metrics.facts.jsonl`,
not tracked) over the 499 acceptance episodes: TSR 99% (493/499), FSR 97% (132/136), ERSR 95% (120/126); failure
attribution: low_level_execution_failure 6. These are scripted routes: feasibility evidence, not planner results.

| Task | Household goal | Conditions |
|---|---|---|
| T11 collect the fruit | lunch is over: the apple from the dining table into the fruit basket on the bedroom bookcase | easy; basket missing → serving tray on the study desk (alternative) |
| T12 tidy the toys | bedtime: toy car and rubber duck into the bedroom storage basket | easy; duck left on the study desk (search) |
| T13 set the breakfast table | bowl and cup from the TV stand next to the spoon on the dining table (a mug if there is no cup) | easy; no cup → mug from the bookcase (alternative); bowl on the low wall cabinet (search); both |
| T14 shelve the book | the red book from the study desk back on the bedroom low bookcase | flat book, no overhang (medium): Normal = Expose → Pick; fallback = Pick fails → Expose → Pick |
| T15 book face up | turn the face-down paperback on the island face up, leave it there | easy; start elsewhere (search) |
| T16 rolling pin at the edge | roll the pin back from the island's front edge (and see it rolls) | easy; start elsewhere (search) |
| T17 hide and seek | hide the toy block in the pot and put the lid on | easy; lid on (Uncover); block boxed in (Separate); lid on + boxed in; far start + lid on |
| T18 check the cabinet | look into the low wall cabinet for a plate and a bowl, close the door | easy |
| T19 recycling | the soda can from the TV stand and the foam cube from the living-room floor into the bedroom bin | easy only |
| T20 juice back to the table | the juice bottle from the low wall cabinet back on the dining table, upright | easy only |

Conditions tried and dropped, with the evidence, are listed under each task's `not_adopted` (MATRIX.md lists them),
among them: flip with the path to the edge blocked (flip sweeps the book and the pin off the island), roll with a bowl
behind the pin (the pin pushes the bowl aside), taking the bowl out of the cabinet (no reachable grasp), the orange
in T11 (slips out of the grasp while carried), the bowl on the bedroom bookcase or the study desk in T13 (pick not
held / slipped while carried); T14 with the book laid over the desk edge (the overhang was never reached); T19 with
the bin moved out of view (study desk: no base pose for the drop; dining table: already known after exploring the
living room); T20 with the bottle out of view (lower wall cabinet: still in view; study desk: tipped over after the
place; bedroom bookcase: slipped while carried) and on the TV stand (tipped at the pick). The first T14 draft
(homework desk) was dropped (`v3_candidates.DROPPED_TASKS`: the notebook edge pinch did not hold).
<!-- v3status:end -->
