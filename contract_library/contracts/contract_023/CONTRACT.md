# contract_023 — Pick an object from a cavity

Attempt one right-hand cavity retrieval and verify grasp and lift.

Paired SkillNode: `skill_015`. Status: `experimental_callable`.

## Inputs

- `object`: object_ref
- `cavity`: appliance_ref

## Preconditions

- `right_hand_empty` — contract_precheck
- `object_annotated` — policy_attempt
- `object_reachable` — policy_attempt

## Measured postconditions

- `held_by_right_hand` — contract_runner
- `object_lifted` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`
- `cavity`: `articulated`; constraints `{'source': 'rig.ann', 'required': True, 'category_equals': 'microwave', 'required_annotation': 'cavity_aabb'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_048` with ['object', 'cavity']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_002` / `cavity`.
