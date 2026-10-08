# policy_079 — pull_toward_base

Drag an object toward the robot with pads on its top.

## Scope

One low-level controller invocation. Reported effect: `moved_toward_base(name)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `distance_m`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_079.execute(...)`
- Legacy alias: `PolicySuite(rig).pull_toward_base.execute(...)`
- Class: `PullTowardBasePolicy`
- Availability: `callable`
- Skill Contract paths: contract_038:pull/top_drag

## Recorded evidence

pending Isaac Sim check (skill library v2)
