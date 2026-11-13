"""Rig.payload_torques: the torques that carry a load held in the hand (11-12, liftdbg_1112)."""
import numpy as np
import pytest

from zeno_skills.kinematics import ArmKin
from zeno_skills.rig import GRAVITY, payload_torques


@pytest.mark.parametrize("side", ["right", "left"])
def test_payload_torques_are_the_gradient_of_the_loads_height(side):
    # virtual work: tau_i = d(m g z_com)/dq_i, the load rigid in the hand (a book held at its edge, its
    # centre 9 cm out along the approach and 1 cm down: the lever an edge pinch hangs on)
    kin = ArmKin(side=side)
    kin.set_base((0.3, -0.2, 0.0), 0.7)
    q = np.array(kin.posture, float) + 0.1
    p, R = kin.tcp(q)
    r_local = R.T @ (R @ np.array([0.0, 0.0, 0.09]) + np.array([0.0, 0.0, -0.01]))
    m = 0.25

    def height(qq):
        pp, RR = kin.tcp(qq)
        return m * GRAVITY * (pp + RR @ r_local)[2]

    tau = payload_torques(kin, q, p + R @ r_local, m)
    eps = 1e-6
    num = np.array([(height(q + eps * e) - height(q - eps * e)) / (2 * eps) for e in np.eye(len(q))])
    assert tau.shape == (len(q),)
    assert np.allclose(tau, num, atol=1e-5)


def test_no_mass_no_torque():
    kin = ArmKin(side="right")
    q = np.array(kin.posture, float)
    assert np.allclose(payload_torques(kin, q, kin.tcp(q)[0], 0.0), 0.0)
