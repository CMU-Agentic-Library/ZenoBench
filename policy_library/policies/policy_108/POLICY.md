# policy_108 — plan_square_yaw

Yaw correction that aligns an object with its support axes (no motion).

## Scope

One low-level controller invocation. Reported effect: `returns degrees, xy (no state change)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_108.execute(...)`
- Legacy alias: `PolicySuite(rig).plan_square_yaw.execute(...)`
- Class: `PlanSquareYawPolicy`
- Availability: `callable`
- Skill Contract paths: contract_072:square/pick_rotate_place

## Recorded evidence

pending Isaac Sim check (skill library v2)
