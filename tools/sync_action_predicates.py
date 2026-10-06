"""Keep 50 unique verb+noun action predicates paired with verified state facts.

The action predicate is planner-visible and bound to Contract input nouns.
Existing requires/achieves remain shared measured world facts for composition.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "zeno_skills/node_contracts.json"
SKILLS = ROOT / "skill_library/skills"

# One distinct action verb per SkillNode. Nouns describe its operated entity.
ACTION_NAMES = {
    "skill_001": ("navigate", "base"),
    "skill_002": ("transport", "carried_object"),
    "skill_003": ("open", "articulated_joint"),
    "skill_004": ("acquire", "object"),
    "skill_005": ("deposit", "object_on_support"),
    "skill_006": ("insert", "object_in_container"),
    "skill_007": ("close", "articulated_joint"),
    "skill_008": ("shove", "object_along_support"),
    "skill_009": ("press", "appliance_door_button"),
    "skill_010": ("start", "microwave_heating"),
    "skill_011": ("tuck", "right_arm"),
    "skill_012": ("set", "torso_height"),
    "skill_013": ("pitch", "waist"),
    "skill_014": ("load", "microwave_cavity"),
    "skill_015": ("retrieve", "cavity_object"),
    "skill_016": ("pinch", "flat_object_edge"),
    "skill_017": ("grip", "cup_handle"),
    "skill_018": ("intercept", "moving_object"),
    "skill_019": ("deliver", "object"),
    "skill_020": ("scoop", "floor_object"),
    "skill_021": ("convoy", "bimanual_load"),
    "skill_022": ("swing", "articulated_door"),
    "skill_023": ("trigger", "microwave_door_opening"),
    "skill_024": ("shut", "microwave_door"),
    "skill_025": ("pull", "manual_handle"),
    "skill_026": ("push", "manual_handle"),
    "skill_027": ("clamp", "object_top"),
    "skill_028": ("grasp", "round_rim"),
    "skill_029": ("clasp", "rectangular_rim"),
    "skill_030": ("lay", "edge_held_flat_object"),
    "skill_031": ("lower", "torso"),
    "skill_032": ("raise", "torso"),
    "skill_033": ("lean", "waist"),
    "skill_034": ("straighten", "waist"),
    "skill_035": ("expose", "flat_object_edge"),
    "skill_036": ("orient", "held_object"),
    "skill_037": ("stand", "object_on_support"),
    "skill_038": ("position", "object_near_hint"),
    "skill_039": ("align", "upright_object_near_hint"),
    "skill_040": ("attain", "food_temperature"),
    "skill_041": ("hoist", "carried_object"),
    "skill_042": ("retreat", "carried_object"),
    "skill_043": ("pivot", "base"),
    "skill_044": ("translate", "base"),
    "skill_045": ("nudge", "supported_object"),
    "skill_046": ("drag", "supported_object"),
    "skill_047": ("unfold", "hinged_door"),
    "skill_048": ("extend", "drawer"),
    "skill_049": ("ready", "floor_object"),
    "skill_050": ("clear", "microwave_door_sweep"),
}


def _action(row: dict) -> dict:
    verb, noun = ACTION_NAMES[row["skill_id"]]
    return {
        "name": f"{verb}_{noun}",
        "verb": verb,
        "noun": noun,
        "arguments": row["legacy_call_args"],
        "verified_by": row["expected_state_change"],
    }


def _insert(row: dict, action: dict) -> dict:
    return {key: value for pair in (
        [(key, value), ("action_predicate", action)]
        if key == "expected_state_change" else [(key, value)]
        for key, value in row.items() if key != "action_predicate")
        for key, value in pair}


def build() -> dict[Path, str]:
    catalog = json.loads(CONTRACTS.read_text())
    rows = catalog["contracts"]
    if set(ACTION_NAMES) != {row["skill_id"] for row in rows}:
        raise ValueError("action vocabulary must cover exactly the active SkillNodes")
    verbs = [verb for verb, _ in ACTION_NAMES.values()]
    if len(verbs) != len(set(verbs)):
        raise ValueError("action verbs must be globally unique")
    files: dict[Path, str] = {}
    for row in rows:
        action = _action(row)
        skill_path = SKILLS / row["skill_id"] / "skill.json"
        skill = json.loads(skill_path.read_text())
        if skill["contract_id"] != row["contract_id"]:
            raise ValueError(f"{row['skill_id']}: Contract pairing differs")
        files[skill_path] = json.dumps(_insert(skill, action), indent=2) + "\n"
        row.update(action_predicate=action)
    files[CONTRACTS] = json.dumps(catalog, indent=2) + "\n"
    lines = [
        "# Skill 动作谓词与任务状态", "",
        "每个 Skill 有一个唯一的动词＋名词动作谓词；括号内是 Contract 输入槽位，运行时绑定真实场景实例。只有配对 Contract 的 `verified_by` 状态事实全通过，才报告该动作已验证。", "",
        "同一个 `on`、`inside` 或 `joint_closed` 状态事实可以由多个 Skill 建立，供任务目标和其他 Skill 的前置条件共用。", "",
        "| Skill | 动作谓词 | verifier 测得的状态事实 |", "| --- | --- | --- |",
    ]
    for row in rows:
        action = row["action_predicate"]
        signature = ", ".join(action["arguments"])
        facts = ", ".join(f"`{fact}`" for fact in action["verified_by"])
        lines.append(f"| `{row['skill_id']}` | `{action['name']}({signature})` | {facts} |")
    task_files = sorted((ROOT / "tasks").glob("*/task.json"))
    task_count = len(task_files)
    clause_count = sum(len(json.loads(path.read_text())["goal"]["all"])
                       for path in task_files)
    lines += ["", "## 与 ZenoBench 任务目标的关系", "",
              f"[goal_predicates.json](goal_predicates.json) 把 8 类目标子句映射到候选动作和最终 TaskEvaluator 检查。[task_coverage.json](task_coverage.json) 对照当前 {task_count} 个任务的 {clause_count} 条子句。", "",
              "`near` 是组内两两距离，单次 `within_hint_radius` 只检查一个物体到提示点；`not_dropped` 是跨动作的不变量，不可能由单个 Skill 谓词保证。目标可表达不代表所有场景都物理成功。", ""]
    files[ROOT / "skill_library/ACTION_PREDICATES.md"] = "\n".join(lines)

    # Keep the planner-facing README table in sync with the JSON argument
    # schemas. The caller fills the arguments, while Contract verifiers create
    # the state facts; they are not free-form output labels from the VLM.
    readme_path = ROOT / "skill_library/README.md"
    readme = readme_path.read_text()
    begin = "<!-- action-signatures:start -->"
    end = "<!-- action-signatures:end -->"
    if readme.count(begin) != 1 or readme.count(end) != 1:
        raise ValueError("README action-signature markers must each occur once")
    table = [
        begin,
        "| SkillNode | 动词 | 动词＋名词动作谓词 | 可填写参数及类型 | Contract 验证的状态 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        skill = json.loads(files[SKILLS / row["skill_id"] / "skill.json"])
        action = row["action_predicate"]
        params = ", ".join(
            f"`{name}: {spec['type']}`" for name, spec in skill["args"].items()
        ) or "无"
        verified = ", ".join(f"`{fact}`" for fact in action["verified_by"])
        table.append(
            f"| `{row['skill_id']}` | `{action['verb']}` | `{action['name']}` | {params} | {verified} |"
        )
    table.append(end)
    prefix, rest = readme.split(begin, 1)
    _, suffix = rest.split(end, 1)
    files[readme_path] = prefix + "\n".join(table) + suffix
    return files


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = build()
    stale = [str(path) for path, content in files.items()
             if not path.exists() or path.read_text() != content]
    if args.check:
        if stale:
            raise SystemExit(f"stale action predicates: {stale[:4]} ({len(stale)})")
        print(f"{len(ACTION_NAMES)} unique action predicates current")
    else:
        for path, content in files.items():
            path.write_text(content)
        print(f"wrote {len(ACTION_NAMES)} unique action predicates")


if __name__ == "__main__":
    main()
