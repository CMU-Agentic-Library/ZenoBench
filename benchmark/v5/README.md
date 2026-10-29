# ZenoBench v5: extensible skills, failure injection, 180 formal variants

v5 builds on v3/v4 (`benchmark/v3/`, unchanged and still the catalog Graph Manager and the HTTP service
read). It adds a separate catalog, `benchmark/v5/tasks.json`, with the same 20 task ids.

| Part | Where | What |
|---|---|---|
| Skill System | [`skill_ext/`](../../skill_ext/README.md) | user skills from `SKILL.md` (schema-validated, dynamically loaded, VLA / RL / scripted executors), Skill Registry, Fixed-Skill vs Open-Skill tracks |
| Failure Injection | [`failure_injection/`](../../failure_injection/README.md) | action-level (grasp, slip, placement, IK), task-level (capacity, destination, resource, dependency; initial or dynamic), mixed / coupled; deterministic, hidden from the planner |
| Task suite | `define_tasks_v5.py` → `tasks.json` | 20 tasks × (2 Easy + 3 Medium + 4 Hard) = **180 formal variants**; existing variants reused with identical configurations |
| Validation | `validate.py` | static checks of all 1,800 episodes (180 × seeds 10-19) and the physical-episode report, kept apart |

## Tiers and categories

* **Easy (2)**: nominal execution. E1 is the v3 Easy (T05: the named pencil; T14: the book already
  overhanging); E2 an independent nominal layout (another start room, a longer trip).
* **Medium (3)**: skill-level adaptation. v3 Medium conditions first (search, alternative, fallback), then
  action-level injected failures with a local recovery (retry after a slip, re-park after an IK refusal).
* **Hard (4)**, one per category (`variants[*].v5.hard_category`):
  * `task`: task-level replanning forced by the environment: the v4 Hard where one exists (13 tasks), a new
    initial constraint for the other 7 (T04 drinks spot taken, T05 pencil behind a closed door, T10 can in
    the closed microwave, T15 a block on the book, T16 a bowl in the pin's path, T17 the lid elsewhere, T18
    the bowl in the other cabinet);
  * `action`: two action-level failures whose recoveries chain;
  * `mixed`: a task-level constraint (declared and checked at the start) plus an action-level failure;
  * `dynamic`: a task-level event while the robot works (an object moved, a door opened / closed, a
    destination filled).

Every variant states its challenge (`v5.challenge`), resolves to a goal (the task's or its own), and maps to
one oracle route (`oracle[variant]`, new ones named `v5_<variant>`). Failing steps carry `expect: fail`;
injected ones also `injected: true` (the GT oracle planner meets them as well, it does not skip them).
Existing variants outside the formal set are kept as `v5_supplementary`.

## Commands

```bash
python benchmark/v5/define_tasks_v5.py                 # regenerate tasks.json (--check: up to date?)
python benchmark/v5/validate.py static                 # 1,800 episodes, writes STATIC.json
python benchmark/v5/validate.py batch --seeds 10-19 --out benchmark/v5/batches/physics_all.json
$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v5/tasks.json \
    --batch benchmark/v5/batches/physics_all.json --jobs 2 --out benchmark/runs/v5_physics --no-eval
python benchmark/v5/validate.py report --runs benchmark/runs/v5_physics   # writes PHYSICS.json
python -m pytest -q benchmark/v5/tests failure_injection/tests skill_ext/tests
```

Static evidence (configuration) and physical evidence (simulated episodes) are reported separately; an
unrun episode is `unrun`, never passed. See [VALIDATION.md](VALIDATION.md) for the latest results.
