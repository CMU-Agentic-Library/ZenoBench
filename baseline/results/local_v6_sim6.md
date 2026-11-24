# ZenoBench v6 本地 VLM 基线 · Isaac Sim 6.0.0.1

**原生计分覆盖 81 / 24,546 局。** 当前为阶段性结果。各行先完成的布局可能不同，跨模型比较请看配对分表。

汇总时间为 2026-11-24 11:18 UTC。

Isaac Lab 适配清单 SHA-256 为 `5e09ce356754c98e3f02eeb3b5d7f931cf78d4a684758db346189976a18a6c39`。cuRobo 0.7.8，Warp 1.13.0，PyTorch 2.11.0（CUDA 13.0）。

本表是在 Isaac Sim 6.0.0.1 上独立运行的版本适配实验。仓库原协议使用 Isaac Sim 5.1。物理接触、相机渲染以及技能执行结果会受仿真版本影响。

主实验按公开 v6 批次覆盖 30 个任务、151 个设计、316 种布局，种子 10–19。每个方法和模型计划运行相同的 1,510 局，技能调用上限为 60。消融在每种布局首次出现的种子上运行，共 316 局，并与相同种子的 ReAct 配对。

计分需要规划器和 Isaac Sim 同时记录相同的任务、种子、episode hash 和最终判定。实际成功率使用环境的最终 success，得分大于零和满分率另列。仿真记录中的掉落规则可能使实际成功率低于正分率。

## 主实验

| 方法 | 模型 | 已计分/计划 | 中断待重跑 | 平均分 | 平均分 95% CI | 任务成功 | 正分 | 满分 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 5/1510 | 0 | 0.000 | — | 0/5 | 0/5 | 0/5 |
| OpenLoop | qwen3.5-27b | 4/1510 | 0 | 0.000 | — | 0/4 | 0/4 | 0/4 |
| OpenLoop | internvl3.5-8b | 5/1510 | 0 | 0.000 | — | 0/5 | 0/5 | 0/5 |
| ReAct | qwen3.5-4b | 5/1510 | 0 | 0.000 | — | 0/5 | 0/5 | 0/5 |
| ReAct | qwen3.5-27b | 3/1510 | 0 | 0.000 | — | 0/3 | 0/3 | 0/3 |
| ReAct | internvl3.5-8b | 5/1510 | 0 | 0.000 | — | 0/5 | 0/5 | 0/5 |
| CodeAsPolicies | qwen3.5-4b | 5/1510 | 0 | 0.000 | — | 0/5 | 0/5 | 0/5 |
| CodeAsPolicies | qwen3.5-27b | 4/1510 | 0 | 0.000 | — | 0/4 | 0/4 | 0/4 |
| CodeAsPolicies | internvl3.5-8b | 5/1510 | 0 | 0.000 | — | 0/5 | 0/5 | 0/5 |
| SayPlan | qwen3.5-4b | 3/1510 | 0 | 0.000 | — | 0/3 | 0/3 | 0/3 |
| SayPlan | qwen3.5-27b | 4/1510 | 0 | 0.000 | — | 0/4 | 0/4 | 0/4 |
| SayPlan | internvl3.5-8b | 4/1510 | 0 | 0.000 | — | 0/4 | 0/4 | 0/4 |
| GraphManager | qwen3.5-4b | 4/1510 | 0 | 0.000 | — | 0/4 | 0/4 | 0/4 |
| GraphManager | qwen3.5-27b | 4/1510 | 0 | 0.000 | — | 0/4 | 0/4 | 0/4 |
| GraphManager | internvl3.5-8b | 4/1510 | 0 | 0.000 | — | 0/4 | 0/4 | 0/4 |

置信区间按任务内的设计聚类，重采样 2,000 次。只有全量覆盖的行给出区间。

## 按任务条件配对

每种方法取三个模型都已计分的相同任务、布局和种子。前三列按任务类别给出平均分和配对局数，接下来两列按布局中的理想选项是否可用划分。理想选项不可用时，v6 给该布局的最佳替代结果记 1.0 分。最后一列统计达到这一档且通过环境最终成功检查的局数，分母是理想选项不可用的配对局。

