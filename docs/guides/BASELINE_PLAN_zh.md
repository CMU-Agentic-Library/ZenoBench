# SHIFT Baseline 计划

> 2026-11-23 定稿。目标：3 月投稿（benchmark + Graph Manager + SFT/RL + 真机）。
> 本文只管 baseline 部分：要跑哪些方法、统一设置、共用组件、每个方法怎么实现、跑哪些组合、怎么出表。
> 真机由 Zeno 那边做；SFT/RL 复用本文的共用组件和任务划分。

---

## 1. 要跑的方法

| # | 方法 | 角色 | 计划何时改 | 模型 | 现状 |
|---|---|---|---|---|---|
| 1 | VLM open-loop | 证明闭环必要 | 从不：开头一次给出整份计划 | 4 个（见下） | 要写 |
| 2 | ReAct / tool-use | 平铺、每步反馈 | 每次调用之后 | 4 个 | 要写 |
| 3 | Code-as-Policies | 用代码表示计划 | 程序里的分支 | 4 个 | 要写 |
| 4 | SayPlan 式 | 场景图记忆 + 搜索 | 场景图搜索后重规划 | 4 个 | 要写 |
| 5 | Graph Manager | skill graph 规划器（方法论文中作为 ours） | 每个子目标边界，以及失败时 | 4 个 | 代码已放进 `baseline/graph_manager/`，要在 v6 上统一设置后重跑 |

暂不跑：Nominal script、Oracle（11-23 先删掉，之后需要上下界时再加回）、Retry-only、Reflexion、LLM+P、SayCan 式、相似度启发式。主表完成后再决定。

模型：每个 VLM 方法用 4 个模型各跑一遍：

| 模型 | 类型 | 说明 |
|---|---|---|
| Qwen3.5-4B | 开源，本地部署 | 之后 SFT / RL 的基座 |
| Claude Opus 5.5（`claude-opus-5-5`） | 闭源 API | |
| GPT（当前旗舰，具体版本待填） | 闭源 API | |
| Gemini（当前旗舰，具体版本待填） | 闭源 API | |

三个闭源模型的输入信息、预算和 prompt 完全相同；只换 VLM 客户端的后端。

---

## 2. 统一设置（所有方法必须相同）

| 项目 | 设置 | 备注 |
|---|---|---|
| Commit | 冻结 tag 后的同一个 commit | 结果里记录 commit、profile hash、episode hash（runner 已经在记录） |
| 观察 profile | **`sticky/benchmark`**（11-23 定） | 受限观察和 `physical/benchmark` 完全一样（门控、屏蔽反馈、只看头部相机、无自动恢复），只多了 `sticky_hands: carry`：拿起的物体在手指张开前焊在夹爪上，搬运时不会滑落；pick 和 place 仍是物理的，失败就是失败。目的是减少搬运滑落带来的执行噪声。`sticky/gt` 只用于观察消融 |
| 观察内容 | 头部相机图像、看到的物体、观察缓存、已知地点、机器人状态、上一步结果 | 物体名字是匿名的 `<category>_<k>`（`anonymize_names: true`）；没有目标状态，没有 GT 物体位置 |
| 调用预算 | **60 次技能调用**（失败和被拒绝的也算；VLM 思考不算） | 参考路线中位数 11 步、90% 分位 21 步、最长 34 步，60 约为最长的 1.8 倍。进程内默认已经是 60；HTTP 服务默认 40，要改成 60 |
| 技能列表 | `registry.menu(track)`，71 个动词 | 所有方法给相同的技能说明 |
| 种子 | 10–19 | |
| 采样 | **每个 episode 跑 1 次**；temperature 固定 | 不做多次采样（11-23 定） |
| 自动恢复 | 关闭（profile 里已经是 `auto_recovery: false`） | |

**Graph Manager 走 HTTP 时**：HTTP 服务会给物体位置和每条目标的真假，必须关掉，或者改成走进程内的 `--planner recovery`，保证和其他方法看到的一样。

---

## 3. 任务划分（为 SFT/RL 预留）

- 按**任务**划分，不按种子：约 22 个任务训练，8 个任务测试。测试集要覆盖 Control、Task、Action+Task 三类。
- 划分写进一个文件（建议 `benchmark/v6/split.json`），之后不再改。
- **主表**：所有方法（包括之后的 SFT/RL）在测试任务上比。
- **完整 benchmark 表**：零样本方法（1–5）在全部 30 个任务上的结果。
- 闭源模型在训练任务上的成功轨迹，留作 SFT 数据。

---

## 4. 共用组件（先做，所有 VLM 方法都用）

