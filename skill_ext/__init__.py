"""Extensible skills (ZenoBench v5): user skills defined by a SKILL.md, next to the fixed library.

The built-in library (contract_library/skill_contracts.json, the 71 SkillNodes, their GT policies and
the GT oracle) is read here and never changed.  A user skill is one directory holding a ``SKILL.md``
whose YAML front matter declares the skill (name, description, parameters, preconditions, expected
effects, executor) and whose body is free documentation shown to the planner.

    from skill_ext import SkillRegistry
    reg = SkillRegistry.default()                       # built-ins only: the Fixed-Skill track
    reg.load_dir("skill_ext/examples")                  # + user skills: the Open-Skill track
    reg.menu("open")                                    # what a planner is shown

Tracks:

* ``fixed``: the built-in SkillNodes only (the v3/v4 benchmark as it was); results are comparable with
  every earlier run.
* ``open``: built-ins plus the registered user skills.  A user skill may call built-ins (scripted), or
  drive the robot from observations through an action interface (VLA / RL / scripted policy).

``skill_ext.dispatch.install`` puts the registry in front of an ``episode.episode.Episode``'s runner;
nothing else in the episode changes.
"""
from skill_ext.registry import SkillRegistry, SkillSpec, TRACKS  # noqa: F401
from skill_ext.schema import SkillSchemaError, validate_spec  # noqa: F401
