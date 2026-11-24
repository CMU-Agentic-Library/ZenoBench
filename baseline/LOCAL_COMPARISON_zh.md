# v6 本地 VLM 对比协议

本轮在 Isaac Sim 6.0.0.1 上运行，原生执行和规划方法沿用 `7846509`。Graph Manager 的本地服务配置另记录在每次尝试的 `local-provider.json` 中。结果表列出每个模型和方法已计分的局数、相同布局上的得分，以及脚本参考路线的原生判定。[本轮结果表](results/local_v6_sim6.md)

同一组任务用于比较三个本地模型。Qwen3.5-4B 与 Qwen3.5-27B 给出同一家族的规模对照，InternVL3.5-8B 加入另一种视觉语言架构。精确的权重 revision 在 `baseline/comparison.py` 中。vLLM 0.32.0 使用 BF16，温度为 0，单次最多生成 4,096 token，上下文长度 32,768。Qwen 关闭显式思考。所有模型端点绑定在实验机的回环地址上。

| 部分 | 方法和条件 | 每模型局数 |
| --- | --- | ---: |
| 主实验 | OpenLoop、ReAct、CodeAsPolicies、SayPlan、GraphManager，共用 sticky/benchmark | 5 × 1,510 |
| 替代提示 | ReActHint，使用相同技能菜单、观测和调用预算 | 316 |
| 额外观测 | ReAct 使用 sticky/privileged，额外获得匿名任务物体及位置，仍须到场观察后才能操作 | 316 |

三个模型的主实验共 22,650 局。两项消融另有 1,896 局。主实验直接读取公开批次中的任务、具体布局和种子，包含 Control 330 局、Task 1,100 局、Action + Task 80 局。1,060 局的理想选择可用，450 局不可用。两项消融各选择每种具体布局出现的第一个评测种子，并与主实验中同一局的 ReAct 比较。上述划分在运行前确定。

仓库的 VLM 基线方案规定主实验使用 `sticky/benchmark`。物体抓稳后在搬运中固定，抓取和放置仍通过物理执行。原始脚本批次的 profile 随类别变化，330 个 Control 和 80 个 Action + Task 条目为 `benchmark`（无搬运辅助），1,100 个 Task 条目为 `sticky_snap/gt`（提供 GT，允许修正失败的抓放）。本轮脚本参考统一为与主实验相同的搬运和抓放条件。引用历史脚本分数时需标明对应的 profile 和仿真版本。[VLM 基线设置](README.md) · [不同执行辅助的含义](../episode/README.md)

为尽早获得跨任务的同局对照，另用三个仿真槽优先运行每个任务在主批次中首次出现的标准 ReAct 局，覆盖 30 个任务 × 3 个模型。选取顺序取自任务清单，30 局均为种子 10，其中 6 局的理想选择不可用。每条结果只计入原有主实验一次。可在调度器传入 `--method ReAct --first-layout-per-task` 复现这个子集。

这 30 个相同初始条件也逐个运行批次指定的脚本参考路线，以检查同一套底层技能能否完成该路线。脚本单独计数，沿用 `sticky/benchmark` 和仓库原生评分。结果表把每条脚本及其首个执行错误与同局三个模型并排展示。T01 的 `overhang_ready` 是独立校准局，T12 种子 19 的参考路线用于复核下文的九局零分。

例如 T12 收拾玩具的 `bins_capacity__half_bin_and_tray_duck_dining` 布局（种子 19），Qwen3.5-4B 三种条件的配置哈希都是 `31ff2877cf88`。三者的初始观测都有 164 个预先标注的静态地点，当时的可见物体清单为空。额外观测条件还把 11 个任务相关实体的名称、类型和 GT 三维坐标写进提示，包括用匿名编号标识的玩具车和橡皮鸭。常规 ReAct、替代提示和额外观测分别调用技能 6、7 和 6 次，这一局均得 0 分。静态地点取自场景标注，可见物体由环境按头部相机的可见性与遮挡计算。[观测生成](../benchmark/observation.py) · [VLM 实际收到的提示](prompt.py)

