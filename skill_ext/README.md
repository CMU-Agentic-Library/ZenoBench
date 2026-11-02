# Extensible skills (ZenoBench v5)

User-defined skills next to the fixed SkillNode library. The library, its Contracts, its GT policies
and the GT oracle are read here and never changed.

## Two tracks

| Track | Skills | Use |
|---|---|---|
| **Fixed-Skill** (`--track fixed`, default) | the 71 built-in SkillNodes (`contract_library/skill_contracts.json`) | planner comparison; identical to v3/v4 runs (no code path changes) |
| **Open-Skill** (`--track open --skills DIR`) | built-ins + every `DIR/*/SKILL.md` | bring your own skill: VLA, RL, scripted policy, or a composite of built-ins |

A run records `config.json: skill_track` with the skill directories, the user skills and a
fingerprint of the skill set (contract library hash + every SKILL.md hash), so Open-Skill results
are never mixed with Fixed-Skill results.

```bash
$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v5/tasks.json --task T01_book_to_dining_table \
    --variant e1_nominal --planner recovery --policy my_planner:Planner --track open --skills skill_ext/examples
```

## SKILL.md

YAML front matter = the spec (validated against [`skill.schema.json`](skill.schema.json)); the body
is free documentation.

```yaml
---
name: deliver                          # the verb; may not shadow a built-in
description: Carry one object to a support and put it down there.
parameters:
  object: {type: object_ref, required: true}
  support: {type: support_ref, required: true}
preconditions: [hand_empty(hand=right)]                     # GT predicates, checked before
effects: ["on(object=$object, support=$support)"]           # expected effects, checked after
executor:
  type: scripted                       # scripted | python | vla | rl | scripted_policy
  steps:
    - {skill: pick, args: {object: $object}}
    - {skill: navigate, args: {destination: $support}}
    - {skill: place, args: {object: $object, support: $support}}
---
```

* **Preconditions / effects** use the same GT predicates as the built-in Contracts
  (`zeno_skills.predicates`) and the goal verifiers (`episode/goal_predicates.py`), with `$param`
  references. A false precondition refuses the call (`PRECONDITION_FAILED`); a false effect fails it
  (`POSTCONDITION_FAILED`).
* **Executors** (`executors.py`):
  * `scripted`: built-in or user skill calls; each nested call is gated and verified as a top-level one.
  * `python`: `entry: file.py:func` (`func(ctx, **args)`) or a class with `run(ctx, args)`.
  * `vla` / `rl` / `scripted_policy`: `entry: file.py:Policy` with `reset(instruction, args)` and
    `act(observation) -> action`, run for at most `max_steps` through the action interface
    (`actions.py`): `ee_delta` (≤ 3 cm per step, cuRobo-checked motion), `joint_delta`, or `skill_calls`.
    The observation contains only what the episode profile shows a planner (`images`, `robot`,
    `visible_objects`) plus `proprio` and `instruction`; GT poses only for `privileged: true` baselines.
* **Validation** (at load time, all problems at once): schema, name pattern, no built-in shadowing,
  known predicates, declared `$params`, executor entry importable, scripted steps resolvable, no call
  cycles between user skills.
* **Registry** (`registry.py`): `SkillRegistry.default()`, `load_dir`, `register`, `reload`,
  `unregister` (user skills only), `menu(track)` (planner view, never the executor), `fingerprint`.

Examples in [`examples/`](examples): `deliver` (scripted composite), `raise_held` (scripted
closed-loop policy), `rl_raise_held` (linear RL policy from a weights file), `vla_raise_held` (VLA
adapter; `backend: mock` or `http`).

Tests: `python -m pytest -q skill_ext/tests` (no simulator; a fake runner and fake predicates).
