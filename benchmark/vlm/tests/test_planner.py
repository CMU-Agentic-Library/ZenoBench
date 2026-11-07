"""VLMPlanner without Isaac: prompt building, reply parsing, repairs, stop, step log."""
import json

from benchmark.vlm.planner import VLMPlanner, parse_reply

SKILLS = [{"name": "navigate", "parameters": {"destination": {"type": "place_ref", "required": True}}},
          {"name": "pick", "parameters": {"object": {"type": "object_ref", "required": True}}}]
OBS = {"images": [{"camera": "head", "path": "/nonexistent.png"}],
       "visible_objects": [{"name": "cup_1", "category": "breakfast_cup", "last_seen_on": "table/top"}],
       "observation_cache": [], "known_places": {"kitchen": {"kind": "room"}, "table/top": {"kind": "support"}},
       "robot": {"room": "kitchen"}, "last_result": None}


class Scripted:
    name = "scripted"

    def __init__(self, replies):
        self.replies, self.seen = list(replies), []

    def decide(self, system, messages):
        self.seen.append(json.loads(json.dumps(messages)))
        return self.replies.pop(0)


def test_parse():
    sk = {s["name"]: s for s in SKILLS}
    assert parse_reply('{"skill": "pick", "args": {"object": "cup_1"}}', sk)[0] == "call"
    assert parse_reply('sure: {"done": true}', sk)[0] == "done"
    assert parse_reply('{"skill": "fly", "args": {}}', sk) == ("error", "unknown skill 'fly'")
    assert parse_reply('{"skill": "pick", "args": {}}', sk)[0] == "error"
    assert parse_reply('{"skill": "pick", "args": {"obj": 1, "object": "x"}}', sk)[0] == "error"
    assert parse_reply("no json", sk)[0] == "error"


def test_loop_repairs_and_logs(tmp_path):
    b = Scripted(['{"skill": "fly"}', '{"skill": "pick", "args": {"object": "cup_1"}}', '{"done": true}'])
    p = VLMPlanner(backend=b)
    p.attach(tmp_path)
    p.reset("Bring the cup.", SKILLS)
    assert p.next_call(OBS) == {"skill": "pick", "args": {"object": "cup_1"}, "note": ""}
    first = b.seen[0][0]["content"]
    text = " ".join(x.get("text", "") for x in first)
    assert "Bring the cup." in text and "pick(object: object_ref)" in text and "cup_1" in text
    assert any(x["type"] == "image" for x in first)
    assert "not a valid call" in b.seen[1][-1]["content"][0]["text"]          # the error went back to the model
    assert p.next_call(OBS) is None and p.error is None                       # done
    rows = [json.loads(x) for x in (tmp_path / "vlm_steps.jsonl").read_text().splitlines()]
    assert [r["parsed"] for r in rows] == ["error", "call", "done"]


def test_gives_up_after_repairs(tmp_path):
    p = VLMPlanner(backend=Scripted(["nope"] * 3))
    p.reset("x", SKILLS)
    assert p.next_call(OBS) is None and "no valid call" in p.error


def test_old_images_are_dropped():
    p = VLMPlanner(backend=Scripted(['{"skill": "pick", "args": {"object": "a"}}'] * 4))
    p.keep_images = 1
    p.reset("x", SKILLS)
    for _ in range(3):
        p.next_call(OBS)
    imgs = [m for m in p.messages if m["role"] == "user" and any(b["type"] == "image" for b in m["content"])]
    assert len(imgs) == 1
