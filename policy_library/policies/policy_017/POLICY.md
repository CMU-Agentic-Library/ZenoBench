# policy_017 — place_edge

把边缘持握的平物体滑回支撑面

## Scope

One low-level controller invocation. Reported effect: `on(object,support)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `support`: positional_or_keyword; required
- `hint`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_017.execute(...)`
- Legacy alias: `PolicySuite(rig).place_edge.execute(...)`
- Class: `EdgePlacePolicy`
- Availability: `verified`
- Direct Contract routes: contract_013, contract_038
- Legacy family Contracts: contract_003

## Recorded evidence

Isaac Sim shelve_books: edge-held book_red released onto desk support, on_support true and tilt 1.1 deg, runs/verify_callable_place_edge, 2026-10-01
