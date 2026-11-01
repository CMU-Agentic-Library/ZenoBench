"""Collision policy of robot motions (docs/COLLISION_AUDIT.md).

``Allow``      what one motion may touch.  ``FREE`` (the default) checks the whole robot;
               ``unchecked(reason)`` turns checking off for that motion, and ``LEGACY`` is the
               unchecked motion every former ``collision=False`` became (not migrated yet).
``Clearance``  ``rig.clear``: the skill scope (each skill starts with a fresh ``coll_kw`` on both
               arms and gives the caller's back when it ends) and the contact monitor.

The contact monitor (profile switch ``execution.contact_monitor``) checks every
``MONITOR_EVERY`` ticks which robot links sit inside the world at the real joint state and
base pose (Motion.robot_contacts) and logs each new link / obstacle pair as an
``unexpected_contact`` event, unless the current motion's Allow permits it.  A metric only:
it never fails a skill, and it leaves the planner's state exactly as it found it.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

import numpy as np

FINGER_LINKS = ("gripper_left_finger_link", "gripper_right_finger_link")
HAND_LINKS = FINGER_LINKS + ("gripper_link", "gripper_camera_link")
MONITOR_EVERY = 30          # ticks (4 per simulated second)
MIN_DEPTH = 0.003           # m: shallower penetration is the sphere model's noise
STILL = 1e-3                # rad / m: a robot that moved less since the last check is not checked again
MAX_RECORDS = 200           # contact onsets kept per episode (the counts keep counting)


@dataclass(frozen=True)
class Allow:
    """What one motion may touch; whatever is not listed is checked against the whole robot."""
    hand: str | None = None          # "right" / "left": the hand that may touch
    links: str = "fingers"           # "fingers" | "hand" (fingers, gripper, wrist camera)
    touch: tuple[str, ...] = ()      # entities that hand may touch (object, part, support)
    held_on: tuple[str, ...] = ()    # entities the held object may touch (its support, a container)
    checked: bool = True             # False: the motion is not collision-checked at all
    reason: str = ""

    def __post_init__(self):
        if (not self.checked or self.touch or self.held_on) and not self.reason:
            raise ValueError("an Allow that permits contact needs a reason")

    def permits(self, link: str, entity: str) -> bool:
        """The monitor's test: link (e.g. right_gripper_link) touching entity (object / part name)."""
        if self.hand is None or not link.startswith(self.hand + "_"):
            return False
        names = HAND_LINKS if self.links == "hand" else FINGER_LINKS
        return link[len(self.hand) + 1:] in names and any(
            entity == t or entity.startswith(t + "/") for t in self.touch)


FREE = Allow()


def unchecked(reason: str) -> Allow:
    """A motion that is not collision-checked; say why."""
    return Allow(checked=False, reason=reason)


LEGACY = unchecked("legacy: unchecked before docs/COLLISION_AUDIT.md, not migrated yet")
BASE_DRIVE = unchecked("base drive: the arms are not checked along the base path yet")


class Clearance:
    """``rig.clear``: skill scope, the motion being executed, and the contact monitor."""

    def __init__(self, rig):
        self.rig = rig
        self.monitor = False             # execution.contact_monitor (episode.profile.apply_rig_flags)
        self.skills = []                 # verbs of the running skills, outermost first
        self.leg = None                  # label of the last motion started
        self.allow = FREE                # its Allow
        self._live = set()               # (link, entity) pairs touching at the last check
        self._last = None                # robot state at the last check
        self.records = []
        self.counts = {"unexpected": 0, "allowed": 0, "checks": 0, "by_skill": {}, "by_leg": {}}

    # ------------------------------------------------------------- skill scope
    @contextmanager
    def skill(self, verb):
        """A skill runs with fresh query settings on both arms (``coll_kw``), whatever the
        previous skill left there, and gives the caller's settings back when it ends."""
        kins = [k for k in (getattr(self.rig, "kin", None), getattr(self.rig, "left_kin", None)) if k is not None]
        saved = [k.coll_kw for k in kins]
        for k in kins:
            k.coll_kw = {}
        self.skills.append(verb)
        try:
            yield
        finally:
            self.skills.pop()
            for k, kw in zip(kins, saved):
                k.coll_kw = kw

    def motion(self, label, allow):
        """A motion starts (move_to, move_left_to, joint_path, drive_base): the monitor
        judges contacts against it until the next one."""
        self.leg = label
        self.allow = allow

    # ------------------------------------------------------------- contact monitor
    def tick(self):
        """Rig.step, every MONITOR_EVERY ticks when the monitor is on."""
        motion = getattr(self.rig.kin, "motion", None)
        if motion is None:
            return
        rig = self.rig
        state = np.r_[rig.base_pose(), rig.q(), rig.left_q()[2:], rig.fingers()[:1], rig.left_fingers()[:1]]
        if self._last is not None and np.max(np.abs(state - self._last)) < STILL:
            return                                   # nothing of the robot moved: same contacts
        self._last = state
        try:
            hits = motion.robot_contacts(self.rig, MIN_DEPTH)
        except Exception as exc:                     # a metric: never stop the episode
            self.rig.log("contact_monitor_error", error=str(exc)[:200])
            self.monitor = False
            return
        self.counts["checks"] += 1
        pairs = {(link, ent): depth for link, ent, depth in hits}
        new = [p for p in pairs if p not in self._live]
        self._live = set(pairs)
        if not new:
            return
        skill = self.skills[-1] if self.skills else None
        out = []
        for link, ent in sorted(new):
            ok = self.allow.permits(link, ent)
            self.counts["allowed" if ok else "unexpected"] += 1
            if ok:
                continue
            for key, k in (("by_skill", skill or "-"), ("by_leg", self.leg or "-")):
                self.counts[key][k] = self.counts[key].get(k, 0) + 1
            out.append({"link": link, "entity": ent, "depth_m": round(pairs[(link, ent)], 4)})
        if not out:
            return
        rec = {"tick": self.rig.tick, "skill": skill, "leg": self.leg,
               "checked": self.allow.checked, "contacts": out}
        if len(self.records) < MAX_RECORDS:
            self.records.append(rec)
        self.rig.log("unexpected_contact", **{k: v for k, v in rec.items() if k != "tick"})

    def summary(self):
        """result.json ``contacts``."""
        return {**self.counts, "records": self.records}
