---
name: skill_022
description: Open one annotated door while preserving an existing left-hand hold.
---

# skill_022 — Open a door while the left hand holds an object

## When to use

Open one annotated door while preserving an existing left-hand hold.

## Inputs

- `object` (`object_ref`): object
- `articulated` (`articulated_ref`): articulated

## Preconditions

- `articulated_annotated` — `contract_precheck`
- `opening_route_feasible` — `policy_attempt`
- `held_by_left_hand` — `not_enforced`

## Expected state change

- `joint_open_enough` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_022` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_030", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`
- `articulated`: `articulated`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_060(object, articulated)`


Verifier: `contract_004 / while_left_holds`.

## Related Skills

- No fixed relation; select the next node from the task goal and observation.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one left-hold opening

Availability: `experimental_callable`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
