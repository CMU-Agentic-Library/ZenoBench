---
name: raise_held
description: Lift the object in the right hand straight up by a given height with small end-effector steps.
version: 1
parameters:
  object: {type: object_ref, required: true}
  height_m: {type: positive_number, default: 0.06}
preconditions:
  - holding(hand=right, object=$object)
effects:
  - holding(hand=right, object=$object)
executor:
  type: scripted_policy
  entry: policy.py:RaiseHeld
  action_space: ee_delta
  observation: [proprio]
  max_steps: 12
---

# raise_held

A scripted closed-loop policy behind the same action interface a VLA or RL policy uses: it reads the
TCP height from proprioception and emits `ee_delta` actions until the hand is `height_m` higher.
