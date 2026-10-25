# Episode pipeline

One pipeline for both task sets. The env_service worker (an HTTP planner) and `benchmark/run_episode.py` (scripted routes, the fixed / retry / recovery planners, the GT oracle) run the same `Episode` class. The only difference is who chooses the calls.

```
catalog.load_catalog(path)            any catalog -> {task_id: task}, all in the benchmark shape
benchmark.scene.episode_config(...)   task + variant + seed -> scene overlay + config_hash
profile.load_profile(name or yaml)    execution / observation / evaluation / limits switches
episode.Episode(task, cfg, profile)   scene, runner, observation(), call(), check(), metadata()
```

## Task catalogs ([catalog.py](catalog.py))

Both catalogs store tasks in one shape on disk; `load_catalog` only indexes them by `task_id`.

| catalog | tasks |
|---|---|
| `skill_library/tasks.json` (35 tasks) | one variant `default` on the built scene `tasks/<scene>/` (shared by several tasks), no overlay; `entities` (planner relevance and the GT `objects` observation), `watch` (the objects among them); route `nominal` = the planner subgraph in `skill_library/plans/`, kept in sync by `python -m skill_library.planner`; planner-only inputs under `planner` |
| `benchmark/tasks.json`, `benchmark/v3/tasks.json` | condition variants with overlays, declared routes with expected failures; v3 has `entities` too (the watched objects, then every scene entity its goal and routes name; written by `benchmark/define_tasks_v3.py`), shown only by a profile with `gt_objects` on, never by `benchmark` |

A task with one variant ignores the seed: no distractors to drop and no `vary`, so every seed gives the same `config_hash`.

## Profiles ([profile.py](profile.py), [profiles/](profiles/))

A profile YAML is merged over `DEFAULTS` in profile.py. Unknown keys, wrong types and unsafe combinations are refused when the profile is loaded.

| key | meaning | `gt` | `oracle` | `benchmark` |
|---|---|---|---|---|
| `execution.gate` | object arguments must be observed; the manipulated object must be in view or in hand; navigation drives to the cached pose | off | off | on |
| `execution.nested_repair` | repair fallback and one retry for a failed nested call of a composite skill | off | on | off |
| `execution.auto_recovery` | policy-internal recovery (expose, door retry from another park, pick -> push) | on | on | off |
| `execution.slide_to_edge` | the automatic slide-to-edge step inside pick | on | on | off |
| `execution.advisory` | feasibility predicates that are only recorded | – | – | grasp_clearance, edge_overhang |
| `execution.mask_feedback` | never-observed names -> `<unobserved>` in results | off | off | on |
| `execution.occlusion` / `static_explore` | dynamic occlusion in visibility; explore_room covers static furniture only | off | off | on |
| `execution.edge_pinch_upright_waist` | low-level edge-pinch setting | off | on | on |
| `observation.cameras` | which cameras go into `images` | 3 | head | head |
| `observation.gt_objects` | `objects`: task entities with GT positions | on | on | off |
| `observation.visible_objects` / `observation_cache` / `known_places` | the benchmark's limited observation | off | off | on |
| `observation.robot` | `base_pose`, `held`, `room`, `temperatures` (`none` / `observed` / `all`) | pose, held | pose, held | all, observed temperatures |
| `observation.task_status` | every goal clause, true or false now | on | on | off |
| `observation.last_result` | the previous contract result | off | off | on |
| `evaluation.drops_fail` | a watched object that ended on the floor fails the task | off | on | on |
| `limits.max_calls` | an int, or `task` (the task's `max_calls`, default 60) | 40 | task | task |
| `allow_leak` | accept a gated profile that still shows GT state (debugging only) | – | – | – |

- `gt` reproduces the original env_service interface. `oracle` reproduces the GT runner of `run_episode --planner oracle`. `benchmark` reproduces `LimitedSession`.
- When `gate` is on, `gt_objects`, `task_status`, `temperatures: all` and `mask_feedback: false` each leak GT state. Any of them is refused unless `allow_leak: true`.
- An observer (the observation cache, `benchmark.observation.Observer`) is created when anything reads it: `gate`, `mask_feedback`, `visible_objects`, `observation_cache` or `temperatures: observed`. With `gate` off it still records what the robot saw and turns the head toward the workspace after each call, but refuses nothing.

## Hashes

| hash | covers |
|---|---|
| `config_hash` | the scene overlay (`base`, `remove`, `move`, `start`, thermal); unchanged from benchmark v3, so existing v3 evidence still matches |
| `base_sha1` | the base scene files `scene.usd`, `annotation.json`, `task.json` |
| `profile_hash` | the profile without its name |
| `episode_hash` | all three: two runs with the same `episode_hash` repeat one episode |

`config.json` of every run (run_episode and env_service) records all four hashes. `benchmark/evaluate.py` and `benchmark/conditions.py` do not count a run whose recorded `profile_hash` no longer matches the profile file it names. Runs from before profiles existed have no `profile_hash` and still count.

## Changes against the two old pipelines

- Start: both now step 30, drive to the variant's start pose, step 120, then take the start snapshot. The env_service used to take the snapshot after 30 steps and step 90 more. Results of original tasks from before this change are therefore not directly comparable.
- env_service with `gt`: the start, runner, recovery and observation fields are the same as before, except for the snapshot timing above. The planner-facing result format is unchanged.
- Benchmark planners: the planner-facing result is now the env_service format (`contract`, `args`, `success`, `error_code`, `error`, `preconditions`, `postconditions`, `outputs`, `failed_step`), masked. `calls[].feedback` in `result.json` additionally carries `action` and `path` for the evaluation scripts. A recovery planner's observation now has the env_service field names (`images`, `robot.held_right`, `last_result`, ...).
- A goal predicate that raises now counts as false with the error as its detail. It no longer crashes the episode.
- `LimitedSession` (benchmark/session.py) and `GatedRunner.feedback()` were removed; the planner-facing result is `Episode.call()`.
