"""Offline tests of the baseline planners (no simulator, no API): a fake VLM and fake observations.

    python -m pytest baseline/tests -q
"""

from __future__ import annotations

import io
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from baseline.human import Human, parse_line                                  # noqa: E402
from baseline.parse import ParseError, parse_call                             # noqa: E402
from baseline.prompt import render_menu, system_prompt, user_prompt           # noqa: E402
from baseline.react import ReAct, ReActHint                                   # noqa: E402

MENU = [
    {"name": "navigate", "description": "Drive to a place.",
     "parameters": {"destination": {"type": "place_ref", "required": True, "description": "Where."}},
     "preconditions": [], "effects": ["base_near(place=$destination)"]},
    {"name": "pick", "description": "Pick an object.",
     "parameters": {"object": {"type": "object_ref", "required": True},
                    "hand": {"type": "hand", "required": False, "default": "right"}},
     "preconditions": ["hand_empty(hand=$hand)"], "effects": ["holding(object=$object)"]},
]


def obs(last=None, visible=()):
    return {"images": [{"camera": "head", "path": "/nonexistent/head.png"}],
            "visible_objects": [{"name": n, "category": n.rsplit("_", 1)[0], "tags": [], "in_view": True,
                                 "held": False, "last_seen_position": [1.0, 2.0, 0.8],
                                 "last_seen_on": "kitchen_island/top", "last_seen_in": None, "last_seen_tick": 5}
                                for n in visible],
            "observation_cache": [],
            "known_places": {"kitchen": {"kind": "room"},
                             "kitchen_island/top": {"kind": "support", "category": "island", "z": 0.86,
                                                    "room": "kitchen", "center": [7.4, 1.75]}},
            "robot": {"base_pose": [2.7, 0.7, -150.0], "held_right": None, "held_left": None, "room": "kitchen"},
            "last_result": last}


class FakeClient:
    def __init__(self, answers):
        self.answers, self.calls = list(answers), []

    def chat(self, system, user, images=()):
        self.calls.append((system, user, list(images)))
        return self.answers.pop(0), {"input_tokens": 100, "output_tokens": 10, "cached_input_tokens": 80,
                                     "latency_s": 0.1}


class TestParse(unittest.TestCase):
    def test_call_and_finish(self):
        self.assertEqual(parse_call('Thought: go.\n{"skill": "pick", "args": {"object": "mug_1"}}'),
                         {"skill": "pick", "args": {"object": "mug_1"}})
        self.assertIsNone(parse_call('Thought: done. {"finish": true, "reason": "ok"}'))
        # the last matching object wins; unrelated JSON is skipped
        self.assertEqual(parse_call('{"a": 1} {"skill": "a"} then {"skill": "b", "args": {}}')["skill"], "b")
        for bad in ("no json", '{"skill": 3}', '{"skill": "x", "args": [1]}'):
            with self.assertRaises(ParseError):
                parse_call(bad)


class TestPrompt(unittest.TestCase):
    def test_menu_and_hint(self):
        m = render_menu(MENU)
        self.assertIn("pick(object: object_ref, hand?: hand=\"right\")", m)
        self.assertIn("pre: hand_empty(hand=$hand)", m)
        self.assertNotIn("substitute", system_prompt(MENU, 60).lower())
        self.assertIn("prefer exactly what was asked", system_prompt(MENU, 60, substitution_hint=True).lower())

    def test_user_prompt_has_no_goal(self):
        u = user_prompt("Bring the mug.", obs(visible=["mug_1"]), [], 0, 60)
        self.assertIn("mug_1 (mug) on kitchen_island/top", u)
        self.assertIn("- kitchen: kitchen_island/top [support, island, z=0.86]", u)
        self.assertNotIn("Goal status", u)
        self.assertNotIn("ground truth", u)


