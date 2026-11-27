# ZenoBench v6 本地 VLM 基线 · Isaac Sim 6.0.0.1

**原生计分覆盖 253 / 24,546 局。** 本轮实验已于 2026-11-24 22:18（北京时间）按要求终止。各行覆盖的布局不同，跨模型比较请看配对分表。尚未产生原生判定的局未计分。

汇总时间为 2026-11-24 14:19 UTC。

Isaac Lab 适配清单 SHA-256 为 `5e09ce356754c98e3f02eeb3b5d7f931cf78d4a684758db346189976a18a6c39`。cuRobo 0.7.8，Warp 1.13.0，PyTorch 2.11.0（CUDA 13.0）。

本表是在 Isaac Sim 6.0.0.1 上独立运行的版本适配实验。仓库原协议使用 Isaac Sim 5.1。物理接触、相机渲染以及技能执行结果会受仿真版本影响。

主实验按公开 v6 批次覆盖 30 个任务、151 个设计、316 种布局，种子 10–19。每个方法和模型计划运行相同的 1,510 局，技能调用上限为 60。消融在每种布局首次出现的种子上运行，共 316 局，并与相同种子的 ReAct 配对。

主实验沿用仓库 VLM 基线方案的 sticky/benchmark，物体在搬运时固定，抓放通过物理执行。公开脚本批次在 Control 和 Action + Task 使用 benchmark，在 Task 使用带抓放修正的 sticky_snap/gt。本表末尾的脚本参考路线也按 sticky/benchmark 重新执行。

Graph Manager 只计入使用独立随机工作目录的局。旧 Harness 消息曾包含带布局名的路径，受影响的旧尝试已排除，重跑仍计入各模型原有的 1,510 局。

计分需要规划器和 Isaac Sim 同时记录相同的任务、种子、episode hash 和最终判定。实际成功率使用环境的最终 success，得分大于零和满分率另列。仿真记录中的掉落规则可能使实际成功率低于正分率。

## 主实验

| 方法 | 模型 | 已计分/计划 | 已记录中断或排除 | 平均分 | 平均分 95% CI | 任务成功 | 正分 | 满分 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 13/1510 | 0 | 0.000 | — | 0/13 | 0/13 | 0/13 |
| OpenLoop | qwen3.5-27b | 13/1510 | 0 | 0.000 | — | 0/13 | 0/13 | 0/13 |
| OpenLoop | internvl3.5-8b | 13/1510 | 0 | 0.000 | — | 0/13 | 0/13 | 0/13 |
| ReAct | qwen3.5-4b | 16/1510 | 0 | 0.000 | — | 0/16 | 0/16 | 0/16 |
| ReAct | qwen3.5-27b | 14/1510 | 0 | 0.071 | — | 1/14 | 1/14 | 1/14 |
| ReAct | internvl3.5-8b | 15/1510 | 0 | 0.000 | — | 0/15 | 0/15 | 0/15 |
| CodeAsPolicies | qwen3.5-4b | 13/1510 | 0 | 0.000 | — | 0/13 | 0/13 | 0/13 |
| CodeAsPolicies | qwen3.5-27b | 12/1510 | 0 | 0.083 | — | 1/12 | 1/12 | 1/12 |
| CodeAsPolicies | internvl3.5-8b | 13/1510 | 0 | 0.077 | — | 1/13 | 1/13 | 1/13 |
| SayPlan | qwen3.5-4b | 10/1510 | 0 | 0.000 | — | 0/10 | 0/10 | 0/10 |
| SayPlan | qwen3.5-27b | 11/1510 | 0 | 0.000 | — | 0/11 | 0/11 | 0/11 |
| SayPlan | internvl3.5-8b | 12/1510 | 0 | 0.000 | — | 0/12 | 0/12 | 0/12 |
| GraphManager | qwen3.5-4b | 10/1510 | 2 | 0.100 | — | 1/10 | 1/10 | 1/10 |
| GraphManager | qwen3.5-27b | 9/1510 | 1 | 0.000 | — | 0/9 | 0/9 | 0/9 |
| GraphManager | internvl3.5-8b | 9/1510 | 1 | 0.000 | — | 0/9 | 0/9 | 0/9 |

