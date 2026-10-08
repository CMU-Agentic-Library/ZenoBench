# policy_056 — bimanual_flat_pick

左右手同时抓取宽书本或托盘

## Scope

One low-level controller invocation. Reported effect: `held_by_both_hands`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_056.execute(...)`
- Legacy alias: `PolicySuite(rig).bimanual_flat_pick.execute(...)`
- Class: `BimanualFlatPickPolicy`
- Availability: `callable`
- Skill Contract paths: contract_025:pick/two_hand_flat
- Referenced as support by legacy families: contract_002

## Caveat

book_red 同步接触后物体偏移 0.034 m、双指闭到零且抬升 0 m（runs/repair_bimanual_book_v7）；接触点移入物体 0.035 m 后无法找到无碰撞共享站位（v8）。旧试验短时抬起 0.037 m 后左手滑脱。
