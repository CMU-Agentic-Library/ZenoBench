# Breakfast transfer task status

The seed-0 full refrigerator → microwave → dining-table rollout passed in Isaac
Sim on 2026-09-30, using the complete-shell microwave and its physical powered
door. The [recorded video](../../media/tasks/heat_breakfast.mp4) shows the
complete transfer. The archived [result](../../media/tasks/heat_breakfast.result.json)
reports `success: true` and `progress: 1.0` after 306.7 simulated seconds.
Oatmeal started at 4.0 °C in `breakfast_fridge`, was physically placed on
`kitchen_microwave/inside_floor`, heated to 63.6 °C, retrieved, and placed
upright on the dining table with 7.3 mm XY placement error. Both appliance
doors were closed and no object was on the floor at the final evaluation.

The complete sequence composes the atomic `open`, object-specific `pick`,
`place`, `close`, `microwave_start`, and `navigate` policies. Loading and
retrieval use front-entry paths through the open door; after retrieval the
microwave door closes before carrying the bowl across the kitchen. At the
dining table, the robot backs away, lifts the bowl above the tabletop, then
approaches the release point. The class API is in
[`zeno_skills/policies/`](../../zeno_skills/policies/) and usage is in the
[README](../../README.md#atomic-gt-policy-class-api).

Reproduce from the `zeno-house` repository root with Isaac Lab:

```bash
OMNI_KIT_ACCEPT_EULA=YES $ISAACLAB_PYTHON tools/run_task.py \
    --task heat_breakfast --no-video --max-seconds 1200 \
    --out runs/heat_breakfast
```

This result is one seed-0 rollout, not a measured success rate over seeds or
newly defined object layouts. The task builder checks spawn reachability and
scene physics; every new spec still needs a physical rollout to establish task
success.
