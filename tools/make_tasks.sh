#!/bin/bash
# Build, settle, check (with previews) and annotate task scenes.
#   bash tools/make_tasks.sh [task ...]   (default: all five)   SEED=0
cd "$(dirname "$0")/.."
export OMNI_KIT_ACCEPT_EULA=YES
PY=${ISAACLAB_PYTHON:-python}
TASKS=${@:-breakfast_setup collect_fruits desk_prep tidy_toys shelve_books}
for t in $TASKS; do
  echo "=== $t"
  $PY tools/build_tasks.py --task $t --seed ${SEED:-0} 2>&1 | grep -E "^TASK|Error|Traceback" || true
  $PY tools/settle_scene.py tasks/$t/scene.usd --seconds 5 2>&1 | grep -E "^SKIP|Traceback" || true
  [ -f tasks/$t/task.json ] || { echo "SKIP_TASK $t (build failed)"; continue; }
  VIEWS=$(python3 - "$t" <<'PY'
import json, math, sys
t = json.load(open(f"tasks/{sys.argv[1]}/task.json"))
pts = [p["position"] for p in t["placed_objects"].values()] or [[3.3, 6.7, 0.9]]
cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
x, y, yaw = t["robot_start"]
span = max(max(abs(p[0] - cx) for p in pts + [[x, y]]), max(abs(p[1] - cy) for p in pts + [[x, y]]))
h = max(4.0, 2.3 * span + 1.5)
print(f"--view overview {cx} {cy} {h} {cx} {cy + 0.001} 0.0 --view robot {x - 1.6} {y + 1.4} 1.9 {x} {y} 0.7")
PY
)
  $PY tools/check_scene.py tasks/$t/scene.usd --out tasks/$t/check $VIEWS 2>&1 | grep -E "^CHECK|Traceback" || true
  $PY tools/annotate_scene.py tasks/$t/scene.usd tasks/$t/annotation.json 2>&1 | grep -E "^ANNOTATION|Traceback" || true
done
