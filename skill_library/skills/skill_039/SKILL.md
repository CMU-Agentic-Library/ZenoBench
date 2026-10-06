---
name: place-an-upright-object-near-a-support-hint
description: Orient and place a held object near a supplied xy hint, then verify both.
---

# Place an upright object near a support hint (skill_039)

## When to use

Orient and place a held object near a supplied xy hint, then verify both.

## Inputs

- `object` (`object_ref`): The uniquely grounded scene object.
- `support` (`support_ref`): The grounded target support.
- `hint_xy` (`xy`): Desired [x_m,y_m] point on the support.
- `max_offset_m` (`positive_number`): Maximum final xy distance from hint in metres.

## Preconditions

- `held_by_right_hand` — `contract_precheck`
- `target_annotated` — `policy_attempt`

## Planner action predicate

`align_upright_object_near_hint(object, support, hint_xy, max_offset_m)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['on', 'right_hand_empty', 'object_upright', 'within_hint_radius']`.

## Expected state change

- `on` — measured by `contract_runner`
- `right_hand_empty` — measured by `contract_runner`
- `object_upright` — measured by `contract_runner`
- `within_hint_radius` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_039` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_047", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_054(object, max_tilt_deg=20.0)`
2. `policy_015(object, support, hint=hint_xy)`


Verifier: `contract_003 / surface` plus `upright, within_hint`.

## Related Skills

- May follow `skill_004` (`enables`) when the task requires both upright and near-hint placement.
- May follow `skill_038` (`alternative`) when the task also requires upright after release.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One place an upright object near a support hint attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
