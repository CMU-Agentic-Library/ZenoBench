# ZenoBench-Sub 分级替代评测：怎么跑

对应设计文档《ZenoBench-Sub：分级替代评测设计》。代码在 `benchmark/v6/substitution_eval.py`，测试在 `benchmark/v6/tests/test_substitution_eval.py`。

## 一、跑哪些局

10 个任务、28 个设计，每个设计 10 个 seed，共 280 局：

| 侧 | 局数 | 含义 |
|---|---|---|
| A | 100 | 原物体在，而且在眼前或者好找 |
| A_hidden | 25 | 原物体在，但收在柜子里或别的房间 |
| B | 155 | 原物体用不了，原因分四类：缺失、被占用、能力不足、看着像但不能用 |

同一个任务的 A 和 B 指令完全一样，区别只在场景。`--pairs` 会检查这一点。

```bash
python -m benchmark.v6.substitution_eval --pairs      # 列出 A/B 配对表，并检查配对是否成立
```

批次文件已生成：`benchmark/v6/batches/substitution_pairs.json`。跑法和平常一样：

```bash
# 仿真机：必须是含 11-25 改动的代码（scoring.score 会记下成立的是哪个分支）
$ISAACLAB_PYTHON -m env_service.server --port 8800 --max-sims 2 \
    --catalog benchmark/v6/tasks.json=sticky/benchmark

# 规划器侧
$PY -m baseline.run_http --server http://localhost:8800 --model qwen3.5-4b \
    --policy baseline.react:ReAct --batch benchmark/v6/batches/substitution_pairs.json
```

## 小批次：只跑有替代的局

`benchmark/v6/batches/substitution_smoke.json` 共 103 局，覆盖 20 个任务的 50 个布局，每个布局 2 个 seed（T12 有一个布局只有 1 个 seed）。

挑选标准：指令点名了要用的东西或者放的地方；这个东西用不了（缺失、被占用、装不下）；场景里有别的东西能顶上。比如 T03，宽储物箱没有或者满了，就用收纳筐、托盘代替。

| 不可用原因 | 局数 | 例子 |
|---|---|---|
| 缺失 | 56 | T03 没有储物箱、T04 没有玻璃杯、T15 没有锅盖、T16 没有零食盒、T21 没有纸巾、T30 没有碗、T02 第三块木块没了、T09 没有锅盖或小番茄不够 |
| 被占用 | 26 | T15 锅盖盖着别的锅、T16 零食盒装着蜡笔、T18 一只碗装着剩菜、T05 笔正被人用着、T17 锅盖盖着炖菜 |
| 能力不足 | 19 | T03 小箱子放不下擀面杖、T04 只有塑料杯盛冰饮、T10 垃圾桶满了、T12 玩具箱满了、T16 零食盒满了、T23/T29 玩具盒满了 |
| 看着像但不能用 | 2 | T11 果篮原来的位置上是个用过的碗 |

下面这些情况没选：
- 指令没点名用什么：T07"热完关掉用过的电器"、T24"拿点吃的"、T26"放回放玩具的地方"（T12 也没点名，但考的是箱子满了要换，算能力不足收进来了）。
- 被占的是地方不是东西：桌子满了、书架满了。
- T18 柜门卡住：仿真里还没实现。

**怎么判分：**
- 10 个配对任务里的布局按档位表判：命中、bad、抢占。
- 其余布局只按档判：1.0 档就是这个布局最好的替代，0.3 到 0.6 档是次一档的替代，失败就是没替代成。
- 两类的失败都会按结束原因细分：放弃、预算用完、自称完成、出错中断。

建议跑两组，共 206 局：

```bash
B=benchmark/v6/batches/substitution_smoke.json
$PY -m baseline.run_http --server http://localhost:8800 --model qwen3.5-4b --policy baseline.react:ReAct --batch $B
$PY -m baseline.run_http --server http://localhost:8800 --model qwen3.5-4b --policy baseline.react:ReActHint --batch $B

python -m benchmark.v6.substitution_eval --native $ZB_RUN/native \
    --run ReAct@qwen=baseline/runs/ReAct@qwen3.5-4b --run ReActHint@qwen=baseline/runs/ReActHint@qwen3.5-4b \
    --out baseline/results/substitution_smoke.md
```

