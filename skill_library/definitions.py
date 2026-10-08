"""Single source of truth for the verb-based SkillNode library (schema 2).

Every SkillNode is ``verb + noun``: one verb per node, no two verbs that are
synonyms in this robot's world.  The noun (the bound scene instance) chooses
the policy *path* inside the paired Contract; e.g. ``pick`` covers a top pinch,
a rim pinch, a handle pinch, a slide-to-edge + edge pinch, a floor corner pinch,
a microwave cavity grasp and a two-handed lift, selected from the object's GT
annotation and live state.

Preconditions (``requires``) and postconditions (``ensures``) are predicates
from zeno_skills/predicates.py with explicit arguments, evaluated on GT
simulator state by the ContractRunner before and after the policy chain.
``invalidates`` lists the facts the action may destroy (used by the planner).

Relations:
  sequence     A -> B: B is a natural next step after A (loose; the checker
               verifies that some ensures of A matches a requires of B).
  fallback     when A fails, try B: ``repair`` B establishes the failed
               precondition of A then A is retried; ``substitute`` B achieves A's
               primary effect another way.
  alternative  A and B reach the same primary effect by different means.

Run ``python tools/build_skill_library.py`` to write the JSON/Markdown exports.
"""

from __future__ import annotations

# ----------------------------------------------------------------- tiny DSL


def P(pred, negated=False, **args):
    atom = {"pred": pred, "args": args}
    if negated:
        atom["negated"] = True
    return atom


def I(type_, desc, required=True, default=None, enum=None):
    out = {"type": type_, "required": required, "description": desc}
    if default is not None:
        out["default"] = default
    if enum is not None:
        out["enum"] = enum
    return out


def O(type_, desc):
    return {"type": type_, "description": desc}


def W(noun, field, op, value=True):
    if op not in ("equals", "in", "contains", "gte", "lte", "truthy", "falsy"):
        raise ValueError(op)
    return {"noun": noun, "field": field, "op": op, "value": value}


def St(policy, *args, out=None, **kwargs):
    step = {"policy": policy, "args": list(args), "kwargs": kwargs}
    if out:
        step["as"] = out
    return step


def Call(verb, out=None, **args):
    step = {"call": verb, "args": args}
    if out:
        step["as"] = out
    return step


def ForEach(over, as_, *steps):
    return {"foreach": over, "as": as_, "steps": list(steps)}


def Path(path_id, when, steps, requires=(), ensures=(), note=""):
    return {"path_id": path_id, "when": list(when), "steps": list(steps),
            "requires": list(requires), "ensures": list(ensures), "note": note}


def R(kind, to, when, bind=None, reason="", fallback_type=None, repairs=None):
    """kind: sequence | fallback | alternative.  fallback_type: repair (re-establishes a
    precondition named in ``repairs``), recover (undoes the state that made the policy
    fail; needs a reason) or substitute (reaches the same effect another way)."""
    rel = {"kind": kind, "to": to, "when": when, "bind": bind or {}, "reason": reason}
    if fallback_type:
        rel["fallback_type"] = fallback_type
    if repairs:
        rel["repairs"] = repairs
    return rel


SKILLS: list[dict] = []


def skill(verb, noun, title, description, *, inputs, requires, ensures, paths, outputs=None,
          invalidates=(), relations=(), use_when="", distinct_from=(), group="", includes=(), excludes=(),
          failure_modes=()):
    SKILLS.append({"verb": verb, "noun": noun, "title": title, "description": description,
                   "group": group, "inputs": inputs, "outputs": outputs or {}, "requires": list(requires),
                   "ensures": list(ensures), "invalidates": list(invalidates), "paths": list(paths),
                   "relations": list(relations), "use_when": use_when, "distinct_from": dict(distinct_from),
                   "scope": {"includes": list(includes), "excludes": list(excludes)},
                   "failure_modes": list(failure_modes)})


RIGHT = "right"
HELD_R = W("robot", "right_held", "truthy")
EMPTY_R = W("robot", "right_held", "falsy")

# ================================================================= body & base
G = "base_and_body"

skill("navigate", "place", "Navigate to a place",
      "Drive the holonomic base to a free stand-off pose next to a room, piece of furniture, support, "
      "articulated part or object. The arm is tucked when empty, or held in the compact carry pose with the load.",
      group=G,
      inputs={"destination": I("place_ref", "Where to go: a room, furniture, support, articulated part or object.")},
      outputs={"base_pose": O("pose2d", "Measured base pose [x, y, yaw_deg] at arrival.")},
      requires=[],
      ensures=[P("base_near", place="$destination")],
      invalidates=["base_near(*)", "reachable(*)", "facing(*)", "in_view(*)", "base_clear_of(*)", "pointing_at(*)",
                   "presenting(*)"],
      paths=[
          Path("two_hand_carry", [W("robot", "both_hold_same", "truthy")],
               [St("policy_097", "$destination", out="plan"), St("policy_058", "@robot.right_object", "#plan.pose")],
               note="An object held by both grippers moves at the slow bimanual carry speed."),
          Path("carry", [HELD_R],
               [St("policy_097", "$destination", out="plan"),
                St("policy_002", "#plan.pose", name="@robot.right_object", min_bottom_z="#plan.carry_bottom_z")],
               note="Back off, lift the load to carry height, plan with extra clearance, drive slowly."),
          Path("empty", [],
               [St("policy_097", "$destination", out="plan"), St("policy_001", "#plan.pose")]),
      ],
      relations=[
          R("sequence", "approach", "a manipulation target is on the destination", bind={"target": "$destination"},
            reason="navigate leaves the base near; approach makes the target IK-reachable."),
          R("sequence", "look", "the destination must be observed first", bind={"target": "$destination"}),
          R("fallback", "retreat", "navigation fails because the base or load is wedged against furniture",
            fallback_type="recover", reason="Backing out frees the planner's start cell, then navigate again."),
          R("fallback", "tuck", "navigation fails because the empty arm cannot fold", bind={"hand": "right"},
            fallback_type="recover", reason="A separately planned fold clears the arm before the base path."),
          R("fallback", "lift", "a carried object hangs too low for the doorway clearance",
            fallback_type="recover", reason="Raising the load restores the carry clearance."),
      ],
      use_when="The robot must be in another room or next to another piece of furniture.",
      distinct_from={"approach": "approach fine-parks so the arm reaches one target; navigate only gets near.",
                     "retreat": "retreat moves straight back from a place without a destination."},
      includes=["stand-off pose search around the noun's footprint", "A* base path", "carry posture if loaded"],
      excludes=["arm reachability of a specific target", "grasping"],
      failure_modes=["no free stand-off pose", "no base path", "carried object slipped (Dropped)"])

skill("approach", "target", "Approach a manipulation target",
      "Park the base where the right arm has a collision-free IK solution at the target's reach pose: 10 cm above "
      "an object or support, the handle pre-grasp of a door or drawer, 8 cm in front of a button.",
      group=G,
      inputs={"target": I("entity_ref", "The object, support, handle-bearing part or button to reach."),
              "pass_by": I("pose2d", "Optional base waypoint: reach toward the target while driving past it.",
                           required=False)},
      outputs={"base_pose": O("pose2d", "Base pose at which reachability was verified.")},
      requires=[P("base_near", place="$target")],
      ensures=[P("reachable", target="$target")],
      invalidates=["reachable(*)", "facing(*)", "in_view(*)", "pointing_at(*)"],
      paths=[
          Path("reach_on_the_move", [W("args", "pass_by", "truthy")],
               [St("policy_098", "$target", out="reach"),
                St("policy_051", "#reach.position", "#reach.rotation", "$pass_by")],
               note="Extend the arm toward the reach pose while the base follows the given waypoint."),
          Path("park", [], [St("policy_065", "$target")]),
      ],
      relations=[
          R("sequence", "pick", "the target is an object to grasp", bind={"object": "$target"}),
          R("sequence", "open", "the target is a door or drawer", bind={"articulated": "$target"}),
          R("sequence", "press", "the target is a button", bind={"button": "$target"}),
          R("fallback", "navigate", "no base pose near the current one reaches the target",
            bind={"destination": "$target"}, fallback_type="repair", repairs="base_near"),
          R("fallback", "bend", "the target is just beyond the arm envelope", fallback_type="recover",
            reason="Waist pitch adds forward reach from the same base pose."),
          R("fallback", "pull", "the object sits too deep on its support", bind={"object": "$target"},
            fallback_type="substitute", reason="Dragging the object to the front makes it reachable."),
      ],
      use_when="Right before a contact action on one specific target.",
      distinct_from={"navigate": "navigate goes to a region; approach verifies arm IK for one target."},
      includes=["base pose search with IK + collision checks", "verification from the reached pose"],
      excludes=["contact with the target"],
      failure_modes=["no base pose reaches the target", "IK fails after parking"])

skill("face", "target", "Face a target",
      "Rotate the base in place until it faces the target (heading error <= 20 deg).",
      group=G,
      inputs={"target": I("entity_ref", "What to face.")},
      outputs={"base_yaw_deg": O("number", "Measured heading after the turn.")},
      requires=[],
      ensures=[P("facing", target="$target")],
      invalidates=["reachable(*)", "in_view(*)", "pointing_at(*)"],
      paths=[
          Path("rotate_empty", [EMPTY_R, W("robot", "left_held", "falsy"), W("robot", "right_arm_stowed", "truthy")],
               [St("policy_099", "$target", out="heading"), St("policy_036", "#heading.delta_yaw_deg")],
               note="Tucked and empty: the measured in-place rotation primitive."),
          Path("rotate_loaded", [], [St("policy_066", "$target")],
               note="With a load or unfolded arm: slower turn with grasp checks."),
      ],
      relations=[R("sequence", "look", "the target must be observed", bind={"target": "$target"}),
                 R("sequence", "point", "the target must be indicated", bind={"target": "$target"}),
                 R("alternative", "navigate", "turning in place is blocked by furniture",
                   bind={"destination": "$target"})],
      use_when="The target is beside or behind the robot and only the heading must change.",
      distinct_from={"look": "look moves the head only; face moves the whole base."},
      failure_modes=["turning in place would hit furniture"])

skill("retreat", "obstacle", "Retreat from an obstacle",
      "Back the base straight away from a piece of furniture, appliance or object until it is at least the "
      "given distance away; a held load stays held.",
      group=G,
      inputs={"obstacle": I("place_ref", "What to back away from."),
              "distance_m": I("positive_number", "Required clearance from the obstacle footprint.", default=0.4)},
      outputs={"moved_m": O("number", "Measured base displacement.")},
      requires=[],
      ensures=[P("base_clear_of", place="$obstacle", distance_m="$distance_m")],
      invalidates=["base_near(*)", "reachable(*)", "facing(*)", "in_view(*)"],
      paths=[
          Path("microwave_door_sweep", [W("obstacle", "instance", "equals", "kitchen_microwave")],
               [St("policy_030", "$obstacle")],
               note="The microwave's measured hinge-clearance pose (also when loaded)."),
          Path("bimanual_or_left_load", [W("robot", "left_held", "truthy")], [St("policy_067", "$obstacle", "$distance_m")]),
          Path("loaded", [HELD_R], [St("policy_035", "$distance_m")],
               note="Straight reverse with the right-hand load."),
          Path("empty", [], [St("policy_100", "$obstacle", "$distance_m", out="plan"),
                             St("policy_037", "#plan.forward_m")]),
      ],
      relations=[R("sequence", "navigate", "the robot must leave after backing out", reason="free start cell"),
                 R("sequence", "open", "a door's swing needs room in front of the robot",
                   bind={"articulated": "$obstacle"})],
      use_when="The base is too close to open a door, turn, or start a path.",
      distinct_from={"navigate": "retreat has no destination; it only increases clearance."},
      failure_modes=["the path behind the base is blocked"])

