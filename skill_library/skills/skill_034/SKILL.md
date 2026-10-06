---
name: straighten-waist
description: Return the waist pitch to neutral.
---

# Straighten waist (skill_034)

## When to use

Return the waist pitch to neutral.

## Inputs

- None.

## Preconditions

- `joint_path_clear` — `policy_attempt`

## Planner action predicate

`straighten_waist()` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['posture_at_target']`.

## Expected state change

- `posture_at_target` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_034` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_042", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):


### Policy path: fixed

Match before execution: `[]`.

1. `policy_009()`


Verifier: `contract_008 / straighten`.

## Related Skills

- No fixed relation; select the next node from the task goal and observation.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One straighten waist attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