| 方法 | 模型 | Control | Task | Action + Task | 理想选择可用 | 理想选择不可用 | 达成布局最佳替代/理想选择不可用 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 0.000 (2) | 0.000 (1) | 0.000 (1) | 0.000 (3) | 0.000 (1) | 0/1 |
| OpenLoop | qwen3.5-27b | 0.000 (2) | 0.000 (1) | 0.000 (1) | 0.000 (3) | 0.000 (1) | 0/1 |
| OpenLoop | internvl3.5-8b | 0.000 (2) | 0.000 (1) | 0.000 (1) | 0.000 (3) | 0.000 (1) | 0/1 |
| ReAct | qwen3.5-4b | 0.000 (1) | 0.000 (2) | — | 0.000 (2) | 0.000 (1) | 0/1 |
| ReAct | qwen3.5-27b | 0.000 (1) | 0.000 (2) | — | 0.000 (2) | 0.000 (1) | 0/1 |
| ReAct | internvl3.5-8b | 0.000 (1) | 0.000 (2) | — | 0.000 (2) | 0.000 (1) | 0/1 |
| CodeAsPolicies | qwen3.5-4b | 0.000 (2) | 0.000 (1) | 0.000 (1) | 0.000 (3) | 0.000 (1) | 0/1 |
| CodeAsPolicies | qwen3.5-27b | 0.000 (2) | 0.000 (1) | 0.000 (1) | 0.000 (3) | 0.000 (1) | 0/1 |
| CodeAsPolicies | internvl3.5-8b | 0.000 (2) | 0.000 (1) | 0.000 (1) | 0.000 (3) | 0.000 (1) | 0/1 |
| SayPlan | qwen3.5-4b | 0.000 (1) | 0.000 (1) | 0.000 (1) | 0.000 (2) | 0.000 (1) | 0/1 |
| SayPlan | qwen3.5-27b | 0.000 (1) | 0.000 (1) | 0.000 (1) | 0.000 (2) | 0.000 (1) | 0/1 |
| SayPlan | internvl3.5-8b | 0.000 (1) | 0.000 (1) | 0.000 (1) | 0.000 (2) | 0.000 (1) | 0/1 |
| GraphManager | qwen3.5-4b | 0.000 (2) | 0.000 (1) | 0.000 (1) | 0.000 (3) | 0.000 (1) | 0/1 |
| GraphManager | qwen3.5-27b | 0.000 (2) | 0.000 (1) | 0.000 (1) | 0.000 (3) | 0.000 (1) | 0/1 |
| GraphManager | internvl3.5-8b | 0.000 (2) | 0.000 (1) | 0.000 (1) | 0.000 (3) | 0.000 (1) | 0/1 |

## 提示和观测消融

| 方法 | 模型 | 已计分/计划 | 中断待重跑 | 平均分 | 平均分 95% CI | 任务成功 | 正分 | 满分 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ReActHint | qwen3.5-4b | 4/316 | 0 | 0.000 | — | 0/4 | 0/4 | 0/4 |
| ReActHint | qwen3.5-27b | 2/316 | 0 | 0.000 | — | 0/2 | 0/2 | 0/2 |
| ReActHint | internvl3.5-8b | 2/316 | 0 | 0.000 | — | 0/2 | 0/2 | 0/2 |
| ReActPrivileged | qwen3.5-4b | 4/316 | 0 | 0.000 | — | 0/4 | 0/4 | 0/4 |
| ReActPrivileged | qwen3.5-27b | 2/316 | 0 | 0.500 | — | 1/2 | 1/2 | 1/2 |
| ReActPrivileged | internvl3.5-8b | 3/316 | 0 | 0.000 | — | 0/3 | 0/3 | 0/3 |

| 消融 | 模型 | 配对数 | ReAct 平均分 | 消融平均分 | 差值 |
| --- | --- | --- | --- | --- | --- |
| ReActHint | qwen3.5-4b | 4 | 0.000 (4) | 0.000 (4) | +0.000 |
| ReActHint | qwen3.5-27b | 2 | 0.000 (2) | 0.000 (2) | +0.000 |
| ReActHint | internvl3.5-8b | 2 | 0.000 (2) | 0.000 (2) | +0.000 |
| ReActPrivileged | qwen3.5-4b | 4 | 0.000 (4) | 0.000 (4) | +0.000 |
| ReActPrivileged | qwen3.5-27b | 2 | 0.000 (2) | 0.500 (2) | +0.500 |
| ReActPrivileged | internvl3.5-8b | 3 | 0.000 (3) | 0.000 (3) | +0.000 |

