---
name: skill_021
description: Move a currently two-hand-held object to one base pose.
---

# skill_021 — Carry a large object with both hands

## When to use

Move a currently two-hand-held object to one base pose.

## Inputs

- `object` (`object_ref`): object
- `pose` (`pose2d`): pose

## Preconditions

- `target_navigable` — `policy_attempt`
- `carried_object_matches_state` — `not_enforced`
- `two_hand_hold` — `not_enforced`

## Expected state change

- `base_at` — measured by `contract_runner`
- `grasp_preserved` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_021` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_029", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_058(object, pose)`


Verifier: `contract_001 / two_hand_carry`.

## Related Skills

- No fixed relation; select the next node from the task goal and observation.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one two-hand carry move

Availability: `experimental_callable`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
