---
name: lower-torso-for-floor-reach
description: Lower the robot torso to its configured minimum before floor interaction.
---

# Lower torso for floor reach (skill_031)

## When to use

Lower the robot torso to its configured minimum before floor interaction.

## Inputs

- None.

## Preconditions

- `joint_path_clear` — `policy_attempt`

## Planner action predicate

`lower_torso()` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['posture_at_target']`.

## Expected state change

- `posture_at_target` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_031` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_039", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):


### Policy path: fixed

Match before execution: `[]`.

1. `policy_005()`


Verifier: `contract_008 / lower`.

## Related Skills

- `skill_020` (`preparation`) when a flat object lies on the floor and is hard to reach — Lowering the torso can improve floor reach.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One lower torso for floor reach attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
