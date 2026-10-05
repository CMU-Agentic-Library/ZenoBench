# 新建任务、资产、场景与标注

以下命令从 `zeno-house/` 仓库根目录运行。现有房屋是 `sim/zeno_house.usd`；带冰箱和微波炉的版本是 `sim/zeno_house_appliances.usd`。任务场景是叠在房屋上的 USD layer，可以放入新物体并设置 Malo 的初始位置。

| 文件 | 作用 | 何时更新 |
|---|---|---|
| `task_specs/<name>.json` | 指令、待放置物体、候选起点、目标条件 | 新建或修改任务时 |
| `tasks/<name>/scene.usd` | 生成后的具体布局 | 重新生成任务布局时 |
| `tasks/<name>/task.json` | 本次布局的目标和实际物体清单，供策略与评测使用 | 与 scene 一起生成 |
| `tasks/<name>/annotation.json` | **场景专属**的房间、支撑面、障碍、物体和关节几何 | scene 改变或物体 settle 后重新生成 |
| `annotations/assets.json` | **资产类型共享**的尺寸、质量、抓取候选和容器几何 | 新增或重新处理资产时 |

`scene.usd`、`task.json`、`annotation.json` 必须对应同一次布局。不能把一个任务的 annotation 直接配给另一个 scene。标注提供 GT 几何候选；能否真正抓住、放下或打开，仍要在仿真中验证。

## 1. 用已有资产新建任务

需要 Isaac Lab Python。先查看可用资产、物体实例、支撑面及别名，再从可运行的例子修改任务 spec：

```bash
export OMNI_KIT_ACCEPT_EULA=YES ISAACLAB_PYTHON=/path/to/isaaclab/python
python tools/list_places.py --room bedroom
cp task_specs/examples/serve_guest.json task_specs/serve_guest.json
# 编辑 task_specs/serve_guest.json 中的 objects、supports 和 goal
SEED=0 bash tools/make_tasks.sh serve_guest
$ISAACLAB_PYTHON tools/run_task.py --task serve_guest
```

`make_tasks.sh` 依次执行 `build_tasks.py`（选物体位置并生成 USD/task.json）、`settle_scene.py`（物理落稳）、`check_scene.py`（稳定性和预览图）、`annotate_scene.py`（生成场景标注）。检查终端里的 `TASK`、`CHECK`、`ANNOTATION` 输出，以及 `tasks/serve_guest/` 中生成的文件；脚本为便于批量处理会继续执行后续任务，不能只凭 shell 退出码判断成功。`run_task.py` 把执行与评测结果写入 `runs/serve_guest/`。

