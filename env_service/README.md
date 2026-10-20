# 环境服务

给外部 planner 用的 HTTP 服务：起任务、执行 contract、检查完成，外加一个只读的 `/observe`。每个 `exp_id` 对应一个独立的 simulator。主服务（[server.py](server.py)）只用标准库，每个 exp 的 simulator 跑在一个独立的 [worker.py](worker.py) 进程里，进程跑在 Isaac Sim 的 Python 下。

## 启动

```bash
$ISAACLAB_PYTHON -m env_service.server --port 8800
```

服务本身可以用任意 Python 3 运行；worker 默认用 `$ISAACLAB_PYTHON` 启动，也可以用 `--worker-python` 指定。在容器里运行时，要让 planner 能访问服务端口（例如 `docker run --network host`）。

| 参数 | 默认 | 说明 |
|---|---|---|
| `--port` | 8800 | 服务端口 |
| `--max-sims` | 2 | 同时运行（含正在启动）的 simulator 数，超出时 `initial_task` 返回 503 `BUSY` |
| `--no-wrist-cameras` | 关 | 只给头部相机 |
| `--worker-python` | `$ISAACLAB_PYTHON` | 运行 worker 的 Python |
| `--log-dir` | `runs/env_service` | 每个 exp 的 `worker.log` |

上限是固定的：每个 exp 最多 40 次 contract 调用、总时长 60 分钟，20 分钟没有调用就释放。

- 调用次数按顶层 contract 计：一个 batch 传 5 个就计 5 次；调用前计数，执行失败也算；composite skill 内部的嵌套调用不计。超出后返回 `LIMIT_EXCEEDED`。
- 总时长从 `initial_task` 返回时开始，是墙钟时间，包含 planner 思考的时间。超出后返回 `LIMIT_EXCEEDED`。
- 空闲从上一次 `do_contract` 或 `initial_task` 返回时开始计时，`/observe` 不算活动。超出后释放 simulator。
- simulator 启动最多等 13 分钟，低于 planner 端 15 分钟的客户端超时。

## 接口

请求和返回都是 JSON，全部用 `POST`。

### 1. `POST /initial_task`

```json
{"task_id": "collect_fruits"}
```

**同步**：启动 simulator、加载场景，启动好后才返回：

```json
{"exp_id": "collect_fruits-1a2b3c4d",
 "task": {"task_id": "collect_fruits", "name": "collect_fruits", "description": "Collect both fruits into the basket on the bookcase."},
 "observation": {...}}
```

`task_id` 取自 [tasks.json](../skill_library/tasks.json)，必填；跑全量时由 planner 逐个调用。已有 2 个 simulator 在运行（含正在启动的）时直接返回 503 `BUSY`，服务端不排队，由 planner 稍后重试。启动失败或 13 分钟内没能启动好，返回 500 `SIM_ERROR`。如果返回结果没能送达 planner（连接已断开），这个 exp 立即释放。

### 2. `POST /do_contract`

```json
{"exp_id": "...", "calls": [{"contract": "navigate", "args": {"destination": "apple"}},
                            {"contract": "pick", "args": {"object": "apple"}}]}
```

按顺序执行，遇到第一个失败就停；`calls` 传单个对象等同于长度为 1 的列表。contract 名字就是动词，参数写法以 `skill_library/skills/*/SKILL.md` 为准。参数里不能引用前一个 contract 的输出：需要时先单独调用前一步，从返回值里取。返回：

```json
{"exp_id": "...", "results": [<每个已执行 contract 的结果>], "observation": {...}}
```

单个结果：

```json
{"contract": "pick", "args": {"object": "apple"}, "success": false,
 "error_code": "PRECONDITION_FAILED", "error": "reachable(target=apple) is false (...)",
 "preconditions": [{"atom": "reachable(target=apple)", "holds": false}],
 "postconditions": [], "outputs": {}}
```

composite skill 失败时（`SUBSKILL_FAILED`）多一个 `failed_step`，给出失败的那一步的动作、错误码和测得的前后置条件。选中的 policy 路径、policy 步骤、名词绑定、嵌套调用和 fallback 建议都不返回。失败后不自动重试或修复，composite skill 内部也一样。

### 3. `POST /check_task`

```json
{"exp_id": "..."}
```

返回 `{"exp_id": "...", "success": true, "goal": [{"atom": "inside(apple, fruit_basket)", "holds": true}, ...]}`。`success` 为 goal 的每个子句在当前仿真状态上都成立。返回后释放该 simulator，这个 `exp_id` 不能再用。

### 4. `POST /observe`

```json
{"exp_id": "..."}
```

