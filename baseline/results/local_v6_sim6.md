# ZenoBench v6 本地 VLM 基线 · Isaac Sim 6.0.0.1

**原生计分覆盖 200 / 24,546 局。** 当前为阶段性结果。各行先完成的布局可能不同，跨模型比较请看配对分表。

汇总时间为 2026-11-24 13:26 UTC。

Isaac Lab 适配清单 SHA-256 为 `5e09ce356754c98e3f02eeb3b5d7f931cf78d4a684758db346189976a18a6c39`。cuRobo 0.7.8，Warp 1.13.0，PyTorch 2.11.0（CUDA 13.0）。

本表是在 Isaac Sim 6.0.0.1 上独立运行的版本适配实验。仓库原协议使用 Isaac Sim 5.1。物理接触、相机渲染以及技能执行结果会受仿真版本影响。

主实验按公开 v6 批次覆盖 30 个任务、151 个设计、316 种布局，种子 10–19。每个方法和模型计划运行相同的 1,510 局，技能调用上限为 60。消融在每种布局首次出现的种子上运行，共 316 局，并与相同种子的 ReAct 配对。

主实验沿用仓库 VLM 基线方案的 sticky/benchmark，物体在搬运时固定，抓放通过物理执行。公开脚本批次在 Control 和 Action + Task 使用 benchmark，在 Task 使用带抓放修正的 sticky_snap/gt。本表末尾的脚本参考路线也按 sticky/benchmark 重新执行。

Graph Manager 只计入使用独立随机工作目录的局。旧 Harness 消息曾包含带布局名的路径，受影响的旧尝试已排除，重跑仍计入各模型原有的 1,510 局。

计分需要规划器和 Isaac Sim 同时记录相同的任务、种子、episode hash 和最终判定。实际成功率使用环境的最终 success，得分大于零和满分率另列。仿真记录中的掉落规则可能使实际成功率低于正分率。

## 主实验

| 方法 | 模型 | 已计分/计划 | 中断待重跑 | 平均分 | 平均分 95% CI | 任务成功 | 正分 | 满分 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 11/1510 | 0 | 0.000 | — | 0/11 | 0/11 | 0/11 |
| OpenLoop | qwen3.5-27b | 11/1510 | 0 | 0.000 | — | 0/11 | 0/11 | 0/11 |
| OpenLoop | internvl3.5-8b | 11/1510 | 0 | 0.000 | — | 0/11 | 0/11 | 0/11 |
| ReAct | qwen3.5-4b | 11/1510 | 0 | 0.000 | — | 0/11 | 0/11 | 0/11 |
| ReAct | qwen3.5-27b | 12/1510 | 0 | 0.083 | — | 1/12 | 1/12 | 1/12 |
| ReAct | internvl3.5-8b | 11/1510 | 0 | 0.000 | — | 0/11 | 0/11 | 0/11 |
| CodeAsPolicies | qwen3.5-4b | 11/1510 | 0 | 0.000 | — | 0/11 | 0/11 | 0/11 |
| CodeAsPolicies | qwen3.5-27b | 11/1510 | 0 | 0.091 | — | 1/11 | 1/11 | 1/11 |
| CodeAsPolicies | internvl3.5-8b | 11/1510 | 0 | 0.091 | — | 1/11 | 1/11 | 1/11 |
| SayPlan | qwen3.5-4b | 9/1510 | 0 | 0.000 | — | 0/9 | 0/9 | 0/9 |
| SayPlan | qwen3.5-27b | 8/1510 | 0 | 0.000 | — | 0/8 | 0/8 | 0/8 |
| SayPlan | internvl3.5-8b | 9/1510 | 0 | 0.000 | — | 0/9 | 0/9 | 0/9 |
| GraphManager | qwen3.5-4b | 6/1510 | 3 | 0.167 | — | 1/6 | 1/6 | 1/6 |
| GraphManager | qwen3.5-27b | 3/1510 | 1 | 0.000 | — | 0/3 | 0/3 | 0/3 |
| GraphManager | internvl3.5-8b | 5/1510 | 1 | 0.000 | — | 0/5 | 0/5 | 0/5 |

置信区间按任务内的设计聚类，重采样 2,000 次。只有全量覆盖的行给出区间。

## 按任务条件配对

