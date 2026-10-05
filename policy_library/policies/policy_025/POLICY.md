# policy_025 — close_powered

关闭动力微波炉门

## Scope

One low-level controller invocation. Reported effect: `joint_at(closed_q)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_025.execute(...)`
- Legacy alias: `PolicySuite(rig).close_powered.execute(...)`
- Class: `PoweredDoorClosePolicy`
- Availability: `verified`
- Direct Contract routes: contract_015, contract_032
- Legacy family Contracts: contract_005

## Recorded evidence

Isaac Sim heat_breakfast_combo: powered microwave closed to -0.000002 rad, runs/verify_callable_microwave, 2026-10-01
