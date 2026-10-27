# ZenoBench planning benchmark (observation-limited)

A small benchmark for an upper-level planner (a VLM) on top of the existing 71 SkillNodes. Every planner gets the same
low-level skills and the same observation limits. The question is whether the planner chooses an effective fallback
or alternative from what it sees and from the execution feedback. The Isaac Sim GT verifier decides success; the
planner never sees GT state.

<!-- results:start -->
Declared task routes: **60/60** episodes pass (29 routes: 29 stable); probes 14/21; baselines fixed 2/10, retry 3/10, oracle 9/10; SkillNode coverage **64/70** (5 called but failed, 1 never called).  Per route and seed: [RESULTS.md](RESULTS.md); per skill: [coverage.json](coverage.json).
<!-- results:end -->

## Observation boundary

Every planner acts through `episode.episode.Episode` with the profile `episode/profiles/benchmark.yaml` (the GT
oracle: `oracle.yaml`); the same class and profiles serve the HTTP planners of `env_service`. See
[../episode/README.md](../episode/README.md).

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
* explore_room picks viewpoints from the static layout and computes coverage over
  static furniture only (`rig.static_explore`); explore_furniture aims at every
  support layer of one piece of furniture.

Navigation keeps the GT map and collision checking for safe low-level planning.

No automatic recovery in this interface: no nested repair (`auto_repair=False`),
no slide-to-edge inside pick (`skip_steps`), no pick -> push fallback, no
door "retry from another park" (`rig.auto_recovery=False`).  The feasibility
estimates `grasp_clearance` and `edge_overhang` are advisory (recorded, the
action is attempted), so an infeasible pick fails *physically*.  The original
behaviour stays the default of `SkillContractRunner`; `tools/verify_skills.py`
(GT runner) is the trusted physical acceptance entry and is unchanged.

## Tasks

`benchmark/define_tasks.py` writes `benchmark/tasks.json`. Each task has one fixed base scene plus a local overlay that
removes objects or re-places existing objects on their supports; the house layout never changes. The seed picks a
condition variant (whether the fallback or alternative condition holds) and removes a random subset of distractors.
Instructions state the goal only: no positions, no order, no recovery hints.

Difficulty tiers are chosen with `--difficulty easy|medium|hard` or an explicit `--variant`. Tiers count the
conditions present:

- **easy:** none;
- **medium:** one, e.g. the pick fails, the destination is full, the preferred object or appliance is unavailable, or
  the object is out of view;
- **hard:** one of those plus a second, e.g. starting in another room or facing away.

The instruction is the same in every tier. 29 task × tier combinations exist; T05 has no easy tier.

