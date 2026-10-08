# policy_059 — handover_right_to_left

把右手物品交给左手

## Scope

One low-level controller invocation. Reported effect: `held_by_left_hand`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_059.execute(...)`
- Legacy alias: `PolicySuite(rig).handover_right_to_left.execute(...)`
- Class: `HandoverRightToLeftPolicy`
- Availability: `callable`
- Skill Contract paths: contract_030:handover/right_to_left
- Referenced as support by legacy families: contract_002

## Caveat

toy_block 无分离的第二抓点；breakfast_bowl 右手抓取成功，但 15 个独立左手预抓候选即使忽略碰撞也超出关节可达性（runs/repair_handover_bowl_v3）；反向夹爪姿态的 30 个候选仍不可达（v5）。
