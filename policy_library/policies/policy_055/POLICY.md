# policy_055 — pick_cup_handle

从杯把而不是杯沿抓取

## Scope

One low-level controller invocation. Reported effect: `held(cup) by handle`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_055.execute(...)`
- Legacy alias: `PolicySuite(rig).pick_cup_handle.execute(...)`
- Class: `PickCupHandlePolicy`
- Availability: `verified`
- Skill Contract paths: contract_025:pick/handle_requested, contract_025:pick/handle
- Legacy family Contracts: contract_002

## Caveat

需要实际杯柄接触体：CLI 自动为 pick_cup_handle 目标补充，Python make_rig 需传 handle_objects；仅验证 breakfast_mug 的接触与短距离抬升。

## Recorded evidence

Isaac Sim breakfast_setup original scene: mug handle pinch lifted 0.0226 m with fingers 0.0121/0.0102 m open; runs/final_mug_handle, 2026-10-02
