---
name: skill_011
description: Move the right arm into the measured travel posture.
---

# skill_011 — Tuck the right arm

## When to use

Move the right arm into the measured travel posture.

## Inputs

- None.

## Preconditions

- `right_hand_empty` — `policy_attempt`
- `target_within_joint_limits` — `policy_attempt`
- `collision_free_motion` — `policy_attempt`

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

- No fixed relation; select the next node from the task goal and observation.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one arm tuck

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
