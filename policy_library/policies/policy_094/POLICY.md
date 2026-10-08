# policy_094 — press_button

Press any annotated appliance button.

## Scope

One low-level controller invocation. Reported effect: `button_pressed(button)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `button`: positional_or_keyword; required
- `state`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_094.execute(...)`
- Legacy alias: `PolicySuite(rig).press_button.execute(...)`
- Class: `PressButtonPolicy`
- Availability: `callable`
- Skill Contract paths: contract_050:press/generic_key, contract_051:heat/stove_pot, contract_076:stop/stove_key_off

## Recorded evidence

pending Isaac Sim check (skill library v2)
