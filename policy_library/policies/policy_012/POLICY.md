# policy_012 — pick_rect_rim

沿矩形容器口沿夹取

## Scope

One low-level controller invocation. Reported effect: `held(object)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `max_candidates`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_012.execute(...)`
- Legacy alias: `PolicySuite(rig).pick_rect_rim.execute(...)`
- Class: `RectRimPickPolicy`
- Availability: `verified`
- Direct Contract routes: contract_012, contract_037
- Legacy family Contracts: contract_002

## Caveat

该托盘后续携带时滑脱；单步抓取成功不保证持物移动稳定

## Recorded evidence

Isaac Sim collect_fruits: serving_tray rim pinch lifted 0.0293 m with both fingers in contact; tray slipped during later carry, runs/verify_callable_rect_tray_v3, 2026-10-01
