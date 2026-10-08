# policy_090 — wait_heat

Wait until food reaches a temperature, then switch the source off.

## Scope

One low-level controller invocation. Reported effect: `temperature_at_least(name, t)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `min_temp_c`: positional_or_keyword; required
- `appliance`: positional_or_keyword; required
- `max_wait_s`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_090.execute(...)`
- Legacy alias: `PolicySuite(rig).wait_heat.execute(...)`
- Class: `WaitHeatPolicy`
- Availability: `callable`
- Skill Contract paths: contract_051:heat/stove_pot

## Recorded evidence

pending Isaac Sim check (skill library v2)
