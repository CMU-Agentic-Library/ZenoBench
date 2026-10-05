# contract_046 — Place an object near a support hint

Place a held object near a supplied xy hint and verify the final offset.

Paired SkillNode: `skill_038`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref
- `support`: support_ref
- `hint_xy`: xy
- `max_offset_m`: positive_number

## Preconditions

- `held_by_right_hand` — contract_precheck
- `target_annotated` — policy_attempt

## Measured postconditions

- `on` — contract_runner
- `right_hand_empty` — contract_runner
- `within_hint_radius` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_015` with ['object', 'support']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_003` / `surface`.
