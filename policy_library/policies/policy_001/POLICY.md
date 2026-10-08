# policy_001 — empty_navigate

空手移动到底盘目标位姿

## Scope

One low-level controller invocation. Reported effect: `base_at(pose)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `pose`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_001.execute(...)`
- Legacy alias: `PolicySuite(rig).empty_navigate.execute(...)`
- Class: `EmptyHandNavigatePolicy`
- Availability: `verified`
- Skill Contract paths: contract_009:navigate/empty
- Legacy family Contracts: contract_001

## Recorded evidence

Isaac Sim tidy_toys: empty_goto reached (4.492,-2.146,30°), runs/verify_callable_toy_chain, 2026-10-01
