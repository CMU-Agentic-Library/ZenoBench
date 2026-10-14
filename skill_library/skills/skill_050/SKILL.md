---
name: clear-support
description: Remove every object from a support surface to a destination receptacle.
---

# Clear a support (`skill_050`)

`clear(support: support_ref, receptacle: receptacle_ref)`

Remove every object from a support surface to a destination receptacle.

## When to use

Every object must be removed from one support.

## Not to be confused with

- `collect`: clear is defined by the source support, not by a list of objects.

## Inputs

- `support` (`support_ref`): The surface to clear.
- `receptacle` (`receptacle_ref`): Where the objects go.

## Outputs

- `moved` (`object_list`): Objects that were removed.

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

Requires hand_empty(hand=right).

## Preconditions (checked on live GT state before moving)

- `hand_empty(hand=right)` — The given gripper holds nothing. GT: gripper_state.

## Postconditions (verified on live GT state)

- `support_clear(support=$support)` — No annotated object rests on the support. GT: object_pose, support_annotation.

## Verifier

after the policy chain, every listed predicate is evaluated on ground-truth simulator state (object poses, joint values, finger gaps, head-camera geometry, thermal state, event log); the node succeeds only if all hold for the selected path:

- `support_clear(support=$support)` (all paths)

## Policy paths (first match on the bound nouns)

### `fetch_each_on_support` — when always (default path)

1. `for each item in @support.objects: [fetch](object=$item, receptacle=$receptacle)`

## Relations

- Next step: `wipe` (`skill_037`) (then) — the cleared surface is wiped
- Next step: `arrange` (`skill_052`) (then) — a new layout is set on the cleared surface
- Is a fallback for: `wipe` (`skill_037`) (recover) — objects cover the surface
- Is a fallback for: `arrange` (`skill_052`) (recover) — the support is too crowded
- Alternative: `empty` (`skill_051`) — the items lie on a surface instead

## Failure

Stop and report the measured predicates, completed policy steps and matching fallback skills. Nothing is retried automatically.


Paired Contract: `contract_058`.
