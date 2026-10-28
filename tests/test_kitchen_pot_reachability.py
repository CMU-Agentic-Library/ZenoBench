"""Regression for the kitchen fixture base proxy."""

from pathlib import Path

from zeno_skills.annotations import SceneAnnotations
from zeno_skills.collision import WorldModel


ROOT = Path(__file__).resolve().parents[1]


def test_kitchen_counter_blocks_the_base():
    """The base cannot drive through the counter (the arm's reach into the open
    space under the upper cabinets is cuRobo's, against the real colliders)."""
    ann = SceneAnnotations(ROOT / "scenes/kitchen_pot/annotation.json")
    world = WorldModel(ann)
    assert not world.footprint_clear(-0.2, 7.45, 0.0)