置信区间按任务内的设计聚类，重采样 2,000 次。只有全量覆盖的行给出区间。

## 按任务条件配对

每种方法取三个模型都已计分的相同任务、布局和种子。前三列按任务类别给出平均分和配对局数，接下来两列按布局中的理想选项是否可用划分。理想选项不可用时，v6 给该布局的最佳替代结果记 1.0 分。最后一列统计达到这一档且通过环境最终成功检查的局数，分母是理想选项不可用的配对局。

| 方法 | 模型 | Control | Task | Action + Task | 理想选择可用 | 理想选择不可用 | 达成布局最佳替代/理想选择不可用 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 0.000 (5) | 0.000 (4) | 0.000 (4) | 0.000 (11) | 0.000 (2) | 0/2 |
| OpenLoop | qwen3.5-27b | 0.000 (5) | 0.000 (4) | 0.000 (4) | 0.000 (11) | 0.000 (2) | 0/2 |
| OpenLoop | internvl3.5-8b | 0.000 (5) | 0.000 (4) | 0.000 (4) | 0.000 (11) | 0.000 (2) | 0/2 |
| ReAct | qwen3.5-4b | 0.000 (5) | 0.000 (5) | 0.000 (4) | 0.000 (11) | 0.000 (3) | 0/3 |
| ReAct | qwen3.5-27b | 0.200 (5) | 0.000 (5) | 0.000 (4) | 0.091 (11) | 0.000 (3) | 0/3 |
| ReAct | internvl3.5-8b | 0.000 (5) | 0.000 (5) | 0.000 (4) | 0.000 (11) | 0.000 (3) | 0/3 |
| CodeAsPolicies | qwen3.5-4b | 0.000 (4) | 0.000 (4) | 0.000 (4) | 0.000 (10) | 0.000 (2) | 0/2 |
| CodeAsPolicies | qwen3.5-27b | 0.250 (4) | 0.000 (4) | 0.000 (4) | 0.100 (10) | 0.000 (2) | 0/2 |
| CodeAsPolicies | internvl3.5-8b | 0.250 (4) | 0.000 (4) | 0.000 (4) | 0.100 (10) | 0.000 (2) | 0/2 |
| SayPlan | qwen3.5-4b | 0.000 (4) | 0.000 (3) | 0.000 (3) | 0.000 (8) | 0.000 (2) | 0/2 |
| SayPlan | qwen3.5-27b | 0.000 (4) | 0.000 (3) | 0.000 (3) | 0.000 (8) | 0.000 (2) | 0/2 |
| SayPlan | internvl3.5-8b | 0.000 (4) | 0.000 (3) | 0.000 (3) | 0.000 (8) | 0.000 (2) | 0/2 |
| GraphManager | qwen3.5-4b | 0.333 (3) | 0.000 (3) | 0.000 (3) | 0.143 (7) | 0.000 (2) | 0/2 |
| GraphManager | qwen3.5-27b | 0.000 (3) | 0.000 (3) | 0.000 (3) | 0.000 (7) | 0.000 (2) | 0/2 |
| GraphManager | internvl3.5-8b | 0.000 (3) | 0.000 (3) | 0.000 (3) | 0.000 (7) | 0.000 (2) | 0/2 |

## 提示和观测消融

| 方法 | 模型 | 已计分/计划 | 已记录中断或排除 | 平均分 | 平均分 95% CI | 任务成功 | 正分 | 满分 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ReActHint | qwen3.5-4b | 11/316 | 0 | 0.000 | — | 0/11 | 0/11 | 0/11 |
| ReActHint | qwen3.5-27b | 12/316 | 0 | 0.000 | — | 0/12 | 0/12 | 0/12 |
| ReActHint | internvl3.5-8b | 12/316 | 0 | 0.000 | — | 0/12 | 0/12 | 0/12 |
| ReActPrivileged | qwen3.5-4b | 12/316 | 0 | 0.050 | — | 1/12 | 1/12 | 0/12 |
| ReActPrivileged | qwen3.5-27b | 12/316 | 0 | 0.242 | — | 4/12 | 4/12 | 2/12 |
| ReActPrivileged | internvl3.5-8b | 11/316 | 0 | 0.091 | — | 1/11 | 1/11 | 1/11 |

