"""Scripted closed-loop policy: raise the TCP by ``height_m`` in steps of at most 2 cm."""


class RaiseHeld:
    def __init__(self, config):
        self.step_m = float(config.get("step_m", 0.02))
        self.z_goal = None

    def reset(self, instruction, args):
        self.height = float(args.get("height_m") or 0.06)
        self.z_goal = None

    def act(self, obs):
        z = obs["proprio"]["tcp_pos"][2]
        if self.z_goal is None:
            self.z_goal = z + self.height
        dz = self.z_goal - z
        if dz < 0.005:
            return {"terminate": True}
        return {"ee_delta": [0.0, 0.0, min(self.step_m, dz)]}
