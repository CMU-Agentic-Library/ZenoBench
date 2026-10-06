---
name: upright-a-held-object
description: Rotate a right-held object until its local up axis is within 20 degrees of vertical.
---

# Upright a held object (skill_036)

## When to use

Rotate a right-held object until its local up axis is within 20 degrees of vertical.

## Inputs

- `object` (`object_ref`): The uniquely grounded scene object.

## Preconditions

- `held_by_right_hand` — `policy_attempt`

## Planner action predicate

`orient_held_object(object)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['object_upright']`.

## Expected state change

- `object_upright` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_036` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_044", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_054(object, max_tilt_deg=20.0)`


Verifier: `upright`.

## Related Skills

- `skill_037` (`preparation`) when a held object must be placed upright — The combined placement Contract checks upright again after release.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One upright a held object attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
