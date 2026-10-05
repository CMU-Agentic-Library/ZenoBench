"""The VLM receives conditional options and the measured failure state."""

import unittest

from skill_library.planner_handoff import planner_catalog, replan_request


class PlannerHandoffTests(unittest.TestCase):
    def test_catalog_contains_all_skills_and_conditional_relations(self):
        catalog = planner_catalog()
        self.assertEqual(len(catalog["skills"]), 42)
        self.assertEqual(len(catalog["relations"]), 38)
        self.assertTrue(all(row["automatic"] is False for row in catalog["relations"]))

    def test_failed_mobile_pick_yields_stationary_recovery_with_live_state(self):
        graph = {
            "schema_version": 1, "kind": "skill_subgraph", "subgoal_id": "sg_pick",
            "nodes": [
                {"id": "move_pick", "skill_id": "skill_018",
                 "args": {"object": {"ref": "the apple"},
                          "base_path": {"value": [2.0, 1.0, 0.0]}},
                 "depends_on": []},
                {"id": "place", "skill_id": "skill_005",
                 "args": {"object": {"ref": "the apple"},
                          "support": {"ref": "the table"}},
                 "depends_on": ["move_pick"]},
            ],
        }
        observed = {"base_pose": [1.7, 1.0, 0.0], "held_right": None,
                    "objects": {"apple": {"position": [1.8, 1.0, 0.7]}}}
        execution = {
            "status": "failed",
            "results": [{"node_id": "move_pick", "skill_id": "skill_018",
                         "status": "failed", "error_code": "GRASP_MISSED",
                         "error": "object moved", "contract_observations": {"contact": False}}],
            "last_observation": observed,
        }
        request = replan_request("Put the apple on the table", graph, execution,
                                 {"the apple": "apple", "the table": "table_top"})
        self.assertEqual(request["failed"]["skill_id"], "skill_018")
        self.assertEqual(request["unexecuted"], ["place"])
        self.assertEqual(request["last_observation"], observed)
        self.assertEqual(request["candidate_skills"][0]["skill_id"], "skill_004")
        self.assertTrue(any(row["kind"] == "recovery"
                            for row in request["conditional_relations"]))

    def test_rejects_stale_or_mismatched_execution(self):
        graph = {"schema_version": 1, "kind": "skill_subgraph",
                 "subgoal_id": "sg_pick", "nodes": [
                     {"id": "pick", "skill_id": "skill_004",
                      "args": {"object": {"ref": "the apple"}}, "depends_on": []}]}
        result = {"status": "failed", "results": [
            {"node_id": "wrong", "skill_id": "skill_004", "status": "failed"}],
            "last_observation": {"held_right": None}}
        with self.assertRaisesRegex(ValueError, "node IDs"):
            replan_request("Pick the apple", graph, result, {"the apple": "apple"})


if __name__ == "__main__":
    unittest.main()
