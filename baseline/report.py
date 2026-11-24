"""Summarize the local v6 comparison from paired planner and native simulator receipts."""

import argparse
from collections import defaultdict
from pathlib import Path
import random
from statistics import mean

from baseline.comparison import ABLATIONS, METHODS, MODELS, episodes, read_json, representatives, result_path
from benchmark.metrics import failure_class


def episode_key(j):
    return j["task"], j["variant"], j["seed"]


def read_outcome(directory, native_dir, model, method, job):
    final = directory / "result.json"
    if not final.exists():
        return ("interrupted" if (directory / "failed.json").exists() else "outstanding"), None
    r = read_json(final)
    if r.get("crash") or r.get("check_error"):
        return "interrupted", None
    identity = job["task"], job["variant"], job["seed"], METHODS[method][1]
    if (r["task_id"], r["variant"], r["seed"], r["profile"]) != identity or (
            r["model"], r["policy"], r["max_calls"]) != (model, METHODS[method][0], 60):
        raise ValueError(f"planner result identity mismatch in {final}")
    native_path = native_dir / job["task"] / r["exp_id"] / "result.json"
    n = read_json(native_path)
    if n["incomplete"] or (n["task_id"], n["variant"], n["seed"], n["profile"]) != identity or (
            n["exp_id"], n["episode_hash"], n["score"], n["task_success"]) != (
            r["exp_id"], r["episode"]["episode_hash"], r["score"], r["success"]):
        raise ValueError(f"native verdict mismatch between {final} and {native_path}")
    if n["skill_calls"] != len(n["calls"]):
        raise ValueError(f"native skill count mismatch in {native_path}")
    execution = any(failure_class(c["eval"].get("leaf_code")) == "execution" for c in n["calls"])
    summary = r["planner_summary"]
    return "scored", {**job, "exp_id": r["exp_id"], "config_hash": r["episode"]["config_hash"],
                      "episode_hash": n["episode_hash"], "score": n["score"]["score"],
                      "success": n["task_success"], "execution": execution, "skills": n["skill_calls"],
                      "queries": summary.get("vlm_queries"), "input_tokens": summary.get("input_tokens"),
                      "output_tokens": summary.get("output_tokens"), "wall_s": r["wall_s"]}


def clustered_interval(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r["task"], r["design"]].append(r["score"])
    if len(groups) < 2:
        return None
    sums = [(sum(scores), len(scores)) for scores in groups.values()]
    rng = random.Random(20261124)
    estimates = []
    for _ in range(2000):
        sample = rng.choices(sums, k=len(sums))
        estimates.append(sum(s for s, _ in sample) / sum(n for _, n in sample))
    estimates.sort()
    return estimates[49], estimates[1949]


def table(header, data):
    lines = [header, ["---"] * len(header), *data]
    return ["| " + " | ".join(str(value) for value in row) + " |" for row in lines] + [""]


def ratio(rows, field):
    return f"{sum(r[field] for r in rows)}/{len(rows)}" if rows else "—"


def average(rows, field, places=2):
    values = [r[field] for r in rows if r[field] is not None]
    return f"{mean(values):.{places}f}" if values else "—"


def mean_and_n(rows):
    return f"{mean(r['score'] for r in rows):.3f} ({len(rows)})" if rows else "—"


