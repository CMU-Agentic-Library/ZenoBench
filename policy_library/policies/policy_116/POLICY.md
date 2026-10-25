# policy_116 — explore_furniture

Aim the head at every support layer (shelf, top) of one piece of furniture from stand-off poses in front of it, crouching for low shelves; a layer counts when no board of the piece hides it.

## Scope

One low-level controller invocation. Reported effect: `furniture_explored(furniture)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `furniture`: positional_or_keyword; required
- `max_views`: keyword_only; optional
- `min_spacing`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_116.execute(...)`
- Legacy alias: `PolicySuite(rig).explore_furniture.execute(...)`
- Class: `ExploreFurniturePolicy`
- Availability: `callable`
- Skill Contract paths: contract_079:explore_furniture/layers

## Recorded evidence

pending Isaac Sim check (skill library v2)
