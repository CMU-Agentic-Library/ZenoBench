# contract_027 — Place on a support while the base moves

Release one right-held object onto a support during a base move.

Paired SkillNode: `skill_019`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref
- `support`: support_ref
- `base_path`: pose2d

## Preconditions

- `held_by_right_hand` — contract_precheck
- `target_annotated` — policy_attempt
- `target_accessible` — policy_attempt

## Planner action predicate

`deliver_object(object, support, base_path)` — reported only after the measured state facts pass.

## Measured postconditions

- `on` — contract_runner
- `right_hand_empty` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`
- `support`: `support`; constraints `{'source': 'rig.ann', 'required': True}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_053` with ['object', 'support', 'base_path']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_003` / `moving`.
