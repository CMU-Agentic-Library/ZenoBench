# ZenoBench planning benchmark (observation-limited)

A small benchmark for an upper-level planner (a VLM) on top of the existing 70 SkillNodes. Every planner gets the same
low-level skills and the same observation limits. The question is whether the planner chooses an effective fallback
or alternative from what it sees and from the execution feedback. The Isaac Sim GT verifier decides success; the
planner never sees GT state.

<!-- results:start -->
Declared task routes: **59/62** episodes pass (30 routes: 3 flaky, 27 stable); probes 14/21; baselines fixed 2/10, retry 2/10, oracle 9/10; SkillNode coverage **65/70** (4 called but failed, 1 never called).  Per route and seed: [RESULTS.md](RESULTS.md); per skill: [coverage.json](coverage.json).
<!-- results:end -->

## Observation boundary

`benchmark/session.py: LimitedSession` is the only entry point for planners.

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
* explore picks viewpoints from the static layout and computes coverage over
  static supports only (`rig.static_explore`).

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
(`benchmark/planners.py`). `observation` is `LimitedSession.observe()`, which holds:
- the first-person image path;
- the visible objects and the observation cache;
- the known places;
- the robot state (pose, room, hands, known temperatures);
- the last call's feedback.

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
| `zeno_skills/policies/perceive.py` | `rig.static_explore`: explore coverage over static supports only; `rig.observer` hook in `record_view` |

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
book on bookcase `surface_3`. Repeats on the current code: g_expose_then_pick_book 3/3 pass; k_separate 2/2 and
k_restore_swap 2/2 fail at the same step; the clean worktree fails k_restore_swap 2/2 the same way.

## Known limitations

- **No real VLM run yet.** The closed loop is checked only with test planners.
- **The eval grid (`batches/eval.json`, 174 episodes) has not been run.** The baseline numbers in
  [EVALUATION.md](EVALUATION.md) come from one or two seeds per task and are not benchmark results.
- **Evidence code versions.** 105 of the 113 route episodes ran on `15d948e+dc4ae8f`, before this round's changes.
  For the benchmark the low-level behaviour is meant to be the same (it sets the upright edge-pinch flag, which was the
  default then), but only T01 was rerun on the current code. RESULTS.md shows the code version per route.
- **Flaky routes (pass on one seed, fail on the other):** T01 hard_search_expose (the book slips during place on
  seed 1), T02 fallback_separate and T02 hard_search_separate (the stack after `separate`). The T05 pen variant is diagnostic only (the pen
  slips 4/4), which is why T05 has no easy tier.
- **Probes:** 14 of 21 pass. P04 bottle, P06 two hands, P07 present and brace, P09 sweep, P14 restore swap, P16 empty
  and P17 pour fail.
- **SkillNodes:** 65 of 70 succeeded in a real call. Four were called and failed, and `release` was never called
  (see [coverage.json](coverage.json)). Do not read this as "all 70 skills are stable".
- **Library baseline failures:** 8 of the 35 library scenarios fail (see *Regression*), among them k_separate and
  k_restore_swap, which also fail on a clean 15d948e.
- `inspect` of a closed cabinet sees nothing inside until the door is opened.
