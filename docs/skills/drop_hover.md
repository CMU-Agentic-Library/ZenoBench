# drop 和 hover

两者都是"把手里的物体举到某个东西正上方"，只有一个中继位姿；drop 到了就松手，hover 停在那里。都走运动分层：drop 11-14，hover 11-25（HAND_PLAN 9e：`plan_hover` 就是 `plan_drop` 去掉松手、下落、收臂）。两只手都行，用拿着这个物体的那只。

## drop（扔进容器）

`skills.drop_into` → `motion_skills.run_skill(SKILLS["drop"])`，job 是 `skill_jobs/drop.py` 的 `drop_job`，计划是 `skill_plans/place.py` 的 `plan_drop`（catalog 的 `template`）。`drop` 动作（`DropIntoPolicy`）和 `place(name, "in:<容器>")` 都走这里，托盘除外（托盘走 [place](place.md)）。

**中继位姿：物体在容器开口上方，最低点比沿口高 `LEAVE_GAP`（5 mm）。** 不放下（在空中松手），也没有抽出段（物体落下后手指之间什么都没有）。

1. **已经在上面了吗？** 物体中心在开口中心 0.6 个半径以内，最低点在沿口以上 0–25 cm（比如先 hover 过来的）：目标集合只有现在这个位姿，现在的底盘位置先试（`Problem.near` 带朝向），一般就地做第 5 步以后的部分。
2. **摆好搬运姿态**（见[搬运姿态](carry.md)），物体底部在沿口以上（`_carry_bottom_z`），检查物体还在手里，之后按这个姿态找停车点。
3. **找停车点（`find_park`，整份计划在停车点上做出来）。** 目标集合：开口中心，以及从中心往 ±x、±y 各偏到物体还离得开内壁的位置（深的桶放在桌上，中心可能够不着），偏出去的代价高一点；每个点手腕绕竖直轴转 8 个角度，转得越多代价越高。每个目标是物体的位姿，TCP 按状态里现在的握法推出来（`Aim`，和 place 一样）。计划 `plan_drop`：
   - `drop_arrive`：锚点；
   - `drop_reach`：自由段，持物保持倾角（`FREE_LOAD`：查手指，容器和周围物体都是障碍物），关节解由 `decide_ik` 定（排序 IK 的解先试），带 `PLACE_TOL`，执行前按 `holds` 复核；
   - `drop_release`：40 帧张开到抓取宽度，手指可以碰它松开的物体、物体可以碰容器（`release_spec`）；
   - `drop_fall`：等 1 秒让物体落下；
   - `tuck`：收到第一个不碰的收起 / 下垂姿态（和 place 一样，每次重做）。
   落点预测不了（8.5），不设落地锚点；计划里的状态把物体放到容器底上（落下 `fall`），只是让收臂不把它当障碍物。
4. **开过去**（`run_skill` 调 navigate，带搬运姿态的 `min_bottom_z`）。
5. **照计划执行**：`drop_reach` 之后检查物体还在手里，`drop_release` 之后手里就空了。搜索时做出来的计划原样执行，不再重新规划同一段（旧代码在执行时重新规划 `drop_above`，搜索能过、执行规划不出来的就失败：T19 bin_on_bookcase 时好时坏）。
6. **检查**：物体要整个在容器里。

**已知问题：**

- 要露在容器外面的物体（擀面杖插进杯子）从沿口上方松手会倒或弹出去。以后按几何分流：整个落得进开口的 drop，露在外面的走放下段插进去（计划第 7 节）。

## hover（悬停在目标上方）

`HoverOverPolicy` → `run_skill(SKILLS["hover"])`，job 是 `skill_jobs/drop.py` 的 `hover_job`，计划是 `skill_plans/place.py` 的 `plan_hover`。

**中继位姿：物体底面居中、最低点在目标顶面上方 6 cm**（`HOVER_CLEAR`；目标是物体时顶面 = 底面 + 沿口高度或物体高度，否则是标注点；`hovering_over` 要求 3–15 cm、水平 4 cm 以内）。

1. **摆好搬运姿态**（`carry_posture`，最低高度 = 顶面 + 6 cm，是愿望不是约束）。
2. **找停车点**：一个点 × `PLACE_YAWS` 的手腕朝向，每个是一个目标，停车点上建整份计划。
3. **开过去**（搬运姿态，最低高度同上）。
4. **`hover_arrive` 锚点、`hover_reach` 自由段**：保持物体倾角，`PLACE_TOL`；做不出来就失败。旧代码的 `stow_load` + `park_over` + `move_to` 删了。
5. **检查物体还在手里**；结果：物体底面高于目标顶面。之后的 drop 发现物体已经在开口上方，就地松手（drop 第 1 步）。
