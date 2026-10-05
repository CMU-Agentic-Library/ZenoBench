# contract_035 — Pick by top pinch

Grasp an annotated object from its top pinch region.

Paired SkillNode: `skill_027`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref

## Preconditions

- `right_hand_empty` — contract_precheck
- `target_annotated` — policy_attempt

## Measured postconditions

- `held_by_right_hand` — contract_runner
- `object_lifted` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_grasp_type': 'top_pinch'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_010` with ['object']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_002` / `top`.
