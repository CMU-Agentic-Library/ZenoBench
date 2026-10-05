# contract_026 — Pick while the base moves

Attempt one right-hand pick during a base move to a target pose.

Paired SkillNode: `skill_018`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref
- `base_path`: pose2d

## Preconditions

- `right_hand_empty` — contract_precheck
- `object_annotated` — policy_attempt
- `object_reachable` — policy_attempt

## Measured postconditions

- `held_by_right_hand` — contract_runner
- `object_lifted` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_052` with ['object', 'base_path']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_002` / `moving`.
