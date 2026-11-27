"""ReAct / CaP / open-loop / SayPlan and Graph Manager tell the model the same thing about failures and finishing."""
import ast
from pathlib import Path

from baseline.prompt import SYSTEM_TEMPLATE

GM = Path(__file__).resolve().parents[1] / "graph_manager" / "graph_manager" / "prompts" / "episode.py"


def _const(name):
    for node in ast.parse(GM.read_text()).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == name:
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} not in {GM}")


def test_failure_and_finish_rules_match_graph_manager():
    for name in ("FAILURE_RULE", "FINISH_RULE"):
        assert _const(name) in SYSTEM_TEMPLATE, name


def test_rules_do_not_hint_at_substitutes():
    """ReActHint's ablation is the substitution hint; the shared rules must not carry it."""
    rules = _const("FAILURE_RULE") + _const("FINISH_RULE")
    for word in ("similar", "substitut", "another object", "instead", "serves the same purpose"):
        assert word not in rules.lower(), word
