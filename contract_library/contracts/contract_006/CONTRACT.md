# contract_006 — push.v1

Move an object along its support by contact.

## Scope

One directed contact move of an object along its support.

## Inputs

- `object`: object_id; required
- `support`: support_id; required
- `direction_xy`: unit_vec2; required
- `distance_m`: positive_number; required
- `enough`: nonnegative_number; optional

## Requires

- `right_hand_empty` — runner
- `object_on_support` — policy_attempt

## Achieves on success

- `displacement_along` — runner

## Routes

- `auto` → `policy_026`
- `behind` → `policy_043`
- `top_drag` → `policy_044`

## Outside this contract

- object remains on support after the push

Legacy alias: `push.v1`. Runtime binding: `zeno_skills.contracts.CONTRACTS`.
