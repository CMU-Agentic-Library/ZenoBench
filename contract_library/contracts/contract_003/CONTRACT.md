# contract_003 — place.v1

Attempt one release to a named support or container.

## Scope

One right-hand release onto one support or into one container; target type selects the verifier branch.

## Inputs

- `object`: object_id; required
- `target`: support_or_container_target; required
- `hint_xy_m`: xy; optional

## Requires

- `held_by_right_hand` — runner
- `target_annotated` — policy_attempt
- `target_accessible` — policy_attempt

## Achieves on success

- `inside` — runner when target starts with in:
- `on` — runner when target does not start with in:
- `right_hand_empty` — runner

## Routes

- `auto` → `PlacePolicy`
- `surface` → `policy_015`
- `container` → `policy_016`
- `edge` → `policy_017`
- `microwave` → `policy_021`
- `moving` → `policy_053`

Legacy alias: `place.v1`. Runtime binding: `zeno_skills.contracts.CONTRACTS`.
