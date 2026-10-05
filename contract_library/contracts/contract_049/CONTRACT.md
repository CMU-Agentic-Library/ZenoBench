# contract_049 — Raise carried object for clearance

Lift a right-held object until its bottom clears a required height.

Paired SkillNode: `skill_041`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref
- `min_bottom_z`: positive_number

## Preconditions

- `held_by_right_hand` — policy_attempt

## Measured postconditions

- `held_object_above_height` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_034` with ['min_bottom_z']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: custom `carry_height`.
