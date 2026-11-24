"""Local Harness limits and the working directory exposed in the model's request."""

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml


def configure(patch_path, attempt, workspace=None):
    patch_path = Path(patch_path)
    patch = yaml.safe_load(patch_path.read_text())
    provider = next(entry for entry in patch if entry["id"] == "llm-pi-ai")["config"]["providers"]["lab-vlm"]
    model, = provider["models"]
    model.update(contextWindow=32768, maxTokens=4096)
    data = yaml.safe_dump(patch, sort_keys=False).encode()
    patch_path.write_bytes(data)
    receipt = {"model": model["id"], "context_window": model["contextWindow"], "max_tokens": model["maxTokens"],
               "patch_sha256": hashlib.sha256(data).hexdigest()}
    if workspace is not None:
        receipt["workspace"] = str(workspace)
    (Path(attempt) / "local-provider.json").write_text(json.dumps(receipt, indent=2) + "\n")


@contextmanager
def isolated_workspace(patch_path, attempt):
    # The Harness sends its cwd to the VLM. The artifact directory includes the hidden layout name.
    with TemporaryDirectory(prefix="zenobench-graph-", dir="/tmp") as workspace:
        configure(patch_path, attempt, workspace)
        yield workspace
