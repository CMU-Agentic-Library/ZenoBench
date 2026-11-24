"""Paired, local-VLM v6 runs. One process serves a model/method/shard combination."""

import argparse
from collections import defaultdict
from itertools import zip_longest
import json
import os
from pathlib import Path
import subprocess
import time
from urllib.request import urlopen

from baseline.run_http import ROOT, code_version, run_dir, run_one, write_report

V6 = ROOT / "benchmark/v6"
MODELS = {
    "qwen3.5-4b": ("Qwen/Qwen3.5-4B", "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"),
    "qwen3.5-27b": ("Qwen/Qwen3.5-27B", "81a287ca484a5e71148f5beb7f367bb5286d70f9"),
    "internvl3.5-8b": ("OpenGVLab/InternVL3_5-8B-HF", "741a7d03020411e666c6109218ab71e08151ef86"),
}
MAIN = "sticky/benchmark"
METHODS = {
    "OpenLoop": ("baseline.open_loop:OpenLoop", MAIN),
    "ReAct": ("baseline.react:ReAct", MAIN),
    "CodeAsPolicies": ("baseline.code_policy:CodeAsPolicies", MAIN),
    "SayPlan": ("baseline.sayplan:SayPlan", MAIN),
    "GraphManager": ("GraphManager", MAIN),
    "ReActHint": ("baseline.react:ReActHint", MAIN),
    "ReActPrivileged": ("baseline.react:ReAct", "sticky/privileged"),
}
ABLATIONS = ("ReActHint", "ReActPrivileged")
CATEGORIES = ("control", "task", "action", "action_task")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def episodes():
    catalog = {t["task_id"]: t for t in read_json(V6 / "tasks.json")["tasks"]}
    groups = defaultdict(list)
    seen = set()
    for category in CATEGORIES:
        rows = read_json(V6 / "batches" / f"category_{category}.json")
        for row in rows:
            task, variant, seed = row["task"], row["variant"], row["seed"]
            key = task, variant, seed
            if key in seen or row["category"] != category:
                raise ValueError(f"duplicate or mislabelled v6 batch row: {row}")
            seen.add(key)
            task_spec = catalog[task]
            groups[category].append(dict(task=task, variant=variant, seed=seed, category=category,
                                         design=row["v6_variant"],
                                         ideal_present=task_spec["variants"][variant]["scoring"]["ideal_present"],
                                         reference_steps=len(task_spec["routes"][row["route"]]["steps"])))
    # Interleave conditions, then designs within each seed, so the first pass covers the task set.
    for rows in groups.values():
        rows.sort(key=lambda j: (j["seed"], j["design"], j["task"]))
    return [job for row in zip_longest(*(groups[c] for c in CATEGORIES)) for job in row if job]


def representatives(jobs):
    """First declared seed per concrete layout; identical episodes for both ablations and ReAct."""
    first = {}
    for j in sorted(jobs, key=lambda j: j["seed"]):
        first.setdefault((j["task"], j["variant"]), j["seed"])
    return [j for j in jobs if first[j["task"], j["variant"]] == j["seed"]]


def result_path(out, model, method, job):
    policy, profile = METHODS[method]
    return run_dir(Path(out) / profile, policy, model, job)


def graph_library(path):
    from episode.catalog import difficulty_of
    path.mkdir(parents=True, exist_ok=True)
    skills = path / "skills"
    if not skills.exists():
        skills.symlink_to(ROOT / "skill_library/skills", target_is_directory=True)
    doc = read_json(V6 / "tasks.json")
    tasks = [{"task_id": t["task_id"], "catalog": "benchmark/v6/tasks.json", "default_profile": MAIN,
              "variants": {name: difficulty_of(v) for name, v in t["variants"].items()}} for t in doc["tasks"]]
    (path / "tasks.json").write_text(json.dumps({"schema_version": 1, "kind": "task_index", "tasks": tasks}))
    (path / "COMMIT").write_text(code_version()["commit"] + "\n")