def build_report(out, native_dir):
    jobs = episodes()
    subset = representatives(jobs)
    lines = ["# ZenoBench v6 本地 VLM 基线", "",
             "主实验按公开 v6 批次覆盖 30 个任务、151 个设计、316 种布局，种子 10–19。"
             "每个方法和模型运行相同的 1,510 局，技能调用上限为 60。"
             "消融在每种布局首次出现的种子上运行，共 316 局，并与相同种子的 ReAct 配对。", "",
             "计分需要规划器和 Isaac Sim 同时记录相同的任务、种子、episode hash 和最终判定。"
             "实际成功率使用环境的最终 success，得分大于零和满分率另列。"
             "仿真记录中的掉落规则可能使实际成功率低于正分率。", "",
             "## 主实验", ""]
    main_rows, ablation_rows, traces, slices, paired_ablation = [], [], [], [], []
    scores = {}
    for method in METHODS:
        expected = subset if method in ABLATIONS else jobs
        for model in MODELS:
            rows = {}
            interrupted = 0
            for j in expected:
                status, r = read_outcome(result_path(out, model, method, j), native_dir, model, method, j)
                if r is not None:
                    rows[episode_key(j)] = r
                interrupted += status == "interrupted"
            scores[method, model] = rows
            values = list(rows.values())
            ci = clustered_interval(values) if len(values) == len(expected) else None
            result = [method, model, f"{len(values)}/{len(expected)}", interrupted, average(values, "score", 3),
                      f"[{ci[0]:.3f}, {ci[1]:.3f}]" if ci else "—", ratio(values, "success"),
                      f"{sum(r['score'] > 0 for r in values)}/{len(values)}" if values else "—",
                      f"{sum(r['score'] == 1 for r in values)}/{len(values)}" if values else "—"]
            (ablation_rows if method in ABLATIONS else main_rows).append(result)
            traces.append([method, model, ratio(values, "execution"), average(values, "skills"),
                           average(values, "queries"), average(values, "input_tokens", 0),
                           average(values, "output_tokens", 0), average(values, "wall_s", 1)])
    header = ["方法", "模型", "已计分/计划", "中断待重跑", "平均分", "平均分 95% CI", "任务成功", "正分", "满分"]
    lines += table(header, main_rows)
    lines += ["置信区间按任务内的设计聚类，重采样 2,000 次。只有全量覆盖的行给出区间。", "",
              "## 按任务条件配对", "",
              "每种方法取三个模型都已计分的相同任务、布局和种子。单元格给出平均分及括号中的配对局数。"
              "前三列按任务类别划分，后两列按该布局的理想选择是否可用划分。", ""]
    for method in METHODS:
        if method in ABLATIONS:
            continue
        paired = set.intersection(*(set(scores[method, model]) for model in MODELS))
        for key in paired:
            if len({scores[method, m][key]["episode_hash"] for m in MODELS}) != 1:
                raise ValueError(f"paired episode hash mismatch in {method} {key}")
        for model in MODELS:
            vals = [scores[method, model][key] for key in sorted(paired)]
            slices.append([method, model, *(mean_and_n([r for r in vals if r["category"] == c])
                                           for c in ("control", "task", "action_task")),
                           *(mean_and_n([r for r in vals if r["ideal_present"] == present])
                             for present in (True, False))])
    lines += table(["方法", "模型", "Control", "Task", "Action + Task", "理想选择可用", "理想选择不可用"], slices)
    lines += ["## 提示和观测消融", ""] + table(header, ablation_rows)
    for method in ABLATIONS:
        for model in MODELS:
            base, alt = scores["ReAct", model], scores[method, model]
            keys = sorted(base.keys() & alt.keys())
            for key in keys:
                if base[key]["config_hash"] != alt[key]["config_hash"]:
                    raise ValueError(f"ablation layout mismatch in {model} {key}")
            paired_ablation.append([method, model, len(keys), mean_and_n([base[k] for k in keys]),
                                    mean_and_n([alt[k] for k in keys]),
                                    f"{mean(alt[k]['score'] - base[k]['score'] for k in keys):+.3f}" if keys else "—"])
    lines += table(["消融", "模型", "配对数", "ReAct 平均分", "消融平均分", "差值"], paired_ablation)
    lines += ["## 执行与推理成本", "",
              "执行错误列统计至少一个技能叶节点被仓库归类为 execution 的局数，含后来恢复成功的局。"
              "同一局可能同时发生动作选择错误和执行错误。Graph Manager 的一个 Harness 回合可以向模型发多次请求，"
              "其日志未给出可比的后端请求数和 token 数。", ""]
    lines += table(["方法", "模型", "出现执行错误/已计分", "技能调用/局", "模型查询/局",
                    "输入 token/局", "输出 token/局", "秒/局"], traces)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, type=Path, help="comparison output root")
    ap.add_argument("--native-dir", required=True, type=Path, help="env_service --log-dir")
    ap.add_argument("--markdown", required=True, type=Path)
    args = ap.parse_args()
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(build_report(args.out, args.native_dir), encoding="utf-8")


if __name__ == "__main__":
    main()
