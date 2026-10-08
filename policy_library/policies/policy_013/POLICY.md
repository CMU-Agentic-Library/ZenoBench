# policy_013 — pick_edge

先推到桌边，再夹住悬出的平物体

## Scope

One low-level controller invocation. Reported effect: `held(object)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_013.execute(...)`
- Legacy alias: `PolicySuite(rig).pick_edge.execute(...)`
- Class: `EdgePickPolicy`
- Availability: `verified`
- Skill Contract paths: contract_025:pick/flat_overhang_ready, contract_025:pick/flat_edge, contract_036:flip/edge_roll
- Legacy family Contracts: contract_002

## Recorded evidence

Isaac Sim: pick_edge book_red, 2026-10-01
