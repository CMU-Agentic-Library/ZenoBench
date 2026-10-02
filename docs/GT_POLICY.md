# Zeno House: atomic GT policy inventory

This document describes the code in this repository as of 2026-10-01. **GT policy means one reusable, target-parameterized action with a checked outcome at the skill-graph boundary**: `pick`, `place`, `open`, `close`, `navigate`, and supporting actions such as `push` and microwave control. Its internal controller may contain multiple motion stages. A call such as `pick(apple)` takes a target and the current privileged simulator/annotation state, selects a feasible strategy, executes it, and checks the actual result. `pick(apple)` and `pick(book_red)` use different branches and grasp geometry; they are not the same action trace.

`TaskPolicy` is the **task-level coordinator** that chooses and sequences atomic policies to satisfy goal predicates. Despite its Python name, it is the coordinator in the terminology used here. Task specs are benchmark instances, not separate atomic policies or trained models. These policies are annotation-driven scripted controllers with privileged state, not learned vision policies or optimal oracles.

In the Goal → sub-goal → skill sub-graph → contract → policy diagram, a skill node invokes an atomic policy with concrete arguments. A contract states the required and expected state of that invocation. For example, `pick(book_red)` needs a reachable book and should leave that book held. The repository has eight `ContractSpec` entries and a `ContractRunner` that binds a requested route, invokes its policy and checks shared measured postconditions. It does not yet plan a skill sub-graph or select routes automatically. Function preconditions, `SkillFailure`/`Dropped`, post-action measurements, and goal re-evaluation provide the execution checks. A policy family can serve many target-specific contracts.

## Where each layer lives

| Layer | Implementation | Responsibility |
|---|---|---|
| Task/goal data | `task_specs/*.json`, `tools/build_tasks.py` | Spawned objects, alternatives, placements, goal predicates, seeded USD scene and `task.json`. |
| GT annotations | `annotations/assets.json`, `annotations/<scene>.json`, `zeno_skills/annotations.py` | Per-asset grasp types, size, mass and container shape; world object/support/obstacle geometry; joint, handle, moving-part, cavity and button geometry. |
| Task coordinator | `zeno_skills/task_policy.py:TaskPolicy` | Selects an unmet goal, object, alternative and destination; calls atomic policies and reacts to failures. |
| Atomic GT policies | `zeno_skills/policies/` class API backed by `zeno_skills/skills.py` | Bound `navigate`, `open`, `close`, `pick`, `place`, `push`, and microwave-start policies; target-specific geometry and control live in `skills.py`. |
| Motion and control | `zeno_skills/planner.py`, `kinematics.py`, `collision.py`, `rig.py` | A* base paths, base-park search, IK, collision checks, joint trajectories and PhysX feedback. |
| Goal evaluation | `zeno_skills/evaluator.py:TaskEvaluator` | Scores the final simulator state independently of the coordinator decision log. |

`tools/run_task.py` runs the coordinator through `PolicySuite` and records a result and video. `tools/run_skills.py` runs a **manually supplied** atomic-policy sequence through `PolicySuite`, including the finer-grained routes documented in the README. The manual `open`/`close` commands also dispatch to the powered microwave door; `click <appliance> start` presses its annotated start button when the heating preconditions hold.

## Atomic policy interfaces and outcome checks

| Policy call | State needed before/during execution | Action and measured result |
|---|---|---|
| `NavigatePolicy.execute(pose)` | Target `(x, y, yaw)`, obstacle geometry, whether an object is held | Tuck or carry the arm; plan and drive a base path. While carrying, check object-to-hand distance and finger gap; slip raises `Dropped`. No separate final pose assertion is made in this function. |
| `OpenPolicy.execute(name)` / `ClosePolicy.execute(name)` | Annotated articulated part, handle, joint type and limits, feasible arm/base pose | Hook handle, follow measured joint motion, release; compare measured joint value with open/closed target, else raise `SkillFailure`. |
| `PickPolicy.execute(name)` | Asset has at least one annotated grasp type; object pose is known, and a support is needed for the edge branch | Dispatch to object-specific grasp branch, approach, close, lift; require finger separation and measured object lift. Store measured hand-to-object transform in `rig.held`. |
| `PushPolicy.execute(name, support, direction, distance)` | Object rests on annotated support with a reachable push or drag path | Push or top-drag in short segments; require measured progress on each segment. |
| `PlacePolicy.execute(name, support, xy)` / `.on(...)` | Named object is currently held; target support or container exists | Carry, aim, release, settle; check `geo.on` plus position tolerance or `geo.inside`. Edge-held flat objects dispatch to `place_flat`. |
| `MicrowaveStartPolicy.execute(name)` | Thermal state configured; door closed; task food in annotated cavity | Press annotated start button, check fingertip proximity, activate task-level heating. |
| `OpenPolicy.execute("kitchen_microwave")` / `ClosePolicy.execute("kitchen_microwave")` | Annotated blue button and powered hinge available | Open: press button, move clear and open the physical hinge. Close: move clear and close it. Each checks the measured joint target. `MicrowaveDoorCycle` composes the two for a demonstration. |

