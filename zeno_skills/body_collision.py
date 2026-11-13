"""The arms against the robot's own base (docs/MOTION_ARCHITECTURE.md 4.4): one more world-collision term in
cuRobo's optimisation and feasibility, inside the planner -- not a check after it.

The base (chassis and column) has no collision spheres: the robot model's sphere and self-collision budgets
are spent (305 robot spheres + the held ones of 512; 16271 of the fast self-collision kernel's 16384 pairs,
the general kernel too slow).  So the base is a second environment of the one world checker
(scene_geometry.BODY_ENV, its two layers rigid with the base: place_body), and every rollout that queries the
world queries it once more: the robot spheres with the body's switched off (BODY_LINKS: the torso rides on the
column and the head comes down over it, they would always touch it) and the other arm's (fixed during this
arm's plan; it is checked when it moves) are left out of that query: only this arm's spheres and its
load's are taken (index_select), not the whole set copied with radii switched off (+3.8 GB per simulation,
T29 several 11-12).  What the hand holds is
a sphere set on its held link: checked against the base like the arm.

install() patches ArmBase.cost_fn / constraint_fn once; attach(rollouts, side) gives each rollout that has a
world-collision cost or constraint its own pair of terms (same configuration: the checker, the weight, the
activation distance, the sweep) -- before the solvers' CUDA graphs are captured (motion._Arm, before warmup).
"""

from __future__ import annotations

from .tolerances import BODY_GAP

BODY_LINKS = ("torso_lift_link", "torso_link", "head_yaw_link", "head_link", "stereo_camera_link")

_installed = False


def off_links(link_names, side):
    """The links whose spheres are not checked against the base in ``side``'s arm model: the body, and
    every link of the other arm (its hand, its fingers, its held link)."""
    other = "left" if side == "right" else "right"
    return {n for n in link_names if n in BODY_LINKS or n.startswith(other + "_")}   # (its held link: {other}_held_object)


def _mask(robot_model, side):
    """(n,) bool on the device: the spheres off_links switches off.  ``robot_model``: a kinematics
    config (CudaRobotModel.kinematics_config: the link and sphere index maps)."""
    import torch
    by_idx = {v: k for k, v in robot_model.link_name_to_idx_map.items()}
    idx = robot_model.link_sphere_idx_map.cpu().tolist()
    off = off_links(set(by_idx.values()), side)
    return torch.tensor([by_idx.get(int(i)) in off for i in idx], dtype=torch.bool,
                        device=robot_model.link_sphere_idx_map.device)


def masked(spheres, mask):
    """``spheres`` (..., n, 4) with the radius of each sphere in ``mask`` set to -1 (cuRobo skips it);
    differentiable for the rest."""
    import torch
    r = torch.where(mask.view(*([1] * (spheres.dim() - 2)), -1), torch.full_like(spheres[..., 3], -1.0),
                    spheres[..., 3])
    return torch.cat([spheres[..., :3], r.unsqueeze(-1)], dim=-1)


def kept(mask):
    """The sphere indices the base is checked against: those ``mask`` does not switch off (this arm, its
    hand, its load) -- a long tensor on the mask's device."""
    import torch
    return torch.nonzero(~mask).view(-1)


def _query(term, keep, spheres):
    """The base term over the kept spheres only (index_select: no copy of the whole set, a smaller query)."""
    import torch
    from .scene_geometry import BODY_ENV
    env = torch.full((spheres.shape[0],), BODY_ENV, dtype=torch.int32, device=spheres.device)
    return term.forward(spheres.index_select(-2, keep), env_query_idx=env)


def install():
    """Patch ArmBase.cost_fn / constraint_fn (idempotent): a rollout with ``_zb_body`` adds its terms."""
    global _installed
    if _installed:
        return
    from curobo.rollout.arm_base import ArmBase
    from curobo.util.tensor_util import cat_sum, cat_sum_horizon
    cost_fn, constraint_fn = ArmBase.cost_fn, ArmBase.constraint_fn

    def body_cost_fn(self, state, action_batch=None, return_list=False):
        body = getattr(self, "_zb_body", None)
        # as the world term it goes with: on while that is on
        if body is None or body.get("cost") is None or not self.primitive_collision_cost.enabled:
            return cost_fn(self, state, action_batch, return_list)
        out = cost_fn(self, state, action_batch, return_list=True)
        out.append(_query(body["cost"], body["keep"], state.robot_spheres))
        if return_list:
            return out
        return cat_sum_horizon(out) if self.sum_horizon else cat_sum(out)

    def body_constraint_fn(self, state, out_metrics=None, use_batch_env=True):
        out = constraint_fn(self, state, out_metrics, use_batch_env)
        body = getattr(self, "_zb_body", None)
        if body is not None and body.get("constraint") is not None and self.primitive_collision_constraint.enabled:
            out.constraint = out.constraint + _query(body["constraint"], body["keep"], state.robot_spheres)
            out.feasible = out.constraint == 0.0
        return out

    ArmBase.cost_fn, ArmBase.constraint_fn = body_cost_fn, body_constraint_fn
    _installed = True


def attach(rollouts, side):
    """Give each rollout that queries the world its pair of base terms (install() first).  Rollouts with
    no world (a kinematic IK) get none.  How many got them."""
    from curobo.rollout.cost.primitive_collision_cost import PrimitiveCollisionCost
    n = 0
    for r in rollouts:
        cost_cfg = getattr(getattr(r, "cost_cfg", None), "primitive_collision_cfg", None)
        con_cfg = getattr(getattr(r, "constraint_cfg", None), "primitive_collision_cfg", None)
        if (cost_cfg is None or cost_cfg.world_coll_checker is None) and \
                (con_cfg is None or con_cfg.world_coll_checker is None):
            continue
        terms = {k: PrimitiveCollisionCost(c) if c is not None and c.world_coll_checker else None
                 for k, c in (("cost", cost_cfg), ("constraint", con_cfg))}
        for t in terms.values():           # never touched: BODY_GAP more than the world term's activation
            if t is not None:
                t.activation_distance = t.activation_distance + BODY_GAP
        r._zb_body = {**terms, "keep": kept(_mask(r.dynamics_model.robot_model.kinematics_config, side))}
        n += 1
    return n
