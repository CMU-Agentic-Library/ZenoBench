# policy_044 — top_drag

压住物体顶部沿支撑面拖动

## Scope

One low-level controller invocation. Reported effect: `object_displaced`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `support`: positional_or_keyword; required
- `direction`: positional_or_keyword; required
- `distance`: positional_or_keyword; required
- `enough`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_044.execute(...)`
- Legacy alias: `PolicySuite(rig).top_drag.execute(...)`
- Class: `TopDragPolicy`
- Availability: `verified`
- Direct Contract routes: contract_054
- Legacy family Contracts: contract_006

## Recorded evidence

Isaac Sim shelve_books: book_green moved 0.057 m by a 0.040 m top-contact drag, runs/verify_callable_top_drag_v4, 2026-10-01 Active Contract top-drag pass on book_green: 0.024 m measured progress for 0.040 m request, runs/check_50_top_drag_green_fixed, 2026-10-06; book_red case still failed to move.
