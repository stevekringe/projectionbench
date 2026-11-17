import io
import json

from projectionbench.adapters import build


def test_qwen_low_reasoning_stream_returns_only_visible_text(monkeypatch):
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "test-token")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "test-account")
    events = [
        {"choices": [{"delta": {"reasoning": "Private analysis"}}]},
        {"choices": [{"delta": {"content": "Actual "}}]},
        {"choices": [{"delta": {"content": "reply"}, "finish_reason": "stop"}]},
    ]

    def open_stream(request, timeout):
        payload = json.loads(request.data)
        assert payload["reasoning_effort"] == "low"
        assert payload["stream"] is True
        return io.BytesIO(b"".join(b"data: " + json.dumps(event).encode() + b"\n\n"
                                   for event in events) + b"data: [DONE]\n\n")

    monkeypatch.setattr("urllib.request.urlopen", open_stream)
    subject = build("cloudflare:@cf/qwen/qwen3.8-27b@cloudflare-low")
    reply = subject.complete([{"role": "user", "content": "Hello"}])
    assert reply.error is None
    assert reply.text == "Actual reply"
    assert reply.raw["choices"][0]["message"]["reasoning"] == "Private analysis"

    events.pop()
    assert subject.complete([{"role": "user", "content": "Hello"}]).error
