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


def matches_local_protocol(directory, result, model):
    """Whether this attempt used both the served capacity and a layout-independent cwd."""
    if not result.get("graph_attempt"):
        return False
    receipt = directory / "graph" / Path(result["graph_attempt"]).name / "local-provider.json"
    if not receipt.is_file():
        return False
    provider = json.loads(receipt.read_text())
    if (provider["model"], provider["context_window"], provider["max_tokens"]) != (model, 32768, 4096):
        raise ValueError(f"Graph Manager provider configuration mismatch in {receipt}")
    workspace = Path(provider.get("workspace", ""))
    return workspace.parent == Path("/tmp") and workspace.name.startswith("zenobench-graph-")
