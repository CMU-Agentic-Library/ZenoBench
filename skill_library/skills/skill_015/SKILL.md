---
name: pick-an-object-from-a-cavity
description: Attempt one right-hand cavity retrieval and verify grasp and lift.
---

# Pick an object from a cavity (skill_015)

## When to use

Attempt one right-hand cavity retrieval and verify grasp and lift.

## Inputs

- `object` (`object_ref`): object
- `cavity` (`appliance_ref`): The annotated microwave cavity appliance.

## Preconditions

- `right_hand_empty` — `contract_precheck`
- `object_annotated` — `policy_attempt`
- `object_reachable` — `policy_attempt`

## Planner action predicate

`retrieve_cavity_object(object, cavity)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['held_by_right_hand', 'object_lifted']`.

## Expected state change

- `held_by_right_hand` — measured by `contract_runner`
- `object_lifted` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_015` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_023", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`
- `cavity`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'category_equals': 'microwave', 'required_annotation': 'cavity_aabb'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_048(object, cavity)`


Verifier: `contract_002 / cavity`.

## Related Skills

- `skill_037` (`follows`) when retrieved food must be served upright — Place the still-held item and verify support and tilt.
- May follow `skill_023` (`enables`) when food must be retrieved from a closed microwave.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one cavity-route pick

Availability: `experimental_callable`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
