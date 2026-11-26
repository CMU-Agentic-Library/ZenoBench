# 11-25 起 GT 路线全量检查：给 muqingj 的技能问题清单

整理：2026-11-25 夜开始，边跑边补。以 `main` 为准（已含你的 remove-handcoded-motion，HAND_PLAN 9a-9j）。

## 1. 在跑什么

- `--profile sticky/gt --jobs 1`，参考路线（scripted planner），每个 episode 约 8 分钟。
- 批次 1：`benchmark/v6/batches/gt_check_1125.json`，55 个从没在全量里成功过的布局 → `benchmark/runs/gt_check_1125`。
- 批次 2：`gt_check_1125b.json`，剩下 118 个没成功过的布局 → `benchmark/runs/gt_check_1125b`。
- 批次 3：`gt_check_all.json`，其余 1194 个 episode，先每个布局第二个种子，再其余种子 → `benchmark/runs/gt_check_all`。
- 布局问题我直接改 `define_tasks_v6.py` / `new_tasks_v6.py` 并推到 main；下面只列**技能侧**的。

## 2. 技能侧问题（不是布局能绕开的）

| 任务 / 布局 / 种子 | 失败的步骤 | 报错 | 我的判断 |
|---|---|---|---|
| T07 `two_portions__dining` s11 | #5 `place(soup_pot, kitchen_stove/top)` | `place_arrive: no collision-free IK at the set-down pose (out of reach)` | 站位选在了灶台远的一侧，没换另一边再试。 |
| T08 `wipe_and_sort__duck` s12 | #15 `wipe(kitchen_island/top, kitchen_sponge)` | `wipe_stroke: the arm stopped 0.007 m short of where it was sent` | 前 15 步都成功，只差 7 mm 就判失败，擦拭的到位容差太紧。 |
| T10 `after_dinner_clear__leftovers_mug` s14 | #16 `place(leftovers, breakfast_fridge/inside_shelf)` | `tuck: its path collides now at 1/243: world left_gripper_right_finger_link 6 mm ... INVALID_START_STATE_WORLD_COLLISION` | 在冰箱里放下后，收臂起点手指已经和冰箱碰上 6 mm，退出失败。 |
| T27 `two_leftovers__soup_on_table` s16 | #0 `navigate` 的第一次 tuck | `tuck: the arm stopped 0.172 m short` | 开局站在墙角，第一次收臂碰墙。跟 11-16 记的“zihan 机器第一次收臂”一类；开局生成器按用户 11-17 的规定不动。 |

## 3. 已经在 bench 侧改掉的

- T30 `how_many__three_bowls`：三只碗挨太近，中间那只没有抓取 → 两只放 6 号柜相隔 30 cm，第三只放 4 号柜顶（570f15b5）。
- T14 `whose_book`：大人书架从 `large_shelf_2/shelf_2`（0.81 m，place 差 14 cm）改到 `shelf_1`（17a867e5）。
