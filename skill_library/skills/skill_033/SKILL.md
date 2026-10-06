---
name: lean-waist-forward
description: Lean the waist forward to its configured safe posture.
---

# Lean waist forward (skill_033)

## When to use

Lean the waist forward to its configured safe posture.

## Inputs

- None.

## Preconditions

- `joint_path_clear` — `policy_attempt`

## Planner action predicate

`lean_waist()` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['posture_at_target']`.

## Expected state change

- `posture_at_target` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_033` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_041", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):


### Policy path: fixed

Match before execution: `[]`.

1. `policy_008()`


Verifier: `contract_008 / lean`.

## Related Skills

- No fixed relation; select the next node from the task goal and observation.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One lean waist forward attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
