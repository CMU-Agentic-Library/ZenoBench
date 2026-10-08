# policy_073 — drop_into

Release a held object 5 cm above a container opening.

## Scope

One low-level controller invocation. Reported effect: `inside(name, container), hand_empty(right)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `container`: positional_or_keyword; required
- `clearance_m`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_073.execute(...)`
- Legacy alias: `PolicySuite(rig).drop_into.execute(...)`
- Class: `DropIntoPolicy`
- Availability: `callable`
- Skill Contract paths: contract_027:drop/above_opening

## Recorded evidence

pending Isaac Sim check (skill library v2)
