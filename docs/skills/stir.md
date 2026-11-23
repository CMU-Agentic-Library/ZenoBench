# stir（拿勺子在锅里搅，2026-11-15 起走运动分层）

右手拿着勺子，把勺尖伸进锅里，绕锅心转 1.25 圈。数的是勺尖实际转过的角度：勺尖在锅沿半径以内、锅沿以下时才算，满 1 圈才成功。`turns=0` 是 dip（policy DipUtensilPolicy）：勺尖伸进去再出来，不画圈。

入口：policy_085 `StirContainerPolicy` → `motion_skills.run_skill(SKILLS["stir"])` → `skill_jobs/stir.py` 的 `stir_job` + `skill_plans/contact.py` 的 `plan_stir`。设计见 `../motion/MOTION_ARCHITECTURE.md` 第 6 节"接触类技能"。

## 勺尖在哪：`tool_frame`

勺子的两端都是标注里的具名坐标系：`annotations/assets.json` 中 `breakfast_spoon` 的 `tool_frame.bowl`（+x 端的勺碗，离端头 1 cm、碗里往下 4 mm）和 `tool_frame.handle`（−x 端，勺柄末端往里 5 mm）。它们写在资产自己的刚体坐标系里（和 `grasps` 一样），在 `tools/prepare_assets.py` 的 `TOOL_FRAMES` 里，重新生成资产时会一起写回。

伸进锅里的是**离手远的那一端**（`skill_jobs/tool.py` 的 `free_end`）。勺子的 top pinch 捏在勺碗那头：两指张开约 4 cm，抓取点在刚体 +x 0.054 m（stir_1115）。所以搅的是勺柄，这和旧代码"长轴上离 TCP 远的一端"一样。第一版只标了勺碗，算出来勺尖离 TCP 只有 3 cm，手得伸进锅里，T09 lid_off、tomato_elsewhere 两集的停车点全部建不出来（stir_1115 第一轮）。

只有 `tool_in_tcp` 读这条标注，按手里现在的握法换成 `T_tcp_tool = Held.T_tcp_obj · T_obj_tool`。计划只拿这个矩阵。以后加新的工具，只需要加一条标注。

## 停车点怎么选（`stir_job` → `park_search.find_park`）

1. **先把勺子收到搬运姿态**（`carry_posture`，相当于旧代码的 `stow_load`）。
2. **勺尖的圈**：圆心在锅口中心，比锅沿低 `STIR_DEPTH`，即 min(4 cm, 锅沿高 − 1.5 cm)。圈半径 `STIR_RADII` 依次是 3.5 cm（不超过锅沿半径的 0.45）、2.2 cm、1.2 cm。圈写在锅的坐标系里，锅被碰动了，重做的计划也跟着锅走。
3. **勺子的姿态**：从搬运姿态出发，绕横过勺子的水平轴转 `STIR_TILT`（50°），让勺尖朝下；手再绕竖直轴转 0°、90°、−90°、180°（`STIR_YAWS`），对应从锅的四个方向下勺。
4. **目标集合**：3 个半径 × 4 个朝向 = 12 个目标。`Problem.tiers` 按半径分层，最大的圈全部构造完才轮到小圈；同一层里，朝向每靠后一名加一个 `VARIANT_COST`。预筛要求 TCP 能到下勺点的上方、下勺点，以及圈上的四个四分点；排序 IK 解的是下勺点（relay `stir_reach`）。
5. **按顺序做整份计划**（`plan_stir`），第一个做得出来的胜出：

| # | 段 | 做法 | 查碰撞 |
|---|---|---|---|
| 1 | `stir_arrive` | 锚点：底盘、锅、握法 | — |
| 2 | `stir_reach` | 自由段，到下勺点正上方 `深度 + STIR_ABOVE`（6 cm），勺子已经倾斜好。TCP 直线不通时，走到 `decide_ik` 定的解（种子是排序解）。容差 `STIR_TOL` | 查，手指在模型里；**不保持倾角**（见下） |
| 3 | `stir_dip` | 竖直往下，勺尖到圈的起点 | 勺子和捏着它的手指可以碰锅和锅里的东西，手臂其余部分照查 |
| 4 | `stir_circle` | 任务段：`Script` 加 `Still(锅)` 耦合，s 是勺尖在圈上的角度，从 0 到 2π × 1.25，每 15°（`STIR_STEP`）一个检查点，手臂沿着走（carry "arm"，IK 接续）。整圈要么都过、要么失败 | 同上 |
| 5 | `stir_stirred` | 锚点：圈画完后的锅和勺子 | — |
| 6 | `stir_leave` | 竖直往上 `深度 + STIR_ABOVE` | 同 3（出发时还在锅里） |
| 7 | `stir_back` | 自由段，回到进来时的搬运姿态（这是计划记下的决定；后面重做时，回的还是第一次记下的那个姿态） | 查，不保持倾角 |

**倾角**：拿着东西时，"倾角规则"（`kinematics.carry_tilt_allowed`，4a48b66）管的是必须端平的东西（杯子、盘子、书）。在新架构里，每段用哪个 `Spec` 由技能自己定，stir 的两段自由段用 `FREE_HAND`（`hold_tilt=False`），所以勺子可以故意倾斜。旧代码由 `rig._carrying()` 一律打开约束：勺子从搬运姿态转到倾斜 50° 的路上会超过 1.02 rad，v6full_1115 里 T09 lid_off、tomato_elsewhere 因此失败（`stir_above: carry tilts 1.8 rad`）。全局规则没改。

**勺子碰锅**：`Spec.touch` 新增了一类 `(名字, "held")`：手指和手里的东西（held link）可以碰这些物体，手臂其余部分照样对它们查碰撞（`Motion.path_free_only` 关掉手指和 held link 再查一遍）。监控器用 `Allow.held_on` 记同样这几样（锅和 `objects_inside` 给出的锅里的东西）。

## 执行和判定

- `run.run` 每段之前复核，在两个锚点处重做剩下的部分。
- 下勺和画圈这两段执行时，job 在 `Rig.tick_watchers` 上挂一个采样：每 4 个物理步读一次勺尖的实际位置（`rig.obj_pose` 加上 `tool_frame`），勺尖在锅里时，把相邻两次绕锅心转过的角度累加起来。判据和旧代码一样，只是从每圈 16 个点改成每 4 个物理步采一次。
- 回到搬运姿态后检查勺子还在手里。
- 结果：圈数写进 `memory["stirred"]`，满 1 圈才成功；dip 时勺尖进过锅里就写 `memory["dipped"]`。

## 和旧代码比

- 删了旧 `StirContainerPolicy._stir` 和"腰先限 0.3 rad、找不到停车点再放开"的特判。旧代码这么做，是因为腰弯 0.54 rad 时停在 0.40 rad，勺尖停在锅沿上方。新架构下还要不要这个限制，看仿真。
- 旧代码画圈时，够不着的点就跳过、照样数圈（`stir_circle_skip`）。现在整圈都要做得出来，做不出来就换一个停车点或者更小的圈；都不行就失败。
- 旧代码画圈和下勺都不查碰撞（`LEGACY`），现在查（勺子可以碰锅和锅里的东西）。

## 已知问题和没查到的

- 仿真检查（stir2_1115）：T09 lid_off nominal、tomato_elsewhere dining 整集成功；pot_in_use（换成勺柄以后）、tomato_in_fridge、pot_in_dining_room、lid_on_spoon_away 还没跑。详见 `../motion/MOTION_ARCHITECTURE.md` 9.3 第 7 步。