All these calls can fail. The coordinator decides whether to retry, choose another object/support, or re-evaluate the task; a failed atomic call does not itself create a new high-level goal plan.

### Finer-grained executable routes

`PolicySuite` retains the general `pick`, `place`, `open`, `close`, and `navigate`
entry points, and now exposes route-specific policies in `zeno_skills/policies/`:
`pick_top`, `pick_round_rim`, `pick_rect_rim`, `pick_edge`, `pick_floor_corner`;
`place_surface`, `place_container`, `place_edge`, `place_microwave`;
`open_handle`, `close_handle`, `open_powered`, `close_powered`;
`empty_navigate`, `carry_navigate`; and the measured posture policies
`tuck_arm`, `lower_torso`, `raise_torso`, `set_torso_height`,
`lean_forward`, `straighten_waist`, `set_waist_pitch`, and `click`. A route checks its
required grasp type or held-object state before invoking the existing motion
controller. The smaller `right_gripper_open`, `right_gripper_close`, `right_tcp_move`,
`right_joint_move`, `carry_height_adjust`, `back_off_with_load`,
`push_from_behind`, and `top_drag` policies each expose a single actuator or
contact route with a measured result. `base_rotate_in_place` and
`base_translate_local` add checked local base motions with an empty hand and tucked arm.
Gripper closure reports finger positions,
not a grasp; the pick policy verifies contact and lift. `push_from_behind` and
`top_drag` fix the contact mode, while the general `push` may choose between them.
The general `pick` path still selects candidates and fallback from
the annotation, so existing task results do not depend on explicitly choosing
a route.

`pick_and_carry` is a **sequential composition** of pick and carry navigation.
The established book route still pushes with the right arm and edge pinches.
The new `bimanual_flat_pick` route has separate left-arm IK, gripper control,
paired-arm collision checks, and two contact points. An Isaac Sim book trial
briefly lifted 3.7 cm, but the left grasp subsequently slipped; stable two-hand
pickup has not passed. The
new synchronized base/arm controller passed a moving reach and a moving
`toy_block` pickup; moving placement released an apple onto the dining table before the base stopped. See the
[capability catalog](POLICY_CATALOG.md) for each route's status and caveat.
Eight `ContractSpec` objects connect direct routes to a measured `ContractRunner`.
The [verification record](POLICY_VERIFICATION.md) separates 54 scene-verified routes from six callable routes that still lack a successful object-level test. A skill sub-graph planner is not implemented.

## `pick`: object-specific policies

`pick` first reads the asset's `grasps` list. If it is empty, it fails immediately. If a top/rim pinch exists, it tries that first. If the asset also allows `edge_pinch_after_push`, a failed pinch can fall back to the edge route while nothing is held. The selected candidate must admit a reachable base park and approach/lift IK path. After parking, the policy re-reads the object's pose, opens to the annotated width, approaches, closes, lifts, and checks finger separation and object rise. Pinch lifts must raise the object more than 1.5 cm; floor corner pinch requires more than 3 cm. Thus an annotation is a **candidate**, not proof of physical success.

The annotation generator in `zeno_skills/annotations.py:grasp_poses` rotates grasp geometry with the object's current yaw. For top grasps it uses the asset's `offset_xy`, `height`, `close_yaw` and `pre_open`; for round rims it enumerates azimuth and tilt; for rectangular rims it tests four sides and tilt. `zeno_skills/skills.py` then filters these geometric candidates through reachability and collision tests. These parameters differ by object even when two objects use the same branch.

