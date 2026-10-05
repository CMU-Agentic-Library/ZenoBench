# policy_054 — upright_object

把倾倒的物品扶正

## Scope

One low-level controller invocation. Reported effect: `upright(object)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `max_tilt_deg`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_054.execute(...)`
- Legacy alias: `PolicySuite(rig).upright_object.execute(...)`
- Class: `UprightObjectPolicy`
- Availability: `verified`
- Direct Contract routes: contract_044, contract_045, contract_047
- Referenced as support by legacy families: contract_003

## Caveat

要求右手先抓住物体；倾倒物体姿态修正尚待 Isaac Sim 验证

## Recorded evidence

Isaac Sim tidy_toys: toy_block physically tipped to 29.129 deg in right grasp, UprightObjectPolicy reduced tilt to 0.951 deg, runs/verify_callable_upright, 2026-10-01
