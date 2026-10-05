# policy_045 — slide_to_edge

把平物体推到可夹取的支撑面悬边

## Scope

One low-level controller invocation. Reported effect: `graspable_overhang`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_045.execute(...)`
- Legacy alias: `PolicySuite(rig).slide_to_edge.execute(...)`
- Class: `SlideToEdgePolicy`
- Availability: `verified`
- Direct Contract routes: contract_043
- Referenced as support by legacy families: contract_002, contract_006

## Recorded evidence

Isaac Sim: slide_to_edge book_red, 0.0885 m overhang, 2026-10-01
