"""Linear policy a = W @ [dz_to_goal, 1] (numpy), the minimal RL executor template."""
import json
from pathlib import Path

import numpy as np


class LinearPolicy:
    def __init__(self, config):
        w = json.loads((Path(config["base_dir"]) / config["weights"]).read_text())
        self.W = np.asarray(w["W"], float)
        self.goal = float(w["goal_dz_m"])
        self.done_tol = float(w["done_tol_m"])

    def reset(self, instruction, args):
        self.z0 = None

    def act(self, obs):
        z = obs["proprio"]["tcp_pos"][2]
        self.z0 = z if self.z0 is None else self.z0
        err = self.goal - (z - self.z0)
        if err < self.done_tol:
            return {"terminate": True}
        a = self.W @ np.array([err, 1.0])
        return {"ee_delta": [float(a[0]), float(a[1]), float(a[2])]}
