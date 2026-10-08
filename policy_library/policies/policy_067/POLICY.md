# policy_067 — retreat_from

Back away from a place keeping any load.

## Scope

One low-level controller invocation. Reported effect: `base_clear_of(place, distance)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `place`: positional_or_keyword; required
- `distance_m`: positional_or_keyword; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_067.execute(...)`
- Legacy alias: `PolicySuite(rig).retreat_from.execute(...)`
- Class: `RetreatFromPolicy`
- Availability: `callable`
- Skill Contract paths: contract_012:retreat/bimanual_or_left_load

## Recorded evidence

pending Isaac Sim check (skill library v2)
