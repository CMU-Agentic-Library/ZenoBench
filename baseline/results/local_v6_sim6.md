# ZenoBench v6 本地 VLM 基线 · Isaac Sim 6.0.0.1

**原生计分覆盖 114 / 24,546 局。** 当前为阶段性结果。各行先完成的布局可能不同，跨模型比较请看配对分表。

汇总时间为 2026-11-24 12:18 UTC。

Isaac Lab 适配清单 SHA-256 为 `5e09ce356754c98e3f02eeb3b5d7f931cf78d4a684758db346189976a18a6c39`。cuRobo 0.7.8，Warp 1.13.0，PyTorch 2.11.0（CUDA 13.0）。

本表是在 Isaac Sim 6.0.0.1 上独立运行的版本适配实验。仓库原协议使用 Isaac Sim 5.1。物理接触、相机渲染以及技能执行结果会受仿真版本影响。

主实验按公开 v6 批次覆盖 30 个任务、151 个设计、316 种布局，种子 10–19。每个方法和模型计划运行相同的 1,510 局，技能调用上限为 60。消融在每种布局首次出现的种子上运行，共 316 局，并与相同种子的 ReAct 配对。

主实验沿用仓库 VLM 基线方案的 sticky/benchmark，物体在搬运时固定，抓放通过物理执行。公开脚本批次在 Control 和 Action + Task 使用 benchmark，在 Task 使用带抓放修正的 sticky_snap/gt。本表末尾的脚本参考路线也按 sticky/benchmark 重新执行。

Graph Manager 只计入使用独立随机工作目录的局。旧 Harness 消息曾包含带布局名的路径，受影响的旧尝试已排除，重跑仍计入各模型原有的 1,510 局。

计分需要规划器和 Isaac Sim 同时记录相同的任务、种子、episode hash 和最终判定。实际成功率使用环境的最终 success，得分大于零和满分率另列。仿真记录中的掉落规则可能使实际成功率低于正分率。

## 主实验

| 方法 | 模型 | 已计分/计划 | 中断待重跑 | 平均分 | 平均分 95% CI | 任务成功 | 正分 | 满分 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 7/1510 | 0 | 0.000 | — | 0/7 | 0/7 | 0/7 |
| OpenLoop | qwen3.5-27b | 7/1510 | 0 | 0.000 | — | 0/7 | 0/7 | 0/7 |
| OpenLoop | internvl3.5-8b | 7/1510 | 0 | 0.000 | — | 0/7 | 0/7 | 0/7 |
| ReAct | qwen3.5-4b | 8/1510 | 0 | 0.000 | — | 0/8 | 0/8 | 0/8 |
| ReAct | qwen3.5-27b | 8/1510 | 0 | 0.125 | — | 1/8 | 1/8 | 1/8 |
| ReAct | internvl3.5-8b | 8/1510 | 0 | 0.000 | — | 0/8 | 0/8 | 0/8 |
| CodeAsPolicies | qwen3.5-4b | 7/1510 | 0 | 0.000 | — | 0/7 | 0/7 | 0/7 |
| CodeAsPolicies | qwen3.5-27b | 6/1510 | 0 | 0.000 | — | 0/6 | 0/6 | 0/6 |
| CodeAsPolicies | internvl3.5-8b | 7/1510 | 0 | 0.000 | — | 0/7 | 0/7 | 0/7 |
| SayPlan | qwen3.5-4b | 4/1510 | 0 | 0.000 | — | 0/4 | 0/4 | 0/4 |
| SayPlan | qwen3.5-27b | 7/1510 | 0 | 0.000 | — | 0/7 | 0/7 | 0/7 |
| SayPlan | internvl3.5-8b | 5/1510 | 0 | 0.000 | — | 0/5 | 0/5 | 0/5 |
| GraphManager | qwen3.5-4b | 0/1510 | 0 | — | — | — | — | — |
| GraphManager | qwen3.5-27b | 0/1510 | 0 | — | — | — | — | — |
| GraphManager | internvl3.5-8b | 0/1510 | 0 | — | — | — | — | — |

