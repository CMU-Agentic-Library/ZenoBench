# policy_065 — approach_target

Park where the right TCP reaches the target (IK-verified).

## Scope

One low-level controller invocation. Reported effect: `reachable(target)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `target`: positional_or_keyword; required
- `max_tries`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_065.execute(...)`
- Legacy alias: `PolicySuite(rig).approach_target.execute(...)`
- Class: `ApproachTargetPolicy`
- Availability: `callable`
- Skill Contract paths: contract_010:approach/park, contract_025:pick/floor_top

## Recorded evidence

pending Isaac Sim check (skill library v2)
