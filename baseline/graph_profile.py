"""Record the local endpoint's actual context and output limits for the pinned Harness."""

import hashlib
import json
from pathlib import Path

import yaml


def configure(patch_path, attempt):
    patch_path = Path(patch_path)
    patch = yaml.safe_load(patch_path.read_text())
    provider = next(entry for entry in patch if entry["id"] == "llm-pi-ai")["config"]["providers"]["lab-vlm"]
    model, = provider["models"]
    model.update(contextWindow=32768, maxTokens=4096)
    data = yaml.safe_dump(patch, sort_keys=False).encode()
    patch_path.write_bytes(data)
    receipt = {"model": model["id"], "context_window": model["contextWindow"], "max_tokens": model["maxTokens"],
               "patch_sha256": hashlib.sha256(data).hexdigest()}
    (Path(attempt) / "local-provider.json").write_text(json.dumps(receipt, indent=2) + "\n")
