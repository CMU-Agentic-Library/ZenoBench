"""Real contacts of the robot, from PhysX contact reports (the contact monitor's ground truth).

The contact monitor (clearance.py) checks the planner's sphere model, which can miss what the
simulator's colliders touch: the finger pad box sticks out of its spheres by 2.3 mm at the tip
edge, 3.7 mm at the corners, and a fingertip came down on a mug's rim wall unseen (T04 no_cup,
2026-11-05).  Here the robot's links (torso up: not the base, lidar, steering or wheels) carry a
``PhysxContactReportAPI``, so PhysX reports every pair a robot collider is in; ``touching`` reads
the report of the last step.

Isaac Lab's SimulationContext switches contact processing off (``/physics/disableContactProcessing``);
``allow_processing`` turns it back on after the context is built.  It only hands the contact data to
Python: the simulation is the same (the T04 knock came on the same tick with and without it), and
an episode took about 1 % longer.
"""

from __future__ import annotations

TOUCH_SEP = 0.0005          # m: a contact point closer than this, or with an impulse, is a touch (PhysX
                            # also reports points within the contact offset, 2 mm on the pads, untouched)
NOT_REPORTED = ("base_link", "lidar_link", "steering_link", "wheel_link")


def enable(stage, root):
    """Contact reports on the robot's rigid links under ``root`` (an articulation's links), before
    the simulation starts.  The names of the links that got one."""
    from pxr import PhysxSchema, Usd, UsdPhysics
    out = []
    for prim in Usd.PrimRange(stage.GetPrimAtPath(root)):
        if not prim.HasAPI(UsdPhysics.RigidBodyAPI) or prim.GetName().endswith(NOT_REPORTED):
            continue
        api = PhysxSchema.PhysxContactReportAPI.Apply(prim)
        api.CreateThresholdAttr().Set(0.0)
        out.append(prim.GetName())
    return out


def allow_processing():
    """Turn PhysX contact processing back on (Isaac Lab's SimulationContext turns it off)."""
    import carb
    carb.settings.get_settings().set_bool("/physics/disableContactProcessing", False)


class Reader:
    """The robot's touches in the last simulation step: {(robot link, other collider path):
    (closest separation m, summed impulse N s)}.  Contacts among the robot's own links are left out."""

    def __init__(self, root):
        from omni.physx import get_physx_simulation_interface
        from pxr import PhysicsSchemaTools
        self.root = root.rstrip("/") + "/"
        self.sim = get_physx_simulation_interface()
        self._to_path = PhysicsSchemaTools.intToSdfPath
        self._paths = {}

    def _path(self, i):
        p = self._paths.get(i)
        if p is None:
            p = self._paths[i] = str(self._to_path(i))
        return p

    def touching(self):
        heads, data = self.sim.get_contact_report()[:2]
        out = {}
        for h in heads:
            if not h.num_contact_data:
                continue                                 # a lost contact
            a0, a1 = self._path(h.actor0), self._path(h.actor1)
            r0, r1 = a0.startswith(self.root), a1.startswith(self.root)
            if r0 == r1:
                continue                                 # the robot on itself (or not the robot)
            link = (a0 if r0 else a1).rsplit("/", 1)[1]
            other = self._path(h.collider1 if r0 else h.collider0)
            sep, imp = float("inf"), 0.0
            for i in range(h.contact_data_offset, h.contact_data_offset + h.num_contact_data):
                d = data[i]
                sep = min(sep, float(d.separation))
                j = d.impulse
                imp += (j[0] * j[0] + j[1] * j[1] + j[2] * j[2]) ** 0.5
            if sep > TOUCH_SEP and imp == 0.0:
                continue                                 # within the contact offset, not touching
            key = (link, other)
            s0, i0 = out.get(key, (float("inf"), 0.0))
            out[key] = (min(s0, sep), i0 + imp)
        return out
