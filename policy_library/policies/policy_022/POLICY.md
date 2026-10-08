# policy_022 — open_handle

通过把手打开门或抽屉

## Scope

One low-level controller invocation. Reported effect: `joint_at(open_q)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `goal`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_022.execute(...)`
- Legacy alias: `PolicySuite(rig).open_handle.execute(...)`
- Class: `HandleOpenPolicy`
- Availability: `verified`
- Skill Contract paths: contract_048:open/refrigerator
- Legacy family Contracts: contract_004

## Recorded evidence

Isaac Sim: Manual cabinet hinge moved from closed to -1.379 rad, runs/verify_callable_handle_cabinet, 2026-10-01
