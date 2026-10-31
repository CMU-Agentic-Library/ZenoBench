---
name: empty-container
description: "Take every object out of a container and put it on/into a destination receptacle."
---

# Empty a container (`skill_051`)

`empty(container: container_ref, receptacle: receptacle_ref)`

Take every object out of a container and put it on/into a destination receptacle.

## When to use

A container must be emptied into another container or onto a surface.

## Not to be confused with

- `pour`: empty may also pick items out one by one.

## Inputs

- `container` (`container_ref`): The container to empty.
- `receptacle` (`receptacle_ref`): Where the contents go: a support or a container.

## Outputs

- `moved` (`object_list`): Objects that were taken out.

## Composite skill

Runs these Skill Contracts inside one call: `navigate`, `place`.

- One call runs the whole chain of the selected path below; each nested step is a full Skill Contract (preconditions, policy, postconditions on GT state). It counts as a single Contract call.
- The chain includes its own navigation: there is no need to navigate or approach first.
- The first nested step that fails stops the call with SUBSKILL_FAILED; the error names the failed nested action. Nothing is repaired or retried, and steps that already succeeded are not undone, so objects may have moved or still be held.

## Applicability

Requires hand_empty(hand=right); uncovered(container=$container).

## Preconditions (checked on live GT state before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing. GT: gripper_state.
- `uncovered(container=$container)` — No lid rests on the container rim. GT: object_pose, container_profile, asset_tags.

## Postconditions (verified on live GT state)

- `container_empty(container=$container)` — No annotated object is inside the container. GT: object_pose, container_profile.

## Verifier

after the policy chain, every listed predicate is evaluated on ground-truth simulator state (object poses, joint values, finger gaps, head-camera geometry, thermal state, event log); the node succeeds only if all hold for the selected path:

- `container_empty(container=$container)` (all paths)

## Policy paths (first match on the bound nouns)

### `pick_each_inside` — when always (default path)

1. `for each item in @container.contents: policy_092($container) -> policy_061($item) -> [navigate](destination=$receptacle) -> [place](object=$item, receptacle=$receptacle)`
- Take the items out one by one; empty never pours (pouring loose solids needs the cup past ~90 deg, which the arm cannot reach over the stove). To pour, call pour.

## Relations

- Previous step: `inspect` (`skill_012`) (then) — every object inside must be removed
- Fallback on failure: `uncover` (`skill_046`) (repair, repairs uncovered) — the container has its lid on
- Alternative: `clear` (`skill_050`) — the items lie on a surface instead

## Failure

Stop and report the error code and the measured pre- and postconditions. Nothing is retried or repaired automatically.


Paired Contract: `contract_059`.
