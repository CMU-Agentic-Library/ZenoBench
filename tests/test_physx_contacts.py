"""physx_contacts.Reader.read: one pass over a contact report, the same answers as the two passes
(touching, held_touching) it replaced on 11-23 (kept below as the reference)."""

from types import SimpleNamespace

import numpy as np

from zeno_skills import physx_contacts as PC

ROOT = "/World/ZenoMalo/Asset/"
ACTORS = [ROOT + "right_gripper_link", ROOT + "left_arm_link4", ROOT + "torso_link",
          "/World/Tasks/mug/Asset", "/World/Tasks/pot_lid/Asset", "/World/Tasks/cup/Asset",
          "/World/House/kitchen_island", "/World/House/table"]


def _reader(report):
    r = object.__new__(PC.Reader)
    r.root, r._paths = ROOT, {}
    r._to_path = lambda i: ACTORS[i] if i < len(ACTORS) else f"{ACTORS[i % len(ACTORS)]}/col_{i}"
    r.sim = SimpleNamespace(get_contact_report=lambda: report)
    return r


def _report(seed, n=400):
    rng = np.random.default_rng(seed)
    heads, data = [], []
    for _ in range(n):
        a0, a1 = rng.integers(len(ACTORS), size=2)
        k = int(rng.integers(0, 4))
        heads.append(SimpleNamespace(actor0=int(a0), actor1=int(a1), collider0=int(a0) + len(ACTORS) * int(rng.integers(1, 3)),
                                     collider1=int(a1) + len(ACTORS) * int(rng.integers(1, 3)),
                                     contact_data_offset=len(data), num_contact_data=k))
        for _ in range(k):
            data.append(SimpleNamespace(separation=float(rng.choice([-0.002, 0.0001, 0.001, 0.003])),
                                        position=rng.normal(size=3).tolist(),
                                        impulse=(rng.normal(size=3) * rng.integers(0, 2)).tolist()))
    return heads, data


def _old_touching(r, heads, data):
    out = {}
    for h in heads:
        if not h.num_contact_data:
            continue
        a0, a1 = r._path(h.actor0), r._path(h.actor1)
        r0, r1 = a0.startswith(r.root), a1.startswith(r.root)
        if r0 == r1:
            continue
        link = (a0 if r0 else a1).rsplit("/", 1)[1]
        other = r._path(h.collider1 if r0 else h.collider0)
        sep, imp, at = float("inf"), 0.0, None
        for i in range(h.contact_data_offset, h.contact_data_offset + h.num_contact_data):
            d = data[i]
            if float(d.separation) < sep:
                sep, at = float(d.separation), (float(d.position[0]), float(d.position[1]), float(d.position[2]))
            j = d.impulse
            imp += (j[0] * j[0] + j[1] * j[1] + j[2] * j[2]) ** 0.5
        if sep > PC.TOUCH_SEP and imp == 0.0:
            continue
        key = (link, other)
        s0, i0, a0_ = out.get(key, (float("inf"), 0.0, None))
        out[key] = (sep, i0 + imp, at) if sep < s0 else (s0, i0 + imp, a0_)
    return out


def _old_held_touching(r, heads, data, bodies):
    bodies = set(bodies)
    out = {}
    for h in heads:
        if not h.num_contact_data:
            continue
        a0, a1 = r._path(h.actor0), r._path(h.actor1)
        if (a0 in bodies) == (a1 in bodies):
            continue
        body, other_actor = (a0, a1) if a0 in bodies else (a1, a0)
        if other_actor.startswith(r.root):
            continue
        other = r._path(h.collider1 if a0 == body else h.collider0)
        sep, imp, at = float("inf"), 0.0, None
        for i in range(h.contact_data_offset, h.contact_data_offset + h.num_contact_data):
            d = data[i]
            if float(d.separation) < sep:
                sep, at = float(d.separation), (float(d.position[0]), float(d.position[1]), float(d.position[2]))
            j = d.impulse
            imp += (j[0] * j[0] + j[1] * j[1] + j[2] * j[2]) ** 0.5
        if sep > PC.TOUCH_SEP and imp == 0.0:
            continue
        s0, i0, a0_ = out.get((body, other), (float("inf"), 0.0, None))
        out[(body, other)] = (sep, i0 + imp, at) if sep < s0 else (s0, i0 + imp, a0_)
    return out


def test_one_pass_gives_the_two_passes_answers():
    for seed in range(5):
        heads, data = _report(seed)
        for bodies in ((), (ACTORS[3],), (ACTORS[3], ACTORS[4])):
            r = _reader((heads, data))
            robot, held = r.read(bodies)
            ref = _reader((heads, data))
            assert list(robot.items()) == list(_old_touching(ref, heads, data).items())
            assert list(held.items()) == list(_old_held_touching(ref, heads, data, bodies).items())
            assert robot and (held or not bodies)
            assert r.touching() == robot          # cached ids: the same answer again
