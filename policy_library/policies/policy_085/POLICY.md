# policy_085 — stir_container

Circle a held spoon inside a container below its rim.

## Scope

One low-level controller invocation. Reported effect: `stirred(container)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `tool`: positional_or_keyword; required
- `container`: positional_or_keyword; required
- `turns`: keyword_only; optional
- `tilt_deg`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_085.execute(...)`
- Legacy alias: `PolicySuite(rig).stir_container.execute(...)`
- Class: `StirContainerPolicy`
- Availability: `callable`
- Skill Contract paths: contract_046:stir/circle_below_rim

## Recorded evidence

pending Isaac Sim check (skill library v2)
