# Handoff 2026-11-14: "carry tilt held" failures, and the stages choosing the arm posture with different criteria

Branch `remove-handcoded-motion`, HEAD e278e82 at the time of writing. Another session committed "Tray place" on top
of d116156. Nothing below is committed or pushed.

## 1. The full v6 run 11-13 (the baseline these failures come from)

- Run: `/data/zenobench/v6full_1113`, commit c5b71ab. Result 91/153.
- 12 newly failing episodes compared with 11-12. Nine of them are a place or a drop with a held load failing with
  "carry tilt held".
- Classification of all 62 failures:
  - only one looks physically impossible: T18, a bowl on a cabinet top at 1.13 m, where no base pose has IK;
  - 10 "carry tilt held";
  - 10 perception (look / search / explore);
  - 8 slide to edge or edge spot;
  - 7 grading, route or goal problems (the two T24 apple ones are fixed, see section 5);
  - 7 execution (arm stopped short, held object grazes 2 mm, target moved);
  - 7 other base pose or spot searches;
  - 3 closing cabinet_4 finds no base pose;
  - 4 grasp kinds missing: cups and tissue in cabinet_4, a flat book;
  - 3 millimetre contacts during the pinch (apple, banana, tray);
  - 1 fridge door opened only to about 60°;
  - 1 spoon bounced out of the basket;
  - 1 out of reach (T18).

## 2. What "carry tilt held" is (code: `Motion._plan_js` / `plan_to`, zeno_skills/motion.py)

Two different failures share the message:

1. **"carry tilt held: MotionGenStatus.FINETUNE_TRAJOPT_FAIL"** (22 times in the 1113 logs). **The status is
   mislabeled.** The first trajopt pass had no feasible seed and finetune never ran. cuRobo
   (motion_gen.py, about line 3573) overwrites TRAJOPT_FAIL with FINETUNE_TRAJOPT_FAIL whenever finetune is enabled
   and nothing succeeded.
2. **"carry tilt held: tilts X rad"** (14 times, X = 0.15–0.26). A plan was found, but the TCP tilts more than
   `CARRY_TILT` 0.15 from the *start*.

## 3. Reproduction on current code (one sim at a time, `/data/zenobench/tiltdiag_1114`)

The worktree `wt` is d116156 plus the working tree. The 9 tilt-held episodes failed again in the 1113 run on
c5b71ab, which does not contain the collider change 9f011ec. Reproduced here on d116156, which does contain it, so
the collider change is not the cause.

| Episode | Rerun | Mechanism |
|---|---|---|
| T01 table_seats | **OK** | intermittent |
| T19 bin_on_bookcase | **OK** | intermittent |
| T07 vessel_decides_appliance foil tray | fails every time | **self collision right_gripper_link ↔ head_link**. The pick park is now [6.87, 2.47, -90°] (11-12: [6.03, 1.98, 0°]). Its IK bows the waist 0.7 rad and folds the wrist up beside the lowered head; the carry keeps that posture. All 6 trajopt seeds collide 5–8 steps in. No tilt metric: same failure. Load off: same failure. The pair was checked before 90a2a31 too. The head is locked at its live pitch for planning and pitches down to look, so the hand is clear at planning and touching afterwards. |
| T23 by_kind spoon | fails every time | Same start posture, grasp and park candidate as the 11-12 success. The place goal IK is the flipped branch (joint 2 0.10 → 2.89). At that base all 145 IK solutions are elbow-up (offline, 256 seeds). The goal itself is 0.11 rad off the start tilt, and `_plan_js` allows max_tilt 0.15 *from the start*: 0.04 rad of slack (`plan_to` allows CARRY_TILT + goal tilt — inconsistent). The tilt-held plan: about half the attempts have no feasible seed (fingers and spoon 2–11 mm into static geometry), the other half succeed but tilt 0.19. Moving the base environment (11c1196) away changes nothing. Removing the load makes it plan. |

Open questions:
- Why the same T23 query passed on 11-12. The user said not to run historical A/B, so this was not checked.
- Why the T07 pick in the sim took the elbow-up solution. Offline, the ranking IK finds elbow-down solutions for
  that pose, and the one nearest the tuck posture is elbow-down. A park dump of the T07 pick (`ZB_PARK_DUMP`,
  `ZB_PARK_DUMP_MATCH="pick foil"`) would show it.

