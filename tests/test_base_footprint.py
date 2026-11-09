"""The base footprint in two layers (collision.py): a rounded chassis up to LOW_TOP and a slim column
behind the centre above it, FOOTPRINT_MARGIN from the annotated boxes."""

import math
from types import SimpleNamespace

import numpy as np

from zeno_skills.collision import BASE_HALF, FOOTPRINT_MARGIN, LOW_CORNER, WorldModel


def world(*boxes):
    ann = SimpleNamespace(obstacles=[{"name": f"b{i}", "kind": "furniture", "aabb": list(b)} for i, b in enumerate(boxes)],
                          supports=[], articulated=[])
    return WorldModel(ann)


WALL = (1.0, -2.0, 0.0, 1.1, 2.0, 2.4)          # a wall face at x = 1.0


def test_square_on_to_a_wall_keeps_the_chassis_side():
    w = world(WALL)
    edge = 1.0 - BASE_HALF - FOOTPRINT_MARGIN
    assert w.footprint_clear(edge - 0.005, 0.0, 0.0)
    assert not w.footprint_clear(edge + 0.005, 0.0, 0.0)


def test_turned_45_deg_the_rounded_corner_comes_closer_than_a_square_one():
    w = world(WALL)
    corner = (BASE_HALF - LOW_CORNER) * math.sqrt(2) + LOW_CORNER        # 0.296 m, the square's was 0.345
    assert w.footprint_clear(1.0 - corner - FOOTPRINT_MARGIN - 0.005, 0.0, math.pi / 4)
    assert not w.footprint_clear(1.0 - corner - FOOTPRINT_MARGIN + 0.005, 0.0, math.pi / 4)
    # the old square column needed 0.391 m: 0.35 m is clear now
    assert w.footprint_clear(1.0 - 0.35, 0.0, math.pi / 4)


def test_above_the_chassis_only_the_column_counts():
    # a board at 0.55-0.65 m in front of the base: over the chassis, clear of the column behind the centre
    board = (0.05, -0.3, 0.55, 0.6, 0.3, 0.65)
    assert world(board).footprint_clear(0.0, 0.0, 0.0)
    # the same board behind the centre is in the column's way
    assert not world((-0.3, -0.3, 0.55, -0.05, 0.3, 0.65)).footprint_clear(0.0, 0.0, 0.0)


def test_a_low_box_in_front_blocks_the_chassis():
    assert not world((0.2, -0.05, 0.0, 0.3, 0.05, 0.2)).footprint_clear(0.0, 0.0, 0.0)


def test_batched_and_single_agree():
    w = world(WALL, (-0.8, 0.4, 0.0, -0.3, 0.9, 0.75), (0.05, -0.3, 0.55, 0.6, 0.3, 0.65))
    rng = np.random.default_rng(3)
    poses = np.c_[rng.uniform(-1.0, 1.0, 400), rng.uniform(-1.0, 1.0, 400), rng.uniform(-math.pi, math.pi, 400)]
    single = np.array([w.footprint_clear(*p) for p in poses])
    assert 50 < single.sum() < 350
    assert np.array_equal(w.footprints_clear(poses), single)
