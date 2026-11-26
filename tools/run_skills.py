"""Run a sequence of annotation-driven Zeno skills in any scene and record it.

    cd zeno-house   # repository root
    OMNI_KIT_ACCEPT_EULA=YES ${ISAACLAB_PYTHON:-python} tools/run_skills.py \
        --scene sim/zeno_house.usd --ann annotations/zeno_house.json --out runs/demo \
        --plan "open kitchen_cabinet_6" \
               "close kitchen_cabinet_6"

Retired policies (skill_library/check.py RETIRED_POLICIES: the Right* primitives, the handle grasp / release steps,
the microwave's staged press and cavity policies, prepare_floor_reach, pick_from_cavity, reach_while_moving ...) are
no plan steps here: their policies raise, naming what replaced them.

Plan steps:  open <art> | close <art> | pick <obj>
             | pick_top/pick_round_rim/pick_rect_rim/pick_edge <obj>
             | place <obj> in:<container>          drop into a container
             | place <obj> <support> [<x> <y>]      free spot on a support (near x, y)
             | place_surface/place_edge <obj> <support> | place_container <obj> <container>
             | push <obj> <dx> <dy>                 slide along its support (world m)
             | goto/carry_to/empty_goto <x> <y> <yaw_deg>
             | pick_and_carry <obj> <x> <y> <yaw_deg>  sequential composite
             | tuck_arm | lower_torso [height_m] | raise_torso [height_m]
             | lean_forward [pitch_rad] | straighten_waist | click <art> <door|start>
             | carry_height_adjust [min_bottom_z_m] | back_off_with_load [distance_m]
             | push_from_behind/top_drag <obj> <dx> <dy>  displacement vector in world frame
             | base_rotate_in_place <delta_yaw_deg> | base_translate_local <forward_m> [left_m]
             | microwave_door_clear <art> | microwave_hinge_drive <art> <open|close>
             | slide_to_edge <obj>
             | open_revolute_door/open_prismatic_drawer <art>
             | open_handle/close_handle/open_powered/close_powered <art>
             | microwave_start <art>
             | bimanual_flat_pick/bimanual_box_lift <obj>
             | bimanual_carry <obj> <x> <y> <yaw> | handover_right_to_left <obj>
             | open_door_while_left_holds <obj> <door> | upright_object <held_obj>
             | tilt_held <held_obj> <roll_deg>  physical test fixture: tip a held object
             | pick_cup_handle <mug> | pick_while_moving <obj> <base_x> <base_y> <base_yaw_deg>
             | place_while_moving <obj> <support> <base_x> <base_y> <base_yaw_deg> [<place_x> <place_y>]
Supports may be aliases from task_specs/places.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--ann", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--plan", nargs="+", required=True)
    ap.add_argument("--res", nargs=2, type=int, default=[720, 1280])
    ap.add_argument("--stride", type=int, default=8)
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--start-base", nargs=3, type=float, metavar=("X", "Y", "YAW_DEG"),
                    help="optional robot base start pose for a local policy smoke run")
    args = ap.parse_args()
    out = ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)

    from zeno_skills.runtime import launch
    app = launch(not args.no_video)
    import numpy as np
    from zeno_skills.policies import PolicySuite
    from zeno_skills.interface_ids import resolve_policy_id
    from zeno_skills.rig import SkillFailure
    from zeno_skills.runtime import make_rig
    from zeno_skills.tasks import load_places, resolve_place

    places = load_places()
    report = {"scene": args.scene, "plan": args.plan, "steps": [], "success": False,
              "written_state": "robot drive targets and base anchor only"}
    rig = None
    try:
        handle_objects = {raw.split()[1] for raw in args.plan
                          if resolve_policy_id(raw.split()[0]) == "pick_cup_handle"
                          and len(raw.split()) > 1}
        rig = make_rig(app, args.scene, args.ann, video=not args.no_video,
                       res=args.res, stride=args.stride, handle_objects=handle_objects)
        task_path = (ROOT / args.scene).parent / "task.json"
        if task_path.is_file():
            rig.configure_thermal(json.loads(task_path.read_text()))
        rig.caption = "start"
        if args.start_base is not None:
            rig.set_base(*args.start_base)
        rig.step(60)
        startup = np.r_[rig.q(), rig.fingers(), rig.base_pose()]
        if not np.isfinite(startup).all():
            raise SkillFailure("initial robot state is nonfinite; the --start-base pose may intersect physical geometry")
        policies = PolicySuite(rig)
        for raw in args.plan:
            tok = raw.split()
            tok[0] = resolve_policy_id(tok[0])
            t0 = time.time()
            row = {"step": raw}
            report["steps"].append(row)
            if tok[0] == "open":
                row["result_q"] = policies.open.execute(tok[1])
            elif tok[0] == "close":
                row["result_q"] = policies.close.execute(tok[1])
            elif tok[0] in ("open_handle", "close_handle", "open_powered", "close_powered"):
                row["result_q"] = getattr(policies, tok[0]).execute(tok[1])
            elif tok[0] == "microwave_start":
                row["heating_active"] = bool(policies.microwave_start.execute(tok[1]))
            elif tok[0] == "pick":
                policies.pick.execute(tok[1])
            elif tok[0] in ("pick_top", "pick_round_rim", "pick_rect_rim", "pick_edge"):
                getattr(policies, tok[0]).execute(tok[1])
            elif tok[0] == "slide_to_edge":
                row["edge"] = policies.slide_to_edge.execute(tok[1])
            elif tok[0] in ("open_revolute_door", "open_prismatic_drawer"):
                row["result_q"] = getattr(policies, tok[0]).execute(tok[1])
            elif tok[0] == "pick_cup_handle":
                row["lift_m"] = policies.pick_cup_handle.execute(tok[1])
            elif tok[0] == "pick_while_moving":
                row["lift_m"] = policies.pick_while_moving.execute(
                    tok[1], tuple(float(v) for v in tok[2:5]))
            elif tok[0] == "place_while_moving":
                row["object_pose"] = policies.place_while_moving.execute(
                    tok[1], resolve_place(tok[2], places),
                    tuple(float(v) for v in tok[3:6]),
                    xy=(float(tok[6]), float(tok[7])) if len(tok) >= 8 else None)
            elif tok[0] in ("bimanual_flat_pick", "bimanual_box_lift", "handover_right_to_left"):
                row["lift_m"] = getattr(policies, tok[0]).execute(tok[1])
            elif tok[0] == "tilt_held":
                if rig.held is None or rig.held["name"] != tok[1]:
                    raise SkillFailure(f"tilt fixture: right hand is not holding {tok[1]}")
                from scipy.spatial.transform import Rotation
                from zeno_skills.clearance import unchecked
                from zeno_skills.evaluator import tilt_deg
                p, R = rig.kin.tcp(rig.q())
                tipped = R @ Rotation.from_euler("x", float(tok[2]), degrees=True).as_matrix()
                rig.move_to(p, tipped, step=0.008, steps_per_wp=5,
                            label="tilt_held_fixture", allow=unchecked("test fixture: tips the held object in place"))
                rig.step(60)
                _, quat = rig.obj_pose(tok[1])
                row["tilt_deg"] = float(tilt_deg(quat))
                if row["tilt_deg"] <= 15.0:
                    raise SkillFailure(f"tilt fixture: object only tilted {row['tilt_deg']:.1f} degrees")
            elif tok[0] == "upright_object":
                row["tilt_deg"] = policies.upright_object.execute(tok[1])
            elif tok[0] == "bimanual_carry":
                row["base_pose"] = policies.bimanual_carry.execute(
                    tok[1], (float(tok[2]), float(tok[3]), float(tok[4])))
            elif tok[0] == "open_door_while_left_holds":
                row["result_q"] = policies.open_door_while_left_holds.execute(tok[1], tok[2])
            elif tok[0] == "pick_and_carry":
                policies.pick_and_carry.execute(tok[1], (float(tok[2]), float(tok[3]), float(tok[4])))
            elif tok[0] in ("place_surface", "place_edge"):
                getattr(policies, tok[0]).execute(tok[1], resolve_place(tok[2], places))
            elif tok[0] == "place_container":
                policies.place_container.execute(tok[1], tok[2])
            elif tok[0] == "place" and tok[2].startswith("in:"):
                policies.place.execute(tok[1], tok[2])
            elif tok[0] == "place":
                hint = (float(tok[3]), float(tok[4])) if len(tok) >= 5 else None
                policies.place.on(tok[1], resolve_place(tok[2], places), hint=hint)
            elif tok[0] in ("push", "push_from_behind", "top_drag"):
                d = np.array([float(tok[2]), float(tok[3])])
                if np.linalg.norm(d) <= 0:
                    raise ValueError("push/drag displacement must be nonzero")
                sup = rig.geo.support_under(tok[1], rig.state())
                if sup is None:
                    raise SkillFailure(f"push {tok[1]}: not on an annotated support")
                row["moved_m"] = getattr(policies, tok[0]).execute(
                    tok[1], sup, d / np.linalg.norm(d), float(np.linalg.norm(d)))
            elif tok[0] == "goto":
                policies.navigate.execute((float(tok[1]), float(tok[2]), float(tok[3])))
            elif tok[0] in ("carry_to", "empty_goto"):
                getattr(policies, "carry_navigate" if tok[0] == "carry_to" else "empty_navigate").execute(
                    (float(tok[1]), float(tok[2]), float(tok[3])))
            elif tok[0] == "carry_height_adjust":
                row["object_bottom_z_m"] = policies.carry_height_adjust.execute(
                    float(tok[1]) if len(tok) > 1 else 0.55)
            elif tok[0] == "back_off_with_load":
                row["reversed_m"] = policies.back_off_with_load.execute(
                    float(tok[1]) if len(tok) > 1 else 0.35)
            elif tok[0] == "base_rotate_in_place":
                row["yaw_deg"] = policies.base_rotate_in_place.execute(float(tok[1]))
            elif tok[0] == "base_translate_local":
                row["base_pose"] = policies.base_translate_local.execute(
                    float(tok[1]), float(tok[2]) if len(tok) > 2 else 0.0)
            elif tok[0] == "tuck_arm":
                policies.tuck_arm.execute()
            elif tok[0] in ("lower_torso", "raise_torso"):
                row["torso_height_m"] = getattr(policies, tok[0]).execute(float(tok[1]) if len(tok) > 1 else None)
            elif tok[0] == "lean_forward":
                row["waist_pitch_rad"] = policies.lean_forward.execute(float(tok[1]) if len(tok) > 1 else None)
            elif tok[0] == "straighten_waist":
                row["waist_pitch_rad"] = policies.straighten_waist.execute()
            elif tok[0] == "click":
                policies.click.execute(tok[1], button=tok[2])
            elif tok[0] == "microwave_door_clear":
                row["base_pose"] = policies.microwave_door_clear.execute(tok[1])
            elif tok[0] == "microwave_hinge_drive":
                row["result_q"] = policies.microwave_hinge_drive.execute(tok[1], target=tok[2])
            else:
                raise ValueError(raw)
            row["success"] = True
            row["wall_s"] = round(time.time() - t0, 1)
        rig.caption = "done"
        rig.step(60)
        report["success"] = True
    except Exception as exc:
        report["failure"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
        print("FAIL", report["failure"], flush=True)
    finally:
        if rig is not None:
            report["events"] = rig.events
            if rig.thermal is not None:
                report["thermal_active"] = rig.thermal.active
                report["temperatures_c"] = rig.thermal.temperatures_c
            if not args.no_video:
                report["video"] = str(rig.write_video(out / "run.mp4"))
        (out / "result.json").write_text(json.dumps(report, indent=1, default=float))
        print("RESULT", out / "result.json", "SUCCESS", report["success"], flush=True)
        sys.stdout.flush()
        os._exit(0 if report["success"] else 3)


if __name__ == "__main__":
    main()
