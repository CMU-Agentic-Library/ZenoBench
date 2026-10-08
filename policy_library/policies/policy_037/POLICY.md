# policy_037 — base_translate_local

空手收臂后沿底盘局部坐标短距离直线移动

## Scope

One low-level controller invocation. Reported effect: `base_translated`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `forward_m`: positional_or_keyword; required
- `left_m`: positional_or_keyword; optional
- `tolerance_m`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_037.execute(...)`
- Legacy alias: `PolicySuite(rig).base_translate_local.execute(...)`
- Class: `BaseTranslateLocalPolicy`
- Availability: `verified`
- Skill Contract paths: contract_012:retreat/empty, contract_063:sidestep/empty_tucked
- Referenced as support by legacy families: contract_001

## Recorded evidence

Isaac Sim: tuck_arm; base_rotate_in_place 10; base_translate_local 0.1, 2026-10-01; runs/atomic_base_smoke/result.json
