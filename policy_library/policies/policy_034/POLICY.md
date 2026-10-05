# policy_034 — carry_height_adjust

持物时把物品抬到安全携带高度

## Scope

One low-level controller invocation. Reported effect: `held_above(min_height)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `min_bottom_z`: positional_or_keyword; optional
- `tolerance`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_034.execute(...)`
- Legacy alias: `PolicySuite(rig).carry_height_adjust.execute(...)`
- Class: `CarryHeightAdjustPolicy`
- Availability: `verified`
- Direct Contract routes: contract_049
- Referenced as support by legacy families: contract_001

## Recorded evidence

Isaac Sim tidy_toys: held toy_block bottom raised to 0.1459 m for 0.15 m target (0.02 m tolerance), runs/verify_callable_toy_chain, 2026-10-01
