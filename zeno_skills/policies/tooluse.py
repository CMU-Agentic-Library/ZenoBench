"""Tool-use policies with a held object.

policy_084 WipeSurfacePolicy   press a held sponge on a support and sweep a strip; measure contact coverage
policy_085 StirContainerPolicy dip a held spoon into a container and circle it (the motion-layer "stir")
policy_086 PourIntoPolicy      tilt a held cup over a container so its loose contents fall in

Each policy writes its measured result into rig.memory (wiped / stirred) or
leaves it in the scene (poured items), so the Contract's GT predicates verify it.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.spatial.transform import Rotation

from .base import AtomicPolicy
from .. import skills
from ..skill_jobs.carry import carry_posture
from ..clearance import FREE_ELSE_STRAIGHT, LEGACY, into_contact
from ..evaluator import quat_R
from ..planner import find_park, find_park_set
from ..predicates import memory, objects_inside
from ..rig import FINGERS_KW, Dropped, SkillFailure


def _park_diag():
    from ..planner import LAST_PARK_DIAG
    return {k: v for k, v in LAST_PARK_DIAG.items() if v}


def stow_load(rig, min_bottom_z=None):
    """Bring the held object into the compact carry pose (as navigation does)
    so a base re-park is not rejected for an arm still hanging over furniture.
    ``min_bottom_z`` keeps the load above a rim (a pour must not drop the cup
    from above the pot back to the low carry height)."""
    if rig.held is not None:
        carry_posture(rig, min_bottom_z=min_bottom_z, label="stow_load")
        skills.check_held(rig, "stow_load")


def _held_frame(rig, name):
    """TCP pose and the held body's pose expressed in the TCP frame."""
    tcp, R = rig.kin.tcp(rig.q())
    body, q = rig.obj_pose(name)
    Rb = quat_R(q)
    return tcp, R, R.T @ (body - tcp), R.T @ Rb


def _tcp_for_body(R_goal, body_goal, body_in_tcp):
    return body_goal - R_goal @ body_in_tcp




class WipeSurfacePolicy(AtomicPolicy):
    """Wipe a free 30 cm strip along an edge of a support with a held sponge: the wipe skill (skill_jobs.wipe.wipe_job,
    skill_plans.plan_wipe; HAND_PLAN 9g) with the hand that holds it -- the sponge pressed WIPE_PRESS into the
    surface and stroked there and back by the arm (the old policy held the arm and drove the base).  ``passes``:
    kept for the call's signature; a wipe is one stroke and its return."""

    def execute(self, tool, support, *, length=0.30, passes=2):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["wipe"], {"tool": tool, "support": support, "length": float(length)})


class StirContainerPolicy(AtomicPolicy):
    """Dip a held spoon into the container and turn its tip round inside it: the catalog's "stir" on the
    motion layers (skill_jobs.stir.stir_job, skill_plans.plan_stir; docs/skills/stir.md).  ``turns`` 0
    is a dip (DipUtensilPolicy): the tip in and out, no circle."""

    def execute(self, tool, container, *, turns=1.25):
        from ..motion_skills import SKILLS, run_skill
        return run_skill(self.rig, SKILLS["stir"], {"tool": tool, "container": container, "turns": turns})


