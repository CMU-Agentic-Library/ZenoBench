# policy_099 — plan_heading

Yaw change that faces a target (no motion).

## Scope

One low-level controller invocation. Reported effect: `returns delta_yaw_deg (no state change)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `target`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_099.execute(...)`
- Legacy alias: `PolicySuite(rig).plan_heading.execute(...)`
- Class: `PlanHeadingPolicy`
- Availability: `callable`
- Skill Contract paths: contract_011:face/rotate_empty

## Recorded evidence

pending Isaac Sim check (skill library v2)
