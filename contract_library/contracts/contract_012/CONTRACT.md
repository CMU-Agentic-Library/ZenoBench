# contract_012 — Pick an object

Grasp and lift one annotated scene object with the right hand.

Paired SkillNode: `skill_004`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref

## Preconditions

- `right_hand_empty` — contract_precheck
- `object_annotated` — contract_noun_binding
- `object_reachable` — policy_attempt

## Measured postconditions

- `held_by_right_hand` — contract_runner
- `object_lifted` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`

## Policy paths

### microwave_cavity

Match before execution: `[{'noun': 'object', 'field': 'location', 'equals': 'microwave_cavity'}]`.

1. `policy_048` with ['object']

### floor_corner

Match before execution: `[{'noun': 'object', 'field': 'on_floor', 'equals': True}, {'noun': 'object', 'field': 'grasp_types', 'contains': 'edge_pinch_after_push'}]`.

1. `policy_014` with ['object']

### rectangular_rim

Match before execution: `[{'noun': 'object', 'field': 'grasp_types', 'contains': 'rim_pinch_rect'}]`.

1. `policy_012` with ['object']

### round_rim

Match before execution: `[{'noun': 'object', 'field': 'grasp_types', 'contains': 'rim_pinch'}]`.

1. `policy_011` with ['object']

### top_pinch

Match before execution: `[{'noun': 'object', 'field': 'grasp_types', 'contains': 'top_pinch'}]`.

1. `policy_010` with ['object']

### flat_edge

Match before execution: `[{'noun': 'object', 'field': 'on_floor', 'equals': False}, {'noun': 'object', 'field': 'grasp_types', 'contains': 'edge_pinch_after_push'}]`.

1. `policy_013` with ['object']

### handle_only

Match before execution: `[{'noun': 'object', 'field': 'grasp_types', 'contains': 'handle_pinch'}, {'noun': 'object', 'field': 'handle_collider', 'equals': True}]`.

1. `policy_055` with ['object']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_002` / `auto`.
