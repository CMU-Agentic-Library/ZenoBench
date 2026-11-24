# ZenoBench v6 本地 VLM 基线 · Isaac Sim 6.0.0.1

**原生计分覆盖 33 / 24,546 局。** 当前为阶段性结果。各行先完成的布局可能不同，跨模型比较请看配对分表。

汇总时间为 2026-11-24 10:10 UTC。

Isaac Lab 适配清单 SHA-256 为 `5e09ce356754c98e3f02eeb3b5d7f931cf78d4a684758db346189976a18a6c39`。cuRobo 0.7.8，Warp 1.13.0，PyTorch 2.11.0（CUDA 13.0）。

本表是在 Isaac Sim 6.0.0.1 上独立运行的版本适配实验。仓库原协议使用 Isaac Sim 5.1。物理接触、相机渲染以及技能执行结果会受仿真版本影响。

主实验按公开 v6 批次覆盖 30 个任务、151 个设计、316 种布局，种子 10–19。每个方法和模型计划运行相同的 1,510 局，技能调用上限为 60。消融在每种布局首次出现的种子上运行，共 316 局，并与相同种子的 ReAct 配对。

计分需要规划器和 Isaac Sim 同时记录相同的任务、种子、episode hash 和最终判定。实际成功率使用环境的最终 success，得分大于零和满分率另列。仿真记录中的掉落规则可能使实际成功率低于正分率。

## 主实验

| 方法 | 模型 | 已计分/计划 | 中断待重跑 | 平均分 | 平均分 95% CI | 任务成功 | 正分 | 满分 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 4/1510 | 0 | 0.000 | — | 0/4 | 0/4 | 0/4 |
| OpenLoop | qwen3.5-27b | 3/1510 | 0 | 0.000 | — | 0/3 | 0/3 | 0/3 |
| OpenLoop | internvl3.5-8b | 4/1510 | 0 | 0.000 | — | 0/4 | 0/4 | 0/4 |
| ReAct | qwen3.5-4b | 2/1510 | 0 | 0.000 | — | 0/2 | 0/2 | 0/2 |
| ReAct | qwen3.5-27b | 1/1510 | 0 | 0.000 | — | 0/1 | 0/1 | 0/1 |
| ReAct | internvl3.5-8b | 2/1510 | 0 | 0.000 | — | 0/2 | 0/2 | 0/2 |
| CodeAsPolicies | qwen3.5-4b | 3/1510 | 0 | 0.000 | — | 0/3 | 0/3 | 0/3 |
| CodeAsPolicies | qwen3.5-27b | 2/1510 | 0 | 0.000 | — | 0/2 | 0/2 | 0/2 |
| CodeAsPolicies | internvl3.5-8b | 2/1510 | 0 | 0.000 | — | 0/2 | 0/2 | 0/2 |
| SayPlan | qwen3.5-4b | 2/1510 | 0 | 0.000 | — | 0/2 | 0/2 | 0/2 |
| SayPlan | qwen3.5-27b | 1/1510 | 0 | 0.000 | — | 0/1 | 0/1 | 0/1 |
| SayPlan | internvl3.5-8b | 2/1510 | 0 | 0.000 | — | 0/2 | 0/2 | 0/2 |
| GraphManager | qwen3.5-4b | 1/1510 | 0 | 0.000 | — | 0/1 | 0/1 | 0/1 |
| GraphManager | qwen3.5-27b | 1/1510 | 0 | 0.000 | — | 0/1 | 0/1 | 0/1 |
| GraphManager | internvl3.5-8b | 1/1510 | 0 | 0.000 | — | 0/1 | 0/1 | 0/1 |

置信区间按任务内的设计聚类，重采样 2,000 次。只有全量覆盖的行给出区间。

## 按任务条件配对

每种方法取三个模型都已计分的相同任务、布局和种子。前三列按任务类别给出平均分和配对局数，接下来两列按布局中的理想选项是否可用划分。理想选项不可用时，v6 给该布局的最佳替代结果记 1.0 分。最后一列统计达到这一档且通过环境最终成功检查的局数，分母是理想选项不可用的配对局。

