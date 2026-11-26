"""Compare local planners on the declared substitution batch, joining to native verdicts."""

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from statistics import mean

from baseline.comparison import ABLATIONS, METHODS, MODELS, V6, episodes, read_json, result_path
from baseline.report import average, count_ratio, episode_key, graph_attempt_table, ratio, read_outcome, table
from benchmark.v6.substitution_eval import catalog, episode_row


def collect(root, batch):
    if (root / "manifest.json").is_file():
        manifest = read_json(root / "manifest.json")
    else:
        protocol = next((root / "planner/protocol").glob("*/*/*/protocol.json"), None)
        if protocol is None:
            raise ValueError(f"no run protocol found in {root}")
        recorded = read_json(protocol)
        manifest = {"runner_commit": recorded["commit"], "batch_sha256": recorded["batch_sha256"],
                    "packages": {"isaacsim": recorded["isaacsim"]}}
    digest = hashlib.sha256(batch.read_bytes()).hexdigest()
    if digest != manifest["batch_sha256"]:
        raise ValueError("batch differs from the run manifest")
    if "catalog_sha256" in manifest:
        catalog_digest = hashlib.sha256((V6 / "tasks.json").read_bytes()).hexdigest()
        if catalog_digest != manifest["catalog_sha256"]:
            raise ValueError("task catalog differs from the one used by the simulator")
    jobs = episodes(batch)
    tasks = catalog()
    layouts, initial, exp_ids = {}, {}, set()
    rows = []
    for index, job in enumerate(jobs):
        key = episode_key(job)
        for method, (_, profile) in METHODS.items():
            for model in MODELS:
                directory = result_path(root / "planner", model, method, job)
                status, outcome = read_outcome(directory, root / "native", model, method, job, manifest["packages"]["isaacsim"])
                row = dict(task=key[0], layout=key[1], seed=key[2], model=model, method=method, status=status)
                if outcome is not None:
                    protocol = root / "planner/protocol" / model / method / f"{index}-of-{len(jobs)}" / "protocol.json"
                    config = read_json(protocol)
                    if config["batch_sha256"] != digest or config["commit"] != manifest["runner_commit"]:
                        raise ValueError(f"run configuration mismatch in {protocol}")
                    exp = outcome["exp_id"]
                    if (exp in exp_ids or layouts.setdefault(key, outcome["config_hash"]) != outcome["config_hash"]
                            or initial.setdefault((key, profile), outcome["episode_hash"]) != outcome["episode_hash"]):
                        raise ValueError(f"duplicate run or mismatched paired scene at {directory}")
                    exp_ids.add(exp)
                    native = read_json(root / "native" / job["task"] / exp / "result.json")
                    if native["config_hash"] != outcome["config_hash"] or (
                            "overlay_sha256" in manifest and
                            native["runtime"].get("lab_compat_sha256") != manifest["overlay_sha256"]):
                        raise ValueError(f"native scene or simulator overlay mismatch at {directory}")
                    wrapper = read_json(directory / "result.json")
                    stop = wrapper.get("stop_reason")
                    if stop == "planner_done":
                        stop = wrapper.get("planner_summary", {}).get("stop_reason") or stop
                    substitution = episode_row({**native, "_stop": stop}, tasks[job["task"]])
                    if substitution is None or substitution["side"] not in ("B", "B_open"):
                        raise ValueError(f"expected a substitution-side verdict at {directory}")
                    row.update(substitution, exp_id=exp, profile=profile, episode_hash=outcome["episode_hash"],
                               config_hash=outcome["config_hash"], native_score=outcome["score"],
                               valid_execution_failures=outcome["valid_execution_failures"])
                elif status == "interrupted":
                    failure_path = directory / "failed.json"
                    if failure_path.exists():
                        failure = read_json(failure_path)
                        row["interruption"] = failure.get("crash") or failure.get("check_error")
                rows.append(row)
    return manifest, rows


