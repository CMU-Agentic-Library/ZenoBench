"""Compile skill_library/definitions.py into every SkillNode / Contract export.

    python tools/build_skill_library.py          # write
    python tools/build_skill_library.py --check  # fail if any export is stale or the library is invalid

Writes
  skill_library/skills/skill_XXX/{skill.json, SKILL.md}   one Agent-Skill folder per verb
  skill_library/vlm_skill_catalog.json                    every skill.json in one file, for the VLM prompt
  skill_library/catalog.json                              index
  skill_library/SKILLS.md                                 human table (verbs, nouns, paths)
  contract_library/skill_contracts.json                   runtime catalog read by SkillContractRunner
  contract_library/contracts/contract_XXX/{contract.json, CONTRACT.md}
  contract_library/catalog.json                           index (+ the eight legacy family contracts)
  policy_library/POLICY_COVERAGE.md                       which skill paths use each policy
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from skill_library.check import RETIRED_POLICIES, check_library  # noqa: E402
from skill_library.definitions import SKILLS  # noqa: E402
from zeno_skills.predicates import ALL_TYPES, GT_SOURCES, REGISTRY  # noqa: E402

SKILL_OFFSET = 1
CONTRACT_OFFSET = 9          # contract_001..008 are the legacy family contracts


def _json(obj):
    return json.dumps(obj, indent=1, ensure_ascii=False) + "\n"


def atom_text(a):
    args = ", ".join(f"{k}={v}" for k, v in a["args"].items())
    return ("not " if a.get("negated") else "") + f"{a['pred']}({args})"


def atom_record(a, role):
    p = REGISTRY[a["pred"]]
    rec = {"predicate": atom_text(a), "name": a["pred"], "args": a["args"], "negated": bool(a.get("negated")),
           "meaning": p.doc, "kind": p.kind, "gt_sources": GT_SOURCES[a["pred"]]}
    rec["checked"] = ("before execution on live GT state; the Contract does not move if false"
                      if role == "pre" else "after the policy chain on live GT state; the action is reported only if true")
    return rec


def cond_text(c):
    v = c["value"]
    return {"equals": f"{c['noun']}.{c['field']} == {v!r}", "in": f"{c['noun']}.{c['field']} in {v!r}",
            "contains": f"{v!r} in {c['noun']}.{c['field']}", "gte": f"{c['noun']}.{c['field']} >= {v}",
            "lte": f"{c['noun']}.{c['field']} <= {v}", "truthy": f"{c['noun']}.{c['field']}",
            "falsy": f"not {c['noun']}.{c['field']}"}[c["op"]]


def step_text(step):
    if "foreach" in step:
        return f"for each {step['as']} in {step['foreach']}: " + " -> ".join(step_text(s) for s in step["steps"])
    if "call" in step:
        return f"[{step['call']}]({', '.join(f'{k}={v}' for k, v in step['args'].items())})"
    args = [str(a) for a in step["args"]] + [f"{k}={v}" for k, v in step["kwargs"].items()]
    out = f"{step['policy']}({', '.join(args)})"
    return out + (f" as {step['as']}" if step.get("as") else "")


def compile_records():
    from zeno_skills.policies import PolicySuite
    from zeno_skills.interface_ids import POLICY_PUBLIC_IDS
    names = {pid: legacy for legacy, pid in POLICY_PUBLIC_IDS.items()}
    records = []
    for i, s in enumerate(SKILLS):
        rec = dict(s)
        rec["skill_id"] = f"skill_{i + SKILL_OFFSET:03d}"
        rec["contract_id"] = f"contract_{i + CONTRACT_OFFSET:03d}"
        rec["policy_plan"] = {"selection": "first path whose noun conditions all hold, decided before any motion",
                              "on_no_match": "NO_PATH: the Contract refuses without moving",
                              "paths": s["paths"]}
        records.append(rec)
    return records, names


def planner_atom(a):
    """Planner-facing predicate: the atom and its meaning, without GT sources."""
    return {"predicate": atom_text(a), "meaning": REGISTRY[a["pred"]].doc}


ARG_FORMATS = dict(ALL_TYPES, pose2d="a base pose [x, y, yaw_deg] in metres and degrees")
RETURNS = {
    "success": "true when every precondition held, the action ran and every postcondition holds",
    "error_code": "on failure: INPUT_MISSING, INPUT_UNKNOWN, PRECONDITION_FAILED, NO_PATH, POLICY_FAILED, "
                  "SUBSKILL_FAILED or POSTCONDITION_FAILED",
    "preconditions": "each precondition as evaluated before moving, with holds = true/false",
    "postconditions": "each postcondition as evaluated after the action, with holds = true/false",
    "outputs": "the measured values listed under Outputs",
}


def skill_json(rec):
    required = [k for k, m in rec["inputs"].items() if m["required"]]
    sig = ", ".join(f"{k}: {m['type']}" + ("" if m["required"] else "?") for k, m in rec["inputs"].items())
    conditional = []
    for p in rec["policy_plan"]["paths"]:
        if p.get("requires") or p.get("ensures"):
            conditional.append({"when": [cond_text(c) for c in p["when"]] or ["always"],
                                "preconditions": [planner_atom(a) for a in p.get("requires", [])],
                                "postconditions": [planner_atom(a) for a in p.get("ensures", [])]})
    pre_txt = [atom_text(a) for a in rec["requires"]]
    summary = "Requires " + "; ".join(pre_txt) + "." if pre_txt else "No precondition."
    if any(c["preconditions"] for c in conditional):
        summary += " Some bound nouns add preconditions (see Conditions that depend on the bound nouns)."
    example_args = {k: f"<{m['type'].removesuffix('_ref')}>" for k, m in rec["inputs"].items() if m["required"]}
    types = sorted({m["type"] for m in rec["inputs"].values()})
    return {
        "schema_version": 2, "kind": "skill_node",
        "skill_id": rec["skill_id"], "name": f"{rec['verb']}-{rec['noun']}", "verb": rec["verb"], "noun": rec["noun"],
        "title": rec["title"], "group": rec["group"],
        "signature": f"{rec['verb']}({sig})",
        "description": rec["description"], "use_when": rec["use_when"],
        "not_to_be_confused_with": rec["distinct_from"],
        "inputs": rec["inputs"], "required_inputs": required, "outputs": rec["outputs"],
        "applicability": {"always": not pre_txt and not any(c["preconditions"] for c in conditional),
                          "summary": summary},
        "preconditions": [planner_atom(a) for a in rec["requires"]],
        "postconditions": [planner_atom(a) for a in rec["ensures"]],
        "conditional": conditional,
        "invalidates": rec["invalidates"],
        "failure": {"on_failure": "stop and report the measured pre/postconditions; nothing is retried.",
                    "typical": rec["failure_modes"]},
        "scope": rec["scope"],
        "call": {"request": {"contract": rec["verb"], "args": example_args},
                 "arg_formats": {t: ARG_FORMATS[t] for t in types},
                 "returns": RETURNS},
    }


def _policies(steps):
    for st in steps:
        if "foreach" in st:
            yield from _policies(st["steps"])
        elif "policy" in st:
            yield st["policy"]


def contract_json(rec):
    verifier = []
    for a in rec["ensures"]:
        verifier.append(dict(atom_record(a, "post"), scope="all paths"))
    for p in rec["policy_plan"]["paths"]:
        for a in p.get("ensures", []):
            verifier.append(dict(atom_record(a, "post"), scope=f"path {p['path_id']}"))
    precheck = [dict(atom_record(a, "pre"), scope="all paths") for a in rec["requires"]]
    for p in rec["policy_plan"]["paths"]:
        for a in p.get("requires", []):
            precheck.append(dict(atom_record(a, "pre"), scope=f"path {p['path_id']}"))
    return {
        "schema_version": 2, "kind": "skill_contract",
        "contract_id": rec["contract_id"], "verb": rec["verb"], "noun": rec["noun"],
        "name": rec["title"], "description": rec["description"], "group": rec["group"],
        "inputs": rec["inputs"], "outputs": rec["outputs"],
        "requires": rec["requires"], "ensures": rec["ensures"], "invalidates": rec["invalidates"],
        "precheck": precheck, "verifier": verifier,
        "noun_binding": {slot: {"type": m["type"], "attributes_from": "zeno_skills.skill_runtime.bind_nouns (GT)"}
                         for slot, m in rec["inputs"].items() if m["type"].endswith("_ref")},
        "action_predicate": {"name": f"{rec['verb']}_{rec['noun']}", "verb": rec["verb"], "noun": rec["noun"],
                             "arguments": list(rec["inputs"])},
        "policy_plan": rec["policy_plan"],
        "failure": {"stop_and_report": True},
        "scope": rec["scope"],
    }


def skill_md(js):
    L = ["---", f"name: {js['name']}", f"description: {js['description']}", "---", "",
         f"# {js['title']} (`{js['verb']}`)", "", f"`{js['signature']}`", "", js["description"], ""]
    if js["use_when"]:
        L += ["## When to use", "", js["use_when"], ""]
    if js["not_to_be_confused_with"]:
        L += ["## Not to be confused with", ""] + [f"- `{k}`: {v}" for k, v in js["not_to_be_confused_with"].items()] + [""]
    L += ["## Inputs", ""] + [f"- `{k}` (`{m['type']}`{'' if m['required'] else ', optional'}"
                              f"{', one of ' + ', '.join(repr(x) for x in m['enum']) if 'enum' in m else ''}"
                              f"{', default ' + repr(m['default']) if 'default' in m else ''}): {m['description']}"
                              for k, m in js["inputs"].items()] + ([""] if js["inputs"] else ["- none", ""])
    if js["outputs"]:
        L += ["## Outputs", ""] + [f"- `{k}` (`{m['type']}`): {m['description']}" for k, m in js["outputs"].items()] + [""]
    call = js["call"]
    L += ["## Call", "", "Send one JSON object:", "", "```json", json.dumps(call["request"], ensure_ascii=False),
          "```", ""]
    if call["arg_formats"]:
        L += ["Argument formats:", ""] + [f"- `{t}`: {d}" for t, d in call["arg_formats"].items()] + [""]
    L += ["Scene names are the object names listed in the observation.", "", "The reply contains:", ""]
    L += [f"- `{k}`: {d}" for k, d in call["returns"].items()] + [""]
    L += ["## Applicability", "", js["applicability"]["summary"], ""]
    L += ["## Preconditions (checked before moving)", ""]
    L += [f"- `{p['predicate']}` — {p['meaning']}" for p in js["preconditions"]] or ["- none"]
    L += ["", "## Postconditions (checked after the action)", ""]
    L += [f"- `{p['predicate']}` — {p['meaning']}" for p in js["postconditions"]] or ["- none"]
    if js["conditional"]:
        L += ["", "## Conditions that depend on the bound nouns", ""]
        for c in js["conditional"]:
            parts = [f"needs `{x['predicate']}`" for x in c["preconditions"]] + \
                    [f"ensures `{x['predicate']}`" for x in c["postconditions"]]
            L.append(f"- when {' and '.join(c['when'])}: " + "; ".join(parts))
    if js["invalidates"]:
        L += ["", "## May invalidate", "", ", ".join(f"`{x}`" for x in js["invalidates"])]
    L += ["", "## Failure", "", "Stop and report the measured preconditions and postconditions. Nothing is retried.", ""]
    L += [f"- {f}" for f in js["failure"]["typical"]]
    L += [""]
    return "\n".join(L)


def contract_md(cj):
    L = [f"# {cj['contract_id']} — {cj['name']}", "", cj["description"], "",
         f"Verb: `{cj['verb']}`.", "", "## Precheck", ""]
    L += [f"- [{p['scope']}] `{p['predicate']}` — GT: {', '.join(p['gt_sources'])}" for p in cj["precheck"]] or ["- none"]
    L += ["", "## Verifier", ""]
    L += [f"- [{p['scope']}] `{p['predicate']}` — GT: {', '.join(p['gt_sources'])}" for p in cj["verifier"]]
    L += ["", "## Policy paths", ""]
    for p in cj["policy_plan"]["paths"]:
        L.append(f"- `{p['path_id']}` when {' and '.join(cond_text(c) for c in p['when']) or 'always'}: "
                 + " -> ".join(f"`{step_text(s)}`" for s in p["steps"]))
    L += ["", "The runtime chooses the first path whose conditions hold; callers cannot select a path.", "",
          "Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.", ""]
    return "\n".join(L)


def skills_table(records):
    L = ["# Verb-based SkillNodes", "",
         "Generated by `tools/build_skill_library.py` from `skill_library/definitions.py`; do not edit by hand.", "",
         "| SkillNode | Verb + noun | Signature | Postconditions |", "|---|---|---|---|"]
    for r in records:
        sig = ", ".join(f"{k}{'' if m['required'] else '?'}" for k, m in r["inputs"].items())
        post = ", ".join(f"`{a['pred']}`" for a in r["ensures"]) or "depends on the bound nouns"
        extra = {a["pred"] for p in r["paths"] for a in p.get("ensures", [])}
        if extra:
            post += " + " + ", ".join(f"`{x}`" for x in sorted(extra))
        L.append(f"| `{r['skill_id']}` | **{r['verb']}** {r['noun']} | `{r['verb']}({sig})` | {post} |")
    return "\n".join(L) + "\n"


def coverage_md(records, names):
    used = {}
    for r in records:
        for p in r["paths"]:
            for pid in _policies(p["steps"]):
                tag = f"{r['verb']}/{p['path_id']}"
                if tag not in used.setdefault(pid, []):
                    used[pid].append(tag)
    L = ["# Policy coverage by SkillNode paths", "",
         "Generated by `tools/build_skill_library.py`. Every public policy is reached by at least one "
         "noun-selected path, except retired policies (listed with the measured reason).", "", "| Policy | Name | Used by (skill/path) |", "|---|---|---|"]
    from skill_library.check import RETIRED_POLICIES
    for pid in sorted(names):
        where = used.get(pid) or ([f"retired: {RETIRED_POLICIES[pid]}"] if pid in RETIRED_POLICIES else ["**unused**"])
        L.append(f"| `{pid}` | `{names[pid]}` | {', '.join(where)} |")
    return "\n".join(L) + "\n"


def build():
    records, names = compile_records()
    errors = check_library(records)
    files = {}
    skills_js = []
    for r in records:
        js = skill_json(r)
        skills_js.append(js)
        base = Path("skill_library/skills") / r["skill_id"]
        files[base / "skill.json"] = _json(js)
        files[base / "SKILL.md"] = skill_md(js)
        cj = contract_json(r)
        cbase = Path("contract_library/contracts") / r["contract_id"]
        files[cbase / "contract.json"] = _json(cj)
        files[cbase / "CONTRACT.md"] = contract_md(cj)
    files[Path("skill_library/vlm_skill_catalog.json")] = _json({
        "schema_version": 2, "kind": "vlm_skill_catalog",
        "how_to_use": "Each SkillNode is one verb + one noun; call its Contract by verb with the typed inputs. "
                      "The executor verifies every pre/postcondition on ground-truth simulator state and returns "
                      "the measured facts.",
        "predicates": {n: {"args": [list(a) for a in p.args], "kind": p.kind, "meaning": p.doc,
                           "gt_sources": GT_SOURCES[n]} for n, p in sorted(REGISTRY.items())},
        "skills": skills_js})
    files[Path("skill_library/catalog.json")] = _json({
        "schema_version": 2, "kind": "skill_catalog",
        "skills": [{"skill_id": r["skill_id"], "verb": r["verb"], "noun": r["noun"],
                    "definition": f"skills/{r['skill_id']}/skill.json"} for r in records]})
    files[Path("skill_library/SKILLS.md")] = skills_table(records)
    files[Path("policy_library/POLICY_COVERAGE.md")] = coverage_md(records, names)
    files[Path("contract_library/skill_contracts.json")] = _json({
        "schema_version": 2, "kind": "skill_contract_catalog",
        "contracts": [contract_json(r) for r in records]})
    from zeno_skills.contracts import CONTRACTS
    legacy = [{"contract_id": spec.public_id, "legacy_id": lid,
               "definition": f"contracts/{spec.public_id}/contract.json"} for lid, spec in CONTRACTS.items()]
    files[Path("contract_library/catalog.json")] = _json({
        "schema_version": 2, "kind": "contract_catalog",
        "contracts": [{"contract_id": r["contract_id"], "verb": r["verb"],
                       "definition": f"contracts/{r['contract_id']}/contract.json"} for r in records],
        "legacy_family_contracts": legacy})
    # public ID table (contracts by verb, policies with legacy aliases)
    ids = json.loads((ROOT / "zeno_skills/interface_ids.json").read_text())
    ids.pop("node_contract_ids", None)
    files[Path("zeno_skills/interface_ids.json")] = json.dumps(ids, indent=1) + "\n"
    L = ["# Public IDs", "", "Generated by `tools/build_skill_library.py`. Contracts are called by verb. "
         "`contract_001`-`contract_008` are the legacy family Contracts. Policies keep their descriptive names "
         "as aliases.", "",
         "## Contracts", "", "| Contract | Verb |", "|---|---|"]
    L += [f"| `{r['contract_id']}` | {r['verb']} |" for r in records]
    L += ["", "## Legacy family Contracts", "", "| Contract | Legacy name |", "|---|---|"]
    L += [f"| `{pub}` | `{leg}` |" for leg, pub in sorted(ids["contract_ids"].items(), key=lambda kv: kv[1])]
    L += ["", "## Policies", "", "| Policy | Alias (PolicySuite attribute) |", "|---|---|"]
    L += [f"| `{pub}` | `{leg}` |" for leg, pub in sorted(ids["policy_ids"].items(), key=lambda kv: kv[1])]
    files[Path("docs/INTERFACE_IDS.md")] = "\n".join(L) + "\n"
    # counts + verb table injected into skill_library/README.md
    n_paths = sum(len(r["paths"]) for r in records)
    n_tasks = len(json.loads((ROOT / "skill_library/tasks.json").read_text())["tasks"])
    counts = (f"**{len(records)} 个 SkillNode**（`skill_001`–`skill_{len(records):03d}`，{len(records)} 个不同动词），"
              f"**{len(records)} 个 Contract**（`contract_{CONTRACT_OFFSET:03d}`–`contract_"
              f"{len(records) + CONTRACT_OFFSET - 1:03d}`，按动词调用），共 **{n_paths} 条按名词选择的 policy 路径**，"
              f"覆盖 **{len(names) - len(RETIRED_POLICIES)}/{len(names)} 个底层 policy**"
              f"（{len(RETIRED_POLICIES)} 个因物理上不可行而退役，原因见 [POLICY_COVERAGE.md](../policy_library/POLICY_COVERAGE.md)）；"
              f"前后条件来自 **{len(REGISTRY)} 个 GT 谓词**。"
              f"[tasks.json](tasks.json) 列出 {n_tasks} 个任务。")
    table = skills_table(records).split("\n", 4)[4]
    readme = (ROOT / "skill_library/README.md").read_text()
    readme = _inject(readme, "counts", counts)
    readme = _inject(readme, "skills", "## 全部 SkillNode\n\n" + table)
    files[Path("skill_library/README.md")] = readme
    groups = {}
    for r in records:
        groups.setdefault(r["group"], []).append(r["verb"])
    gtitle = {"base_and_body": "底盘与身体", "perception_and_gesture": "感知与手势", "grasp_and_hand": "抓取与手",
              "contact": "非抓取接触与工具", "articulated_and_appliance": "门、抽屉与电器", "multi_object": "多物体（嵌套 Contract）"}
    lib = [f"**{len(records)} 个动词 SkillNode** 和 {len(records)} 个按动词调用的 Contract，共 {n_paths} 条按名词选择的 policy 路径，"
           f"覆盖 {len(names) - len(RETIRED_POLICIES)}/{len(names)} 个底层 policy（退役 {len(RETIRED_POLICIES)} 个，"
           f"见 [POLICY_COVERAGE.md](policy_library/POLICY_COVERAGE.md)）；前后条件来自 {len(REGISTRY)} 个 GT 谓词。", "",
           "| 类别 | 动词 |", "|---|---|"]
    lib += [f"| {gtitle.get(g, g)} | {', '.join(f'`{v}`' for v in vs)} |" for g, vs in groups.items()]
    files[Path("README.md")] = _inject((ROOT / "README.md").read_text(), "library", "\n".join(lib))
    n_policy = len(names)
    n_planner = sum(1 for leg in names.values() if leg.startswith("plan_"))
    files[Path("contract_library/README.md")] = _inject(
        (ROOT / "contract_library/README.md").read_text(), "counts",
        f"当前有 **{len(records)} 个 Skill Contract**（`contract_{CONTRACT_OFFSET:03d}`–`contract_"
        f"{len(records) + CONTRACT_OFFSET - 1:03d}`），按动词调用，"
        f"共 {n_paths} 条 policy 路径。")
    files[Path("policy_library/README.md")] = _inject(
        (ROOT / "policy_library/README.md").read_text(), "counts",
        f"当前有 **{n_policy} 个公开 policy**（`policy_001`–`policy_{n_policy:03d}`），其中 {n_planner} 个是只计算目标、"
        f"不运动的规划 policy；{n_policy - len(RETIRED_POLICIES)} 个被 {len(records)} 个 Contract 的路径覆盖"
        f"（{len(RETIRED_POLICIES)} 个退役，见 POLICY_COVERAGE.md）。")
    return files, errors, records


def _inject(text, key, body):
    a, b = f"<!-- {key}:start -->", f"<!-- {key}:end -->"
    i, j = text.index(a), text.index(b)
    return text[:i + len(a)] + "\n" + body.rstrip() + "\n" + text[j:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    files, errors, records = build()
    if errors:
        print("LIBRARY INVALID")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    managed_dirs = [ROOT / "skill_library/skills", ROOT / "contract_library/contracts"]
    expected = {ROOT / p for p in files}
    stale = []
    for path, text in files.items():
        full = ROOT / path
        if not full.exists() or full.read_text() != text:
            stale.append(str(path))
    keep_contracts = {f"contract_{i:03d}" for i in range(1, CONTRACT_OFFSET)}
    extra = []
    for d in managed_dirs:
        for child in d.iterdir() if d.exists() else []:
            if child.name in keep_contracts:
                continue
            if not any(e.parent == child for e in expected):
                extra.append(child)
    if args.check:
        if stale or extra:
            print("STALE:", stale[:20], "EXTRA:", [str(e.relative_to(ROOT)) for e in extra][:20])
            sys.exit(1)
        print(f"OK {len(records)} SkillNodes, {len(files)} exports up to date")
        return
    for child in extra:
        shutil.rmtree(child)
    for path, text in files.items():
        full = ROOT / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(text)
    print(f"WROTE {len(files)} files for {len(records)} SkillNodes; removed {len(extra)} stale folders")


if __name__ == "__main__":
    main()
