"""Check which baseline models are configured and answer: one tiny text request per model.

    $ISAACLAB_PYTHON -m baseline.check_models                       # the default four
    $ISAACLAB_PYTHON -m baseline.check_models claude-opus-5-5 gpt-5.5

A model whose key / server is missing is reported, not called.  Each real call is a few tokens.
"""

from __future__ import annotations

import os
import sys

from baseline.vlm import load_env, make_client

DEFAULT = ["qwen3.5-4b", "claude-opus-5-5", os.environ.get("SHIFT_GPT_MODEL", "gpt-5.5"),
           os.environ.get("SHIFT_GEMINI_MODEL", "gemini-3-pro")]
NEEDS = {"claude": "ANTHROPIC_API_KEY", "gpt": "OPENAI_API_KEY", "gemini": "GEMINI_API_KEY"}


def main(models):
    load_env()
    bad = 0
    for m in models:
        key = next((v for k, v in NEEDS.items() if m.lower().startswith(k)), None)
        if key and not os.environ.get(key):
            print(f"{m:24s} NOT CONFIGURED  set {key} (shell or baseline/.env)")
            bad += 1
            continue
        try:
            text, u = make_client(m).chat("Answer with one word.", 'Reply with the JSON {"ok": true} and nothing else.')
            print(f"{m:24s} OK  {text.strip()[:40]!r}  in={u['input_tokens']} out={u['output_tokens']} "
                  f"{u['latency_s']}s")
        except Exception as exc:                                   # noqa: BLE001
            print(f"{m:24s} FAILED  {type(exc).__name__}: {str(exc)[:160]}")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or DEFAULT))
