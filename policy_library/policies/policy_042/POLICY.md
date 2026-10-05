# policy_042 — prepare_floor_reach

协调躯干、腰部和右臂进入地面可达姿态

## Scope

One low-level controller invocation. Reported effect: `floor_target_reachable`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `clearance_m`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_042.execute(...)`
- Legacy alias: `PolicySuite(rig).prepare_floor_reach.execute(...)`
- Class: `PrepareFloorReachPolicy`
- Availability: `verified`
- Referenced as support by legacy families: contract_002, contract_008

## Recorded evidence

Isaac Sim tidy_toys: lowered torso to -0.537 m, pitched waist 0.292 rad, reached collision-checked pregrasp above toy_block with 0.0043 m TCP error, 2026-10-01
