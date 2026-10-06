---
name: pivot-base-in-place
description: Rotate an empty, tucked robot by a bounded signed angle and verify its new yaw.
---

# Pivot base in place (skill_043)

## When to use

Rotate an empty, tucked robot by a bounded signed angle and verify its new yaw.

## Inputs

- `delta_yaw_deg` (`number`): delta yaw deg

## Preconditions

- `right_hand_empty` — `policy_attempt`
- `arm_tucked` — `policy_attempt`
- `turn_arc_clear` — `policy_attempt`

## Planner action predicate

`pivot_base(delta_yaw_deg)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['base_yaw_changed']`.

## Expected state change

- `base_yaw_changed` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_043` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_051", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):


### Policy path: fixed

Match before execution: `[]`.

1. `policy_036(delta_yaw_deg)`


Verifier: `base_rotate`.

## Related Skills

- May follow `skill_011` (`preparation`) when after arm tucking and a local orientation correction is needed.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One pivot base in place attempt on grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
