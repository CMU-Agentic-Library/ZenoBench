# contract_028 — Pick a flat object from a floor corner

Attempt one floor-corner grasp and verify right-hand lift.

Paired SkillNode: `skill_020`. Status: `experimental_callable`.

## Inputs

- `object`: object_ref

## Preconditions

- `right_hand_empty` — contract_precheck
- `object_annotated` — policy_attempt
- `object_reachable` — policy_attempt

## Measured postconditions

- `held_by_right_hand` — contract_runner
- `object_lifted` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_grasp_type': 'edge_pinch_after_push'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_014` with ['object']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_002` / `floor_corner`.
