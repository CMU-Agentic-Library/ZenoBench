# policy_035 — back_off_with_load

持物从家具旁后退到安全距离

## Scope

One low-level controller invocation. Reported effect: `base_reversed(distance) and held(object)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `distance`: positional_or_keyword; optional
- `min_distance`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_035.execute(...)`
- Legacy alias: `PolicySuite(rig).back_off_with_load.execute(...)`
- Class: `BackOffWithLoadPolicy`
- Availability: `verified`
- Skill Contract paths: contract_012:retreat/loaded
- Referenced as support by legacy families: contract_001

## Recorded evidence

Isaac Sim tidy_toys: held toy_block while base reversed 0.120 m, runs/verify_callable_toy_chain, 2026-10-01