| Object(s) in `annotations/assets.json` | First strategy and object-specific distinction | Alternative/limit |
|---|---|---|
| `apple`, `orange` | `top_pinch` at each fruit's annotated width and height; the orange has a different closing yaw from the apple. | No annotated edge fallback. |
| `banana` | `top_pinch` across its narrow section, with a shifted contact point (`offset_xy`) and rotated closing axis to account for its long curved footprint. | `edge_pinch_after_push` if direct pinch fails. |
| `breakfast_spoon`, `pen`, `pencil` | Narrow `top_pinch` across each utensil's shaft, with different widths, heights and offsets; approach height is kept above the support. | Each also has an annotated push/edge fallback. |
| `toy_car`, `toy_block` | `top_pinch` using their respective widths and heights; the car is elongated and also has an edge option. | Block has no annotated edge fallback. |
| `teddy_bear`, `rubber_duck` | `top_pinch` at distinct off-centre contact points: teddy's crown and the duck's offset top. | No annotated edge fallback. |
| `breakfast_bowl`, `breakfast_cup`, `breakfast_mug` | `rim_pinch`: sample multiple azimuths/tilts at each object's **own** rim radius and height; pinch the wall below the rim, not across the full body. | Cup, mug and bowl are different sizes/weights; a common rim template does not imply the same grasp pose or outcome. |
| `fruit_basket` | `rim_pinch` around its larger circular rim. | Reach and holding remain physical constraints. |
| `serving_tray` | `rim_pinch_rect` tests four rectangular sides and tilt angles. | Has an annotated push/edge fallback. |
| `toy_box`, `storage_basket` | `rim_pinch_rect` on their separately sized rectangular rims. | Annotation marks them graspable, but the large/heavy box still has to pass reach, collision and lift checks. |
| `breakfast_plate`, `notebook`, `book_red`, `book_green`, `book_blue` | Only `edge_pinch_after_push`: choose a free support edge, push until the item overhangs, then approach horizontally from outside and pinch its thickness. | If already on the floor, use the diagonal `corner_pinch`; if no free edge exists on a support, fail. |
| `cereal_box` | No `grasps` annotation; `graspable_by_zeno` is false. | `pick` fails immediately rather than inventing a grasp. |

For a surface-supported flat object, `pick_flat` checks which edge is open and has room outside it, how far the object's rotated footprint extends toward that edge, and whether the centre of mass stays inside the support. `push` moves it only as far as needed for a usable overhang. `_edge_pinch` keeps the lower pad outside the support edge, closes on the exposed thickness, lifts, and pulls out. On the floor there is no support edge: `_corner_pinch` contacts a side face and top face diagonally, avoiding a lower finger digging into the floor. Objects on a support with no usable free edge cannot take the floor route.

For ordinary pinch candidates, `_pick_pinch` searches feasible parks. An object on a recessed refrigerator shelf gets a seeded search from the open side; this is a scene-specific search preference, not a different grasp type. Floor objects set the arm's focus height low. Failed reach, collision, grip or lift checks raise `SkillFailure` for the coordinator.

## `place`: held object and destination both matter

`place` requires `rig.held["name"]` to match the requested object. The stored grasp kind determines the branch:

- **Pinch-held item onto a surface:** `place_on` scores free spots using the object's footprint, nearby objects and any hint; it tries up to four spots while still holding the object. `place` searches object yaw and a reachable base park, carries the object there, re-measures how it hangs in the fingers, lowers, opens the gripper and waits for settling. Success needs `geo.on` and XY error below 10 cm.
- **Corner-held flat item:** use the measured lowest corner to set release height. It may pivot flat on release, so the XY tolerance is 12 cm, still requiring `geo.on`.
- **Edge-held plate/book/notebook onto a surface:** `place_flat` finds a free target edge and room for the object's actual footprint, slides the held edge over the surface, releases, withdraws the lower finger, then pushes the object fully inward. Success needs `geo.on` and tilt at most 20°.
- **Any held item into `in:<container>`:** aim at the container centre using its annotated rim and current pose. For a deep container (rim height above 12 cm), release 3 cm above the rim instead of driving the wrist between its walls. After settling, require `geo.inside`.

A narrow cabinet or microwave cavity changes the free-spot clearance and park search. The complete-shell microwave uses a front-entry insertion path. Its placement route is independently callable as `microwave_cavity_insert` → `microwave_cavity_release` → `microwave_cavity_withdraw`; the final stage checks that the released object settled on the annotated cavity support, remains within cavity bounds, and is upright. Retrieval uses the same door-clear arm pose and withdraws the bowl horizontally before base motion; the full physical rollout is recorded below. The object can rotate or slip in the gripper during travel, so the policy re-measures its hand-to-object offset before lowering and checks that it remains held. Placement success is measured from the final simulator state, not from the commanded hand pose alone.

## `open` and `close`: articulated target changes the motion

`open_articulated` and `close_articulated` share `_move_articulated`, but use the target part's annotated handle, `closed_q`, `open_q`, joint type and live joint value. A revolute door requires a hinge-following base/arm trajectory; a prismatic drawer requires a linear one and may be approached from either handle end. The park search checks a continuous approach to the handle and samples whether the robot can ride the entire part motion without collision. It favours feasible poses with lower wrist torque.

At the handle, the arm uses a side-hook grasp, checks finger separation, and the base follows the **measured** joint state with a small lead. After release and settling, the measured final value must be near the requested target. Revolute joints use a 0.10 rad tolerance. A closing drawer uses 0.04 m; an opening drawer allows some slide-back after release and is accepted within 40% of its travel. If the part moved while navigating to its park, the skill replans from its new joint value.

