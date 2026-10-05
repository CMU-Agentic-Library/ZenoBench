---
name: skill_003
description: Open one annotated articulated target and verify its joint position.
---

# skill_003 — Open an articulated door or drawer

## When to use

Open one annotated articulated target and verify its joint position.

## Inputs

- `articulated` (`articulated_ref`): articulated

## Preconditions

- `articulated_annotated` — `contract_precheck`
- `opening_route_feasible` — `policy_attempt`

## Expected state change

- `joint_open_enough` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_003` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_011", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `articulated`: `articulated`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: powered_microwave

Match before execution: `[{'noun': 'articulated', 'field': 'powered_microwave', 'equals': True}]`.

1. `policy_024(articulated)`

### Policy path: manual_drawer

Match before execution: `[{'noun': 'articulated', 'field': 'type', 'equals': 'prismatic'}, {'noun': 'articulated', 'field': 'has_handle', 'equals': True}]`.

1. `policy_050(articulated)`

### Policy path: manual_hinged_door

Match before execution: `[{'noun': 'articulated', 'field': 'type', 'equals': 'revolute'}, {'noun': 'articulated', 'field': 'has_handle', 'equals': True}]`.

1. `policy_049(articulated)`


Verifier: `contract_004 / auto`.

## Related Skills

- `skill_025` (`alternative`) when a manual door must use an explicit handle route — Select the handle-specific operation when annotation supports it.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one articulated opening

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
