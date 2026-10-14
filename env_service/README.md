# 环境服务

给外部 planner 用的 HTTP 服务，三个接口：起任务、执行 contract、检查完成。每个 `exp_id` 对应一个独立的 simulator。主服务（[server.py](server.py)）只用标准库，每个 exp 的 simulator 跑在一个独立的 [worker.py](worker.py) 进程里，进程跑在 Isaac Sim 的 Python 下。

## 启动

```bash
$ISAACLAB_PYTHON -m env_service.server --port 8800 --callback-url http://<planner 主机>:<端口>/<路径>
```

服务本身可以用任意 Python 3 运行；worker 默认用 `$ISAACLAB_PYTHON` 启动，也可以用 `--worker-python` 指定。在容器里运行时，要让 planner 能访问服务端口，服务也要能访问回调地址（例如 `docker run --network host`）。

| 参数 | 默认 | 说明 |
|---|---|---|
| `--callback-url` | `$ZENO_CALLBACK_URL` | planner 的回调地址，必填 |
| `--port` | 8800 | 服务端口 |
| `--max-sims` | 2 | 同时运行的 simulator 数，超出的 exp 排队 |
| `--no-wrist-cameras` | 关 | 只给头部相机 |
| `--worker-python` | `$ISAACLAB_PYTHON` | 运行 worker 的 Python |
| `--log-dir` | `runs/env_service` | 每个 exp 的 `worker.log` |

上限是固定的：每个 exp 最多 40 次 contract 调用、总时长 30 分钟，10 分钟没有调用就释放。

## 接口

请求和返回都是 JSON，全部用 `POST`。

### 1. `POST /initial_task`

```json
{"task_id": "collect_fruits"}
```

立即返回 `{"exp_id": "collect_fruits-1a2b3c4d"}`。`task_id` 取自 [tasks.json](../skill_library/tasks.json)；为空或不传时为 35 个任务各起一个 exp，返回 `{"exp_ids": [...]}`。

exp 轮到 simulator 后启动场景，然后向回调地址 POST：

```json
{"exp_id": "...", "status": "ready",
 "task": {"task_id": "collect_fruits", "name": "collect_fruits", "description": "Collect both fruits into the basket on the bookcase."},
 "observation": {...}}
```

启动失败时 `status` 为 `"failed"`，带 `error`，没有 `observation`。推送失败时每 5 秒重试一次，3 次都失败就释放这个 exp。

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

## Observation

| 字段 | 内容 |
|---|---|
| `images` | `[{"camera": "head" \| "left_wrist" \| "right_wrist", "png_base64": ...}]`，480×640 PNG |
| `objects` | 当前任务的相关物体（tasks.json 的 `entities`）：`name`、`kind`、`position` |
| `robot` | `base_pose` [x, y, yaw_deg]、`held_right`、`held_left` |
| `task_status` | goal 每个子句当前的真假 `[{"atom", "holds"}]` |

## 错误

contract 本身的失败放在结果的 `error_code` 里，HTTP 仍是 200。其中 `UNKNOWN_CONTRACT`、`BAD_CALL`、`INPUT_MISSING`、`INPUT_UNKNOWN` 和 `NOUN_INVALID` 是调用写错了，`LIMIT_EXCEEDED` 是超出上限，`INTERNAL_ERROR` 是仿真里抛了异常。

请求级错误返回 `{"error_code", "error"}`：

| HTTP | `error_code` | 含义 |
|---|---|---|
| 400 | `BAD_REQUEST` / `UNKNOWN_TASK` | 请求格式错误 / 没有这个任务 |
| 404 | `UNKNOWN_EXP` | 没有这个 exp |
| 409 | `EXP_NOT_READY` | exp 还在排队或启动，等回调 |
| 410 | `EXP_RELEASED` | exp 已释放（已检查、空闲超时、回调失败或 simulator 崩溃） |
| 500 | `SIM_CRASHED` / `SIM_ERROR` | simulator 进程退出或出错，exp 随之释放 |

## 测试

```bash
$ISAACLAB_PYTHON -m pytest tests/test_env_service.py   # 不起 simulator
```

[mock_planner.py](mock_planner.py) 是一个替身 planner：它接收回调，把 `skill_library/plans/<task>.skill_subgraph.json` 按顺序转成 contract 调用发给服务，最后调用 `check_task`。在同一台机器上起服务和 mock planner：

```bash
$ISAACLAB_PYTHON -m env_service.server --callback-url http://127.0.0.1:8801/callback &
$ISAACLAB_PYTHON -m env_service.mock_planner --task hide_block throw_away_can count_tomatoes
```

`hide_block`、`throw_away_can`、`count_tomatoes`、`lay_down_bottle` 已通过端到端测试；3 个任务同时提交时，第三个会排队，等到前面的 exp 释放后再启动，两个 simulator 的显存峰值约 8.3 GB。
