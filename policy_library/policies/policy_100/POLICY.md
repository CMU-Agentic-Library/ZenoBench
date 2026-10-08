# policy_100 — plan_retreat

Signed forward distance that backs away from a place (no motion).

## Scope

One low-level controller invocation. Reported effect: `returns forward_m (no state change)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `place`: positional_or_keyword; required
- `distance_m`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_100.execute(...)`
- Legacy alias: `PolicySuite(rig).plan_retreat.execute(...)`
- Class: `PlanRetreatPolicy`
- Availability: `callable`
- Skill Contract paths: contract_012:retreat/empty

## Recorded evidence

pending Isaac Sim check (skill library v2)