目录：`baseline/`（每个方法一个子目录或模块；Graph Manager 在 `baseline/graph_manager/`）

| 组件 | 文件 | 内容 |
|---|---|---|
| Planner 基类 | `baseline/base.py` | 继承 `benchmark.planners.Planner`；负责 `reset` / `next_call`，记录每次 VLM 调用的 usage |
| VLM 客户端 | `baseline/vlm.py` | 统一接口 `chat(messages, images) -> text, usage`；后端：本地 Qwen3.5-4B（vLLM 或 HF）和闭源 API；有重试和超时；temperature 可配置 |
| Prompt 构建 | `baseline/prompt.py` | 技能说明（来自 `skills`）、指令、观察序列化（文字 + 头部图像）、上一步结果和错误码。四个方法共用同一套写法，只在"输出格式"段不同 |
| 输出解析 | `baseline/parse.py` | 把模型输出解析成 `{"skill", "args"}`；格式错了重试 1 次，还错就记为一次无效调用并结束 |
| 日志 | runner 小改动 | `run_episode.py` 的 `log_row` 现在只记 `planner_note`，要加上 `act.get("usage")`（VLM 调用次数、输入/输出 token） |

---

## 5. 每个方法的实现

新写的 VLM 方法都实现成 `--planner recovery --policy baseline.<模块>:<类>`。Graph Manager 先保留它自己的 HTTP 运行方式（见 5.5）。

### 5.1 VLM open-loop（`baseline/open_loop.py`）
- 第一次 `next_call`：把指令、技能说明和初始观察交给 VLM，让它输出整份调用列表（JSON）。
- 之后每次 `next_call`：按顺序吐出下一个调用。
- 上一步失败，或者列表用完了，就返回 `None`。
- 预期：看不到的物体会被拒绝（NOT_OBSERVED），所以很多 Task variant 会接近 0。这是预期结果，正好说明需要闭环。

### 5.2 ReAct / tool-use（`baseline/react.py`）
- 每次 `next_call`：发送指令、技能说明、当前观察、历史（之前的调用和结果），让模型先写一段简短思考，再输出一个调用或 `finish`。
- 历史过长时只保留最近 K 步的完整信息，更早的步骤压缩成一行。
- 闭源模型可以用原生函数调用（每个技能一个工具），Qwen 用 JSON 输出；两种方式的输入信息保持一致。
- **最先写**，在 Control 类上跑通后再写其他方法。

### 5.3 Code-as-Policies（`baseline/code_policy.py`）
- 第一次 `next_call`：让 VLM 写一个 Python 函数，用 `skill_name(**args)` 调用技能，每个调用返回结果（success、error code、看到的物体）。程序可以用 `if` / `for` 根据结果分支。
- 执行：程序放在生成器或线程里跑。每调用一次技能就暂停，通过 `next_call` 把调用交给环境，拿到下一个观察和结果后再恢复程序。
- 程序结束或抛异常就返回 `None`。可选：异常时允许重新生成一次程序（算一次 VLM 调用）。
- 安全：程序在受限命名空间里执行，只暴露技能函数和少量内置函数。

### 5.4 SayPlan 式（`baseline/sayplan.py`）
- 场景图：房间 → 家具/容器，**只放静态结构**（来自 known places）。物体只有被观察到才加进图里，不提前给出位置。
- 每一步：VLM 先在图上选一个要展开或前往的节点（搜索），再决定下一个技能调用；拿到新观察后更新图。
- 失败或发现新信息时，基于当前图重新规划剩余步骤。
- 放在最后写。12/21 还没完成就放附录或砍掉。

