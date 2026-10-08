# policy_062 — open

Annotation-selected open dispatcher

## Scope

One low-level controller invocation. Reported effect: `joint_open_enough(articulated)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `goal`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_062.execute(...)`
- Legacy alias: `PolicySuite(rig).open.execute(...)`
- Class: `OpenPolicy`
- Availability: `verified`
- Skill Contract paths: contract_020:inspect/closed_cabinet
- Legacy family Contracts: contract_004

## Recorded evidence

Existing annotation-dispatching policy used by previously verified contract route.
