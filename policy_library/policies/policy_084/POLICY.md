# policy_084 — wipe_surface

Press a held sponge on a support and sweep a strip.

## Scope

One low-level controller invocation. Reported effect: `wiped(support)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `tool`: positional_or_keyword; required
- `support`: positional_or_keyword; required
- `length`: keyword_only; optional
- `passes`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_084.execute(...)`
- Legacy alias: `PolicySuite(rig).wipe_surface.execute(...)`
- Class: `WipeSurfacePolicy`
- Availability: `callable`
- Skill Contract paths: contract_045:wipe/sponge_strip

## Recorded evidence

pending Isaac Sim check (skill library v2)
