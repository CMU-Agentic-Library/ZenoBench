# policy_053 — place_while_moving

底盘未停下时完成放置和松手

## Scope

One low-level controller invocation. Reported effect: `on(object,support) while base_moves`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `support`: positional_or_keyword; required
- `base_path`: positional_or_keyword; required
- `xy`: keyword_only; optional
- `speed`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_053.execute(...)`
- Legacy alias: `PolicySuite(rig).place_while_moving.execute(...)`
- Class: `PlaceWhileMovingPolicy`
- Availability: `verified`
- Skill Contract paths: contract_026:place/on_the_move
- Legacy family Contracts: contract_003

## Recorded evidence

Isaac Sim collect_fruits: apple released onto dining table at tick 3257 while base moved 0.078 m; base ended tick 3472, support bottom error 0.0377 m, runs/verify_callable_place_while_moving_apple_v2, 2026-10-01
