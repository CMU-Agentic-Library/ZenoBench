# contract_048 — Wait for food to reach target temperature

Advance the live thermal simulation until the named food reaches its target temperature.

Paired SkillNode: `skill_040`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref
- `min_temp_c`: positive_number

## Preconditions

- `thermal_model_configured` — policy_attempt
- `heating_active_or_already_hot` — policy_attempt

## Measured postconditions

- `temperature_at_least` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_064` with ['object', 'min_temp_c']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: custom `temperature`.
