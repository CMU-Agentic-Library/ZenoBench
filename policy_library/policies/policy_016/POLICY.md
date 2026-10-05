# policy_016 — place_container

把物品放进容器

## Scope

One low-level controller invocation. Reported effect: `inside(object,container)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `container`: positional_or_keyword; required

## Binding and status

- Runtime: `PolicySuite(rig).policy_016.execute(...)`
- Legacy alias: `PolicySuite(rig).place_container.execute(...)`
- Class: `ContainerPlacePolicy`
- Availability: `verified`
- Direct Contract routes: contract_014
- Legacy family Contracts: contract_003

## Recorded evidence

Isaac Sim collect_fruits: apple placed inside fruit_basket (measured radial offset 0.075 m < 0.143 m), runs/verify_callable_container_apple, 2026-10-01
