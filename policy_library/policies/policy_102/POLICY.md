# policy_102 — shake_held

Oscillate a held object sideways.

## Scope

One low-level controller invocation. Reported effect: `shaken(name)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `cycles`: keyword_only; optional
- `amplitude`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_102.execute(...)`
- Legacy alias: `PolicySuite(rig).shake_held.execute(...)`
- Class: `ShakeHeldPolicy`
- Availability: `callable`
- Skill Contract paths: contract_070:shake/lateral

## Recorded evidence

pending Isaac Sim check (skill library v2)
