"""Tool-use policies with a held object.

policy_084 WipeSurfacePolicy   press a held sponge on a support and sweep a strip; measure contact coverage
policy_085 StirContainerPolicy dip a held spoon into a container and circle it; count turns below the rim
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
from ..evaluator import quat_R
from ..planner import find_park
from ..predicates import memory, objects_inside
from ..rig import Dropped, SkillFailure


def _park_diag():
    from ..planner import LAST_PARK_DIAG
    return {k: v for k, v in LAST_PARK_DIAG.items() if v}


def stow_load(rig, min_bottom_z=None):
    """Bring the held object into the compact carry pose (as navigation does)
    so a base re-park is not rejected for an arm still hanging over furniture.
    ``min_bottom_z`` keeps the load above a rim (a pour must not drop the cup
    from above the pot back to the low carry height)."""
    if rig.held is not None:
        skills._back_off(rig, dist=0.25)
        skills._carry_pose(rig, min_bottom_z=min_bottom_z)
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
    """Wipe a 30 cm strip of a support next to the robot with a held sponge.

    The arm presses the sponge and holds still while the holonomic base
    translates along the strip. The sponge bottom is pressed 1 mm below the surface; coverage is the
    fraction of 2 cm strip cells under the sponge footprint while its bottom
    was within 8 mm of the surface."""

    def execute(self, tool, support, *, length=0.30, passes=2):
        rig = self.rig
        if rig.held is None or rig.held["name"] != tool:
            raise SkillFailure(f"wipe: {tool} is not right-held")
        s = rig.ann.support(support)
        st = rig.state()
        x, y, yaw = rig.base_pose()
        x0, y0, x1, y1 = s["aabb_xy"]
        # the strip runs along the robot-side edge, 8 cm in: fingers-down
        # reach at counter height ends ~10 cm past the edge
        # the edge nearest the robot sets the inward direction (not the
        # offset to the centre: from behind a long counter that pointed along it)
        edges = [(abs(x - x0), np.array([1.0, 0.0])), (abs(x1 - x), np.array([-1.0, 0.0])),
                 (abs(y - y0), np.array([0.0, 1.0])), (abs(y1 - y), np.array([0.0, -1.0]))]
        inward = min(edges, key=lambda e: e[0])[1]
        near = np.array([min(max(x, x0 + 0.08), x1 - 0.08), min(max(y, y0 + 0.08), y1 - 0.08)])
        along = np.array([-inward[1], inward[0]])
        size = np.asarray(rig.ann.asset_of(rig.ann.objects[tool])["size"], float)
        width = float(min(size[:2]))
        best = None
        for shift in np.linspace(-0.4, 0.4, 9):
            c = near + along * shift
            a, b = c - along * length / 2, c + along * length / 2
            if not all(x0 + 0.03 <= p[0] <= x1 - 0.03 and y0 + 0.03 <= p[1] <= y1 - 0.03 for p in (a, b)):
                continue
            lo = np.minimum(a, b) - width / 2
            hi = np.maximum(a, b) + width / 2
            box = [lo[0], lo[1], s["z"], hi[0], hi[1], s["z"] + 0.2]
            if skills._overlaps_objects(rig, box, {tool}, st, margin=0.02):
                continue
            score = abs(shift)
            if best is None or score < best[0]:
                best = (score, a, b)
        if best is None:
            raise SkillFailure(f"wipe {support}: no free strip near the robot")
        _, a, b = best
        stow_load(rig)
        tcp, R, body_in_tcp, _ = _held_frame(rig, tool)
        body, _ = rig.obj_pose(tool)
        st = rig.state()                     # after stow_load lifted it
        hang = float(body[2] - skills._lowest_z(rig, tool, st))
        z_body = s["z"] - 0.001 + hang      # light press: a 3 mm press dragged the sponge out of the pinch
        pts = [a + (b - a) * u for u in np.linspace(0, 1, 7)]
        lane = [pts if k % 2 == 0 else pts[::-1] for k in range(passes)]
        rig.sync_world()
        rig.kin.coll_kw = {"ignore_fingers": True}
        # A long fingers-down stroke at counter height has almost no IK; the
        # base is holonomic, so the arm holds the pressed pose and the base
        # translates along the strip (one IK solution, a straight stroke).
        stroke = b - a
        rig.log("wipe_plan", strip=[np.round(a, 3).tolist(), np.round(b, 3).tolist()], z_body=round(float(z_body), 4),
                body_in_tcp=np.round(body_in_tcp, 4).tolist(), tcp_R=np.round(R, 3).tolist(),
                base=[round(v, 3) for v in rig.base_pose()])
        park, R0 = None, R
        for psi in (0.0, math.pi / 2, -math.pi / 2, math.pi):     # sponge yaw does not matter
            R = Rotation.from_euler("z", psi).as_matrix() @ R0
            legs = [(_tcp_for_body(R, np.r_[a, z_body + 0.06], body_in_tcp), R),
                    (_tcp_for_body(R, np.r_[a, z_body], body_in_tcp), R)]

            def stroke_clear(x, y, yaw, q_last):
                return all(rig.world.footprint_clear(x + stroke[0] * u, y + stroke[1] * u, math.radians(yaw))
                           for u in np.linspace(0, 1, 7))
            park = find_park(rig.kin, rig.world, legs, near=rig.base_pose(), max_tries=80, q_start=rig.q_cmd,
                             travel_q=skills._travel_q(rig), ride=stroke_clear)
            if park is not None:
                break
        if park is None:
            raise SkillFailure(f"wipe {support}: no base pose reaches the strip (rejected: {_park_diag()})")
        skills._goto_park(rig, park)
        rig.caption = f"WIPE {support} with {tool}"
        rig.move_to(*legs[0], step=0.01, label="wipe_above", collision=False, smooth=True)
        rig.move_to(*legs[1], step=0.003, steps_per_wp=5, label="wipe_press", collision=False)
        n_cells = max(1, int(round(length / 0.02)))
        covered = np.zeros(n_cells, bool)
        px, py, pyaw = rig.base_pose()

        def mark():
            st2 = rig.state()
            bottom = rig.geo.bottom(tool, st2)
            if abs(float(skills._lowest_z(rig, tool, st2)) - s["z"]) <= 0.008:
                u = float((bottom[:2] - a) @ (b - a) / (length ** 2))
                half = 0.5 * float(max(size[:2])) / length
                i0, i1 = int(max(0, (u - half) * n_cells)), int(min(n_cells, math.ceil((u + half) * n_cells)))
                covered[i0:i1] = True
        mark()
        for k in range(passes):
            us = np.linspace(0, 1, 7)[1:] if k % 2 == 0 else np.linspace(1, 0, 7)[1:]
            for u in us:
                rig.drive_base([(px + stroke[0] * u, py + stroke[1] * u, pyaw)], speed=0.05, ramp=0.4)
                rig.log("wipe_stroke", u=round(float(u), 2), sponge=np.round(rig.obj_pose(tool)[0], 3).tolist(),
                        fingers=np.round(rig.fingers(), 4).tolist(), base=[round(v, 3) for v in rig.base_pose()])
                mark()
        skills.check_held(rig, "wipe")
        t, R1 = rig.kin.tcp(rig.q_cmd)
        rig.move_to(t + np.array([0, 0, 0.08]), R1, step=0.01, label="wipe_lift", collision=False)
        cov = float(covered.mean())
        memory(rig)["wiped"][support] = max(cov, memory(rig)["wiped"].get(support, 0.0))
        rig.log("wipe_result", tool=tool, support=support, coverage=round(cov, 3),
                strip=[np.round(a, 3).tolist(), np.round(b, 3).tolist()])
        if cov < 0.5:
            raise SkillFailure(f"wipe {support}: contact coverage {cov:.2f}")
        return cov


class StirContainerPolicy(AtomicPolicy):
    """Tilt a held spoon's far end down into the container and move it on a
    circle; turns are counted only while the tip is inside the wall profile
    and below the rim."""

    def execute(self, tool, container, *, turns=1.25, tilt_deg=50.0):
        """Waist kept near upright first: a 0.54 rad bow over the low hob
        stalled at 0.40 and the spoon tip stopped above the rim."""
        rig = self.rig
        widx = rig.kin.names.index("waist_pitch_joint")
        hi = float(rig.kin.hi[widx])
        rig.kin.hi[widx] = min(hi, 0.3)
        try:
            return self._stir(tool, container, turns=turns, tilt_deg=tilt_deg)
        except SkillFailure as exc:
            if "no base pose" not in str(exc) or rig.held is None:
                raise
            rig.log("stir_waist_relaxed", reason=str(exc))
        finally:
            rig.kin.hi[widx] = hi
        return self._stir(tool, container, turns=turns, tilt_deg=tilt_deg)

    def _stir(self, tool, container, *, turns=1.25, tilt_deg=50.0):
        rig = self.rig
        if rig.held is None or rig.held["name"] != tool:
            raise SkillFailure(f"stir: {tool} is not right-held")
        ca = rig.ann.asset_of(rig.ann.objects[container]).get("container")
        if not ca:
            raise SkillFailure(f"stir: {container} is not a container")
        stow_load(rig)
        st = rig.state()
        cb = np.asarray(rig.geo.bottom(container, st), float)
        rim_r = float(ca.get("rim_radius") or min(ca["bands"][0][2:4]))
        tcp, R, body_in_tcp, Rb_in_tcp = _held_frame(rig, tool)
        size = np.asarray(rig.ann.asset_of(rig.ann.objects[tool])["size"], float)
        # far end of the tool along its long axis, in the TCP frame
        axis_local = np.eye(3)[int(np.argmax(size))]
        o2b = np.asarray(rig.ann.asset_of(rig.ann.objects[tool])["origin_to_bottom_center"], float)
        centre_local = o2b + np.array([0, 0, size[2] / 2])
        ends = [centre_local + axis_local * max(size) / 2 * sgn for sgn in (1, -1)]
        ends_tcp = [body_in_tcp + Rb_in_tcp @ e for e in ends]
        tip_tcp = max(ends_tcp, key=np.linalg.norm)
        axis_w = R @ (tip_tcp / np.linalg.norm(tip_tcp))
        side = np.cross(axis_w, [0, 0, 1.0])
        if np.linalg.norm(side) < 1e-6:
            side = np.array([1.0, 0, 0])
        side /= np.linalg.norm(side)
        R_goal = Rotation.from_rotvec(-side * math.radians(tilt_deg)).as_matrix() @ R
        if (R_goal @ tip_tcp)[2] > 0:
            R_goal = Rotation.from_rotvec(side * math.radians(tilt_deg)).as_matrix() @ R
        depth = min(0.04, ca["rim_height"] - 0.015)
        radius = min(0.035, 0.45 * rim_r)
        tip_z = cb[2] + ca["rim_height"] - depth

        def tcp_for_tip(th):
            tip = np.array([cb[0] + radius * math.cos(th), cb[1] + radius * math.sin(th), tip_z])
            return tip - R_goal @ tip_tcp

        rig.sync_world()
        rig.kin.coll_kw = {"ignore_fingers": True}
        park, R_base, r_full = None, R_goal, radius
        # the whole circle is part of the base search (only 0 and 180 deg were
        # checked and the arm lost IK at the quarter points); a tighter circle
        # needs less arm travel and still turns the tip around the pot centre
        for radius in (r_full, 0.022, 0.012):
            for psi in (0.0, math.pi / 2, -math.pi / 2, math.pi):     # approach the pot from any side
                R_goal = Rotation.from_euler("z", psi).as_matrix() @ R_base
                above = tcp_for_tip(0.0) + np.array([0, 0, depth + 0.06])
                legs = [(above, R_goal), (tcp_for_tip(0.0), R_goal), (tcp_for_tip(math.pi / 2), R_goal),
                        (tcp_for_tip(math.pi), R_goal), (tcp_for_tip(1.5 * math.pi), R_goal)]
                park = find_park(rig.kin, rig.world, legs, near=rig.base_pose(), max_tries=60, q_start=rig.q_cmd,
                                 travel_q=skills._travel_q(rig))
                if park is not None:
                    rig.log("stir_plan", radius_m=radius, wrist_turn_deg=round(math.degrees(psi)))
                    break
            if park is not None:
                break
        if park is None:
            raise SkillFailure(f"stir {container}: no base pose reaches the stirring circle (rejected: {_park_diag()})")
        skills._goto_park(rig, park)
        rig.caption = f"STIR {container} with {tool}"
        t0, R0 = rig.kin.tcp(rig.q_cmd)
        try:            # a short lift first when the arm allows; "above" itself was planned reachable
            rig.move_to(t0 + np.array([0, 0, 0.05]), R0, step=0.01, label="stir_raise", collision=False)
        except SkillFailure as exc:
            if rig.held is None:
                raise
            rig.log("stir_raise_skipped", reason=str(exc))
        rig.move_to(above, R_goal, step=0.005, steps_per_wp=5, label="stir_above", collision=False, smooth=True,
                    q_hint=park[3][0])
        rig.move_to(tcp_for_tip(0.0), R_goal, step=0.003, steps_per_wp=5, label="stir_dip", collision=False)
        swept, prev = 0.0, None
        rim_top = cb[2] + ca["rim_height"]
        tip_index = int(np.argmax([np.linalg.norm(e) for e in ends_tcp]))
        rig.step(30)
        body, q = rig.obj_pose(tool)
        tip_w = body + quat_R(q) @ ends[tip_index]
        if np.linalg.norm(tip_w[:2] - cb[:2]) < rim_r and tip_w[2] < rim_top:
            memory(rig).setdefault("dipped", {})[container] = True
        rig.log("dip_sample", tool=tool, container=container, tip=np.round(tip_w, 3).tolist(),
                inside=bool(memory(rig).get("dipped", {}).get(container)))
        if turns <= 0:
            rig.step(90)
            rig.move_to(above, R_goal, step=0.005, label="dip_out", collision=False)
            skills.check_held(rig, "dip")
            if not memory(rig).get("dipped", {}).get(container):
                raise SkillFailure(f"dip {container}: the tip did not get below the rim inside")
            return {"dipped": True}
        for th in np.linspace(0, 2 * math.pi * turns, int(16 * turns) + 1)[1:]:
            try:
                rig.move_to(tcp_for_tip(th), R_goal, step=0.004, steps_per_wp=4, label="stir_circle",
                            collision=False)
            except SkillFailure as exc:
                if rig.held is None:
                    raise
                rig.log("stir_circle_skip", theta_deg=round(math.degrees(th), 1), reason=str(exc))
                prev = None
                continue
            t_now, R_now = rig.kin.tcp(rig.q())
            body, q = rig.obj_pose(tool)
            tip_w = body + quat_R(q) @ ends[tip_index]
            rel = tip_w[:2] - cb[:2]
            inside = np.linalg.norm(rel) < rim_r and tip_w[2] < rim_top
            ang = math.atan2(rel[1], rel[0])
            if prev is not None and inside:
                swept += abs((ang - prev + math.pi) % (2 * math.pi) - math.pi)
            prev = ang if inside else None
        skills.check_held(rig, "stir")
        rig.move_to(above, R_goal, step=0.005, label="stir_out", collision=False)
        n_turns = swept / (2 * math.pi)
        memory(rig)["stirred"][container] = max(n_turns, memory(rig)["stirred"].get(container, 0.0))
        rig.log("stir_result", tool=tool, container=container, turns=round(n_turns, 2))
        if n_turns < 1.0:
            raise SkillFailure(f"stir {container}: {n_turns:.2f} turns inside")
        return n_turns


class PourIntoPolicy(AtomicPolicy):
    """Hold the cup's far rim over the target, tilt it up to 120 deg about a
    horizontal axis through the TCP, hold, and return upright."""

    def execute(self, source, target, *, max_tilt_deg=120.0):
        rig = self.rig
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
        rig.move_to(goal, R, step=0.005, steps_per_wp=5, label="pour_over", collision=False, smooth=True)
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
                rig.move_to(goal_k, Rk, step=0.004, steps_per_wp=5, label="pour_tilt", collision=False, smooth=True,
                            q_hint=hint)
            except SkillFailure as exc:
                rig.log("pour_tilt_limit", deg=float(ang), reason=str(exc))
                if not (planned_tilt and ang < planned_tilt and len(park[3]) > 1):
                    break
                # the intermediate tilt has no IK on this branch: the planned
                # (verified) tilt configuration is reachable in joint space
                ang = float(planned_tilt)
                try:
                    rig.follow(rig.joint_path(park[3][1], "pour_tilt_planned", check=False), steps_per_wp=8)
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
                        rig.move_to(goal_k, Rk, step=0.004, steps_per_wp=3, label="pour_rock", collision=False)
                    except SkillFailure:
                        break
                rig.step(60)
                if not objects_inside(rig, source, rig.state()):
                    rig.log("pour_rock_emptied", rocks=k_ + 1)
                    break
        try:
            for ang in np.arange(reached - 10.0, -1e-6, -10.0):
                goal_k, Rk = tilted(goal, R, u, lip_xy, ang)
                rig.move_to(goal_k, Rk, step=0.002, steps_per_wp=8, label="pour_return", collision=False, smooth=True)
        except SkillFailure as exc:
            if rig.held is None:
                raise
            # no straight IK back from the planned tilt: retrace in joint space
            rig.log("pour_return_joint", reason=str(exc))
            rig.follow(rig.joint_path(q_over, "pour_return", check=False), steps_per_wp=10)
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
