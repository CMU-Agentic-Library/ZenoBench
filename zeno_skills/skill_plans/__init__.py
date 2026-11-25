"""Skill plans (docs/motion/MOTION_ARCHITECTURE.md section 6, layer 2): one module per shape of skill
(9.4) -- pick, place, navigate, look, posture, door, contact (slide, stir) -- what they share in _common.  They know no simulator: no module
here imports the rig (tests/test_layering.py)."""

from ._common import FREE_HAND, FREE_LOAD, TOUCHING, T_of, held_frame, plan_clear
from .pick import HELD_POSE_MARGIN, PICK_ANCHORS, PICK_RELAY, PICK_STAGES, PICK_TOL, plan_pick
from .place import (DROP_RELAY, DROP_STAGES, HOVER_RELAY, HOVER_STAGES, PLACE_ANCHORS, PLACE_RELAY, PLACE_STAGES, PLACE_TOL,
                    RELEASE_STAGES, plan_drop, plan_hover, plan_place, plan_release,
                    set_down_length)
from .navigate import NAV_STAGES, Carry, plan_navigate, travel_chain
from .look import LOOK_STEPS, head_segment, plan_look
from .posture import plan_held_move, plan_posture
from .door import (DOOR_ANCHORS, DOOR_RELAY, DOOR_STAGES, DOOR_TOL, PUSH_ANCHORS, PUSH_RELAY, PUSH_STAGES,
                   plan_door, plan_push)
from .contact import (PRESS_ANCHORS, PRESS_RELAY, PRESS_STAGES, SLIDE_ANCHORS, SLIDE_RELAY, SLIDE_STAGES, SLIDE_STEP,
                      STIR_ANCHORS, STIR_RELAY, STIR_STAGES, WIPE_RELAY, WIPE_STAGES, plan_press, plan_slide, plan_stir,
                      plan_wipe, slide_travel, stir_tcp)
