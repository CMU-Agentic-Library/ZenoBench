---
name: translate-base-locally
description: Move an empty, tucked robot along a short local forward axis and measure displacement.
---

# Translate base locally (skill_044)

## When to use

Move an empty, tucked robot along a short local forward axis and measure displacement.

## Inputs

- `forward_m` (`number`): forward m

## Preconditions

- `right_hand_empty` — `policy_attempt`
- `arm_tucked` — `policy_attempt`
- `straight_path_clear` — `policy_attempt`

## Planner action predicate

`translate_base(forward_m)` — bind the listed argument slots to the current scene.
This action predicate is reported only after its measured state facts pass.
Verified facts: `['base_translated_locally']`.

## Expected state change

- `base_translated_locally` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_044` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_052", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):


### Policy path: fixed

Match before execution: `[]`.

1. `policy_037(forward_m)`


Verifier: `base_translate`.

## Related Skills

- May follow `skill_011` (`preparation`) when after arm tucking and a short straight reposition is needed.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One translate base locally attempt on grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
