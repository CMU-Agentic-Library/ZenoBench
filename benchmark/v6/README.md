# ZenoBench v6: task design in four categories (design stage)

v6 is the task-design layer on top of v5. It reads `benchmark/v5/tasks.json` and never writes it. v6 adds new
variants on the 20 v5 base tasks and ten base tasks of its own (T21-T30, `new_tasks_v6.py`: everyday goals with one
step of reasoning each), removes every injected action failure, and puts each variant in one of four categories.

| | |
|---|---|
| base tasks | 30: T01-T20 from v5, T21-T30 new in v6 (`new_tasks_v6.py`); one house, 10 rooms, existing assets only |
| variants | 172; each runs seeds 10-19 (1,720 episodes) |
| categories | control 30 (one per task), Action-Level 0, Task-Level 137, Action + Task 5 (`TRACKS.md`) |
| static checks | 1,720 / 1,720 episodes |
| physics | none yet: every layout is new (seed generator); all STATIC_VALIDATED (`PHYSICS_TODO.md`) |

## Definitions

An episode is **task + variant + seed**.

* **Variant** = the task design: which dynamic events happen, which scene conditions hold (an
  absent object and its substitute, a lid on the pot, a book with something on it, a taken destination, an item
  in another room, the start room), which goal. Two variants differ in what the planner has to do.
  (`v6_variants[vid]` in `tasks.json`.)