| 消融 | 模型 | 配对数 | ReAct 平均分 | 消融平均分 | 差值 |
| --- | --- | --- | --- | --- | --- |
| ReActHint | qwen3.5-4b | 11 | 0.000 (11) | 0.000 (11) | +0.000 |
| ReActHint | qwen3.5-27b | 12 | 0.000 (12) | 0.000 (12) | +0.000 |
| ReActHint | internvl3.5-8b | 12 | 0.000 (12) | 0.000 (12) | +0.000 |
| ReActPrivileged | qwen3.5-4b | 12 | 0.000 (12) | 0.050 (12) | +0.050 |
| ReActPrivileged | qwen3.5-27b | 12 | 0.000 (12) | 0.242 (12) | +0.242 |
| ReActPrivileged | internvl3.5-8b | 11 | 0.000 (11) | 0.091 (11) | +0.091 |

## Graph Manager 首次结局与重试

统计使用随机工作目录并已写出 Graph Manager 结果的尝试。首次结局按每个布局和种子的首次尝试统计。管理器返回 error 时仍保留该次记录，补跑后取得原生判定的局另列。错误码计入管理器内部的重启，例如一次 CLIENT_TIMEOUT 后同次启动仍可给出结局。MODEL_ERROR 表示管理器没有收到完整决策，Harness 中可能已有模型输出和被拒绝的工具调用。

| 模型 | 已返回的局 | 首次有结局/已返回的局 | 首次返回 error | 首次 error 后已计分 | 已返回的启动次数 | 全部尝试记录的错误码 |
| --- | --- | --- | --- | --- | --- | --- |
| qwen3.5-4b | 11 | 10/11 | 1 | 0 | 11 | `MODEL_ERROR` × 1 |
| qwen3.5-27b | 9 | 9/9 | 0 | 0 | 9 | `CLIENT_TIMEOUT` × 1 |
| internvl3.5-8b | 9 | 9/9 | 0 | 0 | 9 | — |

## 技能调用和错误

每格为出现该情况的局数 / 已计分局数。一局可以遇到多类错误，随后仍可能成功。分类沿用仓库对技能调用最内层错误码的定义，例如 NOT_OBSERVED 归入观测，NO_PATH 归入前置条件，POLICY_FAILED 归入执行。错误码描述技能的返回状态，判断失败原因还需要结合模型选的参数和当时的场景。

| 方法 | 模型 | 执行 | 观测 | 前置条件 | 无效调用 | 其他错误 | 全局零技能调用 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 8/13 | 0/13 | 1/13 | 2/13 | 0/13 | 0/13 |
| OpenLoop | qwen3.5-27b | 7/13 | 1/13 | 0/13 | 2/13 | 0/13 | 0/13 |
| OpenLoop | internvl3.5-8b | 2/13 | 2/13 | 1/13 | 0/13 | 0/13 | 0/13 |
| ReAct | qwen3.5-4b | 10/16 | 1/16 | 9/16 | 4/16 | 0/16 | 1/16 |
| ReAct | qwen3.5-27b | 12/14 | 0/14 | 9/14 | 2/14 | 0/14 | 0/14 |
| ReAct | internvl3.5-8b | 8/15 | 5/15 | 10/15 | 1/15 | 0/15 | 0/15 |
| CodeAsPolicies | qwen3.5-4b | 5/13 | 1/13 | 0/13 | 0/13 | 0/13 | 2/13 |
| CodeAsPolicies | qwen3.5-27b | 6/12 | 1/12 | 2/12 | 2/12 | 0/12 | 0/12 |
| CodeAsPolicies | internvl3.5-8b | 4/13 | 4/13 | 3/13 | 1/13 | 0/13 | 5/13 |
| SayPlan | qwen3.5-4b | 9/10 | 5/10 | 4/10 | 8/10 | 0/10 | 0/10 |
| SayPlan | qwen3.5-27b | 8/11 | 3/11 | 6/11 | 5/11 | 0/11 | 0/11 |
| SayPlan | internvl3.5-8b | 7/12 | 3/12 | 6/12 | 4/12 | 0/12 | 0/12 |
| GraphManager | qwen3.5-4b | 8/10 | 4/10 | 5/10 | 6/10 | 0/10 | 0/10 |
| GraphManager | qwen3.5-27b | 8/9 | 0/9 | 4/9 | 3/9 | 0/9 | 0/9 |
| GraphManager | internvl3.5-8b | 2/9 | 0/9 | 1/9 | 0/9 | 0/9 | 7/9 |
| ReActHint | qwen3.5-4b | 4/11 | 1/11 | 5/11 | 3/11 | 2/11 | 3/11 |
| ReActHint | qwen3.5-27b | 10/12 | 2/12 | 7/12 | 2/12 | 0/12 | 0/12 |
| ReActHint | internvl3.5-8b | 8/12 | 2/12 | 6/12 | 2/12 | 0/12 | 0/12 |
| ReActPrivileged | qwen3.5-4b | 6/12 | 7/12 | 4/12 | 4/12 | 0/12 | 1/12 |
| ReActPrivileged | qwen3.5-27b | 10/12 | 2/12 | 6/12 | 0/12 | 0/12 | 0/12 |
| ReActPrivileged | internvl3.5-8b | 7/11 | 7/11 | 9/11 | 0/11 | 0/11 | 0/11 |

