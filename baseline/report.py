"""Summarize the local v6 comparison from paired planner and native simulator receipts."""

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import random
from statistics import mean

from baseline.comparison import ABLATIONS, MAIN, METHODS, MODELS, V6, episodes, read_json, representatives, result_path
from benchmark.metrics import call_records, failure_class


def episode_key(j):
    return j["task"], j["variant"], j["seed"]


def read_outcome(directory, native_dir, model, method, job, sim_version=None):
    final = directory / "result.json"
    if not final.exists():
        return ("interrupted" if (directory / "failed.json").exists() else "outstanding"), None
    r = read_json(final)
    if r.get("crash") or r.get("check_error"):
        return "interrupted", None
    if method == "GraphManager":
        receipt = directory / "graph" / Path(r["graph_attempt"]).name / "local-provider.json"
        if not receipt.is_file():
            return "interrupted", None
        provider = read_json(receipt)
        if (provider["model"], provider["context_window"], provider["max_tokens"]) != (model, 32768, 4096):
            raise ValueError(f"Graph Manager provider configuration mismatch in {receipt}")
    identity = job["task"], job["variant"], job["seed"], METHODS[method][1]
    if (r["task_id"], r["variant"], r["seed"], r["profile"]) != identity or (
            r["model"], r["policy"], r["max_calls"]) != (model, METHODS[method][0], 60):
        raise ValueError(f"planner result identity mismatch in {final}")
    native_path = native_dir / job["task"] / r["exp_id"] / "result.json"
    n = read_json(native_path)
    if sim_version and (n.get("runtime", {}).get("isaacsim") != sim_version or
                        n["runtime"] != r["episode"].get("runtime")):
        raise ValueError(f"simulator version mismatch in {native_path}, expected {sim_version}")
    if n["incomplete"] or (n["task_id"], n["variant"], n["seed"], n["profile"]) != identity or (
            n["exp_id"], n["episode_hash"], n["score"], n["task_success"]) != (
            r["exp_id"], r["episode"]["episode_hash"], r["score"], r["success"]):
        raise ValueError(f"native verdict mismatch between {final} and {native_path}")
    if n["skill_calls"] != len(n["calls"]):
        raise ValueError(f"native skill count mismatch in {native_path}")
    failure_classes = {failure_class(c["eval"].get("leaf_code")) for c in n["calls"]
                       if c["eval"].get("leaf_code") is not None or c.get("feedback", {}).get("success") is False}
    calls = call_records(n, job)
    summary = r["planner_summary"]
    stop_reason = r.get("stop_reason")
    if stop_reason == "planner_done":
        stop_reason = summary.get("stop_reason") or stop_reason
    return "scored", {**job, "exp_id": r["exp_id"], "config_hash": r["episode"]["config_hash"],
                      "episode_hash": n["episode_hash"], "score": n["score"]["score"],
                      "runtime": n.get("runtime", {}),
                      "success": n["task_success"], "best_success": n["task_success"] and n["score"]["tier"] == "best",
                      "execution": "execution" in failure_classes, "failure_classes": failure_classes,
                      "plan_labels": Counter(c["plan"] for c in calls),
                      "valid_execution_failures": sum(c["plan"] == "valid" and c["class"] == "execution" for c in calls),
                      "skills": n["skill_calls"],
                      "queries": summary.get("vlm_queries"), "input_tokens": summary.get("input_tokens"),
                      "output_tokens": summary.get("output_tokens"), "wall_s": r["wall_s"],
                      "stop_reason": stop_reason.partition(":")[0] if stop_reason else "未记录"}


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
    return count_ratio(sum(r[field] for r in rows), len(rows))


def count_ratio(numerator, denominator):
    return f"{numerator}/{denominator}" if denominator else "—"


def average(rows, field, places=2):
    values = [r[field] for r in rows if r[field] is not None]
    return f"{mean(values):.{places}f}" if values else "—"


def mean_and_n(rows):
    return f"{mean(r['score'] for r in rows):.3f} ({len(rows)})" if rows else "—"