skill("crouch", "torso", "Crouch the torso",
      "Lower the torso lift to its bottom (or a requested height) for floor and low-shelf work.",
      group=G,
      inputs={"height_m": I("number", "Optional torso joint target in [-0.54, 0]; omit for the lowest.",
                            required=False)},
      requires=[],
      ensures=[P("torso_raised", negated=True)],
      invalidates=["torso_raised()", "torso_lowered()", "torso_at(*)", "reachable(*)", "in_view(*)"],
      paths=[Path("to_height", [W("args", "height_m", "truthy")], [St("policy_004", "$height_m")],
                  ensures=[P("torso_at", height_m="$height_m")]),
             Path("lowest", [], [St("policy_005")], ensures=[P("torso_lowered")])],
      relations=[R("sequence", "pick", "the object is on the floor or a low shelf", reason="floor reach"),
                 R("sequence", "stand", "low work is done", reason="restore travel height")],
      distinct_from={"bend": "bend pitches the waist forward; crouch lowers the torso vertically."})

skill("stand", "torso", "Stand up to full height",
      "Raise the torso lift to its top travel height.",
      group=G, inputs={}, requires=[], ensures=[P("torso_raised")],
      invalidates=["torso_lowered()", "reachable(*)", "in_view(*)"],
      paths=[Path("highest", [], [St("policy_006")])],
      relations=[R("sequence", "navigate", "the robot drives after low work", reason="travel height"),
                 R("alternative", "reset", "the arm and waist must also be restored")],
      distinct_from={"lift": "lift raises a held object, stand raises the body."})

skill("bend", "waist", "Bend the waist",
      "Pitch the waist forward to extend the reach over a deep surface.",
      group=G,
      inputs={"pitch_rad": I("positive_number", "Forward pitch in rad (max 0.69); omit for the maximum.",
                             required=False)},
      requires=[],
      ensures=[P("waist_bent", min_pitch_rad=0.2)],
      invalidates=["waist_straight()", "reachable(*)", "in_view(*)"],
      paths=[Path("to_pitch", [W("args", "pitch_rad", "truthy")], [St("policy_007", "$pitch_rad")]),
             Path("full", [], [St("policy_008")])],
      relations=[R("sequence", "straighten", "the reach is done", reason="restore upright posture"),
                 R("sequence", "approach", "the target was just out of reach", reason="extra reach")])

skill("straighten", "waist", "Straighten the waist",
      "Return the waist pitch to upright.", group=G, inputs={}, requires=[],
      ensures=[P("waist_straight")], invalidates=["waist_bent(*)", "reachable(*)", "in_view(*)"],
      paths=[Path("upright", [], [St("policy_009")])],
      relations=[R("sequence", "navigate", "the robot drives after a bent reach", reason="travel posture"),
                 R("alternative", "reset", "the arm and torso must also be restored")])

skill("tuck", "arm", "Tuck an arm",
      "Fold an empty arm to its travel posture along a collision-checked path.",
      group=G,
      inputs={"hand": I("hand", "Which arm to fold.", default="right", enum=["right", "left"])},
      requires=[P("hand_empty", hand="$hand")],
      ensures=[P("arm_stowed", hand="$hand")],
      invalidates=["reachable(*)", "pointing_at(*)"],
      paths=[Path("left", [W("args", "hand", "equals", "left")], [St("policy_091")]),
             Path("right", [], [St("policy_003")])],
      relations=[R("sequence", "navigate", "the robot drives next", reason="a folded arm is the travel posture"),
                 R("fallback", "retreat", "the fold collides with furniture", fallback_type="recover",
                   reason="More room around the base gives the fold a collision-free path.")])

skill("reset", "posture", "Reset the posture",
      "Return to the home posture: fingers open, arm folded, torso up, waist straight, by a collision-checked "
      "joint-space move. Used to recover from an unknown arm state.",
      group=G, inputs={},
      requires=[P("hand_empty", hand="right")],
      ensures=[P("arm_stowed", hand="right"), P("torso_raised"), P("waist_straight")],
      invalidates=["torso_lowered()", "waist_bent(*)", "reachable(*)", "pointing_at(*)", "in_view(*)"],
      paths=[Path("joint_home", [], [St("policy_040"), St("policy_003"), St("policy_095", out="home"),
                                     St("policy_039", "#home.target")])],
      relations=[R("sequence", "navigate", "after a failed manipulation, before driving on",
                   reason="a known posture makes the base path plannable")],
      distinct_from={"tuck": "tuck only folds one arm; reset also restores torso and waist."})

# ================================================================= perception & gesture
G = "perception_and_gesture"

skill("look", "target", "Look at a target",
      "Aim the head camera at a target (turning the base if it is outside the head yaw range) and record every "
      "annotated object in view as observed.",
      group=G,
      inputs={"target": I("entity_ref", "What to look at.")},
      outputs={"seen": O("object_list", "Objects in the head camera frustum with clear line of sight.")},
      requires=[],
      ensures=[P("in_view", target="$target"), P("observed", target="$target")],
      invalidates=["in_view(*)"],
      paths=[Path("head_only", [W("target", "bearing_abs_deg", "lte", 55)], [St("policy_068", "$target")]),
             Path("turn_then_head", [], [St("policy_066", "$target"), St("policy_068", "$target")])],
      relations=[R("sequence", "approach", "the observed target will be manipulated", bind={"target": "$target"}),
                 R("fallback", "navigate", "the line of sight is blocked", bind={"destination": "$target"},
                   fallback_type="repair"),
                 R("alternative", "inspect", "the target is a receptacle whose contents matter",
                   bind={"receptacle": "$target"})],
      distinct_from={"inspect": "inspect reports a receptacle's contents; look only aims the camera.",
                     "search": "search visits several places to find an unseen object."})

skill("inspect", "receptacle", "Inspect a receptacle",
      "Look into a container, a cabinet, an appliance cavity or onto a support and report the objects inside or on "
      "it. A closed cabinet is opened for the look and closed again.",
      group=G,
      inputs={"receptacle": I("entity_ref", "Container, articulated cabinet/appliance or support to examine.")},
      outputs={"contents": O("object_list", "Objects found inside/on the receptacle and visible.")},
      requires=[P("base_near", place="$receptacle")],
      ensures=[P("observed", target="$receptacle")],
      paths=[Path("closed_cabinet", [W("receptacle", "kind", "equals", "articulated"),
                                     W("receptacle", "is_open", "falsy")],
                  [St("policy_003"), St("policy_062", "$receptacle"), St("policy_088", "$receptacle"),
                   St("policy_003"), St("policy_063", "$receptacle")],
                  requires=[P("hand_empty", hand="right")],
                  note="Open with the annotation-selected route, look, close again."),
             Path("open_view", [], [St("policy_088", "$receptacle")])],
      relations=[R("sequence", "pick", "an object found inside must be taken out",
                   reason="contents output names the object"),
                 R("sequence", "empty", "every object inside must be removed", bind={"container": "$receptacle"}),
                 R("alternative", "look", "only the receptacle itself must be seen", bind={"target": "$receptacle"})],
      distinct_from={"look": "look reports nothing about contents.",
                     "search": "inspect examines one given receptacle; search chooses where to look."})

skill("search", "object", "Search for an object",
      "Find an object whose location is unknown: visit the supports of a room in order of distance and aim the "
      "head at each surface until the object is seen.",
      group=G,
      inputs={"object": I("object_ref", "The object to find."),
              "region": I("room_ref", "Room to search; default the robot's room.", required=False)},
      outputs={"found_on": O("support_ref", "Support under the object when it was seen."),
               "visited": O("object_list", "Furniture visited in order.")},
      requires=[],
      ensures=[P("observed", target="$object")],
      invalidates=["base_near(*)", "reachable(*)", "facing(*)", "in_view(*)"],
      paths=[Path("room_sweep", [], [St("policy_070", "$object", "$region")])],
      relations=[R("sequence", "navigate", "the found object must be fetched", bind={"destination": "$object"}),
                 R("fallback", "explore", "the object is not on any visited support", fallback_type="recover",
                   reason="room coverage marks every visible object observed, including the target"),
                 R("fallback", "inspect", "the object may be inside a closed cabinet", fallback_type="substitute")],
      distinct_from={"explore": "explore covers a room without a target."})

skill("explore", "room", "Explore a room",
      "Cover a room from up to three viewpoints with a left/centre/right head sweep; succeeds when at least 75 % "
      "of the room's supports and objects were seen.",
      group=G,
      inputs={"room": I("room_ref", "The room to cover.")},
      outputs={"seen": O("object_list", "Objects observed during the sweep.")},
      requires=[],
      ensures=[P("room_explored", room="$room")],
      invalidates=["base_near(*)", "reachable(*)", "facing(*)", "in_view(*)"],
      paths=[Path("viewpoints", [], [St("policy_069", "$room")])],
      relations=[R("sequence", "search", "a specific object must then be located", reason="narrow to one target")])

skill("point", "target", "Point at a target",
      "Point the closed right fingers at a target (finger axis within 8 deg) to indicate it.",
      group=G,
      inputs={"target": I("entity_ref", "What to indicate.")},
      requires=[P("hand_empty", hand="right")],
      ensures=[P("pointing_at", target="$target"), P("hand_empty", hand="right")],
      invalidates=["arm_stowed(right)", "reachable(*)"],
      paths=[Path("front", [W("target", "bearing_abs_deg", "lte", 60)],
                  [St("policy_041"), St("policy_101", "$target", out="aim"),
                   St("policy_038", "#aim.position", "#aim.rotation", position_tolerance=0.04, rotation_tolerance=0.2)]),
             Path("turn_and_point", [], [St("policy_071", "$target")])],
      relations=[R("sequence", "tuck", "the gesture is finished", bind={"hand": "right"}),
                 R("alternative", "look", "a gaze is enough to indicate the target", bind={"target": "$target"})])

skill("present", "object", "Present a held object",
      "Hold the carried object in front of the body at 0.9-1.4 m height, inside the head camera view.",
      group=G,
      inputs={"object": I("object_ref", "The right-held object to show.")},
      requires=[P("holding", hand="right", object="$object")],
      ensures=[P("presenting", object="$object"), P("holding", hand="right", object="$object")],
      invalidates=["reachable(*)"],
      paths=[Path("front_of_head", [], [St("policy_072", "$object")])],
      relations=[R("sequence", "place", "the object is put away after showing it", bind={"object": "$object"}),
                 R("sequence", "handover", "the object is passed to the left hand", bind={"object": "$object"}),
                 R("alternative", "lift", "only the height of the load matters", bind={"object": "$object"})])

# ================================================================= grasp & hand
G = "grasp_and_hand"