## 逐次技能调用的规划正确性

使用仓库 Planning Correctness 的逐次调用判定。正确率和判定覆盖率均列出分子与分母。成功执行的调用会判为合理，即使模型交付了错误物体。控制器报错时，接口与前置条件允许的调用也可以判为合理。最后一列列出在这些合理调用中，仓库归类为底层执行失败的次数。整局是否完成任务见主实验和消融表。

| 方法 | 模型 | 合理/可判定调用 | 可判定/全部调用 | 无法判定的调用 | 执行失败/合理调用 |
| --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 20/22 | 22/23 | 1 | 5/20 |
| OpenLoop | qwen3.5-27b | 21/23 | 23/24 | 1 | 1/21 |
| OpenLoop | internvl3.5-8b | 17/17 | 17/20 | 3 | 1/17 |
| ReAct | qwen3.5-4b | 179/189 | 189/206 | 17 | 24/179 |
| ReAct | qwen3.5-27b | 199/209 | 209/234 | 25 | 37/199 |
| ReAct | internvl3.5-8b | 644/650 | 650/804 | 154 | 99/644 |
| CodeAsPolicies | qwen3.5-4b | 14/14 | 14/15 | 1 | 4/14 |
| CodeAsPolicies | qwen3.5-27b | 29/34 | 34/38 | 4 | 4/29 |
| CodeAsPolicies | internvl3.5-8b | 24/27 | 27/49 | 22 | 2/24 |
| SayPlan | qwen3.5-4b | 179/205 | 205/239 | 34 | 39/179 |
| SayPlan | qwen3.5-27b | 149/157 | 157/184 | 27 | 55/149 |
| SayPlan | internvl3.5-8b | 245/255 | 255/266 | 11 | 98/245 |
| GraphManager | qwen3.5-4b | 94/105 | 105/116 | 11 | 13/94 |
| GraphManager | qwen3.5-27b | 40/43 | 43/48 | 5 | 10/40 |
| GraphManager | internvl3.5-8b | 4/4 | 4/5 | 1 | 1/4 |
| ReActHint | qwen3.5-4b | 157/165 | 165/198 | 33 | 8/157 |
| ReActHint | qwen3.5-27b | 128/134 | 134/151 | 17 | 14/128 |
| ReActHint | internvl3.5-8b | 477/490 | 490/548 | 58 | 99/477 |
| ReActPrivileged | qwen3.5-4b | 104/109 | 109/137 | 28 | 9/104 |
| ReActPrivileged | qwen3.5-27b | 126/127 | 127/164 | 37 | 18/126 |
| ReActPrivileged | internvl3.5-8b | 330/332 | 332/454 | 122 | 62/330 |

## 推理与执行成本

技能调用数统计从规划器进入环境的顶层契约。一个 fetch 可以在内部依次执行导航、拾取、导航和放置。模型用量取自有完整用量记录的计分局。Graph Manager 按该原生局对应的 Harness 会话统计每次模型响应，包括用于压缩历史的生成。一个 Harness 回合可以包含多次响应。表中用量不含重跑前的尝试。前四种方法的墙钟耗时包含环境启动和排队，Graph Manager 从环境就绪起算。物理执行和同机并发都会影响这些时间。

