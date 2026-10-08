# policy_076 — regrasp

Set an object down and grasp it again.

## Scope

One low-level controller invocation. Reported effect: `holding(right, name)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `support`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_076.execute(...)`
- Legacy alias: `PolicySuite(rig).regrasp.execute(...)`
- Class: `RegraspPolicy`
- Availability: `callable`
- Skill Contract paths: contract_034:regrasp/set_down_and_pick

## Recorded evidence

pending Isaac Sim check (skill library v2)
