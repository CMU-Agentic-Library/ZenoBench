# policy_013 — pick_edge

夹住伸出支撑面边缘的平板物体的厚度（捏取流程，thickness_pinch；推到边是 slide_to_edge）

## Scope

One low-level controller invocation. Reported effect: `held(object)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `max_candidates`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_013.execute(...)`
- Legacy alias: `PolicySuite(rig).pick_edge.execute(...)`
- Class: `EdgePickPolicy`
- Availability: `callable`
- Skill Contract paths: contract_025:pick/flat_overhang_ready, contract_025:pick/flat_edge, contract_036:flip/edge_roll
- Legacy family Contracts: contract_002
