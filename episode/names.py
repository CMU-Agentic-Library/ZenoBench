"""Anonymous object names for the planner (profile ``observation.anonymize_names``).

Instance names in the scene configuration often say what the object is *for* (``spare_mug``,
``full_bowl``, ``stock_cup_1``, ``his_cup``) - a hint the image does not give.  With the switch on, the
planner never sees them: every object is called ``<category>_<k>`` (its asset, numbered within the
category in an order fixed by the episode's ``config_hash``, so the number says nothing either), in
every planner-facing field - observations, call results, masked feedback - and the names in its
calls are mapped back before execution.  A real instance name in a call is refused as unknown.

Logs keep the real names (``calls.jsonl`` records the planner's own arguments, ``feedback`` the
executed ones) and the episode directory gets ``names.json`` (alias -> real) for the evaluation.
Places (rooms, furniture, surfaces, appliances) keep their names: they are the static map.
"""
from __future__ import annotations

import hashlib
import re

KEEP = ("category", "tags")                           # fields that name a kind, never an instance
_EDGE_L, _EDGE_R = r"(?<![A-Za-z0-9_])", r"(?![A-Za-z0-9_])"


def _pattern(names):
    if not names:
        return None
    return re.compile(_EDGE_L + "(" + "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
                      + ")" + _EDGE_R)


class NameMap:
    def __init__(self, objects: dict, salt: str, reserved=()):
        """``objects``: {instance name: category}; ``salt``: the episode's config hash;
        ``reserved``: names an alias must not take (places, other instance names)."""
        taken = set(reserved) | set(objects)
        by_cat: dict[str, list[str]] = {}
        for name, cat in objects.items():
            by_cat.setdefault(cat, []).append(name)
        self.alias: dict[str, str] = {}
        for cat, names in sorted(by_cat.items()):
            names.sort(key=lambda n: hashlib.sha1(f"{salt}:{n}".encode()).hexdigest())
            k = 0
            for n in names:
                while True:
                    k += 1
                    a = f"{cat}_{k}"
                    if a not in taken or a == n:
                        break
                taken.add(a)
                self.alias[n] = a
        self.real = {a: n for n, a in self.alias.items()}
        self._out = _pattern([n for n, a in self.alias.items() if n != a])
        self._in = _pattern(list(self.real))
        self._leak = _pattern([n for n in self.alias if n not in self.real])

    # -- outward: everything the planner reads ----------------------------------------------------------
    def public(self, value):
        """Replace instance names with their aliases in a JSON-like value (strings, keys, lists)."""
        if self._out is None:
            return value
        if isinstance(value, str):
            return self._out.sub(lambda m: self.alias[m.group(1)], value)
        if isinstance(value, dict):                   # a category may be spelled like an instance name
            return {self.public(k): v if k in KEEP else self.public(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.public(v) for v in value]
        return value

    def scrub(self, value):
        """Instance names that are not also aliases -> ``<unknown>`` (echoing a guessed name back would
        let ``public`` reveal its alias)."""
        if self._leak is None:
            return value
        if isinstance(value, str):
            return self._leak.sub("<unknown>", value)
        if isinstance(value, dict):
            return {k: self.scrub(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.scrub(v) for v in value]
        return value

    # -- inward: the planner's call arguments ------------------------------------------------------------
    def private(self, value):
        """Aliases -> instance names in call arguments.  Raises KeyError naming a real instance name
        the planner was never given (it can only have guessed it)."""
        if isinstance(value, str):
            if self._leak is not None:
                m = self._leak.search(self._in.sub("", value) if self._in is not None else value)
                if m:
                    raise KeyError(m.group(1))
            return self._in.sub(lambda m: self.real[m.group(1)], value) if self._in is not None else value
        if isinstance(value, dict):
            return {k: self.private(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.private(v) for v in value]
        return value