class TestReAct(unittest.TestCase):
    def test_episode_loop(self):
        fake = FakeClient(['Thought: go there.\n{"skill": "navigate", "args": {"destination": "kitchen_island/top"}}',
                           "I am not sure",                                   # unparseable -> one retry
                           'Thought: grab it. {"skill": "pick", "args": {"object": "mug_1"}}',
                           'Thought: done. {"finish": true, "reason": "holding the mug"}'])
        p = ReAct(model="fake", client=fake)
        p.reset("Bring the mug.", MENU)
        a1 = p.next_call(obs())
        self.assertEqual(a1["skill"], "navigate")
        self.assertEqual(a1["usage"]["input_tokens"], 100)
        a2 = p.next_call(obs(last={"success": True, "error_code": None, "outputs": {"base_pose": [5.5, 1.7, 0]},
                                   "now_visible": ["mug_1"]}, visible=["mug_1"]))
        self.assertEqual(a2, {"skill": "pick", "args": {"object": "mug_1"}, "note": "grab it.",
                              "usage": a2["usage"]})
        self.assertIn("could not be used", fake.calls[2][1])                   # retry note in the prompt
        self.assertIn('1. navigate("destination":"kitchen_island/top") -> OK', fake.calls[2][1])
        self.assertIn("now visible: mug_1", fake.calls[2][1])
        self.assertEqual(fake.calls[0][2], ["/nonexistent/head.png"])
        self.assertIsNone(p.next_call(obs(last={"success": False, "error_code": "GRASP_FAILED", "error": "slipped"})))
        self.assertIn("FAILED GRASP_FAILED: slipped", fake.calls[3][1])
        s = p.summary()
        self.assertEqual((s["vlm_queries"], s["parse_errors"], s["input_tokens"]), (4, 1, 400))
        self.assertTrue(s["stop_reason"].startswith("finish"))
        self.assertEqual(p.history[-1]["result"]["error_code"], "GRASP_FAILED")

    def test_hint_and_parse_give_up(self):
        fake = FakeClient(["?", "?", "?"])
        p = ReActHint(model="fake", client=fake)
        p.reset("Bring the mug.", MENU)
        self.assertIn("Prefer exactly what was asked", p.system)
        self.assertIsNone(p.next_call(obs()))
        self.assertEqual((p.stop_reason, p.usage["vlm_queries"]), ("parse_error", 3))

    def test_budget(self):
        fake = FakeClient(['{"skill": "pick", "args": {"object": "mug_1"}}'] * 3)
        p = ReAct(model="fake", max_calls=2, client=fake)
        p.reset("x", MENU)
        self.assertIsNotNone(p.next_call(obs()))
        self.assertIsNotNone(p.next_call(obs(last={"success": False, "error_code": "E"})))
        self.assertIsNone(p.next_call(obs(last={"success": False, "error_code": "E"})))
        self.assertEqual(p.stop_reason, "budget")
        self.assertIn("at most 2 skill calls", p.system)


class TestHuman(unittest.TestCase):
    def test_parse_line(self):
        self.assertEqual(parse_line('pick object=mug_1 hand=left'),
                         {"skill": "pick", "args": {"object": "mug_1", "hand": "left"}})
        self.assertEqual(parse_line('arrange objects=["a_1","b_1"] max_dist_m=0.4')["args"],
                         {"objects": ["a_1", "b_1"], "max_dist_m": 0.4})
        self.assertIsNone(parse_line("finish"))
        self.assertEqual(parse_line("help pick"), "help pick")

    def test_session(self):
        out = io.StringIO()
        h = Human(stdin=io.StringIO("menu\nfly up=1\npick object=mug_1\nfinish\n"), stdout=out)
        h.reset("Bring the mug.", MENU)
        self.assertEqual(h.next_call(obs(visible=["mug_1"]))["args"], {"object": "mug_1"})
        self.assertIsNone(h.next_call(obs(last={"success": True})))
        text = out.getvalue()
        self.assertIn("Instruction: Bring the mug.", text)
        self.assertIn("[image] /nonexistent/head.png", text)
        self.assertIn("? no skill 'fly'", text)
        self.assertEqual(h.stop_reason, "finish")


if __name__ == "__main__":
    unittest.main()
