# policy_032 — microwave_start

按启动按钮并启动任务级加热

## Scope

One low-level controller invocation. Reported effect: `heating_active`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_032.execute(...)`
- Legacy alias: `PolicySuite(rig).microwave_start.execute(...)`
- Class: `MicrowaveStartPolicy`
- Availability: `verified`
- Legacy family Contracts: contract_007

## Recorded evidence

Isaac Sim heat_breakfast_combo: start button activated heating with oatmeal inside, runs/verify_callable_microwave, 2026-10-01
