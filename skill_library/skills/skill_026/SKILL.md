---
name: close-a-manual-handle
description: Close one handle-operated door or drawer.
---

# Close a manual handle (skill_026)

## When to use

Close one handle-operated door or drawer.

## Inputs

- `articulated` (`articulated_ref`): The uniquely grounded door or drawer.

## Preconditions

- `right_hand_empty` — `policy_attempt`
- `target_annotated` — `policy_attempt`

## Planner action predicate

`push_manual_handle(articulated)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['joint_closed']`.

## Expected state change

- `joint_closed` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_026` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_034", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `articulated`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'required_annotation': 'handle', 'forbid_annotation': 'door_button'}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_023(articulated)`


Verifier: `contract_005 / handle`.

## Related Skills

- May follow `skill_004` (`follows`) when an object was removed and the manual access must be closed.
- May follow `skill_007` (`alternative`) when a manual door close needs an explicit handle route.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One close a manual handle attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