| 方法 | 模型 | Control | Task | Action + Task | 理想选择可用 | 理想选择不可用 | 达成布局最佳替代/理想选择不可用 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 0.000 (1) | 0.000 (1) | 0.000 (1) | 0.000 (2) | 0.000 (1) | 0/1 |
| OpenLoop | qwen3.5-27b | 0.000 (1) | 0.000 (1) | 0.000 (1) | 0.000 (2) | 0.000 (1) | 0/1 |
| OpenLoop | internvl3.5-8b | 0.000 (1) | 0.000 (1) | 0.000 (1) | 0.000 (2) | 0.000 (1) | 0/1 |
| ReAct | qwen3.5-4b | 0.000 (1) | — | — | 0.000 (1) | — | — |
| ReAct | qwen3.5-27b | 0.000 (1) | — | — | 0.000 (1) | — | — |
| ReAct | internvl3.5-8b | 0.000 (1) | — | — | 0.000 (1) | — | — |
| CodeAsPolicies | qwen3.5-4b | 0.000 (1) | 0.000 (1) | — | 0.000 (2) | — | — |
| CodeAsPolicies | qwen3.5-27b | 0.000 (1) | 0.000 (1) | — | 0.000 (2) | — | — |
| CodeAsPolicies | internvl3.5-8b | 0.000 (1) | 0.000 (1) | — | 0.000 (2) | — | — |
| SayPlan | qwen3.5-4b | — | 0.000 (1) | — | 0.000 (1) | — | — |
| SayPlan | qwen3.5-27b | — | 0.000 (1) | — | 0.000 (1) | — | — |
| SayPlan | internvl3.5-8b | — | 0.000 (1) | — | 0.000 (1) | — | — |
| GraphManager | qwen3.5-4b | 0.000 (1) | — | — | 0.000 (1) | — | — |
| GraphManager | qwen3.5-27b | 0.000 (1) | — | — | 0.000 (1) | — | — |
| GraphManager | internvl3.5-8b | 0.000 (1) | — | — | 0.000 (1) | — | — |

## 提示和观测消融

| 方法 | 模型 | 已计分/计划 | 中断待重跑 | 平均分 | 平均分 95% CI | 任务成功 | 正分 | 满分 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ReActHint | qwen3.5-4b | 1/316 | 0 | 0.000 | — | 0/1 | 0/1 | 0/1 |
| ReActHint | qwen3.5-27b | 0/316 | 0 | — | — | — | — | — |
| ReActHint | internvl3.5-8b | 0/316 | 0 | — | — | — | — | — |
| ReActPrivileged | qwen3.5-4b | 1/316 | 0 | 0.000 | — | 0/1 | 0/1 | 0/1 |
| ReActPrivileged | qwen3.5-27b | 0/316 | 0 | — | — | — | — | — |
| ReActPrivileged | internvl3.5-8b | 0/316 | 0 | — | — | — | — | — |

| 消融 | 模型 | 配对数 | ReAct 平均分 | 消融平均分 | 差值 |
| --- | --- | --- | --- | --- | --- |
| ReActHint | qwen3.5-4b | 1 | 0.000 (1) | 0.000 (1) | +0.000 |
| ReActHint | qwen3.5-27b | 0 | — | — | — |
| ReActHint | internvl3.5-8b | 0 | — | — | — |
| ReActPrivileged | qwen3.5-4b | 1 | 0.000 (1) | 0.000 (1) | +0.000 |
| ReActPrivileged | qwen3.5-27b | 0 | — | — | — |
| ReActPrivileged | internvl3.5-8b | 0 | — | — | — |

## 技能调用和错误

每格为出现该情况的局数 / 已计分局数。一局可以遇到多类错误，随后仍可能成功。分类沿用仓库对技能调用最内层错误码的定义，例如 NOT_OBSERVED 归入观测，NO_PATH 归入前置条件，POLICY_FAILED 归入执行。错误码描述技能的返回状态，判断失败原因还需要结合模型选的参数和当时的场景。

| 方法 | 模型 | 执行 | 观测 | 前置条件 | 无效调用 | 其他错误 | 全局零技能调用 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 3/4 | 0/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| OpenLoop | qwen3.5-27b | 2/3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| OpenLoop | internvl3.5-8b | 0/4 | 1/4 | 0/4 | 0/4 | 0/4 | 0/4 |
| ReAct | qwen3.5-4b | 2/2 | 1/2 | 2/2 | 0/2 | 0/2 | 0/2 |
| ReAct | qwen3.5-27b | 1/1 | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 |
| ReAct | internvl3.5-8b | 1/2 | 1/2 | 1/2 | 0/2 | 0/2 | 0/2 |
| CodeAsPolicies | qwen3.5-4b | 1/3 | 0/3 | 0/3 | 0/3 | 0/3 | 1/3 |
| CodeAsPolicies | qwen3.5-27b | 2/2 | 0/2 | 0/2 | 0/2 | 0/2 | 0/2 |
| CodeAsPolicies | internvl3.5-8b | 1/2 | 1/2 | 0/2 | 0/2 | 0/2 | 1/2 |
| SayPlan | qwen3.5-4b | 2/2 | 1/2 | 0/2 | 1/2 | 0/2 | 0/2 |
| SayPlan | qwen3.5-27b | 1/1 | 1/1 | 1/1 | 1/1 | 0/1 | 0/1 |
| SayPlan | internvl3.5-8b | 2/2 | 0/2 | 2/2 | 2/2 | 0/2 | 0/2 |
| GraphManager | qwen3.5-4b | 1/1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| GraphManager | qwen3.5-27b | 1/1 | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 |
| GraphManager | internvl3.5-8b | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 | 1/1 |
| ReActHint | qwen3.5-4b | 0/1 | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 |
| ReActHint | qwen3.5-27b | — | — | — | — | — | — |
| ReActHint | internvl3.5-8b | — | — | — | — | — | — |
| ReActPrivileged | qwen3.5-4b | 1/1 | 1/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| ReActPrivileged | qwen3.5-27b | — | — | — | — | — | — |
| ReActPrivileged | internvl3.5-8b | — | — | — | — | — | — |

