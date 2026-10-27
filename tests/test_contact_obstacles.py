"""Contact motions (push, drag, sweep) plan with the pushed object's neighbours as obstacles for
the hand and the fingers (WorldModel.temp_obstacles(fingers=True), skills._contact_boxes)."""

from types import SimpleNamespace

import numpy as np

from zeno_skills import skills
from zeno_skills.collision import WorldModel
from zeno_skills.kinematics import ArmKin


def test_finger_obstacles_count_under_ignore_fingers_and_are_restored():
    world = WorldModel(SimpleNamespace(obstacles=[], supports=[], articulated=[]))
    kin = ArmKin()
    kin.set_base((0.0, 0.0, 0.0), 0.0)
    q = kin.posture
    tcp, _ = kin.tcp(q)
    box = np.r_[tcp - 0.01, tcp + 0.01]                    # around the fingertips only
    free = world.clearance(kin, q, ignore_fingers=True)
    with world.temp_obstacles([box]):
        assert world.clearance(kin, q, ignore_fingers=True) > 0           # the fingers are left out
        assert world.clearance(kin, q) < 0
    with world.temp_obstacles([box], fingers=True):
        assert world.clearance(kin, q, ignore_fingers=True) < 0           # a contact move: they count
    assert len(world.finger_B) == 0 and world.clearance(kin, q, ignore_fingers=True) == free


class _Geo:
    """Axis-aligned boxes: name -> (centre xy, bottom z, size)."""

    def __init__(self, objs):
        self.o = objs

    def bottom(self, n, st):
        (x, y), z, _ = self.o[n]
        return np.array([x, y, z])

    def centre(self, n, st):
        (x, y), z, s = self.o[n]
        return np.array([x, y, z + s[2] / 2])

    def footprint(self, n, st, margin=0.0):
        (x, y), _, s = self.o[n]
        return np.array([x - s[0] / 2 - margin, y - s[1] / 2 - margin, x + s[0] / 2 + margin, y + s[1] / 2 + margin])

    def inside(self, a, b, st):
        return (a == "block" and b == "tray"), ""


def test_contact_boxes_are_the_neighbours_not_the_object_its_tray_or_far_things():
    objs = {"block": ((7.05, 1.60), 0.86, (0.05, 0.05, 0.05)),
            "bowl": ((7.00, 1.717), 0.86, (0.178, 0.176, 0.09)),
            "pin": ((6.866, 1.58), 0.86, (0.22, 0.06, 0.05)),
            "tray": ((7.05, 1.60), 0.85, (0.30, 0.20, 0.02)),        # the block stands in it
            "held_cup": ((7.10, 1.60), 0.95, (0.08, 0.08, 0.10)),
            "far_mug": ((8.00, 1.60), 0.86, (0.08, 0.08, 0.10))}
    rig = SimpleNamespace(geo=_Geo(objs), held={"name": "held_cup"}, left_held=None,
                          ann=SimpleNamespace(objects={n: {"asset": n} for n in objs}, asset_of=lambda o: {
                              "size": objs[o["asset"]][2], "container": o["asset"] == "tray"}))
    boxes = skills._contact_boxes(rig, "block", {"objects": {n: {} for n in objs}})
    assert len(boxes) == 2
    bowl = next(b for b in boxes if b[5] > 0.95)
    assert np.allclose(bowl, [6.906, 1.624, 0.86, 7.094, 1.81, 0.955], atol=1e-3)