置信区间按任务内的设计聚类，重采样 2,000 次。只有全量覆盖的行给出区间。

## 按任务条件配对

每种方法取三个模型都已计分的相同任务、布局和种子。前三列按任务类别给出平均分和配对局数，接下来两列按布局中的理想选项是否可用划分。理想选项不可用时，v6 给该布局的最佳替代结果记 1.0 分。最后一列统计达到这一档且通过环境最终成功检查的局数，分母是理想选项不可用的配对局。

| 方法 | 模型 | Control | Task | Action + Task | 理想选择可用 | 理想选择不可用 | 达成布局最佳替代/理想选择不可用 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 0.000 (3) | 0.000 (2) | 0.000 (2) | 0.000 (6) | 0.000 (1) | 0/1 |
| OpenLoop | qwen3.5-27b | 0.000 (3) | 0.000 (2) | 0.000 (2) | 0.000 (6) | 0.000 (1) | 0/1 |
| OpenLoop | internvl3.5-8b | 0.000 (3) | 0.000 (2) | 0.000 (2) | 0.000 (6) | 0.000 (1) | 0/1 |
| ReAct | qwen3.5-4b | 0.000 (3) | 0.000 (3) | 0.000 (1) | 0.000 (5) | 0.000 (2) | 0/2 |
| ReAct | qwen3.5-27b | 0.333 (3) | 0.000 (3) | 0.000 (1) | 0.200 (5) | 0.000 (2) | 0/2 |
| ReAct | internvl3.5-8b | 0.000 (3) | 0.000 (3) | 0.000 (1) | 0.000 (5) | 0.000 (2) | 0/2 |
| CodeAsPolicies | qwen3.5-4b | 0.000 (3) | 0.000 (1) | 0.000 (2) | 0.000 (5) | 0.000 (1) | 0/1 |
| CodeAsPolicies | qwen3.5-27b | 0.000 (3) | 0.000 (1) | 0.000 (2) | 0.000 (5) | 0.000 (1) | 0/1 |
| CodeAsPolicies | internvl3.5-8b | 0.000 (3) | 0.000 (1) | 0.000 (2) | 0.000 (5) | 0.000 (1) | 0/1 |
| SayPlan | qwen3.5-4b | 0.000 (2) | 0.000 (1) | 0.000 (1) | 0.000 (3) | 0.000 (1) | 0/1 |
| SayPlan | qwen3.5-27b | 0.000 (2) | 0.000 (1) | 0.000 (1) | 0.000 (3) | 0.000 (1) | 0/1 |
| SayPlan | internvl3.5-8b | 0.000 (2) | 0.000 (1) | 0.000 (1) | 0.000 (3) | 0.000 (1) | 0/1 |
| GraphManager | qwen3.5-4b | — | — | — | — | — | — |
| GraphManager | qwen3.5-27b | — | — | — | — | — | — |
| GraphManager | internvl3.5-8b | — | — | — | — | — | — |

## 提示和观测消融

| 方法 | 模型 | 已计分/计划 | 中断待重跑 | 平均分 | 平均分 95% CI | 任务成功 | 正分 | 满分 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ReActHint | qwen3.5-4b | 7/316 | 0 | 0.000 | — | 0/7 | 0/7 | 0/7 |
| ReActHint | qwen3.5-27b | 5/316 | 0 | 0.000 | — | 0/5 | 0/5 | 0/5 |
| ReActHint | internvl3.5-8b | 6/316 | 0 | 0.000 | — | 0/6 | 0/6 | 0/6 |
| ReActPrivileged | qwen3.5-4b | 6/316 | 0 | 0.000 | — | 0/6 | 0/6 | 0/6 |
| ReActPrivileged | qwen3.5-27b | 5/316 | 0 | 0.200 | — | 1/5 | 1/5 | 1/5 |
| ReActPrivileged | internvl3.5-8b | 4/316 | 0 | 0.000 | — | 0/4 | 0/4 | 0/4 |