Spec 中 `objects` 使用 `annotations/assets.json` 的资产名，`supports` 使用 `list_places.py` 列出的支撑面或 `task_specs/places.json` 中的别名。`goal` 可组合 `on`、`inside`、`upright`、`near`、`heated`、`closed`、`not_dropped`；结构见 [示例](../task_specs/examples/serve_guest.json) 和 [评测说明](../README.md#success-conditions)。`SEED` 可生成另一种布局，但会覆盖同名 `tasks/<name>/`；生成新布局后要重新 settle、check 和 annotate。新目标谓词或新的电器机制可能还需要扩展 evaluator、任务协调器或底层 policy。

## 2. 新增可抓取资产

`tools/generate_assets.py` 将 EmbodiedGen V2 生成的网格注册为带物理碰撞、纹理和抓取标注的 USD 资产。EmbodiedGen 需要单独的环境；参考其[安装文档](https://horizonrobotics.github.io/EmbodiedGen/docs/install.html)。已有 URDF 可使用 `--skip-generate`，此时不需要重新生成网格。

```bash
export EMBODIEDGEN_ROOT=/path/to/EmbodiedGen
# 可选：export EMBODIEDGEN_PYTHON=/path/to/embodiedgen/bin/python
python tools/generate_assets.py --name soda_can \
  --prompt "an empty red aluminium soda can" \
  --size 0.12 --mass 0.02 --tags can recyclable

# 或从照片生成容器；圆形容器需有可放物的碰撞结构
python tools/generate_assets.py --name my_mug --image photos/mug.jpg \
  --size 0.10 --mass 0.30 --tags mug container --collider round_container
```

`--size` 是最长边（米），`--mass` 是千克；`--collider` 可选 `solid`、`round_container`、`rect_container`；薄物体可加 `--lay-flat`。命令依次写入 `assets/asset3d/<name>/result/`、`assets/custom_assets.json`、`usd/assets/<name>.usd`、`annotations/assets.json`，并修复材质纹理。抓取标注可能包含 `top_pinch`、`rim_pinch` 或宽于夹爪物体的 `edge_pinch_after_push`；无法标出可行抓取时，资产会被标为不可抓。可用 `--batch assets/new_assets.example.json` 批量生成。

随后在 task spec 中引用新资产，并重新生成任务场景和场景 annotation：

```json
"objects": {"can_1": {"asset": "soda_can", "supports": ["tv_stand"]}}
```

如果已有 URDF，只需把文件放在 `assets/asset3d/<name>/result/<name>.urdf`，然后用 `--skip-generate` 运行同一命令；不要手工只改 `annotations/assets.json` 而漏掉 USD 和注册信息。

## 3. 选择或扩展场景

通常无需手写任务 USD：`build_tasks.py` 会在基础房屋上创建任务 layer。普通任务默认使用 `sim/zeno_house.usd` 与 `annotations/zeno_house.json`；电器任务在 spec 中指定相互匹配的基础 scene/annotation：

```json
"base_scene": "sim/zeno_house_appliances.usd",
"base_annotation": "annotations/zeno_house_appliances.json"
```

如果要给房屋增加门、抽屉等 PartNet-Mobility 资产，使用导入、放置和标注工具；实例和关节名要以新 annotation 中的条目为准：

```bash
$ISAACLAB_PYTHON tools/import_partnet.py --id 48452 --name partnet_cabinet_48452 --height 1.0
$ISAACLAB_PYTHON tools/place_partnet.py --asset partnet_cabinet_48452 --name partnet_cabinet
$ISAACLAB_PYTHON tools/annotate_scene.py sim/zeno_house_partnet.usd annotations/zeno_house_partnet.json
$ISAACLAB_PYTHON tools/run_skills.py --scene sim/zeno_house_partnet.usd \
  --ann annotations/zeno_house_partnet.json --out runs/partnet_open \
  --plan "open partnet_cabinet" "close partnet_cabinet"
```

导入器从 URDF 提取关节轴、限位及门板/抽屉，并为可识别的把手生成接触几何；是否能 hook 或 pinch，要看导入报告和实际动作。若新的基础场景不是上述房屋结构，需要先适配标注器预期的房间、支撑面、机器人路径和关节约定；它不是通用 USD 自动标注器。

## 4. 手工改了 scene 后重新标注

场景标注应在物体 settle、物理检查之后生成。以下命令也适用于修改过的任务 USD；路径按实际场景替换：

```bash
$ISAACLAB_PYTHON tools/settle_scene.py tasks/serve_guest/scene.usd --seconds 5
$ISAACLAB_PYTHON tools/check_scene.py tasks/serve_guest/scene.usd --out tasks/serve_guest/check
$ISAACLAB_PYTHON tools/annotate_scene.py tasks/serve_guest/scene.usd tasks/serve_guest/annotation.json
```

`annotate_scene.py` 复用 `annotations/house_static.json` 中的房屋静态几何，读取当前 USD 的任务物体、关节和机器人位置。新场景若改变了房屋本体，不能只重用旧的静态缓存。`annotations/assets.json` 是按资产类型共享的数据，不应把世界坐标写入其中。

最后确认三个文件指向同一场景，再运行任务：

```bash
python - <<'PY'
import json
from pathlib import Path
name = "serve_guest"
root = Path("tasks") / name
task = json.loads((root / "task.json").read_text())
ann = json.loads((root / "annotation.json").read_text())
assert task["scene_usd"] == ann["scene_usd"] == str(root / "scene.usd")
print("scene / task / annotation match:", ann["scene_usd"])
PY
$ISAACLAB_PYTHON tools/run_task.py --task serve_guest
```

想仅验证一个原子动作，可以调用 `tools/run_skills.py --scene ... --ann ... --plan "pick <object>"`；完整任务是否成功以 `runs/<name>/result.json` 中的评测结果为准。
