# policy_020 — microwave_cavity_withdraw

松爪后撤回手和底盘并验证物体落在炉腔支撑面

## Scope

One low-level controller invocation. Reported effect: `on(object,cavity_support)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_020.execute(...)`
- Legacy alias: `PolicySuite(rig).microwave_cavity_withdraw.execute(...)`
- Class: `MicrowaveCavityWithdrawPolicy`
- Availability: `verified`
- Skill Contract paths: contract_026:place/microwave_staged
- Referenced as support by legacy families: contract_003

## Recorded evidence

Isaac Sim: heat_breakfast fridge -> microwave -> dining table, 100% progress, 2026-10-01; runs/heat_breakfast/result.json
