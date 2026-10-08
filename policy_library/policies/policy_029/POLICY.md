# policy_029 — microwave_button_retract

按键后撤回右手并检查离开按钮

## Scope

One low-level controller invocation. Reported effect: `tcp_retracted_from_button`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; optional
- `button`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_029.execute(...)`
- Legacy alias: `PolicySuite(rig).microwave_button_retract.execute(...)`
- Class: `MicrowaveButtonRetractPolicy`
- Availability: `verified`
- Skill Contract paths: contract_050:press/microwave_start_staged
- Referenced as support by legacy families: contract_004, contract_007

## Recorded evidence

Isaac Sim: staged start/door buttons and powered hinge open/close, 2026-10-01; runs/microwave_atomic_smoke/result.json; composed entry points in runs/microwave_composed_smoke/result.json