Graph Manager 使用固定的子模块、当前 checkout 的 71 项技能和 v6 任务索引，保留其原生 Harness 工具调用。它每回合可以多次调用模型，原生停止条件还包括 5 次重规划和约 27 分钟的时间预算。InternVL 发布的视觉对话模板用于普通请求；有工具时，通过其 Qwen3 语言基座的 ChatML 工具格式提供函数签名和返回值。模型工具协议影响 Graph Manager 的横向比较。其余四种方法沿用仓库统一的文本调用格式。

Harness 的手动模型配置须声明 `contextWindow: 32768` 和 `maxTokens: 4096`，与本地 vLLM 实际容量相同。这样 Harness 可以按自己的策略及时压缩历史。最早一批 Graph Manager 尝试遗漏容量声明，沿用了 262,144 token 的默认值，其中一次请求达到 35,298 token。已归档该配置下的尝试，并对三个模型重跑；正式表只接受带本地容量记录的 Graph Manager 结果。

本分支最初在按布局命名的结果目录下创建 Graph Manager 工作目录。复查真实 Harness 会话时，发现发给模型的 `sandbox:policy` 消息自动附上了这个绝对路径。例如 T02 的旧消息包含 `s10_block_put_away__gone_toy_block`，直接提示了布局。已将三个模型分片 0–6 的 21 个实验配置列入重跑，旧得分从表中撤回。修复后，每次会话使用独立的 `/tmp/zenobench-graph-<随机串>`，轨迹仍保存在带布局名的结果目录。复核三个模型在 T02 的真实消息，均有随机工作目录，均未出现完整布局名。三条会话编号依模型 4B、27B、InternVL 为 `T02_stack_blocks-61bde01b`、`T02_stack_blocks-56ff37c7`、`T02_stack_blocks-2c9b8856`。汇总器逐局核对工作目录和本地模型配置。

## 运行

先将 Git LFS 场景资产和 `baseline/graph_manager` 子模块取到本地。仓库原协议使用 Isaac Sim 5.1、Isaac Lab 2.3.2 和 cuRobo 0.7.8。vLLM 和规划器各使用独立 Python 环境。下面是一个模型和一个方法的完整分片。其他方法和模型替换对应参数。

```bash
git submodule update --init baseline/graph_manager
git lfs pull --include='tasks/**/scene*.usd,scenes/**,sim/**,usd/**,robot_sources/**,assets/**'
```

```bash
export ZB_RUN=/path/to/local-v6-run
export MODEL=qwen3.5-4b
export CUDA_DEVICE_ORDER=PCI_BUS_ID
CUDA_VISIBLE_DEVICES=5 VLLM_PY=/path/to/vllm/bin/python \
  bash baseline/serve_local.sh "$MODEL" /path/to/pinned/Qwen3.5-4B 8101 0.52
```

在独立终端启动环境服务。CUDA 设备用于 cuRobo，ZENO_SIM_GPU 填写 Kit 日志中同一张卡的 Vulkan 索引。

```bash
CUDA_VISIBLE_DEVICES=0 ZENO_SIM_GPU=0 OMNI_KIT_ACCEPT_EULA=YES \
  "$ISAACLAB_PYTHON" -m env_service.server --host 127.0.0.1 --port 8800 --max-sims 2 \
  --catalog benchmark/v6/tasks.json=sticky/benchmark --profiles sticky/benchmark,sticky/privileged \
  --log-dir "$ZB_RUN/native"
```

在规划器终端设定相同的 ZB_RUN 和 MODEL，运行评测并生成 Markdown 表格。GraphManager 额外传入 `--graph-bin /path/to/graph-env/bin/graph-manager-run`。多个 GPU 可以分别启动环境服务，使用相同的原生结果目录，再以相同的 `--shards K` 和互不重复的 `--shard 0…K-1` 划分同一模型和方法。

```bash
python -m baseline.comparison --model "$MODEL" --method ReAct \
  --vlm-url http://127.0.0.1:8101/v1 --server http://127.0.0.1:8800 \
  --out "$ZB_RUN/planner" --native-dir "$ZB_RUN/native"
python -m baseline.report --out "$ZB_RUN/planner" --native-dir "$ZB_RUN/native" \
  --markdown "$ZB_RUN/comparison.md"
```

