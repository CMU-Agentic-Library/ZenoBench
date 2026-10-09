---
name: wipe-surface
description: Press a held sponge on a support and sweep a 30 cm strip twice; succeeds when the sponge stayed in contact over at least half of the strip.
---

# Wipe a surface (`wipe`)

`wipe(surface: support_ref, tool: tool_ref)`

Press a held sponge on a support and sweep a 30 cm strip twice; succeeds when the sponge stayed in contact over at least half of the strip.

## When to use

A surface must be wiped with a held sponge or cloth.

## Not to be confused with

- `sweep`: wipe uses a held tool on the surface itself.

## Inputs

- `surface` (`support_ref`): The support to clean.
- `tool` (`tool_ref`): The held wiping tool (sponge).

## Outputs

- `coverage` (`number`): Fraction of the strip wiped in contact.

## Call

Send one JSON object:

```json
{"contract": "wipe", "args": {"surface": "<support>", "tool": "<tool>"}}
```

Argument formats:

- `support_ref`: an annotated horizontal support surface
- `tool_ref`: an object tagged as a hand tool (sponge, spoon)

Scene names are the object names listed in the observation.

The reply contains:

- `success`: true when every precondition held, the action ran and every postcondition holds
- `error_code`: on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, SUBSKILL_FAILED or POSTCONDITION_FAILED
- `preconditions`: each precondition as evaluated before moving, with holds = true/false
- `postconditions`: each postcondition as evaluated after the action, with holds = true/false
- `outputs`: the measured values listed under Outputs

## Applicability

Requires holding(hand=right, object=$tool); base_near(place=$surface).

## Preconditions (checked before moving)

- `holding(hand=right, object=$tool)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.
- `base_near(place=$surface)` — Base centre within 1.3 m of the place's footprint (inside the room for a room).

## Postconditions (checked after the action)

- `wiped(support=$surface)` — A held wiping tool stayed in contact with at least 50 % of the requested strip of the support.
- `holding(hand=right, object=$tool)` — The object is in the given gripper: fingers not shut, TCP-to-body distance unchanged since the grasp.

## Failure

Stop and report the measured preconditions and postconditions. Nothing is retried.

