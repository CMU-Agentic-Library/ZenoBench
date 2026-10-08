# policy_097 — plan_standoff

Free base pose next to a place (no motion).

## Scope

One low-level controller invocation. Reported effect: `returns pose (no state change)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `place`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_097.execute(...)`
- Legacy alias: `PolicySuite(rig).plan_standoff.execute(...)`
- Class: `PlanStandoffPolicy`
- Availability: `callable`
- Skill Contract paths: contract_009:navigate/two_hand_carry, contract_009:navigate/carry, contract_009:navigate/empty

## Recorded evidence

pending Isaac Sim check (skill library v2)
