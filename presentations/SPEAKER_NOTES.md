# ZenoBench group meeting — speaking notes

These notes match the 20-slide [presentation](ZenoBench_group_meeting.pptx), built by
[`build_zenobench_deck.py`](build_zenobench_deck.py). Slides 11–18 cover the planning benchmark
([benchmark/README.md](../benchmark/README.md)). The last two slides are full-slide reconstructions of the two
upper-level architecture figures.

1. **Title.** ZenoBench turns generated 3D content into household tasks a mobile robot can execute and we can score, and now into a benchmark for the planner above the skills.
2. **EmbodiedGen V2.** Upstream generates assets, multi-room scenes and task worlds from language or images. [Official README](https://github.com/HorizonRobotics/EmbodiedGen/blob/master/README.md)
3. **What I built.** Generated task assets prepared for interaction, a reusable 10-room home, eight whole-task definitions, and a 10-task planning benchmark. The house layout comes from Infinigen; task objects come from EmbodiedGen V2.
4. **What it can do.** The robot moves through rooms, handles different objects, operates doors and appliances, and completes state-checked goals.
5. **Skill library.** 70 verb SkillNodes, 70 Contracts and 120 policy paths over 114 low-level policies. A Contract checks GT preconditions, picks a policy path by noun, then checks GT postconditions. The regression of the library's 35 scenarios on benchmark-v1 (2026-10-18): 27 pass, 8 fail, none new. Six failed before at the same step. k_separate and k_restore_swap fail the same way on a clean 15d948e. Do not say that all 70 skills are stable. [Skill library](../skill_library/README.md)
6. **Task suite.** Eight specs span collection, organization, preparation and appliances. They are reusable tasks in one house, not eight separate houses.
7. **Task showcase.** Examples: fruit collection across rooms, floor toy storage, flat-book shelving. Videos: [fruits](../media/tasks/collect_fruits.mp4), [toys](../media/tasks/tidy_toys.mp4), [books](../media/tasks/shelve_books.mp4).
8. **Breakfast example.** The robot moves oatmeal from fridge to microwave to table. Its [recorded seed-0 rollout](../media/tasks/heat_breakfast.mp4) satisfied all goals; this is one representative run. [Result JSON](../media/tasks/heat_breakfast.result.json)
9. **Current whole-task results.** Seven of eight task definitions have a successful representative run. `breakfast_setup` reached 67% after dropping a mug. This is a status snapshot, not a multi-seed success rate. [Task table](../README.md#tasks-zenobench)
10. **Why useful.** An upper-level planner selects skills, grounds them, observes the result and recovers. The next slides turn that into a measured test.
11. **Planning benchmark.** Every planner gets the same 70 SkillNodes with auto-recovery off and the same limited observation. The Isaac Sim GT verifier decides success. The question is whether the planner picks an effective fallback or alternative from what it sees and from the execution feedback.
12. **Observation boundary.** The planner's input: the first-person image, the objects observed so far, known places, the robot state, measured temperatures, and the last call's feedback. A call on an object that was never observed is refused by the gate. Feedback falls into three classes: grounding, precondition (nothing executed) and execution (physics failed). Interface: `reset` / `next_call`; returning `None` gives `planner_done`, `max_calls` gives `budget`, an exception makes the run `incomplete`.
13. **Ten tasks, three tiers.** The instruction is the same in every tier. Medium adds one condition (the fallback or alternative condition), hard adds a second (another room, facing away). There are 29 task × tier combinations because T05 has no easy tier: the pen slips 4/4, so its route is diagnostic. There are also 21 probes.
14. **T01 example.** Head-camera frames from `benchmark/runs/retest`, seed 0. With no overhang, the edge pinch really fails; expose slides the book over the edge, then pick and place work. Retest on current code: nominal 2/2, fallback 2/2, hard 1/2 (seed 1: the book slips during place). `fixed` stops after the failed pick.
15. **Other recoveries.** T02 pick fails → push (fallback); T09 collect refused because the lid is on → uncover (fallback); T07 the microwave does not heat → stove (alternative). The frames come from the declared scripted routes, seed 0.
16. **Scoring.** Task success and skill success are reported separately, and crashed runs are `incomplete`. `fixed`, `retry` and the VLM share the gate, settings and budget. The oracle uses GT and nested repair: it is an upper bound, reported separately, and the fixed–oracle gap is not a VLM gain. SPL counts only against an oracle route that passed; an empty denominator shows N/A. Eval grid: 58 episodes per planner. It has not been run yet.
17. **Status.** Declared routes: 59/62 episodes pass (27 stable, 3 flaky routes: T01 hard and the two T02 separate routes). Oracle 9/10 tasks; fixed and retry 2/10 each, one episode per task. 65/70 SkillNodes succeeded in a real call (4 called but failed, `release` never called). Probes 14/21. Route replays are feasibility evidence, not planner results. 105 of 113 route episodes ran on 15d948e+dc4ae8f; only T01 was rerun on the current code.
18. **Next steps.** (1) Connect a real VLM on 3–4 stable tasks; (2) rerun every route on current code; (3) fix the flaky routes by local layout first, otherwise mark them diagnostic; (4) run the eval grid.
19. **Upper-level Figure 1.** Full-slide reconstruction of the supplied diagram; the next speaker explains the Skill-Graph-based execution loop.
20. **Upper-level Figure 2.** Full-slide reconstruction of the supplied diagram; the next speaker explains the Skill Library interface from semantic SkillNodes and Contracts to low-level policies.

## Source boundary

- EmbodiedGen V2 capabilities: [official README](https://github.com/HorizonRobotics/EmbodiedGen/blob/master/README.md).
- ZenoBench facts and recorded results: [repository README](../README.md), [skill verification](../skill_library/verification/STATUS.md).
- Benchmark facts: [benchmark/README.md](../benchmark/README.md), [RESULTS.md](../benchmark/RESULTS.md), [EVALUATION.md](../benchmark/EVALUATION.md). The benchmark frames on slides 14–15 are copied into [`frames/`](frames/) from `benchmark/runs/`, which is not tracked.
- The planner interface and its harness exist, but they have been tested only with test planners. No VLM result is shown in this deck.

Slides 19–20 use high-resolution reconstructions of the two chat images, keeping their visible labels and structure. Their editable SVG sources are in [`figures/`](figures/).

Rebuild: `pip install python-pptx opencv-python-headless pillow`, then run `python presentations/build_zenobench_deck.py` from the repository root.