| 消融 | 模型 | 配对数 | ReAct 平均分 | 消融平均分 | 差值 |
| --- | --- | --- | --- | --- | --- |
| ReActHint | qwen3.5-4b | 7 | 0.000 (7) | 0.000 (7) | +0.000 |
| ReActHint | qwen3.5-27b | 5 | 0.000 (5) | 0.000 (5) | +0.000 |
| ReActHint | internvl3.5-8b | 6 | 0.000 (6) | 0.000 (6) | +0.000 |
| ReActPrivileged | qwen3.5-4b | 6 | 0.000 (6) | 0.000 (6) | +0.000 |
| ReActPrivileged | qwen3.5-27b | 5 | 0.000 (5) | 0.200 (5) | +0.200 |
| ReActPrivileged | internvl3.5-8b | 4 | 0.000 (4) | 0.000 (4) | +0.000 |

## 技能调用和错误

每格为出现该情况的局数 / 已计分局数。一局可以遇到多类错误，随后仍可能成功。分类沿用仓库对技能调用最内层错误码的定义，例如 NOT_OBSERVED 归入观测，NO_PATH 归入前置条件，POLICY_FAILED 归入执行。错误码描述技能的返回状态，判断失败原因还需要结合模型选的参数和当时的场景。

| 方法 | 模型 | 执行 | 观测 | 前置条件 | 无效调用 | 其他错误 | 全局零技能调用 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 6/7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 |
| OpenLoop | qwen3.5-27b | 5/7 | 0/7 | 0/7 | 1/7 | 0/7 | 0/7 |
| OpenLoop | internvl3.5-8b | 0/7 | 1/7 | 1/7 | 0/7 | 0/7 | 0/7 |
| ReAct | qwen3.5-4b | 6/8 | 1/8 | 6/8 | 0/8 | 0/8 | 0/8 |
| ReAct | qwen3.5-27b | 7/8 | 0/8 | 5/8 | 1/8 | 0/8 | 0/8 |
| ReAct | internvl3.5-8b | 3/8 | 3/8 | 5/8 | 0/8 | 0/8 | 0/8 |
| CodeAsPolicies | qwen3.5-4b | 4/7 | 0/7 | 0/7 | 0/7 | 0/7 | 1/7 |
| CodeAsPolicies | qwen3.5-27b | 4/6 | 0/6 | 0/6 | 1/6 | 0/6 | 0/6 |
| CodeAsPolicies | internvl3.5-8b | 3/7 | 4/7 | 3/7 | 1/7 | 0/7 | 2/7 |
| SayPlan | qwen3.5-4b | 4/4 | 2/4 | 2/4 | 3/4 | 0/4 | 0/4 |
| SayPlan | qwen3.5-27b | 6/7 | 3/7 | 4/7 | 3/7 | 0/7 | 0/7 |
| SayPlan | internvl3.5-8b | 4/5 | 1/5 | 3/5 | 3/5 | 0/5 | 0/5 |
| GraphManager | qwen3.5-4b | — | — | — | — | — | — |
| GraphManager | qwen3.5-27b | — | — | — | — | — | — |
| GraphManager | internvl3.5-8b | — | — | — | — | — | — |
| ReActHint | qwen3.5-4b | 3/7 | 0/7 | 3/7 | 0/7 | 0/7 | 3/7 |
| ReActHint | qwen3.5-27b | 5/5 | 2/5 | 2/5 | 0/5 | 0/5 | 0/5 |
| ReActHint | internvl3.5-8b | 3/6 | 2/6 | 4/6 | 1/6 | 0/6 | 0/6 |
| ReActPrivileged | qwen3.5-4b | 2/6 | 3/6 | 2/6 | 0/6 | 0/6 | 1/6 |
| ReActPrivileged | qwen3.5-27b | 5/5 | 0/5 | 1/5 | 0/5 | 0/5 | 0/5 |
| ReActPrivileged | internvl3.5-8b | 3/4 | 4/4 | 3/4 | 0/4 | 0/4 | 0/4 |

## 逐次技能调用的规划正确性

