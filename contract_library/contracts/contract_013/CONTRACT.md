# contract_013 — Place an object on a support

Release one right-held object onto one annotated support.

Paired SkillNode: `skill_005`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref
- `support`: support_ref

## Preconditions

- `held_by_right_hand` — contract_precheck
- `target_annotated` — policy_attempt
- `target_accessible` — policy_attempt

## Planner action predicate

`deposit_object_on_support(object, support)` — reported only after the measured state facts pass.

## Measured postconditions

- `on` — contract_runner
- `right_hand_empty` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True}`

## Policy paths

### microwave_support

Match before execution: `[{'noun': 'support', 'field': 'furniture', 'equals': 'kitchen_microwave'}]`.

1. `policy_018` with ['object', 'support']
2. `policy_019` with ['object']
3. `policy_020` with ['object']

### edge_held

Match before execution: `[{'noun': 'object', 'field': 'held_kind', 'equals': 'edge'}]`.

1. `policy_017` with ['object', 'support']

### ordinary_surface

Match before execution: `[{'noun': 'support', 'field': 'kind', 'equals': 'support'}]`.

1. `policy_015` with ['object', 'support']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_003` / `surface`.
