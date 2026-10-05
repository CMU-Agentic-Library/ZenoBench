# contract_024 — Pick a flat object at an edge

Attempt one edge grasp of a flat object and verify grasp and lift.

Paired SkillNode: `skill_016`. Status: `representative_runs_only`.

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

1. `policy_013` with ['object']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_002` / `edge`.
