# 文档索引

整个仓库的文档从这里找。`docs/` 下按用途分目录；benchmark 和各模块的文档留在各自目录里（很多是脚本生成的，路径不能动），这里只列出来。

## docs/ 的目录

| 目录 | 放什么 | 状态 |
|---|---|---|
| [motion/](motion/) | 运动规划与碰撞的设计、执行计划、待删清单、待定问题 | 现行，跟着代码改 |
| [skills/](skills/) | 每个技能在物理上一步一步做什么；代码地图 | 现行，跟着代码改 |
| [reference/](reference/) | 脚本生成的 ID 表、policy 目录、contract 关系图 | 生成文件，不要手改 |
| [guides/](guides/) | 操作步骤：新建任务、资产、场景与标注 | 现行 |
| [archive/](archive/) | 写的是过去某个时间点的状态：旧审计、旧接口提案、验证记录、交接文档、旧图 | 只读，不再更新 |

新文档放哪：描述现在的设计和要做的事 → `motion/` 或 `skills/`；一次会话的交接 → `archive/handoffs/HANDOFF_<日期>_<主题>.md`（交接完就是历史）；计划里做完的过程记录 → `archive/`。

## 运动规划与碰撞（motion/）

1. [MOTION_ARCHITECTURE.md](motion/MOTION_ARCHITECTURE.md)：运动规划的分层设计。规则、各层职责、9.3 迁移步骤。**先读这篇。**
2. [COLLISION_PLAN.md](motion/COLLISION_PLAN.md)：碰撞与运动规划的执行计划：做什么、按什么顺序、做到什么算完；第 5 节基线、第 9 节"试过、不要再做的"。
3. [COLLISION_CLEANUP.md](motion/COLLISION_CLEANUP.md)：代码里还没删、没改的特殊实现，逐条标类别和归属步骤。
4. [HAND_PLAN.md](motion/HAND_PLAN.md)：选手（pick / place 用哪只手是目标集合的一个维度）和剩下的旧技能迁移的计划（9.3 第 9 步起，11-24）。
5. [CONTAINER_COLLIDERS.md](motion/CONTAINER_COLLIDERS.md)：容器碰撞体和真实网格对不上（未改，改了动基线）。

## 技能（skills/）

[skills/README.md](skills/README.md) 是入口：阅读顺序、哪些技能已走运动分层。[skills/CODE_MAP.md](skills/CODE_MAP.md) 讲代码怎么组织。各技能一篇：[接近与离开](skills/approach_leave.md)、[pick](skills/pick.md)、[place](skills/place.md)、[drop / hover](skills/drop_hover.md)、[wipe](skills/wipe.md)、[搬运姿态](skills/carry.md)、[导航与收臂](skills/navigate.md)、[open](skills/open.md)、[close](skills/close.md)、[push](skills/push.md)、[stir](skills/stir.md)、[mark_spots](skills/mark_spots.md)、[姿态](skills/posture.md)。

## 参考（reference/，生成文件）

| 文件 | 生成命令 |
|---|---|
| [INTERFACE_IDS.md](reference/INTERFACE_IDS.md)：SkillNode / Contract / policy 公开 ID | `python tools/build_skill_library.py` |
| [POLICY_CATALOG.md](reference/POLICY_CATALOG.md)：policy 能力目录 | `python tools/render_policy_catalog.py` |
| [contract_layers.svg](reference/contract_layers.svg)、[预览 png](reference/contract_layers_preview.png)：contract 分层关系图 | `python tools/render_contract_layers.py` |

`tests/test_policy_catalog.py` 检查这些文件和生成结果一致。

## 操作指南（guides/）

- [CREATE_TASKS.md](guides/CREATE_TASKS.md)：新建任务、新增可抓取资产、选择或扩展场景、改 scene 后重新标注。

## 历史（archive/）

