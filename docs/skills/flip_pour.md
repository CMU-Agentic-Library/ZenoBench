# flip 和 pour（拿着的东西绕一条轴转）

两个技能都是"手里的东西绕一条线转"的任务段（`scripted`，`carry="arm"`：底盘不动，手臂沿圆弧走，IK 沿 `s` 连续延续），转多远由手臂量（`reach`：转到够不着为止），转得不够就在构造里拒掉。倾角都不保持（转动本身就是倾角的变化），持物照样在碰撞模型里。计划在 `zeno_skills/skill_plans/contact.py`（`plan_flip`、`plan_pour`），HAND_PLAN 9h（11-25）。

## flip（翻书）

前提：书被捏着一条边（edge pinch，从悬出的边上取起来的），手是拿着它的那只。job 是 `skill_jobs/held.py` 的 `flip_job`，不选停车点（原地做）。

1. `flip_arrive`：锚点。
2. `flip_arc`：任务段，被捏住的近边绕远边（远边在支撑面上，是枢轴）往上翻，手跟着转；转到 `FLIP_RELEASE`（105°）或手臂够不着为止。转不到 `FLIP_MIN`（60°）这份计划就不成立（`plan_flip` 自己的约束，`flip["min_arc"]`：搜索和执行中的重做同一条，11-25 之前只在第一次构造时查）。
3. `flip_release`：张手（手指可以碰书）。
4. `flip_let_go`：锚点，书松开后落在哪（11-25 加：之后的推和退出按实测重做）。
5. `flip_push`：没转过竖直（`FLIP_PAST`，95°）时，张开的手沿同一条圆弧接着推到 `FLIP_PUSH_TO`（120°）；手指可以碰书。
6. `flip_leave`：沿夹爪轴退出，`contact_extent` 量长度。
7. `tuck`、`flip_settle`（等 150 个物理步）。
8. 结果：书的 z 轴和开始时点积不大于 `FLIPPED_DOT`（−0.7，`flipped` 谓词同一个值）。

还没做：`flip_push` 的耦合是 `still`（书在模型里不随 `s` 动），翻 / 滚的 `pivot` / `rolled` 耦合（MOTION_ARCHITECTURE 5.5）没加。检查（P05，11-25）只转得到约 15°：flip 没有自己的停车点搜索，从 pick 留下的手臂姿态延续 IK 转不过去，要把圆弧放进 pick（或 flip 自己）的停车点 / 抓法选择里。

## pour（倒）

job 是 `skill_jobs/pour.py` 的 `pour_job`，有停车点搜索。手是拿着杯子的那只。

1. 先摆好搬运姿态，杯底抬到目标沿口上方 `POUR_ABOVE`（5 cm）。
2. 目标集合：手绕竖直轴转 `POUR_YAWS`（6 个）× 杯口偏移（中心、往机器人这边一点）× 倒的方向（把手捏取多两种侧倒）；倒的轴是"手和杯口的中点"那条水平线。
3. `pour_arrive`：锚点。
4. `pour_reach`：自由段到倒的起点（保持倾角）。
5. `pour_tilt`：任务段，绕轴倾倒，最多 `POUR_TILT`（110°），到手臂够不着为止；不到 `POUR_MIN_TILT`（60°）这份计划不成立（`pour["min_tilt"]`，搜索和重做同一条）。
6. `pour_hold`：停 180 个物理步。
7. `pour_untilt`：沿原弧转回。
8. `pour_back`：回到到达时的手臂姿态（拿着杯子：搬运姿态）。
9. 结果：里面的东西至少一半进了目标。

旧代码卡住时"晃一晃"的补救没有搬（那是退路）。检查（P17，11-25）：左手倒到 110°，3 个番茄倒出 1 个，失败。
