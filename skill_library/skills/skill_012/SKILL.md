---
name: set-torso-height
description: Move the torso lift to one requested joint height.
---

# Set torso height (skill_012)

## When to use

Move the torso lift to one requested joint height.

## Inputs

- `height_m` (`number`): height m

## Preconditions

- `right_hand_empty` — `policy_attempt`
- `target_within_joint_limits` — `policy_attempt`
- `collision_free_motion` — `policy_attempt`

## Planner action predicate

`set_torso_height(height_m)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['posture_at_target']`.

## Expected state change

- `posture_at_target` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_012` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_020", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):


### Policy path: fixed

Match before execution: `[]`.

1. `policy_004(height_m)`


Verifier: `contract_008 / torso`.

## Related Skills

- No fixed relation; select the next node from the task goal and observation.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one torso lift adjustment

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
