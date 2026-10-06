# policy_036 — base_rotate_in_place

空手收臂后检查占用空间并原地旋转

## Scope

One low-level controller invocation. Reported effect: `base_yaw_changed`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `delta_yaw_deg`: positional_or_keyword; required
- `tolerance_deg`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_036.execute(...)`
- Legacy alias: `PolicySuite(rig).base_rotate_in_place.execute(...)`
- Class: `BaseRotateInPlacePolicy`
- Availability: `verified`
- Direct Contract routes: contract_051
- Referenced as support by legacy families: contract_001

## Recorded evidence

Isaac Sim: tuck_arm; base_rotate_in_place 10; base_translate_local 0.1, 2026-10-01; runs/atomic_base_smoke/result.json