skill("pick", "object", "Pick an object",
      "Grasp one object with the right gripper and lift it. The grasp path is chosen from the object's GT "
      "annotation and state: microwave cavity grasp, floor corner pinch, slide-to-edge + edge pinch for flat items, "
      "handle pinch, rectangular or round rim pinch, top pinch, or a two-handed lift for wide items.",
      group=G,
      inputs={"object": I("object_ref", "The object to grasp."),
              "hands": I("hand", "\"both\" requests a two-handed lift for wide items.", required=False,
                         enum=["right", "both"]),
              "grasp": I("tag", "Optional grasp style to request: handle, rim, top or edge.", required=False,
                         enum=["handle", "rim", "top", "edge"]),
              "pass_by": I("pose2d", "Optional base waypoint: grasp while driving past.", required=False)},
      outputs={"grasp": O("hand", "Grasp route actually used."),
               "lift_m": O("number", "Measured lift of the object.")},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$object")],
      ensures=[P("holding", hand="right", object="$object")],
      invalidates=["on($object,*)", "inside($object,*)", "on_top_of($object,*)", "on_floor($object)",
                   "hand_empty(right)", "grasp_clearance($object)", "edge_overhang($object)",
                   "at_initial_place($object)", "arm_stowed(right)", "in_appliance($object,*)",
                   "on_burner($object,*)", "covered(*,$object)"],
      paths=[
          Path("microwave_cavity", [W("object", "location", "equals", "microwave_cavity")],
               [St("policy_048", "$object", "@object.appliance")],
               requires=[P("is_open", articulated="@object.appliance")],
               note="Front withdrawal through the open door."),
          Path("inside_cabinet_or_fridge", [W("object", "location", "in", ["refrigerator", "cabinet"])],
               [St("policy_061", "$object")],
               requires=[P("is_open", articulated="@object.appliance")],
               note="Annotation-selected grasp through the opened door."),
          Path("handle_requested", [W("args", "grasp", "equals", "handle"),
                                    W("object", "grasp_types", "contains", "handle_pinch"),
                                    W("object", "handle_collider", "truthy")],
               [St("policy_055", "$object")],
               note="Handle pinch on request; a container held by its handle can swing, so carry it gently."),
          Path("on_the_move", [W("args", "pass_by", "truthy"), W("object", "grasp_types", "contains", "top_pinch")],
               [St("policy_052", "$object", "$pass_by")],
               requires=[P("grasp_clearance", object="$object")]),
          Path("two_hand_box", [W("args", "hands", "equals", "both"), W("object", "wide_box", "truthy")],
               [St("policy_057", "$object")],
               requires=[P("hand_empty", hand="left")],
               ensures=[P("holding", hand="left", object="$object")]),
          Path("two_hand_flat", [W("args", "hands", "equals", "both"), W("object", "flat", "truthy")],
               [St("policy_045", "$object"), St("policy_056", "$object")],
               requires=[P("hand_empty", hand="left")],
               ensures=[P("holding", hand="left", object="$object")]),
          Path("floor_top", [W("object", "on_floor", "truthy"), W("object", "grasp_types", "contains", "top_pinch")],
               [St("policy_065", "$object"), St("policy_042", "$object"), St("policy_010", "$object")],
               requires=[P("on_floor", object="$object")],
               note="Approach, lower the torso and lean over the item, then pinch it from above. Flat objects "
                    "lying on the floor (books, notebooks) have no pick path: the parallel gripper cannot get "
                    "a pad under or across them."),
          Path("flat_overhang_ready", [W("object", "flat", "truthy"), W("object", "edge_ready", "truthy")],
               [St("policy_013", "$object")], requires=[P("edge_overhang", object="$object")],
               note="The overhang already exists (e.g. after expose): pinch it directly."),
          Path("flat_edge", [W("object", "flat", "truthy")],
               [St("policy_045", "$object"), St("policy_013", "$object")],
               note="Slide the flat item until it overhangs a free edge, then pinch the overhang."),
          Path("rect_rim", [W("object", "grasp_types", "contains", "rim_pinch_rect")], [St("policy_012", "$object")]),
          Path("round_rim", [W("object", "grasp_types", "contains", "rim_pinch")], [St("policy_011", "$object")],
               requires=[P("grasp_clearance", object="$object")],
               note="Preferred for cups, mugs, bowls and pots: a rim pinch does not let the vessel swing."),
          Path("handle", [W("object", "grasp_types", "contains", "handle_pinch"),
                          W("object", "handle_collider", "truthy")],
               [St("policy_055", "$object")]),
          Path("top_pinch", [W("object", "grasp_types", "contains", "top_pinch")], [St("policy_010", "$object")],
               requires=[P("grasp_clearance", object="$object")]),
          Path("annotation_dispatch", [W("object", "grasp_types", "truthy")], [St("policy_061", "$object")],
               note="Any other annotated pinch: the general dispatcher selects it."),
      ],
      relations=[
          R("sequence", "navigate", "the object must be carried elsewhere", reason="carry path is chosen from holding"),
          R("sequence", "place", "the object goes onto a surface or into a container", bind={"object": "$object"}),
          R("sequence", "lift", "the object must clear a high rim while carried", bind={"object": "$object"}),
          R("fallback", "expose", "a flat object cannot be pinched from the top: push it to the edge by hand, "
            "then pick the overhang", bind={"object": "$object"}, fallback_type="repair", repairs="edge_overhang"),
          R("fallback", "separate", "fingers have no room beside the object (grasp_clearance false)",
            bind={"object": "$object"}, fallback_type="repair", repairs="grasp_clearance"),
          R("fallback", "pull", "the object sits too deep to reach", bind={"object": "$object"},
            fallback_type="recover", reason="dragging it toward the base brings it into the arm's envelope"),
          R("fallback", "approach", "no grasp is reachable from base poses near the current one",
            bind={"target": "$object"}, fallback_type="recover", reason="a base pose with verified IK at the object"),
          R("fallback", "upright", "a tall object fell over and its top pinch is gone", bind={"object": "$object"},
            fallback_type="recover", reason="standing it up restores the annotated top pinch"),
          R("fallback", "crouch", "the object is on the floor or a low shelf", fallback_type="recover",
            reason="the lowered torso brings the gripper to floor height"),
          R("fallback", "uncover", "the object to take is a lid-covered container's content", fallback_type="recover",
            reason="the lid blocks every approach into the container"),
          R("fallback", "open", "the object is inside a closed cabinet or appliance", fallback_type="repair",
            repairs="is_open"),
          R("alternative", "regrasp", "the object is already in the hand but badly held", bind={"object": "$object"}),
      ],
      use_when="The robot must hold an object for any later hand action.",
      distinct_from={"regrasp": "regrasp improves a grasp on an object that is already held.",
                     "uncover": "uncover lifts a lid off its container and keeps it.",
                     "fetch": "fetch also navigates and places."},
      includes=["grasp route selection from GT annotation", "base re-park for the chosen grasp",
                "approach, close, lift, measured hold check"],
      excludes=["transport", "placement"],
      failure_modes=["no reachable grasp from any base pose", "object not held after lift (slipped)",
                     "no free support edge for a flat object"])

skill("place", "object", "Place a held object",
      "Put the right-held object down on a support surface or into an open container and release it. "
      "The path follows the receptacle and grasp: microwave cavity (insert, release, withdraw), container, "
      "edge-held flat object slid back over an edge, ordinary surface (optionally near a hint point), or while "
      "driving past.",
      group=G,
      inputs={"object": I("object_ref", "The held object."),
              "receptacle": I("receptacle_ref", "A support surface or an open container."),
              "hint_xy": I("xy", "Optional preferred position on a surface.", required=False),
              "pass_by": I("pose2d", "Optional base waypoint: place while driving past.", required=False)},
      outputs={"position": O("xy", "Measured bottom position after release.")},
      requires=[P("holding", hand="right", object="$object"), P("base_near", place="$receptacle")],
      ensures=[P("hand_empty", hand="right")],
      invalidates=["holding(right,$object)", "presenting($object)", "base_clear_of(*)"],
      paths=[
          Path("microwave_staged", [W("receptacle", "kind", "equals", "support"),
                                    W("receptacle", "is_microwave_cavity", "truthy"),
                                    W("robot", "right_kind", "equals", "pinch")],
               [St("policy_018", "$object", "$receptacle"), St("policy_019", "$object"), St("policy_020", "$object")],
               requires=[P("is_open", articulated="kitchen_microwave")],
               ensures=[P("on", object="$object", support="$receptacle"),
                        P("in_appliance", object="$object", appliance="kitchen_microwave")]),
          Path("microwave", [W("receptacle", "kind", "equals", "support"), W("receptacle", "is_microwave_cavity", "truthy")],
               [St("policy_021", "$object", "$receptacle")],
               requires=[P("is_open", articulated="kitchen_microwave")],
               ensures=[P("on", object="$object", support="$receptacle"),
                        P("in_appliance", object="$object", appliance="kitchen_microwave")]),
          Path("cabinet_or_fridge_shelf", [W("receptacle", "kind", "equals", "support"),
                                           W("receptacle", "category", "equals", "cabinet_inside"),
                                           W("receptacle", "appliance", "truthy")],
               [St("policy_015", "$object", "$receptacle", hint="$hint_xy")],
               requires=[P("is_open", articulated="@receptacle.appliance")],
               ensures=[P("on", object="$object", support="$receptacle")]),
          Path("container", [W("receptacle", "kind", "equals", "object")], [St("policy_016", "$object", "$receptacle")],
               requires=[P("uncovered", container="$receptacle")],
               ensures=[P("inside", object="$object", container="$receptacle")]),
          Path("on_the_move", [W("receptacle", "kind", "equals", "support"), W("args", "pass_by", "truthy")],
               [St("policy_053", "$object", "$receptacle", "$pass_by", xy="$hint_xy")],
               ensures=[P("on", object="$object", support="$receptacle")]),
          Path("edge_held_flat", [W("receptacle", "kind", "equals", "support"), W("robot", "right_kind", "equals", "edge")],
               [St("policy_017", "$object", "$receptacle", hint="$hint_xy")],
               ensures=[P("on", object="$object", support="$receptacle")]),
          Path("stove_burner", [W("receptacle", "kind", "equals", "support"),
                                W("receptacle", "category", "equals", "cooktop")],
               [St("policy_015", "$object", "$receptacle", hint="@receptacle.burner_xy")],
               ensures=[P("on", object="$object", support="$receptacle"),
                        P("on_burner", object="$object", appliance="@receptacle.appliance")],
               note="Cookware goes centred on the burner disc so the stove can heat it."),
          Path("surface", [W("receptacle", "kind", "equals", "support")],
               [St("policy_015", "$object", "$receptacle", hint="$hint_xy")],
               ensures=[P("on", object="$object", support="$receptacle")]),
      ],
      relations=[
          R("sequence", "close", "the object went into a cabinet or appliance whose door must be shut",
            reason="appliance cycles and task goals require closed doors"),
          R("sequence", "heat", "the food went into the microwave or onto the stove", bind={"food": "$object"}),
          R("sequence", "tuck", "the hand is empty and the robot drives next", bind={"hand": "right"}),
          R("fallback", "drop", "a deep container leaves no room to lower the hand inside",
            bind={"object": "$object", "container": "$receptacle"}, fallback_type="substitute"),
          R("fallback", "approach", "the receptacle is out of reach", bind={"target": "$receptacle"},
            fallback_type="recover", reason="a base pose with verified IK above the receptacle"),
          R("fallback", "open", "the receptacle is behind a closed door", fallback_type="repair",
            repairs="is_open"),
          R("fallback", "uncover", "the container has its lid on", bind={"container": "$receptacle"},
            fallback_type="repair", repairs="uncovered"),
          R("fallback", "regrasp", "the object turned in the hand and no longer clears the target",
            bind={"object": "$object"}, fallback_type="recover", reason="a fresh centred grasp restores the hold offset"),
          R("alternative", "stack", "the object should rest on another object", bind={"object": "$object"}),
          R("alternative", "drop", "the target is a deep bin and a gentle release is not required",
            bind={"object": "$object", "container": "$receptacle"}),
      ],
      distinct_from={"drop": "drop releases above a container opening without lowering.",
                     "stack": "stack targets another object's top face.",
                     "release": "release opens the fingers where the object already rests."},
      failure_modes=["target unreachable", "container shifted before release", "object not on/in target after release"])

skill("drop", "object", "Drop an object into a container",
      "Hold the object 5 cm above a container's opening, centred, and let go; the object falls in.",
      group=G,
      inputs={"object": I("object_ref", "The held object."), "container": I("container_ref", "The open container.")},
      requires=[P("holding", hand="right", object="$object"), P("base_near", place="$container"),
                P("uncovered", container="$container")],
      ensures=[P("inside", object="$object", container="$container"), P("hand_empty", hand="right")],
      invalidates=["holding(right,$object)"],
      paths=[Path("above_opening", [], [St("policy_073", "$object", "$container")])],
      relations=[R("sequence", "pick", "more items go into the same container", reason="the hand is free again"),
                 R("alternative", "place", "a gentle release inside is needed",
                   bind={"object": "$object", "receptacle": "$container"})],
      distinct_from={"place": "place lowers the object onto the container floor before opening."})

