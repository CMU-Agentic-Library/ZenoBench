---
name: fetch-object
description: Bring one object to a support or container: navigate to it, pick it (noun-selected grasp path), navigate to the receptacle and place it (noun-selected placement path). Each step is a verified Skill Contract.
---

# Fetch an object to a receptacle (`skill_047`)

`fetch(object: object_ref, receptacle: receptacle_ref)`

Bring one object to a support or container: navigate to it, pick it (noun-selected grasp path), navigate to the receptacle and place it (noun-selected placement path). Each step is a verified Skill Contract.

## When to use

One object must be brought to a destination (navigate, pick, carry, place in one node).

## Not to be confused with

- `restore`: restore's destination is the object's starting support.
- `collect`: collect moves a list into one container.
- `pick`: fetch also carries and places the object.

## Inputs

- `object` (`object_ref`): What to bring.
- `receptacle` (`receptacle_ref`): Destination support or open container.

## Applicability

Requires hand_empty(hand=right). Depending on the bound nouns, the chosen path also needs: to_container (receptacle.kind == 'object'): uncovered(container=$receptacle).

## Preconditions (checked on live GT state before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing. GT: gripper_state.

## Postconditions (verified on live GT state)

- `hand_empty(hand=right)` — The given gripper holds nothing. GT: gripper_state.

## Verifier

after the policy chain, every listed predicate is evaluated on ground-truth simulator state (object poses, joint values, finger gaps, head-camera geometry, thermal state, event log); the node succeeds only if all hold for the selected path:

- `hand_empty(hand=right)` (all paths)
- `inside(object=$object, container=$receptacle)` (path to_container)
- `on(object=$object, support=$receptacle)` (path to_surface)

## May invalidate

`on($object,*)`, `inside($object,*)`, `at_initial_place($object)`, `base_near(*)`, `reachable(*)`

## Policy paths (first match on the bound nouns)

### `to_container` — when receptacle.kind == 'object'

1. `[navigate](destination=$object)`
2. `[pick](object=$object)`
3. `[navigate](destination=$receptacle)`
4. `[place](object=$object, receptacle=$receptacle)`
- extra precondition `uncovered(container=$receptacle)`
- extra postcondition `inside(object=$object, container=$receptacle)`

### `to_surface` — when receptacle.kind == 'support'

1. `[navigate](destination=$object)`
2. `[pick](object=$object)`
3. `[navigate](destination=$receptacle)`
4. `[place](object=$object, receptacle=$receptacle)`
- extra postcondition `on(object=$object, support=$receptacle)`

## Relations

- Previous step: `fetch` (`skill_047`) (enables) — more objects go to the same place
- Next step: `fetch` (`skill_047`) (enables) — more objects go to the same place
- Fallback on failure: `search` (`skill_013`) (recover) — the object is not where expected
- Alternative: `restore` (`skill_053`) — the object should return to its starting support
- Alternative: `swap` (`skill_054`) — only one object needs to move
- Alternative: `hide` (`skill_070`) — the object only needs to move

## Failure

Stop and report the measured predicates, completed policy steps and matching fallback skills. Nothing is retried automatically.


Paired Contract: `contract_055`.