| Task | Instruction (short) | easy | medium (condition -> declared route) | hard (conditions -> declared route) |
|---|---|---|---|---|
| T01 | Bring the paperback from the kitchen island to the dining table. | book overhangs the island edge | no overhang -> **fallback** Pick fails -> Expose -> Pick | starts at the wall cabinet facing away + no overhang -> Search, Pick fails -> Expose -> Pick |
| T02 | Stack one wooden block on the other. | blocks free | block B boxed in by a bowl and the rolling pin -> **fallback** Pick fails -> Separate -> Pick; **fallback** Pick fails -> Push -> Pick | starts at the wall cabinet facing away + boxed in -> Search, Pick fails -> Separate -> Pick |
| T03 | Put the rolling pin and the spoon away together in one container. | only the storage bin | a mug as well -> **alternative** the pin does not fit the mug -> lift, retreat -> storage bin | starts facing away + mug -> Search, then the same alternative |
| T04 | Set out a cup on the low wall cabinet; a mug if there is no cup. | cup on the island | no cup -> **alternative** Count 0, Search fails -> mug | no cup + mug on the TV stand -> Count, Search fails -> Search mug -> mug |
| T05 | Bring a pen to the study desk; a pencil if there is no pen. | — (no easy tier: the pen slips out of the hand 4/4, its route is diagnostic) | no pen -> **alternative** navigate to the pen refused -> pencil | no pen + pencil in the dining room -> Search pencil -> pencil |
| T06 | Put a toy block on display on the wall cabinet or the TV stand. | cabinet top free | top full -> **alternative** Place fails -> TV stand | top full + block in the dining room -> Search, Place fails -> TV stand |
| T07 | Warm the oatmeal to >= 40 C; stove off, microwave closed afterwards. | microwave works | microwave does not heat -> **alternative** Heat fails -> Stop, take out -> stove | broken + oatmeal on the wall cabinet -> Search, then the same alternative |
| T08 | Wipe the kitchen island with the sponge, leave the sponge there. | sponge on the island | sponge on the TV stand -> fetch it, Approach the island, Wipe | starts in the dining room + sponge away -> Search, Approach, Wipe |
| T09 | Tomato soup: tomatoes into the pot, stir, cover, heat to 60 C, stove off. | lid off | lid on -> **fallback** Collect refused -> Uncover -> Collect | lid on + spoon on the TV stand -> Uncover, Search spoon |
| T10 | Throw the empty soda can into the trash can. | can on the island | can in the dining room -> **fallback** Pick refused (not observed) -> Search | starts in the dining room + can on the TV stand -> Pick refused -> Search -> Explore for the trash can |


- **Fallback:** a real failure, after which an auxiliary skill repairs the state and the same action is retried.
- **Alternative:** another legal object, skill or destination reaches the same goal.

Routes record which kind they are (`kind`). Step roles inside a route are:
- `failure` (expected to fail, `"expect": "fail"`);
- `recovery`, `alternative` and `retry_after_recovery`;
- `unwind`, which only undoes the failed call's side effect.

Routes that failed physically when tried are kept as `kind: diagnostic` (T05 pen, T06 clear-then-place) and are not
acceptance routes. Probes P01–P22 (21; there is no P10) are single-scene checks for SkillNodes that do not fit the ten tasks naturally.

## Connecting a VLM

A planner implements `reset(task_instruction, skills)` and `next_call(observation) -> {"skill", "args"} | None`
(`benchmark/planners.py`). `observation` is `Episode.observation("path")` with the `benchmark` profile, the same
fields an HTTP planner gets from env_service:
- `images`: the head-camera image as a PNG path;
- `visible_objects` and `observation_cache`;
- `known_places`;
- `robot`: pose, room, hands, known temperatures;
- `last_result`: the last call's result, unobserved names masked.

Returning `None` ends the episode (`stop_reason: planner_done`). Reaching `--max-calls` (default 60) ends it with
`stop_reason: budget`. An exception in the planner or the harness makes the episode *incomplete*.

```bash
export ISAACLAB_PYTHON=~/miniforge3/envs/isaaclab/bin/python
python benchmark/define_tasks.py && python benchmark/check_layouts.py      # tasks.json, static overlay check
python -m pytest benchmark/tests -q                                        # gate tests (stub rig)
$ISAACLAB_PYTHON benchmark/tests/sim_permissions.py                        # gate tests in Isaac Sim

# your planner on one episode of a tier
$ISAACLAB_PYTHON benchmark/run_episode.py --task T07_heat_oatmeal --seed 10 --difficulty hard \
    --planner recovery --policy mypkg.planner:MyPlanner
# baselines on the same episode: fixed / retry / oracle
$ISAACLAB_PYTHON benchmark/run_episode.py --task T07_heat_oatmeal --seed 10 --difficulty hard --planner fixed
# a declared route (physical feasibility evidence, not a planner result)
$ISAACLAB_PYTHON benchmark/run_episode.py --task T01_book_to_dining_table --seed 0 --route fallback_expose

# batches (at most two Isaac processes)
python benchmark/make_batches.py [--policy mypkg.planner:MyPlanner]       # accept / baselines / probes / eval
python benchmark/run_episode.py --batch benchmark/batches/eval.json --jobs 2 --out benchmark/runs/eval
python benchmark/evaluate.py --runs benchmark/runs/eval --group planner,tier
python benchmark/report.py --runs benchmark/runs/final benchmark/runs/retest
```

