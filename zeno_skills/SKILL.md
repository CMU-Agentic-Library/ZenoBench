---
name: zeno-skills
description: Annotation-driven manipulation skills for the Zeno Malo mobile manipulator in Isaac Sim (open/close supported articulated doors and drawers, pick/place annotated objects, navigate, and operate the microwave buttons). Use when scripting Zeno Malo rollouts, generating GT demonstrations, or needing privileged GT (grasp poses, handle frames, joint axes, support surfaces) for RL in the zeno_house scenes.
---

# Zeno Malo skills

这里的 skills 指底层注释驱动的控制代码，是 Contract 的内部实现，
不是规划器接口。上层规划器按动词调用的 Skill/Contract 定义在
[skill_library](../skill_library/README.md)。

The core grasp and geometry data come from annotations. Current appliance
skills also use scene-specific parking and camera defaults:

| file | content |
|---|---|
| `annotations/assets.json` | per asset type (object frame): size, mass, tags, container profile, grasp primitives (`rim_pinch`, `rim_pinch_rect`, `top_pinch`, `edge_pinch_after_push`), Zeno feasibility |
| `annotations/<scene>.json` | per scene (world frame): rooms, obstacles (furniture + wall segments), support surfaces (z, xy extent, clearance), articulated parts (joint, pivot, axis, limits, open/closed value, moving-part boxes, handle frame), objects (asset, body prim, room, support), robot start |

## Run

```bash
cd ZenoBench   # repository root
OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} tools/run_skills.py \
  --scene sim/zeno_house.usd --ann annotations/zeno_house.json --out runs/my_run \
  --plan "open KitchenCabinetFactory_7025538_spawn_asset_6631478" \
         "close KitchenCabinetFactory_7025538_spawn_asset_6631478"
# steps: open <art> | close <art> | pick <obj> | place <obj> <support> <x> <y> | goto <x> <y> <yaw>
```

## OOP policies and contracts

规划器按动词调用 Contract；skill_XXX、contract_XXX 和 policy_XXX 是内部记录编号，
PolicySuite 的旧属性名仍可用。逐项定义见
[Skill Library](../skill_library/README.md)、
[Contract Library](../contract_library/README.md) 和
[Policy Library](../policy_library/README.md)。

`PolicySuite(rig)` exposes the [115 policy entries](../docs/POLICY_CATALOG.md)
(`policy_001`–`policy_115`). For low-level debugging a policy can be called
directly, e.g. `PolicySuite(rig).pick_round_rim.execute("cup")`; the upper
planner never does this. It calls Contracts by verb, and each Contract chooses
its policies from the bound nouns. The eight legacy family
[contracts](../docs/CONTRACT_PROPOSAL.md) (`tools/run_contracts.py`, caller-chosen
routes) are slated for removal.

For an existing scene, construct `make_rig(..., handle_objects=("mug",))` before
calling `pick_cup_handle.execute("mug")`; the CLI detects this automatically.
A separate collision bar then represents the mug handle. `pick_from_cavity`
uses the measured release pose when the same rig has just placed the object
in the microwave. Its preloaded-object route has not passed physical
verification. See the [verification record](../docs/POLICY_VERIFICATION.md)
for which policies have passed physical checks.

## How each skill works

* **navigate** — fold the arm (collision-checked retreat), A* over free base
  cells (column + 3 cm), drive the holonomic base (anchor joint).
* **open / close** — `planner.find_park` searches base poses around the
  handle where pre-grasp → grasp is a collision-free continuous IK path *and*
  the whole robot can ride rigidly with the part from the current joint value
  to the goal (footprint + arm checked at 8 samples); among feasible parks the
  one needing the least wrist torque for the pull wins.  Side-hook grasp: the
  hand slides along the face, one finger between panel and bar, so the pull
  loads the bar through a finger's normal force.  Then closed loop: read the
  real joint value, place the base at the pose rigid with the part at
  (value + lead), repeat.  The part moves only through the grasp.
* **microwave door / start** — the complete-shell microwave uses two annotated
  physical buttons. Zeno presses the blue door button, then a powered PhysX
  hinge opens/closes the door; it presses the green start button to heat food
  inside the closed cavity. The generic handle-pull skill cannot currently
  operate this microwave. Heating uses a task-level temperature model.
* **pick** — grasp candidates from the asset annotation at the object's
  current pose, nearest-first; park search per candidate; approach, close,
  lift 7 cm; success = object rose and is still between the fingers.
* **place** — keeps the measured TCP→object offset from the grasp, parks,
  lowers onto the support at (x, y), releases, verifies the object rests on
  that support within 6 cm.

All joint targets are time-scaled to 60 % of the URDF velocity limits.
Success is measured from simulator state; failures raise `SkillFailure`.

## Kinematic / collision model

`kinematics.ArmKin`: exact FK from the URDF chain (torso lift, waist pitch,
7-DoF right arm and a separately driven 7-DoF left arm), TCP at the finger-pad centre (0.12 m along the gripper's
-Z), damped least-squares pose IK with analytic Jacobian (~17 ms per global
solve).  `collision.WorldModel`: sphere model of the robot vs. annotation
AABBs and the moving parts at their current joint values.  The gripper may
touch the part it operates, the wrist may not intersect it, and the rest of
the body keeps 6 cm from it.

## For RL

The same annotations give privileged observations / dense rewards: handle
frame and joint value (`SceneAnnotations.handle_pose`), grasp candidates in
world frame (`grasp_poses`), support regions, container profiles.
`zeno_skills.physics` holds the physics fixes used for both scenes and assets.
