# policy_051 — reach_while_moving

底盘行进期间同步右臂接近目标

## Scope

One low-level controller invocation. Reported effect: `tcp_at_pregrasp`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `position`: positional_or_keyword; required
- `rotation`: positional_or_keyword; required
- `base_path`: positional_or_keyword; required
- `speed`: keyword_only; optional
- `tolerance`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_051.execute(...)`
- Legacy alias: `PolicySuite(rig).reach_while_moving.execute(...)`
- Class: `ReachWhileMovingPolicy`
- Availability: `verified`
- Skill Contract paths: contract_010:approach/reach_on_the_move
- Referenced as support by legacy families: contract_001, contract_002

## Recorded evidence

Isaac Sim: 0.10 m base travel with concurrent right-arm reach, 0.003 m TCP error, 2026-10-01
