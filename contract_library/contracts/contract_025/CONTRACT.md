# contract_025 — Pick a cup by its handle

Attempt one handle grasp of a cup and verify grasp and lift.

Paired SkillNode: `skill_017`. Status: `representative_runs_only`.

## Inputs

- `object`: object_ref

## Preconditions

- `right_hand_empty` — contract_precheck
- `object_annotated` — policy_attempt
- `object_reachable` — policy_attempt
- `handle_collision_body_prepared` — not_enforced

## Planner action predicate

`grip_cup_handle(object)` — reported only after the measured state facts pass.

## Measured postconditions

- `held_by_right_hand` — contract_runner
- `object_lifted` — contract_runner

## Grounded noun slots

- `object`: `scene_object`; constraints `{'source': 'rig.ann', 'required': True, 'requires_grasp_type': 'handle_pinch'}`

## Policy paths

### fixed

Match before execution: `[]`.

1. `policy_055` with ['object']


## Failure

Stop, return completed policy steps and measured state; upper layer replans.

Verifier: `contract_002` / `cup_handle`.
