# policy_011 — pick_round_rim

沿圆形容器口沿夹取

## Scope

One low-level controller invocation. Reported effect: `held(object)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `max_candidates`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_011.execute(...)`
- Legacy alias: `PolicySuite(rig).pick_round_rim.execute(...)`
- Class: `RoundRimPickPolicy`
- Availability: `verified`
- Direct Contract routes: contract_012, contract_036
- Legacy family Contracts: contract_002

## Recorded evidence

Isaac Sim: pick_round_rim cup, 2026-10-01
