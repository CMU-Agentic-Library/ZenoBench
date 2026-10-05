# contract_030 — Open a door while the left hand holds an object

Open one annotated door while preserving an existing left-hand hold.

Paired SkillNode: `skill_022`. Status: `experimental_callable`.

## Inputs

- `object`: object_ref
- `articulated`: articulated_ref

## Preconditions

- `articulated_annotated` — contract_precheck
- `opening_route_feasible` — policy_attempt
- `held_by_left_hand` — not_enforced

## Measured postconditions

- `joint_open_enough` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True}`
- `articulated`: `articulated`; constraints `{'source': 'rig.ann', 'required': True}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_060` with ['object', 'articulated']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_004` / `while_left_holds`.
