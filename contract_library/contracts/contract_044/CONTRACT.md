# contract_044 — Upright a held object

Rotate a right-held object until its local up axis is within 20 degrees of vertical.

Paired SkillNode: `skill_036`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref

## Preconditions

- `held_by_right_hand` — policy_attempt

## Planner action predicate

`orient_held_object(object)` — reported only after the measured state facts pass.

## Measured postconditions

- `object_upright` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_054` with ['object']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: custom `upright`.
