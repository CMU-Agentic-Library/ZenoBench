# policy_031 — microwave_hinge_drive

在机器人退离后驱动微波炉门到开或关位置

## Scope

One low-level controller invocation. Reported effect: `joint_at(target)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; optional
- `target`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_031.execute(...)`
- Legacy alias: `PolicySuite(rig).microwave_hinge_drive.execute(...)`
- Class: `MicrowaveHingeDrivePolicy`
- Availability: `verified`
- Referenced as support by legacy families: contract_004, contract_005

## Recorded evidence

Isaac Sim: staged start/door buttons and powered hinge open/close, 2026-10-01; runs/microwave_atomic_smoke/result.json; composed entry points in runs/microwave_composed_smoke/result.json