每种方法取三个模型都已计分的相同任务、布局和种子。前三列按任务类别给出平均分和配对局数，接下来两列按布局中的理想选项是否可用划分。理想选项不可用时，v6 给该布局的最佳替代结果记 1.0 分。最后一列统计达到这一档且通过环境最终成功检查的局数，分母是理想选项不可用的配对局。

| 方法 | 模型 | Control | Task | Action + Task | 理想选择可用 | 理想选择不可用 | 达成布局最佳替代/理想选择不可用 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 0.000 (4) | 0.000 (4) | 0.000 (3) | 0.000 (9) | 0.000 (2) | 0/2 |
| OpenLoop | qwen3.5-27b | 0.000 (4) | 0.000 (4) | 0.000 (3) | 0.000 (9) | 0.000 (2) | 0/2 |
| OpenLoop | internvl3.5-8b | 0.000 (4) | 0.000 (4) | 0.000 (3) | 0.000 (9) | 0.000 (2) | 0/2 |
| ReAct | qwen3.5-4b | 0.000 (4) | 0.000 (4) | 0.000 (2) | 0.000 (7) | 0.000 (3) | 0/3 |
| ReAct | qwen3.5-27b | 0.250 (4) | 0.000 (4) | 0.000 (2) | 0.143 (7) | 0.000 (3) | 0/3 |
| ReAct | internvl3.5-8b | 0.000 (4) | 0.000 (4) | 0.000 (2) | 0.000 (7) | 0.000 (3) | 0/3 |
| CodeAsPolicies | qwen3.5-4b | 0.000 (4) | 0.000 (4) | 0.000 (3) | 0.000 (9) | 0.000 (2) | 0/2 |
| CodeAsPolicies | qwen3.5-27b | 0.250 (4) | 0.000 (4) | 0.000 (3) | 0.111 (9) | 0.000 (2) | 0/2 |
| CodeAsPolicies | internvl3.5-8b | 0.250 (4) | 0.000 (4) | 0.000 (3) | 0.111 (9) | 0.000 (2) | 0/2 |
| SayPlan | qwen3.5-4b | 0.000 (3) | 0.000 (3) | 0.000 (2) | 0.000 (6) | 0.000 (2) | 0/2 |
| SayPlan | qwen3.5-27b | 0.000 (3) | 0.000 (3) | 0.000 (2) | 0.000 (6) | 0.000 (2) | 0/2 |
| SayPlan | internvl3.5-8b | 0.000 (3) | 0.000 (3) | 0.000 (2) | 0.000 (6) | 0.000 (2) | 0/2 |
| GraphManager | qwen3.5-4b | 0.000 (1) | 0.000 (1) | 0.000 (1) | 0.000 (2) | 0.000 (1) | 0/1 |
| GraphManager | qwen3.5-27b | 0.000 (1) | 0.000 (1) | 0.000 (1) | 0.000 (2) | 0.000 (1) | 0/1 |
| GraphManager | internvl3.5-8b | 0.000 (1) | 0.000 (1) | 0.000 (1) | 0.000 (2) | 0.000 (1) | 0/1 |

## 提示和观测消融

| 方法 | 模型 | 已计分/计划 | 中断待重跑 | 平均分 | 平均分 95% CI | 任务成功 | 正分 | 满分 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ReActHint | qwen3.5-4b | 10/316 | 0 | 0.000 | — | 0/10 | 0/10 | 0/10 |
| ReActHint | qwen3.5-27b | 11/316 | 0 | 0.000 | — | 0/11 | 0/11 | 0/11 |
| ReActHint | internvl3.5-8b | 10/316 | 0 | 0.000 | — | 0/10 | 0/10 | 0/10 |
| ReActPrivileged | qwen3.5-4b | 10/316 | 0 | 0.060 | — | 1/10 | 1/10 | 0/10 |
| ReActPrivileged | qwen3.5-27b | 10/316 | 0 | 0.260 | — | 3/10 | 3/10 | 2/10 |
| ReActPrivileged | internvl3.5-8b | 9/316 | 0 | 0.111 | — | 1/9 | 1/9 | 1/9 |

