"""Stand-in for env_service.worker without a simulator: speaks the same pipe protocol.

``pick`` of an object named ``fail_*`` fails; task ``crash_task`` exits after ready;
``bad_start`` reports a start error; ``slow_start`` takes 3 s to become ready;
the ``slow`` contract takes 2 s.
"""
import argparse
import json
import os
import time

ap = argparse.ArgumentParser()
ap.add_argument("--task-id")
ap.add_argument("--cmd-fd", type=int)
ap.add_argument("--resp-fd", type=int)
ap.add_argument("--wrist-cameras", action="store_true")
args = ap.parse_args()
cmd, resp = os.fdopen(args.cmd_fd), os.fdopen(args.resp_fd, "w")
held = None


def send(msg):
    resp.write(json.dumps(msg) + "\n")
    resp.flush()


def observation():
    return {"images": [{"camera": "head", "png_base64": ""}], "objects": [], "robot": {"held_right": held},
            "task_status": [{"atom": "holding(right, apple)", "holds": held == "apple"}]}


if args.task_id == "bad_start":
    send({"type": "error", "error": "scene failed to load"})
    os._exit(1)
if args.task_id == "slow_start":
    time.sleep(3)
send({"type": "ready", "observation": observation()})
if args.task_id == "crash_task":
    os._exit(1)
for line in cmd:
    req = json.loads(line)
    if req["op"] == "contract":
        call = req["call"]
        if call["contract"] == "slow":
            time.sleep(2)
        obj = call.get("args", {}).get("object", "")
        ok = not obj.startswith("fail_")
        if ok and call["contract"] == "pick":
            held = obj
        send({"result": {"contract": call["contract"], "args": call.get("args", {}), "success": ok,
                         "error_code": None if ok else "PRECONDITION_FAILED", "error": None,
                         "preconditions": [], "postconditions": [], "outputs": {}}})
    elif req["op"] == "observe":
        send({"observation": observation()})
    elif req["op"] == "check":
        send({"success": held == "apple", "goal": [{"atom": "holding(right, apple)", "holds": held == "apple"}]})
    elif req["op"] == "close":
        break
os._exit(0)
