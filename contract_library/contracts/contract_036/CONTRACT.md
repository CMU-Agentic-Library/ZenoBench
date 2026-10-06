# contract_036 — Pick by round rim

Grasp a bowl or cup by its annotated round rim.

Paired SkillNode: `skill_028`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref

## Preconditions

- `right_hand_empty` — contract_precheck
- `target_annotated` — policy_attempt

## Planner action predicate

`grasp_round_rim(object)` — reported only after the measured state facts pass.

## Measured postconditions

- `held_by_right_hand` — contract_runner
- `object_lifted` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_grasp_type': 'rim_pinch'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_011` with ['object']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_002` / `round_rim`.
