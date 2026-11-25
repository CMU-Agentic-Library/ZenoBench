# 物体与家具注册表

11-24 建的注册表，11-25 起只用来做分类：affordance 判替代（`roles.yaml`、`affordance_check.py`）和 `SHIFT_REVEAL` 消融都已删掉，物体的用途、材质、尺寸字段也一起删了。评分只看 tasks.json 里手写的档位，模型输入里没有注册表的任何内容。

| 文件 | 内容 |
|---|---|
| `registry/objects.yaml` | 47 种可移动物体的类别和小类（如 餐具 → dish） |
| `registry/furniture.yaml` | 家具和电器的类别和小类 |
| `object_registry.py` | 读上面两个文件；表面所在的房间从场景标注读 |
| `tests/test_object_registry.py` | 类别封闭、v6 用到的物体和表面都登记了 |

用到它的地方：`substitution_eval.py`（`layout_objects()`）。`taxonomy.py` 的物体类别用的是同一套类别名，按布局手写。
