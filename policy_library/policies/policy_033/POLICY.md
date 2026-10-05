# policy_033 — click

物理按下有标注的门/启动按钮

## Scope

One low-level controller invocation. Reported effect: `button_contact`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; optional
- `button`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_033.execute(...)`
- Legacy alias: `PolicySuite(rig).click.execute(...)`
- Class: `ClickPolicy`
- Availability: `verified`
- Legacy family Contracts: contract_007

## Recorded evidence

Isaac Sim: click kitchen_microwave door, 2026-10-01