停止原因保留方法或服务的原始分类。budget 表示用尽调用预算，service_limit 表示达到环境服务限制，time_budget 和 replan_limit 分别表示 Graph Manager 的计时或重规划上限。finish 表示模型主动报告完成，实际任务成功仍以环境判定为准。

| 方法 | 模型 | 技能调用/局 | 模型用量完整/已计分局 | 模型响应/局 | 输入 token/局 | 输出 token/局 | 秒/局 | 停止原因与局数 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 1.77 | 13/13 | 1.00 | 10583 | 246 | 344.2 | `call_failed` × 11，`plan_done` × 2 |
| OpenLoop | qwen3.5-27b | 1.85 | 13/13 | 1.08 | 11416 | 545 | 629.7 | `call_failed` × 10，`plan_done` × 3 |
| OpenLoop | internvl3.5-8b | 1.54 | 13/13 | 1.00 | 13509 | 114 | 380.5 | `plan_done` × 8，`call_failed` × 5 |
| ReAct | qwen3.5-4b | 12.88 | 16/16 | 16.81 | 185255 | 8807 | 2097.3 | `parse_error` × 10，`service_limit` × 3，`finish` × 3 |
| ReAct | qwen3.5-27b | 16.71 | 14/14 | 17.79 | 198519 | 1956 | 2728.4 | `finish` × 8，`service_limit` × 6 |
| ReAct | internvl3.5-8b | 53.60 | 15/15 | 54.07 | 774205 | 3717 | 2191.3 | `budget` × 8，`service_limit` × 4，`finish` × 3 |
| CodeAsPolicies | qwen3.5-4b | 1.15 | 13/13 | 1.00 | 10688 | 82 | 366.7 | `program_done` × 13 |
| CodeAsPolicies | qwen3.5-27b | 3.17 | 12/12 | 1.08 | 11583 | 698 | 930.2 | `program_done` × 10，`service_limit` × 1，`program_error` × 1 |
| CodeAsPolicies | internvl3.5-8b | 3.77 | 13/13 | 1.69 | 23116 | 3057 | 452.2 | `program_done` × 7，`parse_error` × 6 |
| SayPlan | qwen3.5-4b | 23.90 | 10/10 | 36.00 | 302534 | 4039 | 2876.3 | `service_limit` × 5，`budget` × 2，`parse_error` × 1，`finish` × 1，`search_budget` × 1 |
| SayPlan | qwen3.5-27b | 16.73 | 11/11 | 23.82 | 197684 | 2463 | 2142.2 | `finish` × 5，`parse_error` × 3，`service_limit` × 2，`search_budget` × 1 |
| SayPlan | internvl3.5-8b | 22.17 | 12/12 | 35.42 | 401493 | 2526 | 2113.8 | `parse_error` × 5，`service_limit` × 3，`budget` × 2，`search_budget` × 2 |
| GraphManager | qwen3.5-4b | 11.60 | 10/10 | 24.00 | 425739 | 7326 | 1050.2 | `replan_limit` × 5，`model_finished` × 3，`model_gave_up` × 1，`time_budget` × 1 |
| GraphManager | qwen3.5-27b | 5.33 | 8/9 | 14.62 | 227653 | 2999 | 1682.7 | `replan_limit` × 4，`time_budget` × 3，`model_finished` × 2 |
| GraphManager | internvl3.5-8b | 0.56 | 8/9 | 6.62 | 112686 | 16711 | 525.5 | `model_gave_up` × 9 |
| ReActHint | qwen3.5-4b | 18.00 | 11/11 | 22.55 | 252793 | 10298 | 1335.2 | `parse_error` × 6，`service_limit` × 2，`finish` × 2，`budget` × 1 |
| ReActHint | qwen3.5-27b | 12.58 | 12/12 | 13.58 | 151344 | 1283 | 2572.4 | `finish` × 7，`service_limit` × 5 |
| ReActHint | internvl3.5-8b | 45.67 | 12/12 | 46.42 | 663345 | 3196 | 2569.5 | `finish` × 5，`service_limit` × 4，`budget` × 3 |
| ReActPrivileged | qwen3.5-4b | 11.42 | 12/12 | 14.50 | 162464 | 6720 | 1906.5 | `parse_error` × 6，`finish` × 4，`service_limit` × 2 |
| ReActPrivileged | qwen3.5-27b | 13.67 | 12/12 | 14.83 | 169754 | 1980 | 2565.1 | `finish` × 8，`service_limit` × 4 |
| ReActPrivileged | internvl3.5-8b | 41.27 | 11/11 | 41.91 | 605222 | 2800 | 2646.3 | `service_limit` × 6，`budget` × 4，`finish` × 1 |