skill("stack", "object", "Stack an object on another",
      "Set the held object centred on the top face of another object (block on block, plate on plate).",
      group=G,
      inputs={"object": I("object_ref", "The held object."), "base": I("object_ref", "The object to stack onto.")},
      requires=[P("holding", hand="right", object="$object"), P("base_near", place="$base"),
                P("top_clear", object="$base")],
      ensures=[P("on_top_of", object="$object", base="$base"), P("hand_empty", hand="right")],
      invalidates=["holding(right,$object)", "top_clear($base)"],
      paths=[Path("top_face", [], [St("policy_074", "$object", "$base")])],
      relations=[R("sequence", "pick", "a taller stack is built", reason="the hand is free for the next block"),
                 R("fallback", "pick", "the base's top is occupied: remove the top object first",
                   fallback_type="recover", reason="taking the top object off frees the base's top face"),
                 R("alternative", "place", "a support surface is acceptable instead", bind={"object": "$object"})])

skill("release", "object", "Release an object",
      "Open one gripper where the object already rests (e.g. let go of a braced pot, or of an object that was set "
      "down by another action) and back the fingers off.",
      group=G,
      inputs={"object": I("object_ref", "The object in the hand."),
              "hand": I("hand", "Which gripper opens.", default="right", enum=["right", "left"])},
      requires=[P("holding", hand="$hand", object="$object")],
      ensures=[P("hand_empty", hand="$hand")],
      invalidates=["holding($hand,$object)", "steadied($object)"],
      paths=[Path("open_in_place", [], [St("policy_096", "$object", "$hand")])],
      relations=[R("sequence", "tuck", "the arm is folded after letting go", bind={"hand": "$hand"}),
                 R("alternative", "drop", "the object should fall into a container", bind={"object": "$object"})],
      distinct_from={"drop": "drop moves above a container first; release does not move the object."})

skill("handover", "object", "Hand an object over to the left hand",
      "Transfer a right-held object into the left gripper and open the right gripper.",
      group=G,
      inputs={"object": I("object_ref", "The right-held object.")},
      requires=[P("holding", hand="right", object="$object"), P("hand_empty", hand="left")],
      ensures=[P("holding", hand="left", object="$object"), P("hand_empty", hand="right")],
      invalidates=["holding(right,$object)"],
      paths=[Path("right_to_left", [], [St("policy_059", "$object")])],
      relations=[R("sequence", "open", "the right hand must open a door while the left carries the load",
                   reason="open's left_holds_load path"),
                 R("sequence", "pick", "a second object is picked with the free right hand", reason="right hand free"),
                 R("alternative", "brace", "the left hand should hold an object that stays on its support")])

skill("lift", "object", "Lift a held object",
      "Raise the held object until its bottom is at least the given world height (e.g. above a bin rim or a "
      "furniture edge before carrying).",
      group=G,
      inputs={"object": I("object_ref", "The held object."),
              "height_m": I("positive_number", "Minimum world height of the object's bottom.", default=0.55)},
      requires=[P("holding", hand="right", object="$object")],
      ensures=[P("held_above", object="$object", height_m="$height_m"), P("holding", hand="right", object="$object")],
      invalidates=["held_below($object,*)"],
      paths=[Path("raise", [], [St("policy_034", "$height_m")])],
      relations=[R("sequence", "navigate", "the object is carried over furniture", reason="carry clearance"),
                 R("sequence", "drop", "the object is released over a tall container", bind={"object": "$object"})],
      distinct_from={"stand": "stand moves the torso, not the held object.", "lower": "opposite direction."})

skill("lower", "object", "Lower a held object",
      "Move the held object down until its bottom is at most the given height (e.g. under a low shelf clearance).",
      group=G,
      inputs={"object": I("object_ref", "The held object."),
              "height_m": I("positive_number", "Maximum world height of the object's bottom.")},
      requires=[P("holding", hand="right", object="$object")],
      ensures=[P("held_below", object="$object", height_m="$height_m"), P("holding", hand="right", object="$object")],
      invalidates=["held_above($object,*)"],
      paths=[Path("descend", [], [St("policy_093", "$object", "$height_m")])],
      relations=[R("sequence", "place", "the object goes onto a low shelf or into the fridge", bind={"object": "$object"}),
                 R("alternative", "lift", "opposite direction", bind={"object": "$object"})])

skill("rotate", "object", "Rotate a held object",
      "Turn the held object about the vertical axis by the requested angle (e.g. align a book's spine).",
      group=G,
      inputs={"object": I("object_ref", "The held object."),
              "degrees": I("number", "Yaw change in degrees (positive = counter-clockwise).")},
      requires=[P("holding", hand="right", object="$object")],
      ensures=[P("yaw_rotated", object="$object", degrees="$degrees"), P("holding", hand="right", object="$object")],
      paths=[Path("wrist_yaw", [], [St("policy_075", "$object", "$degrees")])],
      relations=[R("sequence", "place", "the object is set down in the new orientation", bind={"object": "$object"}),
                 R("alternative", "regrasp", "the grasp, not the yaw, must change", bind={"object": "$object"})],
      distinct_from={"flip": "flip turns an object upside down; rotate keeps it level."})

skill("regrasp", "object", "Regrasp a held object",
      "Set the held object down on a support and grasp it again with a fresh, centred grasp (recovery when the "
      "object has pivoted in the pinch).",
      group=G,
      inputs={"object": I("object_ref", "The held object."),
              "support": I("support_ref", "Where to set it down briefly.")},
      outputs={"grasp": O("hand", "Grasp kind after the regrasp.")},
      requires=[P("holding", hand="right", object="$object"), P("base_near", place="$support")],
      ensures=[P("holding", hand="right", object="$object")],
      paths=[Path("set_down_and_pick", [], [St("policy_076", "$object", "$support")])],
      relations=[R("sequence", "place", "the corrected grasp is used to place precisely", bind={"object": "$object"})],
      distinct_from={"pick": "pick starts from an empty hand."})

skill("brace", "object", "Brace an object with the left hand",
      "Pinch a resting container with the left gripper so it cannot slide while the right hand stirs, wipes or "
      "pours into it.",
      group=G,
      inputs={"object": I("object_ref", "The resting object to hold still.")},
      requires=[P("hand_empty", hand="left"), P("base_near", place="$object")],
      ensures=[P("steadied", object="$object"), P("holding", hand="left", object="$object")],
      invalidates=["arm_stowed(left)", "hand_empty(left)"],
      paths=[Path("left_rim_pinch", [W("object", "location", "in", ["support", "floor", "container"])],
                  [St("policy_077", "$object")],
                  note="Only an object standing in the open (not behind an appliance or cabinet door).")],
      relations=[R("sequence", "stir", "the braced container is stirred", bind={"container": "$object"}),
                 R("sequence", "release", "bracing is finished", bind={"object": "$object", "hand": "left"})])

skill("flip", "object", "Flip a flat object over",
      "Turn a flat object upside down where it lies: slide it to an edge, pinch the overhang, lift, roll the hand "
      "180 deg, lay it back and release.",
      group=G,
      inputs={"object": I("object_ref", "A flat object (book, plate, notebook) on a support.")},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$object")],
      ensures=[P("flipped", object="$object"), P("hand_empty", hand="right")],
      paths=[Path("edge_roll", [W("object", "flat", "truthy")],
                  [St("policy_045", "$object"), St("policy_013", "$object"), St("policy_078", "$object")])],
      relations=[R("sequence", "center", "the object is left overhanging the edge", bind={"object": "$object"}),
                 R("fallback", "center", "the flipped object landed too close to the edge", bind={"object": "$object"},
                   fallback_type="recover", reason="pushes it back from the edge")])

# ================================================================= non-prehensile contact
G = "contact"

skill("push", "object", "Push an object",
      "Slide an object along its support in a direction with closed fingers: from behind when there is room, "
      "or by pressing on its top and dragging when it stands against a wall or closed edge.",
      group=G,
      inputs={"object": I("object_ref", "The object to slide."),
              "direction_xy": I("unit_vec2", "World horizontal direction."),
              "distance_m": I("positive_number", "Requested travel.")},
      outputs={"moved_m": O("number", "Measured displacement along the direction.")},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$object")],
      ensures=[P("object_moved", object="$object", direction_xy="$direction_xy", distance_m="$distance_m")],
      invalidates=["edge_overhang($object)", "grasp_clearance($object)", "away_from_edge($object,*)",
                   "at_initial_place($object)"],
      paths=[Path("drag_from_top", [W("object", "near_closed_edge", "truthy")],
                  [St("policy_041"), St("policy_044", "$object", "@object.support", "$direction_xy", "$distance_m")]),
             Path("thin_auto", [W("object", "flat", "truthy")],
                  [St("policy_026", "$object", "@object.support", "$direction_xy", "$distance_m")],
                  note="The dispatcher chooses push or drag for thin items."),
             Path("from_behind", [], [St("policy_041"),
                                      St("policy_043", "$object", "@object.support", "$direction_xy", "$distance_m")])],
      relations=[R("sequence", "pick", "the object was pushed into a graspable spot", bind={"object": "$object"}),
                 R("alternative", "pull", "the object should come toward the robot")],
      distinct_from={"pull": "pull drags toward the base to make an object reachable.",
                     "expose": "expose pushes until a graspable overhang exists.",
                     "separate": "separate pushes away from the nearest neighbour.",
                     "center": "center pushes away from the support edges.",
                     "roll": "roll makes a cylinder rotate instead of slide.",
                     "tip": "tip pushes high so the object falls over."})

skill("pull", "object", "Pull an object closer",
      "Drag an object toward the robot with the pads pressed on its top until it is within reach "
      "(e.g. from the back of a deep counter); if the pads slide over a round or slippery top, the fingers hook "
      "the far side and push it toward the robot.",
      group=G,
      inputs={"object": I("object_ref", "The object to drag."),
              "distance_m": I("positive_number", "Requested travel toward the base.", default=0.15)},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$object")],
      ensures=[P("moved_toward_base", object="$object", distance_m="$distance_m"), P("reachable", target="$object")],
      invalidates=["grasp_clearance($object)", "at_initial_place($object)"],
      paths=[Path("top_drag", [], [St("policy_041"), St("policy_079", "$object", "$distance_m")])],
      relations=[R("sequence", "pick", "the object is now close enough to grasp", bind={"object": "$object"})])

skill("expose", "object", "Expose a grasp edge",
      "Push a flat object (book, plate, notebook) until it overhangs a free support edge by >= 5.5 cm while its "
      "centre of mass stays on the support, so the overhang can be pinched.",
      group=G,
      inputs={"object": I("object_ref", "A flat object on a support.")},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$object")],
      ensures=[P("edge_overhang", object="$object")],
      invalidates=["at_initial_place($object)", "away_from_edge($object,*)"],
      paths=[Path("slide_to_edge", [W("object", "flat", "truthy")], [St("policy_045", "$object")])],
      relations=[R("sequence", "pick", "pinch the overhang", bind={"object": "$object"}),
                 R("sequence", "flip", "turn the object over", bind={"object": "$object"}),
                 R("fallback", "approach", "no base pose reaches behind the object", bind={"target": "$object"},
                   fallback_type="repair")])

skill("separate", "object", "Separate an object from its neighbour",
      "Push an object straight away from its closest neighbour until there is room for a finger "
      "(>= 3.5 cm gap) without leaving the support.",
      group=G,
      inputs={"object": I("object_ref", "The crowded object.")},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$object"),
                P("grasp_clearance", negated=True, object="$object")],
      ensures=[P("grasp_clearance", object="$object")],
      invalidates=["at_initial_place($object)"],
      paths=[Path("push_apart", [], [St("policy_080", "$object")])],
      relations=[R("sequence", "pick", "grasp the freed object", bind={"object": "$object"})])

skill("center", "object", "Center an object on its support",
      "Push an object back from the support edges until every edge margin is at least the requested value "
      "(secures an item left overhanging).",
      group=G,
      inputs={"object": I("object_ref", "The object near an edge."),
              "margin_m": I("positive_number", "Required margin to every edge.", default=0.06)},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$object")],
      ensures=[P("away_from_edge", object="$object", margin_m="$margin_m")],
      invalidates=["edge_overhang($object)"],
      paths=[Path("push_inward", [], [St("policy_083", "$object", "$margin_m")])],
      relations=[R("alternative", "push", "a specific direction is wanted", bind={"object": "$object"}),
                 R("sequence", "pick", "the secured object is grasped later", bind={"object": "$object"})])

