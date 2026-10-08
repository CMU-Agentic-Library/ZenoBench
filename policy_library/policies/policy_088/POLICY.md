# policy_088 — inspect_receptacle

Look into a receptacle and list its contents.

## Scope

One low-level controller invocation. Reported effect: `observed(contents)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `receptacle`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_088.execute(...)`
- Legacy alias: `PolicySuite(rig).inspect_receptacle.execute(...)`
- Class: `InspectReceptaclePolicy`
- Availability: `callable`
- Skill Contract paths: contract_020:inspect/closed_cabinet, contract_020:inspect/open_view

## Recorded evidence

pending Isaac Sim check (skill library v2)