## 脚本参考路线

每个任务取预先选定的第一个布局。脚本与三个标准 ReAct 均有终态的布局共 11 / 30 个。每个布局只计一次，单列的校准局和诊断局不进入该分母。脚本成功给出同一初始条件下可行的一条路线。

| 脚本终态 | 四方已配对布局数 | qwen3.5-4b 成功/配对局 | qwen3.5-27b 成功/配对局 | internvl3.5-8b 成功/配对局 |
| --- | --- | --- | --- | --- |
| 脚本至少一次成功 | 8 | 0/8 | 0/8 | 0/8 |
| 脚本尝试均失败 | 3 | 0/3 | 0/3 | 0/3 |

以下各局在 sticky/benchmark 下执行任务目录预写的动作和真实物体名。三个模型栏给出同一任务、布局、种子和初始局哈希下标准 ReAct 的原生分数及最终成功判定。横线表示该模型尚无这局的判定。脚本执行错误列显示第一个本应成功却失败的技能，一条脚本路线失败时，其他动作序列仍可能可行。脚本局单独计数。

| 任务 | 布局 | 种子 | 脚本代码 | 脚本已执行/路线步数 | 脚本分数与结局 | qwen3.5-4b | qwen3.5-27b | internvl3.5-8b | 脚本执行错误 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T01_book_to_dining_table | overhang_ready | 10 | 696211a +工作树 | 7/7 | 1.0 成功 | 0.0 失败 | 1.0 成功 | 0.0 失败 | — |
| T01_book_to_dining_table | no_room_fallback__seats_c | 10 | 7846509 | 5/8 | 0.0 失败 | 0.0 失败 | 0.0 失败 | 0.0 失败 | pick · pick_held: the rest built again from here: the arm has IK only 0.000 m along the exit and still touches there |
| T02_stack_blocks | block_put_away__gone_toy_block | 10 | 7846509 | 8/23 | 0.0 失败 | 0.0 失败 | 0.0 失败 | 0.0 失败 | open · open kitchen_cabinet_4: no base pose can grasp the handle and ride the motion |
| T09_tomato_soup | lid_on_spoon_away | 10 | 7846509 | 23/23 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | — |
| T10_trash_the_can | after_dinner_clear__rubbish_leftovers | 10 | 7846509 | 13/24 | 0.0 失败 | 0.0 失败 | 0.0 失败 | 0.0 失败 | pick · carry_in: the arm stopped 0.024 m short of where it was sent |
| T11_collect_fruits | basket_gone_bowl_there | 10 | 7846509 | 11/11 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | — |
| T12_tidy_toys | bins_capacity__half_bin_and_tray_duck_dining | 19 | 7846509 | 15/15 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | — |
| T19_recycling | bin_on_bookcase | 10 | 7846509 | 14/14 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | drop · tuck: the arm stopped 0.066 m short of where it was sent |
| T20_juice_back_to_table | bottle_on_cabinet | 10 | 7846509 | 6/6 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | — |
| T24_snack_for_kid | apple_on_table | 10 | 7846509 | 6/6 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | — |
| T26_kids_things_to_room | bear_to_bed__top_free | 10 | 7846509 | 6/6 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | — |
| T28_cup_to_bedside | already_there__wrong_cup | 10 | 7846509 | 8/8 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | — |
| T30_bowls_for_soup | bowl_on_cabinet | 10 | 7846509 | 6/6 | 1.0 成功 | 0.0 失败 | 0.0 失败 | 0.0 失败 | — |
