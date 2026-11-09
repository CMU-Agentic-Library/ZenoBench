"""The dependency direction of the motion layers (docs/MOTION_ARCHITECTURE.md 2.5, rule 10): the
primitives, the skill plans and the park search know no simulator -- not the rig, not the skills
that drive it -- and the execution touches it only through motion_state.Actuator.  Read off the
import statements (module-level and inside functions), followed through the package."""

import ast
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parents[1] / "zeno_skills"


def _module_file(name):
    path = PKG.joinpath(*name.split(".")[1:])
    return path / "__init__.py" if path.is_dir() else path.with_suffix(".py")


def _imports(name):
    """zeno_skills modules ``name`` imports (relative or absolute, anywhere in the file)."""
    file = _module_file(name)
    pkg = name if file.name == "__init__.py" else name.rsplit(".", 1)[0]
    out = set()
    for node in ast.walk(ast.parse(file.read_text())):
        if isinstance(node, ast.ImportFrom):
            if node.level:
                base = pkg.split(".")
                base = base[:len(base) - node.level + 1]
                mod = ".".join(base + ([node.module] if node.module else []))
            else:
                mod = node.module or ""
            if not mod.startswith("zeno_skills"):
                continue
            for alias in node.names:                        # "from . import x" may name a module
                sub = f"{mod}.{alias.name}"
                out.add(sub if _module_file(sub).exists() else mod)
        elif isinstance(node, ast.Import):
            out |= {a.name for a in node.names if a.name.startswith("zeno_skills")}
    return {m for m in out if _module_file(m).exists()}


def _reach(name):
    seen, todo = set(), [name]
    while todo:
        m = todo.pop()
        if m in seen:
            continue
        seen.add(m)
        todo += sorted(_imports(m))
    return seen - {name}


RIG_FREE = ["zeno_skills.motion_state", "zeno_skills.primitives", "zeno_skills.skill_plans",
            "zeno_skills.skill_plans._common", "zeno_skills.skill_plans.pick", "zeno_skills.skill_plans.place",
            "zeno_skills.skill_plans.navigate", "zeno_skills.park_search"]


@pytest.mark.parametrize("module", RIG_FREE)
def test_layers_1_to_3_import_neither_the_rig_nor_the_skills(module):
    reached = _reach(module)
    assert not reached & {"zeno_skills.rig", "zeno_skills.skills", "zeno_skills.planner", "zeno_skills.motion_skills"}, \
        sorted(reached)


def test_the_execution_reads_and_writes_the_simulator_only_through_the_actuator():
    src = (PKG / "run.py").read_text()
    calls = {n.func.value.id + "." + n.func.attr for n in ast.walk(ast.parse(src))
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name)
             and n.func.value.id == "act"}
    actuator = {"act." + m for m in ("follow", "grip", "drive_base", "swing", "declare", "contact_allow",
                                     "snapshot", "arm_kin", "log")}
    assert calls and calls <= actuator, calls - actuator
    assert "rig." not in src


def test_no_rig_attribute_shadows_an_actuator_method():
    # Rig.arm is the articulation's joint index tensor: an Actuator method of that name was shadowed
    # by it (a TypeError at the first segment, 11-08)
    from zeno_skills.motion_state import Actuator
    methods = [m for m in vars(Actuator) if not m.startswith("_")]
    src = (PKG / "rig.py").read_text()
    shadowed = [m for m in methods if f"self.{m} =" in src]
    assert methods and not shadowed, shadowed