def reference_table(directories, scores):
    catalog = {t["task_id"]: t for t in read_json(V6 / "tasks.json")["tasks"]}
    rows = []
    for directory in directories:
        for path in sorted(directory.glob("*/*/result.json")):
            result = read_json(path)
            config = read_json(path.parent / "config.json")
            if result["planner"] != "scripted" or result["profile"] != MAIN:
                raise ValueError(f"expected a scripted {MAIN} reference in {path}")
            task, route = result["task_id"], result["route"]
            expected = len(catalog[task]["routes"][route]["steps"])
            calls = result["calls"]
            failure = next((c for c in calls if c["expect"] == "ok" and not c["feedback"]["success"]), None)
            detail = "—"
            if failure:
                detail = (failure["eval"].get("leaf_error") or failure["feedback"].get("error") or "")
                detail = f"{failure['skill']} · {detail}".replace("|", "\\|").replace("\n", " ")
            code = config["code"]["commit"][:7] + (" +工作树" if config["code"]["dirty_files"] else "")
            score = (result.get("score") or {}).get("score")
            outcome = "中断" if result.get("crash") else ("成功" if result.get("task_success") else "失败")
            key = task, result["variant"], result["seed"]
            matched = []
            for model in MODELS:
                peer = scores["ReAct", model].get(key)
                if peer is None:
                    matched.append("—")
                    continue
                if outcome != "中断" and (peer["episode_hash"], peer["config_hash"]) != (
                        result["episode_hash"], result["config_hash"]):
                    raise ValueError(f"scripted/ReAct episode mismatch in {path} for {model}")
                matched.append(f"{peer['score']:.1f} {'成功' if peer['success'] else '失败'}")
            rows.append([task, result["variant"], result["seed"], code, f"{len(calls)}/{expected}",
                         f"{score:.1f} {outcome}" if score is not None and not result.get("crash") else outcome,
                         *matched, str(result.get("crash") or detail)])
    return ["## 脚本参考路线", "",
            "以下各局在 sticky/benchmark 下执行任务目录预写的动作和真实物体名。"
            "三个模型栏给出同一任务、布局、种子和初始局哈希下标准 ReAct 的原生分数及最终成功判定。"
            "横线表示该模型尚无这局的判定。脚本执行错误列显示第一个本应成功却失败的技能，"
            "一条脚本路线失败时，其他动作序列仍可能可行。脚本局单独计数。", ""] + table(
                ["任务", "布局", "种子", "脚本代码", "脚本已执行/路线步数", "脚本分数与结局",
                 *MODELS, "脚本执行错误"], rows)


