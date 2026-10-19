# v3 candidate conditions (under debugging, not part of the benchmark)

Generated from `benchmark/v3_candidates.py` with `python benchmark/define_tasks_v3.py --candidates benchmark/v3/candidates/tasks.json`.
Matrix: `python benchmark/matrix.py --tasks benchmark/v3/candidates/tasks.json --out benchmark/v3/candidates`.

* `tasks.json` holds the 15 tasks and 82 variants: the v2 variants with seed variation, plus the new candidate
  conditions and the new tasks T11–T15.
* `batches/smoke_a|b|c.json` hold the first-seed (10) runs of every declared route, split into three Isaac batches:
  T01–T03; T04, T07, T08, T10; T05, T06, T09, T11–T15 (household phrasing: T11 book face up, T12 try the rolling pin, T13 hide-and-seek block, T14 tidy the TV stand, T15 check the cabinet dishes).

Run with `--tasks benchmark/v3/candidates/tasks.json`. None of these conditions has physical evidence yet. A task
moves into `benchmark/v3/tasks.json` once it is verified, as described in [../README.md](../README.md).