不执行动作，也不会等正在执行的 `do_contract`。返回 `{"exp_id", "state", "calls_used", "observation"}`：

| `state` | 含义 | `observation` |
|---|---|---|
| `running` | 有 `do_contract` 正在执行 | `null` |
| `ready` | 空闲，可以接收调用 | 当前 observation |
| `released` | 已释放 | `null` |

用于客户端超时或网络中断后判断 exp 是否还在、是否还在执行。`/observe` 不重置空闲计时。

## Observation

| 字段 | 内容 |
|---|---|
| `images` | `[{"camera": "head" \| "left_wrist" \| "right_wrist", "png_base64": ...}]`，480×640 PNG |
| `objects` | 当前任务的相关物体（tasks.json 的 `entities`）：`name`、`kind`、`position` |
| `robot` | `base_pose` [x, y, yaw_deg]、`held_right`、`held_left` |
| `task_status` | goal 每个子句当前的真假 `[{"atom", "holds"}]` |

## 错误

contract 本身的失败放在结果的 `error_code` 里，HTTP 仍是 200：

| `error_code` | 含义 | 机器人动了吗 | 返回的前后置条件 |
|---|---|---|---|
| `UNKNOWN_CONTRACT` | 没有这个动词 | 没有 | 无 |
| `BAD_CALL` | 调用不是 `{"contract", "args"}` 结构 | 没有 | 无 |
| `INPUT_MISSING` | 缺少必填参数 | 没有 | 无 |
| `INPUT_UNKNOWN` | 参数名不认识，或参数值不在枚举里（如 `grasp`、`hands`） | 没有 | 无 |
| `NOUN_INVALID` | 物件名不在场景中，或类型不符（比如把 support 当 object） | 没有 | 无 |
| `PRECONDITION_FAILED` | 执行前检查不满足 | 没有 | 前置条件 |
| `NO_PATH` | 前置条件都满足，但绑定的名词和机器人当前状态（如手里拿着什么）没有匹配的 policy 路径 | 没有 | 前置条件 |
| `POLICY_FAILED` | policy 执行中失败（没抓住、规划不出路径、掉落等） | 可能已动 | 前置条件 |
| `POSTCONDITION_FAILED` | 动作做完了，但后置条件不成立 | 动了 | 前置和后置条件 |
| `SUBSKILL_FAILED` | composite skill 的某一步失败，详见 `failed_step` | 可能已动 | composite 自己的前置条件，加 `failed_step` 里那一步的前后置条件 |
| `INTERNAL_ERROR` | 仿真或 skill 定义出错 | 可能已动 | 无 |
| `LIMIT_EXCEEDED` | 超出调用次数或总时长 | 没有 | 无 |

请求级错误返回 `{"error_code", "error"}`：

| HTTP | `error_code` | 含义 |
|---|---|---|
| 400 | `BAD_REQUEST` / `UNKNOWN_TASK` | 请求格式错误（含空 `task_id`）/ 没有这个任务 |
| 404 | `UNKNOWN_EXP` | 没有这个 exp |
| 410 | `EXP_RELEASED` | exp 已释放（已检查、空闲超时或 simulator 崩溃） |
| 500 | `SIM_CRASHED` / `SIM_ERROR` | simulator 进程退出、出错或启动失败，exp 随之释放 |
| 503 | `BUSY` | 已有 2 个 simulator 在运行（含正在启动的），稍后重试 |

## 测试

```bash
$ISAACLAB_PYTHON -m pytest tests/test_env_service.py   # 不起 simulator
```

[mock_planner.py](mock_planner.py) 是一个替身 planner：它调用 `initial_task`（遇到 `BUSY` 每 30 秒重试），把 `skill_library/plans/<task>.skill_subgraph.json` 按顺序转成 contract 调用发给服务，最后调用 `check_task`。在同一台机器上起服务和 mock planner：

```bash
$ISAACLAB_PYTHON -m env_service.server &
$ISAACLAB_PYTHON -m env_service.mock_planner --task hide_block throw_away_can count_tomatoes
```

同步版本在 Isaac Sim 里端到端测过：`throw_away_can`、`count_tomatoes`、`lay_down_bottle` 同时提交，前两个先启动，第三个等到 `count_tomatoes` 释放后才启动（当时是服务端排队，现在改成 planner 遇到 `BUSY` 重试），三个都判定成功；两个 simulator 的显存峰值约 8.9 GB。`/observe` 在 contract 执行期间立即返回 `running`，执行完返回 `ready` 和三路图片；`grasp: "spoon"` 返回 `INPUT_UNKNOWN`。回调版本还测过 `hide_block`（composite skill）。