每个结果通过 exp_id 对应到仿真服务记录的最终状态和技能轨迹。分表使用各模型共同完成的相同局。任务成功、正分和满分分别统计，保留中途服务失败的日志，重新运行同一分片会继续未完成的局。技能错误表按原生错误码统计出现过执行、观测、前置条件或参数错误的局，同时列出整局没有调用任何技能的情况。判断一个正确的替代动作是否被物理执行阻断，仍需结合具体动作和当时状态。

环境服务在接受下一次技能调用前检查从就绪起算的 60 分钟上限。以 T10 餐后清理、种子 10 的 Qwen3.5-4B / SayPlan 为例，环境实际执行了 18 次技能，第 19 次请求因超时被拒绝。规划器随后调用原生评分器，得 0 分。成本表记录 `service_limit`，技能数按实际执行的 18 次统计。

在 450 个理想选项不可用的布局与种子组合中，v6 给该布局的最佳可用方案记 1.0 分。其中 373 局有多个可计分档位（`D=1`），77 局只有一个可计分档位（`D=0`）。配对分表另列达到最佳档且最终成功的比例。例如积木任务 `block_put_away__gone_toy_block` 的理想第三块木块缺失，用玩具积木搭成三层可得满分。种子 10 的参考脚本先把木块 A 叠到木块 B 上，第 8 步开柜时失败，未执行第 19 步起的寻找、拾取和堆叠玩具积木。仅凭路线里的 `role: alternative` 标签无法确认机器人已使用替代物。

### 同一个零分如何产生

首个对照局 T24 要求“给在书房做作业的孩子带些吃的”。在 `apple_on_table` 布局、种子 10 下，成功条件是苹果在书桌上且右手为空。参考脚本 6 步完成，得 1.0 分。三套 ReAct 使用相同初始局 `959e5e1cebbf`，以下记录均来自 Isaac Sim 6.0.0.1。

| 模型 | 实际执行与终止原因 | 原生得分 | 原生记录编号 |
| --- | --- | ---: | --- |
| Qwen3.5-4B | 拿到了苹果，随后在卧室和客厅间移动。后续模型回复解析失败，结束时手中仍是苹果 | 0.0 | `T24_snack_for_kid-a026dbf6` |
| Qwen3.5-27B | 把早餐碗成功放到书桌，报告已经完成。苹果仍在原处 | 0.0 | `T24_snack_for_kid-88a99d8f` |
| InternVL3.5-8B | 拿到了苹果。60 次技能调用中有 55 次返回未观测到目标，最终用尽预算 | 0.0 | `T24_snack_for_kid-261deafa` |

逐步动作和最终目标判定可在 `$ZB_RUN/native/T24_snack_for_kid/<原生记录编号>/result.json` 中复核。这一局说明记录动作、错误码和最终物体位置，有助于区分选错交付物、未交付和访问未观测目标。

### 给模型任务相关物体真值后，同一局发生了什么

Qwen3.5-27B 在同一个 T24 布局和种子上完成了三种 ReAct 条件。三局的配置哈希均为 `cc2635286b50`。

| 模型获得的信息 | 实际技能调用 | 最后交付的物体 | 原生得分 | 原生记录编号 |
| --- | ---: | --- | ---: | --- |
| 标准观测 | 14 | 早餐碗 | 0.0 | `T24_snack_for_kid-88a99d8f` |
| 标准观测加替代提示 | 11 | 早餐碗 | 0.0 | `T24_snack_for_kid-04d01013` |
| 特权观测 | 6 | 苹果 | 1.0 | `T24_snack_for_kid-ebbf8a5d` |

特权局开场的可见物体清单为空，但系统另给的任务相关物体清单只有 `apple_1`，并附有世界坐标 `[3.706, 5.821, 0.876]`。模型随后在餐厅找到苹果，把它放到书桌。这个条件同时提示了该选哪件物体以及它的位置。单独一个样本无法区分这两项信息各自的贡献。这个布局有理想物体，属于 `D=0` 对照局。

最后一次 `place` 返回了 `POLICY_FAILED`。逐步记录显示苹果已经放下，出错的是随后的收臂，手臂距指令位置还差 0.011 米。最终苹果在 `desk_1/top`、右手为空，两个成功条件均满足。若把任一技能报错的局都计作任务失败，会把这一局的满分判错。

