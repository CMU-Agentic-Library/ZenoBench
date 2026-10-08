# policy_098 — plan_reach

Right TCP pose that reaches a target (no motion).

## Scope

One low-level controller invocation. Reported effect: `returns position, rotation (no state change)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `target`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_098.execute(...)`
- Legacy alias: `PolicySuite(rig).plan_reach.execute(...)`
- Class: `PlanReachPolicy`
- Availability: `callable`
- Skill Contract paths: contract_010:approach/reach_on_the_move

## Recorded evidence

pending Isaac Sim check (skill library v2)
