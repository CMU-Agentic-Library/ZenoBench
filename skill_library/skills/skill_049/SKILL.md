---
name: ready-floor-reach
description: Lower and lean toward a floor object, then verify a fresh reachable pregrasp.
---

# Ready floor reach (skill_049)

## When to use

Lower and lean toward a floor object, then verify a fresh reachable pregrasp.

## Inputs

- `object` (`object_ref`): The uniquely grounded scene object.

## Preconditions

- `right_hand_empty` — `policy_attempt`
- `object_on_floor` — `policy_attempt`
- `pregrasp_reachable` — `policy_attempt`

## Planner action predicate

`ready_floor_object(object)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['floor_reach_ready']`.

## Expected state change

- `floor_reach_ready` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_049` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_057", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_042(object)`


Verifier: `floor_reach`.

## Related Skills

- `skill_020` (`preparation`) when a floor item has a verified pregrasp and corner pick is appropriate — Prepared arm pose can precede the floor-corner grasp.
- May follow `skill_001` (`preparation`) when floor target is beyond the current arm reach.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.
- Conditional fallback `skill_001` when floor pregrasp is unreachable from the current base pose and the right hand is empty: Move to a safe pose near the floor target, then retry floor pregrasp.

## Scope and evidence

One ready floor reach attempt on grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