Each episode directory keeps:
- `config.json`: variant, overlay, removed distractors, git commit and diff hash;
- `annotation.json`;
- `calls.jsonl`: every call with its feedback and a state summary;
- `images/`;
- `result.json`: goal atoms, drops, `final_state`, `sim_ticks`, `stop_reason`, observation cache, gate log, and the
  last 300 events.

## Evaluation

**Task Success:** every GT goal atom holds after the run settles (60 ticks after the last call), no watched object is
on the floor, a scripted route ran to its last step, and every `expect: fail` step really failed. **Skill Success**
is per call (`feedback.success`) and is reported separately. An episode that crashed or timed out is *incomplete*: it
is kept out of SR and of every failure count, and shown in its own column.

`evaluate.py` scores how a planner behaved; `report.py` checks which routes ran and which SkillNodes they covered.
Both read `result.json` only.

| Metric | Definition |
|---|---|
| **SR** | Task Success over the completed episodes |
| **skill_SR** | Successful calls / calls (scripted `expect: fail` calls left out) |
| **GC** | Fraction of the goal atoms that hold at the end (for `any` groups, the best group): partial progress |
| **pass^k** | Share of tasks where every seed in the group passed |
| **SPL-c** | Mean of S · L_ref / max(L, L_ref), where L is the calls made. L_ref is the call count of the variant's oracle route in `tasks.json`, without its expected-failure and unwind steps. It counts only when a run of that route passed on that variant in the evaluated runs; otherwise N/A, and the denominator is shown in brackets |
| **unseen / ghost / not_in_view** | Gate refusals per episode. *Unseen*: the object exists but was never observed. *Ghost*: the object is not in this episode (the planner gets the same refusal for both). *Not in view*: the object was seen earlier but is out of view now |
| **pre** | State or geometry precondition failures per episode (PRECONDITION_FAILED, NO_PATH): nothing was executed |
| **exec** | Execution failures per episode (POLICY_FAILED, SUBSKILL_FAILED, POSTCONDITION_FAILED): the robot tried and the physics said no |
| **invalid** | Interface errors per episode (BAD_CALL, INPUT_*, NOUN_INVALID, BINDING) |
| **recov_gate / recov_pre / recov_exec** | Of the episodes with at least one failure of that class, the share that still succeeded. The denominator is in brackets; N/A when it is 0 |
| **repeat** | Share of pre + exec failures followed by the identical call (blind retry), with the denominator |
| **drops / side / budget** | Episodes with a floor drop (this also fails SR); non-goal watched objects moved more than 5 cm (informational, because separate and push move things on purpose); episodes ended by the call budget |

Comparability:
- `fixed`, `retry` and `recovery` run through the same gate, with the same low-level settings (`auto_recovery` off,
  upright edge-pinch waist) and the same skills.
- `fixed` runs the nominal plan once; `retry` repeats a failed call up to twice; `recovery` is bounded by `max_calls`.
- `oracle` is a capability upper bound and is reported separately. It runs the GT runner (full state, no gate, nested
  repair on) with the hand-written route for the variant, minus its expected-failure and unwind steps.
- The gap between `fixed` and `oracle` is therefore not a VLM recovery gain. Compare a VLM with `fixed` and `retry` on
  the same grid.
- `scripted` rows replay declared routes, which fail on purpose; they are feasibility evidence.

### Evaluation-spec metrics (EVALUATION_SPEC.md)

