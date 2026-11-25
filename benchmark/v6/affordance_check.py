"""Compare the hand-written tiers of tasks.json with the affordance registry (object_registry.py).

For every role of registry/roles.yaml and every layout it covers: what each stand-in scores by hand (the first
tier whose goal places it in the role's slot) against its registry level.  Findings:

  illegal_scored   scored by hand, but the registry finds it illegal (lacks an affordance, does not fit or cover)
  order            ranked against the registry: a higher level scores lower by hand
  unscored_legal   legal and free in the layout, but no tier accepts it (a candidate for widening; not applied)
  specific_partial a named-thing role still gives another thing partial credit (recorded, by design)
  appliance        the best tier keeps a dish away from an appliance it may go into, or allows one it may not

and whether loosen_1124's hand tables (SUBSTITUTE_KINDS, PLACES, ATOM_ALTERNATIVES) are all legal by the
registry.  Writes AFFORDANCE_CHECK.json and AFFORDANCE_CHECK_zh.md; ``--check`` fails when they are stale.

    python benchmark/v6/affordance_check.py [--check]
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from benchmark.v6 import loosen_1124 as L                     # noqa: E402
from benchmark.v6 import object_registry as R                 # noqa: E402

HERE = Path(__file__).resolve().parent
OUT_JSON = HERE / "AFFORDANCE_CHECK.json"
OUT_MD = HERE / "AFFORDANCE_CHECK_zh.md"
LEVEL_ZH = {0: "不合法", 1: "合法但被占用"}


# -- goals and slots -----------------------------------------------------------------------------------------
def tier_goals(v: dict, lid: str) -> list:
    """[(score, goal)] of a layout's tiers, each goal resolved to the {"all", "any"} form."""
    out = []
    base = v.get("goal")
    for tr in (v.get("scoring") or {}).get("tiers", []):
        g = tr.get("goal")
        if g is None:
            g = base
        elif isinstance(g, dict) and "by_layout" in g:
            g = g["by_layout"].get(lid)
        elif isinstance(g, dict) and "drop" in g:
            g = {"all": [a for b in L._branches(base) for a in b if a[0] not in g["drop"]]} if base else None
        if isinstance(g, dict):
            out.append((tr["score"], g))
    return out


def match(pat: list, atom: list) -> list | None:
    if len(pat) != len(atom) or pat[0] != atom[0]:
        return None
    got = []
    for p, a in zip(pat[1:], atom[1:]):
        if p == "?":
            got += [a] if isinstance(a, str) else [x for x in a if isinstance(x, str)] if isinstance(a, list) else []
        elif p != "*" and p != a:
            return None
    return got


def captures(role: dict, v: dict, lid: str) -> dict:
    """name -> best hand score among the tiers that place it in one of the role's slots."""
    out = {}
    for score, g in tier_goals(v, lid):
        for b in L._branches(g):
            for a in b:
                for pat in role["slot"]:
                    for n in match(pat, a) or []:
                        out[n] = max(out.get(n, 0.0), score)
    return out


def excluded(role: dict, name: str, objs: dict) -> bool:
    for e in role.get("exclude", []):
        if e == name or (e.startswith("kind:") and objs.get(name, {}).get("kind") == e[5:]):
            return True
    return False


# -- one layout ----------------------------------------------------------------------------------------------
def check_layout(role: dict, t: dict, v: dict, lid: str, design: str) -> dict | None:
    objs = R.layout_objects(t, v)
    got = captures(role, v, lid)
    rec = {"task": t["task_id"][:3], "design": design, "layout": lid,
           "ideal_present": (v.get("scoring") or {}).get("ideal_present", True), "items": [], "proposals": [],
           "flags": []}
    kind = role["kind"]
    if kind == "appliance":
        return _check_appliance(role, v, lid, rec, objs)
    names = [n for n in got if not excluded(role, n, objs)
             and (n in objs if kind in ("object", "specific") else n in R.surfaces())]
    if not names:
        return None
    for n in names:
        if kind == "place":
            lvl, why = R.assess_place(role, n, lid)
            k = R.surface(n)["taxonomy"]["subcategory"]
        else:
            lvl, why = R.assess_object(role, n, objs) if kind == "object" else (IDEAL_OR(role, n, objs), [])
            k = objs[n]["kind"]
        rec["items"].append({"name": n, "kind": k, "score": got[n], "level": lvl, "why": why})
    items = rec["items"]
    if kind == "specific":
        top = max(i["score"] for i in items)
        rec["flags"] += [{"type": "specific_partial", "name": i["name"], "score": i["score"]}
                         for i in items if 0 < i["score"] < top]
        return rec
    rec["flags"] += [{"type": "illegal_scored", "name": i["name"], "score": i["score"], "why": i["why"]}
                     for i in items if i["level"] == 0 and i["score"] > 0]
    for x in items:
        for y in items:
            if x["level"] > y["level"] and x["score"] < y["score"] and x["level"] > 0:
                rec["flags"].append({"type": "order", "higher": x["name"], "higher_level": x["level"],
                                     "higher_score": x["score"], "lower": y["name"], "lower_level": y["level"],
                                     "lower_score": y["score"]})
    if kind == "object":
        pool = [n for n in objs if n not in got and not excluded(role, n, objs)]
        for n in sorted(pool):
            lvl, why = R.assess_object(role, n, objs)
            if lvl >= 2:
                rec["proposals"].append({"name": n, "kind": objs[n]["kind"], "level": lvl, "why": why})
    else:
        for n in sorted(R.surfaces()):
            if n not in got:
                lvl, why = R.assess_place(role, n, lid)
                if lvl >= 2:
                    rec["proposals"].append({"name": n, "kind": R.surface(n)["taxonomy"]["subcategory"],
                                             "level": lvl, "why": why})
    return rec


