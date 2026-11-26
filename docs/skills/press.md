# press、touch、knock（指尖压上去再退出来）

三个技能是同一份计划 `plan_press`（`zeno_skills/skill_plans/contact.py`）：合拢的指尖沿一个方向压进一个面一点点，停在那里（锚点），按碰撞模型量着退出来，收臂。区别只在压哪里、压完记什么：

| 技能 | 压哪里 | job | 压完 |
|---|---|---|---|
| press（8a，11-24） | 电器的按键（`<电器>/<键>`），指尖进按键面 `PRESS_DEPTH` 3 mm | `skill_jobs/press.py` 的 `press_job` | 按键的动作：热源开关（`toggle`）；门键的门由电机开到位（`press_door`，只在机器人整段都在门扫过的范围外时） |
| touch（9g，11-25） | 物体顶面中心，指尖进顶面 `TOUCH_DEPTH` 2 mm；合拢方向 4 个（`TOUCH_CLOSES`） | `touch_job` | 记 `touch_contact`（`touched` 谓词：物体挪动小于 `TOUCHED_STILL` 1.5 cm） |
| knock（9g，11-25） | 门板上把手旁的 5 个点（`KNOCK_AT`，在把手条后面的门板平面上）× 2 个合拢方向，指尖进门板 `TOUCH_DEPTH` | `knock_job`，`KnockPanelPolicy` 每敲一次跑一次技能 | 记 `knock_contact`；门的关节动了 `KNOCKED_STILL` 以上算失败（`knocked` 谓词同一个值） |

## 用哪只手

空着的手。两只手都空时两只都在停车点搜索的目标集合里（每个目标带手，`Problem.goals` 第 4 项），右手只靠 `VARIANT_COST` 排在前面，实际按排序的分数选（HAND_PLAN 3.1）。touch / knock 11-25 规则审查时改成这样；之前和 press 一样，两只都空就直接取右手（job 里先选手）。press 还是这样（8a 的写法，HAND_PLAN 第 7 节"规则审查"里列着）。

## 一步一步

1. **停车点搜索**：每个目标（压点 × 合拢方向 × 手）是一个目标，排序 IK 解的是压完的位姿；每个候选停车点上建整份计划，建得出来才算。
2. `press_arrive`：锚点，底盘停下的样子。
3. `press_reach`：自由段到压点正前方 `PRESS_APPROACH`（10 cm）。
4. `press_close_hand`：在空中合爪（一秒，等手指真合上：11-25 之前只给 30 个物理步，手指还张着约 2 cm，下一段的复核按张开的手指查）。
5. `press_in`：直线压进去，只有手指可以碰被压的东西（`Spec.touch`），其余照查。
6. `press_toggle`：电器的动作（只有 press 有）。
7. `press_pressed`：锚点，手被按键 / 物体 / 门板挡住的地方。
8. `press_leave`：沿来路退出，长度由 `contact_extent` 量（离开 `LEAVE_GAP` 再走 `LEAVE_MARGIN`）。
9. `tuck`：收臂（每次重选，不复用）。
10. `press_door` / `press_door_moved`：只有门键有。

## 已知问题

- `TOUCH_DEPTH`、`PRESS_DEPTH` 是力的几何替身（COLLISION_PLAN 第 8 节），有力控制时换成力。
- knock 在 v6 里没用到，只有单测；touch 在 T19 lookalike_bin 里用到。