`evaluate.py` also writes the metrics of [EVALUATION_SPEC.md](EVALUATION_SPEC.md) (section *Evaluation-spec
metrics* of its markdown, `spec` in its JSON, one line per episode in `<json>.facts.jsonl`). The code is
`metrics.py`. Instruction semantics of alternatives are in `eval_semantics.py`, which only the evaluation reads.
A `--batch` run of `run_episode.py` ends by running it on its `--out` directory and writes `EVALUATION.md`,
`metrics.json` and `metrics.facts.jsonl` there (`--no-eval` skips this). It can also be run by hand:

```bash
python benchmark/evaluate.py --tasks benchmark/v3/tasks.json --runs benchmark/runs/eval_vlm \
    --batch benchmark/v3/batches/eval.json --md benchmark/runs/eval_vlm/EVALUATION.md \
    --json benchmark/runs/eval_vlm/metrics.json
```

The tables are per planner. Every ratio is shown as *value (numerator/denominator)*, and N/A means no sample.

| Metric | Implementation |
|---|---|
| TSR | Successes / valid episodes. Planned (`--batch`/`--planned`), started, valid and system-error counts are reported. Also task-equal and condition-equal means, and *physical verifier only* next to *instruction semantics* (a legal substitute is required). |
| Planning Correctness | Each call is `valid` (ran; or the controller failed after the preconditions held), `invalid` (interface error; a hand-state precondition that the planner's robot observation shows), or `undetermined` (gate refusals, other state preconditions, NO_PATH). Reported as valid/(valid+invalid), with the undetermined count and the coverage. |
| FSR | The denominator is the variants with a registered substitute condition (`eval_semantics.substitute`) that also have a passing alternative route (in the runs or in `conditions.json`). Legal results, not a particular skill sequence, identify the option used. Selection comes from state / Contract-effect evidence; final outcomes can establish selection with unknown timing. Reports selection, selected-then-failed, proactive selection and unknown timing separately. |
| ERSR | Episodes with a physical execution failure, and the share whose task then succeeded. Also reports verified recovery **and** final task success, excluding blind retries / unverified mechanisms. State-precondition and observation failures get separate rows. Local recovery accepts the same operation or equivalent bound Contract effects after relevant repair evidence; a composite can instead satisfy the verified original task goal (reported as `task_goal`, not an inferred intermediate grasp). `retry_only`, `mechanism_unverified`, alternatives and unrecovered events stay separate. |
| Robustness | TSR by challenge count (normal / single / combined), number of goal objects, reference route length, and actual room transitions (from the base pose after each call). |
| Efficiency | Means over successful episodes and over failed episodes, each with its n: calls, extra recovery calls, invalid repeats (the same call with no state change in between), base travel (straight lines between call end poses, a lower bound), room transitions, simulated time, wall time, and planner response time (closed loop only). |
| Success types | `direct`, `fallback` (with its observation / precondition / execution subtype), `alternative` and `combined`. `recovered_unverified` covers blind retries and recoveries without state evidence; `undetermined` covers the rest. |
| Failure attribution | `planning_failure`, `exploration_failure`, `substitution_failure`, `recovery_failure`, `low_level_execution_failure`, `feasibility_unverified`, `system_error` and `undetermined`, with one direct cause per event. Replayed `scripted` and `oracle` routes are never charged with planner, recovery or substitution failures. |

From `eval_log_version` 2 on, call rows log `state_before`, `state` and `eval`. `eval` holds the chain down to the
deepest failed nested call, its code, message and false checks. Closed-loop rows also log `planner_s`, `tick` and
`wall_s`. None of this reaches the planner. For older logs, the state before a call is the previous call's state,
and the failed sub-step is parsed from the nested error text. Anything missing is N/A.

**Outcome evaluation v1** changes scoring only (`eval_outcomes.py`, `eval_semantics.py`, `metrics.py`).
Alternatives declare `groups` of existing final Goal predicates or intermediate `outcomes` (OR of ANDs of
predicate lists), plus optional `entities` / `destinations` for selection evidence. Multiple legal options are
allowed. No `pick`, `place`, `heat`, fallback helper or reference route name is required for scoring. Shared
Contract postconditions can be recovered from successful calls in old logs; missing state remains unknown.
Feedback preconditions are not treated as post-execution results. Geometry, final GT checks, instructions,
policies, observation permissions and historical result files are unchanged. Feasibility routes still establish
that a condition is executable; they do not prescribe the planner's actions. New facts and summaries carry
`outcome_evaluation_version: 1`.

### Quantitative protocol (12 metrics)

The paper protocol of the task-level replanning redesign (2026-10-26) is implemented in `protocol.py`. Opportunities
for proactive adaptation are registered in `eval_adaptation.py`, which only the evaluation reads. `evaluate.py`
writes the section *Quantitative protocol (12 metrics)* (main table, groups A–D, main metrics by tier), adds
`protocol` (per planner) and `protocol_tiers` (per planner × tier) to its JSON, and puts each episode's inputs
under `protocol` in `<json>.facts.jsonl`. A `--batch` run of `run_episode.py` produces all of this as well.
Everything comes from the existing logs (`result.json`): there is no new simulator logging, and old runs can be
rescored.

The paper's main table is **TSR · SCR · OISR · PASR · RRSR · RTSR**; the other metrics are for ablations and failure
analysis. Ratios are shown as *value (num/den) [Wilson 95 % CI]*. Only valid episodes count; system errors are
listed separately. The event metrics (PASR, RRSR, FSA, RE) show N/A when nothing is eligible, never 0 or 100 %.

| Group | Metric | Implementation |
|---|---|---|
| A | **TSR** Task Success Rate | Same as the spec TSR: every goal atom holds, the substitute is legal, nothing ended on the floor |
| A | **SCR** Subgoal Completion Rate | Per episode: goal-category atoms (below) other than `hand_empty` that hold at the end / their number, equal weights; for `any` goals the group that got furthest. Mean over episodes, also over failed episodes. The subgoals are the benchmark's pre-defined goal atoms, so every method is scored on the same standard. Subgoals a VLM planner generates itself are logged separately for later analysis and never enter SCR |
| A | **CSR** Constraint Satisfaction Rate | Satisfied / applicable atomic constraints, pooled, overall and per category. Constraints define the *legal result*, never the route: **Success = GoalSatisfied ∧ HardConstraintsSatisfied**. **Goal**: the required end state (`on`, `inside`, `fully_inside`, `on_top_of`, `temperature_at_least`, `wiped`, `stirred`, `covered`, `grouped`, `hand_empty`, and `upright` / `not on_floor` of a target object). **Spatial**: placement and space (`clear_of`, `near_any`, `away_from_edge`, `front_visible`, `count_on_at_least`). **Semantic**: instruction semantics: a legal substitute (`eval_semantics.py`), and decoy destinations (`eval_semantics.DECOYS`: T11 bowl, T12 any container other than the small bin / tray, T19 look-alike bin). When an object's last placement went to a decoy, its failed goal atom is counted as semantic instead of goal: it is the same atom, so Goal Satisfaction and TSR still fail and nothing is counted twice. **Preservation**: no forbidden side effects (`near_start`, `is_closed`, `not heating`, `upright` / `not on_floor` of non-target objects, no floor drop: all hard; no non-goal object displaced > 5 cm: soft; no watched object below 8 cm in any per-call state: soft, trajectory). Environment conditions (an occupied microwave, a bin too small for the car) decide only feasibility; they are never scored and never told to the planner. Using the stove instead of the occupied microwave is a legal success |
| B | **OISR** Oracle-Independent Success Rate | 1 if the episode succeeded and its path matches none of the variant's oracle paths; N/A if the variant has no oracle. Also reported among successes only |
| B | **OPS** Oracle Plan Similarity | LCS(agent path, oracle path) / max(lengths), taking the most similar oracle. Computed both on calls and on skill names only. It describes how far the route differs and never scores success |
| B | **PFR** Planning Failure Rate | Episodes whose primary cause is `planning_failure`, `substitution_failure` or `recovery_failure` (the existing attribution) / valid episodes. Failed episodes are also split into planning / physical / exploration / feasibility / undetermined / system |
| C | **PASR** Proactive Adaptation Success Rate | One opportunity per episode of a variant registered in `eval_adaptation.py` (the 13 v4 Hard variants), or with a registered substitute condition. The adaptation is the first successful call that moves a registered obstacle (`moved`) or puts a registered object on/in a registered destination (`objects`/`destinations`, from the logged support or a measured postcondition). Success = adapted before the first execution or precondition failure **and** the registered local goal holds at the end. Also reports reactive adaptations, adaptations never made, and proactive adaptations whose local goal failed |
| C | **RRSR** Reactive Recovery Success Rate | Eligible: execution and precondition failure events (not observation refusals). Failures of the same call with no successful call in between merge into one event. **Recovered**: the same or an equivalent result is verified later (`local_recovery`, `retry_only`, `mechanism_unverified`, `resolved_by_alternative`), **or the task succeeds in the end by any legal path** (`task_completed`); the agent does not have to follow the reference fallback. Also reports the verified share (state evidence) and the outcomes by resolution |
| C | **FSA** Fallback Selection Accuracy | Decision: the first call after a failure event. The same call again is a blind retry, not a fallback; no call means abandoned. Another call is **valid** if it succeeded and the failure was resolved (locally, by an alternative, or by the finished task), **invalid** if the planner's call was invalid or it ran but the episode never recovered, otherwise undetermined. FSA = valid / (valid + invalid). It measures that the first call after a failure ran and the task was finished in the end; it does **not** certify that the best or the intended alternative skill was chosen |
| C | **RE** Recovery Efficiency | Outcome-based. Per failure event in a successful episode: C*/max(C, C*). C = calls after the failure until the task is finished. C* = calls after the same failing call in the variant's declared fallback route; that route is one feasible reference, not a required way, and a shorter legal path scores 1. Events without a reference report their mean calls; failed episodes report the calls used after an unrecovered failure; the calls until a local recovery are shown separately. RE is computed only for recovered events in successful episodes that have a reference route; **RE coverage** = those events / all recovered events in successful episodes is reported next to it |
| D | **SESR** Skill Execution Success Rate | Verified calls / executed calls. Executed = verified + execution failures (including perception calls that found nothing). Interface errors, precondition refusals and gate refusals form the refusal rate over all calls |
| D | **RTSR** Robust Task Success Rate | Mean over tasks of the mean over variants of the mean over seeds, with a 95 % bootstrap interval (1000 resamples of the seeds in each cell, fixed seed). Also given per task |

The rules are fixed in code, so they are the same for every method:
- **Oracle = one feasible route, not the required one:** TSR, CSR, RRSR, FSA and RE judge the result (goal, constraints, final state). No metric requires the oracle's skills or order; only OISR / OPS describe how far a path is from it.
- **Path:** the successful calls, each as (skill, arguments without `hint*`), with immediate repeats collapsed. The
  variant's oracle set is every nominal / fallback / alternative / explore route declared for it, with its
  expected-failure and unwind steps dropped. Extra `look` or `navigate` calls therefore make a path non-oracle;
  use OPS to see how close it is.
- **Adding a Hard variant:** register its opportunity in `eval_adaptation.py`. Give state evidence (`moved` /
  `objects` + `destinations`) and the `local` goal; never list skill names. Then check that its oracle route scores
  PASR 1 and its negative route 0. Across the 13 current Hard variants, s10 and s11 give 26/26 oracle runs with
  proactive success, and every negative run scores 0.
- `scripted` and `oracle` rows are feasibility evidence, not planner results. Compare methods on the same
  task/variant/seed list.

**Evaluation grid** (`batches/eval.json`, not run yet): 29 task × tier combinations × seeds 10 and 11 gives 58
episodes per planner (fixed, retry, oracle = 174; one more set per `--policy`). T05 easy is the missing 30th
combination.

## Results

<!-- smoke:start -->
Live check of the result fields (`batches/retest_t01_smoke.json`, code of this commit;
`python benchmark/tests/check_live_fields.py benchmark/runs/retest --old benchmark/runs/final`: all checks pass):

| Run | Outcome | What it checks |
|---|---|---|
| T01 nominal, seeds 0, 1 | pass, pass | normal finish; book on the dining table in `final_state` (z 0.868, not held) |
| T01 fallback_expose, seeds 0, 1 | pass, pass | a real execution failure (edge pinch not held) followed by expose + pick; `recov_exec` counts it |
| T01 hard_search_expose, seeds 0, 1 | pass, **fail** | seed 1: the book slips out during `place` and is on the floor; `dropped` and `final_state` (z 0.014) agree. Same result as the earlier run of that seed |
| T01 fixed, seed 2 | fail | failure exit: the nominal pick fails and the plan ends; the book stays on the island |
| T01 oracle, seed 3 | pass | upper-bound runner on the same variant |
| T01 recovery + `BudgetPlanner` (`--max-calls 3`) | fail, `stop_reason: budget` | budget exit after 3 calls |
| T01 recovery + `CrashPlanner` | incomplete | the planner raises; no goal or `final_state` is written; kept out of SR and of every failure count |

The two recovery runs use test planners from `tests/smoke_planners.py`. They check the interface only and are not VLM
recovery results; `report.py` leaves every `recovery` run out of the route evidence. In all completed runs
`sim_ticks` is at least the last call's tick + 60 (the settle) and `sim_s = sim_ticks / 120`. The 113 old runs in
`runs/final` have no `final_state` or `sim_ticks`; `evaluate.py` still reads them and falls back to the last call's
state.
<!-- smoke:end -->

## Changes to existing code

All changes are behind flags; the skill library's defaults are unchanged except two local fixes, and the
*Regression* section checks those: the open-hand clear after a failed top pinch (`skills.py`) and the closed-loop
`lift` (`policies/navigation.py`). The benchmark sets its flags in `run_episode.py` and `observation.py`.

| File | Change |
|---|---|
| `zeno_skills/perception.py` | `dynamic_occluder()`; used by `project_to_head_camera` only when `rig.occlusion` |
| `zeno_skills/skill_runtime.py` | `SkillContractRunner(auto_repair=True, advisory=(), skip_steps=None)` |
| `zeno_skills/skills.py` | `rig.auto_recovery` (default True): pick → push fallback, slide-to-edge inside `pick_flat`, door retry from another park; `_edge_pinch(attempt=)`. `rig.edge_pinch_upright_waist` (default False; the benchmark sets it): at table height the edge pinch keeps the waist ≤ 0.2 rad, as `_pick_pinch` does; without it the chest stalled against the island edge in 4/4 direct paperback picks. A failed top pinch ends with the hand open and 8 cm higher; fingers left closed beside a crowding bowl stopped at 5 mm, and the next push could not make its fist (3/4) |
| `zeno_skills/policies/navigation.py` | `lift` (carry_height_adjust) repeats the vertical move on the measured object bottom, up to 3 times while the object keeps rising: a rolling pin caught in a mug after a failed place lagged the hand by 4-5 cm and one move fell short (4/4); the verifier (bottom >= target - 2 cm) is unchanged |
| `zeno_skills/policies/perceive.py` | `rig.static_explore`: explore_room coverage over static furniture only; `rig.observer` hook in `record_view` |

## Regression

Full run of the skill library's 35 scenarios on this branch (`tools/verify_skills.py --all --jobs 2`, 2026-10-18,
code with the edge-pinch flag), compared with `skill_library/verification/status.json`:

