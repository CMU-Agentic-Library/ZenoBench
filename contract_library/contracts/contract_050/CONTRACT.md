# contract_050 — Back away while carrying

Reverse the base while preserving the right-hand grasp.

Paired SkillNode: `skill_042`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref
- `distance_m`: positive_number

## Preconditions

- `held_by_right_hand` — policy_attempt
- `backward_path_clear` — policy_attempt

## Planner action predicate

`retreat_carried_object(object, distance_m)` — reported only after the measured state facts pass.

## Measured postconditions

- `base_backed_off` — contract_runner
- `grasp_preserved` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_035` with ['distance_m']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: custom `back_off`.