skill("roll", "object", "Roll a cylinder",
      "Roll a lying constant-radius cylinder (rolling pin, can on its side) along its support by pressing on its "
      "top; the object must rotate, not slide. A bottle with a neck rolls in an arc around the neck and is not "
      "a valid noun.",
      group=G,
      inputs={"object": I("object_ref", "A lying cylinder."),
              "distance_m": I("positive_number", "Requested travel.", default=0.10)},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$object"), P("lying", object="$object")],
      ensures=[P("object_rolled", object="$object")],
      invalidates=["at_initial_place($object)", "grasp_clearance($object)"],
      paths=[Path("push_above_axis", [], [St("policy_081", "$object", "$distance_m")])],
      relations=[R("sequence", "pick", "the rolled object is then grasped", bind={"object": "$object"}),
                 R("alternative", "push", "sliding is acceptable", bind={"object": "$object"})])

skill("tip", "object", "Tip an object over",
      "Push a standing tall object near its top so it falls onto its side on the same support "
      "(lays down a carton or bottle that is too tall to top-pinch).",
      group=G,
      inputs={"object": I("object_ref", "A standing tall object.")},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$object"), P("upright", object="$object")],
      ensures=[P("lying", object="$object")],
      invalidates=["upright($object)", "at_initial_place($object)"],
      paths=[Path("push_high", [W("object", "tall", "truthy")], [St("policy_082", "$object")])],
      relations=[R("sequence", "roll", "the lying cylinder is rolled", bind={"object": "$object"}),
                 R("sequence", "pick", "the lying object is pinched across its side", bind={"object": "$object"}),
                 R("alternative", "upright", "opposite effect")],
      distinct_from={"upright": "upright makes a lying object stand."})

skill("upright", "object", "Stand an object upright",
      "Make a lying object stand: pinch it, rotate its local up axis to vertical in the hand, and set it down "
      "upright on the same support.",
      group=G,
      inputs={"object": I("object_ref", "A lying object.")},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$object"), P("lying", object="$object")],
      ensures=[P("upright", object="$object"), P("hand_empty", hand="right")],
      invalidates=["lying($object)"],
      paths=[Path("pick_orient_place", [W("object", "grasp_types", "contains", "top_pinch")],
                  [St("policy_010", "$object"), St("policy_054", "$object", max_tilt_deg=15.0),
                   St("policy_015", "$object", "@object.support")],
                  ensures=[P("on", object="$object", support="@object.support")])],
      relations=[R("sequence", "pick", "the standing object is then grasped by its top", bind={"object": "$object"}),
                 R("alternative", "tip", "opposite effect")])

skill("wipe", "surface", "Wipe a surface",
      "Press a held sponge on a support and sweep a 30 cm strip twice; succeeds when the sponge stayed in contact "
      "over at least half of the strip.",
      group=G,
      inputs={"surface": I("support_ref", "The support to clean."),
              "tool": I("tool_ref", "The held wiping tool (sponge).")},
      outputs={"coverage": O("number", "Fraction of the strip wiped in contact.")},
      requires=[P("holding", hand="right", object="$tool"), P("base_near", place="$surface")],
      ensures=[P("wiped", support="$surface"), P("holding", hand="right", object="$tool")],
      paths=[Path("sponge_strip", [W("tool", "tags", "contains", "wiping_tool")], [St("policy_084", "$tool", "$surface")])],
      relations=[R("sequence", "place", "the sponge is put back", bind={"object": "$tool"}),
                 R("fallback", "clear", "objects cover the surface", bind={"support": "$surface"},
                   fallback_type="recover", reason="no free strip exists until the surface is cleared")])

skill("stir", "container", "Stir a container",
      "Dip a held spoon's far end into a container and move it in a circle below the rim; succeeds after one full "
      "turn inside.",
      group=G,
      inputs={"container": I("container_ref", "The pot or bowl to stir."),
              "tool": I("tool_ref", "The held utensil (spoon).")},
      outputs={"turns": O("number", "Measured turns of the tip inside the container.")},
      requires=[P("holding", hand="right", object="$tool"), P("base_near", place="$container"),
                P("uncovered", container="$container")],
      ensures=[P("stirred", container="$container"), P("holding", hand="right", object="$tool")],
      paths=[Path("circle_below_rim", [W("tool", "tags", "contains", "utensil")], [St("policy_085", "$tool", "$container")])],
      relations=[R("sequence", "cover", "the pot is covered again", bind={"container": "$container"}),
                 R("sequence", "heat", "the stirred food is heated", reason="stove path"),
                 R("fallback", "brace", "the container slides while stirring", bind={"object": "$container"},
                   fallback_type="recover", reason="the left hand holds the pot still")])

skill("pour", "contents", "Pour contents into a container",
      "Hold the cup's far lip over a container, turn the cup about that lip up to 90 deg and return it upright; "
      "succeeds when at least half of the loose items that were in the cup are inside the target. A rim-held cup "
      "tilts away from the pinch; a handle-held cup rolls sideways about the forearm.",
      group=G,
      inputs={"source": I("container_ref", "The held cup or mug with loose items."),
              "target": I("container_ref", "The receiving container.")},
      outputs={"moved": O("object_list", "Items now inside the target.")},
      requires=[P("holding", hand="right", object="$source"), P("base_near", place="$target"),
                P("uncovered", container="$target"), P("container_empty", negated=True, container="$source")],
      ensures=[P("poured_into", source="$source", target="$target"), P("holding", hand="right", object="$source")],
      paths=[Path("tilt_over_rim", [W("source", "is_container", "truthy")], [St("policy_086", "$source", "$target")])],
      relations=[R("sequence", "place", "the empty cup is put down", bind={"object": "$source"}),
                 R("sequence", "stir", "the poured food is stirred", bind={"container": "$target"}),
                 R("fallback", "uncover", "the target has its lid on", bind={"container": "$target"},
                   fallback_type="repair", repairs="uncovered"),
                 ])

# ================================================================= articulated & appliances
G = "articulated_and_appliance"

skill("open", "articulated", "Open a door or drawer",
      "Open a door, drawer, refrigerator door or microwave door to its annotated open value. The path follows the "
      "part: powered microwave (door button + hinge), refrigerator handle, drawer handle pull, hinged door "
      "side-hook ride, or a door opened by the right hand while the left hand holds a load.",
      group=G,
      inputs={"articulated": I("articulated_ref", "The door, drawer or appliance door.")},
      outputs={"joint": O("number", "Measured joint value.")},
      requires=[P("base_near", place="$articulated")],
      ensures=[P("is_open", articulated="$articulated")],
      invalidates=["is_closed($articulated)", "base_near(*)", "reachable(*)", "facing(*)"],
      paths=[
          Path("powered_microwave", [W("articulated", "powered", "truthy")], [St("policy_024", "$articulated")],
               requires=[P("hand_empty", hand="right")]),
          Path("left_holds_load", [W("robot", "left_held", "truthy"), W("articulated", "type", "equals", "revolute")],
               [St("policy_060", "@robot.left_object", "$articulated")],
               requires=[P("hand_empty", hand="right")]),
          Path("refrigerator", [W("articulated", "category", "equals", "refrigerator")],
               [St("policy_003"), St("policy_022", "$articulated", goal="@articulated.wide_open_q")],
               requires=[P("hand_empty", hand="right")],
               note="Rides the door to 75 % of its annotated range (60 deg), wide enough to put a can on the shelf."),
          Path("drawer", [W("articulated", "type", "equals", "prismatic")],
               [St("policy_003"), St("policy_046", "$articulated"), St("policy_050", "$articulated"),
                St("policy_047", "$articulated")],
               requires=[P("hand_empty", hand="right")]),
          Path("hinged_door", [W("articulated", "type", "equals", "revolute")],
               [St("policy_003"), St("policy_046", "$articulated"), St("policy_049", "$articulated"),
                St("policy_047", "$articulated")],
               requires=[P("hand_empty", hand="right")]),
      ],
      relations=[R("sequence", "pick", "an object inside must be taken out", reason="is_open is a cavity-pick precondition"),
                 R("sequence", "place", "an object must go inside", reason="is_open is a cavity-place precondition"),
                 R("sequence", "close", "the door must be shut afterwards", bind={"articulated": "$articulated"}),
                 R("fallback", "retreat", "the door swing hits the base", bind={"obstacle": "$articulated"},
                   fallback_type="recover", reason="room for the door's sweep"),
                 R("fallback", "handover", "the right hand still holds a load", fallback_type="repair",
                   repairs="hand_empty"),
                 R("fallback", "approach", "the handle is out of reach", bind={"target": "$articulated"},
                   fallback_type="recover", reason="a base pose with verified IK at the handle")],
      distinct_from={"press": "press only pushes a button; open guarantees the door is open."})

skill("close", "articulated", "Close a door or drawer",
      "Close a door, drawer or appliance door to within 0.10 rad / 4 cm of closed. A powered microwave door "
      "closes from its hinge-clearance pose, also while the robot carries a load.",
      group=G,
      inputs={"articulated": I("articulated_ref", "The open part.")},
      outputs={"joint": O("number", "Measured joint value.")},
      requires=[P("base_near", place="$articulated")],
      ensures=[P("is_closed", articulated="$articulated")],
      invalidates=["is_open($articulated)", "base_near(*)", "reachable(*)", "facing(*)"],
      paths=[
          Path("powered_loaded", [W("articulated", "powered", "truthy"), HELD_R],
               [St("policy_030", "$articulated"), St("policy_031", "$articulated", target="close")]),
          Path("powered", [W("articulated", "powered", "truthy")], [St("policy_025", "$articulated")]),
          Path("handle_push", [W("articulated", "has_handle", "truthy")], [St("policy_003"), St("policy_023", "$articulated")],
               requires=[P("hand_empty", hand="right")]),
          Path("dispatch", [], [St("policy_063", "$articulated")], requires=[P("hand_empty", hand="right")]),
      ],
      relations=[R("sequence", "heat", "a microwave or fridge must be closed before its cycle",
                   bind={"appliance": "$articulated"}),
                 R("sequence", "chill", "the fridge must be closed while cooling", bind={"appliance": "$articulated"}),
                 R("sequence", "navigate", "the robot leaves", reason="task done here"),
                 R("fallback", "retreat", "the door swing hits the base", bind={"obstacle": "$articulated"},
                   fallback_type="recover", reason="room for the door's sweep")])

skill("press", "button", "Press a button",
      "Press an annotated appliance button with the closed fingertips and retract: the microwave door key, the "
      "microwave start key, or the stove power key (which toggles the burner).",
      group=G,
      inputs={"button": I("button_ref", "E.g. kitchen_microwave/door_button, kitchen_stove/power_button.")},
      requires=[P("hand_empty", hand="right"), P("base_near", place="@button.appliance")],
      ensures=[P("button_pressed", button="$button"), P("hand_empty", hand="right")],
      invalidates=["arm_stowed(right)", "reachable(*)"],
      paths=[Path("microwave_start_staged", [W("button", "button", "equals", "start_button")],
                  [St("policy_027", "@button.appliance", button="start"),
                   St("policy_028", "@button.appliance", button="start"),
                   St("policy_029", "@button.appliance", button="start")],
                  requires=[P("is_closed", articulated="@button.appliance")],
                  ensures=[P("heating", appliance="@button.appliance")]),
             Path("microwave_door_key", [W("button", "button", "equals", "door_button")],
                  [St("policy_033", "@button.appliance", button="door")]),
             Path("generic_key", [], [St("policy_094", "$button")])],
      relations=[R("sequence", "heat", "the start key began a cycle", reason="heat then only waits"),
                 R("sequence", "tuck", "the hand is free again", bind={"hand": "right"}),
                 R("alternative", "open", "the door key is pressed only to open the microwave door")],
      distinct_from={"heat": "heat guarantees a temperature; press guarantees only the key press.",
                     "open": "open guarantees the door is open."})