def IDEAL_OR(role: dict, name: str, objs: dict) -> int:          # noqa: N802 (specific roles: ideal kind or not)
    return R.IDEAL_LEVEL if objs[name]["kind"] in role.get("ideal", []) else 0


def _check_appliance(role: dict, v: dict, lid: str, rec: dict, objs: dict) -> dict | None:
    tiers = tier_goals(v, lid)
    if not tiers:
        return None
    vessel = None
    for _, g in tiers:
        for b in L._branches(g):
            for a in b:
                got = match(role["vessel_slot"], a)
                if got:
                    vessel = got[0]
    if vessel not in objs:
        return None
    vk = objs[vessel]["kind"]
    best = tiers[0][1]
    avoided = {n for b in L._branches(best) for a in b for pat in role["slot"] for n in (match(pat, a) or [])}
    ok = sorted(a for a in R.APPLIANCE_AFFORD if R.appliance_ok(a, vk))
    for a in sorted(R.APPLIANCE_AFFORD):
        lvl = R.IDEAL_LEVEL if a in ok else 0
        why = [f"{vk} {'may' if a in ok else 'may not'} go into {a}"]
        rec["items"].append({"name": a, "kind": vk, "score": 0.0 if a in avoided else tiers[0][0],
                             "level": lvl, "why": why})
        if (a in avoided) == (a in ok):
            rec["flags"].append({"type": "appliance", "name": a, "vessel": vessel,
                                 "why": f"best tier {'avoids' if a in avoided else 'allows'} {a}; registry: "
                                        f"{vk} {'may' if a in ok else 'may not'} go in"})
    rec["vessel"] = vessel
    return rec


# -- loosen_1124 tables --------------------------------------------------------------------------------------
def loosen_tables(records: list) -> list:
    """Every stand-in kind, place and storage alternative loosen_1124 adds by hand, judged by the registry."""
    out = []
    tasks = {t["task_id"][:3]: t for t in R.tasks_json()["tasks"]}
    by_role = defaultdict(list)
    for r, rec in records:
        by_role[(rec["task"], r["id"])].append((r, rec))
    for prefix, table in L.SUBSTITUTE_KINDS.items():
        for name, kinds in table.items():
            hits = [(r, rec) for (tk, _), rs in by_role.items() if tk == prefix for r, rec in rs
                    if r["kind"] == "object" and any(i["name"] == name for i in rec["items"])]
            role = hits[0][0] if hits else None
            for k in kinds:
                if role is None:
                    out.append({"table": "SUBSTITUTE_KINDS", "task": prefix, "from": name, "to": k,
                                "ok": None, "why": "no registry role covers this stand-in"})
                    continue
                why = R._legal(role, R.obj(k))
                t = tasks[prefix]
                for _, rec in hits:
                    objs = R.layout_objects(t, t["variants"][rec["layout"]])
                    if role.get("covers") and role["covers"] in objs and not R.covers(k, objs[role["covers"]]["kind"]):
                        why.append(f"does not cover {role['covers']}")
                    if role.get("fits") and role["fits"] in objs and not R.fits(k, objs[role["fits"]]["kind"]):
                        why.append(f"{role['fits']} does not fit")
                out.append({"table": "SUBSTITUTE_KINDS", "task": prefix, "from": name, "to": k, "role": role["id"],
                            "ok": not why, "why": sorted(set(why))})
    def design_of(prefix, key):
        """A loosen key names a design, or one layout of a design: the design."""
        t = tasks[prefix]
        if key == "*" or key in t.get("v6_variants", {}):
            return key
        return next((d for d, info in t["v6_variants"].items() if key in info["layouts"]), key)

    def place_rows(table_name, items):
        for (prefix, key), sups in items:
            design = design_of(prefix, key)
            rs = [r for r in R.roles() if r["kind"] == "place" and prefix in r["tasks"]
                  and ("*" in r["tasks"][prefix] or design == "*" or design in r["tasks"][prefix])]
            for s in sups:
                if not rs:
                    out.append({"table": table_name, "task": prefix, "design": key, "to": s, "ok": None,
                                "why": "no registry role"})
                    continue
                lvl, why = R.assess_place(rs[0], s)
                out.append({"table": table_name, "task": prefix, "design": key, "to": s, "role": rs[0]["id"],
                            "ok": lvl >= 2, "why": [] if lvl >= 2 else why})
    place_rows("PLACES", [((p, d), sorted({x for k, more in m.items() for x in [k, *more]}))
                          for (p, d), m in L.PLACES.items()])
    place_rows("ATOM_ALTERNATIVES", [((p, d), sorted({s for _, alts in pairs for alt in alts for s in alt[2]}))
                                     for (p, d), pairs in L.ATOM_ALTERNATIVES.items()])
    return out


