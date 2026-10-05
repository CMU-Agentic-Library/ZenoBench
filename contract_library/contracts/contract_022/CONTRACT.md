# contract_022 — Place an object on the microwave cavity support

Release one right-held object onto the annotated microwave cavity support.

Paired SkillNode: `skill_014`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref
- `support`: microwave_support_ref

## Preconditions

- `held_by_right_hand` — contract_precheck
- `target_annotated` — policy_attempt
- `target_accessible` — policy_attempt

## Measured postconditions

- `on` — contract_runner
- `right_hand_empty` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True, 'furniture_equals': 'kitchen_microwave'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_018` with ['object', 'support']
2. `policy_019` with ['object']
3. `policy_020` with ['object']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_003` / `microwave`.
