# policy_082 — tip_over

Push a standing object near its top so it lies down.

## Scope

One low-level controller invocation. Reported effect: `lying(name)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_082.execute(...)`
- Legacy alias: `PolicySuite(rig).tip_over.execute(...)`
- Class: `TipOverPolicy`
- Availability: `callable`
- Skill Contract paths: contract_043:tip/push_high

## Recorded evidence

pending Isaac Sim check (skill library v2)
