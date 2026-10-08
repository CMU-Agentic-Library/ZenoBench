# policy_086 — pour_into

Tilt a held cup over a container.

## Scope

One low-level controller invocation. Reported effect: `poured_into(source, target)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `source`: positional_or_keyword; required
- `target`: positional_or_keyword; required
- `max_tilt_deg`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_086.execute(...)`
- Legacy alias: `PolicySuite(rig).pour_into.execute(...)`
- Class: `PourIntoPolicy`
- Availability: `callable`
- Skill Contract paths: contract_047:pour/tilt_over_rim

## Recorded evidence

pending Isaac Sim check (skill library v2)
