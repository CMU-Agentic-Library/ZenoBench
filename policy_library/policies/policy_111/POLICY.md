# policy_111 — measure_object

Look at an object and record its size.

## Scope

One low-level controller invocation. Reported effect: `measured(name)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_111.execute(...)`
- Legacy alias: `PolicySuite(rig).measure_object.execute(...)`
- Class: `MeasureObjectPolicy`
- Availability: `callable`
- Skill Contract paths: contract_066:measure/look_and_size

## Recorded evidence

pending Isaac Sim check (skill library v2)
