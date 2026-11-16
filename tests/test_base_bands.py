"""The base against the static colliders (collision.StaticBands, WorldModel.use_colliders): a table is
its top and legs, so the chassis may go under the top while the column stays out."""

import math
from types import SimpleNamespace

import numpy as np

from zeno_skills.collision import (BAND_RES, BASE_HALF, COLUMN_XY, FOOTPRINT_MARGIN, LOW_CORNER, StaticBands,
                                   WorldModel, static_triangles)

FACES = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1],
                  [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])


def box_mesh(lo, hi):
    """A static collider: the closed box [lo, hi] as a mesh (world frame)."""
    V = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])], float)
    return SimpleNamespace(owner="static", kind="mesh", body=None, local=np.eye(4), vertices=V, faces=FACES)


def table(x0=0.5, x1=1.5, y0=-0.5, y1=0.5, top=0.72, leg=0.04):
    """A top 2 cm thick and four legs in its corners."""
    parts = [box_mesh((x0, y0, top - 0.02), (x1, y1, top))]
    for x in (x0, x1 - leg):
        for y in (y0, y1 - leg):
            parts.append(box_mesh((x, y, 0.0), (x + leg, y + leg, top - 0.02)))
    return parts


def world(cols, obstacles=()):
    ann = SimpleNamespace(obstacles=list(obstacles), supports=[], articulated=[])
    w = WorldModel(ann)
    w.use_colliders(SimpleNamespace(items=cols), lambda path: np.eye(4), cache=None)
    return w


def test_the_chassis_goes_under_a_table_top_until_the_column_reaches_its_edge():
    w = world(table())
    # facing +x towards the table's edge at x = 0.5: the column's front is COLUMN_XY[2] ahead of the centre
    deepest = 0.5 - COLUMN_XY[2] - FOOTPRINT_MARGIN                       # the column at the margin from the top
    assert w.footprint_clear(deepest - 0.03, 0.0, 0.0)                   # the chassis' front 0.2 m under the top
    assert 0.5 + 0.15 < deepest - 0.03 + BASE_HALF
    assert not w.footprint_clear(deepest + 0.03, 0.0, 0.0)


def test_the_box_from_the_floor_to_the_top_keeps_the_chassis_out():
    ann = SimpleNamespace(obstacles=[{"name": "t", "kind": "furniture", "aabb": [0.5, -0.5, 0.0, 1.5, 0.5, 0.72]}],
                          supports=[], articulated=[])
    w = WorldModel(ann)                                                   # no colliders: the annotation's box
    assert not w.footprint_clear(0.5 - BASE_HALF - FOOTPRINT_MARGIN + 0.03, 0.0, 0.0)


def test_a_leg_blocks_the_chassis():
    w = world(table())
    # the base's centre in line with the near left leg (centre y = -0.48): the chassis' front side hits it
    x = 0.5 - BASE_HALF
    assert not w.footprint_clear(x, -0.48, 0.0)


def test_the_annotations_boxes_are_not_used_with_colliders():
    box = {"name": "t", "kind": "furniture", "aabb": [0.5, -0.5, 0.0, 1.5, 0.5, 0.72]}
    w = world(table(), [box])
    assert w.footprint_clear(0.5 - COLUMN_XY[2] - FOOTPRINT_MARGIN - 0.03, 0.0, 0.0)


def test_a_wall_keeps_the_rounded_chassis_at_the_margin():
    wall = [box_mesh((1.0, -2.0, -0.1), (1.1, 2.0, 2.4))]
    w = world(wall)
    edge = 1.0 - BASE_HALF - FOOTPRINT_MARGIN
    assert w.footprint_clear(edge - 1.5 * BAND_RES - 0.005, 0.0, 0.0)    # the raster costs up to 1.5 cells
    assert not w.footprint_clear(edge + 0.005, 0.0, 0.0)
    corner = (BASE_HALF - LOW_CORNER) * math.sqrt(2) + LOW_CORNER
    assert w.footprint_clear(1.0 - corner - FOOTPRINT_MARGIN - 1.5 * BAND_RES - 0.005, 0.0, math.pi / 4)


def test_the_floor_and_a_rug_are_below_the_chassis():
    floor = box_mesh((-3.0, -3.0, -0.15), (3.0, 3.0, 0.0))
    rug = box_mesh((-1.0, -1.0, 0.0), (1.0, 1.0, 0.0036))
    assert world([floor, rug]).footprint_clear(0.0, 0.0, 0.3)


def test_the_relaxation_is_the_chassis_disc_under_the_top():
    w = world(table())
    # the disc of the chassis fits between the legs under the top: the field may go there
    assert w.circles_clear(np.array([[1.0, 0.0]]))[0]
    assert not w.circles_clear(np.array([[0.5, -0.48]]))[0]               # on a leg


def test_batched_and_single_agree():
    w = world(table() + [box_mesh((-1.2, -2.0, -0.1), (-1.1, 2.0, 2.4))])
    rng = np.random.default_rng(5)
    poses = np.c_[rng.uniform(-1.0, 2.0, 300), rng.uniform(-1.0, 1.0, 300), rng.uniform(-math.pi, math.pi, 300)]
    single = np.array([w.footprint_clear(*p) for p in poses])
    assert 30 < single.sum() < 270
    assert np.array_equal(w.footprints_clear(poses), single)


def test_cached_bands_are_the_same(tmp_path):
    tris = static_triangles(SimpleNamespace(items=table()), lambda path: np.eye(4))
    a = StaticBands(tris, cache=tmp_path)
    b = StaticBands(tris, cache=tmp_path)                                 # read back
    assert len(list(tmp_path.glob("*.npz"))) == 1
    for k in a.dist_grid:
        assert np.array_equal(a.dist_grid[k], b.dist_grid[k])


def test_a_carcass_is_posed_by_its_body():
    part = box_mesh((-0.1, -0.1, 0.0), (0.1, 0.1, 0.8))
    part.body = "/cabinet"
    T = np.eye(4)
    T[:3, 3] = (2.0, 0.0, 0.0)
    tris = static_triangles(SimpleNamespace(items=[part]), {"/cabinet": T}.get)
    assert np.allclose(tris[..., 0].min(), 1.9) and np.allclose(tris[..., 0].max(), 2.1)
