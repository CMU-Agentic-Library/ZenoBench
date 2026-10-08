# policy_027 — microwave_button_approach

对齐微波炉开门或启动按钮前方的右手指尖

## Scope

One low-level controller invocation. Reported effect: `tcp_aligned_to_button`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; optional
- `button`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_027.execute(...)`
- Legacy alias: `PolicySuite(rig).microwave_button_approach.execute(...)`
- Class: `MicrowaveButtonApproachPolicy`
- Availability: `verified`
- Skill Contract paths: contract_050:press/microwave_start_staged
- Referenced as support by legacy families: contract_004, contract_007

## Recorded evidence

Isaac Sim: staged start/door buttons and powered hinge open/close, 2026-10-01; runs/microwave_atomic_smoke/result.json; composed entry points in runs/microwave_composed_smoke/result.json
