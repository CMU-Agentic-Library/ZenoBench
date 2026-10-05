---
name: skill_038
description: Place a held object near a supplied xy hint and verify the final offset.
---

# skill_038 — Place an object near a support hint

## When to use

Place a held object near a supplied xy hint and verify the final offset.

## Inputs

- `object` (`object_ref`): The uniquely grounded scene object.
- `support` (`support_ref`): The grounded target support.
- `hint_xy` (`xy`): Desired [x_m,y_m] point on the support.
- `max_offset_m` (`positive_number`): Maximum final xy distance from hint in metres.

## Preconditions

- `held_by_right_hand` — `contract_precheck`
- `target_annotated` — `policy_attempt`

## Expected state change

- `on` — measured by `contract_runner`
- `right_hand_empty` — measured by `contract_runner`
- `within_hint_radius` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_038` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_046", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_015(object, support, hint=hint_xy)`


Verifier: `contract_003 / surface` plus `within_hint`.

## Related Skills

- `skill_039` (`alternative`) when the task also requires upright after release — Use the combined contract with both final checks.
- May follow `skill_004` (`enables`) when the task requires a target area on a support.
- May follow `skill_037` (`alternative`) when the task needs near placement but upright is already satisfied or unnecessary.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One place an object near a support hint attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
