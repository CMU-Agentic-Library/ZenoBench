---
name: skill_008
description: Move one object by directed contact and measure progress.
---

# skill_008 — Push an object along a support

## When to use

Move one object by directed contact and measure progress.

## Inputs

- `object` (`object_ref`): object
- `support` (`support_ref`): support
- `direction_xy` (`unit_vec2`): direction xy
- `distance_m` (`positive_number`): distance m

## Preconditions

- `right_hand_empty` — `contract_precheck`
- `object_on_support` — `policy_attempt`

## Expected state change

- `displacement_along` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_008` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_016", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_026(object, support, direction_xy, distance_m)`


Verifier: `contract_006 / auto`.

## Related Skills

- No fixed relation; select the next node from the task goal and observation.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one directed contact move

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
