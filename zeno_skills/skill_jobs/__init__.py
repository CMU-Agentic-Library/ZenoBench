"""Layer 5's skill jobs (docs/MOTION_ARCHITECTURE.md 2.3, 9.4): the Python part of each skill that runs
on motion_skills.run_skill -- what it reads off the rig (annotations, the objects, the hand), its hooks,
its result -- one module per skill, and the rig's base model.  Not in skills.py (it only shrinks), not in
skill_plans/ (that layer knows no rig)."""
