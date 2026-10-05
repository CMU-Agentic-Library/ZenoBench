"""One Isaac Sim session with a Zeno rig: shared by tools/run_skills.py
and tools/run_task.py.

    app = launch(video=True)                      # before any omni/isaac import
    rig = make_rig(app, "tasks/collect_fruits/scene.usd", "tasks/collect_fruits/annotation.json",
                   video=True, res=(720, 1280), stride=4)
    ...skills...
    rig.write_video("run.mp4")
"""

from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# follow-camera viewpoints (base frame u, v; height 1.35 + dz * target height)
FOLLOW = [(-0.9, -1.25, 0.5), (0.3, -1.4, 0.5), (-1.3, 0.0, 0.6), (-0.9, 1.1, 0.5), (0.9, -1.0, 0.8),
          (-0.5, -0.7, 1.2)]


def _clear(world, eye, tgt):
    """No wall/furniture box between the camera and its target (and the
    camera not inside one)."""
    import numpy as np
    B = world.B[:-1]
    P = np.asarray(eye, float)[None, :] + np.linspace(0.0, 0.85, 12)[:, None] * \
        (np.asarray(tgt, float) - np.asarray(eye, float))[None, :]
    inside = (P[:, None, 0] > B[None, :, 0]) & (P[:, None, 0] < B[None, :, 3]) & \
        (P[:, None, 1] > B[None, :, 1]) & (P[:, None, 1] < B[None, :, 4]) & \
        (P[:, None, 2] > B[None, :, 2]) & (P[:, None, 2] < B[None, :, 5])
    return not bool(inside.any())


def launch(video=True, first_person=False):
    """Start Isaac Sim with rendering enabled when either camera is requested."""
    from isaaclab.app import AppLauncher
    return AppLauncher({"headless": True, "enable_cameras": bool(video or first_person), "no_splash": True,
                        "fast_shutdown": True}).app


def make_rig(app, scene, ann_path, video=True, res=(720, 1280), stride=4, log=None, prepare=None,
             handle_objects=(), first_person=False, first_person_res=(480, 640)):
    """Build a rig; optionally attach an RGB camera to Malo's stereo camera mount.

    ``prepare(stage)`` can make USD edits before the simulation starts.
    Camera resolutions are (height, width).
    """
    import omni.usd
    import torch
    import isaaclab.sim as sim_utils
    from isaacsim.core.prims import SingleArticulation
    from .annotations import SceneAnnotations
    from .collision import WorldModel
    from .kinematics import ArmKin
    from .rig import Rig

    omni.usd.get_context().open_stage(str(ROOT / scene))
    for _ in range(10):
        app.update()
    stage = omni.usd.get_context().get_stage()
    ann = SceneAnnotations(ROOT / ann_path)
    from . import physics as P
    for name in handle_objects:
        obj = ann.objects[name]
        asset = ann.asset_of(obj)
        handle = asset.get("container", {}).get("handle_collider")
        if handle is None:
            raise ValueError(f"{name} has no physical handle collider annotation")
        P.deinstance(stage, obj["prim"])
        P.add_handle_collider(stage, obj["body"], handle)
    if prepare is not None:
        prepare(stage)
    sim = sim_utils.SimulationContext(sim_utils.SimulationCfg(dt=1 / 120, device="cpu",
                                                              physics_prim_path="/World/PhysicsScene"))
    cams = {}
    if video:
        from isaaclab.sensors import Camera, CameraCfg
        H, W = res
        for k, f in (("follow", 13.0), ("wide", 11.0)):
            cams[k] = Camera(CameraCfg(prim_path=f"/World/RunCam_{k}", update_period=0, height=H, width=W,
                                       data_types=["rgb"], spawn=sim_utils.PinholeCameraCfg(
                                           focal_length=f, clipping_range=(0.05, 40.0))))
    first_person_camera = None
    if first_person:
        from isaaclab.sensors import Camera, CameraCfg
        height, width = first_person_res
        first_person_camera = Camera(CameraCfg(
            prim_path="/World/ZenoMalo/Asset/stereo_camera_link/FirstPersonCamera",
            update_period=0, height=height, width=width, data_types=["rgb"],
            offset=CameraCfg.OffsetCfg(pos=(0.04, 0.0, 0.0), convention="world"),
            spawn=sim_utils.PinholeCameraCfg(focal_length=10.0, clipping_range=(0.05, 40.0)),
        ))
    robot = SingleArticulation("/World/ZenoMalo/Asset", name="zeno")
    sim.reset()
    robot.initialize()
    kin = ArmKin()
    world = WorldModel(ann)
    kin.scene = world
    rig = Rig(sim, stage, robot, kin, world, ann, cams=cams, stride=stride,
              log=log or (lambda s: print(s, flush=True)),
              first_person_camera=first_person_camera)
    if cams:
        orig_step = rig.step
        cam_state = {}

        def step_with_cams(n=1):
            # cameras follow the base: over-the-shoulder + a higher wide view.
            # Low targets (floor pick) get a lower, closer follow camera.
            for _ in range(n):
                if rig.tick % rig.stride == 0:
                    x, y, yaw = rig.base_pose()
                    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))

                    def w(u, v, z):
                        return [x + c * u - s * v, y + s * u + c * v, z]
                    f32 = torch.float32
                    low = getattr(rig, "focus_z", None)
                    tz = 0.55 if low is None else max(0.1, min(0.9, low))
                    # over the right (arm-side) shoulder by default; another
                    # viewpoint when a wall is in the way (kept until blocked)
                    tgt = w(0.55, -0.3, tz)
                    if rig.tick % (rig.stride * 8) == 0 or cam_state.get("eye") is None:
                        order = [cam_state.get("k", 0)] + list(range(len(FOLLOW)))
                        for k in order:
                            u, v, dz = FOLLOW[k]
                            if _clear(rig.world, w(u, v, 1.35 + dz * tz), tgt):
                                cam_state["k"] = k
                                break
                    u, v, dz = FOLLOW[cam_state.get("k", 0)]
                    cam_state["eye"] = w(u, v, 1.35 + dz * tz)
                    cams["follow"].set_world_poses_from_view(torch.tensor([cam_state["eye"]], dtype=f32),
                                                             torch.tensor([tgt], dtype=f32))
                    cams["wide"].set_world_poses_from_view(torch.tensor([w(-2.2, -1.2, 2.4)], dtype=f32),
                                                           torch.tensor([w(0.4, 0.0, 0.5)], dtype=f32))
                    if rig.camera_override is not None:
                        eye, target = rig.camera_override
                        cams["follow"].set_world_poses_from_view(torch.tensor([eye], dtype=f32),
                                                                  torch.tensor([target], dtype=f32))
                orig_step(1)
        rig.step = step_with_cams
    return rig
