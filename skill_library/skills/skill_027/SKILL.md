---
name: pick-by-top-pinch
description: Grasp an annotated object from its top pinch region.
---

# Pick by top pinch (skill_027)

## When to use

Grasp an annotated object from its top pinch region.

## Inputs

- `object` (`object_ref`): The uniquely grounded scene object.

## Preconditions

- `right_hand_empty` — `contract_precheck`
- `target_annotated` — `policy_attempt`

## Planner action predicate

`clamp_object_top(object)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['held_by_right_hand', 'object_lifted']`.

## Expected state change

- `held_by_right_hand` — measured by `contract_runner`
- `object_lifted` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_027` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_035", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_grasp_type': 'top_pinch'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_010(object)`


Verifier: `contract_002 / top`.

## Related Skills

- `skill_005` (`enables`) when an object was top-pinched for transfer — Place uses the successful right-hand grasp.
- `skill_004` (`alternative`) when top pinch geometry is absent or fails but another grasp exists — The general dispatcher can select another annotated grasp.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One pick by top pinch attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
