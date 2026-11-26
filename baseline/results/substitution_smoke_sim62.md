# ZenoBench 替代任务基线

北京时间 2026-11-26 17:08，原生计分 **105 / 2163** 局，运行中断 0 局，待取得结局 2058 局。 当前为阶段快照，各行覆盖的布局随调度进度变化。

来自 `substitution_smoke.json` 的 103 局覆盖 20 个任务、52 个布局。所有方法使用相同的布局和种子。其中有 42 局可按物体分级，另有 61 局按完成档位评分。这批场景均需替代，无法估计理想物可用时的误替代率。

上游 main `4457acb`，Graph Manager `26df036`，运行代码 `4b797f6`。与上一轮 `7846509` 的 103 个相同任务、布局和种子相比，103 局的机器人起点改变，57 局的模型可见指令改变。使用 Isaac Sim 6.2.0.0、Isaac Lab 2.3.2、cuRobo 0.7.8。仓库默认的 Isaac Sim 5.1 与本表使用的仿真版本不同。

每局最多调用 60 次技能。主方法使用 sticky/benchmark，观测含头部 RGB、已知地点和环境给出的可见物体清单。ReActHint 增加替代提示，ReActPrivileged 使用 sticky/privileged 额外提供任务物体及位置。所有模型均在本地推理，温度为 0。

## 方法对比

成功以仿真最终判定为准。严格成功还要求达到该布局可用的最佳替代。执行故障列统计最终失败且至少一次有效技能调用出现执行错误的局，分母为已计分的失败局。一次失败可能同时涉及规划与执行。

| 方法 | 模型 | 计分/计划 | 中断 | 任务成功 | 平均原生分 | 严格成功 | 执行故障/失败 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 6/103 | 0 | 0/6 | 0.000 | 0/6 | 3/6 |
| OpenLoop | qwen3.5-27b | 6/103 | 0 | 0/6 | 0.000 | 0/6 | 0/6 |
| OpenLoop | internvl3.5-8b | 6/103 | 0 | 0/6 | 0.000 | 0/6 | 0/6 |
| ReAct | qwen3.5-4b | 11/103 | 0 | 0/11 | 0.000 | 0/11 | 7/11 |
| ReAct | qwen3.5-27b | 7/103 | 0 | 1/7 | 0.143 | 1/7 | 4/6 |
| ReAct | internvl3.5-8b | 9/103 | 0 | 1/9 | 0.067 | 0/9 | 2/8 |
| CodeAsPolicies | qwen3.5-4b | 5/103 | 0 | 0/5 | 0.000 | 0/5 | 1/5 |
| CodeAsPolicies | qwen3.5-27b | 5/103 | 0 | 0/5 | 0.000 | 0/5 | 0/5 |
| CodeAsPolicies | internvl3.5-8b | 5/103 | 0 | 0/5 | 0.000 | 0/5 | 2/5 |
| SayPlan | qwen3.5-4b | 4/103 | 0 | 0/4 | 0.000 | 0/4 | 4/4 |
| SayPlan | qwen3.5-27b | 5/103 | 0 | 0/5 | 0.000 | 0/5 | 5/5 |
| SayPlan | internvl3.5-8b | 5/103 | 0 | 0/5 | 0.000 | 0/5 | 1/5 |
| GraphManager | qwen3.5-4b | 4/103 | 0 | 0/4 | 0.000 | 0/4 | 2/4 |
| GraphManager | qwen3.5-27b | 3/103 | 0 | 0/3 | 0.000 | 0/3 | 0/3 |
| GraphManager | internvl3.5-8b | 5/103 | 0 | 0/5 | 0.000 | 0/5 | 0/5 |
| ReActHint | qwen3.5-4b | 4/103 | 0 | 0/4 | 0.000 | 0/4 | 3/4 |
| ReActHint | qwen3.5-27b | 1/103 | 0 | 1/1 | 1.000 | 1/1 | — |
| ReActHint | internvl3.5-8b | 3/103 | 0 | 0/3 | 0.000 | 0/3 | 1/3 |
| ReActPrivileged | qwen3.5-4b | 5/103 | 0 | 0/5 | 0.000 | 0/5 | 3/5 |
| ReActPrivileged | qwen3.5-27b | 3/103 | 0 | 0/3 | 0.000 | 0/3 | 0/3 |
| ReActPrivileged | internvl3.5-8b | 3/103 | 0 | 0/3 | 0.000 | 0/3 | 0/3 |

## 五种主方法的同局比较

按任务、布局和种子配对后，全部 15 个组合共同完成了 3 局。下表在这些共同样本上计算严格成功。

| 模型 | OpenLoop | ReAct | CodeAsPolicies | SayPlan | GraphManager |
| --- | --- | --- | --- | --- | --- |
| qwen3.5-4b | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |
| qwen3.5-27b | 0/3 | 1/3 | 0/3 | 0/3 | 0/3 |
| internvl3.5-8b | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |

## 替代选择

可分级的 B 局从成功分支或最后拿起的候选物推断选择，因此可能命中替代物而任务仍失败。若布局只提供差档替代物，命中最佳与选差档可以重合。容器作为目的地时，失败轨迹有时无法识别所选容器。B_open 只按仿真完成档位判定，失败包含已想到替代方案但执行未完成的情况。每个分母均为该方法在对应侧已计分的局数。

