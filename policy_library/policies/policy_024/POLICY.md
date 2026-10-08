# policy_024 — open_powered

按钮释放并打开动力微波炉门

## Scope

One low-level controller invocation. Reported effect: `joint_at(open_q)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_024.execute(...)`
- Legacy alias: `PolicySuite(rig).open_powered.execute(...)`
- Class: `PoweredDoorOpenPolicy`
- Availability: `verified`
- Skill Contract paths: contract_048:open/powered_microwave, contract_076:stop/microwave_door
- Legacy family Contracts: contract_004

## Recorded evidence

Isaac Sim heat_breakfast_combo: powered microwave opened to -1.400 rad, runs/verify_callable_microwave, 2026-10-01
