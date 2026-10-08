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
- Skill Contract paths: contract_025:pick/floor_top, contract_025:pick/top_pinch, contract_044:upright/pick_orient_place, contract_054:uncover/knob_lift_aside, contract_072:square/pick_rotate_place
- Legacy family Contracts: contract_002

## Recorded evidence

Isaac Sim: pick_top toy_block, 2026-10-01
