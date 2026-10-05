# contract_037 — Pick by rectangular rim

Grasp a rectangular tray or box by its annotated rim.

Paired SkillNode: `skill_029`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref

## Preconditions

- `right_hand_empty` — contract_precheck
- `target_annotated` — policy_attempt

## Measured postconditions

- `held_by_right_hand` — contract_runner
- `object_lifted` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_grasp_type': 'rim_pinch_rect'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_012` with ['object']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_002` / `rect_rim`.
