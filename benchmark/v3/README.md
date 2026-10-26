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

* **One condition = one `variant_id`.** A condition is never defined by a seed. Easy has no condition tag; Medium
  has one, or two local ones (the former v3 Hard variants, labelled `"difficulty": "medium"`,
  `"v3_difficulty": "hard"`); Hard is the v4 task-level replanning tier (`"since": "v4"`, explicit
  `"difficulty": "hard"`, see [Difficulty redesign](#difficulty-redesign-v4-hard)), checked by
  `tests/test_matrix.py`. The registry gives each tag a *condition type* and the *decision* it requires:
  * `explore`: search, look, explore_room or explore_furniture only, no physical repair;
  * `fallback`: a real failure, then an auxiliary skill, then a retry;
  * `alternative`: another legal object, destination, appliance or tool;
  * v4 Hard: `decompose` (split / allocate by capacity, location, several goals), `insert` (a missing
    precondition becomes a subgoal), `replace` (another appliance, vessel or strategy).
* **Seeds 10–19** are used for every easy, medium and hard condition and every planner. Each planner gets the
  identical configuration of (task, variant, seed).
* **What a seed changes**:
  * which removable distractors are removed (as in v2);
  * where a variant declares a safe range (`vary`), a rigid shift of an object group, and the robot start
    (x ± 0.1 m and heading ± 10° around the default start, or heading only around an explicit start).

  A group moves together, so the gaps, overhangs and contacts that make a condition hold stay exactly as declared.
* **Configuration hash**: `scene.config_hash` is computed over the base scene, the removed objects, the moved
  objects, the start and the thermal settings (and the added objects, for the variants that add any). Task, variant and seed labels are excluded. Two seeds with the
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

## Difficulty redesign (v4 Hard)

Source: *ZenoBench Task-Level Replanning* report (2026-10-24). Easy / Medium / Hard are now tiers of planning
ability, not counts of environment conditions:

| Tier | Name | Environment | Expected ability | Task graph |
|---|---|---|---|---|
| Easy | Nominal execution | resources as expected | execute a legal plan | unchanged |
| Medium | Skill-level adaptation | search / substitute / local failure | Search, Alternative, Fallback | structure kept |
| Hard | Task-level replanning | capacity, space, dependencies, resources interact | Decompose, Insert, Replace | changed by the environment |

* **v4 is a label, not a catalog.** Everything lives in this `tasks.json` (same path, same 20 task ids), so Graph
  Manager's sync and the HTTP service see the same file. The former v3 Hard variants (two local conditions) are
  Medium now: `"difficulty": "medium"`, `"v3_difficulty": "hard"`. Their configurations are unchanged
  (`tests/test_matrix.py::test_v3_configurations_unchanged_by_the_redesign` checks all 510 (task, variant, seed)
  hashes against `tests/v3_config_hashes.json`), so their route evidence still counts.
* **Hard variants** come from `benchmark/v4_hard.py` (`"since": "v4"`, explicit `"difficulty": "hard"`). A Hard
  variant may carry its own `instruction` / `instruction_zh` (the report's Proposed Hard instruction) and `goal`
  (`episode.catalog.resolve_task`). The instruction never states the solution: the constraint is observed or met
  through feedback. `public_task` returns the selected variant's instruction in the same `description` field.
* **Task-level decision, not more actions.** Choosing another functional resource or strategy from what the
  environment offers counts, even when the skill sequence looks similar. No Hard fails on purpose: where a failure
  appears it is the environment's real constraint (no free spot, an occupied appliance), and the proactive plan avoids it.
* **Verifiers accept every instruction-compliant strategy and reject the shortcuts.** Goal-only predicates in
  `episode/goal_predicates.py` (not Contract conditions, no skill export changes): `near_start` (layout restored; an object never picked up must stay within 3 cm: shoved is not restored),
  `clear_of` / `near_any` (beside a setting but out of its way), `front_visible` (on display, not hidden),
  `count_on_at_least` (the table was not cleared), `fully_inside` (put away, not perched on top: real capacity).
* **Added objects.** A variant may add assets the base scene lacks (`"add"`, e.g. the small storage bin, a
  look-alike bin, stored blocks, a laid party table); the configuration hash covers them only when present.
* **Each Hard has an oracle route and a negative route.** The oracle shows one complete strategy is physically
  feasible; the negative route is the naive plan the Hard is built to reject (expected outcome: planning failure).
  `benchmark/v4_report.py` classifies every scripted run as passed / planning_failure / physical_failure /
  refused / condition_not_met / system_error, kept apart ([V4_HARD_VALIDATION.md](V4_HARD_VALIDATION.md)).

| Task | Report category | Hard variant | Environment | Decision the planner must make |
|---|---|---|---|---|
| T01 | insert | `table_set` | table set along the robot's side; free slots wedged between settings, far from them, and one beside a plate | place the book beside a setting yet clear of it (not where `place` would put it) |
| T02 | insert | `edge_base` | block A at the island's front edge, block B in the open | choose B as the base (or move A in first), not the Easy stack on A |
| T03 | decompose | `three_containers` | the mug by the utensils; a small and the wide storage bin side by side on the TV stand | allocate both utensils jointly: the spoon fits the small bin, the 22 cm pin only the wide one |
| T06 | insert | `display_hidden` | a closed row of cereal boxes and a bottle along the cabinet's open front: its free space is behind them | display on the TV stand (or make a front spot), not hidden |
| T07 | replace | `microwave_holds_pot` | the microwave works but holds the soup pot; the stove is free | heat on the stove instead of clearing the microwave (both allowed) |
| T08 | insert (cleanup ①) | `island_cluttered` | clutter along both strips: no free strip within reach of the robot, `wipe` refuses | take what stands in the strip off the island, wipe, put it and the sponge back (a shoved object fails the goal) |
| T09 | replace | `cookware_choice` | a breakfast bowl and a mug by the tomatoes, the pot on the stove; the instruction asks for "a suitable pot" | choose the pot (stirring, lid, burner) over the nearer containers |
| T11 | decompose | `basket_gone_bowl_there` | no basket; a bowl stands where it should be | keep to the stated substitute (the tray on the study desk), not the bowl |
| T12 | decompose | `toys_everywhere` | car and duck in two rooms; no basket: a small bin half full of blocks and a shallow tray | allocate by capacity: the duck fits only the bin's last gap, so the car goes to the tray (no single container holds both) |
| T13 | insert | `no_cup_spoon_boxed_in` | no cup; no room for a bowl or mug next to the spoon | mug for the cup, and move the setting (spoon) to where it fits |
| T14 | insert (cleanup ②) | `shelf_taken` | the mug at the front and the duck at the east end of the bookcase top: no edge slot fits the book | move the mug to a legal place first, then shelve the book |
| T19 | decompose | `lookalike_bin` | can out of view in the dining room; a look-alike toy bin on the way | search the can, route both items to the instructed recycling bin |
| T20 | insert (cleanup ③) | `table_full` | party table covered: no spot for the upright bottle | move a few things (one bowl), not clear the table |

Medium-only (the report proposes no Hard): T04, T05, T10, T15, T16, T17, T18 — their alternatives are local
substitutions or action-level recoveries without a task-graph change.

**Validation (2026-10-26)** ([V4_HARD_VALIDATION.md](V4_HARD_VALIDATION.md), runs `benchmark/runs/v4_accept`,
`v4_accept_r2` … `v4_accept_r8`, `v4_fixes`, `v4_fixes_wipe`, `v4_fixes_t14*`, batches `batches/accept_v4_*.json`,
`batches/fix_probe*.json`; only runs whose configuration hash matches the catalog count): **all 13 Hard oracles pass
on seeds 10 and 11; all 13 negative routes end as `planning_failure`** (every call works, the goal rejects the
plan). Physics and planning are kept apart:

* **Skill fixes (2026-10-26, `zeno_skills/`, no Contract / SkillNode / export change):** `place_flat` kept the
  worst-squared park (the score sign was inverted), its park now also reaches the final push, and the hand turns to
  the release yaw by a level Cartesian turn before `flat_pre` (the joint swing flipped the book); an object that
  turned in the pinch stops outside the support instead of being slid in and dropped; under another level the book
  comes down fully outside the front. `wipe`, `slide_to_edge` and the regrasp free test passed their box to
  `_overlaps_objects` as `[x0, y0, z0, x1, y1, z1]` instead of `[x0, y0, x1, y1, z0, z1]`, so they never saw
  objects in the way (`wipe` shoved them); `wipe` now also tries a strip 4.5 cm in from the edge when the 8 cm line
  is taken (the nominal island has the mug and the spoon along it). Failed articulated parks are retried last.
* **T14 `shelf_taken`** (was blocked by the `place_flat` bug): with the skill fixed the east end of the top was a
  free slot, so the duck moved from the front to the east end (front and east end both too narrow; the oracle's
  front slot after the mug moved is unchanged). The negative leaves the book on the other bookcase
  (`bookcase_3/top`). The Clear -> Continue fallback (`hard_place_fails_then_make_room`: place refused, book back on
  the desk, mug moved, book fetched again) is a **physical failure** on s10 / s11: setting the edge-held book down
  again is unreliable (desk: 10° tilt; s11: it slipped on the long carry back). Remaining `place_flat` limits: on
  `bookcase_3/top` and `bookcase_2/shelf_1` (under the top) the lower finger stays under the released book and the
  hand pulls it out (1 of 4 and 0 of 2 placed); the dining table (81 of 83), the island and `bookcase_2/top` work.
* **T08**: the naive wipe is now refused (no free strip), so it ends without `wiped`; the verifier still rejects a
  shoved object (`near_start` with `untouched_tol_m` 0.03 for objects never picked up). `restore` returns an object
  to its start support, not its spot, so the oracle puts block B back with a hinted place.
* **T06**: the negative (block behind the closed row) is rejected because reaching behind the row knocks the boxes
  and the bottle over (`upright` fails); `front_visible` then holds only because the row fell. The hidden spot is
  unusable either way; the TV stand is the working plan.
* **Physics fixes made during validation (layouts / routes only):** T02 block B 14.5 cm in (the pick missed it
  23.5 cm in); T03 small bin on the TV stand (no drop pose above it on the island) and the goal `fully_inside`
  ("completely inside": the pin perched across the small bin passed `inside`); T13 the setting 14 cm further south
  and a re-park after the spoon pick (the arm knocks a cereal box over onto the old mug spot); T08 the sponge goes
  back to the TV stand and block B west of it there.
* **Regression** (seed 10, after the skill fixes): the non-Hard routes of T01, T07, T08, T14, T15 and T18 pass,
  except T08 `oracle_approach` (never accepted before, not an oracle), refused `NOT_OBSERVED` at its first
  `navigate` to the unseen sponge (route authoring, no skill involved).

**Compatibility.** No Graph Manager file, Contract, skill export (`skill_library/`, `tools/build_skill_library.py
--check` unchanged) or HTTP field changed. Graph Manager main (7289dd7) synced against this catalog indexes
13 Hard / 32 Medium variants with its own `difficulty_of`; one of its tests hard-codes "12 tasks with a hard
variant" (`tests/test_run_cli.py`, 24 requests), which becomes 26 after the next sync — a data expectation in
Graph Manager, not an interface change.

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
