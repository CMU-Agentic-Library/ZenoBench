# v6 本地 VLM 对比协议

同一组任务用于比较三个本地模型。Qwen3.5-4B 与 Qwen3.5-27B 给出同一家族的规模对照，InternVL3.5-8B 加入另一种视觉语言架构。精确的权重 revision 在 `baseline/comparison.py` 中。vLLM 0.32.0 使用 BF16，温度为 0，单次最多生成 4,096 token，上下文长度 32,768。Qwen 关闭显式思考。所有模型端点绑定在实验机的回环地址上。

| 部分 | 方法和条件 | 每模型局数 |
| --- | --- | ---: |
| 主实验 | OpenLoop、ReAct、CodeAsPolicies、SayPlan、GraphManager，共用 sticky/benchmark | 5 × 1,510 |
| 替代提示 | ReActHint，使用相同技能菜单、观测和调用预算 | 316 |
| 额外观测 | ReAct 使用 sticky/privileged，额外获得匿名任务物体及位置，仍须到场观察后才能操作 | 316 |

三个模型的主实验共 22,650 局。两项消融另有 1,896 局。主实验直接读取公开批次中的任务、具体布局和种子，包含 Control 330 局、Task 1,100 局、Action + Task 80 局。1,060 局的理想选择可用，450 局不可用。两项消融各选择每种具体布局出现的第一个评测种子，并与主实验中同一局的 ReAct 比较。上述划分在运行前确定。

Graph Manager 使用固定的子模块、当前 checkout 的 71 项技能和 v6 任务索引，保留其原生 Harness 工具调用。它每回合可以多次调用模型，原生停止条件还包括 5 次重规划和约 27 分钟的时间预算。InternVL 发布的视觉对话模板用于普通请求；有工具时，通过其 Qwen3 语言基座的 ChatML 工具格式提供函数签名和返回值。模型工具协议影响 Graph Manager 的横向比较。其余四种方法沿用仓库统一的文本调用格式。

## 运行

先将 Git LFS 场景资产和 `baseline/graph_manager` 子模块取到本地。仓库原协议使用 Isaac Sim 5.1、Isaac Lab 2.3.2 和 cuRobo 0.7.8。vLLM 和规划器各使用独立 Python 环境。下面是一个模型和一个方法的完整分片。其他方法和模型替换对应参数。

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

每个结果通过 exp_id 对应到仿真服务记录的最终状态和技能轨迹。分表使用各模型共同完成的相同局。任务成功、正分、满分和执行错误分别统计，保留中途服务失败的日志，重新运行同一分片会继续未完成的局。执行错误列记录技能叶节点报错的发生率。判断一个正确的替代动作是否被物理执行阻断，仍需结合具体动作和当时状态。

## Isaac Sim 6 独立实验

目标实例的驱动为 NVIDIA 595.91.07。Isaac Sim 5.1 在启用 RTX 相机时于 `librtx.scenedb.plugin.so` 崩溃。此实例使用单独的 Isaac Sim **6.0.0.1** 环境和输出目录。跨版本比较需要考虑接触动力学、渲染和执行器行为的变化。

仿真环境使用 Python 3.12、PyTorch 2.11.0+cu130、Isaac Sim 6.0.0.1、Isaac Lab 2.3.2 的源码和按 sm_120 编译的 cuRobo 0.7.8。使用 `isaacsim[all,extscache]` 安装完整扩展。将 2.3.2 wheel 中含有 `apps/` 和 `source/` 的 `isaaclab/` 目录解包到 `LAB_SOURCE`。以下命令生成适配后的独立副本，并使每局原生记录包含版本和适配清单的 SHA-256。

```bash
"$ISAACLAB_PYTHON" baseline/sim6/prepare_lab.py "$LAB_SOURCE" "$LAB_SIM6"
export PYTHONPATH="$LAB_SIM6/source/isaaclab${PYTHONPATH:+:$PYTHONPATH}"
export ZENO_LAB_COMPAT_MANIFEST="$LAB_SIM6/compatibility.json"
```

用上面的环境启动 HTTP 服务，在评测和汇总两条命令中都传入 `--sim-version 6.0.0.1`。生成的表头显示实际版本，汇总器检查每个原生结果的版本号。用于相机和参考技能验证的局存放于规划器结果目录之外。

以下例子给 8860、8861、8862 三个仿真服务各分配两个并发局，在不同模型和方法间轮转。各服务的 `--log-dir` 都指向 `$ZB_RUN/native`。端口 8101、8102、8103 分别对应 Qwen 4B、Qwen 27B 和 InternVL 8B。收到 SIGTERM 后，调度器等待正在运行的局结束。再次启动时继续剩余的局。

```bash
python -m baseline.launch_comparison --run-dir "$ZB_RUN" --sim-version 6.0.0.1 \
  --servers 8860=2 8861=2 8862=2 --graph-bin /path/to/graph-env/bin/graph-manager-run
```
