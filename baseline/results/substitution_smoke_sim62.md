# ZenoBench 替代任务基线

北京时间 2026-11-26 15:59，原生计分 **26 / 2163** 局，运行中断 0 局，待取得结局 2137 局。 当前为阶段快照，各行覆盖的布局随调度进度变化。

来自 `substitution_smoke.json` 的 103 局覆盖 20 个任务、52 个布局。所有方法使用相同的布局和种子。其中有 42 局可按物体分级，另有 61 局按完成档位评分。这批场景均需替代，无法估计理想物可用时的误替代率。

上游 main `4457acb`，Graph Manager `26df036`，运行代码 `4b797f6`。与上一轮 `7846509` 的 103 个相同任务、布局和种子相比，103 局的机器人起点改变，57 局的模型可见指令改变。使用 Isaac Sim 6.2.0.0、Isaac Lab 2.3.2、cuRobo 0.7.8。仓库默认的 Isaac Sim 5.1 与本表使用的仿真版本不同。

每局最多调用 60 次技能。主方法使用 sticky/benchmark，观测含头部 RGB、已知地点和环境给出的可见物体清单。ReActHint 增加替代提示，ReActPrivileged 使用 sticky/privileged 额外提供任务物体及位置。所有模型均在本地推理，温度为 0。

## 方法对比

成功以仿真最终判定为准。严格成功还要求达到该布局可用的最佳替代。执行故障列统计最终失败且至少一次有效技能调用出现执行错误的局，分母为已计分的失败局。一次失败可能同时涉及规划与执行。

| 方法 | 模型 | 计分/计划 | 中断 | 任务成功 | 平均原生分 | 严格成功 | 执行故障/失败 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 2/103 | 0 | 0/2 | 0.000 | 0/2 | 1/2 |
| OpenLoop | qwen3.5-27b | 2/103 | 0 | 0/2 | 0.000 | 0/2 | 0/2 |
| OpenLoop | internvl3.5-8b | 2/103 | 0 | 0/2 | 0.000 | 0/2 | 0/2 |
| ReAct | qwen3.5-4b | 1/103 | 0 | 0/1 | 0.000 | 0/1 | 0/1 |
| ReAct | qwen3.5-27b | 0/103 | 0 | — | — | — | — |
| ReAct | internvl3.5-8b | 2/103 | 0 | 0/2 | 0.000 | 0/2 | 0/2 |
| CodeAsPolicies | qwen3.5-4b | 2/103 | 0 | 0/2 | 0.000 | 0/2 | 0/2 |
| CodeAsPolicies | qwen3.5-27b | 2/103 | 0 | 0/2 | 0.000 | 0/2 | 0/2 |
| CodeAsPolicies | internvl3.5-8b | 2/103 | 0 | 0/2 | 0.000 | 0/2 | 0/2 |
| SayPlan | qwen3.5-4b | 2/103 | 0 | 0/2 | 0.000 | 0/2 | 2/2 |
| SayPlan | qwen3.5-27b | 2/103 | 0 | 0/2 | 0.000 | 0/2 | 2/2 |
| SayPlan | internvl3.5-8b | 1/103 | 0 | 0/1 | 0.000 | 0/1 | 0/1 |
| GraphManager | qwen3.5-4b | 1/103 | 0 | 0/1 | 0.000 | 0/1 | 1/1 |
| GraphManager | qwen3.5-27b | 0/103 | 0 | — | — | — | — |
| GraphManager | internvl3.5-8b | 2/103 | 0 | 0/2 | 0.000 | 0/2 | 0/2 |
| ReActHint | qwen3.5-4b | 1/103 | 0 | 0/1 | 0.000 | 0/1 | 0/1 |
| ReActHint | qwen3.5-27b | 0/103 | 0 | — | — | — | — |
| ReActHint | internvl3.5-8b | 0/103 | 0 | — | — | — | — |
| ReActPrivileged | qwen3.5-4b | 1/103 | 0 | 0/1 | 0.000 | 0/1 | 0/1 |
| ReActPrivileged | qwen3.5-27b | 1/103 | 0 | 0/1 | 0.000 | 0/1 | 0/1 |
| ReActPrivileged | internvl3.5-8b | 0/103 | 0 | — | — | — | — |

## 替代选择

可分级的 B 局从成功分支或最后拿起的候选物推断选择，因此可能命中替代物而任务仍失败。若布局只提供差档替代物，命中最佳与选差档可以重合。容器作为目的地时，失败轨迹有时无法识别所选容器。B_open 只按仿真完成档位判定，失败包含已想到替代方案但执行未完成的情况。每个分母均为该方法在对应侧已计分的局数。