def build_report(out, native_dir, sim_version, reference_dirs=()):
    jobs = episodes()
    subset = representatives(jobs)
    lines = [f"# ZenoBench v6 本地 VLM 基线 · Isaac Sim {sim_version}", "",
             ("本表使用仓库指定的 Isaac Sim 5.1。 " if sim_version == "5.1.0.0" else
              f"本表是在 Isaac Sim {sim_version} 上独立运行的版本适配实验。仓库原协议使用 Isaac Sim 5.1。"
              "物理接触、相机渲染以及技能执行结果会受仿真版本影响。"), "",
             "主实验按公开 v6 批次覆盖 30 个任务、151 个设计、316 种布局，种子 10–19。"
             "每个方法和模型计划运行相同的 1,510 局，技能调用上限为 60。"
             "消融在每种布局首次出现的种子上运行，共 316 局，并与相同种子的 ReAct 配对。", "",
             "计分需要规划器和 Isaac Sim 同时记录相同的任务、种子、episode hash 和最终判定。"
             "实际成功率使用环境的最终 success，得分大于零和满分率另列。"
             "仿真记录中的掉落规则可能使实际成功率低于正分率。", "",
             "## 主实验", ""]
    main_rows, ablation_rows, traces, errors, planning, slices, paired_ablation = [], [], [], [], [], [], []
    scores = {}
    for method in METHODS:
        expected = subset if method in ABLATIONS else jobs
        for model in MODELS:
            rows = {}
            interrupted = 0
            for j in expected:
                status, r = read_outcome(result_path(out, model, method, j), native_dir, model, method, j, sim_version)
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
            if values:
                counts = [f"{sum(kind in r['failure_classes'] for r in values)}/{len(values)}"
                          for kind in ("execution", "observation", "precondition", "invalid", "unknown")]
                counts.append(f"{sum(r['skills'] == 0 for r in values)}/{len(values)}")
            else:
                counts = ["—"] * 6
            errors.append([method, model, *counts])
            labels = Counter()
            for row in values:
                labels.update(row["plan_labels"])
            judged = labels["valid"] + labels["invalid"]
            valid_execution_failures = sum(r["valid_execution_failures"] for r in values)
            planning.append([method, model, count_ratio(labels["valid"], judged),
                             count_ratio(judged, sum(labels.values())), labels["undetermined"],
                             count_ratio(valid_execution_failures, labels["valid"])])
            stops = Counter(r["stop_reason"] for r in values)
            traces.append([method, model, average(values, "skills"),
                           average(values, "queries"), average(values, "input_tokens", 0),
                           average(values, "output_tokens", 0), average(values, "wall_s", 1),
                           "，".join(f"`{s}` × {count}" for s, count in stops.most_common()) or "—"])
    header = ["方法", "模型", "已计分/计划", "中断待重跑", "平均分", "平均分 95% CI", "任务成功", "正分", "满分"]
    scored = sum(len(group) for group in scores.values())
    planned = len(MODELS) * (len(jobs) * (len(METHODS) - len(ABLATIONS)) + len(subset) * len(ABLATIONS))
    stacks = {tuple(sorted(row["runtime"].items())) for group in scores.values() for row in group.values()}
    if len(stacks) > 1:
        raise ValueError(f"multiple simulation runtime configurations in one comparison: {stacks}")
    coverage = f"**原生计分覆盖 {scored:,} / {planned:,} 局。**"
    if scored < planned:
        coverage += " 当前为阶段性结果。各行先完成的布局可能不同，跨模型比较请看配对分表。"
    provenance = [coverage, "", f"汇总时间为 {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}。", ""]
    if stacks:
        runtime = dict(next(iter(stacks)))
        if runtime.get("lab_compat_sha256"):
            provenance.extend([f"Isaac Lab 适配清单 SHA-256 为 `{runtime['lab_compat_sha256']}`。"
                               f"cuRobo {runtime.get('nvidia-curobo')}，Warp {runtime.get('warp')}，"
                               f"PyTorch {runtime.get('torch')}（CUDA {runtime.get('torch_cuda')}）。", ""])
    lines[2:2] = provenance
    lines += table(header, main_rows)
    lines += ["置信区间按任务内的设计聚类，重采样 2,000 次。只有全量覆盖的行给出区间。", "",
              "## 按任务条件配对", "",
              "每种方法取三个模型都已计分的相同任务、布局和种子。前三列按任务类别给出平均分和配对局数，"
              "接下来两列按布局中的理想选项是否可用划分。理想选项不可用时，v6 给该布局的最佳替代结果记 1.0 分。"
              "最后一列统计达到这一档且通过环境最终成功检查的局数，分母是理想选项不可用的配对局。", ""]
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
                             for present in (True, False)),
                           ratio([r for r in vals if not r["ideal_present"]], "best_success")])
    lines += table(["方法", "模型", "Control", "Task", "Action + Task", "理想选择可用", "理想选择不可用",
                    "达成布局最佳替代/理想选择不可用"], slices)
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
    lines += ["## 技能调用和错误", "",
              "每格为出现该情况的局数 / 已计分局数。一局可以遇到多类错误，随后仍可能成功。"
              "分类沿用仓库对技能调用最内层错误码的定义，例如 NOT_OBSERVED 归入观测，NO_PATH 归入前置条件，"
              "POLICY_FAILED 归入执行。错误码描述技能的返回状态，判断失败原因还需要结合模型选的参数和当时的场景。", ""]
    lines += table(["方法", "模型", "执行", "观测", "前置条件", "无效调用", "其他错误", "全局零技能调用"], errors)
    lines += ["## 逐次技能调用的规划正确性", "",
              "使用仓库 Planning Correctness 的逐次调用判定。正确率和判定覆盖率均列出分子与分母。"
              "成功执行的调用会判为合理，即使模型交付了错误物体。控制器报错时，接口与前置条件允许的调用也可以判为合理。"
              "最后一列列出在这些合理调用中，仓库归类为底层执行失败的次数。整局是否完成任务见主实验和消融表。", ""]
    lines += table(["方法", "模型", "合理/可判定调用", "可判定/全部调用", "无法判定的调用",
                    "执行失败/合理调用"], planning)
    lines += ["## 推理与执行成本", "",
              "Graph Manager 的一个 Harness 回合可以向模型发多次请求，"
              "其日志未给出可比的后端请求数和 token 数。前四种方法的墙钟耗时包含环境启动和排队，"
              "Graph Manager 从环境就绪起算。物理执行和同机并发都会影响这些时间。", "",
              "停止原因保留方法或服务的原始分类。budget 表示用尽调用预算，service_limit 表示达到环境服务限制，"
              "time_budget 和 replan_limit 分别表示 Graph Manager 的计时或重规划上限。"
              "finish 表示模型主动报告完成，实际任务成功仍以环境判定为准。", ""]
    lines += table(["方法", "模型", "技能调用/局", "模型查询/局",
                    "输入 token/局", "输出 token/局", "秒/局", "停止原因与局数"], traces)
    if reference_dirs:
        lines += reference_table(reference_dirs, scores)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True, type=Path, help="comparison output root")
    ap.add_argument("--native-dir", required=True, type=Path, help="env_service --log-dir")
    ap.add_argument("--sim-version", default="5.1.0.0")
    ap.add_argument("--markdown", required=True, type=Path)
    ap.add_argument("--reference-dir", action="append", type=Path, default=[],
                    help="additional same-version scripted run_episode output, repeatable")
    args = ap.parse_args()
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.write_text(build_report(args.out, args.native_dir, args.sim_version, args.reference_dir), encoding="utf-8")


if __name__ == "__main__":
    main()