### 5.5 Graph Manager（`baseline/graph_manager/`）
- 来源：[CMU-Agentic-Library/Graph_manager](https://github.com/CMU-Agentic-Library/Graph_manager) main `b766b66`（2026-10-29），原样导出（不含 .venv / run / build），说明见 `baseline/README.md`。
- 做法：一次给出全部子目标，每个子目标一个 skill DAG；每执行完一个子目标（或失败）回到 VLM：continue、给出剩余部分的新 task_plan，或 finish。走 env_service HTTP 接口，模型通过 DeepSeek Harness 调用。
- 要做的事：
  - 技能说明：现在 vendored 的是旧快照（70 个技能，ZenoBench `eb4b3f0`），而且 `graph-manager-run` 每次运行前会从 git 拉最新的 ZenoBench。放进本仓库后改成直接读本仓库的 `skill_library/`，和冻结 commit 一致
  - 预算：HTTP 默认 40 次，改成 60
  - 观察：HTTP 服务会给物体位置和目标状态，改成和 `sticky/benchmark` 一样（或接到进程内 runner）
  - 模型：现在支持本地 vLLM 的 Qwen3.5-4B；要加 Claude / GPT / Gemini 后端
  - 在 v6 的冻结 commit 上重跑

---

## 6. 运行矩阵

| 方法 | 模型 | 全部 30 个任务 | 测试任务 |
|---|---|---|---|
| Open-loop / ReAct / CaP / SayPlan / Graph Manager | Qwen3.5-4B | ✓ | ✓ |
| 同上 | Claude Opus 5.5 / GPT / Gemini | ✓ | ✓ |

- 1,510 个 episode × 5 方法 × 4 模型 = 30,200 个 episode，每个 episode 跑 1 次。
- 闭源模型 API 费用粗估（按每个 episode 约 20 次 VLM 调用、每次约 8k 输入 token 和 500 输出 token，未计 prompt caching）：Claude Opus 5.5（$4 / $20 每百万 token）约 $0.85 / episode，5 个方法 × 1,510 个 episode ≈ $6,400。GPT 和 Gemini 按各自价格另算，三家合计大约是这个数的 2–3 倍。用 prompt caching 缓存技能说明和历史，预计能明显降低。实测前几十个 episode 后再更新。
- 如果费用或时间不够：三个闭源模型只在测试任务上跑全部方法，30 个任务的完整表只用 Qwen3.5-4B + 一个闭源模型。
- **第一件事是测单个 episode 的耗时**（Isaac + VLM），算出总时长后决定：全量跑，还是每个 variant 抽 3–5 个种子。
- 测试任务上的 episode 必须全量跑（主表要用，SFT/RL 也在这里比）。
- 用现有的 batches 机制分批跑，失败或中断的可以续跑。

---

## 7. 指标和出表

每个 episode 按现有规则打分（1.0 最佳；0.6 / 0.3 替代品；0 不可接受）。

**主表列**：Mean graded score、Success rate（得分 > 0）、Best-choice rate（得分 = 1.0）、VLM queries、Tokens。

**诊断（正文分析或附录）**：Over-substitution rate（理想物体在场却选了替代品）、失败归因（规划 / 接口 / 执行）。

**切分**：按类别（Control / Task / Action+Task）、按参考路线长度。

**统计**：按 variant 做 bootstrap 求 95% 置信区间（同一 variant 的 10 个种子不独立）。

汇总脚本：`baseline/report.py`，读各 run 的 `result.json` 和 `calls.jsonl`，输出主表（Markdown + CSV）和切分表。

---

## 8. 时间线

| 时间 | 内容 |
|---|---|
| 11/24–11/30 | 冻结 tag；预算统一为 60、全部改用 sticky/benchmark；`split.json`；共用组件；测耗时；Graph Manager 接入本仓库的技能库；ReAct 在 Control 上跑通 |
| 12/1–12/7 | Open-loop、Code-as-Policies；Graph Manager 统一设置并接入；汇总脚本 |
| 12/8–12/14 | 主表开跑（Qwen3.5-4B）；SayPlan 式 |
| 12/15–12/21 | 主表闭源部分（Claude / GPT / Gemini）；第一版主表 |
| 12/22 之后 | 消融（子集）、失败分析；结果交给 SFT/RL 使用 |

---

## 9. 开跑前检查

- [ ] 冻结 tag，所有 run 的 commit 相同
- [ ] 调用预算统一为 60，进程内和 HTTP 一致
- [ ] 所有方法都用 `sticky/benchmark`（进程内 runner 用 `--profile sticky/benchmark`；Graph Manager 用 `--env-profile`）
- [ ] `sticky/benchmark.yaml` 开头的注释写着"不是计分用的 benchmark，结果不能和 physical/benchmark 比"；论文以 sticky 为准，这条注释要改
- [ ] Graph Manager 看不到物体位置和目标状态
- [ ] `split.json` 已提交
- [ ] 每个 VLM 方法在 3 个 Control variant 上跑通，日志里有 usage
- [ ] Graph Manager 读的是本仓库冻结 commit 的技能库，不再从 git 拉

---

## 10. 待定事项

1. GPT 和 Gemini 的具体版本
2. 测试任务具体是哪 8 个
3. SFT / RL 的具体设置（数据、奖励、训练规模）：后面再定，复用本文的任务划分和共用组件

已定（11-23）：Nominal / Oracle 暂不跑；调用预算 60 次；观察 profile 用 `sticky/benchmark`；每个 VLM 方法用 Qwen3.5-4B + Claude Opus 5.5 + GPT + Gemini；每个 episode 跑 1 次。