* **Seed** (10-19, ten per variant) = the layout of that design:
  - where the objects stand and where the robot starts, drawn by the seed generator (`layout.py`, the variant's
    `layout` block): every cluster of task objects is moved to a random free place on its own support (stacks
    and crowded groups move together, an overhang stays; on a table or counter top every object ends within 35 cm of
    an edge the base can stand at (`layout.reach_edges`: not a side against a wall or furniture), elsewhere never
    deeper from the reachable edge than designed,
    clear of route and event places; objects in closed furniture or on an appliance stay). What the variant
    places differently from its control is its design - together with what stands within 15 cm of it, it moves
    as one group, or stays when any part has to (a full table, a boxed-in spoon, the bowl in the pin's path),
    so the seed never changes what the variant tests, and the robot starts
    at a random free, reachable cell of the start room with a random yaw (a hidden item is not in the start
    view). Routes never open with a `look` from the start: each opening look has a `navigate` to its target before
    it (`define_tasks_v6.navigate_first`), since the start can be 12 m away or behind furniture. Over the 1,270 episodes a moved object shifts 0.21 m
    (median, 90th percentile 0.86 m) and the start 3.8 m (90th percentile 8.4 m); which removable distractors
    are left out is drawn too;
  - for a variant with several **layouts** (56 variants), which one: the same design with the resource,
    substitute or item in another place, or an event taking it elsewhere (e.g. the cup in cabinet 4 or in
    cabinet 6). The seeds are spread over the layouts by a fixed-RNG, balanced manifest
    (`v6_variants[vid]["seeds"]`); each layout has its own configuration and oracle route (`variants[<layout>]`).
* **Control**: the variant this one differs from in one factor (`v6_variants[vid]["control"]`; for a v5
  variant the task's first nominal one).
* **Status**: PHYSICS_VALIDATED (every seed passed in simulation with the current hash and route),
  STATIC_VALIDATED (all static checks pass), DESIGN_COMPLETE (specified, static not passing).

Earlier multi-case families whose cases differed in the design, not only in place (which object lies on the
book, which failure mechanism, which subgoal the event undoes, how many places the instruction names), are
one variant per case (`SPLIT` in `define_tasks_v6.py`).

## Four categories (`tracks.py`, `TRACKS.md`)

Each variant contains the fallback its category is about; the category reads only the configuration
(`tracks.content`).

| category | the variant needs | variants | episodes |
|---|---|---|---|
| **Control** | nothing: the nominal plan works (the reference for the others) | 30 | 300 |
| **Action-Level** | a short fallback at the work spot, a few skills combined, then the plan goes on: expose a flat book before the pick, separate a crowded block, take the lid off, clear what lies on the target or open the door first, move clutter off the work strip, clear a full destination, move the base in from the edge (`LOCAL_CONDITIONS`, `local_failure`); also a dynamic event put right at the work spot: a book pushed back, a tomato taken out of the pot, a door opened again (`event_is_local`); none left as a variant of its own (TAMPAgent covers clearing a blocker), only inside Action + Task | 0 | 0 |
| **Task-Level** | a longer-horizon change of plan: a substitute, a search in another place or room, a capacity split, another destination / appliance / cookware, an object an event takes elsewhere | 137 | 1370 |
| **Action + Task** | both | 5 | 50 |

**No injected action failures, anywhere.** No IK refusal, grasp miss, slip or placement miss is forced on a
call, once or every time. Every challenge comes from the scene (an absent or hidden object, a lid on, a closed
door, a full destination, a book flat on the table ...) or from a dynamic event (someone moves an object).
`tracks.strip_injected` removes the v5 ones from every inherited variant and its route; a variant built on a
failure that never goes away (another object or procedure because an action never succeeds) is dropped, one
left with nothing is dropped, and one variant is kept per design (`tracks.design_key`: conditions, failures,
goal, instruction and the objects handled; not where things stand or where the robot starts, which is the
seed's part). `v6_dropped` per task says why each v5 variant left. The v6 design source has no such variants.
An initial resource / destination / capacity failure next to a scene condition only restates that condition
(`declares_condition`).

**Task-Level choices happen over a longer horizon.** A choice the robot could make where it already is (which
container, which cookware, the substitute next to it) is redesigned so the right one is in another room
(`LONG` / `REPLACED` in `define_tasks_v6.py`: the bins on the bedroom bookcase, the mug in the living room, the
pot on the dining table); the in-place variant leaves v6 (`v6_replaced`). T01 `table_seats` stays a choice at
the table: the instruction asks for a place beside a guest's setting, clear of the tableware, not which slot; the edge of the set table has several free slots (too
narrow, away from every seat, one beside a seat) and the seed picks one of three settings, so the suitable slot is
judged from what is seen, not remembered (`keep_design`: the seed leaves the setting as it is). T01 `which_table`
(it replaces `far_no_overhang`) adds the table itself: breakfast is set on one of the two dining tables (the near
one or the one in the west dining room, 16 m from the island), the other holds toys; the robot looks at the near
table and goes on when nobody eats there.

A goal of a variant's own (close the door again, leave the block on the island) states how a fallback ends and
does not by itself make a variant Task-Level.

Status: static (`validate_v6.py` checks that no injected failure is left and every category matches its
content). `oracle_check.py` replays every oracle route on a symbolic state (where each object is, the hand, open
doors, lids, temperatures, the robot's place): each step's preconditions (from the skill contracts, plus an item in
closed furniture needs the door open, a covered container takes nothing, the robot is near what it handles), the
dynamic events at their trigger, and at the end the goal (278 / 278 routes, all of them also under the benchmark's observation gate; atoms only geometry can decide, such as
upright or clear_of, are left to the simulation). Evaluation metrics are not defined yet.

Reference routes look before they use what the robot has not seen: when the catalog is built,
`oracle_check.observe_first` puts a walk to the object's support and a look (an object on the floor: an
explore of its room) before the first call that names an object not yet seen, so every route passes the gate.

`plan_dependence.py` screens the catalog for fixed plans and information dependence (report:
`PLAN_DEPENDENCE_zh.md`). It replays layouts on the symbolic state with the observation gate; `search` keeps to
its room, opens that room's closed cabinets and does not see under a lid. A plan passes when every step is legal
and every symbolic goal atom holds, process requirements included; geometric atoms are listed apart, and passing is
not a physics validation. It moves the control's route to every other variant, moves routes between the layouts of
a variant and asks whether one of them passes all layouts, and finds hidden-state branches (two layouts the same
before the key observation, each route failing on the other). Each failure is classified (unknown object, resource
missing, not observed, argument mismatch, goal not met). A fixed sequence that passes means one exists across the
layouts, not that the variant needs no observation; nothing is removed on these results. The leakage audit checks
what reaches a planner; the env_service ready message sends the variant (with the layout), its conditions and the
seed.

Goals accept every way that does what the person asked: `on_any` (either counter, the bookcase or the desk by the
bed), `count_on_at_least` over the house's own bowls and cups; and a process requirement is checked as one:
`never_picked` (the castle, the homework, a bowl in use are never lifted, not just back in place at the end).
Five variants chain decisions on hidden state (`dependent_decisions`): the layouts look the same before the key
observation, and what the robot finds on arrival or behind a door decides the later subgoals, resources or order
(the tissues in the first cabinet, the second or nowhere and then the sponge; the tray in the other room with an
orange or covered by books; the cups the guests still lack from the cabinet or a mug from the dining room; his cup
on the counter or in the cabinet; three bowls or two and a mug); the reference route may look first, nothing has to
fail first. `never_picked` holds when the objects were never lifted; it does not show they were never pushed or
that a structure never fell during the episode.

## Commands

```bash
python benchmark/v6/layout.py              # start_cells.json (free, reachable start cells per room; ~2 min)
python benchmark/v6/define_tasks_v6.py     # tasks.json (catalog + tracks); --check: up to date?
python benchmark/v6/validate_v6.py         # STATIC.json: per-episode static checks, v5 hashes, manifests
python benchmark/v6/report_v6.py           # variant_cards.json, ROUTES.md, SKILL_FIX_LIST.md, PHYSICS_TODO.md
python benchmark/v6/tracks.py              # TRACKS.md, batches/category_*.json
python benchmark/v6/success_routes.py      # SUCCESS_ROUTES_zh.md (after VARIANTS_zh.md)
python benchmark/v6/oracle_check.py        # ORACLE_CHECK.json: every route replayed on a symbolic state, goal tested
python benchmark/v6/plan_dependence.py     # PLAN_DEPENDENCE.json: which variants a plan fixed before the episode solves
$ISAACLAB_PYTHON benchmark/v6/render_variants.py --task T01   # Isaac Sim start-scene pictures -> ~/Pictures/<task>/<variant>/
python -m pytest -q benchmark/v6/tests failure_injection
$ISAACLAB_PYTHON benchmark/run_episode.py --tasks benchmark/v6/tasks.json \
    --batch benchmark/v6/batches/physics_v6_new.json --jobs 2 --out benchmark/runs/v6_physics --no-eval
```

A route step of a skill that has left the library (today `approach`: every manipulation skill picks its own base
park) is rewritten by `define_tasks_v6.py` through `benchmark/retired_skills.py`: dropped right after a navigate to
the same place, otherwise turned into that navigate. Write new routes without it.

## Files

* `VARIANTS_zh.md` - every variant in plain Chinese: the situation, what the robot does, what the seed chooses.
* `SUCCESS_ROUTES_zh.md` - every variant's success conditions (goal atoms, in Chinese) and reference skill call
  order (oracle route, one per layout).
* `PLAN_DEPENDENCE_zh.md` - fixed-route transfer and information dependence (symbolic screening), the hard
  variants' key observations, hidden facts and plan forks, the leakage audit.
* `TRACKS.md` - the four categories, counts per task, every variant with its local fallback and longer-horizon change.
* `variant_cards.json` - per concrete variant: instruction, initial conditions, failure triggers, goal, tracks,
  control, oracle route, challenge / rationale, success criteria.
* `ROUTES.md` - every oracle reference route, by track. `SKILL_FIX_LIST.md` - for the skill owner.
  `PHYSICS_TODO.md` + `batches/` - what still needs simulation.
