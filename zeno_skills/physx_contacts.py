"""Real contacts of the robot, from PhysX contact reports (the contact monitor's ground truth).

The contact monitor (clearance.py) checks the planner's sphere model, which can miss what the
simulator's colliders touch: the finger pad box sticks out of its spheres by 2.3 mm at the tip
edge, 3.7 mm at the corners, and a fingertip came down on a mug's rim wall unseen (T04 no_cup,
2026-11-05).  Here the robot's links (torso up: not the base, lidar, steering or wheels) carry a
``PhysxContactReportAPI``, so PhysX reports every pair a robot collider is in; ``touching`` reads
the report of the last step.  The loose objects' bodies carry one too, so what a hand holds is seen
touching the world (``held_touching``): its spheres in the planner's model are an approximation as
well (held_spheres), and before 11-11 a lid scraping a pot's rim (T17) or a carried mug knocking a
cup over (T04) went unrecorded.

Isaac Lab's SimulationContext switches contact processing off (``/physics/disableContactProcessing``);
``allow_processing`` turns it back on after the context is built.  It only hands the contact data to
Python: the simulation is the same (the T04 knock came on the same tick with and without it), and
an episode took about 1 % longer.
"""

from __future__ import annotations

TOUCH_SEP = 0.0005          # m: a contact point closer than this, or with an impulse, is a touch (PhysX
                            # also reports points within the contact offset, 2 mm on the pads, untouched)
NOT_REPORTED = ("base_link", "lidar_link", "steering_link", "wheel_link")


def enable(stage, root, bodies=()):
    """Contact reports on the robot's rigid links under ``root`` (an articulation's links) and on
    the rigid ``bodies`` (the loose objects), before the simulation starts.  The names of the
    robot links that got one."""
    from pxr import PhysxSchema, Usd, UsdPhysics
    out = []
    for prim in Usd.PrimRange(stage.GetPrimAtPath(root)):
        if not prim.HasAPI(UsdPhysics.RigidBodyAPI) or prim.GetName().endswith(NOT_REPORTED):
            continue
        api = PhysxSchema.PhysxContactReportAPI.Apply(prim)
        api.CreateThresholdAttr().Set(0.0)
        out.append(prim.GetName())
    for b in bodies:
        prim = stage.GetPrimAtPath(b)
        if prim and prim.HasAPI(UsdPhysics.RigidBodyAPI):
            PhysxSchema.PhysxContactReportAPI.Apply(prim).CreateThresholdAttr().Set(0.0)
    return out


def allow_processing():
    """Turn PhysX contact processing back on (Isaac Lab's SimulationContext turns it off)."""
    import carb
    carb.settings.get_settings().set_bool("/physics/disableContactProcessing", False)


class Reader:
    """The robot's touches in the last simulation step: {(robot link, other collider path):
    (closest separation m, summed impulse N s, the closest contact point)}.  Contacts among the robot's own links are left out."""

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

    def _link(self, i):
        """The robot link name of actor ``i``, None for an actor outside the robot (cached per id)."""
        links = self.__dict__.setdefault("_links", {})
        if i not in links:
            p = self._path(i)
            links[i] = p.rsplit("/", 1)[1] if p.startswith(self.root) else None
        return links[i]

    def touching(self):
        return self.read()[0]

    def read(self, bodies=()):
        """One pass over the last step's report: (the robot's touches as the class says; what the
        rigid ``bodies`` (held objects) touch outside the robot and themselves: {(body, other
        collider path): (closest separation m, summed impulse N s, the closest contact point)}).
        Most pairs are loose objects resting on furniture (~1300 a tick, 11-23): a pair is classed by
        its actors' ids, and only one the robot or a held body is in is read further."""
        heads, data = self.sim.get_contact_report()[:2]
        bodies = set(bodies)
        robot, held = {}, {}
        link = self.__dict__.get("_links", {}).get
        miss = self._link
        for h in heads:
            if not h.num_contact_data:
                continue                                 # a lost contact
            i0, i1 = h.actor0, h.actor1
            l0, l1 = link(i0, 0), link(i1, 0)
            if l0 == 0:
                l0 = miss(i0)
            if l1 == 0:
                l1 = miss(i1)
            if l0 is not None and l1 is not None:
                continue                                 # the robot on itself
            if l0 is not None or l1 is not None:
                key = (l0 if l0 is not None else l1, self._path(h.collider1 if l0 is not None else h.collider0))
                out = robot
            else:
                if not bodies:
                    continue
                a0, a1 = self._path(i0), self._path(i1)
                if (a0 in bodies) == (a1 in bodies):
                    continue                             # neither held, or held on held
                key = (a0, self._path(h.collider1)) if a0 in bodies else (a1, self._path(h.collider0))
                out = held
            sep, imp, at = float("inf"), 0.0, None
            for i in range(h.contact_data_offset, h.contact_data_offset + h.num_contact_data):
                d = data[i]
                if float(d.separation) < sep:
                    sep, at = float(d.separation), (float(d.position[0]), float(d.position[1]), float(d.position[2]))
                j = d.impulse
                imp += (j[0] * j[0] + j[1] * j[1] + j[2] * j[2]) ** 0.5
            if sep > TOUCH_SEP and imp == 0.0:
                continue                                 # within the contact offset, not touching
            s0, i0_, a0_ = out.get(key, (float("inf"), 0.0, None))
            out[key] = (sep, i0_ + imp, at) if sep < s0 else (s0, i0_ + imp, a0_)
        return robot, held
