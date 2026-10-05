# policy_003 — tuck_arm

碰撞检查后收起右臂

## Scope

One low-level controller invocation. Reported effect: `right_arm_tucked`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- None.

## Binding and status

- Runtime: `PolicySuite(rig).policy_003.execute(...)`
- Legacy alias: `PolicySuite(rig).tuck_arm.execute(...)`
- Class: `TuckArmPolicy`
- Availability: `verified`
- Direct Contract routes: contract_019
- Legacy family Contracts: contract_008
- Referenced as support by legacy families: contract_001

## Recorded evidence

Isaac Sim: lower_torso 自动收臂, 2026-10-01
