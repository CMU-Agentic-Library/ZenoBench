---
name: skill_013
description: Move the waist to one requested pitch angle in radians.
---

# skill_013 — Set waist pitch

## When to use

Move the waist to one requested pitch angle in radians.

## Inputs

- `pitch_rad` (`number`): pitch rad

## Preconditions

- `right_hand_empty` — `policy_attempt`
- `target_within_joint_limits` — `policy_attempt`
- `collision_free_motion` — `policy_attempt`

## Expected state change

- `posture_at_target` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_013` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_021", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):


### Policy path: fixed

Match before execution: `[]`.

1. `policy_007(pitch_rad)`


Verifier: `contract_008 / waist`.

## Related Skills

- No fixed relation; select the next node from the task goal and observation.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one waist pitch adjustment

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
