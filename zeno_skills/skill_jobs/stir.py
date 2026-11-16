"""The stir's job (motion_skills.Job, the catalog's "stir": docs/MOTION_ARCHITECTURE.md section 6, contact;
docs/skills/stir.md): a held spoon dipped into a pot and turned round inside it -- every way to hold it over
the pot (the hand turned about the vertical, the circle's radius) one goal of the park search, the whole stir
planned there (skill_plans.plan_stir); the turns counted from the tip as the simulator has it while it runs."""

from __future__ import annotations

import math

import numpy as np
from scipy.spatial.transform import Rotation

from ..evaluator import quat_R
from ..park_search import VARIANT_COST, Problem
from ..predicates import memory, objects_inside
from ..rig import SkillFailure
from ..skill_plans import STIR_RELAY, stir_tcp
from ..skills import check_held
from ..tolerances import STIR_ABOVE, STIR_DEPTH, STIR_RADII, STIR_TILT
from .carry import carry_posture
from .tool import free_end, tool_in_tcp

STIR_YAWS = (0.0, 90.0, -90.0, 180.0)   # deg the hand turns about the vertical over the pot (the old stir's four
#                                         sides of approach), ranked in this order (VARIANT_COST each)
STIR_ENDS = ("bowl", "handle")          # the spoon's annotated ends (tool_frame); the one away from the hand stirs
TIP_EVERY = 4                            # physics ticks between samples of the tip (60 Hz / 4: 15 a second)


def _tilted(R, t_tool):
    """R turned STIR_TILT about the horizontal across the tool so its tip (t_tool in the TCP frame) goes down."""
    axis = R @ (t_tool / np.linalg.norm(t_tool))
    side = np.cross(axis, [0.0, 0.0, 1.0])
    side = np.array([1.0, 0.0, 0.0]) if np.linalg.norm(side) < 1e-6 else side / np.linalg.norm(side)
    for sgn in (-1.0, 1.0):
        Rg = Rotation.from_rotvec(sgn * side * STIR_TILT).as_matrix() @ R
        if (Rg @ t_tool)[2] < 0:
            return Rg
    return Rg


