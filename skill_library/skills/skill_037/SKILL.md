---
name: skill_037
description: Orient a held object, place it on a support, then verify support and tilt.
---

# skill_037 — Place an object upright on a support

## When to use

Orient a held object, place it on a support, then verify support and tilt.

## Inputs

- `object` (`object_ref`): The uniquely grounded scene object.
- `support` (`support_ref`): The grounded target support.

## Preconditions

- `held_by_right_hand` — `contract_precheck`
- `target_annotated` — `policy_attempt`

## Expected state change

- `on` — measured by `contract_runner`
- `right_hand_empty` — measured by `contract_runner`
- `object_upright` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_037` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_045", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_054(object, max_tilt_deg=20.0)`
2. `policy_015(object, support)`


Verifier: `contract_003 / surface` plus `upright`.

## Related Skills

- `skill_038` (`alternative`) when the task needs near placement but upright is already satisfied or unnecessary — Use the proximity-specific contract when orientation is not part of the goal.
- May follow `skill_015` (`follows`) when retrieved food must be served upright.
- May follow `skill_004` (`enables`) when the task requires the object upright on a support.
- May follow `skill_028` (`enables`) when a rim-grasped vessel must end upright on a support.
- May follow `skill_036` (`preparation`) when a held object must be placed upright.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One place an object upright on a support attempt on the grounded scene state.

Availability: `experimental_callable`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
