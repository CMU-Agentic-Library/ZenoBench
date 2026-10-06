"""Meaningful checks for the upper-layer graph handoff without Isaac Sim."""

from copy import deepcopy
import json
import unittest

from skill_library.graph import (
    GraphValidationError, compile_contract_calls, compile_grounded_nodes,
    load_skills, read_json, validate_subgraph,
)
from skill_library.graph import HERE


class SkillSubgraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = read_json(HERE / "examples/collect_fruits.skill_subgraph.json")
        cls.bindings = read_json(HERE / "examples/collect_fruits.bindings.json")
        cls.annotation = read_json(HERE.parent / "tasks/collect_fruits/annotation.json")

    def test_example_compiles_to_existing_contract_routes(self):
        calls = compile_contract_calls(self.graph, self.bindings, self.annotation)
        self.assertEqual(
            calls,
            [
                {"contract": "contract_012", "route": "compose", "args": ["apple"]},
                {"contract": "contract_014", "route": "compose",
                 "args": ["apple", "fruit_basket"]},
                {"contract": "contract_012", "route": "compose", "args": ["orange"]},
                {"contract": "contract_014", "route": "compose",
                 "args": ["orange", "fruit_basket"]},
            ],
        )
        self.assertEqual(
            [call["node_id"] for call in
             compile_grounded_nodes(self.graph, self.bindings, self.annotation)],
            ["n1", "n2", "n3", "n4"],
        )
        grounded = compile_grounded_nodes(self.graph, self.bindings, self.annotation)
        self.assertEqual(grounded[1]["action_predicate"], {
            "name": "insert_object_in_container",
            "arguments": {"object": "apple", "container": "fruit_basket"},
        })

    def test_preloaded_heating_example_compiles_to_start_then_wait(self):
        graph = read_json(HERE / "examples/heat_preloaded.skill_subgraph.json")
        bindings = read_json(HERE / "examples/heat_preloaded.bindings.json")
        annotation = read_json(HERE.parent / "tasks/heat_breakfast_preloaded/annotation.json")
        calls = compile_grounded_nodes(graph, bindings, annotation)
        self.assertEqual([row["contract"] for row in calls],
                         ["contract_018", "contract_048"])
        self.assertEqual(calls[1]["depends_on"], ["start"])
        self.assertEqual(calls[1]["args"], ["oatmeal", 60.0])

    def test_all_published_skill_records_load(self):
        skills = load_skills()
        self.assertEqual(len(skills), 50)
        self.assertEqual(set(skills), {f"skill_{i:03d}" for i in range(1, 51)})
        self.assertEqual(skills["skill_011"]["invocation"]["input_order"], [])

    def test_typed_navigation_and_push_compile(self):
        support = self.annotation["supports"][0]["name"]
        graph = {
            "schema_version": 1, "kind": "skill_subgraph",
            "subgoal_id": "sg_typed",
            "nodes": [
                {"id": "nav", "skill_id": "skill_001",
                 "args": {"pose": {"value": [2.4, 5.6, 15.0]}}, "depends_on": []},
                {"id": "push", "skill_id": "skill_008",
                 "args": {
                     "object": {"ref": "the apple"},
                     "support": {"ref": "the support"},
                     "direction_xy": {"value": [1.0, 0.0]},
                     "distance_m": {"value": 0.08},
                 }, "depends_on": ["nav"]},
            ],
        }
        bindings = {**self.bindings, "the support": support}
        calls = compile_grounded_nodes(graph, bindings, self.annotation)
        self.assertEqual([call["contract"] for call in calls],
                         ["contract_009", "contract_016"])
        self.assertEqual(calls[0]["args"], [[2.4, 5.6, 15.0]])
        self.assertEqual(calls[1]["args"],
                         ["apple", support, [1.0, 0.0], 0.08])
        graph["nodes"][1]["args"]["direction_xy"] = {"value": [2.0, 0.0]}
        with self.assertRaisesRegex(GraphValidationError, "invalid unit_vec2"):
            validate_subgraph(graph)

    def test_every_skill_compiles_one_typed_node(self):
        from skill_library.graph import compile_grounded_nodes
        import json
        from pathlib import Path
        skills = load_skills()
        assets = read_json(HERE.parent / "annotations/assets.json")
        microwave_ann = read_json(
            HERE.parent / "runs/verify_microwave_fixture/task/annotation.json"
        )
        for skill_id, spec in skills.items():
            ann = microwave_ann if skill_id in {
                "skill_009", "skill_010", "skill_014", "skill_015",
                "skill_023", "skill_024"
            } else self.annotation
            bindings = {}
            args = {}
            for key, meta in spec["args"].items():
                kind = meta["type"]
                if kind.endswith("_ref"):
                    if kind == "object_ref":
                        instance = ann["objects"][0]["name"]
                    elif kind == "container_ref":
                        instance = next(obj["name"] for obj in ann["objects"]
                                        if assets[obj["asset"]].get("container"))
                    elif kind == "microwave_support_ref":
                        instance = next(row["name"] for row in ann["supports"]
                                        if row.get("furniture") == "kitchen_microwave"
                                        and row["name"].endswith("/inside_floor"))
                    elif kind == "support_ref":
                        instance = ann["supports"][0]["name"]
                    elif kind == "appliance_ref":
                        instance = "kitchen_microwave"
                    else:
                        instance = ann["articulated"][0]["name"]
                    phrase = f"the {key}"
                    bindings[phrase] = instance
                    args[key] = {"ref": phrase}
                else:
                    value = {
                        "pose2d": [2.0, 2.0, 0.0],
                        "unit_vec2": [1.0, 0.0],
                        "xy": [2.0, 2.0],
                        "positive_number": 0.08,
                        "number": 0.0,
                    }[kind]
                    args[key] = {"value": value}
            graph = {"schema_version": 1, "kind": "skill_subgraph",
                     "subgoal_id": "sg_catalog",
                     "nodes": [{"id": "n1", "skill_id": skill_id,
                                "args": args, "depends_on": []}]}
            calls = compile_grounded_nodes(graph, bindings, ann)
            self.assertEqual(len(calls), 1, skill_id)
            self.assertEqual(calls[0]["contract"], spec["contract_id"])

    def test_articulated_ref_must_match_scene_annotation(self):
        graph = {
            "schema_version": 1, "kind": "skill_subgraph",
            "subgoal_id": "sg_open",
            "nodes": [{"id": "open", "skill_id": "skill_003",
                       "args": {"articulated": {"ref": "the door"}},
                       "depends_on": []}],
        }
        with self.assertRaisesRegex(GraphValidationError, "absent from scene annotation"):
            compile_grounded_nodes(graph, {"the door": "apple"}, self.annotation)

    def test_cycle_is_rejected(self):
        graph = deepcopy(self.graph)
        graph["nodes"][0]["depends_on"] = ["n4"]
        with self.assertRaisesRegex(GraphValidationError, "cycle"):
            validate_subgraph(graph)

    def test_unresolved_ref_is_rejected(self):
        bindings = dict(self.bindings)
        del bindings["the orange"]
        with self.assertRaisesRegex(GraphValidationError, "unresolved ref"):
            compile_contract_calls(self.graph, bindings, self.annotation)

    def test_container_must_have_container_annotation(self):
        bindings = dict(self.bindings)
        bindings["the fruit basket visible on the low bookcase"] = "orange"
        with self.assertRaisesRegex(GraphValidationError, "not an annotated container"):
            compile_contract_calls(self.graph, bindings, self.annotation)

    def test_unknown_skill_is_rejected(self):
        graph = deepcopy(self.graph)
        graph["nodes"][0]["skill_id"] = "skill_999"
        with self.assertRaisesRegex(GraphValidationError, "unknown skill_id"):
            validate_subgraph(graph)

    def test_skill_contract_pairing_is_strict(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "catalog.json").write_text(json.dumps({
                "schema_version": 1, "kind": "skill_catalog",
                "skills": [{"skill_id": "skill_006", "definition": "skill_006.json"}]
            }))
            skill = read_json(HERE / "skills/skill_006/skill.json")
            skill["contract_id"] = "contract_013"
            (root / "skill_006.json").write_text(json.dumps(skill))
            with self.assertRaisesRegex(GraphValidationError, "Contract pairing"):
                load_skills(root)
            skill["contract_id"] = "contract_014"
            skill["achieves"][0]["predicate"] = "on"
            (root / "skill_006.json").write_text(json.dumps(skill))
            with self.assertRaisesRegex(GraphValidationError, "pre/postconditions differ"):
                load_skills(root)


if __name__ == "__main__":
    unittest.main()
