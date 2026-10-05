# contract_014 — Place an object in a container

Release a right-held object into an annotated container and verify the final geometry.

Paired SkillNode: `skill_006`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref
- `container`: container_ref

## Preconditions

- `held_by_right_hand` — contract_precheck
- `container_annotated` — contract_noun_binding
- `container_accessible` — policy_attempt

## Measured postconditions

- `inside` — contract_runner
- `right_hand_empty` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_right_held': True}`
- `container`: `container`; constraints `{'source': 'rig.ann', 'required': True, 'required_annotation': 'asset.container'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_016` with ['object', 'container']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_003` / `container`.