skill("heat", "food", "Heat food",
      "Bring food to a target temperature with an appliance and switch the heat off: in the closed microwave "
      "(start key + wait) or in a pot on the stove burner (power key on, wait, power key off).",
      group=G,
      inputs={"food": I("object_ref", "The food item (has task-level thermal state)."),
              "appliance": I("appliance_ref", "kitchen_microwave or kitchen_stove."),
              "temp_c": I("number", "Target temperature in degC.", default=60.0)},
      outputs={"temp_c": O("number", "Measured final temperature.")},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$appliance")],
      ensures=[P("temperature_at_least", object="$food", temp_c="$temp_c"),
               P("heating", negated=True, appliance="$appliance")],
      paths=[
          Path("microwave", [W("appliance", "category", "equals", "microwave")],
               [St("policy_032", "$appliance"), St("policy_064", "$food", "$temp_c")],
               requires=[P("in_appliance", object="$food", appliance="$appliance"),
                         P("is_closed", articulated="$appliance")]),
          Path("stove_pot", [W("appliance", "category", "equals", "stove")],
               [St("policy_094", "@appliance.power_button", state=True),
                St("policy_090", "$food", "$temp_c", "$appliance")],
               requires=[P("in_cookware_on_burner", food="$food", appliance="$appliance")],
               note="Food must be inside a pot (or pan) whose bottom rests on the burner."),
      ],
      relations=[R("sequence", "open", "the heated food is taken out of the microwave",
                   bind={"articulated": "$appliance"}),
                 R("sequence", "pick", "the heated food is served", bind={"object": "$food"}),
                 R("alternative", "heat", "no microwave is available: heat in a pot on the stove",
                   bind={"food": "$food", "appliance": "kitchen_stove"},
                   reason="Same verb, other noun: the stove path pours/places the food into the pot first."),
                 R("fallback", "close", "the microwave door is open", bind={"articulated": "$appliance"},
                   fallback_type="repair", repairs="is_closed"),
                 R("fallback", "place", "the food is not in the appliance", bind={"object": "$food"},
                   fallback_type="repair", repairs="in_appliance"),
                 R("fallback", "wait", "the food is still below the target when the time budget ends",
                   fallback_type="recover", reason="keep the heat on longer, then re-check the temperature"),
                 R("fallback", "pour", "the food is in a cup, not in the pot on the burner", fallback_type="recover",
                   reason="pouring the cup into the pot on the burner puts the food in the heated vessel")],
      distinct_from={"chill": "opposite direction, in the refrigerator.", "press": "press does not wait."})

skill("chill", "food", "Chill food",
      "Keep food in the closed refrigerator until it is at or below a target temperature.",
      group=G,
      inputs={"food": I("object_ref", "The food item with thermal state."),
              "appliance": I("appliance_ref", "The refrigerator.", default="breakfast_fridge"),
              "temp_c": I("number", "Maximum temperature in degC.", default=8.0)},
      outputs={"temp_c": O("number", "Measured final temperature.")},
      requires=[P("in_appliance", object="$food", appliance="$appliance"), P("is_closed", articulated="$appliance")],
      ensures=[P("temperature_at_most", object="$food", temp_c="$temp_c")],
      paths=[Path("fridge_wait", [W("appliance", "category", "equals", "refrigerator")],
                  [St("policy_089", "$food", "$temp_c", "$appliance")])],
      relations=[R("sequence", "open", "the chilled food is taken out", bind={"articulated": "$appliance"}),
                 R("fallback", "close", "the fridge door is open", bind={"articulated": "$appliance"},
                   fallback_type="repair", repairs="is_closed")])

skill("cover", "container", "Cover a container with a lid",
      "Lay the held lid centred on the container rim (within 3 cm, tilt <= 12 deg) and release it.",
      group=G,
      inputs={"container": I("container_ref", "The pot or box to cover."),
              "lid": I("lid_ref", "The held lid.")},
      requires=[P("holding", hand="right", object="$lid"), P("base_near", place="$container"),
                P("uncovered", container="$container")],
      ensures=[P("covered", container="$container", lid="$lid"), P("hand_empty", hand="right")],
      invalidates=["uncovered($container)", "holding(right,$lid)"],
      paths=[Path("rim_plane", [W("lid", "is_lid", "truthy")], [St("policy_087", "$lid", "$container")])],
      relations=[R("sequence", "heat", "the covered pot is heated", reason="stove path"),
                 R("alternative", "uncover", "opposite effect")])

skill("uncover", "container", "Uncover a container",
      "Lift the lid off a container by its knob and set it down beside the container: on the same support when it "
      "has room, else on the nearest counter-height support; the lid noun is found from GT (the lid resting on the rim).",
      group=G,
      inputs={"container": I("container_ref", "The covered container.")},
      outputs={"lid": O("lid_ref", "The lid that was removed.")},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$container")],
      ensures=[P("uncovered", container="$container"), P("hand_empty", hand="right")],
      invalidates=["covered($container,*)"],
      paths=[Path("knob_lift_aside", [W("container", "lid", "truthy")],
                  [St("policy_010", "@container.lid"), St("policy_015", "@container.lid", "@container.aside_support")],
                  ensures=[P("on", object="@container.lid", support="@container.aside_support")])],
      relations=[R("sequence", "pour", "food is poured into the opened pot", bind={"target": "$container"}),
                 R("sequence", "stir", "the opened pot is stirred", bind={"container": "$container"}),
                 R("sequence", "pick", "something inside is taken out", reason="the opening is free"),
                 R("alternative", "cover", "opposite effect")])

# ================================================================= multi-step goals (contract chains of Skill Contracts)
G = "multi_object"

skill("fetch", "object", "Fetch an object to a receptacle",
      "Bring one object to a support or container: navigate to it, pick it (noun-selected grasp path), navigate to "
      "the receptacle and place it (noun-selected placement path). Each step is a verified Skill Contract.",
      group=G,
      inputs={"object": I("object_ref", "What to bring."),
              "receptacle": I("receptacle_ref", "Destination support or open container.")},
      requires=[P("hand_empty", hand="right")],
      ensures=[P("hand_empty", hand="right")],
      invalidates=["on($object,*)", "inside($object,*)", "at_initial_place($object)", "base_near(*)", "reachable(*)"],
      paths=[Path("to_container", [W("receptacle", "kind", "equals", "object")],
                  [Call("navigate", destination="$object"), Call("pick", object="$object"),
                   Call("navigate", destination="$receptacle"), Call("place", object="$object", receptacle="$receptacle")],
                  requires=[P("uncovered", container="$receptacle")],
                  ensures=[P("inside", object="$object", container="$receptacle")]),
             Path("to_surface", [W("receptacle", "kind", "equals", "support")],
                  [Call("navigate", destination="$object"), Call("pick", object="$object"),
                   Call("navigate", destination="$receptacle"), Call("place", object="$object", receptacle="$receptacle")],
                  ensures=[P("on", object="$object", support="$receptacle")])],
      relations=[R("sequence", "fetch", "more objects go to the same place", reason="the hand is free again"),
                 R("alternative", "restore", "the object should return to its starting support", bind={"object": "$object"}),
                 R("fallback", "search", "the object is not where expected", bind={"object": "$object"},
                   fallback_type="recover", reason="locates the object and reports its support")],
      distinct_from={"restore": "restore's destination is the object's starting support.",
                     "collect": "collect moves a list into one container."})

skill("collect", "objects", "Collect objects into a container",
      "Put every listed object into one container (fetch each in turn).",
      group=G,
      inputs={"objects": I("object_list", "Objects to gather."), "container": I("container_ref", "The container.")},
      requires=[P("hand_empty", hand="right"), P("uncovered", container="$container")],
      ensures=[P("all_inside", objects="$objects", container="$container")],
      paths=[Path("fetch_each", [], [ForEach("$objects", "item", Call("fetch", object="$item", receptacle="$container"))])],
      relations=[R("sequence", "close", "the container sits in a cabinet that must be closed", reason="closed: all goal"),
                 R("alternative", "sort", "the objects belong in different containers")])

skill("sort", "objects", "Sort objects by category",
      "Put each listed object into the container mapped to its category tag (e.g. fruit -> basket, toy -> toy box).",
      group=G,
      inputs={"objects": I("object_list", "Objects to sort."),
              "rule": I("category_map", "Tag -> destination mapping (a container or a support), e.g. {\"fruit\": \"fruit_basket\"}.")},
      requires=[P("hand_empty", hand="right")],
      ensures=[P("sorted_by_category", objects="$objects", rule="$rule")],
      paths=[Path("fetch_by_tag", [], [ForEach("$objects", "item",
                                               Call("fetch", object="$item", receptacle="@item.sort_target"))])],
      relations=[R("alternative", "collect", "all objects go into one container"),
                 R("sequence", "close", "a sorted container sits in a cabinet", reason="closed: all goal")])

skill("clear", "support", "Clear a support",
      "Remove every object from a support surface to a destination receptacle.",
      group=G,
      inputs={"support": I("support_ref", "The surface to clear."),
              "receptacle": I("receptacle_ref", "Where the objects go.")},
      outputs={"moved": O("object_list", "Objects that were removed.")},
      requires=[P("hand_empty", hand="right")],
      ensures=[P("support_clear", support="$support")],
      paths=[Path("fetch_each_on_support", [], [ForEach("@support.objects", "item",
                                                       Call("fetch", object="$item", receptacle="$receptacle"))])],
      relations=[R("sequence", "wipe", "the cleared surface is wiped", bind={"surface": "$support"}),
                 R("sequence", "arrange", "a new layout is set on the cleared surface", bind={"support": "$support"})])

skill("empty", "container", "Empty a container",
      "Take every object out of a container and put it on/into a destination receptacle.",
      group=G,
      inputs={"container": I("container_ref", "The container to empty."),
              "receptacle": I("receptacle_ref", "Where the contents go (a container for the pouring path).")},
      outputs={"moved": O("object_list", "Objects that were taken out.")},
      requires=[P("hand_empty", hand="right"), P("uncovered", container="$container")],
      ensures=[P("container_empty", container="$container")],
      paths=[Path("pour_out", [W("container", "grasp_types", "contains", "rim_pinch"), W("receptacle", "kind", "equals", "object")],
                  [Call("navigate", destination="$container"), Call("pick", object="$container"),
                   Call("navigate", destination="$receptacle"), Call("pour", source="$container", target="$receptacle"),
                   Call("place", object="$container", receptacle="@container.support")],
                  note="A cup or mug of loose items is emptied by pouring, then put back."),
             Path("pick_each_inside", [], [ForEach("@container.contents", "item",
                                                   St("policy_092", "$container"), St("policy_061", "$item"),
                                                   Call("navigate", destination="$receptacle"),
                                                   Call("place", object="$item", receptacle="$receptacle"))])],
      relations=[R("alternative", "clear", "the items lie on a surface instead"),
                 R("fallback", "uncover", "the container has its lid on", bind={"container": "$container"},
                   fallback_type="repair", repairs="uncovered")])

skill("arrange", "objects", "Arrange objects together",
      "Place the listed objects on one support so that they are pairwise within a distance (a place setting).",
      group=G,
      inputs={"objects": I("object_list", "Objects to group."), "support": I("support_ref", "The surface."),
              "max_dist_m": I("positive_number", "Pairwise distance limit.", default=0.5)},
      requires=[P("hand_empty", hand="right")],
      ensures=[P("grouped", objects="$objects", support="$support", max_dist_m="$max_dist_m")],
      paths=[Path("place_near_common_spot", [], [
          ForEach("$objects", "item", Call("navigate", destination="$item"), Call("pick", object="$item"),
                  Call("navigate", destination="$support"),
                  Call("place", object="$item", receptacle="$support", hint_xy="@support.roomiest_xy"))])],
      relations=[R("fallback", "clear", "the support is too crowded", bind={"support": "$support"},
                   fallback_type="recover", reason="frees room for the place setting")])