class PourIntoPolicy(AtomicPolicy):
    """Hold the cup's far rim over the target, tilt it up to 120 deg about a
    horizontal axis through the TCP, hold, and return upright."""

    def execute(self, source, target, *, max_tilt_deg=120.0):
        rig = self.rig
        skills.right_hand_only(rig, source, "pour")
        if rig.held is None or rig.held["name"] != source:
            raise SkillFailure(f"pour: {source} is not right-held")
        st = rig.state()
        items = objects_inside(rig, source, st)
        if not items:
            raise SkillFailure(f"pour: {source} holds no items")
        ta = rig.ann.asset_of(rig.ann.objects[target]).get("container")
        if not ta:
            raise SkillFailure(f"pour: {target} is not a container")
        rim_z = float(rig.geo.bottom(target, st)[2]) + float(ta["rim_height"])
        stow_load(rig, min_bottom_z=rim_z + 0.03)
        st = rig.state()
        tb = np.asarray(rig.geo.bottom(target, st), float)
        tcp, R = rig.kin.tcp(rig.q_cmd)
        c_cup = rig.geo.centre(source, st)
        o_in = c_cup[:2] - tcp[:2]          # TCP -> cup centre (horizontal)
        u = o_in.copy()
        if np.linalg.norm(u) < 1e-3:
            u = np.array([1.0, 0.0])
        u /= np.linalg.norm(u)
        handle = rig.held.get("grasp") == "handle"
        if handle:
            # handle pinch: the pads close across the vertical bar, i.e. along
            # the tilt axis of a pour away from the handle, where only torsional
            # friction holds the cup.  Pour sideways (a wrist roll about the
            # forearm, as people do): the bar length resists that tilt
            u = np.array([-u[1], u[0]])
        cup_r = 0.5 * float(max(rig.ann.asset_of(rig.ann.objects[source])["size"][:2]))
        if handle:
            cup_r = float(rig.ann.asset_of(rig.ann.objects[source]).get("container", {}).get("rim_radius", cup_r))
        # 5 cm above the rim (higher poses, > 1.1 m, leave no wrist range to
        # tilt).  The cup turns about a point toward its pouring lip, as people
        # pour: turned about the hand, its body swung down onto the pot rim and
        # the tilt stalled near 30 deg however far the wrist turned
        lift = tb[2] + ta["rim_height"] + 0.05 - float(rig.geo.bottom(source, st)[2])
        src_rim = float((rig.ann.asset_of(rig.ann.objects[source]).get("container") or {}).get(
            "rim_height", rig.ann.asset_of(rig.ann.objects[source])["size"][2]))
        lip_dz = src_rim - float(tcp[2] - rig.geo.bottom(source, st)[2])     # lip height above the TCP

        def tilted(goal_, R_, u_, lip_xy_, ang_):
            """TCP pose with the cup turned by ang_ about a point half-way from
            the hand to its lip (lip_xy_ = TCP->lip): the body no longer swings
            down onto the target rim, and the hand rises only half as much as
            for a pivot at the lip itself (no wrist range left at 75 deg)."""
            ax_ = np.cross([0, 0, 1.0], np.r_[u_, 0.0])
            Rot = Rotation.from_rotvec(ax_ * math.radians(ang_)).as_matrix()
            pivot = goal_ + 0.5 * np.r_[lip_xy_, lip_dz]
            return pivot + Rot @ (goal_ - pivot), Rot @ R_
        rig.sync_world()
        rig.kin.coll_kw = {"ignore_fingers": True}
        park, planned_tilt = None, None
        R_in, u_in = R.copy(), u.copy()
        # far lip relative to the TCP: centre offset + rim radius along the pour
        # a rim-held cup also pours sideways: turned about the pinch's closing
        # axis its centre of mass stays on that axis, so the pads hold only the
        # carry torque, and the contents leave by a lip 90 deg from the fingers
        side_in = np.array([-u_in[1], u_in[0]])
        # (rim pinch: only "away" pours.  Turned about its closing axis the cup
        # swings in the pads like a pendulum -- a sideways pour tilted a bowl
        # 70 deg off the planned direction and kept the tomatoes in)
        variants = [(u_in, o_in + u_in * cup_r, 1), (-u_in, o_in - u_in * cup_r, -1)] if handle else \
            [(u_in, u_in * 2 * cup_r, 0)]
        # the cup's heading about the vertical does not matter for a pour:
        # turning the wrist (and the pour direction with it) opens other parks.
        # The tilted pose is part of the search: parking for the upright pose
        # alone left the wrist unable to tip the cup at all.
        bxy = np.array(rig.base_pose()[:2])
        to_base = bxy - tb[:2]
        to_base /= max(1e-9, np.linalg.norm(to_base))
        t_rim = 0.5 * float(min(rig.ann.asset_of(rig.ann.objects[target])["size"][:2]))
        # A full rim-held mug turns ~30 deg in the pads (80 commanded gave 48
        # measured; a 40 deg plan only 15): the largest commanded tilt first,
        # with any wrist turn; within a tilt the unturned wrist first
        combos = [(t_, p_, l_) for t_ in (110.0, 100.0, 90.0, 80.0, 70.0, 60.0, 40.0)
                  for p_ in (0.0, 45.0, -45.0, 30.0, -30.0, 60.0, -60.0, 90.0, -90.0, 180.0)
                  for l_ in (0.0, min(0.05, 0.5 * t_rim))]
        combos += [(None, 0.0, 0.0)]
        # an "away" pour (resisted by the whole pad contact) at >= 70 deg before
        # a sideways one: turned about the closing axis the cup still slips
        # (its centre of mass hangs below the pinch) and the low lip drifted
        # toward the inner finger, which held the tomatoes back
        # (away pours stop at 90 deg; sideways ones lag ~10 deg and an item
        # caught at the lip by the fingers only drops past 90)
        order = [(c_, v_) for c_ in combos for v_ in variants
                 if v_[2] == 0 and 70.0 <= (c_[0] or 0) <= 90.0] + \
                [(c_, v_) for c_ in combos for v_ in variants
                 if v_[2] != 0 or (c_[0] or 0) < 70.0]
        for (tilt, psi, lip), (u_base, lip_base, side) in order:
            Rz = Rotation.from_euler("z", math.radians(psi)).as_matrix()
            R, u = Rz @ R_in, (Rz @ np.r_[u_base, 0.0])[:2]
            lip_v = (Rz @ np.r_[lip_base, 0.0])[:2]
            # the cup lip over the opening: at the centre, or a little toward the robot
            goal = np.r_[tb[:2] + to_base * lip - lip_v, tcp[2] + lift]
            legs = [(goal, R)] + ([tilted(goal, R, u, lip_v, tilt)] if tilt else [])
            park = find_park(rig.kin, rig.world, legs, near=rig.base_pose(), max_tries=40 if tilt is None or psi else 80,
                             q_start=rig.q_cmd,
                             travel_q=skills._travel_q(rig))
            if park is not None:
                rig.log("pour_park", planned_tilt_deg=tilt, wrist_turn_deg=psi, lip_offset_m=lip,
                        direction={0: "away", 1: "side+", -1: "side-"}[side])
                planned_tilt = tilt
                break
        planned_goal, planned_R, planned_u, planned_lip = goal.copy(), R.copy(), u.copy(), lip_v.copy()
        if park is None:
            raise SkillFailure(f"pour: no base pose holds {source} over {target} (rejected: {_park_diag()})")
        # keep the cup above the target rim through the re-park (the default
        # carry lowered it to 0.6 m and the long sweep back up threw it out)
        # (12 cm over the rim: from 3 cm the bowl caught a soda can on the
        # counter end while the base turned; it is lowered at the pour pose)
        skills._goto_park(rig, park, min_bottom_z=rim_z + 0.12)
        rig.caption = f"POUR {source} into {target}"
        t0, R0 = rig.kin.tcp(rig.q_cmd)
        lift = float(planned_goal[2] - t0[2])
        if abs(lift) > 0.01:
            try:
                skills.held_vertical_move(rig, lift, "pour_raise")
            except SkillFailure as exc:
                # the pour pose itself was planned reachable: go there directly
                rig.log("pour_raise_direct", reason=str(exc))
                if rig.held is None:
                    raise
        # recompute after parking: the base pose may differ from the plan
        st = rig.state()
        tcp, R = rig.kin.tcp(rig.q_cmd)
        c_cup = rig.geo.centre(source, st)
        o_now = c_cup[:2] - tcp[:2]
        u = o_now / max(1e-9, np.linalg.norm(o_now))
        if side:
            u = np.array([-u[1], u[0]])
            if u @ planned_u < 0:
                u = -u
            far = tcp[:2] + o_now + u * cup_r
        else:
            far = tcp[:2] + u * 2 * cup_r
        goal = tcp + np.r_[tb[:2] - far, 0.0]
        lip_xy = far - tcp[:2]
        if not rig.kin.ik_global(goal, R, seeds=[rig.q_cmd])[1] or abs(np.degrees(np.arccos(
                np.clip(float(np.r_[u, 0.0] @ np.r_[planned_u, 0.0]), -1.0, 1.0)))) > 20.0:
            # the re-measured pose is out of reach, or the plan turns the wrist:
            # use the planned (verified) pose and pour direction
            rig.log("pour_over_planned", measured=np.round(goal, 3).tolist())
            goal, R, u, lip_xy = planned_goal, planned_R, planned_u, planned_lip
        rig.move_to(goal, R, step=0.005, steps_per_wp=5, label="pour_over", allow=FREE_ELSE_STRAIGHT, smooth=True)
        skills.check_held(rig, "pour_over")
        q_over = rig.q_cmd.copy()
        axis = np.cross([0, 0, 1.0], np.r_[u, 0.0])
        reached = 0.0
        top = min(max_tilt_deg, max(80.0, planned_tilt or 0.0))
        angles = [a_ for a_ in np.arange(20.0, top - 1e-6, 20.0)] + [top]
        jumped = False
        for ang in angles:
            goal_k, Rk = tilted(goal, R, u, lip_xy, ang)
            # the planned tilt configuration is a verified fallback for the
            # largest planned angle (the straight tilt path can lose its IK branch)
            hint = park[3][1] if planned_tilt and len(park[3]) > 1 and abs(ang - planned_tilt) < 1e-6 else None
            try:
                rig.move_to(goal_k, Rk, step=0.004, steps_per_wp=5, label="pour_tilt",
                            allow=FREE_ELSE_STRAIGHT, smooth=True,
                            q_hint=hint)
            except SkillFailure as exc:
                rig.log("pour_tilt_limit", deg=float(ang), reason=str(exc))
                if not (planned_tilt and ang < planned_tilt and len(park[3]) > 1):
                    break
                # the intermediate tilt has no IK on this branch: the planned
                # (verified) tilt configuration is reachable in joint space
                ang = float(planned_tilt)
                try:
                    rig.follow(rig.joint_path(park[3][1], "pour_tilt_planned",
                                              allow=FREE_ELSE_STRAIGHT), steps_per_wp=8)
                    skills.check_held(rig, "pour_tilt_planned")
                except Dropped:
                    raise
                except SkillFailure as exc2:
                    rig.log("pour_tilt_planned_failed", reason=str(exc2))
                    break
                rig.log("pour_tilt_planned", deg=ang)
                jumped = True
            reached = ang
            rig.step(90)
            st_t = rig.state()
            Rc = quat_R(st_t["objects"][source]["quat"])
            rig.log("pour_tilt_measured", cmd_deg=float(ang),
                    cup_tilt_deg=round(math.degrees(math.acos(float(np.clip(Rc[2, 2], -1, 1)))), 1),
                    cup_axis=np.round(Rc[:, 2], 3).tolist(), pour_dir=np.round(u, 3).tolist(),
                    items_z=[round(float(st_t["objects"][n]["pos"][2]), 3) for n in items])
            # stop tipping once the contents are out: a rim-held cup tipped
            # further slipped out of the pinch on the way back
            if not objects_inside(rig, source, rig.state()):
                rig.log("pour_emptied_at", deg=float(ang))
                break
            if jumped:
                break               # already at the planned (largest) tilt
        rig.step(180)
        # an item wedged at the lip (seen on video): rock the cup a little
        if reached >= 60.0 and objects_inside(rig, source, rig.state()):
            for k_ in range(3):
                for a_ in (reached - 12.0, reached):
                    goal_k, Rk = tilted(goal, R, u, lip_xy, a_)
                    try:
                        rig.move_to(goal_k, Rk, step=0.004, steps_per_wp=3, label="pour_rock", allow=FREE_ELSE_STRAIGHT)
                    except SkillFailure:
                        break
                rig.step(60)
                if not objects_inside(rig, source, rig.state()):
                    rig.log("pour_rock_emptied", rocks=k_ + 1)
                    break
        try:
            for ang in np.arange(reached - 10.0, -1e-6, -10.0):
                goal_k, Rk = tilted(goal, R, u, lip_xy, ang)
                rig.move_to(goal_k, Rk, step=0.002, steps_per_wp=8, label="pour_return",
                            allow=FREE_ELSE_STRAIGHT, smooth=True)
        except SkillFailure as exc:
            if rig.held is None:
                raise
            # no straight IK back from the planned tilt: retrace in joint space
            rig.log("pour_return_joint", reason=str(exc))
            rig.follow(rig.joint_path(q_over, "pour_return", allow=FREE_ELSE_STRAIGHT), steps_per_wp=10)
        skills.check_held(rig, "pour_return")
        rig.step(60)
        moved = [n for n in items if rig.geo.inside(n, target, rig.state())[0]]
        rig.log("pour_result", source=source, target=target, tilt_deg=reached, moved=moved, items=items,
                item_pos={n: np.round(rig.obj_pose(n)[0], 3).tolist() for n in items},
                target_centre=np.round(rig.geo.centre(target, rig.state()), 3).tolist(),
                cup_pos=np.round(rig.obj_pose(source)[0], 3).tolist())
        if len(moved) < math.ceil(len(items) / 2):
            raise SkillFailure(f"pour: {len(moved)}/{len(items)} items reached {target}")
        return moved
