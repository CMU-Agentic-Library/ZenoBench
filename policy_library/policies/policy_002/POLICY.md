# policy_002 — carry_navigate

右手持物移动并监测滑落

## Scope

One low-level controller invocation. Reported effect: `base_at(pose) and held`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `pose`: positional_or_keyword; required
- `name`: keyword_only; optional
- `min_bottom_z`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_002.execute(...)`
- Legacy alias: `PolicySuite(rig).carry_navigate.execute(...)`
- Class: `CarryNavigatePolicy`
- Availability: `verified`
- Direct Contract routes: contract_010
- Legacy family Contracts: contract_001

## Recorded evidence

Isaac Sim: pick_and_carry toy_block, 2026-10-01
