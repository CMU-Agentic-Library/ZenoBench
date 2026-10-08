# policy_070 — search_object

Visit candidate supports by distance until the object is seen.

## Scope

One low-level controller invocation. Reported effect: `observed(name); returns found_on`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `region`: positional_or_keyword; optional
- `max_places`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_070.execute(...)`
- Legacy alias: `PolicySuite(rig).search_object.execute(...)`
- Class: `SearchObjectPolicy`
- Availability: `callable`
- Skill Contract paths: contract_021:search/room_sweep

## Recorded evidence

pending Isaac Sim check (skill library v2)
