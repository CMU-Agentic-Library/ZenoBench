# policy_106 — knock_panel

Tap a closed panel twice with closed fingertips.

## Scope

One low-level controller invocation. Reported effect: `knocked(name)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `taps`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_106.execute(...)`
- Legacy alias: `PolicySuite(rig).knock_panel.execute(...)`
- Class: `KnockPanelPolicy`
- Availability: `callable`
- Skill Contract paths: contract_074:knock/panel_taps

## Recorded evidence

pending Isaac Sim check (skill library v2)
