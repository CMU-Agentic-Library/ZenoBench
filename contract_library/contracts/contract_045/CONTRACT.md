# contract_045 — Place an object upright on a support

Orient a held object, place it on a support, then verify support and tilt.

Paired SkillNode: `skill_037`. Status: `experimental_callable`.

## Inputs

- `object`: object_ref
- `support`: support_ref

## Preconditions

- `held_by_right_hand` — contract_precheck
- `target_annotated` — policy_attempt

## Planner action predicate

`stand_object_on_support(object, support)` — reported only after the measured state facts pass.

## Measured postconditions

- `on` — contract_runner
- `right_hand_empty` — contract_runner
- `object_upright` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_054` with ['object']
2. `policy_015` with ['object', 'support']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_003` / `surface`.
