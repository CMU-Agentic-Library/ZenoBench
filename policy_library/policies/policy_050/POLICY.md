# policy_050 — open_prismatic_drawer

只选择滑动抽屉的把手轨迹

## Scope

One low-level controller invocation. Reported effect: `joint_at(open_q)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_050.execute(...)`
- Legacy alias: `PolicySuite(rig).open_prismatic_drawer.execute(...)`
- Class: `OpenPrismaticDrawerPolicy`
- Availability: `verified`
- Direct Contract routes: contract_011
- Legacy family Contracts: contract_004

## Caveat

tidy_toys 的第一只抽屉仍未拉动；另一只厨房抽屉已通过独立物理验证

## Recorded evidence

Isaac Sim base scene: kitchen drawer joint moved 0 to -0.130 rad/m toward -0.169 target with physical handle contact, runs/verify_callable_drawer, 2026-10-01
