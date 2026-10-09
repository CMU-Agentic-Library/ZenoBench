"""Write the whole-task rollout section of the README from rollout results.

    python tools/rollout_summary.py runs/skillv2/rollouts [runs/skillv2/rollouts2 ...]

A rollout runs a planner skill subgraph (skill_library/plans/) end to end in
Isaac Sim and checks the task goal on GT state.  Passing rollouts need a
converted video in media/rollouts/<id>.gif (tools/make_media.py).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    roots = [Path(a) for a in sys.argv[1:]] or [ROOT / "runs/skillv2/rollouts"]
    results = {}
    for r in roots:                        # later roots (reruns) override earlier ones
        for f in sorted(r.glob("*/result.json")):
            d = json.loads(f.read_text())
            results[d["id"]] = d
    spec = json.loads((ROOT / "skill_library/verification/task_rollouts.json").read_text())["scenarios"]
    rows, gallery, n_pass = [], [], 0
    for s in spec:
        r = results.get(s["id"])
        if r is None:
            rows.append(f"| `{s['id'][5:]}` | {len(s.get('chain', []))} | not run | |")
            continue
        steps = r.get("steps", [])
        ok = bool(r.get("success"))
        n_pass += ok
        done = sum(1 for x in steps if x.get("success"))
        if ok:
            note = "goal " + ", ".join(g["atom"] for g in r.get("goal", [])) if r.get("goal") else ""
            gif = ROOT / "media/rollouts" / f"{s['id']}.gif"
            if gif.exists():
                gallery.append(f"<img src=\"media/rollouts/{s['id']}.gif\" width=\"240\" title=\"{s['id'][5:]}\">")
        else:
            last = steps[-1] if steps else {}
            note = (r.get("crash") or f"{last.get('action', '')}: {last.get('error', '')}")[:140].replace("|", "/")
        rows.append(f"| `{s['id'][5:]}` | {done}/{len(steps)} | {'pass' if ok else 'fail'} | {note} |")
    text = [f"**Whole-task rollouts**: {n_pass}/{len(spec)} planner-generated skill subgraphs ran end to end in Isaac Sim "
            "with their task goal holding on GT state (`tools/verify_skills.py --scenarios "
            "skill_library/verification/task_rollouts.json --video`). Failures are listed with the step that failed.",
            "", " ".join(gallery), "", "| task | steps done | result | goal / failure |", "|---|---|---|---|"] + rows
    block = "\n".join(text)
    readme = ROOT / "README.md"
    s = readme.read_text()
    a, b = "<!-- rollouts:start -->", "<!-- rollouts:end -->"
    if a not in s:
        s = s.replace("<!-- plans:start -->", f"{a}\n{b}\n\n<!-- plans:start -->", 1)
    i, j = s.index(a) + len(a), s.index(b)
    readme.write_text(s[:i] + "\n" + block + "\n" + s[j:])
    print(f"rollouts passed: {n_pass}/{len(spec)}")


if __name__ == "__main__":
    main()
