# policy_043 — push_from_behind

从物体后侧水平推动

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

- Runtime: `PolicySuite(rig).policy_043.execute(...)`
- Legacy alias: `PolicySuite(rig).push_from_behind.execute(...)`
- Class: `PushFromBehindPolicy`
- Availability: `verified`
- Direct Contract routes: contract_053
- Legacy family Contracts: contract_006

## Recorded evidence

Isaac Sim shelve_books: book_red displaced 0.0568 m along requested 0.060 m push, runs/verify_callable_push_drag, 2026-10-01 Active Contract rear-push pass on book_red: runs/check_50_rear_push, 2026-10-06.