The complete-shell microwave has a separate control route. Button interaction is now independently callable as `microwave_button_approach` → `microwave_button_press` → `microwave_button_retract`; a press requires the measured alignment state, and retraction requires a measured press. Powered door motion is independently callable as `microwave_door_clear` → `microwave_hinge_drive`, with measured base clearance, an empty-arm tuck or held-object check, and a joint-angle result. The existing `open_microwave_door` composes the door-button stages and opens its powered PhysX hinge; `close_microwave_door` composes clearance and hinge close. `cycle_microwave_door` composes these two actions. This is **not** a successful generic handle pull; `open_articulated` does not currently operate that appliance reliably. `press_microwave_start` composes the green start-button stages and requires a closed door and food inside the cavity before enabling the task-level thermal model. This split adds policy executors under the previously proposed `click`, `open`, `close`, and `place` contract concepts; no new contract object is introduced.

## `navigate` and `push`: context-dependent atomic policies

`navigate` takes a concrete base pose. With empty fingers it tucks the arm before planning an A* path through annotated free space. While carrying, it first backs away from furniture, raises and pulls the item toward the body, plans with extra clearance when possible, and drives more slowly for a held container than for a solid object. After lifting and after travel, it compares the object's distance from the fingertip frame with the measured grasp offset and checks that the fingers have not shut; excessive slip raises `Dropped`. A missing path or inability to tuck raises `SkillFailure`.

`push` uses the target object's measured bottom pose, size/yaw and support height. It tries pushing from behind with closed downward-pointing fingertips; if that path cannot be reached, it tries pressing on top and dragging. It moves in segments of at most 25 cm, re-parks between segments, and checks measured object displacement. This is a separate atomic policy and also a step inside the flat-object pick branch and edge placement branch.

## Task-level coordination and evidence

`TaskPolicy.run` reads the evaluator's unmet conditions for up to three rounds by default. It prioritizes moving a bound container, then `heated`, `inside`, `on`, `near`, and `closed`; chooses among role slots (`all:toy`), ordered alternatives (`cup|mug`) and bindings (`$container`); retries failed grasps and spots; and can select another object or container. It re-evaluates goal predicates after actions. `upright` and `not_dropped` are evaluated, but there is no dedicated upright-recovery or floor-cleanup goal handler. This decision loop belongs **above** the atomic GT policy layer.

The table below records individual seed-0 rollouts, **not** multi-seed success rates. Archived results are in `media/tasks/`; local smoke results under `runs/` are ignored by Git.

| Task spec | Atomic policy sequence illustrated | Evidence |
|---|---|---|
| `collect_fruits` | Pick/place container, then object-specific fruit picks and container placements | [Archived result](../media/tasks/collect_fruits.result.json): 100% |
| `tidy_toys` | Floor/table picks, carry, place into toy box or basket | [Archived result](../media/tasks/tidy_toys.result.json): 100% |
| `shelve_books` | Push, edge pinch, carry and edge placement | [Archived result](../media/tasks/shelve_books.result.json): 100% |
| `desk_prep` | Place notebook, pen/pencil and mug/cup | [Archived result](../media/tasks/desk_prep.result.json): 100% |
| `breakfast_setup` | Place plate/bowl, cup/mug and spoon | [Archived result](../media/tasks/breakfast_setup.result.json): 66.7%; cup/mug remains unsatisfied |
| `heat_breakfast_preloaded` | Microwave start press and thermal wait | Current-scene local run `runs/heat_breakfast_preloaded_current/result.json`: 100% |
| `heat_breakfast_combo` | Microwave door-button cycle and start, fetch milk from fridge, close fridge | [Archived result](../media/tasks/heat_breakfast_combo.result.json): 100%; [video](../media/tasks/heat_breakfast_combo.mp4) |
| `heat_breakfast` | Fridge bowl pick → microwave front-entry placement → close/start/heat → reopen/retrieve → close → table place → fridge close | [Archived result](../media/tasks/heat_breakfast.result.json): 100% seed-0 rollout; [video](../media/tasks/heat_breakfast.mp4); 63.6 °C, upright at table, doors closed; see [status](../tasks/heat_breakfast/STATUS.md). |

Zeno Malo's base uses a kinematic anchor; its arm and finger joints use drive targets. Object contact and articulated response occur in PhysX; the powered microwave hinge uses its joint drive. Temperature is a separate task-level model (`zeno_skills/thermal.py`), increasing only while the microwave is active, closed, and food is in the annotated cavity. This GT baseline uses no camera image, detector or language model. `heat_breakfast_combo` starts with oatmeal **already inside** the microwave; the separate full `heat_breakfast` rollout above demonstrates refrigerator-to-microwave loading and retrieval.

Run a task from the `zeno-house` repository root:

```bash
OMNI_KIT_ACCEPT_EULA=YES $ISAACLAB_PYTHON tools/run_task.py --task heat_breakfast_combo
```
