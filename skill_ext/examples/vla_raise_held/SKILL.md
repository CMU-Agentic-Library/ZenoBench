---
name: vla_raise_held
description: Lift the held object a little, driven by a vision-language-action model from the head image and the instruction.
version: 1
parameters:
  object: {type: object_ref, required: true}
preconditions:
  - holding(hand=right, object=$object)
effects:
  - holding(hand=right, object=$object)
executor:
  type: vla
  entry: adapter.py:VLAAdapter
  config: {backend: mock, prompt: "lift the {object} a little"}
  action_space: ee_delta
  observation: [images, proprio, instruction]
  max_steps: 6
---

# vla_raise_held

Adapter template for a VLA model. `backend: mock` emits a fixed upward action so the template runs
without a model; set `backend: http` and `url` to query a served model with the head image (PNG,
base64) and the prompt, expecting `{"ee_delta": [dx, dy, dz], "gripper": ..., "terminate": bool}`.
