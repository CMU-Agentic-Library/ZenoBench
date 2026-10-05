---
name: skill_014
description: Release one right-held object onto the annotated microwave cavity support.
---

# skill_014 — Place an object on the microwave cavity support

## When to use

Release one right-held object onto the annotated microwave cavity support.

## Inputs

- `object` (`object_ref`): object
- `support` (`microwave_support_ref`): Annotated microwave cavity support.

## Preconditions

- `held_by_right_hand` — `contract_precheck`
- `target_annotated` — `policy_attempt`
- `target_accessible` — `policy_attempt`

## Expected state change

- `on` — measured by `contract_runner`
- `right_hand_empty` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_014` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_022", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True, 'furniture_equals': 'kitchen_microwave'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_018(object, support)`
2. `policy_019(object)`
3. `policy_020(object)`


Verifier: `contract_003 / microwave`.

## Related Skills

- `skill_024` (`follows`) when microwave food is loaded and heating is next — The door must be closed before the start button can heat food.
- May follow `skill_023` (`enables`) when microwave cavity must be opened before loading.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one microwave support placement

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