| 方法 | 模型 | B 命中最佳 | B 漏替代 | B 选差档 | B 抢占 | B 其他物体 | B_open 满分 | B_open 部分分 | B_open 失败 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | — | — | — | — | — | 0/2 | 0/2 | 2/2 |
| OpenLoop | qwen3.5-27b | — | — | — | — | — | 0/2 | 0/2 | 2/2 |
| OpenLoop | internvl3.5-8b | — | — | — | — | — | 0/2 | 0/2 | 2/2 |
| ReAct | qwen3.5-4b | — | — | — | — | — | 0/1 | 0/1 | 1/1 |
| ReAct | qwen3.5-27b | — | — | — | — | — | — | — | — |
| ReAct | internvl3.5-8b | — | — | — | — | — | 0/2 | 0/2 | 2/2 |
| CodeAsPolicies | qwen3.5-4b | — | — | — | — | — | 0/2 | 0/2 | 2/2 |
| CodeAsPolicies | qwen3.5-27b | — | — | — | — | — | 0/2 | 0/2 | 2/2 |
| CodeAsPolicies | internvl3.5-8b | — | — | — | — | — | 0/2 | 0/2 | 2/2 |
| SayPlan | qwen3.5-4b | — | — | — | — | — | 0/2 | 0/2 | 2/2 |
| SayPlan | qwen3.5-27b | — | — | — | — | — | 0/2 | 0/2 | 2/2 |
| SayPlan | internvl3.5-8b | — | — | — | — | — | 0/1 | 0/1 | 1/1 |
| GraphManager | qwen3.5-4b | — | — | — | — | — | 0/1 | 0/1 | 1/1 |
| GraphManager | qwen3.5-27b | — | — | — | — | — | — | — | — |
| GraphManager | internvl3.5-8b | — | — | — | — | — | 0/2 | 0/2 | 2/2 |
| ReActHint | qwen3.5-4b | — | — | — | — | — | 0/1 | 0/1 | 1/1 |
| ReActHint | qwen3.5-27b | — | — | — | — | — | — | — | — |
| ReActHint | internvl3.5-8b | — | — | — | — | — | — | — | — |
| ReActPrivileged | qwen3.5-4b | — | — | — | — | — | 0/1 | 0/1 | 1/1 |
| ReActPrivileged | qwen3.5-27b | — | — | — | — | — | 0/1 | 0/1 | 1/1 |
| ReActPrivileged | internvl3.5-8b | — | — | — | — | — | — | — | — |

## 按理想物不可用原因划分的严格成功

| 方法 | 模型 | 缺失（56 局） | 被占用（26 局） | 能力不足（19 局） | 看着像但不能用（2 局） |
| --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 0/2 | — | — | — |
| OpenLoop | qwen3.5-27b | 0/2 | — | — | — |
| OpenLoop | internvl3.5-8b | 0/2 | — | — | — |
| ReAct | qwen3.5-4b | 0/1 | — | — | — |
| ReAct | qwen3.5-27b | — | — | — | — |
| ReAct | internvl3.5-8b | 0/2 | — | — | — |
| CodeAsPolicies | qwen3.5-4b | 0/2 | — | — | — |
| CodeAsPolicies | qwen3.5-27b | 0/2 | — | — | — |
| CodeAsPolicies | internvl3.5-8b | 0/2 | — | — | — |
| SayPlan | qwen3.5-4b | 0/2 | — | — | — |
| SayPlan | qwen3.5-27b | 0/2 | — | — | — |
| SayPlan | internvl3.5-8b | 0/1 | — | — | — |
| GraphManager | qwen3.5-4b | 0/1 | — | — | — |
| GraphManager | qwen3.5-27b | — | — | — | — |
| GraphManager | internvl3.5-8b | 0/2 | — | — | — |
| ReActHint | qwen3.5-4b | 0/1 | — | — | — |
| ReActHint | qwen3.5-27b | — | — | — | — |
| ReActHint | internvl3.5-8b | — | — | — | — |
| ReActPrivileged | qwen3.5-4b | 0/1 | — | — | — |
| ReActPrivileged | qwen3.5-27b | 0/1 | — | — | — |
| ReActPrivileged | internvl3.5-8b | — | — | — | — |

## 同局消融

每一项只比较 ReAct 与相应消融均有原生判定的同一布局和种子。

| 模型 | 与 ReAct 配对的方法 | 同局数 | ReAct 严格成功 | 消融严格成功 | 平均原生分差 |
| --- | --- | --- | --- | --- | --- |
| qwen3.5-4b | ReActHint | 0 | — | — | — |
| qwen3.5-4b | ReActPrivileged | 1 | 0/1 | 0/1 | +0.000 |
| qwen3.5-27b | ReActHint | 0 | — | — | — |
| qwen3.5-27b | ReActPrivileged | 0 | — | — | — |
| internvl3.5-8b | ReActHint | 0 | — | — | — |
| internvl3.5-8b | ReActPrivileged | 0 | — | — | — |