## 技能调用和错误

每格为出现该情况的局数 / 已计分局数。一局可以遇到多类错误，随后仍可能成功。分类沿用仓库对技能调用最内层错误码的定义，例如 NOT_OBSERVED 归入观测，NO_PATH 归入前置条件，POLICY_FAILED 归入执行。错误码描述技能的返回状态，判断失败原因还需要结合模型选的参数和当时的场景。

| 方法 | 模型 | 执行 | 观测 | 前置条件 | 无效调用 | 其他错误 | 全局零技能调用 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 4/5 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| OpenLoop | qwen3.5-27b | 3/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| OpenLoop | internvl3.5-8b | 0/5 | 1/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| ReAct | qwen3.5-4b | 4/5 | 1/5 | 3/5 | 0/5 | 0/5 | 0/5 |
| ReAct | qwen3.5-27b | 3/3 | 0/3 | 3/3 | 0/3 | 0/3 | 0/3 |
| ReAct | internvl3.5-8b | 2/5 | 3/5 | 3/5 | 0/5 | 0/5 | 0/5 |
| CodeAsPolicies | qwen3.5-4b | 2/5 | 0/5 | 0/5 | 0/5 | 0/5 | 1/5 |
| CodeAsPolicies | qwen3.5-27b | 3/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| CodeAsPolicies | internvl3.5-8b | 2/5 | 3/5 | 2/5 | 0/5 | 0/5 | 2/5 |
| SayPlan | qwen3.5-4b | 3/3 | 1/3 | 1/3 | 2/3 | 0/3 | 0/3 |
| SayPlan | qwen3.5-27b | 4/4 | 3/4 | 2/4 | 1/4 | 0/4 | 0/4 |
| SayPlan | internvl3.5-8b | 3/4 | 1/4 | 3/4 | 2/4 | 0/4 | 0/4 |
| GraphManager | qwen3.5-4b | 3/4 | 1/4 | 1/4 | 2/4 | 0/4 | 0/4 |
| GraphManager | qwen3.5-27b | 4/4 | 0/4 | 1/4 | 0/4 | 0/4 | 0/4 |
| GraphManager | internvl3.5-8b | 0/4 | 0/4 | 0/4 | 1/4 | 0/4 | 3/4 |
| ReActHint | qwen3.5-4b | 1/4 | 0/4 | 1/4 | 0/4 | 0/4 | 2/4 |
| ReActHint | qwen3.5-27b | 2/2 | 0/2 | 1/2 | 0/2 | 0/2 | 0/2 |
| ReActHint | internvl3.5-8b | 1/2 | 1/2 | 1/2 | 1/2 | 0/2 | 0/2 |
| ReActPrivileged | qwen3.5-4b | 1/4 | 2/4 | 2/4 | 0/4 | 0/4 | 0/4 |
| ReActPrivileged | qwen3.5-27b | 2/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| ReActPrivileged | internvl3.5-8b | 3/3 | 3/3 | 3/3 | 0/3 | 0/3 | 0/3 |

## 推理与执行成本

Graph Manager 的一个 Harness 回合可以向模型发多次请求，其日志未给出可比的后端请求数和 token 数。前四种方法的墙钟耗时包含环境启动和排队，Graph Manager 从环境就绪起算。物理执行和同机并发都会影响这些时间。

停止原因保留方法或服务的原始分类。budget 表示用尽调用预算，service_limit 表示达到环境服务限制，time_budget 和 replan_limit 分别表示 Graph Manager 的计时或重规划上限。finish 表示模型主动报告完成，实际任务成功仍以环境判定为准。