# -- run -----------------------------------------------------------------------------------------------------
def run() -> dict:
    records = []
    for t in R.tasks_json()["tasks"]:
        design_of = {lid: d for d, info in t.get("v6_variants", {}).items() for lid in info["layouts"]}
        for lid, v in t["variants"].items():
            design = design_of.get(lid, lid)
            for role in R.role_for(t["task_id"], design):
                rec = check_layout(role, t, v, lid, design)
                if rec:
                    records.append((role, rec))
    flags = Counter(f["type"] for _, rec in records for f in rec["flags"])
    tables = loosen_tables(records)
    roles_out = []
    for role in R.roles():
        recs = [rec for r, rec in records if r["id"] == role["id"]]
        roles_out.append({"id": role["id"], "kind": role["kind"], "why": role.get("why", ""),
                          "requires": role.get("requires", []), "requires_any": role.get("requires_any", []),
                          "prefer": role.get("prefer", []), "ideal": role.get("ideal", []),
                          "constraints": {k: role[k] for k in ("fits", "covers", "room_of", "near", "taxonomy_any",
                                                              "ideal_unavailable") if k in role},
                          "legal_kinds": R.stand_in_kinds(role, 2) if role["kind"] == "object" else [],
                          "layouts": recs})
    return {"summary": {"objects": len(R.objects_yaml()["objects"]), "surfaces": len(R.surfaces()),
                        "furniture": len({s["furniture"] for s in R.surfaces().values()}),
                        "roles": len(R.roles()), "layouts_checked": len(records),
                        "flags": dict(sorted(flags.items())),
                        "loosen_rows": len(tables), "loosen_illegal": sum(r["ok"] is False for r in tables),
                        "loosen_uncovered": sum(r["ok"] is None for r in tables)},
            "roles": roles_out, "loosen_tables": tables}


# -- report --------------------------------------------------------------------------------------------------
def _lv(n: int) -> str:
    return "理想" if n == R.IDEAL_LEVEL else LEVEL_ZH.get(n, f"合法 {n}")


