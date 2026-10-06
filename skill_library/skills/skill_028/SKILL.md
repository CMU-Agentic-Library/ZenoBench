---
name: pick-by-round-rim
description: Grasp a bowl or cup by its annotated round rim.
---

# Pick by round rim (skill_028)

## When to use

Grasp a bowl or cup by its annotated round rim.

## Inputs

- `object` (`object_ref`): The uniquely grounded scene object.

## Preconditions

- `right_hand_empty` — `contract_precheck`
- `target_annotated` — `policy_attempt`

## Planner action predicate

`grasp_round_rim(object)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['held_by_right_hand', 'object_lifted']`.

## Expected state change

- `held_by_right_hand` — measured by `contract_runner`
- `object_lifted` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_028` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_036", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_grasp_type': 'rim_pinch'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_011(object)`


Verifier: `contract_002 / round_rim`.

## Related Skills

- `skill_037` (`enables`) when a rim-grasped vessel must end upright on a support — Orient and place the held vessel.
- `skill_017` (`alternative`) when round-rim grasp fails and the cup has an annotated handle — Handle grasp is a distinct physical strategy.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One pick by round rim attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
