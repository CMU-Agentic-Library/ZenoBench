# policy_015 — place_surface

在指定支撑面寻找空位并放置

## Scope

One low-level controller invocation. Reported effect: `on(object,support)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `support`: positional_or_keyword; required
- `hint`: keyword_only; optional
- `tries`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_015.execute(...)`
- Legacy alias: `PolicySuite(rig).place_surface.execute(...)`
- Class: `SurfacePlacePolicy`
- Availability: `verified`
- Direct Contract routes: contract_013, contract_045, contract_046, contract_047
- Legacy family Contracts: contract_003

## Recorded evidence

Isaac Sim collect_fruits: apple placed on dining-table support with 0.0139 m XY error and on_support=true, runs/verify_callable_surface_apple, 2026-10-01