def run_graph(args, job, directory, library, patch):
    result_file = directory / "result.json"
    if result_file.is_file():
        return read_json(result_file)
    directory.mkdir(parents=True, exist_ok=True)
    # Each restart retains the pinned planner's raw decisions, subgraphs, tool errors and images.
    attempt = directory / "graph" / str(time.time_ns())
    attempt.mkdir(parents=True)
    (attempt / "workspace").mkdir()
    command = [args.graph_bin, "--task", job["task"], "--variant", job["variant"], "--seed", str(job["seed"]),
               "--env-profile", MAIN, "--env-url", args.server, "--zenobench-root", str(library),
               "--provider", "lab-vlm", "--model", args.model, "--patch", str(patch),
               "--dsh-home", str(args.out / "harness" / args.model),
               "--workspace", str(attempt / "workspace"), "--max-tokens", "4096",
               "--out", str(attempt), "--concurrency", "1"]
    with (attempt / "runner.log").open("w") as f:
        proc = subprocess.run(command, stdout=f, stderr=subprocess.STDOUT,
                              env={**os.environ, "LAB_VLM_API_KEY": "local"})
    path = attempt / job["task"] / MAIN / job["variant"] / f"seed_{job['seed']}" / "result.json"
    raw = read_json(path) if path.exists() else {}
    record = {"task_id": job["task"], "variant": job["variant"], "seed": job["seed"], "model": args.model,
              "policy": "GraphManager", "profile": MAIN, "graph_attempt": str(attempt)}
    if proc.returncode or raw.get("status") not in ("success", "failure"):
        record["crash"] = raw.get("attempts") or f"graph-manager-run exited {proc.returncode}; see {attempt}/runner.log"
        write_report(directory / "failed.json", record)
        return record
    ep = raw["episode"]
    native = read_json(args.native_dir / job["task"] / ep["exp_id"] / "result.json")
    if native["incomplete"] or native["episode_hash"] != ep["env_episode"]["episode_hash"]:
        raise ValueError(f"missing matching native verdict for {ep['exp_id']}")
    record.update(exp_id=ep["exp_id"], max_calls=ep["profile"]["max_calls"], episode=ep["env_episode"],
                  score=native["score"], success=native["task_success"], dropped=native["dropped"],
                  skill_calls=ep["contract_calls"], wall_s=ep["elapsed_s"], stop_reason=ep["reason"],
                  planner_summary={"model_turns": ep["model_turns"], "invalid_replies": ep["invalid_replies"]})
    write_report(result_file, record)
    return record


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", choices=MODELS, required=True)
    ap.add_argument("--method", choices=METHODS, required=True)
    ap.add_argument("--server", required=True)
    ap.add_argument("--vlm-url", required=True, help="local model's OpenAI-compatible /v1 endpoint")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--native-dir", type=Path, required=True, help="env_service --log-dir")
    ap.add_argument("--sim-version", default="5.1.0.0", help="Isaac Sim wheel version of this output root")
    ap.add_argument("--graph-bin", default="graph-manager-run")
    ap.add_argument("--shards", default=1, type=int)
    ap.add_argument("--shard", default=0, type=int, help="zero-based disjoint episode shard")
    args = ap.parse_args()
    if not 0 <= args.shard < args.shards:
        ap.error("--shard must be in [0, --shards)")
    from baseline.base import default_menu
    args.out = args.out.resolve()
    with urlopen(args.vlm_url.rstrip("/") + "/models", timeout=30) as response:
        served = [m["id"] for m in json.load(response)["data"]]
    if args.model not in served:
        raise ValueError(f"{args.vlm_url} serves {served}, expected {args.model}")
    os.environ.update(SHIFT_MODEL=args.model, SHIFT_VLLM_URL=args.vlm_url, SHIFT_QWEN_THINKING="0",
                      SHIFT_VLLM_TEMPERATURE="0", SHIFT_VLLM_MAX_TOKENS="4096")
    settings = args.out / "protocol" / args.model / args.method / f"{args.shard}-of-{args.shards}"
    settings.mkdir(parents=True, exist_ok=True)
    config = {"commit": code_version()["commit"], "model": args.model, "weights": MODELS[args.model][0],
              "revision": MODELS[args.model][1], "method": args.method, "profile": METHODS[args.method][1],
              "max_calls": 60, "temperature": 0, "max_tokens": 4096, "qwen_thinking": False,
              "isaacsim": args.sim_version}
    meta = settings / "protocol.json"
    if meta.exists() and read_json(meta) != config:
        raise ValueError(f"changed protocol in {settings}; start a new output root")
    write_report(meta, config)
    menu = default_menu()
    jobs = episodes()
    if args.method in ABLATIONS:
        jobs = representatives(jobs)
    jobs = jobs[args.shard::args.shards]
    library, patch = settings / "library", settings / "local-model.patch.yml"
    if args.method == "GraphManager":
        graph_library(library)
        template = (ROOT / "baseline/graph_manager/examples/harness-local-vlm.patch.yml").read_text()
        patch.write_text(template.replace("http://127.0.0.1:8001/v1", args.vlm_url).replace("qwen3.5-4b", args.model))
    policy, profile = METHODS[args.method]
    for job in jobs:
        if args.method == "GraphManager":
            report = run_graph(args, job, result_path(args.out, args.model, args.method, job), library, patch)
        else:
            report = run_one(args.server, job, policy, profile, args.out / profile, args.model, menu)
        if report.get("crash") or report.get("check_error"):
            raise RuntimeError(f"episode interrupted: {job}: {report.get('crash') or report['check_error']}")
        ep = report["episode"]
        if ep["runtime"]["isaacsim"] != args.sim_version:
            raise ValueError(f"expected Isaac Sim {args.sim_version}, received {ep['runtime']}")
        if (ep["task_id"], ep["variant"], ep["seed"], ep["profile"], report["max_calls"]) != (
                job["task"], job["variant"], job["seed"], profile, 60):
            raise ValueError(f"episode or budget mismatch: {job}")


if __name__ == "__main__":
    main()
