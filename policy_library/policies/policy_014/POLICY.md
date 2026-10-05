# policy_014 — pick_floor_corner

从地面平物体侧面和顶部夹角抓取

## Scope

One low-level controller invocation. Reported effect: `held(object)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_014.execute(...)`
- Legacy alias: `PolicySuite(rig).pick_floor_corner.execute(...)`
- Class: `FloorCornerPickPolicy`
- Availability: `callable`
- Direct Contract routes: contract_012, contract_028
- Legacy family Contracts: contract_002

## Caveat

toy_car、地面平书和薄 notebook 均未通过稳定夹持；薄 notebook 接触误差 0.0142 m，但抬升 0 m（runs/repair_floor_notebook_v1）；先执行 prepare_floor_reach 的路径也在关节移动时碰撞（v2）。
