# 环境服务

给外部 planner 用的 HTTP 服务：起任务、执行 contract、检查完成，外加一个只读的 `/observe`。每个 `exp_id` 对应一个独立的 simulator。主服务（[server.py](server.py)）只用标准库和 PyYAML，每个 exp 的 simulator 跑在一个独立的 [worker.py](worker.py) 进程里，进程跑在 Isaac Sim 的 Python 下。

episode 本身由 [episode/episode.py](../episode/episode.py) 的 `Episode` 运行，`benchmark/run_episode.py` 用的也是同一个类。服务同时提供两套任务：

| catalog | 任务 | 默认 profile |
|---|---|---|
| [skill_library/tasks.json](../skill_library/tasks.json) | 原来的 35 个任务，每个只有一个 variant `default` | `gt` |
| [benchmark/v3/tasks.json](../benchmark/v3/tasks.json) | benchmark v3 的 41 个任务，每个任务有若干 condition variant | `benchmark` |

profile（[episode/profiles/](../episode/profiles/)）决定执行开关（gate、自动恢复、反馈遮罩……）、observation 字段和调用上限，详见 [episode/README.md](../episode/README.md)。profile 由 `initial_task` 的 `profile` 字段选，任何任务都能用任一个跑；不传时用上表里任务所在 catalog 的默认 profile。可选的 profile 按 sticky hands 的程度分三个文件夹，每个里面一个 `gt` 一个 `benchmark`：

| 文件夹 | `execution.sticky_hands` | 搬运时焊在夹爪上 | pick / place 失败自动补成功（tp） | 请求里的名字 |
|---|---|---|---|---|
| `physical/` | `false` | 关 | 关 | `gt`、`benchmark` |
| `sticky/` | `carry` | 开 | 关 | `sticky/gt`、`sticky/benchmark` |
| `sticky_snap/` | `snap` | 开 | 开 | `sticky_snap/gt`、`sticky_snap/benchmark` |

sticky hands 是开发 planner 时用的执行辅助，不用于打分。抓取先照常按物理方式做。`carry` 和 `snap`：手里的物体用 PhysX 固定关节焊在夹爪上，手指张开前才解除，所以搬运途中不会掉。`carry` 下 pick 和 place 都是物理的，失败就返回失败。`snap` 另外在前置条件（含 gate）满足后：物理抓取失败（找不到 park、IK 失败、没抓住）时，机器人先尽量把手伸过去，再把物体直接放进手里；place 失败或物体没落在目标上时，把物体摆正放到目标上。如果抓取时把物体所在的容器或托盘一起捏起来了，会先松手，再只把物体放进手里。前置条件、gate 和输入的失败照样返回失败。worker.log 里会有 `sticky_weld`、`sticky_snap`（附原因 `no_park` / `not_held` / `ik` / `caught_neighbour` / `other`）、`sticky_caught`、`sticky_place`、`sticky_release` 事件，planner 收到的结果里没有这些。每个 profile 有自己的 `profile_hash`，三档的结果不能直接比较，详见 [episode/README.md](../episode/README.md)。

## 启动

```bash
$ISAACLAB_PYTHON -m env_service.server --port 8800
```

服务本身可以用任意 Python 3 运行；worker 默认用 `$ISAACLAB_PYTHON` 启动，也可以用 `--worker-python` 指定。在容器里运行时，要让 planner 能访问服务端口（例如 `docker run --network host`）。

| 参数 | 默认 | 说明 |
|---|---|---|
| `--port` | 8800 | 服务端口 |
| `--max-sims` | 2 | 同时运行（含正在启动）的 simulator 数，超出时 `initial_task` 返回 503 `BUSY` |
| `--catalog PATH=PROFILE` | 上表两项 | 任务 catalog 和它的任务默认用的 profile（名字或 YAML 路径），可重复；任务 id 在所有 catalog 里必须唯一 |
| `--profiles NAME,...` | `gt,benchmark,sticky/gt,sticky/benchmark,sticky_snap/gt,sticky_snap/benchmark` | 请求里 `profile` 可以选的 profile（名字或 YAML 路径） |
| `--record-video` | 关 | 每个 exp 保存 `<log-dir>/<task_id>/<exp_id>/run.mp4`，第三人称主视角加小窗，640×360、15 fps |
| `--worker-python` | `$ISAACLAB_PYTHON` | 运行 worker 的 Python |
| `--log-dir` | `runs/env_service` | 每个 exp 的目录 `<log-dir>/<task_id>/<exp_id>/` |

