---
name: place-an-object-in-a-container
description: Release a right-held object into an annotated container and verify the final geometry.
---

# Place an object in a container (skill_006)

## When to use

Release a right-held object into an annotated container and verify the final geometry.

## Inputs

- `object` (`object_ref`): The held object to place.
- `container` (`container_ref`): The target container.

## Preconditions

- `held_by_right_hand` — `contract_precheck`
- `container_annotated` — `contract_noun_binding`
- `container_accessible` — `policy_attempt`

## Planner action predicate

`insert_object_in_container(object, container)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['inside', 'right_hand_empty']`.

## Expected state change

- `inside` — measured by `contract_runner`
- `right_hand_empty` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_006` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_014", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`
- `container`: `container`; constraints `{'source': 'rig.ann', 'required': True, 'required_annotation': 'asset.container'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_016(object, container)`


Verifier: `contract_003 / container`.

## Related Skills

- `skill_005` (`alternative`) when the chosen container is unavailable but the task permits a support destination — Replan the semantic goal; do not silently weaken an inside requirement.
- `skill_007` (`follows`) when container placement used an articulated compartment and the task requires closed doors — Close the relevant compartment after placement.
- May follow `skill_004` (`enables`) when the task requires the grasped object inside a container.
- May follow `skill_029` (`enables`) when a rectangular-rim container was grasped for relocation.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one planner-visible place-in-container attempt

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: placing on a bare support surface
- Outside scope: choosing another container when this one is missing
- Outside scope: checking the entire task goal
