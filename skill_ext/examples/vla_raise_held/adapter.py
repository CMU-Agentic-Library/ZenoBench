"""VLA adapter template: observation (head image + prompt) -> one ee_delta action."""
import json
import urllib.request


class VLAAdapter:
    def __init__(self, config):
        self.backend = config.get("backend", "mock")
        self.url = config.get("url")
        self.prompt_t = config.get("prompt", "{instruction}")
        self.n = 0

    def reset(self, instruction, args):
        self.prompt = self.prompt_t.format(instruction=instruction, **{k: v for k, v in args.items() if v})
        self.n = 0

    def act(self, obs):
        self.n += 1
        if self.backend == "mock":
            return {"terminate": True} if self.n > 3 else {"ee_delta": [0.0, 0.0, 0.015]}
        image = next((i.get("png_base64") for i in obs.get("images", []) if i.get("camera") == "head"), None)
        body = json.dumps({"prompt": self.prompt, "image_png_base64": image, "proprio": obs.get("proprio")}).encode()
        req = urllib.request.Request(self.url, body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