skill("restore", "object", "Restore an object to its place",
      "Return an object to the support it occupied at the start of the episode.",
      group=G,
      inputs={"object": I("object_ref", "The displaced object.")},
      requires=[P("hand_empty", hand="right"), P("at_initial_place", negated=True, object="$object")],
      ensures=[P("at_initial_place", object="$object"), P("hand_empty", hand="right")],
      paths=[Path("dispatch_pick_place", [W("object", "initial_support", "truthy")],
                  [St("policy_092", "$object"), St("policy_061", "$object"),
                   St("policy_092", "@object.initial_support"),
                   St("policy_015", "$object", "@object.initial_support")])],
      relations=[R("alternative", "fetch", "a different destination is wanted", bind={"object": "$object"}),
                 R("sequence", "tuck", "the robot drives on", bind={"hand": "right"})])

skill("swap", "objects", "Swap two objects",
      "Exchange the positions of two objects on their supports via a free buffer spot.",
      group=G,
      inputs={"a": I("object_ref", "First object."), "b": I("object_ref", "Second object.")},
      requires=[P("hand_empty", hand="right")],
      ensures=[P("positions_swapped", a="$a", b="$b"), P("hand_empty", hand="right")],
      paths=[Path("via_buffer", [], [
          Call("navigate", destination="$a"), Call("pick", object="$a"),
          Call("place", object="$a", receptacle="@a.support", hint_xy="@a.buffer_xy"),
          Call("navigate", destination="$b"), Call("pick", object="$b"), Call("navigate", destination="@a.support"),
          Call("place", object="$b", receptacle="@a.support", hint_xy="@a.xy"),
          Call("navigate", destination="$a"), Call("pick", object="$a"), Call("navigate", destination="@b.support"),
          Call("place", object="$a", receptacle="@b.support", hint_xy="@b.xy")])],
      relations=[R("alternative", "fetch", "only one object needs to move"),
                 R("sequence", "tuck", "the robot drives on", bind={"hand": "right"})])

# ================================================================= added verbs (to 70)
G = "base_and_body"

skill("sidestep", "base", "Sidestep the base",
      "Move the base sideways by a signed distance (left positive) without turning, also while carrying a load; "
      "aligns the arm with a target that is a little to the side.",
      group=G,
      inputs={"distance_m": I("number", "Lateral displacement in metres (left > 0).")},
      requires=[],
      ensures=[P("sidestepped", distance_m="$distance_m")],
      invalidates=["base_near(*)", "reachable(*)", "facing(*)", "in_view(*)"],
      paths=[Path("empty_tucked", [EMPTY_R, W("robot", "left_held", "falsy"), W("robot", "right_arm_stowed", "truthy")],
                  [St("policy_037", 0.0, "$distance_m")]),
             Path("loaded", [], [St("policy_114", "$distance_m")])],
      relations=[R("sequence", "approach", "the target is now in front of the arm", reason="small lateral offset fixed"),
                 R("alternative", "navigate", "a larger move is needed")],
      distinct_from={"retreat": "retreat moves straight back; sidestep moves sideways.",
                     "face": "face turns in place; sidestep keeps the heading."})

skill("wait", "duration", "Wait for a duration",
      "Do nothing for the given simulated time (an appliance cycle running, an object settling).",
      group=G,
      inputs={"seconds": I("positive_number", "How long to wait.", default=5.0)},
      requires=[],
      ensures=[P("waited", seconds="$seconds")],
      paths=[Path("idle", [], [St("policy_103", "$seconds")])],
      relations=[R("sequence", "open", "a cycle finished and the door is opened", reason="time passed")],
      distinct_from={"heat": "heat waits for a measured temperature; wait for a fixed time."})

G = "perception_and_gesture"

skill("identify", "object", "Identify an object",
      "Look at an object and report its category and tags (asset annotation) once it is in the head camera view.",
      group=G,
      inputs={"object": I("object_ref", "The object to identify.")},
      outputs={"category": O("tag", "Asset category."), "tags": O("object_list", "Annotated tags.")},
      requires=[],
      ensures=[P("identified", object="$object"), P("in_view", target="$object")],
      paths=[Path("look_and_label", [], [St("policy_110", "$object")])],
      relations=[R("sequence", "sort", "the category decides the destination", reason="category output"),
                 R("alternative", "measure", "the size, not the category, is needed", bind={"object": "$object"}),
                 R("fallback", "navigate", "the object is not visible from here", bind={"destination": "$object"},
                   fallback_type="recover", reason="a closer view")],
      distinct_from={"look": "look only aims the camera.", "measure": "measure reports dimensions."})

skill("measure", "object", "Measure an object",
      "Look at an object and report its current axis-aligned size.",
      group=G,
      inputs={"object": I("object_ref", "The object to measure.")},
      outputs={"size_m": O("xy", "World-frame size [dx, dy, dz] in metres.")},
      requires=[],
      ensures=[P("measured", object="$object"), P("in_view", target="$object")],
      paths=[Path("look_and_size", [], [St("policy_111", "$object")])],
      relations=[R("sequence", "pick", "the size decides the grasp", reason="width vs gripper opening"),
                 R("alternative", "identify", "the category is needed", bind={"object": "$object"})])

skill("count", "category", "Count objects of a category",
      "Sweep the head from the current place and count the visible objects whose asset or tag matches.",
      group=G,
      inputs={"category": I("tag", "Asset name or tag, e.g. \"cherry_tomato\", \"fruit\".")},
      outputs={"count": O("number", "Number of visible matches."), "objects": O("object_list", "The matches.")},
      requires=[],
      ensures=[P("counted", category="$category")],
      paths=[Path("head_sweep", [], [St("policy_112", "$category")])],
      relations=[R("sequence", "collect", "the counted objects are gathered", reason="objects output"),
                 R("fallback", "explore", "objects of the category may be out of view", fallback_type="recover",
                   reason="room coverage")])

skill("wave", "hand", "Wave the hand",
      "Raise the empty right hand at head height and swing it (greeting / attention gesture).",
      group=G, inputs={},
      requires=[P("hand_empty", hand="right")],
      ensures=[P("waved"), P("hand_empty", hand="right")],
      paths=[Path("raised_swing", [], [St("policy_104")])],
      relations=[R("sequence", "point", "the robot then indicates something", reason="gesture sequence"),
                 R("alternative", "nod", "an acknowledgement without the arm")])

skill("nod", "head", "Nod the head",
      "Pitch the head down and up twice (acknowledgement gesture).",
      group=G, inputs={}, requires=[], ensures=[P("nodded")],
      invalidates=["in_view(*)"],
      paths=[Path("pitch_cycles", [], [St("policy_105")])],
      relations=[R("sequence", "look", "the robot looks back at a target", reason="restores gaze"),
                 R("alternative", "wave", "a bigger gesture is needed")])

G = "grasp_and_hand"

skill("shake", "object", "Shake a held object",
      "Oscillate the held object sideways three times (settle or loosen contents) while keeping the grasp.",
      group=G,
      inputs={"object": I("object_ref", "The right-held object.")},
      requires=[P("holding", hand="right", object="$object")],
      ensures=[P("shaken", object="$object"), P("holding", hand="right", object="$object")],
      paths=[Path("lateral", [], [St("policy_102", "$object")])],
      relations=[R("sequence", "pour", "loose contents are poured out", bind={"source": "$object"}),
                 R("alternative", "rotate", "the orientation, not the contents, matters", bind={"object": "$object"})])

skill("hover", "object", "Hover a held object over a target",
      "Hold the carried object centred 6 cm above a target (a container opening, a spot on a surface) without "
      "releasing it, e.g. to show or to align before a drop.",
      group=G,
      inputs={"object": I("object_ref", "The right-held object."), "target": I("entity_ref", "What to hover over.")},
      requires=[P("holding", hand="right", object="$object"), P("base_near", place="$target")],
      ensures=[P("hovering_over", object="$object", target="$target"), P("holding", hand="right", object="$object")],
      paths=[Path("above_target", [], [St("policy_115", "$object", "$target")])],
      relations=[R("sequence", "drop", "the object is released into the container under it",
                   bind={"object": "$object", "container": "$target"}),
                 R("sequence", "release", "the object is let go right there", bind={"object": "$object"}),
                 R("alternative", "lift", "only a height matters", bind={"object": "$object"})],
      distinct_from={"drop": "hover keeps the grasp.", "lift": "lift has no target point."})

skill("square", "object", "Square an object",
      "Align an object's edges with its support's edges (yaw within 5 deg): pick it, turn it by the measured yaw "
      "error and set it back down at the same spot.",
      group=G,
      inputs={"object": I("object_ref", "An object resting on a support.")},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$object")],
      ensures=[P("squared", object="$object"), P("hand_empty", hand="right")],
      paths=[Path("pick_rotate_place", [W("object", "grasp_types", "contains", "top_pinch")],
                  [St("policy_108", "$object", out="sq"), St("policy_010", "$object"),
                   St("policy_075", "$object", "#sq.degrees"),
                   St("policy_015", "$object", "@object.support", hint="#sq.xy")])],
      relations=[R("sequence", "stack", "squared blocks stack cleanly", reason="aligned faces"),
                 R("alternative", "rotate", "the object is already in the hand", bind={"object": "$object"})],
      distinct_from={"rotate": "rotate turns a held object by a requested angle; square finds the angle itself."})

G = "contact"

skill("touch", "object", "Touch an object",
      "Bring the closed fingertips onto an object's top and back off without moving it (probe / indicate by "
      "contact).",
      group=G,
      inputs={"object": I("object_ref", "The object to touch.")},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$object")],
      ensures=[P("touched", object="$object"), P("hand_empty", hand="right")],
      paths=[Path("fingertip_top", [], [St("policy_107", "$object")])],
      relations=[R("sequence", "pick", "the touched object is then grasped", bind={"object": "$object"}),
                 R("alternative", "point", "contact is not allowed", bind={"target": "$object"})],
      distinct_from={"push": "push moves the object; touch must not.", "press": "press actuates a button."})

skill("knock", "articulated", "Knock on a door",
      "Tap a closed door or drawer panel twice with the closed fingertips beside its handle; the panel must stay "
      "closed.",
      group=G,
      inputs={"articulated": I("articulated_ref", "The closed door or drawer.")},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$articulated"), P("is_closed", articulated="$articulated")],
      ensures=[P("knocked", articulated="$articulated"), P("is_closed", articulated="$articulated")],
      paths=[Path("panel_taps", [W("articulated", "has_handle", "truthy")], [St("policy_106", "$articulated")])],
      relations=[R("sequence", "open", "the door is opened after knocking", bind={"articulated": "$articulated"}),
                 R("alternative", "touch", "an object, not a door, is to be tapped")],
      distinct_from={"open": "knock must leave the door closed."})

skill("sweep", "objects", "Sweep objects together",
      "Push several objects on one support toward their centroid until they form a cluster (radius 12 cm), "
      "without grasping them.",
      group=G,
      inputs={"objects": I("object_list", "Objects on one support."),
              "radius_m": I("positive_number", "Cluster radius.", default=0.12)},
      requires=[P("hand_empty", hand="right")],
      ensures=[P("clustered", objects="$objects", radius_m="$radius_m")],
      paths=[Path("push_to_centroid", [], [St("policy_109", "$objects", radius_m="$radius_m")])],
      relations=[R("sequence", "collect", "the cluster is then put into a container", reason="short reaches"),
                 R("alternative", "push", "only one object has to move", reason="single push")],
      distinct_from={"arrange": "arrange picks and places; sweep only pushes.",
                     "collect": "collect puts objects into a container."})

G = "articulated_and_appliance"

