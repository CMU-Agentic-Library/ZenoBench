"""GPU check of the robot's own base as a second checker environment (zeno_skills.body_collision,
docs/motion/MOTION_ARCHITECTURE.md 4.4) -- no simulator: the checker and the arms built as motion.Motion builds
them, with an empty scene.

    docker/run.sh '$ISAACLAB_PYTHON tools/check_body_collision.py'

Checks: the chassis prism and the column box are where collision.py says (spheres inside / outside); the
arms' stored postures (fold, rest, drive) are feasible with the base on; a posture with the hand inside
the column is not; the base moves with the base pose (place_body); a collision-aware IK to a point beside
the column stays out of it.  Prints the closest links to the base at each posture."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    import torch
    import warp as wp
    import yaml
    from curobo.geom.sdf.utils import create_collision_checker
    from curobo.geom.sdf.world import CollisionCheckerType, CollisionQueryBuffer, WorldCollisionConfig
    from curobo.geom.types import Cuboid, WorldConfig
    from curobo.types.base import TensorDeviceType

    from zeno_skills import body_collision as B
    from zeno_skills import motion as M
    from zeno_skills import scene_geometry as G

    wp.init()
    if not hasattr(wp, "torch"):        # outside Isaac Sim's app: cuRobo calls wp.torch.* (warp < 1.x layout)
        wp.torch = SimpleNamespace(**{n: getattr(wp, n) for n in ("device_from_torch", "from_torch", "to_torch",
                                                                 "stream_from_torch", "dtype_from_torch") if hasattr(wp, n)})
    fails = []

    def check(ok, what):
        print(("ok   " if ok else "FAIL ") + what)
        if not ok:
            fails.append(what)

    B.install()
    far = WorldConfig(cuboid=[Cuboid(name="far", pose=[50.0, 50.0, -5.0, 1, 0, 0, 0], dims=[0.1, 0.1, 0.1])])
    slots, sides = M._hand_slots(yaml.safe_load(open(M.ROBOT_CFG))["robot_cfg"]["kinematics"])
    body = G.body_world(other_hand=sides)
    checker = create_collision_checker(WorldCollisionConfig(
        TensorDeviceType(), world_model=[far, body], checker_type=CollisionCheckerType.MESH,
        cache={"obb": len(body.cuboid) + 8, "mesh": 4}))
    oh_idx = torch.tensor([checker.get_obb_idx(f"{G.OTHER_HAND}_{i}", env_idx=G.BODY_ENV) for i in range(len(sides))],
                          dtype=torch.long, device="cuda")
    checker._cube_tensor_list[2][G.BODY_ENV, oh_idx] = 0

    def base_depth(points, r=0.01):
        """Penetration (> 0) of small spheres at ``points`` into the base environment."""
        q = torch.tensor([[[*p, r] for p in points]], dtype=torch.float32, device="cuda").view(1, 1, -1, 4)
        buf = CollisionQueryBuffer.initialize_from_shape(q.shape, TensorDeviceType(), checker.collision_types)
        d = checker.get_sphere_distance(q, buf, torch.ones(1, device="cuda"), torch.zeros(1, device="cuda"),
                                        env_query_idx=torch.full((1,), G.BODY_ENV, dtype=torch.int32, device="cuda"),
                                        sum_collisions=False)
        return d.view(-1).cpu().numpy()

    # the geometry (collision.py: chassis +-0.2442 rounded 0.115 up to 0.27 m; column x -0.115..-0.010, y +-0.063 to 1.05 m)
    d = base_depth([(0.10, 0.0, 0.15), (0.0, 0.20, 0.10), (0.40, 0.0, 0.15), (0.22, 0.22, 0.15),
                    (-0.06, 0.0, 0.60), (0.05, 0.0, 0.60), (-0.06, 0.0, 1.10)])
    print("depths", np.round(d, 3))
    check(d[0] > 0 and d[1] > 0, "points inside the chassis touch it")
    check(d[2] == 0 and d[3] == 0, "points outside the chassis (in front, at the rounded corner) do not")
    check(d[4] > 0, "a point inside the column touches it")
    check(d[5] == 0 and d[6] == 0, "points in front of the column and above it do not")
    G.place_body(checker, (2.0, 1.0, 90.0))
    d = base_depth([(2.0 + 0.0, 1.0 - 0.06, 0.60), (-0.06, 0.0, 0.60)])
    check(d[0] > 0 and d[1] == 0, "the column moves with the base (2, 1, 90 deg)")
    G.place_body(checker, (0.0, 0.0, 0.0))

    cfg = yaml.safe_load(open(M.ROBOT_CFG))["robot_cfg"]
    k = cfg["kinematics"]
    k["urdf_path"] = str(M.ROOT / k["urdf_path"])
    k["asset_root_path"] = str(M.ROOT / k["asset_root_path"])
    M.add_held_links(k)
    motion = SimpleNamespace(body_at=(0.0, 0.0, 0.0), oh_slots=slots)
    t0 = time.time()
    arms = {s: M._Arm(motion, s, cfg, checker) for s in ("right", "left")}
    print(f"arms built in {time.time() - t0:.1f} s")
    for side, arm in arms.items():
        n_on = sum(getattr(r, "_zb_body", None) is not None for r in arm.mg.get_all_rollout_instances())
        check(n_on > 0, f"{side}: {n_on} rollouts carry the base terms")
        kin = arm.kin
        arm.prepare(kin, None, set())
        names = {v: kk for kk, v in arm.kcs[0].link_name_to_idx_map.items()}
        idx = arm.kcs[0].link_sphere_idx_map.cpu().numpy()
        for label, q in (("fold", kin.posture), ("rest", kin.rest), ("drive", kin.drive)):
            ok = bool(arm.feasible(np.asarray(q)[None])[0])
            sph = arm.spheres(np.asarray(q)).view(1, 1, -1, 4)
            pts = B.masked(sph, arm.body_mask).view(-1, 4).cpu().numpy()
            on = pts[:, 3] > 0
            # clearance of each live sphere to the column box and chassis (coarse: box distance less radius)
            from zeno_skills.collision import COLUMN_TOP, COLUMN_XY, LOW_TOP
            x0, y0, x1, y1 = COLUMN_XY
            lo, hi = np.array([x0, y0, LOW_TOP]), np.array([x1, y1, COLUMN_TOP])
            gap = np.linalg.norm(np.maximum(0, np.maximum(lo - pts[:, :3], pts[:, :3] - hi)), axis=1) - pts[:, 3]
            gap[~on] = np.inf
            i = int(np.argmin(gap))
            check(ok, f"{side} {label} feasible with the base on (closest live sphere to the column: "
                      f"{names.get(int(idx[i]))} {gap[i]:+.3f} m)")
        # postures with an arm sphere (not the body's) inside the column or the chassis: sampled in the limits
        from zeno_skills.collision import COLUMN_TOP, COLUMN_XY, LOW_TOP
        x0, y0, x1, y1 = COLUMN_XY
        lo, hi = np.array([x0, y0, LOW_TOP]), np.array([x1, y1, COLUMN_TOP])
        rng = np.random.default_rng(0)
        Qr = rng.uniform(arm.lo, arm.hi, size=(4000, len(arm.lo))).astype(np.float32)
        st = arm.mg.kinematics.get_state(torch.as_tensor(Qr, device="cuda"))
        S = B.masked(st.link_spheres_tensor.view(len(Qr), 1, -1, 4), arm.body_mask).view(len(Qr), -1, 4).cpu().numpy()
        out = np.maximum(0, np.maximum(lo - S[..., :3], S[..., :3] - hi))
        pen = (S[..., 3] - np.linalg.norm(out, axis=-1)) * (S[..., 3] > 0)
        deep = np.nonzero(pen.max(axis=1) > 0.03)[0][:20]
        if len(deep):
            feas_on = arm.feasible(Qr[deep].astype(float))
            G.place_body(checker, (30.0, 30.0, 0.0))            # the base's boxes far away, the robot where it is
            motion.body_at = (30.0, 30.0, 0.0)
            feas_off = arm.feasible(Qr[deep].astype(float))
            G.place_body(checker, (0.0, 0.0, 0.0))
            motion.body_at = (0.0, 0.0, 0.0)
            only_base = [i for i in range(len(deep)) if feas_off[i]]   # free but for the base
            check(len(only_base) > 0 and not any(feas_on[i] for i in only_base),
                  f"{side}: {len(only_base)} sampled postures with the arm 3+ cm in the column, free without "
                  f"the base, are all infeasible with it")
            # a collision-aware IK seeded there, to where that posture's hand is: out of the column or none
            i = only_base[0] if only_base else 0
            p, R = arm.kin.tcp(Qr[deep][i].astype(float))
            q_s, ok_s = arm.ik(p, R, [Qr[deep][i].astype(float)], collision=True)
            if ok_s:
                S1 = B.masked(arm.spheres(q_s).view(1, 1, -1, 4), arm.body_mask).view(-1, 4).cpu().numpy()
                out1 = np.maximum(0, np.maximum(lo - S1[:, :3], S1[:, :3] - hi))
                pen1 = float(np.max((S1[:, 3] - np.linalg.norm(out1, axis=-1)) * (S1[:, 3] > 0)))
                check(pen1 <= 0.0, f"{side}: the collision IK from such a posture leaves the column (deepest {pen1:+.3f} m)")
            else:
                print(f"     {side}: no collision IK to that hand pose (reported, not failed)")
        else:
            print(f"     {side}: no sampled posture reaches into the column (skipped)")
        # timing: a batch of feasibility checks with the base terms on
        Q = np.repeat(np.asarray(kin.posture)[None], 64, 0)
        arm.feasible(Q)
        torch.cuda.synchronize()
        t = time.time()
        for _ in range(20):
            arm.feasible(Q)
        torch.cuda.synchronize()
        print(f"     {side}: feasible(64) {1000 * (time.time() - t) / 20:.2f} ms")
    # the other hand as boxes of BODY_ENV (motion.Motion._other_hand_boxes, rule audit 11-25): the left arm's query
    # with the right hand off in its model (other_hand_off: it holds a load) -- the right hand's spheres stand there
    from zeno_skills.motion import HAND_LINKS
    right, left = arms["right"], arms["left"]
    qr = np.asarray(right.kin.posture, float)
    right.prepare(right.kin, None, set())
    names = {v: kk for kk, v in right.kcs[0].link_name_to_idx_map.items()}
    sidx = right.kcs[0].link_sphere_idx_map.cpu().numpy()
    S = right.spheres(qr).cpu().numpy()
    hand = [i for i in range(len(S)) if names.get(int(sidx[i]), "") in {f"right_{l}" for l in HAND_LINKS}]
    ql = np.r_[qr[:2], np.asarray(left.kin.posture, float)[2:]]
    left.prepare(left.kin, qr, {f"right_{l}" for l in HAND_LINKS})
    fake = SimpleNamespace(checker=checker, oh_idx=oh_idx, oh_on=None, oh_q={"left": ql})
    M.Motion._other_hand_boxes(fake, left)
    d_on = base_depth(S[hand, :3], r=0.002)
    M.Motion._other_hand_boxes(fake, None)
    d_off = base_depth(S[hand, :3], r=0.002)
    check(len(hand) == len(sides) and bool(np.all(d_on > 0)),
          f"the right hand's {len(hand)} spheres stand as boxes for the left arm ({int(np.sum(d_on > 0))} inside)")
    check(bool(np.all(d_off < d_on)) and fake.oh_on is None, "off again: the boxes no longer there")
    # a left posture with its hand where the right hand is: infeasible with the boxes, free of them without
    pr, Rr = right.kin.tcp(qr)
    q_in, ok = left.ik(np.asarray(pr, float), np.asarray(Rr, float), [ql], False)
    if ok:
        M.Motion._other_hand_boxes(fake, left)
        f_on = bool(left.feasible(np.asarray(q_in, float)[None])[0])
        M.Motion._other_hand_boxes(fake, None)
        f_off = bool(left.feasible(np.asarray(q_in, float)[None])[0])
        if f_off:
            check(not f_on, "a left hand inside the right one: infeasible with the boxes (free without)")
        else:
            print("     the left hand inside the right one is infeasible without the boxes too (self collision): "
                  "reported, not failed")
    else:
        print("     no kinematic left IK to the right TCP (reported, not failed)")
    print("FAILED: " + "; ".join(fails) if fails else "ALL OK")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
