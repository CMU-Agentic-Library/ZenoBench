# policy_040 — right_gripper_open

张开右夹爪到指定宽度

## Scope

One low-level controller invocation. Reported effect: `finger_gap_at(width_m)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `width`: positional_or_keyword; optional
- `tolerance`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_040.execute(...)`
- Legacy alias: `PolicySuite(rig).right_gripper_open.execute(...)`
- Class: `RightGripperOpenPolicy`
- Availability: `verified`
- Referenced as support by legacy families: contract_002, contract_003, contract_004, contract_005

## Recorded evidence

Isaac Sim: right_gripper_open 0.04 / right_gripper_close 0.0, 2026-10-01; runs/atomic_gripper_smoke/result.json
