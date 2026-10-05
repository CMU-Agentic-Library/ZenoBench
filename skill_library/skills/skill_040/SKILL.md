---
name: skill_040
description: Advance the live thermal simulation until the named food reaches its target temperature.
---

# skill_040 — Wait for food to reach target temperature

## When to use

Advance the live thermal simulation until the named food reaches its target temperature.

## Inputs

- `object` (`object_ref`): The uniquely grounded scene object.
- `min_temp_c` (`positive_number`): Required target temperature in Celsius.

## Preconditions

- `thermal_model_configured` — `policy_attempt`
- `heating_active_or_already_hot` — `policy_attempt`

## Expected state change

- `temperature_at_least` — measured by `contract_runner`

## Invocation and policy plan

Use `skill_id: skill_040` with typed `args` in a `skill_subgraph`. The Graph Manager grounds refs, then calls `ContractRunner.run("contract_048", "compose", ...)`.

Grounded noun slots (Contract validates the scene instance before execution):

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`

### Policy path: fixed

Match before execution: `[]`.

1. `policy_064(object, min_temp_c)`


Verifier: `temperature`.

## Related Skills

- `skill_023` (`follows`) when heated food must be removed for serving — Open the microwave after heating has stopped.
- May follow `skill_010` (`enables`) when heating was started but target temperature is unmet.

## Failure

Stop and observe the live scene again. The upper layer decides whether to retry, choose a related Skill, or revise the subgraph. Relations never execute automatically.

## Scope and evidence

One wait for food to reach target temperature attempt on the grounded scene state.

Availability: `representative_runs_only`. A callable or previously verified policy does not guarantee success in a new scene.
- Outside scope: choosing the whole-task goal
- Outside scope: guaranteeing success for untested scene states