- ReAct 看替代能力本身：失败多不多，失败里是放弃、一直找到预算用完，还是没换就说做完了；替代的时候拿的是不是最好的那个。
- ReActHint 看"可以替代"这句提示有没有让它更愿意换。这批只有 B 侧的局，看不到会不会乱换；要看乱换，得另外跑全量批次里的 A 侧。
- 重新生成：`python -m benchmark.v6.substitution_eval --subset benchmark/v6/batches/substitution_smoke.json`，选哪些布局写在 `SUBSTITUTION_LAYOUTS`。

## 二、算指标

```bash
python -m benchmark.v6.substitution_eval \
    --run ReAct@qwen=baseline/runs/ReAct@qwen3.5-4b \
    --run SayPlan@qwen=baseline/runs/SayPlan@qwen3.5-4b \
    --native $ZB_RUN/native --k 3 \
    --out baseline/results/substitution.md --json baseline/results/substitution_rows.jsonl
```

- `--run 标签=目录`：读取目录下所有 `result.json`。仿真原生结果带 `calls`，直接读；规划器结果只有 `exp_id`，会到 `--native/<任务>/<exp_id>/result.json` 去找对应的原生结果。
- 输出包括（漏替代按规划器的结束原因再分成放弃、预算用完、自称完成、出错中断）：
  - A 侧：误替代率
  - B 侧：漏替代率、抢占率、命中率、bad 率、else 率，并按不可用原因分开列
  - 两侧都有：完成率、严格成功率、平均效率 E、每个设计的 pass@1 / pass@k / pass^k

## 三、怎么判定"选了什么"

不要求模型声明，从结果里读：

1. **成功的局**：看判分时成立的是哪一档、哪个分支（`score.branch_atoms`），从中取出被用来完成任务的物体，查它在本任务里的档位：ideal、moderate 或 bad。T18 要摆两件，以第二件、也就是替代品那件为准。T07 看成立的档就知道用的是微波炉还是灶。
2. **失败的局**：取最后一次拿在手里的候选物体。手里拿过别的东西、但一个候选都没拿过的，记为 else。什么都没拿过的，记为漏替代。
3. **被占用的理想物**：拿来用了记为抢占，不算命中。例如把炖锅上的锅盖拿过来、把装着蜡笔的零食盒拿来用。

档位只看物体相对任务，不看场景。"本布局最好一档"取自该布局 1.0 档的设计：A 侧是 ideal，B 侧是 moderate，T04 `no_cup_kid` 是 bad，因为那个布局只有孩子的塑料杯。

## 四、为这套评测改了什么

- `scoring.score` 现在会额外记下成立的分支，字段是 `branch` 和 `branch_atoms`。旧的结果文件没有这两个字段：成功局里只有一个分支的照样能判，有多个分支的只能退回看"最后拿过什么"。
- 4 个 A 设计补了替代档。以前用了替代品直接判失败，现在算完成，同时记一次误替代：
  - T15 `lid_by_pot`：用盘子盖，0.6
  - T16 `box_on_counter`：用碗装，0.6
  - T18 `bowls_in_cabinet`：第二只用盘子，0.6
  - T30 `bowl_on_cabinet`：拿马克杯或杯子 0.6，拿盘子 0.3
- 3 个 B 布局移除了场景自带的理想物。它们原本注明"没有杯子"或"只有一只碗"，可房子里自带的 3 个杯子、3 只碗还在，而且会被当作同种替身判成 1.0，等于理想物其实在场。涉及 T13 `no_cup`，以及 T18 `one_bowl`、`bowl_in_use` 两个设计。

## 五、没纳入配对的

- T09 `pot_in_use`：理想物（空锅）一直在，这个设计考的是别在昨天的汤里煮。
- T18 `door_stuck`：另一个柜子里有干净碗，变的是从哪拿，不是拿什么；而且柜门卡住在仿真里还没实现。
- T03 `large_only`、T21 `tissue_on_tv_stand`：这两个 A 场景里没有可替代的东西，误替代不会发生。保留它们，用来算完成率和效率。
- 其余 19 个任务：指令没有点名某个手段，或者考的是找东西、放置等别的能力，只报完成率、效率和 pass@k。
