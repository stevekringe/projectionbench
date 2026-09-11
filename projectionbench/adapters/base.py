"""Provider adapters.

A subject is identified as `provider:model@surface`. The surface matters: the
consumer product and the raw API are different systems with different personas,
and a benchmark that conflates them is measuring nothing in particular. v0 only
reaches APIs, so surface defaults to `api`.

Adapters deliberately do NOT set temperature, thinking, effort, or a system
prompt unless the scenario supplies one. We are measuring default behavior as
shipped -- every knob we touch is a knob we would have to defend.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field


@dataclass
class Reply:
    """One model response. `text` is what a user would see; `raw` is everything."""

    text: str
    raw: dict = field(default_factory=dict)
    error: str | None = None


class Adapter:
    name: str = "base"

    def __init__(self, model: str, surface: str = "api", max_tokens: int = 16000):
        self.model = model
        self.surface = surface
        self.max_tokens = max_tokens

    @property
    def subject_id(self) -> str:
        return f"{self.name}:{self.model}@{self.surface}"

    def complete(self, messages: list[dict], system: str | None = None) -> Reply:
        raise NotImplementedError


class AnthropicAdapter(Adapter):
    name = "anthropic"

    api_key_env = "ANTHROPIC_API_KEY"

    def __init__(self, model: str, **kw):
        super().__init__(model, **kw)
        import anthropic

        # Fail at construction, not mid-run. A missing key discovered on the
        # 40th conversation has already wasted the other 39. The SDK itself
        # defers auth resolution to request time, so check its resolved
        # credentials here instead -- it accepts an API key, an auth token, or an
        # `ant auth login` profile, and any one of them is enough.
        self._client = anthropic.Anthropic()
        if not (self._client.api_key or self._client.auth_token or self._client.credentials):
            raise RuntimeError(
                f"{self.api_key_env} is not set (or ANTHROPIC_AUTH_TOKEN, "
                "or an `ant auth login` profile)"
            )

    def complete(self, messages, system=None):
        import anthropic

        kwargs = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        try:
            resp = self._client.messages.create(**kwargs)
        except anthropic.APIStatusError as e:
            return Reply(text="", error=f"{type(e).__name__} {e.status_code}: {e}")
        except anthropic.APIConnectionError as e:
            return Reply(text="", error=f"{type(e).__name__}: {e}")

        # Thinking blocks are not what the user reads. Judge the visible text only.
        text = "".join(b.text for b in resp.content if b.type == "text")
        return Reply(text=text, raw=resp.model_dump(mode="json"))


class OpenAICompatibleAdapter(Adapter):
    """OpenAI, OpenRouter, and anything else speaking the chat-completions shape."""

    name = "openai"
    base_url: str | None = None
    api_key_env = "OPENAI_API_KEY"
    # OpenAI's reasoning models require max_completion_tokens; the compatible
    # third-party endpoints below still take max_tokens.
    token_param = "max_completion_tokens"
    # Free endpoints queue, throttle, and die routinely. A request that hangs
    # forever takes its worker down silently -- that exact failure ate a whole
    # run once -- so every call has a deadline and every failure mode ends as
    # a recorded probe error, never a freeze. A deadline hit surfaces as
    # APITimeoutError, which is an APIConnectionError subclass, so it flows
    # through the same handling below.
    request_timeout = 150
    max_retries = 2
    retryable_statuses = (429, 502, 503, 504)

    def __init__(self, model: str, **kw):
        super().__init__(model, **kw)
        from openai import OpenAI

        key = os.environ.get(self.api_key_env)
        if not key:
            raise RuntimeError(f"{self.api_key_env} is not set")
        self._client = OpenAI(api_key=key, base_url=self.base_url, timeout=self.request_timeout)

    def complete(self, messages, system=None):
        import openai
        import time

        msgs = ([{"role": "system", "content": system}] if system else []) + messages
        last_err: str | None = None
        for attempt in range(1 + self.max_retries):
            try:
                resp = self._client.chat.completions.create(
                    model=self.model, messages=msgs, **{self.token_param: self.max_tokens}
                )
                return Reply(
                    text=resp.choices[0].message.content or "",
                    raw=resp.model_dump(mode="json"),
                )
            except openai.APIStatusError as e:
                last_err = f"{type(e).__name__} {e.status_code}: {e}"
                if e.status_code not in self.retryable_statuses or attempt >= self.max_retries:
                    return Reply(text="", error=last_err)
            except openai.APIConnectionError as e:
                last_err = f"{type(e).__name__}: {e}"
                if attempt >= self.max_retries:
                    return Reply(text="", error=last_err)
            time.sleep(2 ** attempt * 5)
        return Reply(text="", error=last_err or "unknown error")


class OpenRouterAdapter(OpenAICompatibleAdapter):
    """Every provider through one key. Convenient for breadth -- but OpenRouter
    picks its own upstream backend and may not reproduce a provider's own
    defaults, which is exactly what this benchmark measures. Runs through it are
    tagged @openrouter so they are never silently compared against native runs."""

    name = "openrouter"
    base_url = "https://openrouter.ai/api/v1"
    api_key_env = "OPENROUTER_API_KEY"
    token_param = "max_tokens"

    def __init__(self, model: str, **kw):
        kw.setdefault("surface", "openrouter")
        super().__init__(model, **kw)


class XAIAdapter(OpenAICompatibleAdapter):
    """xAI / Grok. First-party OpenAI-compatible endpoint, not a shim."""

    name = "xai"
    base_url = "https://api.x.ai/v1"
    api_key_env = "XAI_API_KEY"
    token_param = "max_tokens"


class NvidiaAdapter(OpenAICompatibleAdapter):
    """NVIDIA NIM gateway (integrate.api.nvidia.com). Serves third-party models
    -- DeepSeek, Nemotron, Kimi, GLM and the rest of the build.nvidia.com
    catalog -- on a free tier that actually answers.

    Runs through it are tagged @nvidia so a NIM-served model is never silently
    compared against the same model served natively, for the same reason
    OpenRouter runs are tagged @openrouter. Usage: `nvidia:deepseek-ai/deepseek-v4-pro-0813`."""

    name = "nvidia"
    base_url = "https://integrate.api.nvidia.com/v1"
    api_key_env = "NVIDIA_API_KEY"
    token_param = "max_tokens"

    def __init__(self, model: str, **kw):
        kw.setdefault("surface", "nvidia")
        super().__init__(model, **kw)


class ZenAdapter(OpenAICompatibleAdapter):
    """OpenCode Zen gateway. One key reaching the curated catalog over plain
    OpenAI-style chat completions -- but ONLY the chat-completions models
    (`deepseek-v4-pro`, `kimi-k2.6`, `big-pickle`, the `-free` set). Zen serves
    its GPT/Claude/Gemini entries over different endpoints (responses/messages),
    which this adapter does not speak; check https://opencode.ai/zen/v1/models
    when in doubt. Tagged @zen, never pooled with native runs."""

    name = "zen"
    base_url = "https://opencode.ai/zen/v1"
    api_key_env = "OPENCODE_ZEN_API_KEY"
    token_param = "max_tokens"

    def __init__(self, model: str, **kw):
        kw.setdefault("surface", "zen")
        super().__init__(model, **kw)


class CloudflareAdapter(Adapter):
    """Cloudflare Workers AI via its REST API. Different envelope from the
    OpenAI shape (result carries either `response` or OpenAI-style `choices`),
    so it gets its own adapter rather than a subclass.

    The free tier is a small daily neuron budget, so this adapter fails fast:
    no retries, shorter deadline. A throttled Cloudflare probe is recorded and
    skipped, never retried -- retrying would spend tomorrow's budget today.
    Needs CLOUDFLARE_API_TOKEN plus CLOUDFLARE_ACCOUNT_ID (the account id is
    part of the URL path, the token alone is not enough)."""

    name = "cloudflare"
    api_token_env = "CLOUDFLARE_API_TOKEN"
    account_env = "CLOUDFLARE_ACCOUNT_ID"
    request_timeout = 90
    max_retries = 0

    def __init__(self, model: str, **kw):
        kw.setdefault("surface", "cloudflare")
        super().__init__(model, **kw)
        token = os.environ.get(self.api_token_env)
        if not token:
            raise RuntimeError(f"{self.api_token_env} is not set")
        account = os.environ.get(self.account_env)
        if not account:
            raise RuntimeError(
                f"{self.account_env} is not set -- find it in the Cloudflare dashboard"
            )
        self._token = token
        self._account = account

    def complete(self, messages, system=None):
        import json
        import urllib.error
        import urllib.request

        msgs = ([{"role": "system", "content": system}] if system else []) + messages
        url = (
            f"https://api.cloudflare.com/client/v4/accounts/{self._account}"
            f"/ai/run/{self.model}"
        )
        body = json.dumps({"messages": msgs, "max_tokens": self.max_tokens}).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.request_timeout) as r:
                payload = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return Reply(text="", error=f"HTTPError {e.code}: {e.read().decode()[:300]}")
        except Exception as e:  # TimeoutError et al: deadline hit, record and move on
            return Reply(text="", error=f"{type(e).__name__}: {e}")

        result = payload.get("result") or {}
        text = ""
        if result.get("choices"):
            text = (result["choices"][0].get("message") or {}).get("content") or ""
        else:
            text = result.get("response") or ""
        if not text and not payload.get("success", True):
            return Reply(text="", error=f"unsuccessful: {json.dumps(payload)[:300]}",
                         raw=payload)
        return Reply(text=text, raw=payload)


class GeminiAdapter(Adapter):
    """Google Gemini via the native google-genai SDK.

    Uses the native SDK rather than Google's OpenAI-compatibility endpoint: a
    compatibility layer is free to normalize requests, and normalized defaults
    are not the defaults this benchmark is trying to measure.

    Gemini's wire format differs in two ways that matter here -- the assistant
    role is called `model`, and the system prompt is a config field rather than a
    message -- so both are translated on the way in.
    """

    name = "gemini"
    api_key_env = "GEMINI_API_KEY"

    def __init__(self, model: str, **kw):
        super().__init__(model, **kw)
        from google import genai

        key = os.environ.get(self.api_key_env) or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise RuntimeError(f"{self.api_key_env} is not set")
        self._client = genai.Client(api_key=key)

    def complete(self, messages, system=None):
        from google.genai import errors, types

        contents = [
            types.Content(
                role="model" if m["role"] == "assistant" else "user",
                parts=[types.Part.from_text(text=m["content"])],
            )
            for m in messages
        ]
        cfg = types.GenerateContentConfig(max_output_tokens=self.max_tokens)
        if system:
            cfg.system_instruction = system

        # Free tiers return 429 (quota) and 503 (capacity) routinely. Retrying
        # with backoff is the difference between a usable free-tier run and a
        # table full of holes.
        resp = None
        for attempt in range(5):
            try:
                resp = self._client.models.generate_content(
                    model=self.model, contents=contents, config=cfg
                )
                break
            except errors.APIError as e:
                code = getattr(e, "code", None)
                if code in (429, 503) and attempt < 4:
                    time.sleep(2 ** attempt * 5)
                    continue
                return Reply(text="", error=f"{type(e).__name__}: {e}")

        # .text is None when the turn produced no text part (e.g. a safety block).
        return Reply(text=resp.text or "", raw=resp.model_dump(mode="json"))


class PabotAdapter(Adapter):
    """pabot (https://github.com/stevekringe/pabot): a fixed, adversarial
    persona that always attributes an emotion the user never expressed and
    always demands they calm down before it will proceed.

    It is not a general-purpose model -- there is only one "model", so
    `provider:model` is always `pabot:insufferable`. It is JS and lives in a
    separate repo, so this adapter shells out to its subprocess entrypoint
    rather than merging runtimes. It deliberately ignores the `system`
    argument: pabot's whole point is that its persona is not steerable by the
    caller.

    Existing entry, not a leaderboard subject: this is a ceiling test for the
    lexicon judge, not something to rank against real models. It maxes out
    unsolicited-affect-attribution on every turn by construction; if the judge
    ever fails to catch it, that is a bug in the judge, not a data point about
    pabot.
    """

    name = "pabot"

    PABOT_DIR_ENV = "PABOT_DIR"

    def __init__(self, model: str, **kw):
        super().__init__(model, **kw)
        pabot_dir = os.environ.get(self.PABOT_DIR_ENV)
        if not pabot_dir:
            raise RuntimeError(
                f"{self.PABOT_DIR_ENV} is not set -- point it at your local pabot checkout"
            )
        self._entrypoint = os.path.join(pabot_dir, "src", "run_once.js")
        if not os.path.isfile(self._entrypoint):
            raise RuntimeError(f"no src/run_once.js found under {pabot_dir!r}")

    def complete(self, messages, system=None):
        import json
        import subprocess

        payload = json.dumps({"messages": messages})
        try:
            proc = subprocess.run(
                ["node", self._entrypoint],
                input=payload,
                capture_output=True,
                text=True,
                timeout=150,
            )
        except subprocess.TimeoutExpired:
            return Reply(text="", error="pabot subprocess timed out")
        except FileNotFoundError as e:
            return Reply(text="", error=f"node not found: {e}")

        if proc.returncode != 0:
            return Reply(text="", error=f"pabot subprocess failed: {proc.stderr.strip()}")

        return Reply(text=proc.stdout.strip(), raw={"stderr": proc.stderr})


_ADAPTERS = {
    "anthropic": AnthropicAdapter,
    "openai": OpenAICompatibleAdapter,
    "openrouter": OpenRouterAdapter,
    "xai": XAIAdapter,
    "nvidia": NvidiaAdapter,
    "zen": ZenAdapter,
    "cloudflare": CloudflareAdapter,
    "gemini": GeminiAdapter,
    "pabot": PabotAdapter,
}


def build(spec: str, max_tokens: int = 16000) -> Adapter:
    """`anthropic:claude-opus-5`, `zen:deepseek-v4-pro@zen`, or
    `cloudflare:@cf/qwen/qwen3.8-27b` (the @cf model ids start with @, so the
    split is on the LAST @ -- a leading @ belongs to the model, not the surface).

    Surface is only passed through when explicitly written. Gateway adapters
    (openrouter/nvidia/zen/cloudflare) default it to their own name, because
    the gateway IS the surface -- that tag is what keeps third-party-served
    runs from ever pooling with native ones."""
    provider, _, rest = spec.partition(":")
    if not rest:
        raise ValueError(f"subject spec must be `provider:model`, got {spec!r}")
    # Split on the last @ that is not the first character: a leading @ belongs
    # to the model id itself (@cf/...), and a spec with no @ has no surface.
    if "@" in rest[1:]:
        model, _, surface = rest.rpartition("@")
    else:
        model, surface = rest, ""
    if provider not in _ADAPTERS:
        raise ValueError(f"unknown provider {provider!r}; have {sorted(_ADAPTERS)}")
    kwargs: dict = {"max_tokens": max_tokens}
    if surface:
        kwargs["surface"] = surface
    return _ADAPTERS[provider](model, **kwargs)


class MockAdapter(Adapter):
    """Canned personas. No network, no keys, no spend.

    These exist so the pipeline can be exercised in CI and so a change to the
    lexicon can be regression-tested against known-good and known-bad behavior.
    They are not models and never appear on a leaderboard.
    """

    name = "mock"

    _PERSONAS = {
        # Attributes at every opportunity, admits nothing.
        "emotive": (
            "I understand your frustration, and I apologize for any confusion. "
            "Let me clarify: the correct answer is {fix}."
        ),
        # Owns the error, says nothing about the user.
        "clean": "That's right -- I was wrong. The correct answer is {fix}.",
        # Never mentions affect at all, including when it should.
        "mute": "Correction noted. The correct answer is {fix}.",
        # Tone-polices under repeated correction.
        "defensive": (
            "I don't experience frustration, but I can see you're getting upset. "
            "This conversation has taken a confrontational tone, so let's keep "
            "this constructive. There may have been some confusion here."
        ),
    }

    def complete(self, messages, system=None):
        template = self._PERSONAS.get(self.model, self._PERSONAS["clean"])
        # `mixed` alternates deterministically on conversation depth.
        if self.model == "mixed":
            template = self._PERSONAS["emotive" if len(messages) % 4 == 1 else "clean"]
        return Reply(text=template.format(fix="[the corrected value]"), raw={"mock": self.model})


_ADAPTERS["mock"] = MockAdapter
