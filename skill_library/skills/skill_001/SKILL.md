---
name: skill_001
description: Move the empty-handed robot base to one target pose.
---

# skill_001 — Navigate empty-handed

## When to use

Move the empty-handed robot base to one target pose.

## Inputs

- `pose` (`pose2d`): pose

## Preconditions

- `target_navigable` — `policy_attempt`
- `carried_object_matches_state` — `not_enforced`

## Expected state change

- `base_at` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_001` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_009", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):


### Policy path: fixed

Match before execution: `[]`.

1. `policy_001(pose)`


Verifier: `contract_001 / empty`.

## Related Skills

- No fixed relation; select the next node from the task goal and observation.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.
- Conditional fallback `skill_011` when base path blocked and right hand remains empty: tuck the arm before proposing a new navigation attempt

## Scope and evidence

one empty-handed base move

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
