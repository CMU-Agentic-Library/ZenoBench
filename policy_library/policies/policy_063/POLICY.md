# policy_063 — close

Annotation-selected close dispatcher

## Scope

One low-level controller invocation. Reported effect: `joint_closed(articulated)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_063.execute(...)`
- Legacy alias: `PolicySuite(rig).close.execute(...)`
- Class: `ClosePolicy`
- Availability: `verified`
- Skill Contract paths: contract_020:inspect/closed_cabinet, contract_049:close/dispatch
- Legacy family Contracts: contract_005

## Recorded evidence

Existing annotation-dispatching policy used by previously verified contract route.