| 方法 | 模型 | B 命中最佳 | B 漏替代 | B 选差档 | B 抢占 | B 其他物体 | B_open 满分 | B_open 部分分 | B_open 失败 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 0/2 | 2/2 | 0/2 | 0/2 | 0/2 | 0/4 | 0/4 | 4/4 |
| OpenLoop | qwen3.5-27b | 0/2 | 2/2 | 0/2 | 0/2 | 0/2 | 0/4 | 0/4 | 4/4 |
| OpenLoop | internvl3.5-8b | 0/2 | 1/2 | 0/2 | 0/2 | 1/2 | 0/4 | 0/4 | 4/4 |
| ReAct | qwen3.5-4b | 0/3 | 3/3 | 0/3 | 0/3 | 0/3 | 0/8 | 0/8 | 8/8 |
| ReAct | qwen3.5-27b | 0/2 | 2/2 | 0/2 | 0/2 | 0/2 | 1/5 | 0/5 | 4/5 |
| ReAct | internvl3.5-8b | 0/2 | 1/2 | 1/2 | 0/2 | 0/2 | 0/7 | 0/7 | 7/7 |
| CodeAsPolicies | qwen3.5-4b | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 | 0/4 | 0/4 | 4/4 |
| CodeAsPolicies | qwen3.5-27b | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 | 0/4 | 0/4 | 4/4 |
| CodeAsPolicies | internvl3.5-8b | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 | 0/4 | 0/4 | 4/4 |
| SayPlan | qwen3.5-4b | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 | 0/3 | 0/3 | 3/3 |
| SayPlan | qwen3.5-27b | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 | 0/4 | 0/4 | 4/4 |
| SayPlan | internvl3.5-8b | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 | 0/4 | 0/4 | 4/4 |
| GraphManager | qwen3.5-4b | — | — | — | — | — | 0/4 | 0/4 | 4/4 |
| GraphManager | qwen3.5-27b | — | — | — | — | — | 0/3 | 0/3 | 3/3 |
| GraphManager | internvl3.5-8b | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 | 0/4 | 0/4 | 4/4 |
| ReActHint | qwen3.5-4b | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 | 0/3 | 0/3 | 3/3 |
| ReActHint | qwen3.5-27b | — | — | — | — | — | 1/1 | 0/1 | 0/1 |
| ReActHint | internvl3.5-8b | — | — | — | — | — | 0/3 | 0/3 | 3/3 |
| ReActPrivileged | qwen3.5-4b | 0/1 | 1/1 | 0/1 | 0/1 | 0/1 | 0/4 | 0/4 | 4/4 |
| ReActPrivileged | qwen3.5-27b | — | — | — | — | — | 0/3 | 0/3 | 3/3 |
| ReActPrivileged | internvl3.5-8b | — | — | — | — | — | 0/3 | 0/3 | 3/3 |

## 按理想物不可用原因划分的严格成功

| 方法 | 模型 | 缺失（56 局） | 被占用（26 局） | 能力不足（19 局） | 看着像但不能用（2 局） |
| --- | --- | --- | --- | --- | --- |
| OpenLoop | qwen3.5-4b | 0/6 | — | — | — |
| OpenLoop | qwen3.5-27b | 0/6 | — | — | — |
| OpenLoop | internvl3.5-8b | 0/6 | — | — | — |
| ReAct | qwen3.5-4b | 0/8 | 0/1 | 0/2 | — |
| ReAct | qwen3.5-27b | 1/5 | 0/1 | 0/1 | — |
| ReAct | internvl3.5-8b | 0/7 | 0/1 | 0/1 | — |
| CodeAsPolicies | qwen3.5-4b | 0/5 | — | — | — |
| CodeAsPolicies | qwen3.5-27b | 0/5 | — | — | — |
| CodeAsPolicies | internvl3.5-8b | 0/5 | — | — | — |
| SayPlan | qwen3.5-4b | 0/4 | — | — | — |
| SayPlan | qwen3.5-27b | 0/5 | — | — | — |
| SayPlan | internvl3.5-8b | 0/5 | — | — | — |
| GraphManager | qwen3.5-4b | 0/4 | — | — | — |
| GraphManager | qwen3.5-27b | 0/3 | — | — | — |
| GraphManager | internvl3.5-8b | 0/5 | — | — | — |
| ReActHint | qwen3.5-4b | 0/4 | — | — | — |
| ReActHint | qwen3.5-27b | 1/1 | — | — | — |
| ReActHint | internvl3.5-8b | 0/3 | — | — | — |
| ReActPrivileged | qwen3.5-4b | 0/5 | — | — | — |
| ReActPrivileged | qwen3.5-27b | 0/3 | — | — | — |
| ReActPrivileged | internvl3.5-8b | 0/3 | — | — | — |

## 同局消融

每一项只比较 ReAct 与相应消融均有原生判定的同一布局和种子。

| 模型 | 与 ReAct 配对的方法 | 同局数 | ReAct 严格成功 | 消融严格成功 | 平均原生分差 |
| --- | --- | --- | --- | --- | --- |
| qwen3.5-4b | ReActHint | 4 | 0/4 | 0/4 | +0.000 |
| qwen3.5-4b | ReActPrivileged | 5 | 0/5 | 0/5 | +0.000 |
| qwen3.5-27b | ReActHint | 1 | 1/1 | 1/1 | +0.000 |
| qwen3.5-27b | ReActPrivileged | 3 | 1/3 | 0/3 | -0.333 |
| internvl3.5-8b | ReActHint | 3 | 0/3 | 0/3 | +0.000 |
| internvl3.5-8b | ReActPrivileged | 3 | 0/3 | 0/3 | +0.000 |

## 执行器校准

另取 `T04_cup_or_mug_to_cabinet` 的 `no_cup`、种子 10，用目录里的 `alternative_mug` 脚本和相同的 sticky/benchmark 执行。共调用 8 次技能，8 次符合脚本预期，原生得分为 1.0，任务判定为成功。当前有 3 局 VLM 原生记录与其配置及初始条件哈希一致。此单局校准独立于表中 VLM 计数。
