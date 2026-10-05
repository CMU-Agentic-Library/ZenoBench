---
name: skill_007
description: Close one annotated articulated target and verify its joint position.
---

# skill_007 — Close an articulated door or drawer

## When to use

Close one annotated articulated target and verify its joint position.

## Inputs

- `articulated` (`articulated_ref`): articulated

## Preconditions

- `articulated_annotated` — `contract_precheck`
- `closure_path_clear` — `policy_attempt`

## Expected state change

- `joint_closed` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_007` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_015", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `articulated`: `articulated`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: powered_microwave

Match before execution: `[{'noun': 'articulated', 'field': 'powered_microwave', 'equals': True}]`.

1. `policy_025(articulated)`

### Policy path: manual_handle

Match before execution: `[{'noun': 'articulated', 'field': 'has_handle', 'equals': True}]`.

1. `policy_023(articulated)`


Verifier: `contract_005 / auto`.

## Related Skills

- `skill_026` (`alternative`) when a manual door close needs an explicit handle route — Select the handle-specific closure.
- `skill_024` (`alternative`) when a powered microwave door must close — Use the powered closure policy.
- May follow `skill_005` (`follows`) when manipulation used an articulated compartment and the task requires closed doors.
- May follow `skill_006` (`follows`) when container placement used an articulated compartment and the task requires closed doors.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

one articulated closure

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
