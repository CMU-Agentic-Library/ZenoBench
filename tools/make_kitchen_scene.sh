#!/bin/bash
# Rebuild the kitchen layer (stove + prep island), its annotation and the
# kitchen_skills task scene, then settle, check and annotate it.
cd "$(dirname "$0")/.."
export OMNI_KIT_ACCEPT_EULA=YES
PY=${ISAACLAB_PYTHON:-python}
$PY tools/build_kitchen_scene.py 2>&1 | grep -E "^KITCHEN|Traceback" || true
$PY tools/annotate_scene.py sim/zeno_house_kitchen.usd annotations/zeno_house_kitchen.json 2>&1 | grep -E "^ANNOTATION|Traceback" || true
t=kitchen_skills
$PY tools/build_tasks.py --task $t --seed ${SEED:-0} 2>&1 | grep -E "^TASK|Traceback|Error" || true
$PY tools/settle_scene.py tasks/$t/scene.usd --seconds 6 2>&1 | grep -E "^SKIP|Traceback" || true
$PY tools/check_scene.py tasks/$t/scene.usd --out tasks/$t/check --view island 7.4 0.75 1.7 7.4 1.75 0.85 \
    --view stove 8.55 1.0 1.5 8.55 1.75 0.75 --view overview 7.6 -0.4 3.6 7.6 1.6 0.5 2>&1 | grep -E "^CHECK|Traceback" || true
$PY tools/annotate_scene.py tasks/$t/scene.usd tasks/$t/annotation.json 2>&1 | grep -E "^ANNOTATION|Traceback" || true