| 消融 | 模型 | 配对数 | ReAct 平均分 | 消融平均分 | 差值 |
| --- | --- | --- | --- | --- | --- |
| ReActHint | qwen3.5-4b | 10 | 0.000 (10) | 0.000 (10) | +0.000 |
| ReActHint | qwen3.5-27b | 11 | 0.000 (11) | 0.000 (11) | +0.000 |
| ReActHint | internvl3.5-8b | 10 | 0.000 (10) | 0.000 (10) | +0.000 |
| ReActPrivileged | qwen3.5-4b | 9 | 0.000 (9) | 0.000 (9) | +0.000 |
| ReActPrivileged | qwen3.5-27b | 10 | 0.000 (10) | 0.260 (10) | +0.260 |
| ReActPrivileged | internvl3.5-8b | 9 | 0.000 (9) | 0.111 (9) | +0.111 |

## 技能调用和错误

每格为出现该情况的局数 / 已计分局数。一局可以遇到多类错误，随后仍可能成功。分类沿用仓库对技能调用最内层错误码的定义，例如 NOT_OBSERVED 归入观测，NO_PATH 归入前置条件，POLICY_FAILED 归入执行。错误码描述技能的返回状态，判断失败原因还需要结合模型选的参数和当时的场景。

| 方法 | 模型 | 执行 | 观测 | 前置条件 | 无效调用 | 其他错误 | 全局零技能调用 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 8/11 | 0/11 | 0/11 | 2/11 | 0/11 | 0/11 |
| OpenLoop | qwen3.5-27b | 6/11 | 0/11 | 0/11 | 2/11 | 0/11 | 0/11 |
| OpenLoop | internvl3.5-8b | 0/11 | 2/11 | 1/11 | 0/11 | 0/11 | 0/11 |
| ReAct | qwen3.5-4b | 8/11 | 1/11 | 6/11 | 2/11 | 0/11 | 0/11 |
| ReAct | qwen3.5-27b | 10/12 | 0/12 | 7/12 | 2/12 | 0/12 | 0/12 |
| ReAct | internvl3.5-8b | 6/11 | 4/11 | 7/11 | 0/11 | 0/11 | 0/11 |
| CodeAsPolicies | qwen3.5-4b | 4/11 | 1/11 | 0/11 | 0/11 | 0/11 | 1/11 |
| CodeAsPolicies | qwen3.5-27b | 6/11 | 1/11 | 1/11 | 2/11 | 0/11 | 0/11 |
| CodeAsPolicies | internvl3.5-8b | 3/11 | 4/11 | 3/11 | 1/11 | 0/11 | 4/11 |
| SayPlan | qwen3.5-4b | 8/9 | 4/9 | 4/9 | 7/9 | 0/9 | 0/9 |
| SayPlan | qwen3.5-27b | 6/8 | 3/8 | 4/8 | 3/8 | 0/8 | 0/8 |
| SayPlan | internvl3.5-8b | 5/9 | 2/9 | 3/9 | 3/9 | 0/9 | 0/9 |
| GraphManager | qwen3.5-4b | 5/6 | 2/6 | 3/6 | 4/6 | 0/6 | 0/6 |
| GraphManager | qwen3.5-27b | 3/3 | 0/3 | 3/3 | 1/3 | 0/3 | 0/3 |
| GraphManager | internvl3.5-8b | 1/5 | 0/5 | 1/5 | 0/5 | 0/5 | 4/5 |
| ReActHint | qwen3.5-4b | 4/10 | 1/10 | 4/10 | 2/10 | 1/10 | 3/10 |
| ReActHint | qwen3.5-27b | 9/11 | 2/11 | 6/11 | 2/11 | 0/11 | 0/11 |
| ReActHint | internvl3.5-8b | 7/10 | 2/10 | 5/10 | 2/10 | 0/10 | 0/10 |
| ReActPrivileged | qwen3.5-4b | 5/10 | 6/10 | 4/10 | 2/10 | 0/10 | 1/10 |
| ReActPrivileged | qwen3.5-27b | 9/10 | 2/10 | 5/10 | 0/10 | 0/10 | 0/10 |
| ReActPrivileged | internvl3.5-8b | 5/9 | 6/9 | 7/9 | 0/9 | 0/9 | 0/9 |

## 逐次技能调用的规划正确性

使用仓库 Planning Correctness 的逐次调用判定。正确率和判定覆盖率均列出分子与分母。成功执行的调用会判为合理，即使模型交付了错误物体。控制器报错时，接口与前置条件允许的调用也可以判为合理。最后一列列出在这些合理调用中，仓库归类为底层执行失败的次数。整局是否完成任务见主实验和消融表。

