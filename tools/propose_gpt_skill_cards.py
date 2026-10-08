"""Ask GPT to write semantic Skill names/descriptions from existing Contracts.

Output is an experiment-only override catalog. It cannot alter Contract scope,
parameters, policy bindings, or physical verification. No output is fabricated
when OPENAI_API_KEY is unavailable.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from skill_library.gpt_experiment import request_json

DEFAULT_IDS = ('skill_017', 'skill_018', 'skill_040', 'skill_043', 'skill_029', 'skill_039')  # pick, place, open, heat, push, pour
CARD_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["skills"],
    "properties": {"skills": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["skill_id", "name", "description"],
        "properties": {"skill_id": {"type": "string"},
                       "name": {"type": "string"},
                       "description": {"type": "string"}},
    }}},
}
SYSTEM_PROMPT = """Write one planner-visible Skill name and one-sentence description
for each provided existing Contract. Preserve exactly its inputs, preconditions,
measured outcomes, and scope. Do not invent a new policy, a guaranteed success,
or a broader task. Use an actionable natural-language name, never an ID as name.
Return JSON with skills array containing skill_id, name, description only."""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-ids", nargs="+", default=list(DEFAULT_IDS))
    parser.add_argument("--model")
    parser.add_argument("--out", type=Path,
                        default=ROOT / "runs/gpt_skill_experiment/gpt_authored_cards.json")
    args = parser.parse_args()
    contracts = {row["skill_id"]: row for row in json.loads(
        (ROOT / "contract_library/skill_contracts.json").read_text())["contracts"]}
    ids = args.skill_ids
    if len(ids) != len(set(ids)) or any(sid not in contracts for sid in ids):
        parser.error("--skill-ids must be distinct active Skill IDs")
    rows = []
    for sid in ids:
        row = contracts[sid]
        rows.append({key: row[key] for key in (
            "contract_id", "skill_id", "verb", "noun", "scope", "inputs", "outputs", "requires", "ensures",
            "relations", "action_predicate")})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if not os.getenv("OPENAI_API_KEY"):
        status = {"status": "not_run_missing_api_key", "requested_skills": ids}
        args.out.with_suffix(".status.json").write_text(json.dumps(status, indent=2) + "\n")
        print("OPENAI_API_KEY is not set; no GPT-authored cards were produced", flush=True)
        return 2
    result, meta = request_json(SYSTEM_PROMPT, {"contracts": rows}, schema=CARD_SCHEMA,
                                schema_name="zenobench_skill_cards", model=args.model)
    generated = result.get("skills")
    if not isinstance(generated, list) or {r.get("skill_id") for r in generated} != set(ids) \
            or len(generated) != len(ids):
        raise ValueError("GPT did not return exactly one card per requested Skill")
    cards = {}
    for row in generated:
        sid = row["skill_id"]
        if not all(isinstance(row.get(key), str) and row[key].strip()
                   for key in ("name", "description")):
            raise ValueError(f"{sid}: empty or invalid name/description")
        cards[sid] = {"name": row["name"], "description": row["description"]}
    args.out.write_text(json.dumps(cards, indent=2, ensure_ascii=False) + "\n")
    args.out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    print("WROTE", args.out, len(cards), "GPT-authored cards", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