def render(manifest, rows, batch):
    cells = defaultdict(list)
    for row in rows:
        cells[row["method"], row["model"]].append(row)
    by_key = {cell: {(r["task"], r["layout"], r["seed"]): r for r in attempts if r["status"] == "scored"}
              for cell, attempts in cells.items()}
    planned = read_json(batch)
    sides = Counter(r["side"] for r in planned)
    reasons = Counter(r["reason"] for r in planned)
    states = Counter(r["status"] for r in rows)
    beijing = timezone(timedelta(hours=8))
    pause = manifest.get("pause")
    if pause:
        stamp = datetime.fromisoformat(pause["stopped_at"]).astimezone(beijing).strftime("%Y-%m-%d %H:%M")
        if pause["started_without_result"] + pause["never_started"] != states["outstanding"]:
            raise ValueError("pause inventory differs from outstanding episode count")
        summary = (f"实验已于北京时间 {stamp} 暂停。原生计分 **{states['scored']:,} / {len(rows):,}** 局，"
                   f"另有 {states['interrupted']} 局已记录运行中断，{pause['started_without_result']} 局已启动但未取得完整结果，"
                   f"{pause['never_started']:,} 局尚未启动。")
    else:
        stamp = datetime.now(beijing).strftime("%Y-%m-%d %H:%M")
        summary = (f"北京时间 {stamp}，原生计分 **{states['scored']} / {len(rows)}** 局，"
                   f"运行中断 {states['interrupted']} 局，待取得结局 {states['outstanding']} 局。")
        if states["outstanding"]:
            summary += "当前为阶段快照，各行覆盖的布局随调度进度变化。"
    pkg = manifest["packages"]
    source = f"运行代码 `{manifest['runner_commit'][:7]}`。"
    if "upstream_main" in manifest:
        source = f"上游 main `{manifest['upstream_main'][:7]}`，Graph Manager `{manifest['graph_manager'][:7]}`，" + source
    audit = manifest.get("input_audit")
    if audit:
        source += (f"与上一轮 `{audit['previous_runner'][:7]}` 的 {audit['matched_episodes']} 个相同任务、布局和种子相比，"
                   f"{audit['changed_spawn']} 局的机器人起点改变，{audit['changed_public_instruction']} 局的模型可见指令改变。")
    versions = [f"Isaac Sim {pkg['isaacsim']}"]
    if "isaaclab_source" in manifest:
        versions.extend([f"Isaac Lab {manifest['isaaclab_source']}", f"cuRobo {pkg['nvidia-curobo']}"])
    lines = ["# ZenoBench 替代任务基线", "", summary, "",
             f"来自 `{batch.name}` 的 {len(planned)} 局覆盖 {len({r['task'] for r in planned})} 个任务、"
             f"{len({(r['task'], r['variant']) for r in planned})} 个布局。所有方法使用相同的布局和种子。"
             f"其中有 {sides['B']} 局可按物体分级，另有 {sides['B_open']} 局按完成档位评分。"
             "这批场景均需替代，无法估计理想物可用时的误替代率。", "",
             source + f"使用 {'、'.join(versions)}。"
             "仓库默认的 Isaac Sim 5.1 与本表使用的仿真版本不同。", "",
             "每局最多调用 60 次技能。主方法使用 sticky/benchmark，观测含头部 RGB、已知地点和环境给出的可见物体清单。"
             "ReActHint 增加替代提示，ReActPrivileged 使用 sticky/privileged 额外提供任务物体及位置。"
             "所有模型均在本地推理，温度为 0。", "",
             "## 方法对比", "",
             "成功以仿真最终判定为准。严格成功还要求达到该布局可用的最佳替代。"
             "已返回局数包含计分局和中断局。表中同时给出有原生成功凭据的局数占已返回局数的比例。"
             "执行故障列统计最终失败且至少一次有效技能调用出现执行错误的局，分母为已计分的失败局。"
             "一次失败可能同时涉及规划与执行。", ""]
    overall, detail, causes = [], [], []
    for (method, model), attempts in cells.items():
        scored = [r for r in attempts if r["status"] == "scored"]
        fail = [r for r in scored if not r["success"]]
        graded = [r for r in scored if r["side"] == "B"]
        tiered = [r for r in scored if r["side"] == "B_open"]
        interrupted = sum(r["status"] == "interrupted" for r in attempts)
        successes = sum(r["success"] for r in scored)
        overall.append([method, model, f"{len(scored)}/{len(attempts)}", interrupted, ratio(scored, "success"),
                        count_ratio(successes, len(scored) + interrupted), average(scored, "native_score", 3), ratio(scored, "strict"),
                        count_ratio(sum(r["valid_execution_failures"] > 0 for r in fail), len(fail))])
        detail.append([method, model, ratio(graded, "hit"), ratio(graded, "missed_switch"), ratio(graded, "bad"),
                       ratio(graded, "grab"), ratio(graded, "else"), ratio(tiered, "hit"), ratio(tiered, "bad"),
                       ratio(tiered, "missed_switch")])
        causes.append([method, model, *(ratio([r for r in scored if r["reason"] == reason], "strict")
                                        for reason in reasons)])
    lines += table(["方法", "模型", "计分/计划", "中断", "成功/计分", "已证实成功/已返回",
                    "平均原生分", "严格成功", "执行故障/失败"], overall)
    main_methods = [method for method in METHODS if method not in ABLATIONS]
    shared = set.intersection(*(set(by_key[method, model]) for method in main_methods for model in MODELS))
    if len(shared) < len(planned):
        lines += ["## 五种主方法的同局比较", "",
                  f"按任务、布局和种子配对后，全部 15 个组合共同完成了 {len(shared)} 局。"
                  "下表在这些共同样本上计算严格成功。", ""]
        shared_rows = []
        for model in MODELS:
            counts = []
            for method in main_methods:
                counts.append(ratio([by_key[method, model][key] for key in shared], "strict"))
            shared_rows.append([model, *counts])
        lines += table(["模型", *main_methods], shared_rows)
    lines += ["## 替代选择", "",
              "可分级的 B 局从成功分支或最后拿起的候选物推断选择，因此可能命中替代物而任务仍失败。"
              "若布局只提供差档替代物，命中最佳与选差档可以重合。"
              "容器作为目的地时，失败轨迹有时无法识别所选容器。B_open 只按仿真完成档位判定，"
              "失败包含已想到替代方案但执行未完成的情况。每个分母均为该方法在对应侧已计分的局数。", ""]
    lines += table(["方法", "模型", "B 命中最佳", "B 漏替代", "B 选差档", "B 抢占", "B 其他物体",
                    "B_open 满分", "B_open 部分分", "B_open 失败"], detail)
    lines += ["## 按理想物不可用原因划分的严格成功", ""]
    lines += table(["方法", "模型", *(f"{reason}（{n} 局）" for reason, n in reasons.items())], causes)
    lines += ["## 同局消融", "", "每一项只比较 ReAct 与相应消融均有原生判定的同一布局和种子。", ""]
    paired = []
    for model in MODELS:
        indexed = {method: by_key[method, model] for method in ("ReAct", "ReActHint", "ReActPrivileged")}
        for method in ("ReActHint", "ReActPrivileged"):
            common = sorted(indexed["ReAct"].keys() & indexed[method].keys())
            differences = [indexed[method][k]["native_score"] - indexed["ReAct"][k]["native_score"] for k in common]
            paired.append([model, method, len(common), ratio([indexed["ReAct"][k] for k in common], "strict"),
                           ratio([indexed[method][k] for k in common], "strict"),
                           f"{mean(differences):+.3f}" if common else "—"])
    lines += table(["模型", "与 ReAct 配对的方法", "同局数", "ReAct 严格成功", "消融严格成功", "平均原生分差"], paired)
    ref = manifest.get("physical_reference")
    if ref:
        peers = [r for r in rows if r["status"] == "scored" and (r["task"], r["layout"], r["seed"], r["profile"]) ==
                 (ref["task_id"], ref["variant"], ref["seed"], ref["profile"])]
        if any((r["config_hash"], r["episode_hash"]) != (ref["config_hash"], ref["episode_hash"]) for r in peers):
            raise ValueError("scripted reference and planner have different initial conditions")
        lines += ["## 执行器校准", "",
                  f"另取 `{ref['task_id']}` 的 `{ref['variant']}`、种子 {ref['seed']}，用目录里的 "
                  f"`{ref['route']}` 脚本和相同的 {ref['profile']} 执行。"
                  f"共调用 {ref['calls']} 次技能，{ref['expected_outcomes_met']} 次符合脚本预期，"
                  f"原生得分为 {ref['score']['score']:.1f}，任务判定为{'成功' if ref['task_success'] else '失败'}。"
                  f"当前有 {len(peers)} 局 VLM 原生记录与其配置及初始条件哈希一致。"
                  "此单局校准独立于表中 VLM 计数。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--batch", type=Path, default=V6 / "batches/substitution_smoke.json")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--jsonl", type=Path, help="one row for every planned method, model and episode")
    args = parser.parse_args()
    manifest, rows = collect(args.run_dir, args.batch)
    report = render(manifest, rows, args.batch)
    if any(r["method"] == "GraphManager" and r["status"] == "interrupted" for r in rows):
        graph_scores = {}
        for model in MODELS:
            graph_scores["GraphManager", model] = {
                (r["task"], r["layout"], r["seed"]): r for r in rows
                if r["method"] == "GraphManager" and r["model"] == model and r["status"] == "scored"}
        history = graph_attempt_table(args.run_dir / "planner", episodes(args.batch), graph_scores)
        report += "\n" + "\n".join(history)
    args.out.write_text(report)
    if args.jsonl:
        args.jsonl.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


if __name__ == "__main__":
    main()
