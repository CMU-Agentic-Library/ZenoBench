"""Zeno Malo manipulation skills driven by scene annotations (GT affordances).

Modules
-------
kinematics   exact right-arm FK / TCP IK (pure numpy)
collision    robot sphere model + world model from annotations
annotations  scene/asset annotation schema, loader and geometry helpers
planner      base-pose ("park") search for a set of TCP targets
rig          Isaac Sim runtime: joint-drive control, base motion, recording
policies     rig-bound OOP atomic policy API and PolicySuite
skills       existing motion/control implementations used by the policy classes
"""
