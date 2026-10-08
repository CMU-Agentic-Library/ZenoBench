"""Compile skill_library/definitions.py into every SkillNode / Contract export.

    python tools/build_skill_library.py          # write
    python tools/build_skill_library.py --check  # fail if any export is stale or the library is invalid

Writes
  skill_library/skills/skill_XXX/{skill.json, SKILL.md}   one Agent-Skill folder per verb
  skill_library/vlm_skill_catalog.json                    every skill.json in one file, for the VLM prompt
  skill_library/catalog.json                              index
  skill_library/relations.json                            sequence / fallback / alternative edges
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
from zeno_skills.predicates import GT_SOURCES, REGISTRY  # noqa: E402

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
    by_verb = {}
    for i, s in enumerate(SKILLS):
        rec = dict(s)
        rec["skill_id"] = f"skill_{i + SKILL_OFFSET:03d}"
        rec["contract_id"] = f"contract_{i + CONTRACT_OFFSET:03d}"
        rec["policy_plan"] = {"selection": "first path whose noun conditions all hold, decided before any motion",
                              "on_no_match": "NO_PATH: the Contract refuses without moving",
                              "paths": s["paths"]}
        by_verb[s["verb"]] = rec
    for rec in by_verb.values():
        for rel in rec["relations"]:
            rel["to_skill_id"] = by_verb[rel["to"]]["skill_id"] if rel["to"] in by_verb else None
    return list(by_verb.values()), by_verb, names


def skill_json(rec, by_verb, names, incoming):
    required = [k for k, m in rec["inputs"].items() if m["required"]]
    sig = ", ".join(f"{k}: {m['type']}" + ("" if m["required"] else "?") for k, m in rec["inputs"].items())
    rels = {"previous": [], "next": [], "fallback": [], "fallback_for": [], "alternative": []}
    for rel in rec["relations"]:
        item = {"skill_id": rel["to_skill_id"], "verb": rel["to"], "when": rel["when"], "bind": rel["bind"]}
        if rel.get("reason"):
            item["reason"] = rel["reason"]
        if rel["kind"] == "sequence":
            item["type"] = rel["sequence_type"]
            rels["next"].append(item)
        elif rel["kind"] == "fallback":
            item["type"] = rel["fallback_type"]
            if rel.get("repairs"):
                item["repairs"] = rel["repairs"]
            rels["fallback"].append(item)
        else:
            rels["alternative"].append(item)
    for src, rel in incoming.get(rec["verb"], []):
        item = {"skill_id": src["skill_id"], "verb": src["verb"], "when": rel["when"]}
        if rel["kind"] == "sequence":
            rels["previous"].append(dict(item, type=rel["sequence_type"]))
        elif rel["kind"] == "fallback":
            rels["fallback_for"].append(dict(item, type=rel["fallback_type"]))
        elif rel["kind"] == "alternative" and not any(a["verb"] == src["verb"] for a in rels["alternative"]):
            rels["alternative"].append(dict(item, bind={}))
    paths = []
    for p in rec["policy_plan"]["paths"]:
        paths.append({
            "path_id": p["path_id"],
            "when": [cond_text(c) for c in p["when"]] or ["always (default path)"],
            "extra_preconditions": [atom_record(a, "pre") for a in p.get("requires", [])],
            "extra_postconditions": [atom_record(a, "post") for a in p.get("ensures", [])],
            "chain": [step_text(st) for st in p["steps"]],
            "policies": sorted({x for x in _policies(p["steps"])}),
            "note": p.get("note", ""),
        })
    pre_txt = [atom_record(a, "pre")["predicate"] for a in rec["requires"]]
    alt = [(pp["path_id"], pp["when"], [x["predicate"] for x in pp["extra_preconditions"]]) for pp in paths]
    gated = [a for a in alt if a[2]]
    summary = ("Always applicable." if not pre_txt and not gated else
               ("Requires " + "; ".join(pre_txt) + "." if pre_txt else "No skill-level precondition."))
    if gated:
        summary += " Depending on the bound nouns, the chosen path also needs: " + "; ".join(
            f"{pid} ({' and '.join(w)}): {', '.join(x)}" for pid, w, x in gated) + "."
    verifier = ([dict(atom_record(a, "post"), scope="all paths") for a in rec["ensures"]] +
                [dict(x, scope=f"path {pp['path_id']}") for pp in paths for x in pp["extra_postconditions"]])
    example_args = {k: ({"ref": f"<{m['type'].replace('_ref', '')}>"} if m["type"].endswith("_ref") or
                        m["type"] == "place_ref" else {"value": m.get("default", f"<{m['type']}>")})
                    for k, m in rec["inputs"].items() if m["required"]}
    return {
        "schema_version": 2, "kind": "skill_node",
        "skill_id": rec["skill_id"], "name": f"{rec['verb']}-{rec['noun']}", "verb": rec["verb"], "noun": rec["noun"],
        "title": rec["title"], "group": rec["group"],
        "signature": f"{rec['verb']}({sig})",
        "action_predicate": {"name": f"{rec['verb']}_{rec['noun']}", "verb": rec["verb"], "noun": rec["noun"],
                             "arguments": list(rec["inputs"])},
        "description": rec["description"], "use_when": rec["use_when"],
        "not_to_be_confused_with": rec["distinct_from"],
        "inputs": rec["inputs"], "required_inputs": required, "outputs": rec["outputs"],
        "applicability": {"always": not pre_txt and not gated, "summary": summary},
        "preconditions": [atom_record(a, "pre") for a in rec["requires"]],
        "postconditions": [atom_record(a, "post") for a in rec["ensures"]],
        "verifier": {"how": "after the policy chain, every listed predicate is evaluated on ground-truth simulator "
                            "state (object poses, joint values, finger gaps, head-camera geometry, thermal state, "
                            "event log); the node succeeds only if all hold for the selected path",
                     "checks": verifier},
        "invalidates": rec["invalidates"],
        "policy_paths": paths,
        "relations": rels,
        "failure": {"codes": ["INPUT_MISSING", "NOUN_INVALID", "PRECONDITION_FAILED", "NO_PATH", "POLICY_FAILED",
                              "SUBSKILL_FAILED", "POSTCONDITION_FAILED"],
                    "on_failure": "stop; return every measured predicate, the completed policy steps and the "
                                  "fallback skills whose repaired predicate failed; the planner chooses what to do. "
                                  "Inside a multi-object node a nested call that fails a precondition with a matching "
                                  "repair fallback runs that repair once and retries.",
                    "typical": rec["failure_modes"]},
        "scope": rec["scope"],
        "contract_id": rec["contract_id"],
        "invocation": {"skill_subgraph_node": {"id": "n1", "skill_id": rec["skill_id"], "args": example_args,
                                               "depends_on": []},
                       "python": f"SkillContractRunner(rig).run(\"{rec['verb']}\", {{{', '.join(repr(k) + ': ...' for k in required)}}})"},
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
        "contract_id": rec["contract_id"], "skill_id": rec["skill_id"], "verb": rec["verb"], "noun": rec["noun"],
        "name": rec["title"], "description": rec["description"], "group": rec["group"],
        "inputs": rec["inputs"], "outputs": rec["outputs"],
        "requires": rec["requires"], "ensures": rec["ensures"], "invalidates": rec["invalidates"],
        "precheck": precheck, "verifier": verifier,
        "noun_binding": {slot: {"type": m["type"], "attributes_from": "zeno_skills.skill_runtime.bind_nouns (GT)"}
                         for slot, m in rec["inputs"].items() if m["type"].endswith("_ref")},
        "action_predicate": {"name": f"{rec['verb']}_{rec['noun']}", "verb": rec["verb"], "noun": rec["noun"],
                             "arguments": list(rec["inputs"])},
        "policy_plan": rec["policy_plan"],
        "relations": rec["relations"],
        "failure": {"automatic_fallback": "nested calls only: a failed precondition with a matching repair "
                                          "fallback runs the repair once and retries; top-level calls stop",
                    "stop_and_report": True},
        "scope": rec["scope"],
    }


def skill_md(js):
    L = ["---", f"name: {js['name']}", f"description: {js['description']}", "---", "",
         f"# {js['title']} (`{js['skill_id']}`)", "", f"`{js['signature']}`", "", js["description"], ""]
    if js["use_when"]:
        L += ["## When to use", "", js["use_when"], ""]
    if js["not_to_be_confused_with"]:
        L += ["## Not to be confused with", ""] + [f"- `{k}`: {v}" for k, v in js["not_to_be_confused_with"].items()] + [""]
    L += ["## Inputs", ""] + [f"- `{k}` (`{m['type']}`{'' if m['required'] else ', optional'}"
                              f"{', default ' + repr(m['default']) if 'default' in m else ''}): {m['description']}"
                              for k, m in js["inputs"].items()] + ([""] if js["inputs"] else ["- none", ""])
    if js["outputs"]:
        L += ["## Outputs", ""] + [f"- `{k}` (`{m['type']}`): {m['description']}" for k, m in js["outputs"].items()] + [""]
    L += ["## Applicability", "", js["applicability"]["summary"], ""]
    L += ["## Preconditions (checked on live GT state before moving)", ""]
    L += [f"- `{p['predicate']}` — {p['meaning']} GT: {', '.join(p['gt_sources'])}." for p in js["preconditions"]] or ["- none"]
    L += ["", "## Postconditions (verified on live GT state)", ""]
    L += [f"- `{p['predicate']}` — {p['meaning']} GT: {', '.join(p['gt_sources'])}." for p in js["postconditions"]]
    L += ["", "## Verifier", "", js["verifier"]["how"] + ":", ""]
    L += [f"- `{c['predicate']}` ({c['scope']})" for c in js["verifier"]["checks"]]
    if js["invalidates"]:
        L += ["", "## May invalidate", "", ", ".join(f"`{x}`" for x in js["invalidates"])]
    L += ["", "## Policy paths (first match on the bound nouns)", ""]
    for p in js["policy_paths"]:
        L.append(f"### `{p['path_id']}` — when {' and '.join(p['when'])}")
        L.append("")
        L += [f"{i + 1}. `{c}`" for i, c in enumerate(p["chain"])]
        for a in p["extra_preconditions"]:
            L.append(f"- extra precondition `{a['predicate']}`")
        for a in p["extra_postconditions"]:
            L.append(f"- extra postcondition `{a['predicate']}`")
        if p["note"]:
            L.append(f"- {p['note']}")
        L.append("")
    L += ["## Relations", ""]
    for key, title in (("previous", "Previous step"), ("next", "Next step"), ("fallback", "Fallback on failure"),
                       ("fallback_for", "Is a fallback for"), ("alternative", "Alternative")):
        for r in js["relations"][key]:
            extra = f" ({r['type']}{', repairs ' + r['repairs'] if r.get('repairs') else ''})" if r.get("type") else ""
            L.append(f"- {title}: `{r['verb']}` (`{r['skill_id']}`){extra} — {r['when']}")
    L += ["", "## Failure", "", "Stop and report the measured predicates, completed policy steps and matching "
          "fallback skills. Nothing is retried automatically.", ""]
    L += [f"- {f}" for f in js["failure"]["typical"]]
    L += ["", f"Paired Contract: `{js['contract_id']}`.", ""]
    return "\n".join(L)


def contract_md(cj):
    L = [f"# {cj['contract_id']} — {cj['name']}", "", cj["description"], "",
         f"Paired SkillNode: `{cj['skill_id']}` (`{cj['verb']}-{cj['noun']}`).", "", "## Precheck", ""]
    L += [f"- [{p['scope']}] `{p['predicate']}` — GT: {', '.join(p['gt_sources'])}" for p in cj["precheck"]] or ["- none"]
    L += ["", "## Verifier", ""]
    L += [f"- [{p['scope']}] `{p['predicate']}` — GT: {', '.join(p['gt_sources'])}" for p in cj["verifier"]]
    L += ["", "## Policy paths", ""]
    for p in cj["policy_plan"]["paths"]:
        L.append(f"- `{p['path_id']}` when {' and '.join(cond_text(c) for c in p['when']) or 'always'}: "
                 + " -> ".join(f"`{step_text(s)}`" for s in p["steps"]))
    L += ["", "Runtime: `zeno_skills.skill_runtime.SkillContractRunner`.", ""]
    return "\n".join(L)


def skills_table(records):
    L = ["# Verb-based SkillNodes", "",
         "Generated by `tools/build_skill_library.py` from `skill_library/definitions.py`; do not edit by hand.", "",
         "| SkillNode | Verb + noun | Signature | Paths (noun-selected) | Postconditions |", "|---|---|---|---|---|"]
    for r in records:
        sig = ", ".join(f"{k}{'' if m['required'] else '?'}" for k, m in r["inputs"].items())
        post = ", ".join(f"`{a['pred']}`" for a in r["ensures"]) or "path-specific"
        extra = {a["pred"] for p in r["paths"] for a in p.get("ensures", [])}
        if extra:
            post += " + " + ", ".join(f"`{x}`" for x in sorted(extra))
        L.append(f"| `{r['skill_id']}` | **{r['verb']}** {r['noun']} | `{r['verb']}({sig})` | "
                 f"{', '.join(p['path_id'] for p in r['paths'])} | {post} |")
    return "\n".join(L) + "\n"


def coverage_md(records, names):
    used = {}
    for r in records:
        for p in r["paths"]:
            for pid in _policies(p["steps"]):
                used.setdefault(pid, []).append(f"{r['verb']}/{p['path_id']}")
    L = ["# Policy coverage by SkillNode paths", "",
         "Generated by `tools/build_skill_library.py`. Every public policy is reached by at least one "
         "noun-selected path, except retired policies (listed with the measured reason).", "", "| Policy | Name | Used by (skill/path) |", "|---|---|---|"]
    from skill_library.check import RETIRED_POLICIES
    for pid in sorted(names):
        where = used.get(pid) or ([f"retired: {RETIRED_POLICIES[pid]}"] if pid in RETIRED_POLICIES else ["**unused**"])
        L.append(f"| `{pid}` | `{names[pid]}` | {', '.join(where)} |")
    return "\n".join(L) + "\n"


def build():
    records, by_verb, names = compile_records()
    errors = check_library(records)
    incoming = {}
    for r in records:
        for rel in r["relations"]:
            incoming.setdefault(rel["to"], []).append((r, rel))
    files = {}
    skills_js = []
    for r in records:
        js = skill_json(r, by_verb, names, incoming)
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
        "how_to_use": "Plan with these SkillNodes. Each node is one verb + one noun; fill the typed inputs, "
                      "check the preconditions you can see, and chain nodes through their relations. The executor "
                      "verifies every pre/postcondition on ground-truth simulator state and returns measured facts "
                      "and fallback candidates on failure.",
        "predicates": {n: {"args": [list(a) for a in p.args], "kind": p.kind, "meaning": p.doc,
                           "gt_sources": GT_SOURCES[n]} for n, p in sorted(REGISTRY.items())},
        "skills": skills_js})
    files[Path("skill_library/catalog.json")] = _json({
        "schema_version": 2, "kind": "skill_catalog",
        "skills": [{"skill_id": r["skill_id"], "verb": r["verb"], "noun": r["noun"], "contract_id": r["contract_id"],
                    "definition": f"skills/{r['skill_id']}/skill.json"} for r in records]})
    rel_rows = []
    for r in records:
        for rel in r["relations"]:
            rel_rows.append({"id": f"relation_{len(rel_rows) + 1:03d}", "from": r["skill_id"], "from_verb": r["verb"],
                             "to": rel["to_skill_id"], "to_verb": rel["to"], "kind": rel["kind"],
                             **({"fallback_type": rel["fallback_type"]} if rel.get("fallback_type") else {}),
                             **({"sequence_type": rel["sequence_type"]} if rel.get("sequence_type") else {}),
                             **({"repairs": rel["repairs"]} if rel.get("repairs") else {}),
                             "when": rel["when"], "bind": rel["bind"], "automatic": False})
    files[Path("skill_library/relations.json")] = _json({
        "schema_version": 2, "kind": "skill_relations",
        "semantics": {"sequence": "to is a natural next step after from (loose); a postcondition of from matches "
                                  "a precondition of to",
                      "fallback": "when from fails: repair = to establishes a failed precondition, then retry from; "
                                  "substitute = to reaches from's effect another way",
                      "alternative": "same effect by other means"},
        "relations": rel_rows})
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
        "contracts": [{"contract_id": r["contract_id"], "skill_id": r["skill_id"], "verb": r["verb"],
                       "definition": f"contracts/{r['contract_id']}/contract.json"} for r in records],
        "legacy_family_contracts": legacy})
    # public ID table (skill <-> contract <-> verb, policies with legacy aliases)
    ids = json.loads((ROOT / "zeno_skills/interface_ids.json").read_text())
    ids["node_contract_ids"] = {r["skill_id"]: r["contract_id"] for r in records}
    files[Path("zeno_skills/interface_ids.json")] = json.dumps(ids, indent=1) + "\n"
    L = ["# Public IDs", "", "Generated by `tools/build_skill_library.py`. SkillNodes `skill_001`-`skill_"
         f"{len(records):03d}` pair one-to-one with Contracts `contract_{CONTRACT_OFFSET:03d}`-`contract_"
         f"{len(records) + CONTRACT_OFFSET - 1:03d}`. `contract_001`-`contract_008` are the legacy family "
         "Contracts. Policies keep their descriptive names as aliases.", "",
         "## SkillNodes and Contracts", "", "| SkillNode | Verb + noun | Contract |", "|---|---|---|"]
    L += [f"| `{r['skill_id']}` | {r['verb']} {r['noun']} | `{r['contract_id']}` |" for r in records]
    L += ["", "## Legacy family Contracts", "", "| Contract | Legacy name |", "|---|---|"]
    L += [f"| `{pub}` | `{leg}` |" for leg, pub in sorted(ids["contract_ids"].items(), key=lambda kv: kv[1])]
    L += ["", "## Policies", "", "| Policy | Alias (PolicySuite attribute) |", "|---|---|"]
    L += [f"| `{pub}` | `{leg}` |" for leg, pub in sorted(ids["policy_ids"].items(), key=lambda kv: kv[1])]
    files[Path("docs/INTERFACE_IDS.md")] = "\n".join(L) + "\n"
    # counts + verb table injected into skill_library/README.md
    from collections import Counter
    kinds = Counter((r["kind"], r.get("sequence_type") or r.get("fallback_type") or "") for r in rel_rows)
    n_paths = sum(len(r["paths"]) for r in records)
    n_tasks = len(json.loads((ROOT / "skill_library/tasks.json").read_text())["tasks"])
    counts = (f"**{len(records)} 个 SkillNode**（`skill_001`–`skill_{len(records):03d}`，{len(records)} 个不同动词）"
              f"一一对应 **{len(records)} 个 Contract**（`contract_{CONTRACT_OFFSET:03d}`–`contract_"
              f"{len(records) + CONTRACT_OFFSET - 1:03d}`），共 **{n_paths} 条按名词选择的 policy 路径**，"
              f"覆盖 **{len(names) - len(RETIRED_POLICIES)}/{len(names)} 个底层 policy**"
              f"（{len(RETIRED_POLICIES)} 个因物理上不可行而退役，原因见 [POLICY_COVERAGE.md](../policy_library/POLICY_COVERAGE.md)）；"
              f"前后条件来自 **{len(REGISTRY)} 个 GT 谓词**。"
              f"关系图有 {kinds[('sequence', 'enables')]} 条 enables、{kinds[('sequence', 'then')]} 条 then、"
              f"{sum(v for (k, _), v in kinds.items() if k == 'fallback')} 条 fallback "
              f"（repair {kinds[('fallback', 'repair')]}、recover {kinds[('fallback', 'recover')]}、"
              f"substitute {kinds[('fallback', 'substitute')]}）和 {kinds[('alternative', '')]} 条 alternative。"
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
    lib = [f"**{len(records)} 个动词 SkillNode**，一一对应 {len(records)} 个 Contract，共 {n_paths} 条按名词选择的 policy 路径，"
           f"覆盖 {len(names) - len(RETIRED_POLICIES)}/{len(names)} 个底层 policy（退役 {len(RETIRED_POLICIES)} 个，"
           f"见 [POLICY_COVERAGE.md](policy_library/POLICY_COVERAGE.md)）；前后条件来自 {len(REGISTRY)} 个 GT 谓词；关系图有 "
           f"{kinds[('sequence', 'enables')] + kinds[('sequence', 'then')]} 条上一步/下一步、"
           f"{sum(v for (k, _), v in kinds.items() if k == 'fallback')} 条 fallback、{kinds[('alternative', '')]} 条 alternative。", "",
           "| 类别 | 动词 |", "|---|---|"]
    lib += [f"| {gtitle.get(g, g)} | {', '.join(f'`{v}`' for v in vs)} |" for g, vs in groups.items()]
    files[Path("README.md")] = _inject((ROOT / "README.md").read_text(), "library", "\n".join(lib))
    n_policy = len(names)
    n_planner = sum(1 for leg in names.values() if leg.startswith("plan_"))
    files[Path("contract_library/README.md")] = _inject(
        (ROOT / "contract_library/README.md").read_text(), "counts",
        f"当前有 **{len(records)} 个 Skill Contract**（`contract_{CONTRACT_OFFSET:03d}`–`contract_"
        f"{len(records) + CONTRACT_OFFSET - 1:03d}`），与 `skill_001`–`skill_{len(records):03d}` 一一对应，"
        f"共 {n_paths} 条 policy 路径。")
    files[Path("policy_library/README.md")] = _inject(
        (ROOT / "policy_library/README.md").read_text(), "counts",
        f"当前有 **{n_policy} 个公开 policy**（`policy_001`–`policy_{n_policy:03d}`），其中 {n_planner} 个是只计算目标、"
        f"不运动的规划 policy；全部被 {len(records)} 个 Skill Contract 的路径覆盖。")
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