skill("stop", "appliance", "Stop an appliance",
      "Switch an appliance's heat off: press the stove power key off, or open the microwave door, which ends its "
      "cycle.",
      group=G,
      inputs={"appliance": I("appliance_ref", "kitchen_stove or kitchen_microwave.")},
      requires=[P("hand_empty", hand="right"), P("base_near", place="$appliance")],
      ensures=[P("heating", negated=True, appliance="$appliance")],
      paths=[Path("stove_key_off", [W("appliance", "category", "equals", "stove")],
                  [St("policy_094", "@appliance.power_button", state=False)]),
             Path("microwave_door", [W("appliance", "category", "equals", "microwave")],
                  [St("policy_024", "$appliance")],
                  ensures=[P("is_open", articulated="$appliance")])],
      relations=[R("sequence", "pick", "the food is taken off the heat", reason="heat is off"),
                 R("alternative", "heat", "heat stops automatically at a target temperature")],
      distinct_from={"press": "press does not guarantee the heat is off.", "close": "close does not stop a stove."})

G = "contact"

skill("dip", "utensil", "Dip a utensil",
      "Lower a held spoon's far end into a container below its rim, hold it there and lift it out.",
      group=G,
      inputs={"tool": I("tool_ref", "The held utensil."), "container": I("container_ref", "The pot or bowl.")},
      requires=[P("holding", hand="right", object="$tool"), P("base_near", place="$container"),
                P("uncovered", container="$container")],
      ensures=[P("dipped", container="$container"), P("holding", hand="right", object="$tool")],
      paths=[Path("tip_below_rim", [W("tool", "tags", "contains", "utensil")], [St("policy_113", "$tool", "$container")])],
      relations=[R("sequence", "stir", "the utensil then stirs", bind={"tool": "$tool", "container": "$container"}),
                 R("alternative", "stir", "the contents must be mixed", bind={"tool": "$tool", "container": "$container"})],
      distinct_from={"stir": "stir circles inside the container; dip goes in and out once."})

G = "multi_object"

skill("hide", "object", "Hide an object",
      "Make an object invisible from outside: put it into a container and cover that container with its lid, "
      "or put it on a shelf inside a cabinet and close the cabinet.",
      group=G,
      inputs={"object": I("object_ref", "The object to hide."),
              "receptacle": I("receptacle_ref", "A lidded container or a cabinet interior shelf."),
              "lid": I("lid_ref", "The lid to use for a container.", required=False)},
      requires=[P("hand_empty", hand="right")],
      ensures=[P("hidden", object="$object"), P("hand_empty", hand="right")],
      paths=[Path("container_with_lid", [W("receptacle", "kind", "equals", "object"), W("args", "lid", "truthy")],
                  [Call("fetch", object="$object", receptacle="$receptacle"), Call("navigate", destination="$lid"),
                   Call("pick", object="$lid"), Call("navigate", destination="$receptacle"),
                   Call("cover", container="$receptacle", lid="$lid")],
                  requires=[P("uncovered", container="$receptacle")]),
             Path("closed_cabinet", [W("receptacle", "kind", "equals", "support"),
                                     W("receptacle", "category", "equals", "cabinet_inside")],
                  [Call("navigate", destination="@receptacle.appliance"), Call("open", articulated="@receptacle.appliance"),
                   Call("fetch", object="$object", receptacle="$receptacle"),
                   Call("close", articulated="@receptacle.appliance")])],
      relations=[R("alternative", "fetch", "the object only needs to move", bind={"object": "$object"}),
                 R("sequence", "tuck", "the robot leaves", bind={"hand": "right"})])


# ================================================================ planner hints
# When-to-use text for the upper layer (fills nodes that did not set one) and
# the verbs each node is most easily confused with.
USE_WHEN = {
    "navigate": "The robot must be in another room or next to another piece of furniture.",
    "approach": "Right before a contact action on one specific target.",
    "face": "The target is beside or behind the robot and only the heading must change.",
    "retreat": "The base is too close to open a door, turn, or start a path.",
    "crouch": "The next target is low (floor, low shelf) or the head must look under something.",
    "stand": "After a crouch, before driving or reaching high.",
    "bend": "A target is just beyond arm reach over a counter and leaning forward helps.",
    "straighten": "After a bend, before driving or carrying.",
    "tuck": "Before driving through a narrow passage or after a hand action left the arm out.",
    "reset": "Start or end of a task, or after a failure, to return to a known posture.",
    "sidestep": "The robot must shift sideways a few centimetres without turning (align with a target).",
    "wait": "Something must happen over time (cooling, settling) and the robot should not act.",
    "look": "A known target must be brought into the head camera view.",
    "inspect": "The contents of a container or cabinet must be seen (opens it if needed).",
    "search": "The location of an object is unknown in the current room.",
    "explore": "A room must be surveyed before planning (unknown layout or objects).",
    "point": "A person must be shown an object or place without touching it.",
    "present": "A held object must be shown to the head camera or a person.",
    "identify": "The category or identity of a visible object must be confirmed.",
    "measure": "The size or distance of an object must be known before choosing a grasp or place.",
    "count": "The number of objects of one category in view must be known.",
    "wave": "Greeting or getting attention.",
    "nod": "Acknowledging an instruction.",
    "pick": "The robot must hold an object for any later hand action.",
    "place": "A held object must end up resting on a support, in a container or on a burner.",
    "drop": "A held object must go into an open container from above without a precise pose.",
    "stack": "A held object must be put on top of another object.",
    "release": "The hand must open in place (the object is already supported).",
    "handover": "The right hand must be freed while the object stays held (by the left hand).",
    "lift": "A held object must be raised to a height (clear an obstacle, show it).",
    "lower": "A held object must be brought down to a height without releasing it.",
    "rotate": "A held object must turn about the vertical axis (align a handle or label).",
    "regrasp": "The current grasp is unsuitable (wrong end, slipping) and the object can be set down.",
    "brace": "An object must be held still by the left hand while the right hand works on it.",
    "flip": "A flat object must be turned upside down.",
    "shake": "The grasp must be tested or contents shaken while holding.",
    "hover": "A held object must be positioned over a target before dropping or pouring.",
    "square": "An object must be rotated so its sides align with the support edges.",
    "push": "An object must slide along its support without grasping it.",
    "pull": "An object is too far back on a deep support to grasp and must come closer.",
    "expose": "A flat object is wider than the gripper and must overhang an edge before pick.",
    "separate": "Two objects are too close for the fingers to fit beside one of them.",
    "center": "An object near a support edge must be moved inward so it cannot fall.",
    "roll": "A lying cylinder must move along the support by rotating.",
    "tip": "An upright object must be laid on its side.",
    "upright": "A lying object must stand on its base again.",
    "wipe": "A surface must be wiped with a held sponge or cloth.",
    "stir": "The contents of a container must be stirred with a held utensil.",
    "pour": "Loose contents of a held container must go into another container.",
    "touch": "An object must be touched lightly (tap, confirm contact) without moving it.",
    "knock": "A closed door must be knocked on (check, signal) without opening it.",
    "sweep": "Several small objects on one support must be gathered into a cluster.",
    "dip": "A held utensil must go into a container briefly (taste, wet).",
    "open": "A door, drawer or appliance must be opened before reaching inside.",
    "close": "A door, drawer or appliance must be closed (before heating, after taking out).",
    "press": "A button (microwave keys, stove power key) must be pressed.",
    "heat": "Food must reach a target temperature with the microwave or the stove.",
    "chill": "Food or a drink must cool in the refrigerator.",
    "cover": "A container must be closed with its lid.",
    "uncover": "A lid must be removed before reaching into or pouring into a container.",
    "stop": "An appliance that is heating must be switched off.",
    "fetch": "One object must be brought to a destination (navigate, pick, carry, place in one node).",
    "collect": "Several objects must go into one container.",
    "sort": "Objects must go to destinations by category.",
    "clear": "Every object must be removed from one support.",
    "empty": "A container must be emptied into another container or onto a surface.",
    "arrange": "Several objects must be grouped together on one support (a setting).",
    "restore": "An object must return to where it was at the start.",
    "swap": "Two objects must exchange places.",
    "hide": "An object must end up out of sight inside a closed container.",
}

DISTINCT = {
    "navigate": {"approach": "approach goes to a contact pose for one target; navigate only reaches its vicinity."},
    "crouch": {"bend": "bend tilts the waist forward; crouch lowers the torso."},
    "stand": {"straighten": "straighten undoes a waist bend; stand raises the torso."},
    "tuck": {"reset": "reset also restores torso, waist and head; tuck only folds the arm."},
    "look": {"search": "search scans for an unknown location; look turns to a known target."},
    "search": {"explore": "explore surveys a whole room; search stops when the object is found."},
    "inspect": {"look": "inspect also opens a closed receptacle to see inside."},
    "point": {"touch": "point does not make contact."},
    "identify": {"measure": "measure returns sizes and distances, identify returns the category."},
    "count": {"identify": "count returns a number for one category."},
    "drop": {"place": "place sets the object down at a measured pose; drop releases above an opening."},
    "release": {"place": "place moves to a pose first; release only opens the hand."},
    "lift": {"pick": "lift raises an object already held."},
    "lower": {"place": "lower keeps holding the object."},
    "regrasp": {"rotate": "rotate keeps the grasp; regrasp sets the object down and grasps again."},
    "brace": {"pick": "brace leaves the object on its support."},
    "shake": {"stir": "stir moves a utensil inside a container; shake moves the held object itself."},
    "hover": {"drop": "hover keeps holding the object."},
    "square": {"rotate": "square sets the object down aligned with the support edges."},
    "push": {"pull": "pull moves the object toward the robot.", "sweep": "sweep gathers several objects."},
    "separate": {"push": "separate pushes until a finger fits beside the object."},
    "center": {"push": "center moves the object away from the nearest edge by a margin."},
    "upright": {"tip": "opposite direction."},
    "dip": {"stir": "dip does not circle the utensil."},
    "close": {"open": "opposite direction."},
    "cover": {"uncover": "opposite direction.", "place": "cover rests the lid on the rim."},
    "uncover": {"pick": "uncover also puts the lid aside."},
    "stop": {"press": "stop leaves the appliance off whatever its state."},
    "fetch": {"pick": "fetch also carries and places the object."},
    "collect": {"fetch": "collect repeats fetch into one container."},
    "sort": {"collect": "sort chooses a destination per category."},
    "clear": {"collect": "clear is defined by the source support, not by a list of objects."},
    "empty": {"pour": "empty may also pick items out one by one."},
    "arrange": {"sweep": "arrange picks and places; sweep pushes."},
    "restore": {"fetch": "restore's destination is the object's initial support."},
    "swap": {"restore": "swap exchanges two objects."},
    "hide": {"collect": "hide also covers the container."},
    "wipe": {"sweep": "wipe uses a held tool on the surface itself."},
    "bend": {"crouch": "crouch lowers the torso; bend tilts the waist."},
    "straighten": {"stand": "stand raises the torso; straighten undoes a waist bend."},
    "explore": {"search": "search looks for one object and stops when found."},
    "present": {"lift": "lift only changes the height; present holds the object in front of the head."},
    "stack": {"place": "place targets a support or container; stack targets the top face of an object."},
    "handover": {"release": "release lets the object go; handover keeps it held by the left hand."},
    "flip": {"rotate": "rotate turns about the vertical axis; flip turns the object upside down."},
    "pull": {"push": "push moves the object away from the robot or sideways."},
    "expose": {"push": "expose pushes toward a free edge until a pinchable overhang exists."},
    "roll": {"push": "push slides the object; roll makes it rotate."},
    "stir": {"dip": "dip goes in and out without circling."},
    "pour": {"drop": "drop releases the held object itself; pour tips out its contents."},
    "chill": {"heat": "opposite direction, with the microwave or stove."},
    "measure": {"identify": "identify returns the category, measure the size and distance."},
    "wave": {"point": "point indicates a target; wave is a greeting."},
    "nod": {"wave": "wave uses the arm; nod uses the head."},
}

for _s in SKILLS:
    if not _s["use_when"]:
        _s["use_when"] = USE_WHEN.get(_s["verb"], "")
    for _k, _v in DISTINCT.get(_s["verb"], {}).items():
        _s["distinct_from"].setdefault(_k, _v)