| 方法 | 模型 | 合理/可判定调用 | 可判定/全部调用 | 无法判定的调用 | 执行失败/合理调用 |
| --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 17/19 | 19/19 | 0 | 5/17 |
| OpenLoop | qwen3.5-27b | 18/20 | 20/20 | 0 | 0/18 |
| OpenLoop | internvl3.5-8b | 13/13 | 13/16 | 3 | 0/13 |
| ReAct | qwen3.5-4b | 113/121 | 121/129 | 8 | 18/113 |
| ReAct | qwen3.5-27b | 177/187 | 187/210 | 23 | 33/177 |
| ReAct | internvl3.5-8b | 455/455 | 455/585 | 130 | 47/455 |
| CodeAsPolicies | qwen3.5-4b | 13/13 | 13/14 | 1 | 3/13 |
| CodeAsPolicies | qwen3.5-27b | 27/32 | 32/35 | 3 | 4/27 |
| CodeAsPolicies | internvl3.5-8b | 22/25 | 25/47 | 22 | 2/22 |
| SayPlan | qwen3.5-4b | 166/191 | 191/224 | 33 | 39/166 |
| SayPlan | qwen3.5-27b | 102/106 | 106/130 | 24 | 33/102 |
| SayPlan | internvl3.5-8b | 202/208 | 208/215 | 7 | 72/202 |
| GraphManager | qwen3.5-4b | 70/79 | 79/84 | 5 | 12/70 |
| GraphManager | qwen3.5-27b | 19/20 | 20/23 | 3 | 7/19 |
| GraphManager | internvl3.5-8b | 3/3 | 3/4 | 1 | 0/3 |
| ReActHint | qwen3.5-4b | 134/141 | 141/156 | 15 | 8/134 |
| ReActHint | qwen3.5-27b | 122/128 | 128/144 | 16 | 13/122 |
| ReActHint | internvl3.5-8b | 371/384 | 384/430 | 46 | 76/371 |
| ReActPrivileged | qwen3.5-4b | 94/97 | 97/124 | 27 | 7/94 |
| ReActPrivileged | qwen3.5-27b | 115/116 | 116/152 | 36 | 17/115 |
| ReActPrivileged | internvl3.5-8b | 250/251 | 251/370 | 119 | 18/250 |

## 推理与执行成本

技能调用数统计从规划器进入环境的顶层契约。一个 fetch 可以在内部依次执行导航、拾取、导航和放置。Graph Manager 的一个 Harness 回合可以向模型发多次请求，其日志未给出可比的后端请求数和 token 数。前四种方法的墙钟耗时包含环境启动和排队，Graph Manager 从环境就绪起算。物理执行和同机并发都会影响这些时间。

停止原因保留方法或服务的原始分类。budget 表示用尽调用预算，service_limit 表示达到环境服务限制，time_budget 和 replan_limit 分别表示 Graph Manager 的计时或重规划上限。finish 表示模型主动报告完成，实际任务成功仍以环境判定为准。

