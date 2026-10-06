# policy_057 — bimanual_box_lift

左右手从两侧协同抬起箱子

## Scope

One low-level controller invocation. Reported effect: `box_lifted_by_both_hands`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_057.execute(...)`
- Legacy alias: `PolicySuite(rig).bimanual_box_lift.execute(...)`
- Class: `BimanualBoxLiftPolicy`
- Availability: `callable`
- Referenced as support by legacy families: contract_002

## Caveat

serving_tray 与地面轻篮的双臂接触搜索在 45 秒预算内均找不到无碰撞共享站位（runs/repair_bimanual_box_v3、repair_bimanual_basket_v3）。 新生成的 small_storage_bin 在书架顶部也未找到无碰撞双手共享站位（runs/check_new_bin_bimanual）。
