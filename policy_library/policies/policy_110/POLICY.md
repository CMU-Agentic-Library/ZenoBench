# policy_110 — identify_object

Look at an object and record its category.

## Scope

One low-level controller invocation. Reported effect: `identified(name)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_110.execute(...)`
- Legacy alias: `PolicySuite(rig).identify_object.execute(...)`
- Class: `IdentifyObjectPolicy`
- Availability: `callable`
- Skill Contract paths: contract_065:identify/look_and_label

## Recorded evidence

pending Isaac Sim check (skill library v2)