使用仓库 Planning Correctness 的逐次调用判定。正确率和判定覆盖率均列出分子与分母。成功执行的调用会判为合理，即使模型交付了错误物体。控制器报错时，接口与前置条件允许的调用也可以判为合理。最后一列列出在这些合理调用中，仓库归类为底层执行失败的次数。整局是否完成任务见主实验和消融表。

| 方法 | 模型 | 合理/可判定调用 | 可判定/全部调用 | 无法判定的调用 | 执行失败/合理调用 |
| --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 11/11 | 11/11 | 0 | 4/11 |
| OpenLoop | qwen3.5-27b | 9/10 | 10/10 | 0 | 0/9 |
| OpenLoop | internvl3.5-8b | 7/7 | 7/9 | 2 | 0/7 |
| ReAct | qwen3.5-4b | 69/70 | 70/78 | 8 | 12/69 |
| ReAct | qwen3.5-27b | 133/134 | 134/155 | 21 | 30/133 |
| ReAct | internvl3.5-8b | 308/308 | 308/410 | 102 | 40/308 |
| CodeAsPolicies | qwen3.5-4b | 7/7 | 7/7 | 0 | 3/7 |
| CodeAsPolicies | qwen3.5-27b | 14/18 | 18/18 | 0 | 3/14 |
| CodeAsPolicies | internvl3.5-8b | 17/20 | 20/42 | 22 | 2/17 |
| SayPlan | qwen3.5-4b | 108/117 | 117/144 | 27 | 32/108 |
| SayPlan | qwen3.5-27b | 101/105 | 105/129 | 24 | 33/101 |
| SayPlan | internvl3.5-8b | 154/160 | 160/166 | 6 | 60/154 |
| GraphManager | qwen3.5-4b | — | — | 0 | — |
| GraphManager | qwen3.5-27b | — | — | 0 | — |
| GraphManager | internvl3.5-8b | — | — | 0 | — |
| ReActHint | qwen3.5-4b | 76/76 | 76/83 | 7 | 7/76 |
| ReActHint | qwen3.5-27b | 69/69 | 69/81 | 12 | 8/69 |
| ReActHint | internvl3.5-8b | 238/240 | 240/274 | 34 | 44/238 |
| ReActPrivileged | qwen3.5-4b | 29/29 | 29/40 | 11 | 1/29 |
| ReActPrivileged | qwen3.5-27b | 44/44 | 44/71 | 27 | 3/44 |
| ReActPrivileged | internvl3.5-8b | 132/133 | 133/198 | 65 | 9/132 |

## 推理与执行成本

Graph Manager 的一个 Harness 回合可以向模型发多次请求，其日志未给出可比的后端请求数和 token 数。前四种方法的墙钟耗时包含环境启动和排队，Graph Manager 从环境就绪起算。物理执行和同机并发都会影响这些时间。

停止原因保留方法或服务的原始分类。budget 表示用尽调用预算，service_limit 表示达到环境服务限制，time_budget 和 replan_limit 分别表示 Graph Manager 的计时或重规划上限。finish 表示模型主动报告完成，实际任务成功仍以环境判定为准。

