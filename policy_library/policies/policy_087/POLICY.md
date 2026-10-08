# policy_087 — cover_with_lid

Lay a held lid centred on a container rim.

## Scope

One low-level controller invocation. Reported effect: `covered(container, lid)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `lid`: positional_or_keyword; required
- `container`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_087.execute(...)`
- Legacy alias: `PolicySuite(rig).cover_with_lid.execute(...)`
- Class: `CoverWithLidPolicy`
- Availability: `callable`
- Skill Contract paths: contract_053:cover/rim_plane

## Recorded evidence

pending Isaac Sim check (skill library v2)