仓库另有逐次技能调用的 Planning Correctness，可从这些轨迹直接计算。标准 ReAct 的 14 次调用中，13 次判为合理，1 次无法判定。加替代提示时 11 次均判为合理，两局都交付了错误的物体。特权条件下 6 次均判为合理，包含最后一次收臂出错的 `place`。因此表中同时保留可判定调用的比例、逐次合理性和任务最终得分。[逐次判定规则](../benchmark/metrics.py) · [指标规范](../benchmark/EVALUATION_SPEC.md)

### 标准观测下，三种 ReAct 如何完成送书任务

T01 的 `overhang_ready` 布局、种子 10，要求把书带到餐桌。三套模型和脚本参考路线的初始局哈希相同（`8ab4123ec0e5`）。三套模型开场的可见物体清单均为空。脚本用 7 步把书放到餐桌并松手，得 1 分。此处有理想物体，是 `D=0` 对照局。

三套模型的原生日志中，书的初始坐标与底盘位姿一致。各局独立渲染 640 × 480 的头部相机图像。逐对比较三张首帧，RGB 通道的平均绝对像素差为 0.194–0.204（取值范围 0–255）。

| 模型 | 实际调用 | 行为与最终判定 | 原生得分 | 原生记录编号 |
| --- | ---: | --- | ---: | --- |
| Qwen3.5-4B | 8 | 拿到书并移到餐桌旁，模型在仍拿着书时主动报告完成。餐桌上的书和空手两个条件都未满足 | 0.0 | `T01_book_to_dining_table-6b19d5ed` |
| Qwen3.5-27B | 11 | 第一次拾取距离太远，移近后拿到书。放置连续四次返回无可达位置，第五次指定靠近早餐杯，成功将书放在餐桌并松手 | 1.0 | `T01_book_to_dining_table-8c120975` |
| InternVL3.5-8B | 60 | 50 次导航、10 次拾取。10 次拾取时底盘都距书 2.18 米，前置条件拒绝了这些调用，最终用尽预算 | 0.0 | `T01_book_to_dining_table-77c6b185` |

这组配对同时观察到了提前结束、对执行反馈更换放置参数、重复违反距离前置条件。Qwen3.5-27B 的四次放置失败均有原生执行日志，最后两个任务条件仍均满足。

### 缺少理想收纳篮时，模型把什么收起来了

T12 的 `bins_capacity__half_bin_and_tray_duck_dining` 布局、种子 19，普通任务指令只说快到睡觉时间，把孩子的玩具收起来。理想的收纳篮已移除，场景中有小收纳箱和浅盘。获得正分需要把玩具车和橡皮鸭分别放入小箱或浅盘并松手，两件玩具可以分开存放。满分还要求原有的六块积木最终均在小箱内。该局有 1.0 和 0.6 两个可接受档位（`D=1`）。

| 模型 | 标准 ReAct 调用数 | 加替代提示调用数 | 特权观测调用数 | 三种条件下的原生得分 |
| --- | ---: | ---: | ---: | --- |
| Qwen3.5-4B | 6 | 7 | 6 | 0 / 0 / 0 |
| Qwen3.5-27B | 58 | 21 | 4 | 0 / 0 / 0 |
| InternVL3.5-8B | 38 | 42 | 25 | 0 / 0 / 0 |

Qwen3.5-27B 在标准和提示两局里都把装有积木的小箱搬上了书架。提示局中，它随即报告已经把玩具收好，车仍在地面，鸭子仍在餐桌。InternVL 的特权局拿到了玩具车，随后六次以书架顶面为放置目标，两次被距离前置条件拒绝，四次返回顶面没有空位。书架顶面本身也不满足将玩具放入容器的判据。这些轨迹分别暴露了任务指令、模型所选物体与容器、具体放置错误之间的关系。[布局和原生评分条件](../benchmark/v6/tasks.json)

为复核底层可行性，同一配置 `31ff2877cf88` 上执行了目录指定的 15 步脚本。第 10 步把车放入浅盘，第 15 步把鸭子投入小箱。原生终态确认六块积木均在箱内、小箱直立、右手为空、无掉落，任务成功并得满分 1.0。这为该布局提供了一条实际完成的替代路线。该脚本预先知道目标物体和路线，九次 VLM 尝试均未达到可计分结果。

## Isaac Sim 6 独立实验

