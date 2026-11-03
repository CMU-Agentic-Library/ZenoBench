# v6 track evaluation

`python benchmark/v6/track_metrics.py` over: benchmark/runs/v5_grid, benchmark/runs/v6_track_smoke.
Metric definitions: the module docstring of `benchmark/v6/track_metrics.py` and `TRACKS.md`.

## Action-Level

### planner `scripted`

| group | n | ASR | LRR | RC | NSR | CDR | FIV | LRR_ik | LRR_grasp | LRR_slip | LRR_placement |
|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 648 | 55% (357/648) | 82% (540/659) | 1.17 (n=540) | 96% (5929/6199) | 14% (93/648) | 89% (579/648) | 80% (329/413) | 85% (180/211) | 92% (23/25) | 80% (8/10) |
| AL-COMPOUND | 81 | 37% (30/81) | 85% (89/105) | 1.61 (n=89) | 96% (938/979) | 26% (21/81) | 70% (57/81) | 70% (33/47) | 100% (32/32) | 100% (16/16) | 80% (8/10) |
| AL-GRASP | 198 | 61% (121/198) | 83% (148/179) | 0.43 (n=148) | 96% (1624/1697) | 10% (20/198) | 98% (195/198) | N/A | 83% (148/179) | N/A | N/A |
| AL-IK | 360 | 55% (199/360) | 81% (296/366) | 1.36 (n=296) | 96% (3303/3457) | 14% (52/360) | 88% (318/360) | 81% (296/366) | N/A | N/A | N/A |
| AL-SLIP | 9 | 78% (7/9) | 78% (7/9) | 3.00 (n=7) | 97% (64/66) | 0% (0/9) | 100% (9/9) | N/A | N/A | 78% (7/9) | N/A |

## Task-Level

### planner `scripted`

| group | n | TSR | RRSR | PAR | FRR | PE |
|---|---|---|---|---|---|---|
| all | 4 | 100% (4/4) | 100% (3/3) | N/A | 0% (0/2) | 0.89 (n=4) |
| dynamic | 1 | 100% (1/1) | 100% (1/1) | N/A | N/A | 1.00 (n=1) |
| initial | 3 | 100% (3/3) | 100% (2/2) | N/A | 0% (0/2) | 0.85 (n=3) |

GAP (control TSR - family TSR, mean over families with a control run): N/A.
Stop reasons of failed episodes: -.

