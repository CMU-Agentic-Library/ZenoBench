# contract_002 — pick.v1

Attempt one right-hand grasp and lift of an annotated object.

## Scope

One right-hand grasp and lift attempt for one annotated object.

## Inputs

- `object`: object_id; required
- `base_path`: base_path; optional

## Requires

- `right_hand_empty` — runner
- `object_annotated` — policy_attempt
- `object_reachable` — policy_attempt

## Achieves on success

- `held_by_right_hand` — runner
- `object_lifted` — runner

## Routes

- `auto` → `policy_061`
- `top` → `policy_010`
- `round_rim` → `policy_011`
- `rect_rim` → `policy_012`
- `edge` → `policy_013`
- `floor_corner` → `policy_014`
- `cup_handle` → `policy_055`
- `cavity` → `policy_048`
- `moving` → `policy_052`

Legacy alias: `pick.v1`. Runtime binding: `zeno_skills.contracts.CONTRACTS`.
