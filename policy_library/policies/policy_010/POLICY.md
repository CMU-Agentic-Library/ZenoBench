# policy_010 — pick_top

按物品标注的顶部接触点夹取

## Scope

One low-level controller invocation. Reported effect: `held(object)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `max_candidates`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_010.execute(...)`
- Legacy alias: `PolicySuite(rig).pick_top.execute(...)`
- Class: `TopPinchPickPolicy`
- Availability: `verified`
- Direct Contract routes: contract_012, contract_035
- Legacy family Contracts: contract_002

## Recorded evidence

Isaac Sim: pick_top toy_block, 2026-10-01
