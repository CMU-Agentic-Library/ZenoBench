"""SayPlan-style baseline: a collapsed 3D scene graph as memory, semantic search over it, then a
multi-step plan with iterative replanning (after Rana et al., SayPlan, CoRL 2023).

    --planner recovery --policy baseline.sayplan:SayPlan --profile sticky/benchmark

* Scene graph: rooms -> furniture -> surfaces from the static map (known_places); an object is added
  only once the robot has observed it, under the surface / container it was last seen on or in.
  Nothing is placed in the graph before it is seen.
* Each planning round has two phases.  Search: the VLM sees the graph collapsed to rooms and may
  expand / contract nodes (at most MAX_EXPAND queries) to find what the instruction needs.  Plan:
  it then writes the call list for the rest of the task.  A plan step naming an unknown skill or an
  object that is not in the graph is sent back once for correction (a cheap stand-in for SayPlan's
  scene-graph simulator).
* The plan runs call by call; a new round starts when a call fails, when new objects become
  visible, or when the plan is used up.

Unlike ReAct the prompt carries no flat place / object lists - only the graph view the VLM opened.
"""

from __future__ import annotations

from baseline.base import BaselinePlanner
from baseline.parse import ParseError, json_objects, parse_plan, thought
from baseline.reveal import object_section, place_tags
from baseline.prompt import _j, image_paths, render_history, system_prompt

ANSWER = """\
Your memory is a 3D scene graph: rooms contain furniture, furniture has surfaces, observed objects \
sit on or in what they were last seen on or in. You see it collapsed to rooms; expand a room or a \
piece of furniture to see what is inside (its surfaces and the objects seen on them). Objects appear in the graph only after the robot has seen them.
Each turn answer with one or two short sentences starting with "Thought:", then one JSON object:
{"expand": "<node>"} or {"contract": "<node>"} to search the graph (no robot action), or
{"plan": [{"skill": "<skill name>", "args": {...}}, ...]} - the calls for the rest of the task \
(you will get to replan when a call fails or new objects are seen), or
{"finish": true, "reason": "<short reason>"} when the instruction is done or cannot be done."""

MAX_EXPAND = 6            # search queries per planning round
VERIFY_RETRIES = 1        # plans sent back for an unknown skill / object


class SceneGraph:
    def __init__(self):
        self.parent: dict[str, str] = {}
        self.info: dict[str, str] = {}
        self.kind: dict[str, str] = {}
        self.expanded: set[str] = set()

    def _add(self, name, parent, kind, info=""):
        self.parent[name], self.kind[name], self.info[name] = parent, kind, info

    def update(self, obs) -> set[str]:
        """Add the static map once and every observed object; returns the objects new to the graph."""
        places = obs.get("known_places") or {}
        if places and not any(k != "object" for k in self.kind.values()):
            for name, rec in places.items():
                if rec.get("kind") == "room":
                    self._add(name, "", "room")
            for name, rec in places.items():
                k = rec.get("kind")
                if k == "furniture":
                    self._add(name, rec.get("room") or "", "furniture", rec.get("category") or "")
                elif k == "appliance":
                    self._add(name, rec.get("room") or "", "appliance", rec.get("category") or "")
            for name, rec in places.items():
                k = rec.get("kind")
                if k == "support":
                    par = rec.get("furniture") if rec.get("furniture") in self.kind else rec.get("room") or ""
                    tags = place_tags(name)                      # SHIFT_REVEAL=full only
                    self._add(name, par, "surface", f"{rec.get('category') or ''} z={rec.get('z', 0):.2f}"
                              + (f"; {tags}" if tags else ""))
                elif k == "button":
                    self._add(name, rec.get("appliance") or "", "button")
            for name, rec in places.items():
                if rec.get("articulated") and name in self.info:
                    self.info[name] = (self.info[name] + f" opens ({rec.get('joint')})").strip()
        new = set()
        vis = {o["name"] for o in obs.get("visible_objects") or []}
        for o in (obs.get("observation_cache") or []) + (obs.get("visible_objects") or []):
            n = o["name"]
            if o.get("held"):
                par = "robot"
            else:
                par = o.get("last_seen_in") or o.get("last_seen_on") or ""
            if n not in self.kind:
                new.add(n)
            info = (o.get("category") or "") + (" (in view)" if n in vis else "")
            self._add(n, par, "object", info)
        return new

    def children(self, node):
        return sorted(n for n, p in self.parent.items() if p == node)

    def objects_under(self, node) -> int:
        k = 0
        for c in self.children(node):
            k += (self.kind[c] == "object") + self.objects_under(c)
        return k

    def has(self, name) -> bool:
        return name in self.kind

    def render(self) -> str:
        lines = []

        def walk(node, depth):
            kids = self.children(node)
            label = f"{node} [{self.kind.get(node, '?')}{', ' + self.info[node] if self.info.get(node) else ''}]"
            # surfaces and objects are leaves of the search: shown open once their parent is open
            is_open = node in self.expanded or self.kind.get(node) in ("surface", "object", "button")
            if kids and not is_open:
                n_obj = self.objects_under(node)
                label += f" (+{len(kids)} inside{f', {n_obj} seen objects' if n_obj else ''}; collapsed)"
            lines.append("  " * depth + "- " + label)
            if kids and is_open:
                for c in kids:
                    walk(c, depth + 1)
        for top in self.children(""):
            walk(top, 0)
        held = self.children("robot")
        if held:
            lines.append("- robot holds: " + ", ".join(held))
        orphans = [n for n, p in self.parent.items() if p and p not in self.kind and p != "robot"]
        if orphans:
            lines.append("- seen elsewhere: " + ", ".join(f"{n} (in/on {self.parent[n]})" for n in sorted(orphans)))
        return "\n".join(lines)


