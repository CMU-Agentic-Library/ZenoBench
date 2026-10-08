# policy_115 — hover_over

Hold the carried object just above a target.

## Scope

One low-level controller invocation. Reported effect: `hovering_over(name, target)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `target`: positional_or_keyword; required
- `clearance_m`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_115.execute(...)`
- Legacy alias: `PolicySuite(rig).hover_over.execute(...)`
- Class: `HoverOverPolicy`
- Availability: `callable`
- Skill Contract paths: contract_071:hover/above_target

## Recorded evidence

pending Isaac Sim check (skill library v2)
