# policy_114 — sidestep_base

Move the base sideways, also with a load.

## Scope

One low-level controller invocation. Reported effect: `sidestepped(left_m)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `left_m`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_114.execute(...)`
- Legacy alias: `PolicySuite(rig).sidestep_base.execute(...)`
- Class: `SidestepPolicy`
- Availability: `callable`
- Skill Contract paths: contract_063:sidestep/loaded

## Recorded evidence

pending Isaac Sim check (skill library v2)