## 推理与执行成本

Graph Manager 的一个 Harness 回合可以向模型发多次请求，其日志未给出可比的后端请求数和 token 数。前四种方法的墙钟耗时包含环境启动和排队，Graph Manager 从环境就绪起算。物理执行和同机并发都会影响这些时间。

| 方法 | 模型 | 技能调用/局 | 模型查询/局 | 输入 token/局 | 输出 token/局 | 秒/局 |
| --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 1.75 | 1.00 | 10561 | 154 | 269.4 |
| OpenLoop | qwen3.5-27b | 1.33 | 1.00 | 10599 | 252 | 482.0 |
| OpenLoop | internvl3.5-8b | 1.25 | 1.00 | 13487 | 113 | 361.1 |
| ReAct | qwen3.5-4b | 9.50 | 13.50 | 147976 | 10991 | 2505.6 |
| ReAct | qwen3.5-27b | 14.00 | 15.00 | 164001 | 1086 | 2742.7 |
| ReAct | internvl3.5-8b | 60.00 | 60.00 | 867266 | 4336 | 2300.7 |
| CodeAsPolicies | qwen3.5-4b | 0.67 | 1.00 | 10645 | 56 | 348.0 |
| CodeAsPolicies | qwen3.5-27b | 2.50 | 1.00 | 10691 | 1272 | 984.6 |
| CodeAsPolicies | internvl3.5-8b | 3.50 | 1.50 | 20436 | 4218 | 175.2 |
| SayPlan | qwen3.5-4b | 12.00 | 18.50 | 150680 | 2029 | 2208.6 |
| SayPlan | qwen3.5-27b | 56.00 | 55.00 | 471343 | 6420 | 3390.1 |
| SayPlan | internvl3.5-8b | 60.00 | 67.50 | 781163 | 6202 | 3866.8 |
| GraphManager | qwen3.5-4b | 6.00 | — | — | — | 757.0 |
| GraphManager | qwen3.5-27b | 9.00 | — | — | — | 958.6 |
| GraphManager | internvl3.5-8b | 0.00 | — | — | — | 186.1 |
| ReActHint | qwen3.5-4b | 7.00 | 12.00 | 131430 | 5824 | 349.0 |
| ReActHint | qwen3.5-27b | — | — | — | — | — |
| ReActHint | internvl3.5-8b | — | — | — | — | — |
| ReActPrivileged | qwen3.5-4b | 6.00 | 10.00 | 112022 | 6948 | 1882.6 |
| ReActPrivileged | qwen3.5-27b | — | — | — | — | — |
| ReActPrivileged | internvl3.5-8b | — | — | — | — | — |

## 脚本参考路线

以下各局在 sticky/benchmark 下执行任务目录预写的动作和真实物体名。报告记录原生分数及第一个本应成功却失败的技能。参考路线的覆盖数单独统计。

| 任务 | 布局 | 种子 | 代码 | 已执行/路线步数 | 任务结局 | 原生分数 | 执行错误 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T01_book_to_dining_table | overhang_ready | 10 | 696211a +工作树 | 7/7 | 成功 | 1.0 | — |
| T02_stack_blocks | block_put_away__gone_toy_block | 10 | 7846509 | 8/23 | 失败 | 0.0 | open · open kitchen_cabinet_4: no base pose can grasp the handle and ride the motion |
| T10_trash_the_can | after_dinner_clear__rubbish_leftovers | 10 | 7846509 | 13/24 | 失败 | 0.0 | pick · carry_in: the arm stopped 0.024 m short of where it was sent |
| T24_snack_for_kid | apple_on_table | 10 | 7846509 | 6/6 | 成功 | 1.0 | — |
