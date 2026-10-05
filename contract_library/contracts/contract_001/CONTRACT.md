# contract_001 — navigate.v1

Move the base to a target pose, preserving any grasp.

## Scope

One base move to a target pose, preserving any current grasp.

## Inputs

- `pose`: pose2d; required
- `carried_object`: object_id; optional
- `min_bottom_z_m`: number; optional

## Requires

- `target_navigable` — policy_attempt
- `carried_object_matches_state` — not_enforced

## Achieves on success

- `base_at` — runner
- `grasp_preserved` — runner

## Routes

- `auto` → `NavigatePolicy`
- `empty` → `policy_001`
- `carry` → `policy_002`
- `two_hand_carry` → `policy_058`

Legacy alias: `navigate.v1`. Runtime binding: `zeno_skills.contracts.CONTRACTS`.
