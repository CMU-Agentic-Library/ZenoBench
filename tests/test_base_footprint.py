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


def test_a_block_too_low_for_the_old_sample_height_still_blocks_the_chassis():
    # 4 cm tall, the height of floor_block: under the chassis' old 0.15 m sample and in its way all
    # the same -- the chassis' underside is at LOW_BOTTOM (11-10)
    block = (0.2, -0.05, 0.018, 0.3, 0.05, 0.058)
    assert not world(block).footprint_clear(0.0, 0.0, 0.0)
    assert world(block).footprint_clear(-0.2, 0.0, 0.0)              # a pose that keeps clear of it


def test_the_layers_keep_no_margin_up_or_down():
    # FOOTPRINT_MARGIN is in xy only: a 2 cm thing on the floor is under the chassis' underside
    w = world()
    w.set_base_obstacles([[0.2, -0.05, 0.0, 0.3, 0.05, 0.02]])
    assert w.footprint_clear(0.0, 0.0, 0.0)
    w.set_base_obstacles([[0.2, -0.05, 0.0, 0.3, 0.05, 0.03]])
    assert not w.footprint_clear(0.0, 0.0, 0.0)


def test_a_moving_part_just_above_the_chassis_is_the_column_business():
    # an open drawer 3 cm above the chassis' top, over its front: clear of the column behind the
    # centre, so neither the footprint nor the circle blocks (it was a 3-d distance under LOW_CORNER
    # + margin until 11-10); lowered into the chassis' heights it blocks both
    def drawer(z0, z1):
        a = {"name": "d", "closed_q": 0.0, "part_box": [(0.05, -0.3, z0), (0.6, 0.3, z1)]}
        ann = SimpleNamespace(obstacles=[{"name": "wall", "kind": "furniture", "aabb": list(WALL)}],
                              supports=[], articulated=[a], part_pose=lambda a, q: np.eye(4))
        return WorldModel(ann)
    above = drawer(0.30, 0.40)
    assert above.footprint_clear(0.0, 0.0, 0.0) and above.circles_clear(np.array([[0.0, 0.0]]))[0]
    inside = drawer(0.20, 0.40)
    assert not inside.footprint_clear(0.0, 0.0, 0.0) and not inside.circles_clear(np.array([[0.0, 0.0]]))[0]


def test_a_loose_box_the_chassis_passes_under_is_no_pillar_to_the_circle():
    # an object on a worktop beside the base: above the chassis, clear of the slim column behind the
    # centre -- the disc must not block where the footprint is clear at every heading
    w = world(WALL)
    w.set_base_obstacles([[0.2, -0.1, 0.9, 0.4, 0.1, 1.0]])
    assert w.circles_clear(np.array([[0.0, 0.0]]))[0]
    assert w.footprint_clear(0.0, 0.0, 0.0)


def test_the_circle_is_a_relaxation_of_the_footprint_at_every_heading():
    """circles_clear may only block where footprints_clear blocks at every heading: the reachability
    field and the base planner's cut-off refuse outright on it (11-10: a z-blind loose box blocked a
    disc the footprint let through, which isolated the robot's own cell)."""
    rng = np.random.default_rng(11)
    w = world(WALL, (-0.8, 0.4, 0.0, -0.3, 0.9, 0.75), (0.05, -0.3, 0.55, 0.6, 0.3, 0.65))
    boxes = np.c_[rng.uniform(-1.0, 1.0, (40, 2)), rng.uniform(0.0, 0.9, 40)]
    boxes = np.c_[boxes[:, :2], boxes[:, 2], boxes[:, :2] + rng.uniform(0.03, 0.3, (40, 2)),
                  boxes[:, 2] + rng.uniform(0.02, 0.4, 40)]
    w.set_base_obstacles(boxes)
    xy = np.c_[rng.uniform(-1.5, 1.5, 600), rng.uniform(-1.5, 1.5, 600)]
    blocked = ~w.circles_clear(xy)
    assert blocked.sum() > 50
    headings = np.radians(np.arange(0, 360, 15))
    for p in xy[blocked]:
        poses = np.c_[np.full(len(headings), p[0]), np.full(len(headings), p[1]), headings]
        assert not w.footprints_clear(poses).any(), f"the circle blocks {p} where the footprint does not"


def test_batched_and_single_agree():
    w = world(WALL, (-0.8, 0.4, 0.0, -0.3, 0.9, 0.75), (0.05, -0.3, 0.55, 0.6, 0.3, 0.65))
    rng = np.random.default_rng(3)
    poses = np.c_[rng.uniform(-1.0, 1.0, 400), rng.uniform(-1.0, 1.0, 400), rng.uniform(-math.pi, math.pi, 400)]
    single = np.array([w.footprint_clear(*p) for p in poses])
    assert 50 < single.sum() < 350
    assert np.array_equal(w.footprints_clear(poses), single)
