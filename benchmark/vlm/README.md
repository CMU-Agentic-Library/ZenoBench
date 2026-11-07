# VLM planner: the closed loop

Scene -> head-camera image + instruction -> VLM -> one skill call -> execution -> ... -> goal check -> logs.

```bash
# one or more episodes, each in its own Isaac process, with a summary table
$ISAACLAB_PYTHON benchmark/vlm/run_vlm.py --episodes T09_tomato_soup:x6_gd_tomato_elsewhere:10 --backend replay
$ISAACLAB_PYTHON benchmark/vlm/run_vlm.py --episodes T21_bring_tissues:tissue_or_sponge:10-12 --backend claude

# a single episode, directly
VLM_BACKEND=claude $ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json \
    --task T30_bowls_for_soup --variant bowl_on_cabinet --seed 10 \
    --planner recovery --policy benchmark.vlm.planner:VLMPlanner
```

An episode is `task:variant:seed` (a v6 variant id; the seed picks the layout from the variant's seed manifest,
`10-12` is a range). The default profile is `benchmark` (observation gate, masked feedback, no automatic repair);
`--profile sticky_snap/benchmark` completes failed grasps and placements for developing a planner (never for
scoring).

## Pieces

| | |
|---|---|
| `planner.py` `VLMPlanner` | run_episode's `recovery` Planner. Each step: one user turn with the camera image(s), the visible objects, objects seen before, the known places (first turn), the robot state and the last call's result; the backend's reply is parsed into `{"skill", "args"}` or "done". An invalid reply (no JSON, unknown skill or argument, missing argument) goes back to the model with the reason, at most `VLM_MAX_REPAIRS` (2) times; then the episode stops with `stop_reason: planner_error`. Images of older turns are dropped (`VLM_KEEP_IMAGES`, 2); the text history stays. |
| backends (`VLM_BACKEND`) | `replay`: a stand-in that answers with a fixed call list (`VLM_REPLAY`; run_vlm.py writes the layout's oracle route) - a pipeline test, not a planner result. `claude`: the Anthropic SDK, `VLM_MODEL` (default `claude-opus-5-5`), `VLM_EFFORT` (default `medium`), server-side refusal fallback on; needs `pip install anthropic` and a key; not exercised yet. Another model: a class with `decide(system, messages) -> str`, added to `BACKENDS`. |
| `run_vlm.py` | runs the episodes one at a time and writes `vlm_summary.json` / `vlm_summary.md`: success, stop reason, calls, failed calls, goal atoms that did not hold, invalid replies, wall time. |
| `benchmark/run_episode.py` | the loop itself: builds the Episode, gives the planner the instruction, the skill menu (the built-in skills when the catalog has none) and the observation each step, executes the call, checks the goal, writes `result.json` and `calls.jsonl`. |

What the planner never gets: the variant, the goal, the oracle route, GT positions of objects it has not seen.

## Output per episode

`<out>/<task>/s<seed>_<layout>_recovery-VLMPlanner[@profile]/`:

* `result.json` - `success` (the goal on the final GT state), `goal` (every atom, true or false, with detail),
  `stop_reason` (`planner_done`, `planner_error`, `budget`), the calls with feedback and GT state before/after;
* `calls.jsonl` - one row per executed call;
* `vlm_steps.jsonl` - per model reply: the text given, the image paths, the raw reply, parsed call or error, seconds;
* `images/` - the head-camera image of every step.

## Status

* The loop runs end to end in Isaac (2026-11-06): T09 `x6_gd_tomato_elsewhere` seed 10, replay backend, physical
  `benchmark` profile: 19 calls, goal reached, logs complete. T30 `bowl_on_cabinet` seed 10 under
  `sticky_snap/benchmark` runs too but fails: after a snap the gripper command stays shut, the fingers close to 0
  while carrying, and `place` then reads `holding` as false (zeno_skills/sticky.py; reported to the skill owner).
* `tests/test_planner.py` (no Isaac): prompt building, parsing, repairs, giving up, the step log, image trimming.
* No model has been run through it yet; the `claude` backend is written against the SDK documentation only.
