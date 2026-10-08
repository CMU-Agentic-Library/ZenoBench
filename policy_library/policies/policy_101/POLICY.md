# policy_101 — plan_point

Right TCP pose that points at a target (no motion).

## Scope

One low-level controller invocation. Reported effect: `returns position, rotation (no state change)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `target`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_101.execute(...)`
- Legacy alias: `PolicySuite(rig).plan_point.execute(...)`
- Class: `PlanPointPolicy`
- Availability: `callable`
- Skill Contract paths: contract_023:point/front

## Recorded evidence

pending Isaac Sim check (skill library v2)
