# 交接：两只手（给 bench 作者，2026-11-25）

HAND_PLAN（`docs/motion/HAND_PLAN.md`）第 6 节的决定 2 说：改 v6 生成器里写 `hand_empty` 的地方时，在交接文档里写明。这一篇就是。

## 1. 评分：`["hand_empty", "right"]` 改成了 `"both"`（9b，11-24，a2288b35）

- pick 现在会用左手（9c：用哪只手是停车点搜索的目标集合的一维），所以"右手空"不再表示"东西都放下了"。
- 改的地方：`benchmark/v6/define_tasks_v6.py` 的 `both_hands_empty`，以及几个生成器文件里写死的 `["hand_empty", "right"]`（共 2256 处目标）；`benchmark/v6/tasks.json`、`STATIC.json` 重新生成。
- 谓词 `hand_empty` 的手多了 `any`（至少一只空）和 `both`（两只都空）。
- 检查：9b 的针对性检查 4/4，评分 best 1.0，`hand_empty(both)` 都成立；v6 静态检查 1510/1510。

## 2. 路线可以限定 pick 用哪只手（规则审查，11-25）

- pick 合约的 `hands` 输入：`any`（默认，不写也一样：两只都行，搜索选）、`right` / `left`（只用那只手：任务要另一只手留着干别的）、`both`（两手抬宽物体，原来就有）。
- v6 的路线都没写 `hands`，行为不变；静态检查仍是 1510/1510（`STATIC.json` 没变）。
- 诊断用的"强制用左手"以后写在路线参数上：`benchmark/run_episode.py --pick-hand left`（batch 里是 `pick_hand` 键），会写进每集的 `config.json`，不进基线。以前的环境变量 `ZENO_PICK_SIDE` 删了。

## 3. 其他会碰到的

- `skill_library/planner.py`（符号规划器）现在认 `any` / `both`：9a–9c 以后它解不出 collect_fruits、cook_tomato_soup，`skill_library/tests` 有 2 个测试（9d 以后 3 个）一直是红的，11-25 修好。
- 合约文字里"right gripper / right-held"改成了"either hand"；`invalidates` 不再写死右手（pick、point、press、place、drop、stack、cover）。
