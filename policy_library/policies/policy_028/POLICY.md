# policy_028 — microwave_button_press

从对齐位姿按下微波炉按钮并测量接触位姿

## Scope

One low-level controller invocation. Reported effect: `button_pressed`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; optional
- `button`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_028.execute(...)`
- Legacy alias: `PolicySuite(rig).microwave_button_press.execute(...)`
- Class: `MicrowaveButtonPressPolicy`
- Availability: `verified`
- Direct Contract routes: contract_017, contract_018
- Referenced as support by legacy families: contract_004, contract_007

## Recorded evidence

Isaac Sim: staged start/door buttons and powered hinge open/close, 2026-10-01; runs/microwave_atomic_smoke/result.json; composed entry points in runs/microwave_composed_smoke/result.json
