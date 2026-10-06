# contract_038 — Place an edge-held flat object

Place one edge-held flat item onto an annotated support.

Paired SkillNode: `skill_030`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref
- `support`: support_ref

## Preconditions

- `held_by_right_hand` — contract_precheck
- `target_annotated` — policy_attempt
- `held_with_edge_grasp` — policy_attempt

## Planner action predicate

`lay_edge_held_flat_object(object, support)` — reported only after the measured state facts pass.

## Measured postconditions

- `on` — contract_runner
- `right_hand_empty` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_held_kind': 'edge', 'requires_right_held': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_017` with ['object', 'support']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_003` / `edge`.
