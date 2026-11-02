"""Reproducible failure injection (ZenoBench v5).  See failure_injection/spec.py for the taxonomy
(action-level grasp / slip / placement / IK; task-level capacity / destination / resource /
dependency, initial or dynamic; mixed / coupled) and failure_injection/runtime.py for how each one
is applied to the simulator."""
from failure_injection.spec import (ACTION_KINDS, KINDS, TASK_KINDS, FailureSpecError, category,  # noqa: F401
                                    level, mode, validate)