| 方法 | 模型 | 技能调用/局 | 模型查询/局 | 输入 token/局 | 输出 token/局 | 秒/局 | 停止原因与局数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 1.57 | 1.00 | 10586 | 204 | 379.5 | `call_failed` × 6，`plan_done` × 1 |
| OpenLoop | qwen3.5-27b | 1.43 | 1.14 | 12133 | 835 | 762.9 | `call_failed` × 6，`plan_done` × 1 |
| OpenLoop | internvl3.5-8b | 1.29 | 1.00 | 13512 | 97 | 334.3 | `plan_done` × 5，`call_failed` × 2 |
| ReAct | qwen3.5-4b | 9.75 | 13.12 | 143369 | 7843 | 2275.2 | `parse_error` × 6，`service_limit` × 1，`finish` × 1 |
| ReAct | qwen3.5-27b | 19.38 | 20.38 | 227953 | 2028 | 3371.9 | `service_limit` × 5，`finish` × 3 |
| ReAct | internvl3.5-8b | 51.25 | 51.62 | 738686 | 3474 | 2324.7 | `budget` × 5，`service_limit` × 3 |
| CodeAsPolicies | qwen3.5-4b | 1.00 | 1.00 | 10691 | 92 | 322.4 | `program_done` × 7 |
| CodeAsPolicies | qwen3.5-27b | 3.00 | 1.00 | 10688 | 846 | 586.6 | `program_done` × 6 |
| CodeAsPolicies | internvl3.5-8b | 6.00 | 1.86 | 25413 | 2018 | 318.8 | `program_done` × 4，`parse_error` × 3 |
| SayPlan | qwen3.5-4b | 36.00 | 51.75 | 443288 | 6236 | 2618.1 | `budget` × 2，`parse_error` × 1，`service_limit` × 1 |
| SayPlan | qwen3.5-27b | 18.43 | 25.86 | 215718 | 2699 | 2114.8 | `finish` × 3，`parse_error` × 3，`service_limit` × 1 |
| SayPlan | internvl3.5-8b | 33.20 | 43.40 | 496399 | 3453 | 2711.1 | `budget` × 2，`parse_error` × 2，`service_limit` × 1 |
| GraphManager | qwen3.5-4b | — | — | — | — | — | — |
| GraphManager | qwen3.5-27b | — | — | — | — | — | — |
| GraphManager | internvl3.5-8b | — | — | — | — | — | — |
| ReActHint | qwen3.5-4b | 11.86 | 15.71 | 175193 | 5424 | 1229.7 | `parse_error` × 5，`service_limit` × 1，`finish` × 1 |
| ReActHint | qwen3.5-27b | 16.20 | 17.20 | 192711 | 1720 | 3329.6 | `service_limit` × 3，`finish` × 2 |
| ReActHint | internvl3.5-8b | 45.67 | 46.50 | 667014 | 3012 | 3127.5 | `service_limit` × 3，`finish` × 2，`budget` × 1 |
| ReActPrivileged | qwen3.5-4b | 6.67 | 9.67 | 106511 | 4872 | 1408.8 | `parse_error` × 4，`service_limit` × 1，`finish` × 1 |
| ReActPrivileged | qwen3.5-27b | 14.20 | 15.40 | 176608 | 1657 | 3380.4 | `service_limit` × 3，`finish` × 2 |
| ReActPrivileged | internvl3.5-8b | 49.50 | 50.00 | 725026 | 3242 | 2708.8 | `budget` × 2，`service_limit` × 2 |

## 脚本参考路线

以下各局在 sticky/benchmark 下执行任务目录预写的动作和真实物体名。三个模型栏给出同一任务、布局、种子和初始局哈希下标准 ReAct 的原生分数及最终成功判定。横线表示该模型尚无这局的判定。脚本执行错误列显示第一个本应成功却失败的技能，一条脚本路线失败时，其他动作序列仍可能可行。脚本局单独计数。

| 任务 | 布局 | 种子 | 脚本代码 | 脚本已执行/路线步数 | 脚本分数与结局 | qwen3.5-4b | qwen3.5-27b | internvl3.5-8b | 脚本执行错误 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T01_book_to_dining_table | overhang_ready | 10 | 696211a +工作树 | 7/7 | 1.0 成功 | 0.0 失败 | 1.0 成功 | 0.0 失败 | — |
| T02_stack_blocks | block_put_away__gone_toy_block | 10 | 7846509 | 8/23 | 0.0 失败 | 0.0 失败 | 0.0 失败 | 0.0 失败 | open · open kitchen_cabinet_4: no base pose can grasp the handle and ride the motion |
| T10_trash_the_can | after_dinner_clear__rubbish_leftovers | 10 | 7846509 | 13/24 | 0.0 失败 | 0.0 失败 | 0.0 失败 | 0.0 失败 | pick · carry_in: the arm stopped 0.024 m short of where it was sent |
| T19_recycling | bin_on_bookcase | 10 | 7846509 | 14/14 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | drop · tuck: the arm stopped 0.066 m short of where it was sent |
| T24_snack_for_kid | apple_on_table | 10 | 7846509 | 6/6 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | — |
