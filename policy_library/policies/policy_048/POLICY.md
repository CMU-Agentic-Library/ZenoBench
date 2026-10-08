# policy_048 — pick_from_cavity

从狭窄腔体正面取物并后撤

## Scope

One low-level controller invocation. Reported effect: `held(object) and outside_cavity`.
This effect summary is not a Contract guarantee.

## Preconditions

Policy-specific checks remain inside the controller and are not all normalized in this record.

## Execute inputs

- `name`: positional_or_keyword; required
- `cavity`: positional_or_keyword; optional
- `max_candidates`: keyword_only; optional

## Binding and status

- Runtime: `PolicySuite(rig).policy_048.execute(...)`
- Legacy alias: `PolicySuite(rig).pick_from_cavity.execute(...)`
- Class: `PickFromCavityPolicy`
- Availability: `verified`
- Skill Contract paths: contract_025:pick/microwave_cavity
- Legacy family Contracts: contract_002

## Caveat

仅验证同一 rig 刚放入杯子的回取路线；预置碗仍无可达抓取记录。中间上方位 TCP 一次短暂偏差 0.182 m，最终接触位偏差 0.0075 m。

## Recorded evidence

Isaac Sim dedicated microwave cup fixture: open, rim pick, cavity place, same-rig cavity retrieval; four contract postconditions passed, cup lift 0.0742 m and body 0.047 m outside mouth; runs/final_contract_microwave, 2026-10-02
