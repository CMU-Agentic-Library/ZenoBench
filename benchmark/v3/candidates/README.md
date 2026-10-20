# v3 candidate conditions (under debugging, not part of the benchmark)

Generated from `benchmark/v3_candidates.py` with `python benchmark/define_tasks_v3.py --candidates benchmark/v3/candidates/tasks.json`.
Matrix: `python benchmark/matrix.py --tasks benchmark/v3/candidates/tasks.json --out benchmark/v3/candidates`.

* `tasks.json` holds 17 tasks and 80 variants: the v2 variants with seed variation and the new candidate
  conditions for T01–T10, the household tasks T11 collect the apple, T12 tidy the toys, T13 set the breakfast table,
  and copies of the registry tasks T15–T18 (book face up, rolling pin at the edge, hide-and-seek block, check the
  cabinet dishes). T14 (homework desk) was dropped; see `DROPPED_TASKS` in `benchmark/v3_candidates.py`.
* `batches/smoke_a|b|c.json` hold the first-seed (10) runs of every declared T01–T10 route, split into three Isaac
  batches: T01–T03; T04, T07, T08, T10; T05, T06, T09.
* `batches/normal_new.json`, `normal_fix1.json`, `round2.json` … `round7.json` are the debugging rounds of the new
  tasks; their runs (local, git-ignored) are under `benchmark/runs/v3_normal` and `v3_round2` … `v3_round7`;
  `benchmark/v3/RESULTS.md` and `conditions.json`
  count the ones whose config hash matches the registry.

Run with `--tasks benchmark/v3/candidates/tasks.json`. The T01–T10 candidate conditions have no physical evidence yet. A task
moves into `benchmark/v3/tasks.json` once it is verified, as described in [../README.md](../README.md).
