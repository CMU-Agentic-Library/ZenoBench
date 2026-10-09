# contract_050 — Press a button

Press an annotated appliance button with the closed fingertips and retract: the microwave door key, the microwave start key, or the stove power key (which toggles the burner).

Verb: `press`.

## Precheck

- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [all paths] `base_near(place=@button.appliance)` — GT: base_pose, scene_annotation
- [path microwave_start_staged] `is_closed(articulated=@button.appliance)` — GT: articulation_joint, articulation_annotation

## Verifier

- [all paths] `button_pressed(button=$button)` — GT: event_log (measured fingertip contact)
- [all paths] `hand_empty(hand=right)` — GT: gripper_state
- [path microwave_start_staged] `heating(appliance=@button.appliance)` — GT: thermal_state

## Policy paths

- `microwave_start_staged` when button.button == 'start_button': `policy_027(@button.appliance, button=start)` -> `policy_028(@button.appliance, button=start)` -> `policy_029(@button.appliance, button=start)`
- `microwave_door_key` when button.button == 'door_button': `policy_033(@button.appliance, button=door)`
- `generic_key` when always: `policy_094($button)`

The runtime chooses the first path whose conditions hold; callers cannot select a path.

Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.
