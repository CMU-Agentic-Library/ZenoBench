"""The names-only planning baseline must be reproducible without a model key."""

import json
from pathlib import Path
import unittest

from skill_library.gpt_experiment import (compile_proposal, identity_bindings,
                                          planning_payload, skill_cards,
                                          task_scene_view, _response_text)

ROOT = Path(__file__).resolve().parents[2]


class GPTExperimentTests(unittest.TestCase):
    def test_all_cards_have_semantic_names_and_callable_signatures(self):
        cards = skill_cards()
        self.assertEqual(len(cards), 50)
        self.assertEqual(cards[19]["name"], "Pick a flat object from a floor corner")
        self.assertTrue(all(card["name"] != card["skill_id"] and card["description"]
                            for card in cards))
        with self.assertRaisesRegex(ValueError, "unknown skill"):
            skill_cards(overrides={"skill_999": {"name": "x", "description": "y"}})

    def test_planner_sees_task_goal_and_relevant_scene_ids(self):
        task = json.loads((ROOT / "tasks/collect_fruits/task.json").read_text())
        ann = json.loads((ROOT / task["annotation"]).read_text())
        payload = planning_payload(task, ann)
        self.assertEqual(len(payload["skills"]), 50)
        self.assertNotIn("conditional_relations", payload)
        self.assertEqual(payload["goal"], task["goal"])
        target = task["goal"]["all"][1]["support"]
        self.assertIn(target, {row["name"] for row in payload["scene"]["supports"]})
        self.assertIn("apple", {row["name"] for row in payload["scene"]["objects"]})
        self.assertEqual(task_scene_view(task, ann)["roles"]["fruit"], ["apple", "orange"])

    def test_exact_id_json_compiles_to_existing_contracts(self):
        task = json.loads((ROOT / "tasks/heat_breakfast_preloaded/task.json").read_text())
        ann = json.loads((ROOT / task["annotation"]).read_text())
        graph = {"schema_version": 1, "kind": "skill_subgraph",
                 "subgoal_id": "sg_heat", "nodes": [
                     {"id": "start", "skill_id": "skill_010",
                      "args": {"appliance": {"ref": "kitchen_microwave"}},
                      "depends_on": []},
                     {"id": "wait", "skill_id": "skill_040",
                      "args": {"object": {"ref": "oatmeal"},
                               "min_temp_c": {"value": 60}},
                      "depends_on": ["start"]},
                 ]}
        self.assertEqual(identity_bindings(graph),
                         {"kitchen_microwave": "kitchen_microwave", "oatmeal": "oatmeal"})
        self.assertEqual([call["contract"] for call in compile_proposal(graph, ann)],
                         ["contract_018", "contract_048"])

    def test_response_parser_rejects_incomplete_generation(self):
        response = {"status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": '{"graph":{}}'}]}]}
        self.assertEqual(_response_text(response), '{"graph":{}}')
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            _response_text({"status": "incomplete", "output": []})


if __name__ == "__main__":
    unittest.main()
