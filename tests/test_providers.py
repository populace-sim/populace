"""The provider layer, tested without a model anywhere.

The local provider is exercised against a stdlib HTTP server that speaks just
enough of the OpenAI protocol, so these tests run on a laptop with no mlx, in
CI, or in a cloud session with no GPU.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from populace.config import Config
from populace.observe.telemetry import Telemetry
from populace.providers import mock as M
from populace.providers.costs import Meter, ProviderDown, ValidationAlarm
from populace.providers.runner import ModelRunner

SYSTEM = [{"type": "text", "text": "RULES"}, {"type": "text", "text": "YOU ARE SAM"}]
USER = [{"role": "user", "content": "What do you do?"}]


def _runner(tmp_path, config=None, **kw):
    config = config or Config.build("laptop")
    return ModelRunner(config, Meter(config), Telemetry(tmp_path, run_id="t"), **kw)


@pytest.fixture
def echo_handler():
    # Put back whatever was registered before (the mock brain, once any test
    # has imported it), not nothing: later tests' mock towns need it.
    before = M._HANDLERS.get("npc_decision")

    @M.handler("npc_decision")
    def _decide(rng, state, meta):
        return {"action": "wait", "roll": rng.random(), "where": state.get("where")}
    yield
    if before is None:
        M._HANDLERS.pop("npc_decision", None)
    else:
        M._HANDLERS["npc_decision"] = before


async def test_the_mock_is_deterministic_per_call_key(tmp_path, echo_handler):
    meta = {"char_id": "sam", "day": 1, "tick": 3, "mock_state": {"where": "cafe"},
            "mock_no_garbage": True}
    a = await _runner(tmp_path, mock=True, seed=7).call("npc_decision", SYSTEM, USER, meta)
    b = await _runner(tmp_path, mock=True, seed=7).call("npc_decision", SYSTEM, USER, meta)
    c = await _runner(tmp_path, mock=True, seed=8).call("npc_decision", SYSTEM, USER, meta)
    assert a.text == b.text != c.text
    assert json.loads(a.text)["where"] == "cafe"


async def test_the_mock_sometimes_answers_garbage_on_purpose(tmp_path, echo_handler):
    runner = _runner(tmp_path, mock=True, seed=1, garbage_rate=0.5)
    texts = [
        (await runner.call("npc_decision", SYSTEM, USER,
                           {"char_id": "sam", "day": 1, "tick": t})).text
        for t in range(40)
    ]
    bad = [t for t in texts if t in M.GARBAGE]
    assert 5 < len(bad) < 35


async def test_every_call_is_counted_and_logged_with_its_prompt(tmp_path, echo_handler):
    runner = _runner(tmp_path, mock=True)
    await runner.call("npc_decision", SYSTEM, USER, {"char_id": "sam", "day": 1, "tick": 0})
    await runner.call("npc_decision", SYSTEM, USER, {"char_id": "jo", "day": 1, "tick": 0})
    assert runner.meter.calls_by_role["npc_decision"] == 2
    calls = runner.telemetry.read_stream("calls")
    systems = runner.telemetry.read_stream("systems")
    assert [c["char_id"] for c in calls] == ["sam", "jo"]
    assert calls[0]["prompt"] == USER
    assert len(systems) == 1 and systems[0]["blocks"] == ["RULES", "YOU ARE SAM"]


def test_the_validation_alarm_counts_a_window_not_one_bad_reply():
    config = Config.build("laptop", {"engine": {"validation_alarm_window": 10,
                                                "validation_alarm_frac": 0.3}})
    meter = Meter(config)
    for ok in [False, False, False] + [True] * 7:
        meter.note_validation(ok)
    with pytest.raises(ValidationAlarm):
        for _ in range(4):
            meter.note_validation(False)


def test_provider_down_is_a_run_on_one_provider():
    """A success on another provider says nothing about this one."""
    config = Config.build("laptop", {"engine": {"provider_down_after": 3}})
    meter = Meter(config)
    meter.note_transport(False, "local")
    meter.note_transport(False, "local")
    meter.note_transport(True, "other")
    with pytest.raises(ProviderDown):
        meter.note_transport(False, "local")


class _FakeOpenAI(BaseHTTPRequestHandler):
    seen: list[dict] = []
    reply = '{"action": "wait"}'

    def do_POST(self):  # noqa: N802 - stdlib name
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).seen.append({"body": body, "auth": self.headers.get("Authorization")})
        out = {
            "id": "x1", "object": "chat.completion", "created": 0, "model": body["model"],
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": type(self).reply}}],
            "usage": {"prompt_tokens": 120, "completion_tokens": 6, "total_tokens": 126,
                      "prompt_tokens_details": {"cached_tokens": 100}},
        }
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def fake_server():
    _FakeOpenAI.seen = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeOpenAI)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    server.shutdown()


async def test_the_local_provider_speaks_the_openai_protocol(tmp_path, fake_server, monkeypatch):
    monkeypatch.delenv("POPULACE_API_KEY", raising=False)
    config = Config.build("laptop", {
        "providers": {"local": {"base_url": fake_server}},
        "roles": {"npc_decision": {"extra_body": {"lora": [{"id": 0, "scale": 1.0}]}}},
    })
    runner = _runner(tmp_path, config=config)
    result = await runner.call("npc_decision", SYSTEM, USER, {"char_id": "sam"})
    await runner.aclose()
    assert result.ok and result.text == '{"action": "wait"}'
    assert (result.usage.input_tokens, result.usage.cache_read_tokens) == (20, 100)
    sent = _FakeOpenAI.seen[0]
    # The system blocks arrive as one system message, in order, so the
    # server's prefix cache sees the same prefix on every call.
    assert sent["body"]["messages"][0] == {"role": "system", "content": "RULES\n\nYOU ARE SAM"}
    assert sent["body"]["lora"] == [{"id": 0, "scale": 1.0}]
    # Nothing that looks like a real key ever leaves the machine.
    assert sent["auth"] == "Bearer not-needed"


async def test_a_server_that_is_not_there_is_an_error_result_not_a_crash(tmp_path):
    config = Config.build("laptop", {
        "providers": {"local": {"base_url": "http://127.0.0.1:9/v1"}},
        "engine": {"request_timeout_s": 2.0},
    })
    runner = _runner(tmp_path, config=config)
    result = await runner.call("npc_decision", SYSTEM, USER, {"char_id": "sam"})
    await runner.aclose()
    assert not result.ok and result.error
    assert runner.telemetry.read_stream("calls")[0]["error"]
