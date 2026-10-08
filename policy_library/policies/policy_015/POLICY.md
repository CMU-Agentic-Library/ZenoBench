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
- Skill Contract paths: contract_026:place/cabinet_or_fridge_shelf, contract_026:place/stove_burner, contract_026:place/surface, contract_044:upright/pick_orient_place, contract_054:uncover/knob_lift_aside, contract_061:restore/dispatch_pick_place, contract_072:square/pick_rotate_place
- Legacy family Contracts: contract_003

## Recorded evidence

Isaac Sim collect_fruits: apple placed on dining-table support with 0.0139 m XY error and on_support=true, runs/verify_callable_surface_apple, 2026-10-01