| 方法 | 模型 | 技能调用/局 | 模型查询/局 | 输入 token/局 | 输出 token/局 | 秒/局 | 停止原因与局数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 1.73 | 1.00 | 10578 | 209 | 340.0 | `call_failed` × 10，`plan_done` × 1 |
| OpenLoop | qwen3.5-27b | 1.82 | 1.09 | 11562 | 589 | 710.1 | `call_failed` × 8，`plan_done` × 3 |
| OpenLoop | internvl3.5-8b | 1.45 | 1.00 | 13504 | 94 | 364.8 | `plan_done` × 8，`call_failed` × 3 |
| ReAct | qwen3.5-4b | 11.73 | 15.64 | 171934 | 10726 | 2118.9 | `parse_error` × 7，`service_limit` × 2，`finish` × 2 |
| ReAct | qwen3.5-27b | 17.50 | 18.50 | 206623 | 1750 | 2765.7 | `finish` × 7，`service_limit` × 5 |
| ReAct | internvl3.5-8b | 53.18 | 53.64 | 766828 | 3611 | 2416.4 | `budget` × 6，`service_limit` × 3，`finish` × 2 |
| CodeAsPolicies | qwen3.5-4b | 1.27 | 1.00 | 10683 | 85 | 368.8 | `program_done` × 11 |
| CodeAsPolicies | qwen3.5-27b | 3.18 | 1.09 | 11663 | 724 | 999.2 | `program_done` × 9，`service_limit` × 1，`program_error` × 1 |
| CodeAsPolicies | internvl3.5-8b | 4.27 | 1.73 | 23596 | 2798 | 431.8 | `program_done` × 6，`parse_error` × 5 |
| SayPlan | qwen3.5-4b | 24.89 | 38.11 | 320690 | 4326 | 2706.1 | `service_limit` × 4，`budget` × 2，`parse_error` × 1，`finish` × 1，`search_budget` × 1 |
| SayPlan | qwen3.5-27b | 16.25 | 23.88 | 198576 | 2420 | 1902.0 | `finish` × 3，`parse_error` × 3，`service_limit` × 1，`search_budget` × 1 |
| SayPlan | internvl3.5-8b | 23.89 | 37.56 | 425806 | 2719 | 2186.1 | `parse_error` × 3，`budget` × 2，`service_limit` × 2，`search_budget` × 2 |
| GraphManager | qwen3.5-4b | 14.00 | — | — | — | 888.1 | `replan_limit` × 4，`model_finished` × 2 |
| GraphManager | qwen3.5-27b | 7.67 | — | — | — | 1253.2 | `replan_limit` × 3 |
| GraphManager | internvl3.5-8b | 0.80 | — | — | — | 512.6 | `model_gave_up` × 5 |
| ReActHint | qwen3.5-4b | 15.60 | 19.90 | 222776 | 8828 | 1048.3 | `parse_error` × 6，`finish` × 2，`service_limit` × 1，`budget` × 1 |
| ReActHint | qwen3.5-27b | 13.09 | 14.09 | 157163 | 1351 | 2715.7 | `finish` × 6，`service_limit` × 5 |
| ReActHint | internvl3.5-8b | 43.00 | 43.80 | 625320 | 2900 | 2765.5 | `finish` × 4，`service_limit` × 4，`budget` × 2 |
| ReActPrivileged | qwen3.5-4b | 12.40 | 15.70 | 176610 | 7722 | 1944.5 | `parse_error` × 5，`finish` × 3，`service_limit` × 2 |
| ReActPrivileged | qwen3.5-27b | 15.20 | 16.40 | 188002 | 2272 | 2903.9 | `finish` × 6，`service_limit` × 4 |
| ReActPrivileged | internvl3.5-8b | 41.11 | 41.67 | 602784 | 2727 | 2377.7 | `service_limit` × 4，`budget` × 4，`finish` × 1 |

## 脚本参考路线

以下各局在 sticky/benchmark 下执行任务目录预写的动作和真实物体名。三个模型栏给出同一任务、布局、种子和初始局哈希下标准 ReAct 的原生分数及最终成功判定。横线表示该模型尚无这局的判定。脚本执行错误列显示第一个本应成功却失败的技能，一条脚本路线失败时，其他动作序列仍可能可行。脚本局单独计数。

| 任务 | 布局 | 种子 | 脚本代码 | 脚本已执行/路线步数 | 脚本分数与结局 | qwen3.5-4b | qwen3.5-27b | internvl3.5-8b | 脚本执行错误 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T01_book_to_dining_table | overhang_ready | 10 | 696211a +工作树 | 7/7 | 1.0 成功 | 0.0 失败 | 1.0 成功 | 0.0 失败 | — |
| T02_stack_blocks | block_put_away__gone_toy_block | 10 | 7846509 | 8/23 | 0.0 失败 | 0.0 失败 | 0.0 失败 | 0.0 失败 | open · open kitchen_cabinet_4: no base pose can grasp the handle and ride the motion |
| T09_tomato_soup | lid_on_spoon_away | 10 | 7846509 | 23/23 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | — |
| T10_trash_the_can | after_dinner_clear__rubbish_leftovers | 10 | 7846509 | 13/24 | 0.0 失败 | 0.0 失败 | 0.0 失败 | 0.0 失败 | pick · carry_in: the arm stopped 0.024 m short of where it was sent |
| T12_tidy_toys | bins_capacity__half_bin_and_tray_duck_dining | 19 | 7846509 | 15/15 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | — |
| T19_recycling | bin_on_bookcase | 10 | 7846509 | 14/14 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | drop · tuck: the arm stopped 0.066 m short of where it was sent |
| T20_juice_back_to_table | bottle_on_cabinet | 10 | 7846509 | 6/6 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | — |
| T24_snack_for_kid | apple_on_table | 10 | 7846509 | 6/6 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | — |
| T28_cup_to_bedside | already_there__wrong_cup | 10 | 7846509 | 8/8 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | — |
