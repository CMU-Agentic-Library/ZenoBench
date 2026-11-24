# v6 本地 VLM 对比协议

本轮在 Isaac Sim 6.0.0.1 上运行，原生执行和规划方法沿用 `7846509`。Graph Manager 的本地服务配置另记录在每次尝试的 `local-provider.json` 中。结果表列出每个模型和方法已计分的局数、相同布局上的得分，以及脚本参考路线的原生判定。[本轮结果表](results/local_v6_sim6.md)

同一组任务用于比较三个本地模型。Qwen3.5-4B 与 Qwen3.5-27B 给出同一家族的规模对照，InternVL3.5-8B 加入另一种视觉语言架构。精确的权重 revision 在 `baseline/comparison.py` 中。vLLM 0.32.0 使用 BF16，温度为 0，单次最多生成 4,096 token，上下文长度 32,768。Qwen 关闭显式思考。所有模型端点绑定在实验机的回环地址上。

| 部分 | 方法和条件 | 每模型局数 |
| --- | --- | ---: |
| 主实验 | OpenLoop、ReAct、CodeAsPolicies、SayPlan、GraphManager，共用 sticky/benchmark | 5 × 1,510 |
| 替代提示 | ReActHint，使用相同技能菜单、观测和调用预算 | 316 |
| 额外观测 | ReAct 使用 sticky/privileged，额外获得匿名任务物体及位置，仍须到场观察后才能操作 | 316 |

三个模型的主实验共 22,650 局。两项消融另有 1,896 局。主实验直接读取公开批次中的任务、具体布局和种子，包含 Control 330 局、Task 1,100 局、Action + Task 80 局。1,060 局的理想选择可用，450 局不可用。两项消融各选择每种具体布局出现的第一个评测种子，并与主实验中同一局的 ReAct 比较。上述划分在运行前确定。

例如 T12 收拾玩具的 `bins_capacity__half_bin_and_tray_duck_dining` 布局（种子 19），Qwen3.5-4B 三种条件的配置哈希都是 `31ff2877cf88`。三者的初始观测都有 164 个预先标注的静态地点，当时的可见物体清单为空。额外观测条件还把 11 个任务相关实体的名称、类型和 GT 三维坐标写进提示，包括用匿名编号标识的玩具车和橡皮鸭。常规 ReAct、替代提示和额外观测分别调用技能 6、7 和 6 次，这一局均得 0 分。静态地点取自场景标注，可见物体由环境按头部相机的可见性与遮挡计算。[观测生成](../benchmark/observation.py) · [VLM 实际收到的提示](prompt.py)

Graph Manager 使用固定的子模块、当前 checkout 的 71 项技能和 v6 任务索引，保留其原生 Harness 工具调用。它每回合可以多次调用模型，原生停止条件还包括 5 次重规划和约 27 分钟的时间预算。InternVL 发布的视觉对话模板用于普通请求；有工具时，通过其 Qwen3 语言基座的 ChatML 工具格式提供函数签名和返回值。模型工具协议影响 Graph Manager 的横向比较。其余四种方法沿用仓库统一的文本调用格式。

Harness 的手动模型配置须声明 `contextWindow: 32768` 和 `maxTokens: 4096`，与本地 vLLM 实际容量相同。这样 Harness 可以按自己的策略及时压缩历史。最早一批 Graph Manager 尝试遗漏容量声明，沿用了 262,144 token 的默认值，其中一次请求达到 35,298 token。已归档该配置下的尝试，并对三个模型重跑；正式表只接受带本地容量记录的 Graph Manager 结果。

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

## Isaac Sim 6 独立实验

目标实例的驱动为 NVIDIA 595.91.07。Isaac Sim 5.1 在启用 RTX 相机时于 `librtx.scenedb.plugin.so` 崩溃。此实例使用单独的 Isaac Sim **6.0.0.1** 环境和输出目录。跨版本比较需要考虑接触动力学、渲染和执行器行为的变化。

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
