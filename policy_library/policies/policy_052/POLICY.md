# policy_052 — pick_while_moving

底盘未停下时完成接触、闭爪和抬起

## Scope

One low-level controller invocation. Reported effect: `held(object) while base_moves`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `base_path`: positional_or_keyword; required
- `speed`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_052.execute(...)`
- Legacy alias: `PolicySuite(rig).pick_while_moving.execute(...)`
- Class: `PickWhileMovingPolicy`
- Availability: `verified`
- Skill Contract paths: contract_025:pick/on_the_move
- Legacy family Contracts: contract_002

## Recorded evidence

Isaac Sim tidy_toys: toy_block grasped while base traveled 0.072 m; closure tick 1138, lift tick 1255, base motion ended tick 1403; object lifted 0.065 m, 2026-10-01
