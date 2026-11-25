"""The press's job (motion_skills.Job, the catalog's "press": docs/motion/MOTION_ARCHITECTURE.md section 6,
contact; 9.3 step 8): an appliance's annotated button -- the microwave's door and start keys, the stove's
power key -- pressed by the closed right fingertips.  Where the press ends is the button's own collider:
the tips PRESS_DEPTH into its face (scene_geometry.buttons gives the button an owner of its own), the hand
square to the face, every turn of the hand about the press one goal of the park search
(skill_plans.plan_press).  What the press switches -- a heat source on or off -- is an action of the plan
(Actuator.toggle), after the arm reached the button."""

from __future__ import annotations

import math

import numpy as np

from ..kinematics import PAD_TIP, gripper_rot
from ..park_search import VARIANT_COST, Problem
from ..predicates import entity_kind
from ..rig import SkillFailure
from ..skill_plans import PRESS_RELAY
from ..tolerances import PRESS_APPROACH, PRESS_DEPTH, TARGET_TOL

PRESS_ROLLS = (0.0, 90.0, -90.0, 180.0)   # deg the hand turns about the press (the closed tips are one blunt
#                                           tip whatever the turn), ranked in this order (VARIANT_COST each)
EVENTS = {"start_button": "microwave_start", "door_button": "microwave_door_button"}   # the events the
#                                           contracts and predicates read a press of these keys by


