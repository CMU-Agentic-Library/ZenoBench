# policy_103 — wait_seconds

Let simulated time pass.

## Scope

One low-level controller invocation. Reported effect: `waited(seconds)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `seconds`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_103.execute(...)`
- Legacy alias: `PolicySuite(rig).wait_seconds.execute(...)`
- Class: `WaitPolicy`
- Availability: `callable`
- Skill Contract paths: contract_064:wait/idle

## Recorded evidence

pending Isaac Sim check (skill library v2)
