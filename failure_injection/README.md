# Failure injection (ZenoBench v5)

Reproducible failures declared per variant (`"failures": [...]` in the task catalog), applied by a proxy
in front of the episode's Contract runner (`runtime.FailureRunner`, installed by `benchmark/run_episode.py`
and `env_service/worker.py`). Skills, Contracts and GT policies are unchanged.

| Level | Kind | What happens in the simulator | What the planner sees |
|---|---|---|---|
| action | `grasp` | the pick runs; the hand then opens and the object falls back under physics | `pick` fails: `not held (lift … m)`, `holding(...)` false |
| action | `slip` | at the next `navigate` while holding it, the hand opens over the pick spot; the base does not move | `navigate` fails: `… slipped out of the hand while carrying it` |
| action | `placement` | the place runs; the object is then turned on its side (`tipped`) or lands at an authored pose (`displaced`, e.g. beside the bin), and settles | the place fails with the authored `report` atoms that do not hold (only if they really do not) |
| action | `ik` | the call is refused before any motion; refused again from the same park until a base skill re-parks | `no IK solution reaches X from this base pose` |
| task | `capacity` / `destination` / `resource` / `dependency`, `when: initial` | the constraint is in the scene overlay (move / add / remove) | only what it observes |
| task | same kinds, `when: dynamic` | after the trigger call: `move_object` (put something there / take the resource away), `into` (something put into a container), `set_joint` (door closed again) | only what it observes next |
| mixed | action + task failures in one variant; `after_fired` couples one to another | | |

* **Deterministic**: triggers count top-level calls (`{"skill", "args": {subset}, "nth", "while_holding"}`);
  the same call sequence gives the same failures. Seeded values (`jitter`) come from
  `Random(f"{task}:{variant}:{seed}:{id}")`. The failure list is part of the configuration hash (only for
  variants that declare one, so every earlier hash is unchanged).
* **Hidden**: the planner never receives the specs, counters or `failure_log`; error texts match the
  natural failures'. `result.json: failure_injection` (declared / fired / manifested / not_fired / log) is for
  the evaluation only.
* **Honest**: a failure that does not change the outcome (the pick already failed, the displaced object
  still satisfies the report atoms) is logged as `manifested: false`; the call result is left as it was.

Tests: `python -m pytest -q failure_injection/tests` (fake rig); physics: `benchmark/v5/validate.py --physics`.
