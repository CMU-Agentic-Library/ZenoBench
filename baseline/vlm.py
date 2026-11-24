"""One chat interface over the four model families of the baselines.

    client = make_client("claude-opus-5-5")
    text, usage = client.chat(system, user_text, image_paths)

The backend follows the model name:

* ``claude-*``  - Anthropic SDK (``pip install anthropic``, ANTHROPIC_API_KEY); the system prompt
  (skill menu) is cached.
* ``gpt-*``, ``o<digit>*`` - OpenAI SDK (``pip install openai``, OPENAI_API_KEY).
* ``gemini-*``  - Gemini's OpenAI-compatible endpoint through the OpenAI SDK (GEMINI_API_KEY).
Keys can also come from baseline/.env (template baseline/.env.example, git-ignored).

* anything else (``qwen3.5-4b``) - a local vLLM server through the OpenAI SDK, at SHIFT_VLLM_URL
  (default http://localhost:8001/v1, the port of baseline/graph_manager/examples/vllm-qwen3.5-4b.compose.yml).

Every call is one stateless request (system + one user turn); the planners put the history in the
user turn themselves, so all backends see the same input.  ``usage`` is
{"input_tokens", "output_tokens", "cached_input_tokens", "latency_s"}.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
import time

ENV_FILE = Path(__file__).with_name(".env")          # git-ignored; template: baseline/.env.example
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
VLLM_URL = "http://localhost:8001/v1"


def _png_b64(path) -> str:
    return base64.standard_b64encode(Path(path).read_bytes()).decode()


def _retry(fn, tries=4):
    for k in range(tries):
        try:
            return fn()
        except Exception as exc:                       # rate limits, timeouts, 5xx
            if k == tries - 1 or not _transient(exc):
                raise
            time.sleep(5 * 2 ** k)


def _transient(exc) -> bool:
    status = getattr(exc, "status_code", None)
    name = type(exc).__name__
    return status in (408, 409, 429, 500, 502, 503, 504, 529) or "Timeout" in name or "Connection" in name


class AnthropicClient:
    def __init__(self, model, max_tokens=16000):
        import anthropic
        self.client, self.model, self.max_tokens = anthropic.Anthropic(), model, max_tokens

    def chat(self, system, user_text, image_paths=()):
        content = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": _png_b64(p)}}
                   for p in image_paths]
        content.append({"type": "text", "text": user_text})
        t0 = time.time()

        def call():
            with self.client.messages.stream(
                    model=self.model, max_tokens=self.max_tokens,
                    system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                    messages=[{"role": "user", "content": content}]) as stream:
                return stream.get_final_message()
        msg = _retry(call)
        u = msg.usage
        cached = (getattr(u, "cache_read_input_tokens", 0) or 0)
        written = (getattr(u, "cache_creation_input_tokens", 0) or 0)
        text = "".join(b.text for b in msg.content if b.type == "text")
        return text, {"input_tokens": u.input_tokens + cached + written, "output_tokens": u.output_tokens,
                      "cached_input_tokens": cached, "latency_s": round(time.time() - t0, 2),
                      "stop_reason": msg.stop_reason}


class OpenAICompatClient:
    def __init__(self, model, base_url=None, api_key=None):
        import openai
        self.client = openai.OpenAI(base_url=base_url, api_key=api_key)
        self.model = model

    def chat(self, system, user_text, image_paths=()):
        content = [{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{_png_b64(p)}"}}
                   for p in image_paths]
        content.append({"type": "text", "text": user_text})
        t0 = time.time()
        resp = _retry(lambda: self.client.chat.completions.create(
            model=self.model, messages=[{"role": "system", "content": system},
                                        {"role": "user", "content": content}]))
        u = resp.usage
        details = getattr(u, "prompt_tokens_details", None)
        cached = (getattr(details, "cached_tokens", 0) or 0) if details else 0
        choice = resp.choices[0]
        return choice.message.content or "", {
            "input_tokens": u.prompt_tokens if u else 0, "output_tokens": u.completion_tokens if u else 0,
            "cached_input_tokens": cached, "latency_s": round(time.time() - t0, 2),
            "stop_reason": choice.finish_reason}


def load_env(path=ENV_FILE):
    """KEY=VALUE lines of baseline/.env into os.environ (the shell's own values win; empty ones skipped)."""
    if not Path(path).exists():
        return
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if v and k not in os.environ:
            os.environ[k] = v


def make_client(model: str):
    load_env()
    m = model.lower()
    if m.startswith("claude"):
        return AnthropicClient(model)
    if m.startswith("gpt") or (len(m) > 1 and m[0] == "o" and m[1].isdigit()):
        return OpenAICompatClient(model)
    if m.startswith("gemini"):
        return OpenAICompatClient(model, base_url=GEMINI_URL, api_key=os.environ.get("GEMINI_API_KEY"))
    return OpenAICompatClient(model, base_url=os.environ.get("SHIFT_VLLM_URL", VLLM_URL),
                              api_key=os.environ.get("SHIFT_VLLM_KEY", "EMPTY"))
