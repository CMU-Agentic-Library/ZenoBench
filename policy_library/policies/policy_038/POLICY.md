# policy_038 — right_tcp_move

右手末端按给定位姿移动

## Scope

One low-level controller invocation. Reported effect: `tcp_at(pose)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `position`: positional_or_keyword; required
- `rotation`: positional_or_keyword; required
- `step`: keyword_only; optional
- `position_tolerance`: keyword_only; optional
- `rotation_tolerance`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_038.execute(...)`
- Legacy alias: `PolicySuite(rig).right_tcp_move.execute(...)`
- Class: `RightTcpMovePolicy`
- Availability: `verified`
- Referenced as support by legacy families: contract_002, contract_003, contract_004, contract_005, contract_006, contract_007, contract_008

## Recorded evidence

Isaac Sim tidy_toys: TCP moved +0.04 m vertically with 0.0039 m position and 0.0086 rad orientation error, runs/verify_callable_arm_v4, 2026-10-01
