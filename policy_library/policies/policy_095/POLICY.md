# policy_095 — plan_home

Joint vector of the home posture (no motion).

## Scope

One low-level controller invocation. Reported effect: `returns target (no state change)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- None.

## Binding and status

- Runtime: `PolicySuite(rig).policy_095.execute(...)`
- Legacy alias: `PolicySuite(rig).plan_home.execute(...)`
- Class: `PlanHomePolicy`
- Availability: `callable`
- Skill Contract paths: contract_018:reset/joint_home

## Recorded evidence

pending Isaac Sim check (skill library v2)
