# ZenoBench group meeting — speaking notes

> Historical notes for a past talk; slated for removal. They describe a Skill-Graph execution loop with recovery and older counts, which no longer match the design (verb Contracts called by an external planner, no relations or fallback, 35 tasks in `skill_library/tasks.json`).

These notes match the 12-slide [presentation](ZenoBench_group_meeting.pptx). The last two slides contain full-slide reconstructions of the two supplied upper-level architecture figures.

1. **Title.** ZenoBench turns generated 3D content into household tasks a mobile robot can execute and we can score.
2. **EmbodiedGen V2.** Upstream generates assets, multi-room scenes and task worlds from language or images. [Official README](https://github.com/HorizonRobotics/EmbodiedGen/blob/master/README.md)
3. **What I built.** The repo has generated task assets prepared for interaction, a reusable 10-room home, and eight task definitions. The house layout comes from Infinigen; task objects come from EmbodiedGen V2.
4. **What it can do.** The robot moves through rooms, handles different objects, operates doors and appliances, and completes state-checked goals.
5. **Current atomic policies.** The catalog has 60 OOP entries. Fifty-four passed at least one Isaac Sim smoke test; six are callable but unverified. Show representative families: navigation/moving manipulation, posture, object-specific pick/place, and articulated/appliance control. These results concern the recorded scene and action, not all assets or initial states. [Catalog](../docs/POLICY_CATALOG.md)
6. **Task suite.** Eight specs span collection, organization, preparation and appliances. They are reusable tasks in one house, not eight separate houses.
7. **Task showcase.** Examples: fruit collection across rooms, floor toy storage, flat-book shelving. Videos: [fruits](../media/tasks/collect_fruits.mp4), [toys](../media/tasks/tidy_toys.mp4), [books](../media/tasks/shelve_books.mp4).
8. **Breakfast example.** The robot moves oatmeal from fridge to microwave to table. Its [recorded seed-0 rollout](../media/tasks/heat_breakfast.mp4) satisfied all goals; this is one representative run. [Result JSON](../media/tasks/heat_breakfast.result.json)
9. **Current whole-task results.** Seven of eight task definitions have a successful representative run. `breakfast_setup` reached 67% in the recorded run after dropping a mug. This is a status snapshot, not a multi-seed success rate. [Task table](../README.md#tasks-zenobench)
10. **Why useful.** The environment lets an upper-level planner select skills, ground them in a physical scene, observe the result and recover. Hand off to the presenter of the upper-level design.
11. **Upper-level Figure 1.** Full-slide reconstruction of the supplied diagram; the next speaker explains the Skill-Graph-based execution loop.
12. **Upper-level Figure 2.** Full-slide reconstruction of the supplied diagram; the next speaker explains the Skill Library interface from semantic SkillNodes and Contracts to low-level policies.

## Source boundary

- EmbodiedGen V2 capabilities: [official README](https://github.com/HorizonRobotics/EmbodiedGen/blob/master/README.md).
- ZenoBench facts and recorded results: [repository README](../README.md), [policy verification](../docs/POLICY_VERIFICATION.md).
- The architecture slides concern the **proposed upper layer**. The current repo does not yet implement an automatic VLM Skill Graph planner or replanning loop.

The two chat images did not arrive as local binary files. Slides 11–12 use high-resolution diagram reconstructions preserving the visible labels and structure; their editable SVG sources are in [`figures/`](figures/).
