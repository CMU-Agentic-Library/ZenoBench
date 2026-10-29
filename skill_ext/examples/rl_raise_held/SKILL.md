---
name: rl_raise_held
description: Lift the held object up by about 5 cm with a learned (linear) RL policy loaded from weights.json.
version: 1
parameters:
  object: {type: object_ref, required: true}
preconditions:
  - holding(hand=right, object=$object)
effects:
  - holding(hand=right, object=$object)
executor:
  type: rl
  entry: policy.py:LinearPolicy
  config: {weights: weights.json}
  action_space: ee_delta
  observation: [proprio]
  max_steps: 10
---

# rl_raise_held

Template for an RL policy: weights are loaded from a file next to this SKILL.md (here a tiny linear
policy, numpy only). Replace `policy.py` with your network; keep `reset` / `act`.
