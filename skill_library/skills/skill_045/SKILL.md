---
name: nudge-object-from-behind
description: Push an object from rear contact along its annotated support and measure progress.
---

# Nudge object from behind (skill_045)

## When to use

Push an object from rear contact along its annotated support and measure progress.

## Inputs

- `object` (`object_ref`): object
- `support` (`support_ref`): support
- `direction_xy` (`unit_vec2`): direction xy
- `distance_m` (`positive_number`): distance m

## Preconditions

- `right_hand_empty` — `contract_precheck`
- `object_on_support` — `policy_attempt`

## Planner action predicate

`nudge_supported_object(object, support, direction_xy, distance_m)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['displacement_along']`.

## Expected state change

- `displacement_along` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_045` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_053", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_043(object, support, direction_xy, distance_m)`


Verifier: `contract_006 / auto`.

## Related Skills

- `skill_035` (`recovery`) when rear contact could not make required progress on a flat object — Slide to edge offers an alternate flat-object contact route.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One nudge object from behind attempt on grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
