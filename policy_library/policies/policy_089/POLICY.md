# policy_089 — wait_cool

Wait until food in the closed fridge cools.

## Scope

One low-level controller invocation. Reported effect: `temperature_at_most(name, t)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `max_temp_c`: positional_or_keyword; required
- `appliance`: positional_or_keyword; optional
- `max_wait_s`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_089.execute(...)`
- Legacy alias: `PolicySuite(rig).wait_cool.execute(...)`
- Class: `WaitCoolPolicy`
- Availability: `callable`
- Skill Contract paths: contract_052:chill/fridge_wait

## Recorded evidence

pending Isaac Sim check (skill library v2)
