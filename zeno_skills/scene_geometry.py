"""The scene's PhysX colliders as cuRobo obstacles.

Every enabled collider outside the robot becomes one obstacle: a Cube collider
a cuboid, a collision mesh a mesh (its convex hull, at most 64 vertices, when
PhysX approximates it by one; the triangles themselves for approximation "none",
marked two_sided: PhysX collides such a mesh as a surface, from either side, and
the patched cuRobo (docker/patches/curobo_two_sided.py) does the same).  Meshes under an
Xform that carries the CollisionAPI count as that Xform's colliders (the
importer's layout).  Each obstacle is tagged with what it belongs to:

  object:<name>     a loose object of the annotation (moves; pose from its body)
  part:<name>       the moving part of an articulated fixture (door, drawer)
  static            everything else (house, furniture, carcasses, support slabs)

Poses are kept as body pose x collider offset so a moved body only needs its
body pose: ``Colliders.poses(read_body)`` returns world poses for the
obstacles of moving bodies.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

ROBOT = "/World/ZenoMalo"
HULL_VERTICES = 64        # PhysX's default hullVertexLimit


@dataclass
class Collider:
    name: str                 # unique obstacle name (the prim path)
    owner: str                # "static", "object:<name>", "part:<name>", "button:<appliance>/<key>"
    kind: str                 # "cuboid" or "mesh"
    body: str | None          # rigid body prim whose pose moves it (None: static)
    local: np.ndarray         # 4x4 collider pose in the body frame (world frame when static)
    dims: np.ndarray | None = None              # cuboid edge lengths
    vertices: np.ndarray | None = None          # mesh, in the collider frame
    faces: np.ndarray | None = None
    two_sided: bool = False   # a static triangle mesh: PhysX collides its surface from either side


@dataclass
class Colliders:
    items: list = field(default_factory=list)

    def by_owner(self, owner):
        return [c.name for c in self.items if c.owner == owner]

    def owners(self):
        return sorted({c.owner for c in self.items})


BUTTON_KEYS = ("door_button", "start_button", "power_button")    # an appliance's annotated buttons


def buttons(ann):
    """(appliance, key, prim) of every annotated button with a prim: the microwave's door and start keys
    on its body, the stove's power key.  Their colliders are owned by "button:<appliance>/<key>" -- the
    name predicates.entity_kind gives a button -- not "static": a press may touch one (Spec.touch) and
    nothing else of the appliance (skill_plans.plan_press)."""
    out = []
    for a in list(ann.articulated) + list(getattr(ann, "appliances", [])):
        for key in BUTTON_KEYS:
            rec = a.get(key)
            if isinstance(rec, dict) and rec.get("prim"):
                out.append((a["name"], key, rec["prim"]))
    return out


def is_static(owner):
    """A collider that never moves: the house and its furniture, and an appliance's buttons -- part of its body
    for everything but a press (the base's footprint, the surfaces things rest on, the monitor's watch)."""
    return owner == "static" or owner.startswith("button:")


def _enabled(prim, stop):
    from pxr import UsdPhysics
    p = prim
    while p and p.GetPath() != stop:
        if p.HasAPI(UsdPhysics.CollisionAPI):
            return UsdPhysics.CollisionAPI(p).GetCollisionEnabledAttr().Get() is not False, p
        p = p.GetParent()
    return False, None


def _approximation(prim):
    from pxr import UsdPhysics
    if prim is not None and prim.HasAPI(UsdPhysics.MeshCollisionAPI):
        return UsdPhysics.MeshCollisionAPI(prim).GetApproximationAttr().Get() or "none"
    return "none"


def _body_of(prim):
    from pxr import UsdPhysics
    p = prim
    while p and str(p.GetPath()) != "/":
        if p.HasAPI(UsdPhysics.RigidBodyAPI):
            kin = p.GetAttribute("physics:kinematicEnabled").Get()
            en = p.GetAttribute("physics:rigidBodyEnabled").Get()
            return None if (kin or en is False) else p
        p = p.GetParent()
    return None


def _hull(pts):
    """Convex hull limited to HULL_VERTICES vertices like PhysX's cooking (farthest points of
    the full hull, then their hull)."""
    import trimesh
    hull = trimesh.convex.convex_hull(pts)
    V = np.asarray(hull.vertices)
    if len(V) > HULL_VERTICES:
        keep = [int(np.argmax(np.linalg.norm(V - V.mean(0), axis=1)))]
        d = np.linalg.norm(V - V[keep[0]], axis=1)
        while len(keep) < HULL_VERTICES:
            keep.append(int(np.argmax(d)))
            d = np.minimum(d, np.linalg.norm(V - V[keep[-1]], axis=1))
        hull = trimesh.convex.convex_hull(V[keep])
    return np.asarray(hull.vertices), np.asarray(hull.faces)


def collect(stage, ann):
    """All enabled non-robot colliders of the stage, tagged with their owner."""
    from pxr import Usd, UsdGeom
    cache = UsdGeom.XformCache()
    root = stage.GetPseudoRoot().GetPath()
    owners = []                                     # (prim path prefix, owner), longest first
    for name, o in ann.objects.items():
        owners.append((o["prim"], f"object:{name}"))
    for a in ann.articulated:
        if a.get("part"):
            owners.append((a["part"], f"part:{a['name']}"))
    for app, key, prim in buttons(ann):
        owners.append((prim, f"button:{app}/{key}"))
    owners.sort(key=lambda t: -len(t[0]))

    def owner_of(path):
        for pre, own in owners:
            if path == pre or path.startswith(pre + "/"):
                return own
        return "static"

    def M(prim):
        return np.array(cache.GetLocalToWorldTransform(prim), float).T

    out = Colliders()
    for p in Usd.PrimRange(stage.GetPseudoRoot(), Usd.TraverseInstanceProxies()):
        path = str(p.GetPath())
        if path.startswith(ROBOT) or not (p.IsA(UsdGeom.Cube) or p.IsA(UsdGeom.Mesh)):
            continue
        on, api_prim = _enabled(p, root)
        if not on:
            continue
        body = _body_of(p)
        W = M(p)
        if body is not None:
            local = np.linalg.inv(M(body)) @ W
        else:
            local = W
        if p.IsA(UsdGeom.Cube):
            # scale stays in the matrix: split it into dims and a pure rotation
            size = UsdGeom.Cube(p).GetSizeAttr().Get() or 2.0
            S = np.linalg.norm(local[:3, :3], axis=0)
            T = local.copy()
            T[:3, :3] = local[:3, :3] / S
            out.items.append(Collider(path, owner_of(path), "cuboid", str(body.GetPath()) if body else None,
                                      T, dims=S * size))
            continue
        mesh = UsdGeom.Mesh(p)
        pts = np.asarray(mesh.GetPointsAttr().Get() or [], float)
        counts = np.asarray(mesh.GetFaceVertexCountsAttr().Get() or [], int)
        idx = np.asarray(mesh.GetFaceVertexIndicesAttr().Get() or [], int)
        if len(pts) < 4 or len(counts) == 0:
            continue
        # bake scale into the vertices: obstacle poses are rigid
        S = np.linalg.norm(local[:3, :3], axis=0)
        T = local.copy()
        T[:3, :3] = local[:3, :3] / S
        pts = pts * S
        appr = _approximation(api_prim) if api_prim is not None else "none"
        if appr == "none" and body is None:
            faces, k = [], 0
            for c in counts:                         # fan-triangulate polygons
                faces += [[idx[k], idx[k + i], idx[k + i + 1]] for i in range(1, c - 1)]
                k += c
            verts, faces, two_sided = pts, np.asarray(faces, int), True
        else:
            # convexHull, convexDecomposition (hull of the piece) and every dynamic
            # body (PhysX cannot simulate triangle meshes on a moving body)
            verts, faces = _hull(pts)
            two_sided = False
        out.items.append(Collider(path, owner_of(path), "mesh", str(body.GetPath()) if body else None,
                                  T, vertices=verts, faces=faces, two_sided=two_sided))
    return out


def pose7(T):
    """4x4 -> [x, y, z, qw, qx, qy, qz] (cuRobo's pose list)."""
    from scipy.spatial.transform import Rotation
    x, y, z, w = Rotation.from_matrix(T[:3, :3]).as_quat()
    return [*map(float, T[:3, 3]), float(w), float(x), float(y), float(z)]


def world_pose(c, body_pose):
    """World pose of collider ``c``; ``body_pose(path)`` -> 4x4 of a moving body."""
    return c.local if c.body is None else body_pose(c.body) @ c.local


def to_world_config(cols, body_pose):
    """cuRobo WorldConfig with every collider at its current world pose."""
    from curobo.geom.types import Cuboid, Mesh, WorldConfig
    cub, mesh = [], []
    for c in cols.items:
        p = pose7(world_pose(c, body_pose))
        if c.kind == "cuboid":
            cub.append(Cuboid(name=c.name, pose=p, dims=[*map(float, c.dims)]))
        else:
            mesh.append(Mesh(name=c.name, pose=p, vertices=np.asarray(c.vertices, np.float32),
                             faces=np.asarray(c.faces, np.int32)))
    return WorldConfig(cuboid=cub, mesh=mesh)


def usd_body_pose(stage):
    """body_pose for to_world_config from the USD stage (the start state)."""
    from pxr import UsdGeom
    cache = UsdGeom.XformCache()
    return lambda path: np.array(cache.GetLocalToWorldTransform(stage.GetPrimAtPath(path)), float).T


def mark_two_sided(checker, cols, env_idx=0):
    """Set the patched cuRobo mesh flag (2 = enabled, unsigned) on the two-sided meshes."""
    flags = checker._mesh_tensor_list[2]
    for c in cols.items:
        if c.kind == "mesh" and c.two_sided:
            flags[env_idx, checker.get_mesh_idx(c.name, env_idx)] = 2


# ------------------------------------------------------------------ the robot's own base (docs 4.4)
# The base -- the chassis and the column above it -- carries no collision spheres in the arm models (only
# the torso, the head and the arms do), so nothing an arm plan checks met it: a held book swept through the
# column (T05 homework_ready, 11-12).  It is a second environment of the same checker (BODY_ENV): its two
# layers, the shapes the base planner measured (collision.py), rigid with the base (place_body).  The arms,
# the hands and what they hold are checked against it; the body (body_collision.BODY_LINKS: it rides on the
# column and leans over it) is not.
BODY_ENV = 1
BODY_COLUMN = "body:column"
BODY_CHASSIS = "body:chassis"
# The other hand, when it holds a load and stands still while this arm moves (motion.Motion._query: other_hand_off):
# its spheres are off in this arm's model -- they would meet its own load, an obstacle where it holds it -- so
# its collision spheres stand in BODY_ENV as boxes instead (one per sphere, 2 r a side), which only this arm, its
# hand and its load are checked against (body_collision.kept).  Off (enable 0) in every other query.
OTHER_HAND = "body:other_hand"
BODY_ARC_STEPS = (0.0, 30.0, 60.0, 90.0)   # deg: the chassis' rounded square as the union of the rectangles
                                           # with a corner on each corner arc at these angles -- boxes, exact
                                           # at any depth (a mesh is only searched near its surface: a point
                                           # 12 cm inside a chassis prism read as clear); 1.2 cm short of the
                                           # arcs at most, between the steps


def _base_T(base):
    """4x4 of the base (x, y, yaw_deg) on the floor."""
    x, y, yaw = base
    c, s = np.cos(np.radians(yaw)), np.sin(np.radians(yaw))
    T = np.eye(4)
    T[:2, :2] = [[c, -s], [s, c]]
    T[:2, 3] = x, y
    return T


def _body_boxes():
    """[(name, centre in the base frame, dims)] of the base's two layers (collision.py): the chassis'
    rounded square (BASE_HALF, LOW_CORNER) from LOW_BOTTOM to LOW_TOP as BODY_ARC_STEPS rectangles, the
    column above it."""
    from .collision import BASE_HALF, COLUMN_TOP, COLUMN_XY, LOW_BOTTOM, LOW_CORNER, LOW_TOP
    c = BASE_HALF - LOW_CORNER
    out = []
    for i, a in enumerate(BODY_ARC_STEPS):
        hx, hy = c + LOW_CORNER * np.cos(np.radians(a)), c + LOW_CORNER * np.sin(np.radians(a))
        out.append((f"{BODY_CHASSIS}_{i}", np.array([0.0, 0.0, (LOW_BOTTOM + LOW_TOP) / 2]),
                    [2 * hx, 2 * hy, LOW_TOP - LOW_BOTTOM]))
    x0, y0, x1, y1 = COLUMN_XY
    out.append((BODY_COLUMN, np.array([(x0 + x1) / 2, (y0 + y1) / 2, (LOW_TOP + COLUMN_TOP) / 2]),
                [x1 - x0, y1 - y0, COLUMN_TOP - LOW_TOP]))
    return out


def _at(T, ctr):
    M = T.copy()
    M[:3, 3] = T[:3, :3] @ ctr + T[:3, 3]
    return M


def body_world(base=(0.0, 0.0, 0.0), other_hand=()):
    """cuRobo WorldConfig of the base's two layers at ``base`` (boxes: _body_boxes) -- and ``other_hand``: the sides
    (m) of the OTHER_HAND boxes, parked out of the way (Motion places and enables them per query)."""
    from curobo.geom.types import Cuboid, WorldConfig
    T = _base_T(base)
    return WorldConfig(cuboid=[Cuboid(name=n, pose=pose7(_at(T, ctr)), dims=[*map(float, dims)])
                               for n, ctr, dims in _body_boxes()] +
                       [Cuboid(name=f"{OTHER_HAND}_{i}", pose=[0.0, 0.0, -10.0, 1.0, 0.0, 0.0, 0.0], dims=[float(d)] * 3)
                        for i, d in enumerate(other_hand)])


def place_body(checker, base):
    """Move the base's two layers to ``base`` (x, y, yaw_deg) in the checker's BODY_ENV, in place."""
    from curobo.types.math import Pose
    T = _base_T(base)
    for n, ctr, _ in _body_boxes():
        checker.update_obstacle_pose(n, Pose.from_list(pose7(_at(T, ctr))), env_idx=BODY_ENV)
