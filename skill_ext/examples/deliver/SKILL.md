---
name: deliver
description: Carry one object to a support and put it down there (pick, drive, place) in one call.
version: 1
use_when: an object must be moved to a surface in another room or on other furniture and nothing has to be prepared first
parameters:
  object: {type: object_ref, required: true, description: the object to move}
  support: {type: support_ref, required: true, description: where to put it}
preconditions:
  - hand_empty(hand=right)
effects:
  - on(object=$object, support=$support)
  - hand_empty(hand=right)
related:
  fallbacks: [pick, place]
failure_modes: [the pick fails (not graspable from here), the place finds no free spot]
executor:
  type: scripted
  steps:
    - {skill: navigate, args: {destination: $object}}
    - {skill: pick, args: {object: $object}}
    - {skill: navigate, args: {destination: $support}}
    - {skill: place, args: {object: $object, support: $support}}
---

# deliver

A composite written by a user from built-in skills only. Each nested call is gated and verified like
a top-level call; the first failing step stops `deliver` and its error is returned (`SUBSKILL_FAILED`
with the failing step). Nothing is retried.
