# policy_030 — microwave_door_clear

收臂并退到微波炉门运动区域之外

## Scope

One low-level controller invocation. Reported effect: `robot_clear_of_door_sweep`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_030.execute(...)`
- Legacy alias: `PolicySuite(rig).microwave_door_clear.execute(...)`
- Class: `MicrowaveDoorClearPolicy`
- Availability: `verified`
- Referenced as support by legacy families: contract_004, contract_005

## Recorded evidence

Isaac Sim: staged start/door buttons and powered hinge open/close, 2026-10-01; runs/microwave_atomic_smoke/result.json; composed entry points in runs/microwave_composed_smoke/result.json