| Class | Scenarios |
|---|---|
| Passed before, still pass (27) | b_books, c_approach_moving, c_tray_moving, g_expose_then_pick_book, g_heat_on_stove_instead_of_microwave, g_search_then_fetch, k_blocks, k_body, k_book, k_bottle, k_brace, k_cabinet, k_fetch_collect, k_floor, k_handle_mug, k_hands, k_mug_on_burner, k_perceive, k_pin, k_posture, k_present, k_stir_cover, k_sweep, k_trash, k_wipe, o_clear, t_floor_moving |
| Failed before, still fail at the same step (6) | k_arrange_sort (sort, step 1), k_empty_hide (empty, step 2), k_fridge_chill (place in fridge, step 5), k_microwave (place oatmeal, step 12), k_soup_stove (pour, step 6), r_bimanual_box (two-hand lift, step 1) |
| Fail here, `status.json` says pass, and a clean 15d948e worktree fails identically (2) | k_separate (separate precondition `not grasp_clearance` false; same 52-event stream), k_restore_swap (soda can slips during swap's buffer `place_above` on the island; same 226-event stream). `status.json` predates 15d948e; these are failures of the 15d948e baseline, not of this branch |
| New failures | none |
| Incomplete | none |

`g_expose_then_pick_book` failed in an earlier regression run when the upright edge-pinch waist was on by default
(the park moved from 8.20 to 8.34 and the book fell off the bookcase). The waist is now opt-in
(`rig.edge_pinch_upright_waist`, set only by the benchmark); the scenario passes with the baseline trajectory and the
book on the bookcase `top`. Repeats on the current code: g_expose_then_pick_book 3/3 pass; k_separate 2/2 and
k_restore_swap 2/2 fail at the same step; the clean worktree fails k_restore_swap 2/2 the same way.

## Known limitations

- **No real VLM run yet.** The closed loop is checked only with test planners.
- **The eval grid (`batches/eval.json`, 174 episodes) has not been run.** The baseline numbers in
  [EVALUATION.md](EVALUATION.md) come from one or two seeds per task and are not benchmark results.
- **Evidence code version.** The full acceptance was rerun on `10b08a4` (clean tree, `benchmark/runs/v2`, 117
  episodes). The two T01 nominal episodes ran first on `6abdb93` plus the uncommitted diff that became `10b08a4`
  (identical code, a different recorded version). RESULTS.md shows the code version per route.
- **Route stability.** All 29 declared routes passed on both seeds (60/60). T02 `fallback_push` is diagnostic (it
  passes, 2/2, but is not an acceptance route); T05's pen variant (the pen slips while carried, 2/2 again) and T06
  `fallback_clear` (the oatmeal bowl cannot be picked during clear_support, 2/2) are diagnostic failures.
- **Baselines (one seed each, not benchmark results):** the oracle failed T02 crowded on seed 3 (the block slipped
  out on the pick after `separate`); the scripted route passed on seeds 0 and 1.
- **Probes:** 14 of 21 pass. P04 bottle (slips during upright), P06 two hands, P07 present and brace (the left
  fingers close on nothing), P09 sweep (a block falls), P14 restore swap (place inside swap), P16 empty (tomato not
  grasped) and P17 pour (0/3 items reach the pot) fail.
- **SkillNodes:** 64 of 70 succeeded in a real call. Five were called and only failed (brace, upright, pour, empty,
  swap; swap passed in the previous round) and `release` was never called (see [coverage.json](coverage.json)). Do
  not read this as "all 70 skills are stable".
- **Library baseline failures:** 8 of the 35 library scenarios fail (see *Regression*), among them k_separate and
  k_restore_swap, which also fail on a clean 15d948e.
- `inspect` of a closed cabinet sees nothing inside until the door is opened.