Tools and data:
- `diag/*.jsonl`: per-term cuRobo constraint breakdown at the infeasible steps.
- `tmp/selfpairs.py`: offline nearest self-collision pairs.
- `tmp/elbow.py`: link positions and an IK branch survey.
- `tmp/seeds.py`: branch coverage of ranking IK seeds.
- `tmp/elbow_all.py` with `tmp/allcarry.json`: elbow metric against place outcome.

## 4. Analysis and agreed direction (discussion with the user, not implemented)

**Root idea.** Each stage filters by its own proxy, and none asks whether the next stage can still succeed:
- park candidate filters;
- ranking IK: kinematic only, nearest to the seed, scored by manipulability, limit margin and clearance of the
  relay pose alone;
- build: this skill's legs only;
- carry: keeps whatever posture the grasp ended in;
- head: locked at its live angle but moves later;
- tilt: two thresholds;
- the edge place `find_park` is called without `carry=True`, although execution plans the move with the tilt held.

**Elbow metric.** Elbow height above the shoulder–wrist line, in m. It does **not** predict failure. 98 of 176
places in the 1113 run start from an elbow-up carry (> +8 cm), and 95% of those succeed — the best group. The
elbow-down and neutral groups are at 78–80%. So "penalise backhand / elbow-up" is the wrong criterion.

**Branches.** Joint space is a convex box, so any two postures are connected when nothing is constrained. A real
branch exists only with the TCP pose fully fixed. Holding only the tilt removes 2 DOF, but:
- joint 4 (elbow) stays within [0.03, 2.50] and cannot flip, so going from elbow-down to elbow-up swings the elbow
  around the shoulder–wrist axis;
- joint 6 (wrist) is only ±0.755 rad.

Together these leave a narrow, wide-sweeping corridor. This is inferred from the joint limits and not yet measured
along T23's trajectory.

**Agreed plan.** No mandatory hand-off posture: it can break moves that now go directly, and the data contradicts
an elbow standard. Instead:
1. **Consistency: one definition per check, no new coupling.**
   - A single tilt rule.
   - Hand-to-head clearance checked over the head's look range, or the head held still during arm moves.
   - Report "no feasible trajopt seed" instead of FINETUNE.
2. **Soft transition cost in the park ranking (park_search only).** A cheap joint-interpolation check from the
   *actual current posture* to the relay solution: tilt along it (`tips_over`), self collision, head distance.
   Directly reachable cases are not penalised.
3. **Re-posture only as a fallback.** On a start-posture-type failure (self collision, no feasible seed), move to
   a posture meeting check 1 and retry once. Never worse than now, apart from time.

Order: 1, then 2, then 3. After each, rerun only the 10 tilt-held episodes, one sim at a time. Then a full v6
run, which becomes the new baseline.

## 5. Uncommitted work in the tree

**Mine, to commit when asked:**
- Apple / round-object grading: `Geometry.resting` uses the asset's real collider hull (`annotations/assets.json`
  `collider_hull`, all 45 assets) instead of the tilted box corner.
  - `tools/collider_hulls.py` is new and runs in the container with the Isaac app.
  - `tools/prepare_assets.py` keeps the hulls when it writes the file.
  - Tests in `tests/test_behind_door.py`; docs in `docs/skills/place.md`.
  - The T24 apple rerun passes.
- `zeno_skills/skills.py`: the pick message no longer says "no None pinch".
- Park arm overlay visualisation:
  - `zeno_skills/park_search.py` dump of `ranked_arms` / `world` (debug, only with `ZB_PARK_DUMP`);
  - `tools/park_arms_png.py`, `tools/park_arms_view.py`, `tools/park_arms_view.html`;
  - artifact https://claude.ai/artifact/RRjPVws9XfGVAGcvh99Zbq (10 no-grasp episodes).

**Debug only, remove before any commit:** `zeno_skills/motion.py`
- `TILT_DIAG` / `Motion._tilt_diag` (env `ZB_TILT_DIAG`);
- the `TILT_HELD` and `TILT_DIAG` prints;
- the diag call sites in `_plan_js` and `plan_to`.

`.claude/launch.json` (local preview server) is untracked.

## 6. Operating constraints

- One Isaac sim at a time. Another session (`traydepth_1114`) also runs sims on this GPU, and one of my reruns hit
  CUDA OOM. Wait until `docker ps -q` is empty before launching.
- No unasked historical A/B runs. Rerun only the affected episodes.
- Changes to assets, colliders or grasp annotations: ask first, because they move the baseline.
- Do not push. Commit only when asked, and only your own hunks.
