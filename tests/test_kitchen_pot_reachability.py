"""Regression for the kitchen fixture collision proxy and V2 pot handle."""

import json
import math
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from zeno_skills.annotations import SceneAnnotations
from zeno_skills.collision import WorldModel
from zeno_skills.kinematics import ArmKin, gripper_rot


ROOT = Path(__file__).resolve().parents[1]


def test_kitchen_pot_handle_has_collision_aware_ik():
    ann = SceneAnnotations(ROOT / "scenes/kitchen_pot/annotation.json")
    world = WorldModel(ann)
    kin = ArmKin()
    kin.scene = world
    kin.set_base((-1.0, 7.45, 0.0), math.radians(60))

    # The base still cannot drive through the counter while the arm can reach
    # the open space between the worktop and the upper cabinets.
    assert not world.footprint_clear(-0.2, 7.45, 0.0)
    obj = ann.objects["handled_cooking_pot"]
    spec = next(g for g in ann.asset_of(obj)["grasps"] if g["type"] == "handle_pinch")
    task = json.loads((ROOT / "scenes/kitchen_pot/task.json").read_text())
    yaw = task["placed_objects"]["handled_cooking_pot"]["yaw"]
    frame = Rotation.from_euler("z", yaw).as_matrix()
    point = np.asarray(obj["position"]) + frame @ np.asarray(spec["center"])
    orientation = gripper_rot(frame @ np.asarray(spec["approach"]),
                              frame @ np.asarray(spec["close_dir"]))
    _, reachable = kin.ik_global(point, orientation)
    assert reachable
