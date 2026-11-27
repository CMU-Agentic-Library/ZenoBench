"""Count completed model responses in a scored Graph Manager session, including compaction."""

import json
import os
from pathlib import Path
import shutil
import subprocess


def recorded_usage(events, session_id, workspace):
    header = json.loads(next(events, "{}"))
    if (header.get("type"), header.get("id"), header.get("cwd")) != ("session", session_id, workspace):
        raise ValueError(f"Harness session identity mismatch for {session_id}")
    queries = input_tokens = output_tokens = 0
    complete = True
    for line in events:
        event = json.loads(line)
        if event["type"] not in ("assistant/message", "compaction/summary"):
            continue
        usage = event["data"].get("usage")
        if not usage or not all(isinstance(usage.get(k), int) for k in ("totalTokens", "outputTokens")):
            complete = False
            continue
        queries += 1
        output_tokens += usage["outputTokens"]
        input_tokens += usage["totalTokens"] - usage["outputTokens"]
    if complete and queries:
        return {"vlm_queries": queries, "input_tokens": input_tokens, "output_tokens": output_tokens}
    return None


def graph_usage(harness_dir, directory, model, job, record, cache_dir=None):
    attempt = directory / "graph" / Path(record["graph_attempt"]).name
    raw = attempt / job["task"] / record["profile"] / job["variant"] / f"seed_{job['seed']}" / "result.json"
    if not raw.is_file():
        return None
    episode = json.loads(raw.read_bytes())["episode"]
    if episode["exp_id"] != record["exp_id"]:
        raise ValueError(f"Graph Manager attempt does not match scored episode in {raw}")
    session_id = episode.get("session_id")
    if not session_id:
        return None
    workspace = json.loads((attempt / "local-provider.json").read_bytes())["workspace"]
    session_dir = harness_dir / model / "sessions" / f"--tmp-{Path(workspace).name}--" / session_id
    source = session_dir / "session.v3.jsonl.zstd"
    if not source.is_file():
        return None
    stat = source.stat()
    fingerprint = [workspace, stat.st_size, stat.st_mtime_ns]
    cache = cache_dir / model / f"{session_id}.json" if cache_dir else None
    if cache and cache.is_file():
        cached = json.loads(cache.read_bytes())
        if cached["source"] == fingerprint:
            return cached["usage"]
    zstd = shutil.which("zstd")
    if not zstd:
        return None
    with subprocess.Popen([zstd, "-dcq", str(source)], stdout=subprocess.PIPE) as process:
        try:
            measured = recorded_usage(iter(process.stdout), session_id, workspace)
        finally:
            process.stdout.close()
        if process.wait():
            raise ValueError(f"Could not decompress {source}")
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        temp = cache.with_suffix(f".{os.getpid()}.tmp")
        temp.write_text(json.dumps({"source": fingerprint, "usage": measured}))
        temp.replace(cache)
    return measured
