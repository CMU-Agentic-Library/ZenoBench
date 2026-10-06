---
name: tuck-the-right-arm
description: Move the right arm into the measured travel posture.
---

# Tuck the right arm (skill_011)

## When to use

Move the right arm into the measured travel posture.

## Inputs

- None.

## Preconditions

- `right_hand_empty` — `policy_attempt`
- `target_within_joint_limits` — `policy_attempt`
- `collision_free_motion` — `policy_attempt`

## Planner action predicate

`tuck_right_arm()` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['posture_at_target']`.

## Expected state change

- `posture_at_target` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_011` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_019", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):


### Policy path: fixed

Match before execution: `[]`.

1. `policy_003()`


Verifier: `contract_008 / tuck`.

## Related Skills

- `skill_043` (`preparation`) when after arm tucking and a local orientation correction is needed — Tucked arm allows a direct local base turn.
- `skill_044` (`preparation`) when after arm tucking and a short straight reposition is needed — Tucked arm allows a direct local translation.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one arm tuck

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
