# policy_072 — present_held

Hold the carried object in front of the head camera.

## Scope

One low-level controller invocation. Reported effect: `presenting(name)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_072.execute(...)`
- Legacy alias: `PolicySuite(rig).present_held.execute(...)`
- Class: `PresentHeldPolicy`
- Availability: `callable`
- Skill Contract paths: contract_024:present/front_of_head

## Recorded evidence

pending Isaac Sim check (skill library v2)