def render(data: dict) -> str:
    s = data["summary"]
    L_ = ["# 功能可供性对照检查（物体 + 家具注册表 vs 手写 tier）", "",
          "由 `python benchmark/v6/affordance_check.py` 生成，不要手改。注册表在 `benchmark/v6/registry/`，"
          "判定代码在 `benchmark/v6/object_registry.py`，设计说明见 `OBJECT_REGISTRY_zh.md`。", "",
          "等级：0 不合法；1 合法但被占用；2+k 合法且空闲、满足 k 个加分项；10 理想物且空闲。"
          "手工分是该物体（或台面）第一次出现在角色位置上的那个 tier 的分数，0 表示没有 tier 接受它。", "",
          "## 总览", "",
          f"- 物体 {s['objects']} 种，家具 {s['furniture']} 件（支撑面 {s['surfaces']} 个），角色 {s['roles']} 个，"
          f"对照了 {s['layouts_checked']} 个（角色, 布局）。",
          "- 发现：" + ("，".join(f"{k} {v}" for k, v in s["flags"].items()) or "无"),
          f"- loosen_1124 手写表 {s['loosen_rows']} 条：不合法 {s['loosen_illegal']}，没有角色覆盖 {s['loosen_uncovered']}。",
          ""]
    kinds_zh = {"illegal_scored": "手工给了分，但注册表判为不合法（按原标准保留，不改分）", "order": "排序和功能等级相反（按原标准保留）",
                "specific_partial": "点名要的东西，别的东西仍拿部分分（设计如此，记录）",
                "appliance": "加热电器和容器材质不配"}
    for ft, title in kinds_zh.items():
        rows = []
        for r in data["roles"]:
            for rec in r["layouts"]:
                for f in rec["flags"]:
                    if f["type"] != ft:
                        continue
                    if ft == "illegal_scored":
                        rows.append((r["id"], rec["task"], rec["design"], f"{f['name']} 得 {f['score']}：{'; '.join(f['why'])}"))
                    elif ft == "order":
                        rows.append((r["id"], rec["task"], rec["design"],
                                     f"{f['higher']}（{_lv(f['higher_level'])}）得 {f['higher_score']} < "
                                     f"{f['lower']}（{_lv(f['lower_level'])}）得 {f['lower_score']}"))
                    elif ft == "specific_partial":
                        rows.append((r["id"], rec["task"], rec["design"], f"{f['name']} 得 {f['score']}"))
                    else:
                        rows.append((r["id"], rec["task"], rec["design"], f["why"]))
        L_ += [f"## {title}", ""]
        if not rows:
            L_ += ["无。", ""]
            continue
        agg = defaultdict(list)
        for role, task, design, text in rows:
            agg[(role, task, design, text)].append(1)
        L_ += ["| 角色 | 任务 | 设计 | 内容 | 布局数 |", "|---|---|---|---|---:|"]
        L_ += [f"| {a} | {b} | {c} | {d} | {len(n)} |" for (a, b, c, d), n in sorted(agg.items())]
        L_.append("")
    L_ += ["## 合法但没有 tier 接受（只记录，不应用；按原标准）", "",
           "| 角色 | 任务 | 设计 | 候选（等级） | 布局数 |", "|---|---|---|---|---:|"]
    agg = defaultdict(int)
    for r in data["roles"]:
        for rec in r["layouts"]:
            if rec["proposals"]:
                text = ", ".join(f"{p['name']}（{_lv(p['level'])}）" for p in rec["proposals"][:8])
                text += f" 等 {len(rec['proposals'])} 个" if len(rec["proposals"]) > 8 else ""
                agg[(r["id"], rec["task"], rec["design"], text)] += 1
    L_ += [f"| {a} | {b} | {c} | {d} | {n} |" for (a, b, c, d), n in sorted(agg.items())] or ["| 无 | | | | |"]
    L_ += ["", "## loosen_1124 手写表 vs 注册表", "", "| 表 | 任务 | 从 / 设计 | 到 | 角色 | 合法 | 原因 |",
           "|---|---|---|---|---|---|---|"]
    for row in data["loosen_tables"]:
        ok = {True: "是", False: "**否**", None: "无角色"}[row["ok"]]
        why = row["why"] if isinstance(row["why"], str) else "; ".join(row["why"])
        L_.append(f"| {row['table']} | {row['task']} | {row.get('from', row.get('design'))} | {row['to']} | "
                  f"{row.get('role', '')} | {ok} | {why} |")
    L_ += ["", "## 每个角色", "", "| 角色 | 类型 | 必需 | 加分 | 约束 | 理想 | 家里合法的物体种类 | 对照布局数 |",
           "|---|---|---|---|---|---|---|---:|"]
    for r in data["roles"]:
        req = ", ".join(r["requires"]) + ((" 之一：" + "/".join(r["requires_any"])) if r["requires_any"] else "")
        cons = ", ".join(f"{k}={v}" for k, v in r["constraints"].items())
        L_.append(f"| {r['id']} | {r['kind']} | {req} | {', '.join(r['prefer'])} | {cons} | {', '.join(r['ideal'])} | "
                  f"{', '.join(r['legal_kinds'])} | {len(r['layouts'])} |")
    return "\n".join(L_) + "\n"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    data = run()
    js = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    md = render(data)
    if "--check" in argv:
        stale = [p.name for p, x in ((OUT_JSON, js), (OUT_MD, md)) if not p.exists() or p.read_text() != x]
        if stale:
            print("stale:", ", ".join(stale))
            return 1
        print("affordance check up to date")
        return 0
    OUT_JSON.write_text(js)
    OUT_MD.write_text(md)
    print(json.dumps(data["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
