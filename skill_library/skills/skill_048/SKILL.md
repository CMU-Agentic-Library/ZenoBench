---
name: collect-objects
description: Put every listed object into one container (fetch each in turn).
---

# Collect objects into a container (`skill_048`)

`collect(objects: object_list, container: container_ref)`

Put every listed object into one container (fetch each in turn).

## When to use

Several objects must go into one container.

## Not to be confused with

- `fetch`: collect repeats fetch into one container.

## Inputs

- `objects` (`object_list`): Objects to gather.
- `container` (`container_ref`): The container.

## Composite skill

Runs these Skill Contracts inside one call: `fetch`, `navigate`, `pick`, `place`.

- One call runs the whole chain of the selected path below; each nested step is a full Skill Contract (preconditions, policy, postconditions on GT state). It counts as a single Contract call.
- The chain includes its own navigation: there is no need to navigate or approach first.
- The first nested step that fails stops the call with SUBSKILL_FAILED; the error names the failed nested action. Steps that already succeeded are not undone, so objects may have moved or still be held.
- Exception: when a nested step fails a precondition that one of its declared repair fallbacks establishes (listed below), that repair runs once and the nested step is retried once.

Repairs a nested step may run once before its retry:

- `pick` failing `edge_overhang` → `expose` — a flat object cannot be pinched from the top: push it to the edge by hand, then pick the overhang
- `pick` failing `grasp_clearance` → `separate` — fingers have no room beside the object (grasp_clearance false)
- `pick` failing `is_open` → `open` — the object is inside a closed cabinet or appliance
- `place` failing `is_open` → `open` — the receptacle is behind a closed door
- `place` failing `uncovered` → `uncover` — the container has its lid on

## Applicability

Requires hand_empty(hand=right); uncovered(container=$container).

## Preconditions (checked on live GT state before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing. GT: gripper_state.
- `uncovered(container=$container)` — No lid rests on the container rim. GT: object_pose, container_profile, asset_tags.

## Postconditions (verified on live GT state)

- `all_inside(objects=$objects, container=$container)` — Every listed object is inside the container. GT: object_pose, container_profile.

## Verifier

after the policy chain, every listed predicate is evaluated on ground-truth simulator state (object poses, joint values, finger gaps, head-camera geometry, thermal state, event log); the node succeeds only if all hold for the selected path:

- `all_inside(objects=$objects, container=$container)` (all paths)

## Policy paths (first match on the bound nouns)

### `fetch_each` — when always (default path)

1. `for each item in $objects: [fetch](object=$item, receptacle=$container)`

## Relations

- Previous step: `count` (`skill_059`) (then) — the counted objects are gathered
- Previous step: `sweep` (`skill_067`) (then) — the cluster is then put into a container
- Next step: `close` (`skill_041`) (then) — the container sits in a cabinet that must be closed
- Alternative: `sort` (`skill_049`) — the objects belong in different containers

## Failure

Stop and report the measured predicates, completed policy steps and matching fallback skills. Nothing is retried automatically.


Paired Contract: `contract_056`.
