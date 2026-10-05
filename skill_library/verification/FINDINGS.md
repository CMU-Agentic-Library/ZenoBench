# Remaining physical findings

The 42 SkillNodes have been checked as interfaces and each has a physical verification outcome in [STATUS.md](STATUS.md). A physical pass means at least one representative Contract call met its measured postconditions. It does not cover every noun, path, or random scene.

| SkillNode | Current result | Measured blocker | Next engineering step |
| --- | --- | --- | --- |
| `skill_015` / `contract_023` cavity retrieval | Attempted; no Contract pass | In the microwave fixture, the insertion-reversal contact missed by **0.229 m** on repeated runs. Replanning through annotated rim grasps found no reachable pose. | Repair the cavity return/approach trajectory or search a distinct reachable park, then repeat placement and retrieval in one scene. |
| `skill_020` / `contract_028` floor-corner pick | Attempted; no Contract pass | A floor book missed contact by **0.068 m** even after slower tracking. A thinner toy car reached within **0.012 m** but did not lift; fingers closed without retaining it. | Revise corner contact geometry and grasp-force path; verify both contact error and post-lift finger/object state. |
| `skill_021` / `contract_029` two-hand carry | Blocked by preparation | `policy_056` failed to lift the book with two contacts in the current run; the carry Contract was never invoked. | Establish a repeatable bimanual grasp and then test a short base move with contact checks. |
| `skill_022` / `contract_030` open door while left hand holds | Blocked by preparation | After right-hand pick and height adjustment, `policy_059` found no independent left contact on the toy block; the door Contract was never invoked. | Add a feasible left-grasp presentation/handover route, then verify retained left grasp throughout door opening. |

The first two nodes remain callable but are marked experimental because their active Contracts have no passing physical run. The latter two were already marked experimental. Failures and setup plans are preserved in [node_contract_smoke.json](node_contract_smoke.json); each row links to its full `runs/.../result.json` report in the local workspace.
