---
name: skill_005
description: Release one right-held object onto one annotated support.
---

# skill_005 — Place an object on a support

## When to use

Release one right-held object onto one annotated support.

## Inputs

- `object` (`object_ref`): object
- `support` (`support_ref`): support

## Preconditions

- `held_by_right_hand` — `contract_precheck`
- `target_annotated` — `policy_attempt`
- `target_accessible` — `policy_attempt`

## Expected state change

- `on` — measured by `contract_runner`
- `right_hand_empty` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_005` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_013", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: microwave_support

Match before execution: `[{'noun': 'support', 'field': 'furniture', 'equals': 'kitchen_microwave'}]`.

1. `policy_018(object, support)`
2. `policy_019(object)`
3. `policy_020(object)`

### Policy path: edge_held

Match before execution: `[{'noun': 'object', 'field': 'held_kind', 'equals': 'edge'}]`.

1. `policy_017(object, support)`

### Policy path: ordinary_surface

Match before execution: `[{'noun': 'support', 'field': 'kind', 'equals': 'support'}]`.

1. `policy_015(object, support)`


Verifier: `contract_003 / surface`.

## Related Skills

- `skill_030` (`alternative`) when the object is edge-held and surface place is unsuitable — Use the edge-specific place policy.
- `skill_007` (`follows`) when manipulation used an articulated compartment and the task requires closed doors — Close the relevant compartment after manipulation.
- May follow `skill_004` (`enables`) when the task requires the grasped object on a support.
- May follow `skill_027` (`enables`) when an object was top-pinched for transfer.
- May follow `skill_020` (`enables`) when a floor object was lifted and needs a support.
- May follow `skill_019` (`recovery`) when moving place failed and the object remains right-held.
- May follow `skill_006` (`alternative`) when the chosen container is unavailable but the task permits a support destination.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one surface placement

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