class SayPlan(BaselinePlanner):
    name = "sayplan"

    def reset(self, task_instruction, skills=None):
        super().reset(task_instruction, skills)
        self.system = system_prompt(self.skills, self.max_calls, answer=ANSWER)
        self.graph = SceneGraph()
        self.plan: list[dict] = []
        self.usage.update(rounds=0, expansions=0)

    def next_call(self, observation):
        self.observe(observation)
        new = self.graph.update(observation)
        if len(self.history) >= self.max_calls:
            self.stop_reason = "budget"
            return None
        last = self.history[-1].get("result") if self.history else None
        replan = not self.plan or (last is not None and not last.get("success")) or (bool(new) and bool(self.history))
        usage = note = None
        if replan:
            why = ("the last call failed" if last is not None and not last.get("success")
                   else f"new objects seen: {', '.join(sorted(new))}" if new and self.history else "")
            self.plan, usage, note = self._round(observation, why)
            if self.plan is None:
                return None
        return self.emit(self.plan.pop(0), note or "", usage)

    def _prompt(self, observation, why, extra=""):
        robot = observation.get("robot")
        vis = [o["name"] for o in observation.get("visible_objects") or []]
        parts = [f"Instruction: {self.instruction}",
                 f"Calls used: {len(self.history)} of {self.max_calls}",
                 "Calls so far:\n" + render_history(self.history),
                 f"Robot: {_j(robot)}" if robot else "",
                 "In view now: " + (", ".join(vis) if vis else "(nothing)"),
                 "Scene graph:\n" + self.graph.render(),
                 object_section(observation)]                    # SHIFT_REVEAL=objects/full only
        if why:
            parts.append(f"Replanning because {why}.")
        if extra:
            parts.append(extra)
        return "\n\n".join(p for p in parts if p)

    def _verify(self, plan):
        for i, c in enumerate(plan):
            if c["skill"] not in self.skill_names:
                return f"step {i + 1}: there is no skill {c['skill']!r}"
            for v in c["args"].values():
                for name in (v if isinstance(v, list) else [v]):
                    if isinstance(name, str) and "_" in name and name.rsplit("_", 1)[-1].isdigit() \
                            and not self.graph.has(name):
                        return f"step {i + 1}: {name!r} is not in the scene graph (not seen yet)"
        return ""

    def _round(self, observation, why):
        """Search + plan; returns (plan, usage of the deciding query, thought) or (None, ...) to stop."""
        self.usage["rounds"] += 1
        extra, expands, verifies, parse_left = "", 0, 0, 2
        while True:
            text, usage = self.ask(self.system, self._prompt(observation, why, extra), image_paths(observation))
            objs = [o for o in json_objects(text) if {"expand", "contract", "plan", "finish"} & set(o)]
            if not objs:
                self.usage["parse_errors"] += 1
                parse_left -= 1
                if parse_left < 0:
                    self.stop_reason = "parse_error"
                    return None, None, None
                extra = "Your previous answer had no usable JSON object. Answer again in the format."
                continue
            o = objs[-1]
            if "expand" in o or "contract" in o:
                node = str(o.get("expand") or o.get("contract"))
                if expands >= MAX_EXPAND:                    # search budget spent: only a plan or finish counts
                    self.usage["parse_errors"] += 1
                    parse_left -= 1
                    if parse_left < 0:
                        self.stop_reason = "search_budget"
                        return None, None, None
                    extra = "The search budget for this round is used up: answer with a plan or finish."
                    continue
                expands += 1
                self.usage["expansions"] += 1
                if not self.graph.has(node):
                    extra = f"There is no node {node!r} in the scene graph."
                elif "expand" in o:
                    self.graph.expanded.add(node)
                    extra = f"Expanded {node}."
                else:
                    self.graph.expanded.discard(node)
                    extra = f"Contracted {node}."
                if expands >= MAX_EXPAND:
                    extra += " Search budget for this round is used up: answer with a plan or finish now."
                continue
            try:
                plan = parse_plan(text)
            except ParseError as exc:
                self.usage["parse_errors"] += 1
                parse_left -= 1
                if parse_left < 0:
                    self.stop_reason = "parse_error"
                    return None, None, None
                extra = f"Your plan could not be used ({exc}). Answer again."
                continue
            if not plan:
                self.stop_reason = "finish: " + thought(text, 200)
                return None, None, None
            problem = self._verify(plan)
            if problem and verifies < VERIFY_RETRIES:
                verifies += 1
                extra = f"Plan check failed: {problem}. Fix the plan (search the graph if needed)."
                continue
            return plan, usage, thought(text)

    def summary(self):
        return {**super().summary(), "graph_nodes": len(self.graph.kind), "expanded": sorted(self.graph.expanded)}