def stir_job(rig, args, state, skill=None):
    """motion_skills.Job of stirring ``args["container"]`` with ``args["tool"]`` (held in the right hand)
    ``args["turns"]`` times (0: a dip -- the tip in and out, no circle).  The load first in the carry posture
    (carry_posture, the old stow_load); the tip -- the end of the spoon away from the hand, of its annotated
    STIR_ENDS (free_end, tool_in_tcp) -- STIR_DEPTH
    below the rim at the opening's centre, the spoon turned STIR_TILT down and the hand about the vertical
    in STIR_YAWS, on circles of STIR_RADII (the widest built first: Problem.tiers), each one goal of the park
    search.  After the drive the plan run with the stir's hooks: the tip sampled every TIP_EVERY ticks while
    it dips and circles -- counted inside once within the rim's radius and below the rim, the angle it sweeps
    round the opening's centre summed (the old stir's rule, now on every tick it runs instead of 16 points a
    turn).  Then judged: at least one turn inside (memory "stirred"), or for a dip the tip inside ("dipped")."""
    from ..motion_skills import Job
    tool, container, turns = args["tool"], args["container"], float(args.get("turns", 1.25))
    verb = "stir" if turns > 0 else "dip"
    if rig.held is None or rig.held["name"] != tool:
        raise SkillFailure(f"{verb}: {tool} is not right-held")
    ca = rig.ann.asset_of(rig.ann.objects[container]).get("container")
    if not ca:
        raise SkillFailure(f"{verb}: {container} is not a container")
    carry_posture(rig, label=f"{verb}_carry")
    check_held(rig, f"{verb}_carry", open_hand=False)
    rig.sync_world()
    from ..run import observe
    st0 = observe(rig)
    T_pot = (st0.objects or {}).get(container)
    if T_pot is None:
        raise SkillFailure(f"{verb}: {container} is not in the collision model")
    T_pot = np.asarray(T_pot, float)
    end = free_end(rig, st0, tool, STIR_ENDS)          # the end not in the hand goes in the pot
    T_tool = tool_in_tcp(rig, st0, tool, end)
    t_tool = T_tool[:3, 3]
    st = rig.state()
    cb = np.asarray(rig.geo.bottom(container, st), float)
    rim_r = float(ca.get("rim_radius") or min(ca["bands"][0][2:4]))
    rim_top = float(cb[2] + ca["rim_height"])
    depth = min(STIR_DEPTH[0], float(ca["rim_height"]) - STIR_DEPTH[1])
    centre_w = np.r_[cb[:2], rim_top - depth]
    centre = (np.linalg.inv(T_pot) @ np.r_[centre_w, 1.0])[:3]        # in the pot's box frame
    _, R0 = rig.kin.tcp(rig.q())
    R_tilt = _tilted(np.asarray(R0, float), t_tool)
    radii = (min(STIR_RADII[0], 0.45 * rim_r),) + tuple(STIR_RADII[1:])
    touch = (container,) + tuple(objects_inside(rig, container, st))
    above = depth + STIR_ABOVE
    stirs, goals, tiers = [], [], []
    for i, r in enumerate(radii):
        for j, deg in enumerate(STIR_YAWS):
            Rw = Rotation.from_euler("z", math.radians(deg)).as_matrix() @ R_tilt
            stir = {"pot": container, "c": centre, "r": float(r), "R": T_pot[:3, :3].T @ Rw, "t_tool": t_tool,
                    "turns": turns, "above": above, "touch": touch, "yaw": deg,
                    "axes": (T_pot[:3, :3].T @ [1.0, 0.0, 0.0], T_pot[:3, :3].T @ [0.0, 1.0, 0.0])}
            pts = [T_pot @ stir_tcp(stir, a) for a in (0.0, 0.5 * math.pi, math.pi, 1.5 * math.pi)]
            dip = pts[0]
            top = dip[:3, 3] + [0.0, 0.0, above]
            stirs.append(stir)
            goals.append(((top,) + tuple(T[:3, 3] for T in pts), (dip[:3, 3], dip[:3, :3]), VARIANT_COST * j))
            tiers.append(i)
    kin = rig.kin
    build_with = skill.build if skill is not None else None
    if build_with is None:
        from ..skill_plans import plan_stir as build_with

    def build(s, k, prior):
        return build_with(kin, s, stirs[k], prior=prior)
    problem = Problem(tuple(goals), build, STIR_RELAY, near=rig.base_pose(), label=f"{verb} {container}",
                      tiers=tuple(tiers))
    ctx = {"swept": 0.0, "prev": None, "dipped": False, "n": 0}
    tip_local = np.asarray(rig.ann.asset_of(rig.ann.objects[tool])["tool_frame"][end], float)

    def tip_inside():
        body, q = rig.obj_pose(tool)
        tip = np.asarray(body, float) + quat_R(q) @ tip_local
        rel = tip[:2] - cb[:2]
        return tip, bool(np.linalg.norm(rel) < rim_r and tip[2] < rim_top), math.atan2(rel[1], rel[0])

    def sample():
        ctx["n"] += 1
        if ctx["n"] % TIP_EVERY:
            return
        _, inside, ang = tip_inside()
        if inside:
            ctx["dipped"] = True
            if ctx["prev"] is not None:
                ctx["swept"] += abs((ang - ctx["prev"] + math.pi) % (2 * math.pi) - math.pi)
        ctx["prev"] = ang if inside else None

    class _Sampling:
        """The tip sampled on every tick while a segment runs (Rig.tick_watchers)."""
        def __enter__(self):
            rig.tick_watchers.append(sample)

        def __exit__(self, *exc):
            if sample in rig.tick_watchers:
                rig.tick_watchers.remove(sample)
            return False

    def no_park(diag):
        rig.log(f"{verb}_no_park", container=container, tool=tool, radii=[round(r, 3) for r in radii],
                diag=diag)
        return SkillFailure(f"{verb} {container}: no base pose reaches the stirring circle "
                            f"({len(goals)} goals; rejected: { {k: v for k, v in diag.items() if v} })")

    def found_park(found):
        stir = stirs[found.k]
        ctx["stir"] = stir
        rig.log(f"{verb}_plan", radius_m=round(stir["r"], 3), wrist_turn_deg=stir["yaw"], turns=turns,
                depth_m=round(depth, 3), touch=list(touch), end=end, t_tool=np.round(t_tool, 4).tolist(),
                park=[round(found.x, 3), round(found.y, 3), round(found.yaw, 1)])
        rig.caption = f"{verb.upper()} {container} with {tool}"

    def ready(found):
        stir = stirs[found.k]

        def rebuild(state_, frm, prior):
            return build_with(kin, state_, stir, start=frm, prior=prior)

        def after_dip(r):
            tip, inside, _ = tip_inside()
            ctx["dipped"] = ctx["dipped"] or inside
            r.log("dip_sample", tool=tool, container=container, tip=np.round(tip, 3).tolist(), inside=inside)
        return found.plan, rebuild, {"stir_dip": {"around": _Sampling, "after": after_dip},
                                     "stir_circle": {"around": _Sampling},
                                     "stir_back": {"after": lambda r: check_held(r, verb, open_hand=False)}}

    def done():
        if ctx["dipped"]:
            memory(rig).setdefault("dipped", {})[container] = True
        if turns <= 0:
            rig.log("dip_result", tool=tool, container=container, dipped=ctx["dipped"])
            if not ctx["dipped"]:
                raise SkillFailure(f"dip {container}: the tip did not get below the rim inside")
            return {"dipped": True}
        n_turns = ctx["swept"] / (2 * math.pi)
        memory(rig)["stirred"][container] = max(n_turns, memory(rig)["stirred"].get(container, 0.0))
        rig.log("stir_result", tool=tool, container=container, turns=round(n_turns, 2))
        if n_turns < 1.0:
            raise SkillFailure(f"stir {container}: {n_turns:.2f} turns inside")
        return n_turns
    return Job(problem=problem, no_park=no_park, found=found_park, ready=ready, done=done)
