"""Task-level temperature dynamics for food in a closed microwave."""


class ThermalModel:
    def __init__(self, config, appliance="kitchen_microwave"):
        self.config = config
        self.appliance = appliance
        self.temperatures_c = {name: float(v["initial_c"]) for name, v in config.items()}
        self.active = False

    def advance(self, dt, objects_inside, door_closed):
        if not door_closed:
            self.active = False
        if not self.active or not door_closed:
            return
        for name in objects_inside:
            if name in self.config:
                self.temperatures_c[name] += float(self.config[name]["heating_rate_c_per_s"]) * dt
