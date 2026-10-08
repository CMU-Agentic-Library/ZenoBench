# policy_093 — set_held_height

Raise or lower a held object.

## Scope

One low-level controller invocation. Reported effect: `held_above/held_below(name, h)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `height_m`: positional_or_keyword; required
- `tolerance`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_093.execute(...)`
- Legacy alias: `PolicySuite(rig).set_held_height.execute(...)`
- Class: `SetHeldHeightPolicy`
- Availability: `callable`
- Skill Contract paths: contract_032:lower/descend

## Recorded evidence

pending Isaac Sim check (skill library v2)
