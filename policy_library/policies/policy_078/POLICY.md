# policy_078 — flip_flat

Turn an edge-held flat object over and lay it back.

## Scope

One low-level controller invocation. Reported effect: `flipped(name)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `release_deg`: keyword_only; optional
- `step_deg`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_078.execute(...)`
- Legacy alias: `PolicySuite(rig).flip_flat.execute(...)`
- Class: `FlipFlatPolicy`
- Availability: `callable`
- Skill Contract paths: contract_036:flip/edge_roll

## Recorded evidence

pending Isaac Sim check (skill library v2)
