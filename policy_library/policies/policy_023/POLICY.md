# policy_023 — close_handle

通过把手关闭门或抽屉

## Scope

One low-level controller invocation. Reported effect: `joint_at(closed_q)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_023.execute(...)`
- Legacy alias: `PolicySuite(rig).close_handle.execute(...)`
- Class: `HandleClosePolicy`
- Availability: `verified`
- Direct Contract routes: contract_015, contract_034
- Legacy family Contracts: contract_005

## Recorded evidence

Isaac Sim: Manual cabinet hinge returned from -1.379 to -0.011 rad, runs/verify_callable_handle_cabinet, 2026-10-01