def _rz(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def microwave_food(rig, name):
    """The task foods inside ``name``'s cavity with its door closed -- what its start key may start on --
    else SkillFailure (the old _microwave_start_food)."""
    a = rig.ann.art(name)
    if rig.thermal is None:
        raise SkillFailure("microwave: thermal task state is not configured")
    if abs(rig.joint(name) - a["closed_q"]) > 0.10:
        raise SkillFailure("microwave: door must be closed before heating")
    b = a["cavity_aabb"]
    inside = []
    for obj in rig.thermal.config:
        p, _ = rig.obj_pose(obj)
        if all(b[i] + 0.005 < p[i] < b[i + 3] - 0.005 for i in range(3)):
            inside.append(obj)
    if not inside:
        raise SkillFailure("microwave: no task food is inside the cavity")
    return inside


def press_target(rig, button):
    """(the button's record, p, R0, u): the TCP where the press ends with the hand turned R0 (no turn about
    the press), u the unit the press goes in along.  The tips PRESS_DEPTH into the face of the button's
    collider (its world box's extent along the annotated outward from the annotated centre), the TCP PAD_TIP
    behind the tips."""
    kind, rec = entity_kind(rig.ann, button)
    if kind != "button":
        raise SkillFailure(f"press: {button} is not an annotated button")
    rig.sync_world()
    box = rig.kin.motion.button_box(button) if rig.kin.motion is not None else None
    if box is None:
        raise SkillFailure(f"press {button}: the button has no collider of its own (scene_geometry.buttons)")
    c = np.asarray(rec["center"], float)
    out = np.asarray(rec["outward"], float)
    out = out / np.linalg.norm(out)
    lo, hi = (np.asarray(v, float) for v in box)
    corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    face = float(np.max((corners - c) @ out))
    tips = c + out * (face - PRESS_DEPTH)
    return rec, tips + out * PAD_TIP, gripper_rot(-out, [1.0, 0.0, 0.0]), -out


def press_job(rig, args, state, skill=None):
    """motion_skills.Job of pressing ``args["button"]`` ("<appliance>/<key>", predicates.entity_kind) with
    the closed fingertips of the empty hand (the right where both are); ``args["on"]`` what the press switches
    its appliance's heat source to (None: nothing); ``args["door"]`` ("open" / "close", a door key): the press
    then drives the appliance's powered door there, from a park clear of its swing (plan_press press_door).  The microwave's start key switches the
    cycle on, only with its door closed and food inside (microwave_food).  Judged by where the arm got:
    a press that stopped short (run: TARGET_TOL) fails; the event the contracts read (EVENTS, else
    "button_press") logged after it."""
    from ..motion_skills import Job
    from .base import RigBase
    button = args["button"]
    empty = [sd for sd in ("right", "left") if (rig.held if sd == "right" else getattr(rig, "left_held", None)) is None]
    if not empty:
        raise SkillFailure("press: both hands hold something")
    side = empty[0]                     # the empty hand, the right where both are (as a door: door_hand)
    rec, p, R0, u = press_target(rig, button)
    app, key = rec["appliance"], rec["button"]
    on = args.get("on")
    food = microwave_food(rig, app) if key == "start_button" else None
    if key == "start_button":
        on = True
    toggle = None if on is None or rig.thermal is None or app not in rig.thermal.on else (app, bool(on))
    # the contact monitor names a static touch by the annotated obstacle box it is in: the button's own
    # (the microwave's "kitchen_microwave/body/door_button"), never the appliance's whole box
    seen_as = tuple(o["name"] for o in rig.ann.obstacles
                    if o["name"].startswith(app + "/") and o["name"].rsplit("/", 1)[-1] == key)
    door = None
    if args.get("door") is not None:    # a door key: the press drives the appliance's powered door there
        if key != "door_button":
            raise SkillFailure(f"press {button}: only a door key moves a door")
        a = rig.ann.art(app)
        door = {"part": app, "to": float(a["open_q"] if args["door"] == "open" else a["closed_q"])}
    presses, goals = [], []
    for j, deg in enumerate(PRESS_ROLLS):
        R = R0 @ _rz(deg)
        presses.append({"button": button, "p": p, "R": R, "u": u, "approach": PRESS_APPROACH, "toggle": toggle,
                        "seen_as": seen_as, "door": door, "roll": deg})
        goals.append(((p - PRESS_APPROACH * u, p), (p, R), VARIANT_COST * j))
    kin, base = rig.arm_kin(side), RigBase(rig)
    build_with = skill.build if skill is not None else None
    if build_with is None:
        from ..skill_plans import plan_press as build_with
    rest = (kin.rest,)

    def build(s, k, prior):
        return build_with(kin, s, presses[k], rest, prior=prior, base=base)
    problem = Problem(tuple(goals), build, PRESS_RELAY, near=rig.base_pose(), label=f"press {button}", hand=side)
    ctx = {}

    def no_park(diag):
        rig.log("press_no_park", button=button, diag=diag)
        return SkillFailure(f"press {button}: no base pose reaches the button "
                            f"({len(goals)} goals; rejected: { {k: v for k, v in diag.items() if v} })")

    def found_park(found):
        ctx["press"] = presses[found.k]
        rig.log("press_plan", button=button, hand=side, roll_deg=presses[found.k]["roll"],
                toggle=list(toggle) if toggle else None, door=door,
                end=np.round(p, 4).tolist(), park=[round(found.x, 3), round(found.y, 3), round(found.yaw, 1)])
        rig.caption = f"PRESS {button}"

    def pressed(r):
        k = r.arm_kin(side)
        tcp, _ = k.tcp(r.q() if side == "right" else r.left_q())
        ctx["miss"] = float(np.linalg.norm(tcp - p))

    def ready(found):
        press = presses[found.k]

        def rebuild(state_, frm, prior):
            return build_with(kin, state_, press, rest, start=frm, prior=prior, base=base)
        return found.plan, rebuild, {"press_in": {"after": pressed}}

    def done():
        miss = ctx.get("miss")
        if miss is None or miss > TARGET_TOL:
            raise SkillFailure(f"press {button}: the tips stopped {miss if miss is not None else float('nan'):.3f} m "
                               f"off the press's end")
        now = bool(rig.thermal.on.get(app)) if rig.thermal is not None and app in rig.thermal.on else None
        label = EVENTS.get(key)
        if label == "microwave_start":
            rig.log(label, food=food, button_error_m=round(miss, 4))
        elif label is not None:
            rig.log(label, button_error_m=round(miss, 4))
        rig.log("button_press", button=button, appliance=app, error_m=round(miss, 4), on=now)
        return now if now is not None else True
    return Job(problem=problem, no_park=no_park, found=found_park, ready=ready, done=done)
