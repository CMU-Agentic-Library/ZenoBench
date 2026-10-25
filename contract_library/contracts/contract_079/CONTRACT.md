# contract_079 — Explore a piece of furniture

See every support layer of one piece of furniture (each shelf, the top, a cabinet's inside shelves): sweep from where the robot stands when it is already near, else from up to three stand-off poses in front of it, aiming the head at each layer not seen yet, then again with the torso lowered for the layers still hidden (a bottom shelf behind the front edge of the shelf above). A layer is seen when the space just above its board is in the head camera and no board of the piece is in the way. Succeeds only when every layer was seen; a closed cabinet door hides its inside layers.

Paired SkillNode: `skill_071` (`explore-furniture`).

## Precheck

- none

## Verifier

- [all paths] `furniture_explored(furniture=$furniture)` — GT: robot_memory, support_annotation

## Policy paths

- `layers` when always: `policy_116($furniture)`

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