调用上限由所用 profile 的 `limits.max_calls` 决定：`gt` 是 40 次，`benchmark` 用任务自己的 `max_calls`（没写就是 60）。总时长 60 分钟、20 分钟没有调用就释放，这两项对所有任务都一样。

录制边执行边写入文件，不在内存中积累整个任务的视频；释放时关闭编码器。视频使用仿真时间，模型思考期间仿真暂停，不会录下长时间静止等待。它属于服务端调试记录，不会作为 planner 的额外观测。

- 调用次数按顶层 contract 计：一个 batch 传 5 个就计 5 次；调用前计数，执行失败也算；composite skill 内部的嵌套调用不计。超出后返回 `LIMIT_EXCEEDED`。
- 总时长从 `initial_task` 返回时开始，是墙钟时间，包含 planner 思考的时间。超出后返回 `LIMIT_EXCEEDED`。
- 空闲从上一次 `do_contract` 或 `initial_task` 返回时开始计时，`/observe` 不算活动。超出后释放 simulator。
- simulator 启动最多等 13 分钟，低于 planner 端 15 分钟的客户端超时。simulator 逐个启动（一个 Isaac 进程启动时内存峰值约 11 GB），所以两个 `initial_task` 同时到达时，第二个会多等一次启动的时间（约 1–2 分钟），这段等待也算在 13 分钟里。

## 接口

请求和返回都是 JSON，全部用 `POST`。

### 1. `POST /initial_task`

```json
{"task_id": "T01_book_to_dining_table", "profile": "benchmark", "variant": "no_overhang", "seed": 10}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `task_id` | 是 | 任一 catalog 里的任务 |
| `profile` | 否 | `gt` 或 `benchmark`（`--profiles` 里的名字），决定执行开关、observation 字段和调用上限；不传时用任务所在 catalog 的默认 profile |
| `variant` | 否 | 指定 condition；不给时由 `seed` 在分了难度（easy / medium / hard）的 variant 里选，`difficulty` 给了就只在该难度里选；`diagnostic` variant 只有显式指定才会用。只有一个 variant 的任务（原来的任务）忽略它 |
| `seed` | 否，默认 0 | 决定随机删掉哪些干扰物和 `vary` 范围内的微调；只有一个 variant 的任务不受影响 |
| `difficulty` | 否 | `easy` / `medium` / `hard`；任务没有这个难度的 variant 时返回 400 `UNKNOWN_VARIANT`（不少任务只有其中一两档） |

**同步**：启动 simulator、加载场景，启动好后才返回：

```json
{"exp_id": "T01_book_to_dining_table-1a2b3c4d",
 "task": {"task_id": "T01_book_to_dining_table", "name": "T01_book_to_dining_table", "description": "Someone left their paperback ..."},
 "profile": {"name": "benchmark", "observation": ["images", "visible_objects", "observation_cache", "known_places", "robot", "last_result"], "max_calls": 60},
 "observation": {...}}
```

`description` 是任务指令；variant 名字和 goal 不会告诉 planner。`profile.observation` 列出这个 exp 的 observation 里会有哪些字段。跑全量时由 planner 逐个调用。已有 2 个 simulator 在运行（含正在启动的）时直接返回 503 `BUSY`，服务端不排队，由 planner 稍后重试。启动失败或 13 分钟内没能启动好，返回 500 `SIM_ERROR`。如果返回结果没能送达 planner（连接已断开），这个 exp 立即释放。

### 2. `POST /do_contract`

```json
{"exp_id": "...", "calls": [{"contract": "navigate", "args": {"destination": "apple"}},
                            {"contract": "pick", "args": {"object": "apple"}}]}