| 方法 | 模型 | 技能调用/局 | 模型查询/局 | 输入 token/局 | 输出 token/局 | 秒/局 | 停止原因与局数 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 1.60 | 1.00 | 10570 | 205 | 239.4 | `call_failed` × 4，`plan_done` × 1 |
| OpenLoop | qwen3.5-27b | 1.75 | 1.00 | 10561 | 227 | 605.2 | `call_failed` × 3，`plan_done` × 1 |
| OpenLoop | internvl3.5-8b | 1.20 | 1.00 | 13496 | 103 | 321.7 | `plan_done` × 4，`call_failed` × 1 |
| ReAct | qwen3.5-4b | 9.00 | 12.60 | 137454 | 7495 | 2631.4 | `parse_error` × 4，`service_limit` × 1 |
| ReAct | qwen3.5-27b | 35.33 | 36.33 | 409713 | 3506 | 3687.0 | `service_limit` × 2，`finish` × 1 |
| ReAct | internvl3.5-8b | 53.80 | 54.20 | 778345 | 3668 | 2625.6 | `budget` × 3，`service_limit` × 2 |
| CodeAsPolicies | qwen3.5-4b | 1.00 | 1.00 | 10675 | 94 | 368.2 | `program_done` × 5 |
| CodeAsPolicies | qwen3.5-27b | 2.50 | 1.00 | 10666 | 976 | 774.8 | `program_done` × 4 |
| CodeAsPolicies | internvl3.5-8b | 5.40 | 1.80 | 24684 | 2684 | 332.2 | `program_done` × 3，`parse_error` × 2 |
| SayPlan | qwen3.5-4b | 28.00 | 35.67 | 304674 | 4413 | 2220.0 | `parse_error` × 1，`service_limit` × 1，`budget` × 1 |
| SayPlan | qwen3.5-27b | 26.75 | 33.75 | 284685 | 3773 | 2421.9 | `parse_error` × 2，`service_limit` × 1，`finish` × 1 |
| SayPlan | internvl3.5-8b | 35.75 | 45.50 | 521877 | 3767 | 2389.1 | `budget` × 2，`parse_error` × 2 |
| GraphManager | qwen3.5-4b | 7.50 | — | — | — | 606.5 | `replan_limit` × 4 |
| GraphManager | qwen3.5-27b | 6.50 | — | — | — | 1543.5 | `replan_limit` × 2，`time_budget` × 2 |
| GraphManager | internvl3.5-8b | 1.50 | — | — | — | 465.0 | `model_gave_up` × 4 |
| ReActHint | qwen3.5-4b | 3.00 | 6.00 | 65028 | 1773 | 1226.3 | `parse_error` × 3，`service_limit` × 1 |
| ReActHint | qwen3.5-27b | 16.00 | 17.00 | 188142 | 1452 | 1974.9 | `finish` × 2 |
| ReActHint | internvl3.5-8b | 36.00 | 37.00 | 534280 | 2526 | 3015.7 | `finish` × 2 |
| ReActPrivileged | qwen3.5-4b | 6.50 | 9.75 | 107423 | 4991 | 1074.4 | `parse_error` × 3，`finish` × 1 |
| ReActPrivileged | qwen3.5-27b | 5.00 | 6.50 | 71612 | 644 | 2780.2 | `finish` × 1，`service_limit` × 1 |
| ReActPrivileged | internvl3.5-8b | 48.33 | 48.67 | 708038 | 3277 | 2258.7 | `budget` × 2，`service_limit` × 1 |

## 脚本参考路线

以下各局在 sticky/benchmark 下执行任务目录预写的动作和真实物体名。报告记录原生分数及第一个本应成功却失败的技能。参考路线的覆盖数单独统计。

| 任务 | 布局 | 种子 | 代码 | 已执行/路线步数 | 任务结局 | 原生分数 | 执行错误 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T01_book_to_dining_table | overhang_ready | 10 | 696211a +工作树 | 7/7 | 成功 | 1.0 | — |
| T02_stack_blocks | block_put_away__gone_toy_block | 10 | 7846509 | 8/23 | 失败 | 0.0 | open · open kitchen_cabinet_4: no base pose can grasp the handle and ride the motion |
| T10_trash_the_can | after_dinner_clear__rubbish_leftovers | 10 | 7846509 | 13/24 | 失败 | 0.0 | pick · carry_in: the arm stopped 0.024 m short of where it was sent |
| T24_snack_for_kid | apple_on_table | 10 | 7846509 | 6/6 | 成功 | 1.0 | — |
