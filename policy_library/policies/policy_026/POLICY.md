# policy_026 — push

按可达性选择推或顶部拖动物品

## Scope

One low-level controller invocation. Reported effect: `object_displaced`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `support`: positional_or_keyword; required
- `direction`: positional_or_keyword; required
- `distance`: positional_or_keyword; required
- `label`: keyword_only; optional
- `enough`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_026.execute(...)`
- Legacy alias: `PolicySuite(rig).push.execute(...)`
- Class: `PushPolicy`
- Availability: `verified`
- Skill Contract paths: contract_037:push/thin_auto
- Legacy family Contracts: contract_006

## Recorded evidence

Isaac Sim: pick_edge book_red 内部推书, 2026-10-01
