# policy_064 — wait_for_temperature

在已启动的热模型中等待食品达到目标温度

## Scope

One low-level controller invocation. Reported effect: `temperature_at_least(object, min_temp_c)`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `min_temp_c`: positional_or_keyword; required
- `max_wait_s`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_064.execute(...)`
- Legacy alias: `PolicySuite(rig).wait_for_temperature.execute(...)`
- Class: `WaitForTemperaturePolicy`
- Availability: `verified`
- Direct Contract routes: contract_048

## Caveat

Uses task-level temperature model and bounded live simulation steps; requires physical start first.

## Recorded evidence

Isaac Sim heat_breakfast_preloaded: contract_048 waited from 4 C to 63.6 C after physical start-button press, runs/node_contract_heat_wait/result.json, 2026-10-05
