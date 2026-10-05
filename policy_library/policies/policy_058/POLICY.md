# policy_058 — bimanual_carry

两只手共同稳定携带大物品

## Scope

One low-level controller invocation. Reported effect: `base_at(pose) and two_hand_hold`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `pose`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_058.execute(...)`
- Legacy alias: `PolicySuite(rig).bimanual_carry.execute(...)`
- Class: `BimanualCarryPolicy`
- Availability: `callable`
- Direct Contract routes: contract_029
- Legacy family Contracts: contract_001

## Caveat

旧 book_red 双手短时抬起后左手在底盘移动时滑脱；当前没有稳定双手抓持前置状态（runs/bimanual_carry_new_policy）。
