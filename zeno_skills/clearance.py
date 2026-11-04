"""Collision policy of robot motions (docs/COLLISION_AUDIT.md).

``Allow``      what one motion may touch.  ``FREE`` (the default) checks the whole robot;
               ``FREE_ELSE_STRAIGHT`` checks it too, but where no collision-free path exists it
               makes the unchecked straight move it always made and logs a
               ``clearance_fallback``; ``unchecked(reason)`` turns checking off for that motion,
               and ``LEGACY`` is the unchecked motion every former ``collision=False`` became
               (not migrated yet).  ``LEAVE_CONTACT``: the straight, unchecked move out of the
               contact a motion starts in (just grasped, just let go); what the hand and its load
               touch at its start they may touch (Rig._from_contact).
``Clearance``  ``rig.clear``: the skill scope (each skill starts with a fresh ``coll_kw`` on both
               arms and gives the caller's back when it ends) and the contact monitor.

The contact monitor (profile switch ``execution.contact_monitor``) checks every
``MONITOR_EVERY`` ticks which robot links sit inside the world at the real joint state and
base pose (Motion.robot_contacts) and logs each new link / obstacle pair as an
``unexpected_contact`` event, unless the current motion's Allow permits it; what a hand holds
counts as part of the robot (link ``held:<object>``, judged by ``Allow.held_on``).  A movable
object is pushed away before a sphere sinks into it, so the monitor also watches the near
objects nobody holds and logs a ``disturbed_object`` event when one moves or tips.  A metric
only: it never fails a skill, and it leaves the planner's state exactly as it found it.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, replace

import numpy as np

FINGER_LINKS = ("gripper_left_finger_link", "gripper_right_finger_link")
HAND_LINKS = FINGER_LINKS + ("gripper_link", "gripper_camera_link")
MONITOR_EVERY = 30          # ticks (4 per simulated second)
MIN_DEPTH = 0.003           # m: shallower penetration is the sphere model's noise
STILL = 1e-3                # rad / m: a robot that moved less since the last check is not checked again
MAX_RECORDS = 200           # contact onsets / fallbacks kept per episode (the counts keep counting)
# Disturbed objects: a movable object is pushed away at once, so a robot sphere never sinks into
# it by MIN_DEPTH (a spoon carried along the island knocked a bottle over unseen); the monitor
# watches the near objects' poses instead
MOVED_M = 0.02              # m an object nobody holds may drift between checks...
MOVED_TILT = 20.0           # ...or deg its up axis may tip (turning about it is not counted)
SETTLE_TICKS = 240          # an object just let go, or just knocked, settles (falls into a bin, rolls) this long
CARRIED_M = 0.02            # m: an object that moved like a held one since the last check rides in / on it


@dataclass(frozen=True)
class Allow:
    """What one motion may touch; whatever is not listed is checked against the whole robot."""
    hand: str | None = None          # "right" / "left": the hand that may touch
    links: str = "fingers"           # "fingers" | "hand" (fingers, gripper, wrist camera)
    touch: tuple[str, ...] = ()      # entities that hand may touch (object, part, support)
    held_on: tuple[str, ...] = ()    # entities the held object may touch (its support, a container)
    checked: bool = True             # False: the motion is not collision-checked at all
    fallback: bool = False           # checked, but no collision-free path: the unchecked straight move
    from_contact: bool = False       # touch / held_on: what the hand and its load touch at the start
    lifts: str | None = None         # from_contact: the object the closed hand lifts before it counts as
                                     # held (pick checks the lift first); it rides in the hand's collision model
    to_contact: bool = False         # the straight move into the contact a motion ends in (Rig.move_to's
                                     # approach): its hand may touch ``touch``, its load ``held_on``
    reason: str = ""

    def __post_init__(self):
        if (not self.checked or self.fallback or self.from_contact or self.to_contact or self.touch or
                self.held_on) and not self.reason:
            raise ValueError("an Allow that permits contact needs a reason")
        if self.fallback and not self.checked:
            raise ValueError("fallback is for a checked motion")
        if self.lifts is not None and not self.from_contact:
            raise ValueError("lifts is for a motion out of a contact")
        if self.to_contact and (self.checked or self.from_contact):
            raise ValueError("to_contact is the unchecked segment into a contact")

    def permits(self, link: str, entity: str) -> bool:
        """The monitor's test: link (e.g. right_gripper_link, or held:<object> for what a hand
        holds) touching entity (object / part name)."""
        if link.startswith("held:"):
            return any(entity == t or entity.startswith(t + "/") for t in self.held_on)
        if self.hand is None or not link.startswith(self.hand + "_"):
            return False
        names = HAND_LINKS if self.links == "hand" else FINGER_LINKS
        return link[len(self.hand) + 1:] in names and any(
            entity == t or entity.startswith(t + "/") for t in self.touch)


FREE = Allow()


def _up(q):
    """The z axis of quaternion q (w, x, y, z)."""
    w, x, y, z = (float(v) for v in q)
    return np.array([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)])


def unchecked(reason: str) -> Allow:
    """A motion that is not collision-checked; say why."""
    return Allow(checked=False, reason=reason)


LEGACY = unchecked("legacy: unchecked before docs/COLLISION_AUDIT.md, not migrated yet")
# a free-space leg that used to be unchecked (COLLISION_AUDIT.md phase 2, decision 1): planned
# collision-free when a path exists, else the straight move it always made, logged
FREE_ELSE_STRAIGHT = Allow(fallback=True, reason="free-space leg: collision-free when a path exists, "
                                                 "else the straight unchecked move, logged")
# the short straight move out of the contact a motion starts in (lift after the grasp, back out
# after letting go): a contact segment, not planned -- the free-space motion after it starts clear
# of the world.  The hand (fingers, gripper, wrist camera) and what it holds may touch what they
# touch at its start (the 11-01 run's 87 "starts in collision" fallbacks were all the hand on the
# support)
LEAVE_CONTACT = Allow(checked=False, from_contact=True,
                      reason="contact segment out of the contact it starts in: the hand and its load may touch what "
                             "they touch at the start")


def into_contact(touch=(), held_on=()) -> Allow:
    """The contact segment a move_to with an approach ends with (a grasp closing in, a load set
    down): straight along the approach, unchecked, as long as the collision model says the robot
    touches the world there; the hand may touch ``touch`` (the object it grasps), its load
    ``held_on`` (where it is set down).  The approach before it is planned with the fingers."""
    return Allow(checked=False, to_contact=True, touch=tuple(touch), held_on=tuple(held_on),
                 reason="contact segment into the contact the motion ends in: its length from the collision "
                        "model, the approach before it planned")


def lifting(name: str) -> Allow:
    """LEAVE_CONTACT for the lift right after closing the hand on ``name``, before it is held."""
    return replace(LEAVE_CONTACT, lifts=name)


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
        self.fallbacks = []
        self.counts = {"unexpected": 0, "allowed": 0, "checks": 0, "by_skill": {}, "by_leg": {},
                       "fallback": 0, "planned": 0, "fallback_by_leg": {},
                       "disturbed": 0, "disturbed_by_skill": {}, "disturbed_by_leg": {}}
        self.disturbances = []
        self._ref = {}                   # object -> (pos, quat wxyz) where it last stood
        self._held = set()               # objects held at the last check
        self._let_go = {}                # object -> tick it was let go
        self._prev = {}                  # object -> position at the last check
        self._held_since = {}            # object -> tick it was last picked up
        self._pending = []               # disturbances waiting SETTLE_TICKS: not the object being picked up

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

    def planned(self, label):
        """A FREE_ELSE_STRAIGHT leg got a collision-free path."""
        self.counts["planned"] += 1

    def fallback(self, label, why, hit=None):
        """A FREE_ELSE_STRAIGHT leg had no collision-free path and makes the straight move:
        ``why`` the planner's refusal, ``hit`` what the straight path runs into."""
        skill = self.skills[-1] if self.skills else None
        self.counts["fallback"] += 1
        key = label or "-"
        self.counts["fallback_by_leg"][key] = self.counts["fallback_by_leg"].get(key, 0) + 1
        rec = {"tick": self.rig.tick, "skill": skill, "leg": label, "why": why[:200], "hit": hit}
        if len(self.fallbacks) < MAX_RECORDS:
            self.fallbacks.append(rec)
        self.rig.log("clearance_fallback", **{k: v for k, v in rec.items() if k != "tick"})

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
        self._watch_objects(motion)
        self._confirm_disturbances()
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

    def _watch_objects(self, motion):
        """Queue a disturbance (see _confirm_disturbances) for each object near the base that nobody holds and
        that moved MOVED_M or tipped MOVED_TILT since it last stood still, unless the motion's
        Allow lets the hand (or what it holds) touch it, it was let go less than SETTLE_TICKS
        ago, or it moved with what a hand holds (rides in / on it).  A disturbed object is
        reported once, then left to settle for SETTLE_TICKS."""
        rig = self.rig
        held = {h["name"] for h in (getattr(rig, "held", None), getattr(rig, "left_held", None)) if h}
        for n in self._held - held:
            self._let_go[n] = rig.tick
        for n in held - self._held:
            self._held_since[n] = rig.tick
        self._held = held
        near = {o.split(":", 1)[1] for o in getattr(motion, "_mon_near", ()) if o.startswith("object:")} - held
        prev, self._prev = self._prev, {}
        carried_steps = []
        for n in held:
            self._prev[n] = rig.obj_pose(n)[0]
            if n in prev and np.linalg.norm(self._prev[n] - prev[n]) > 0.005:
                carried_steps.append(self._prev[n] - prev[n])
        moved = []
        for n in sorted(near):
            p, q = rig.obj_pose(n)
            self._prev[n] = p
            ref = self._ref.get(n)
            if ref is None or rig.tick - self._let_go.get(n, -SETTLE_TICKS) < SETTLE_TICKS or \
                    (n in prev and any(np.linalg.norm(p - prev[n] - c) < CARRIED_M for c in carried_steps)):
                self._ref[n] = (p, q)
                continue
            d = float(np.linalg.norm(p - ref[0]))
            ang = float(np.degrees(np.arccos(np.clip(np.dot(_up(q), _up(ref[1])), -1.0, 1.0))))
            if d < MOVED_M and ang < MOVED_TILT:
                continue
            self._ref[n] = (p, q)
            if any(n == t or n.startswith(t + "/") for t in self.allow.touch + self.allow.held_on):
                continue
            self._let_go[n] = rig.tick           # rolling on after the knock: not new
            moved.append({"object": n, "moved_m": round(d, 3), "tilt_deg": round(ang, 1)})
        for n in list(self._ref):
            if n not in near:
                del self._ref[n]                 # out of sight (or held): a fresh reference later
        if moved:
            self._pending.append({"tick": rig.tick, "skill": self.skills[-1] if self.skills else None,
                                  "leg": self.leg, "checked": self.allow.checked, "objects": moved})

    def _confirm_disturbances(self, final=False):
        """Log the pending disturbances SETTLE_TICKS old (all of them when ``final``), leaving out
        objects a hand has picked up since: the object being picked moves with the hand before
        the pick declares it held."""
        rig = self.rig
        keep = []
        for rec in self._pending:
            if not final and rig.tick - rec["tick"] < SETTLE_TICKS:
                keep.append(rec)
                continue
            rec["objects"] = [o for o in rec["objects"]
                              if self._held_since.get(o["object"], -1) < rec["tick"]]
            if not rec["objects"]:
                continue
            n = len(rec["objects"])
            self.counts["disturbed"] += n
            for key, k in (("disturbed_by_skill", rec["skill"] or "-"), ("disturbed_by_leg", rec["leg"] or "-")):
                self.counts[key][k] = self.counts[key].get(k, 0) + n
            if len(self.disturbances) < MAX_RECORDS:
                self.disturbances.append(rec)
            rig.log("disturbed_object", at_tick=rec["tick"], **{k: v for k, v in rec.items() if k != "tick"})
        self._pending = keep

    def summary(self):
        """result.json ``contacts``."""
        self._confirm_disturbances(final=True)
        return {**self.counts, "records": self.records, "fallbacks": self.fallbacks,
                "disturbances": self.disturbances}