```

按顺序执行，遇到第一个失败就停；`calls` 传单个对象等同于长度为 1 的列表。contract 名字就是动词，参数写法以 `skill_library/skills/*/SKILL.md` 为准。参数里不能引用前一个 contract 的输出：需要时先单独调用前一步，从返回值里取。返回：

```json
{"exp_id": "...", "results": [<每个已执行 contract 的结果>], "observation": {...}}
```

技能执行完毕不会自动释放 simulator，即使任务目标已满足；客户端仍可继续观察或调用技能，最后必须调用 `check_task` 检查结果并释放名额。原有空闲超时清理机制保留。

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

返回：

```json
{"exp_id": "...", "success": true,
 "goal": [{"atom": "inside(apple, fruit_basket)", "holds": true}, ...],
 "dropped": [],
 "episode": {"task_id", "variant", "seed", "difficulty", "conditions", "config_hash", "base_sha1",
             "profile", "profile_hash", "episode_hash", ...}}
```

goal 是 `all` 的每个子句都成立，并且 `any` 的子句组（benchmark 任务才有，`goal` 里依次列出）至少有一组全部成立。profile 的 `evaluation.drops_fail` 打开时（`benchmark`），被观察物体掉到地上也算失败，掉落的物体在 `dropped` 里。`episode` 给 evaluator 用：`episode_hash` 相同的两次运行是同一个 episode 配置（场景覆盖、base 场景文件、profile 都相同）。返回后释放该 simulator，这个 `exp_id` 不能再用。

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

字段由 profile 打开或关闭，关掉的字段不出现在返回里。

| 字段 | 内容 | `gt` | `benchmark` |
|---|---|---|---|
| `images` | `[{"camera": "head" \| "left_wrist" \| "right_wrist", "png_base64": ...}]`，PNG，大小和焦距由 profile 决定 | 3 路，960×720（宽×高），7.5 mm 焦距，水平视野约 108° | 只有 head，640×480，10 mm，水平视野 92° |
| `objects` | 任务的相关物体（`entities`）：`name`、`kind`、GT `position` | 有 | 无 |
| `visible_objects` | 当前视野里的物体：`name`、`category`、`tags`、`in_view`、`held`、`last_seen_position`、`last_seen_on`、`last_seen_in`、`last_seen_tick` | 无 | 有 |
| `observation_cache` | 见过的每个物体最后一次的样子，字段同上 | 无 | 有 |
| `known_places` | 静态地点：房间、家具、支撑面、门、电器、按钮 | 无 | 有 |
| `robot` | `base_pose` [x, y, yaw_deg]、`held_right`、`held_left`；`benchmark` 另有 `room` 和见过的食物的 `temperatures_c` | 有 | 有 |
| `task_status` | goal 每个子句当前的真假 `[{"atom", "holds"}]` | 有 | 无 |
| `last_result` | 上一次 contract 的结果（同 `do_contract` 的单个结果） | 无 | 有 |

`benchmark` profile 下，结果和 observation 里没见过的物体名都换成 `<unobserved>`（planner 自己在参数里写的名字除外）。

## 错误

contract 本身的失败放在结果的 `error_code` 里，HTTP 仍是 200：

| `error_code` | 含义 | 机器人动了吗 | 返回的前后置条件 |
|---|---|---|---|
| `UNKNOWN_CONTRACT` | 没有这个动词 | 没有 | 无 |
| `BAD_CALL` | 调用不是 `{"contract", "args"}` 结构 | 没有 | 无 |
| `INPUT_MISSING` | 缺少必填参数 | 没有 | 无 |
| `INPUT_UNKNOWN` | 参数名不认识，参数值不在枚举里（如 `grasp`、`hands`），或互斥参数同时给出（`place` 的 `hint_xy` 和 `near`） | 没有 | 无 |
| `NOUN_INVALID` | 物件名不在场景中，或类型不符（比如把 support 当 object） | 没有 | 无 |
| `PRECONDITION_FAILED` | 执行前检查不满足 | 没有 | 前置条件 |
| `NO_PATH` | 前置条件都满足，但绑定的名词和机器人当前状态（如手里拿着什么）没有匹配的 policy 路径 | 没有 | 前置条件 |
| `POLICY_FAILED` | policy 执行中失败（没抓住、规划不出路径、掉落等） | 可能已动 | 前置条件 |
| `POSTCONDITION_FAILED` | 动作做完了，但后置条件不成立 | 动了 | 前置和后置条件 |
| `SUBSKILL_FAILED` | composite skill 的某一步失败，详见 `failed_step` | 可能已动 | composite 自己的前置条件，加 `failed_step` 里那一步的前后置条件 |
| `INTERNAL_ERROR` | 仿真或 skill 定义出错 | 可能已动 | 无 |
| `LIMIT_EXCEEDED` | 超出调用次数或总时长 | 没有 | 无 |
| `NOT_OBSERVED` | 只在 gate 打开时（`benchmark`）：参数里的物体没见过，或名字不存在（两种情况返回同样的文字） | 没有 | 无 |
| `NOT_IN_VIEW` | 只在 gate 打开时：被操作的物体不在当前视野里也不在手上 | 没有 | 无 |
| `NOT_FOUND` | 只在 gate 打开时：look 类动作看向物体最后一次出现的位置，那里看不到它 | 可能转了头 | 无 |

请求级错误返回 `{"error_code", "error"}`：

| HTTP | `error_code` | 含义 |
|---|---|---|
| 400 | `BAD_REQUEST` / `UNKNOWN_TASK` / `UNKNOWN_VARIANT` / `UNKNOWN_PROFILE` | 请求格式错误（含空 `task_id`、非整数 `seed`、未知 `difficulty`）/ 没有这个任务 / 任务没有这个 variant，或没有所给难度的 variant / `profile` 不在可选列表里 |
| 404 | `UNKNOWN_EXP` | 没有这个 exp |
| 410 | `EXP_RELEASED` | exp 已释放（已检查、空闲超时或 simulator 崩溃） |
| 500 | `SIM_CRASHED` / `SIM_ERROR` | simulator 进程退出、出错或启动失败，exp 随之释放 |
| 503 | `BUSY` | 已有 2 个 simulator 在运行（含正在启动的），稍后重试 |

## 输出

每个 exp 的目录 `<log-dir>/<task_id>/<exp_id>/` 和 `benchmark/run_episode.py` 的输出格式相同：`config.json`（场景覆盖、profile、各个 hash）、`annotation.json`、`calls.jsonl`、`result.json`（`planner` 为 `"http"`；没有调用 `check_task` 就被释放的 exp 记为 `incomplete`），外加 `worker.log`。所以可以直接用 `benchmark/evaluate.py --runs runs/env_service --tasks <catalog>` 统计指标。

## 测试

```bash
$ISAACLAB_PYTHON -m pytest tests/test_env_service.py   # 不起 simulator
```

[mock_planner.py](mock_planner.py) 是一个替身 planner：它调用 `initial_task`（遇到 `BUSY` 每 30 秒重试），把任务所在 catalog 里这个 variant 对应的 route（原任务就是 `routes.nominal`，即规划器生成的子图）按顺序转成 contract 调用发给服务，最后调用 `check_task`。有多个 variant 的任务要给 `--variant`，route 里预期失败的那一步会单独发送。在同一台机器上起服务和 mock planner：

```bash
$ISAACLAB_PYTHON -m env_service.server &
$ISAACLAB_PYTHON -m env_service.mock_planner --task hide_block throw_away_can count_tomatoes
$ISAACLAB_PYTHON -m env_service.mock_planner --task T01_book_to_dining_table --variant no_overhang --seed 10
```

同步版本在 Isaac Sim 里端到端测过：`throw_away_can`、`count_tomatoes`、`lay_down_bottle` 同时提交，前两个先启动，第三个等到 `count_tomatoes` 释放后才启动（当时是服务端排队，现在改成 planner 遇到 `BUSY` 重试），三个都判定成功；两个 simulator 的显存峰值约 8.9 GB。`/observe` 在 contract 执行期间立即返回 `running`，执行完返回 `ready` 和三路图片；`grasp: "spoon"` 返回 `INPUT_UNKNOWN`。回调版本还测过 `hide_block`（composite skill）。
