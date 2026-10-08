"""The VLM planning interface must be reproducible without a model key."""

import json
from pathlib import Path
import unittest

from skill_library.gpt_experiment import (compile_proposal, identity_bindings,
                                          planning_payload, skill_cards,
                                          task_scene_view, _response_text)

ROOT = Path(__file__).resolve().parents[2]


class GPTExperimentTests(unittest.TestCase):
    def test_cards_cover_seventy_verbs_with_conditions(self):
        cards = skill_cards()
        self.assertEqual(len(cards), 70)
        pick = next(c for c in cards if c["verb"] == "pick")
        self.assertIn("hand_empty(hand=right)", pick["preconditions"])
        self.assertIn("top_pinch", pick["path_conditions"])
        with self.assertRaisesRegex(ValueError, "unknown skill"):
            skill_cards(overrides={"skill_999": {"name": "x", "description": "y"}})

    def test_payload_has_goal_scene_ids_and_optional_relations(self):
        task = json.loads((ROOT / "tasks/collect_fruits/task.json").read_text())
        ann = json.loads((ROOT / task["annotation"]).read_text())
        payload = planning_payload(task, ann)
        self.assertEqual(payload["goal"], task["goal"])
        self.assertIn("apple", {row["name"] for row in payload["scene"]["objects"]})
        self.assertNotIn("relations", payload["skills"][0])
        self.assertIn("relations", planning_payload(task, ann, with_relations=True)["skills"][0])
        self.assertEqual(task_scene_view(task, ann)["roles"]["fruit"], ["apple", "orange"])

    def test_exact_id_json_grounds_to_skill_contracts(self):
        task = json.loads((ROOT / "tasks/heat_breakfast_preloaded/task.json").read_text())
        ann = json.loads((ROOT / task["annotation"]).read_text())
        graph = {"schema_version": 2, "kind": "skill_subgraph", "subgoal_id": "sg_heat", "nodes": [
            {"id": "go", "skill": "navigate", "args": {"destination": {"ref": "kitchen_microwave"}}, "depends_on": []},
            {"id": "heat", "skill": "heat", "args": {"food": {"ref": "oatmeal"},
                                                     "appliance": {"ref": "kitchen_microwave"},
                                                     "temp_c": {"value": 60}}, "depends_on": ["go"]}]}
        self.assertEqual(identity_bindings(graph), {"kitchen_microwave": "kitchen_microwave", "oatmeal": "oatmeal"})
        self.assertEqual([c["verb"] for c in compile_proposal(graph, ann)], ["navigate", "heat"])

    def test_response_parser_rejects_incomplete_generation(self):
        response = {"status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": '{"graph":{}}'}]}]}
        self.assertEqual(_response_text(response), '{"graph":{}}')
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            _response_text({"status": "incomplete", "output": []})


if __name__ == "__main__":
    unittest.main()
