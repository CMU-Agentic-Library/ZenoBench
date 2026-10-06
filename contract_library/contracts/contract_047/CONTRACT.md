# contract_047 — Place an upright object near a support hint

Orient and place a held object near a supplied xy hint, then verify both.

Paired SkillNode: `skill_039`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref
- `support`: support_ref
- `hint_xy`: xy
- `max_offset_m`: positive_number

## Preconditions

- `held_by_right_hand` — contract_precheck
- `target_annotated` — policy_attempt

## Planner action predicate

`align_upright_object_near_hint(object, support, hint_xy, max_offset_m)` — reported only after the measured state facts pass.

## Measured postconditions

- `on` — contract_runner
- `right_hand_empty` — contract_runner
- `object_upright` — contract_runner
- `within_hint_radius` — contract_runner

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
