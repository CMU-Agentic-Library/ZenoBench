# policy_039 — right_joint_move

右臂关节沿碰撞检查路径移动

## Scope

One low-level controller invocation. Reported effect: `arm_at(joint_target)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `target`: positional_or_keyword; required
- `tolerance`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_039.execute(...)`
- Legacy alias: `PolicySuite(rig).right_joint_move.execute(...)`
- Class: `RightJointMovePolicy`
- Availability: `verified`
- Skill Contract paths: contract_018:reset/joint_home
- Referenced as support by legacy families: contract_002, contract_003, contract_004, contract_005, contract_006, contract_007, contract_008

## Recorded evidence

Isaac Sim tidy_toys: right_arm_joint_5 moved to 0.0318 rad for 0.04 rad command (0.03 rad tolerance), runs/verify_callable_arm_v4, 2026-10-01