| 文件 | 内容 |
|---|---|
| [COLLISION_AUDIT.md](archive/COLLISION_AUDIT.md) | 2026-10-31 碰撞检查现状盘点（代码注释里的"审计 x.y"、"COLLISION_AUDIT §n"指它的章节） |
| [PICK_6_1_2026-11-06.md](archive/PICK_6_1_2026-11-06.md) | 计划 6.1 pick 暂停时的过程记录 |
| [GT_POLICY.md](archive/GT_POLICY.md) | 2026-10-01 的原子 GT policy 清单 |
| [CONTRACT_PROPOSAL.md](archive/CONTRACT_PROPOSAL.md) | contract_001–008 family 接口提案（已被动词 SkillNode 库取代） |
| [POLICY_VERIFICATION.md](archive/POLICY_VERIFICATION.md) | 2026-10-01/02 policy 物理验证记录 |
| [KNOWN_LIMITATIONS.md](archive/KNOWN_LIMITATIONS.md) | 验证第 30 轮的已知限制 |
| [PHYSICS_AUDIT.md](archive/PHYSICS_AUDIT.md) | 2026-10 物理与资产审计 |
| [handoffs/](archive/handoffs/) | 会话交接：10-24 support 碰撞板、10-29 六条失败路线、10-30 http planner 失败、11-14 carry tilt held、11-25 两只手（给 bench 作者） |
| [benchmark_v1/](archive/benchmark_v1/) | benchmark v1 的图（`make_figs.py` 生成） |

## benchmark 的文档（在 benchmark/ 下）

- 总说明：[benchmark/README.md](../benchmark/README.md)；评测指标与失败分类：[EVALUATION_SPEC.md](../benchmark/EVALUATION_SPEC.md)；v2 结果：[EVALUATION.md](../benchmark/EVALUATION.md)、[RESULTS.md](../benchmark/RESULTS.md)。
- **v6（当前）**：[README](../benchmark/v6/README.md)。
  - 任务设计：[VARIANTS_zh](../benchmark/v6/VARIANTS_zh.md)（全部 variant 说明）、[VARIANT_FOCUS_zh](../benchmark/v6/VARIANT_FOCUS_zh.md)、[TRACKS](../benchmark/v6/TRACKS.md)、[SCORING_zh](../benchmark/v6/SCORING_zh.md)、[TIER_REVIEW_1120_zh](../benchmark/v6/TIER_REVIEW_1120_zh.md)、[SUBSTITUTION_STATS_zh](../benchmark/v6/SUBSTITUTION_STATS_zh.md)、[PLAN_DEPENDENCE_zh](../benchmark/v6/PLAN_DEPENDENCE_zh.md)。
  - 路线：[ROUTES](../benchmark/v6/ROUTES.md)、[SUCCESS_ROUTES_zh](../benchmark/v6/SUCCESS_ROUTES_zh.md)。
  - 物理侧（给 muqingj）：[HANDOFF_MUQINGJ_1121_zh](../benchmark/v6/HANDOFF_MUQINGJ_1121_zh.md)（最新）、[HANDOFF_MUQINGJ_1118_zh](../benchmark/v6/HANDOFF_MUQINGJ_1118_zh.md)、[PHYSICS_TODO](../benchmark/v6/PHYSICS_TODO.md)、[PHYSICS_EXCLUDED_zh](../benchmark/v6/PHYSICS_EXCLUDED_zh.md)、[SKILL_FIX_LIST](../benchmark/v6/SKILL_FIX_LIST.md)、[SKILL_ISSUES_zh](../benchmark/v6/SKILL_ISSUES_zh.md)。
- v5：[README](../benchmark/v5/README.md)、[REPORT](../benchmark/v5/REPORT.md)（10-31 基线）、[CAPABILITIES](../benchmark/v5/CAPABILITIES.md)、[VALIDATION](../benchmark/v5/VALIDATION.md)。
- v3 / v4：[README](../benchmark/v3/README.md)、[MATRIX](../benchmark/v3/MATRIX.md)、[RESULTS](../benchmark/v3/RESULTS.md)、[EVALUATION](../benchmark/v3/EVALUATION.md)、[V4_HARD_VALIDATION](../benchmark/v3/V4_HARD_VALIDATION.md)。

## 各模块的 README

[仓库 README](../README.md) · [zeno_skills/SKILL.md](../zeno_skills/SKILL.md) · [skill_library](../skill_library/README.md)（[SKILLS.md](../skill_library/SKILLS.md)、[验证状态](../skill_library/verification/STATUS.md)） · [contract_library](../contract_library/README.md) · [policy_library](../policy_library/README.md)（[POLICY_COVERAGE.md](../policy_library/POLICY_COVERAGE.md)） · [episode](../episode/README.md) · [env_service](../env_service/README.md) · [failure_injection](../failure_injection/README.md) · [skill_ext](../skill_ext/README.md) · [EmbodiedGen V2 资产](../assets/EMBODIEDGEN_V2_ASSETS.md) · [演讲稿](../presentations/SPEAKER_NOTES.md)
