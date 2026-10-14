"""ZenoBench environment service: start a task, run Skill Contracts, check the goal.

``server.py`` is the HTTP service (standard library only); every exp runs its own
simulator in a ``worker.py`` process under Isaac Sim's Python.  See README.md.
"""
