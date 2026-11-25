# 物体与家具注册表

11-24 按 Katia 的建议建的注册表。11-25 起只用来做分类：用 affordance 判断替代品合不合法的部分（`roles.yaml`、`affordance_check.py`、`AFFORDANCE_CHECK_zh.md`）已经删掉。评分仍然只看 tasks.json 里手写的档位。

| 文件 | 内容 |
|---|---|
| `registry/objects.yaml` | 47 种可移动物体：类别 → 小类（如 餐具 → 杯类）、用途、材质等属性 |
| `registry/furniture.yaml` | 家具和电器：类别 → 小类，每种表面（台面、隔层、柜内）的用途 |
| `object_registry.py` | 读上面两个文件。尺寸、开口、表面高度、所在房间都从 `annotations/assets.json` 和场景标注读，不手写 |
| `tests/test_object_registry.py` | 词表封闭、v6 用到的物体和表面都登记了 |

谁在用：
- `taxonomy.py`：场景分类的物体类别（见 `TAXONOMY_zh.md`）。
- `substitution_eval.py`：`layout_objects()` 读布局里有哪些物体。
- `baseline/reveal.py`：`SHIFT_REVEAL` 消融（默认关），把看到过的物体的类别、用途、尺寸写进提示。