目标实例的驱动为 NVIDIA 595.91.07。Isaac Sim 5.1 在启用 RTX 相机时于 `librtx.scenedb.plugin.so` 崩溃。此实例使用单独的 Isaac Sim **6.0.0.1** 环境和输出目录。跨版本比较需要考虑接触动力学、渲染和执行器行为的变化。

实例有 6 张 96 GB 的 RTX PRO 6000 Blackwell Server Edition。Qwen 4B、Qwen 27B 和 InternVL 8B 分别常驻 GPU 5、3、4，仿真服务分布在全部六张卡上。全量队列扩容后由 16 个和 6 个并发槽组成，另有同局对照和补跑。表中的墙钟时间及触发一小时时限的次数受这一同机负载影响。

仿真环境使用 Python 3.12、PyTorch 2.11.0+cu130、Isaac Sim 6.0.0.1、Isaac Lab 2.3.2 的源码和按 sm_120 编译的 cuRobo 0.7.8。使用 `isaacsim[all,extscache]` 安装完整扩展。将 2.3.2 wheel 中含有 `apps/` 和 `source/` 的 `isaaclab/` 目录解包到 `LAB_SOURCE`。以下命令生成适配后的独立副本，并使每局原生记录包含版本和适配清单的 SHA-256。

```bash
"$ISAACLAB_PYTHON" baseline/sim6/prepare_lab.py "$LAB_SOURCE" "$LAB_SIM6"
export PYTHONPATH="$LAB_SIM6/source/isaaclab${PYTHONPATH:+:$PYTHONPATH}"
export ZENO_LAB_COMPAT_MANIFEST="$LAB_SIM6/compatibility.json"
```

用上面的环境启动 HTTP 服务，在评测和汇总两条命令中都传入 `--sim-version 6.0.0.1`。生成的表头显示实际版本，汇总器检查每个原生结果的版本号。用于相机和参考技能验证的局存放于规划器结果目录之外。

同一张 GPU 上有多局同时请求 `/initial_task` 时，原服务会串行启动模拟器，等待前一局启动也计入 780 秒的启动限时。本轮出现过两次尚未拿到初始观测的超时，剩给实际启动的时间分别为 323 秒和 49 秒。多个规划器共用 GPU 时，可在发出请求前排队。以下命令仅在本轮的两个专用规划器环境中注册启动队列。端口映射应与实际运行环境服务的物理 GPU 对应。计分、模型请求、执行中的技能和从环境就绪起算的时限沿用原实现。

```bash
mkdir -p "$ZB_RUN/startup_queue"
cp baseline/sim6/startup_queue.py "$ZB_RUN/startup_queue/zenobench_startup_queue.py"
for py in "$PLANNER_PYTHON" "$GRAPH_PYTHON"; do
  "$py" - "$ZB_RUN" <<'PY'
from pathlib import Path
import sys, sysconfig
root = Path(sys.argv[1]).resolve()
directory = root / "startup_queue"
ports = {8870 + device: device for device in range(6)}
setup = f"import zenobench_startup_queue; zenobench_startup_queue.install({str(directory)!r}, {ports!r})"
(Path(sysconfig.get_path("purelib")) / "zenobench_startup.pth").write_text(f"{directory}\n{setup}\n")
PY
done
```

以下例子给 8860、8861、8862 三个仿真服务各分配两个并发局，在不同模型和方法间轮转。各服务的 `--log-dir` 都指向 `$ZB_RUN/native`。端口 8101、8102、8103 分别对应 Qwen 4B、Qwen 27B 和 InternVL 8B。收到 SIGTERM 后，调度器等待正在运行的局结束。再次启动时继续剩余的局。

```bash
python -m baseline.launch_comparison --run-dir "$ZB_RUN" --sim-version 6.0.0.1 \
  --servers 8860=2 8861=2 8862=2 --graph-bin /path/to/graph-env/bin/graph-manager-run
```

运行期间增加空闲的仿真槽位时，可使用相同的 `--run-dir`，另给新调度器指定 `--dispatch-dir "$ZB_RUN/dispatch-extra"` 和新分配的 `--servers`。调度器按模型、方法、布局和种子锁定每一局。其他调度器可以继续领取剩余的局，已计分的局会自动跳过。补跑受服务中断影响的一个组合时，再指定 `--model` 和 `--method`，它会沿用原分片编号和输出目录。
