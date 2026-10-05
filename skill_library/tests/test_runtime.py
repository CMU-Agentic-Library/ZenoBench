"""The upper layer receives post-failure state, not only an exception string."""

from types import SimpleNamespace
import unittest

from skill_library.runtime import run_grounded_nodes


class FakeRig:
    held = None
    left_held = None

    def base_pose(self):
        return (1.0, 2.0, 0.0)

    def obj_pose(self, name):
        return ((self.object_x, 0.0, 0.7), (1.0, 0.0, 0.0, 0.0))


class MovingThenFailingRunner:
    def __init__(self, rig):
        self.rig = rig
        self.calls = 0

    def run(self, contract, route, *args):
        self.calls += 1
        self.rig.object_x = 1.5
        raise RuntimeError("grasp failed after contact")


class RuntimeResultTests(unittest.TestCase):
    def test_success_keeps_node_id_and_measured_predicates(self):
        rig = FakeRig()
        rig.object_x = 1.0
        class SuccessfulRunner:
            def run(self, contract, route, *args):
                return SimpleNamespace(observations={
                    "verified_predicates": ["held_by_right_hand", "object_lifted"],
                    "lift_m": 0.07,
                })
        calls = [{
            "node_id": "n1", "skill_id": "skill_004",
            "contract": "pick.v1", "route": "auto", "args": ["apple"],
            "resolved_args": {"object": "apple"},
        }]
        result = run_grounded_nodes(rig, calls, runner=SuccessfulRunner())
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["results"][0]["node_id"], "n1")
        self.assertEqual(result["results"][0]["verified_predicates"],
                         ["held_by_right_hand", "object_lifted"])
        self.assertEqual(result["results"][0]["contract_observations"]["lift_m"], 0.07)

    def test_failure_returns_post_action_observation_and_stops(self):
        rig = FakeRig()
        rig.object_x = 1.0
        runner = MovingThenFailingRunner(rig)
        calls = [
            {"node_id": "n1", "skill_id": "skill_004",
             "contract": "pick.v1", "route": "auto", "args": ["apple"],
             "resolved_args": {"object": "apple"}},
            {"node_id": "n2", "skill_id": "skill_006",
             "contract": "place.v1", "route": "container",
             "args": ["apple", "in:fruit_basket"],
             "resolved_args": {"object": "apple", "container": "fruit_basket"}},
        ]
        result = run_grounded_nodes(rig, calls, runner=runner)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(runner.calls, 1)
        self.assertEqual([row["node_id"] for row in result["results"]], ["n1"])
        self.assertEqual(
            result["last_observation"]["objects"]["apple"]["position"][0], 1.5
        )


if __name__ == "__main__":
    unittest.main()
