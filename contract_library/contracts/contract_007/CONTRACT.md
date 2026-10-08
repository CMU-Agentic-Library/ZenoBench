# contract_007 — click.v1

Press one annotated appliance button.

## Scope

One fresh physical button press; start may also activate the task-level heating model.

## Inputs

- `appliance`: articulated_id; required
- `button`: enum; optional

## Requires

- `right_hand_empty` — runner
- `button_reachable` — policy_attempt
- `microwave_door_closed` — policy_attempt
- `task_food_inside_cavity` — policy_attempt

## Achieves on success

- `button_pressed_this_call` — runner
- `heating_active` — runner when button is start

## Routes

- `auto` → `policy_033`
- `start` → `policy_032`

## Outside this contract

- food reached a requested temperature

Legacy alias: `click.v1`. Runtime binding: `zeno_skills.contracts.CONTRACTS`.
