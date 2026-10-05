# contract_016 — Push an object along a support

Move one object by directed contact and measure progress.

Paired SkillNode: `skill_008`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref
- `support`: support_ref
- `direction_xy`: unit_vec2
- `distance_m`: positive_number

## Preconditions

- `right_hand_empty` — contract_precheck
- `object_on_support` — policy_attempt

## Measured postconditions

- `displacement_along` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_026` with ['object', 'support', 'direction_xy', 'distance_m']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_006` / `auto`.
