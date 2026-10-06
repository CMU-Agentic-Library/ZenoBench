# Kitchen pot demo

This scene adds `handled_cooking_pot` to the existing house's kitchen counter. It is a grasp demonstration scene, separate from the ten ZenoBench task specs. The pot is an open vessel with two side handles and a rigid overhead bail. Its 26 mm bail grip is narrower than Zeno's 80 mm gripper opening. The visual OBJ, collision OBJ, URDF, USD, shared asset annotation, and both side-handle/bail collision boxes are committed.

- [Scene spec](../../scene_specs/kitchen_pot.json), [USD scene](scene.usd), [scene annotation](annotation.json)
- [Kitchen close view](check/pot_close.png), [stability check](check/check.json)
- [Handle Contract smoke plan](pick_handle.plan.json), [top-pinch policy smoke plan](pick_top.plan.json)

The seed-0 scene passed a three-second physics check with no unstable bodies and zero robot drift. A pot lift is **not yet verified**. `contract_025` found no reachable contact path from this kitchen setup (`runs/kitchen_pot_bail_pick/result.json`, recorded in [physical findings](../../skill_library/verification/FINDINGS.md)). The bail and rim remain annotated candidates for a revised GT approach; annotation alone does not establish a successful grasp.

To rebuild the scene after configuring `ISAACLAB_PYTHON` as in the root README:

```bash
$ISAACLAB_PYTHON tools/generate_procedural_assets.py
OMNI_KIT_ACCEPT_EULA=YES $ISAACLAB_PYTHON tools/prepare_assets.py --only handled_cooking_pot --convert
OMNI_KIT_ACCEPT_EULA=YES $ISAACLAB_PYTHON tools/build_tasks.py --spec scene_specs/kitchen_pot.json --out scenes/kitchen_pot --seed 0
OMNI_KIT_ACCEPT_EULA=YES $ISAACLAB_PYTHON tools/settle_scene.py scenes/kitchen_pot/scene.usd --seconds 5
OMNI_KIT_ACCEPT_EULA=YES $ISAACLAB_PYTHON tools/check_scene.py scenes/kitchen_pot/scene.usd --out scenes/kitchen_pot/check
OMNI_KIT_ACCEPT_EULA=YES $ISAACLAB_PYTHON tools/annotate_scene.py scenes/kitchen_pot/scene.usd scenes/kitchen_pot/annotation.json
OMNI_KIT_ACCEPT_EULA=YES $ISAACLAB_PYTHON tools/run_contracts.py --scene scenes/kitchen_pot/scene.usd --ann scenes/kitchen_pot/annotation.json --plan scenes/kitchen_pot/pick_handle.plan.json --out runs/kitchen_pot_handle_pick
```
