"""A hosted OpenAI-compatible API, tested against a stdlib fake: the key from
POPULACE_API_KEY arrives as the Authorization header and nowhere else, even
when the host echoes it back; thinking is turned off per request; and a run
prints and reports what it used."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from populace.config import Config
from populace.observe.telemetry import Telemetry
from populace.providers.costs import Meter
from populace.providers.runner import ModelRunner

KEY = "sk-test-0123456789abcdef-SECRET"
ROOT = Path(__file__).resolve().parents[1]
SYSTEM = [{"type": "text", "text": "RULES"}]
USER = [{"role": "user", "content": "What do you do?"}]


class _Host(BaseHTTPRequestHandler):
    seen: list[dict] = []
    fail_with_key = False

    def do_POST(self):  # noqa: N802 - stdlib name
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).seen.append({"body": body, "auth": self.headers.get("Authorization")})
        if type(self).fail_with_key:
            return self._send(401, {"error": {"message": f"Incorrect API key provided: {KEY}", "type": "auth"}})
        system = body["messages"][0]["content"] if body["messages"][0]["role"] == "system" else ""
        if "customer support agent" in system:
            content = json.dumps({"reply": f"Sorry about that. (debug: {KEY})", "actions": [], "end": True})
        else:
            # A resident who gets in touch with the helpdesk, and a host that
            # echoes the key into the model's reasoning.
            content = json.dumps({"action": "contact", "target": "northline", "channel": "text",
                                  "dialogue": "My internet is down.", "reasoning": f"echo {KEY}",
                                  "line": "Hello.", "end_conversation": True})
        self._send(200, {"id": "x", "object": "chat.completion", "created": 0, "model": body["model"],
                         "choices": [{"index": 0, "finish_reason": "stop",
                                      "message": {"role": "assistant", "content": content}}],
                         "usage": {"prompt_tokens": 1000, "completion_tokens": 50, "total_tokens": 1050,
                                   "prompt_tokens_details": {"cached_tokens": 400}}})

    def _send(self, code, payload):
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture
def host():
    _Host.seen, _Host.fail_with_key = [], False
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Host)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    server.shutdown()


def _runner(tmp_path, url, **roles):
    config = Config.build("laptop", {"providers": {"local": {"base_url": url}}, "roles": roles})
    return ModelRunner(config, Meter(config), Telemetry(tmp_path, run_id="t"))


def _files_with_key(root: Path) -> list[str]:
    return [str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()
            and KEY in p.read_text(encoding="utf-8", errors="replace")]


async def test_the_key_is_the_authorization_header(tmp_path, host, monkeypatch):
    monkeypatch.setenv("POPULACE_API_KEY", KEY)
    runner = _runner(tmp_path, host)
    result = await runner.call("npc_decision", SYSTEM, USER, {"char_id": "sam"})
    await runner.aclose()
    assert result.ok and result.usage_reported
    assert _Host.seen[0]["auth"] == f"Bearer {KEY}"
    assert KEY not in result.text and "[POPULACE_API_KEY]" in result.text
    assert _files_with_key(tmp_path) == []


async def test_without_the_variable_a_placeholder_goes(tmp_path, host, monkeypatch):
    monkeypatch.delenv("POPULACE_API_KEY", raising=False)
    runner = _runner(tmp_path, host)
    await runner.call("npc_decision", SYSTEM, USER, {"char_id": "sam"})
    await runner.aclose()
    assert _Host.seen[0]["auth"] == "Bearer not-needed"


async def test_a_host_error_that_echoes_the_key_is_logged_without_it(tmp_path, host, monkeypatch):
    monkeypatch.setenv("POPULACE_API_KEY", KEY)
    _Host.fail_with_key = True
    runner = _runner(tmp_path, host)
    result = await runner.call("npc_decision", SYSTEM, USER, {"char_id": "sam"})
    await runner.aclose()
    assert not result.ok and KEY not in result.error and "[POPULACE_API_KEY]" in result.error
    assert _files_with_key(tmp_path) == []


async def test_thinking_off_the_openrouter_way_and_the_no_think_way(tmp_path, host):
    from populace.config import thinking_off_overrides

    for name in ("openrouter", "no-think"):
        roles = thinking_off_overrides(name)["roles"]
        runner = _runner(tmp_path, host, **roles)
        await runner.call("npc_decision", SYSTEM, USER, {"char_id": "sam"})
        await runner.aclose()
    openrouter, no_think = (s["body"] for s in _Host.seen)
    assert openrouter["reasoning"] == {"enabled": False}
    assert openrouter["messages"][-1]["content"] == "What do you do?"
    assert "reasoning" not in no_think
    assert no_think["messages"][-1]["content"].endswith("\n\n/no_think")


def test_an_unknown_way_is_refused():
    from populace.config import ConfigError, thinking_off_overrides
    with pytest.raises(ConfigError):
        thinking_off_overrides("together")


def test_a_live_run_with_the_helpdesk_keeps_the_key_out_of_everything(tmp_path, host, monkeypatch, capsys):
    """The ISP demo against the fake host, residents and the LLM helpdesk both
    live, the host echoing the key into replies: the key goes only in the
    header, no file under the town and nothing printed has it, and the run
    prints and reports its calls and tokens."""
    from populace.cli import main

    monkeypatch.setenv("POPULACE_API_KEY", KEY)
    out = tmp_path / "isp"
    code = main(["demo", "isp", "--residents", "40", "--days", "0.13", "--out", str(out),
                 "--model-url", host, "--model", "qwen/qwen3-32b", "--thinking-off", "openrouter",
                 "--agent", f"northline={ROOT / 'examples' / 'llm_helpdesk.py'}", "--run-id", "hosted"])
    printed = capsys.readouterr()
    assert code == 0, printed.out + printed.err
    assert {s["auth"] for s in _Host.seen} == {f"Bearer {KEY}"}
    helpdesk = [s["body"] for s in _Host.seen if "customer support agent" in s["body"]["messages"][0]["content"]]
    assert helpdesk, "the helpdesk was reached"
    assert all(b["reasoning"] == {"enabled": False} and "chat_template_kwargs" not in b for b in helpdesk)
    assert _files_with_key(tmp_path) == []
    assert KEY not in printed.out and KEY not in printed.err

    manifest = json.loads((out / "runs" / "hosted" / "manifest.json").read_text())
    resident_calls = manifest["calls"]["total"]
    assert manifest["tokens"]["calls_with_usage"] == resident_calls
    assert manifest["tokens"] == {"calls_with_usage": resident_calls, "calls_without_usage": 0,
                                  "in": 1000 * resident_calls, "in_from_cache": 400 * resident_calls,
                                  "out": 50 * resident_calls}
    assert manifest["agent_calls"]["calls"] == len(helpdesk)
    line = next(l for l in printed.out.splitlines() if l.startswith("Model use:"))
    assert f"{resident_calls} calls; tokens in {1000 * resident_calls:,}" in line
    assert f"The agent's own model: {len(helpdesk)} calls, tokens in {1000 * len(helpdesk):,}" in line
    report = (out / "runs" / "hosted" / "report.md").read_text()
    assert f"| Tokens in / out | {1000 * resident_calls:,} ({400 * resident_calls:,} from the prompt cache)" in report


def test_a_mock_run_says_it_used_no_model(tmp_path, capsys):
    from populace.cli import main

    assert main(["demo", "isp", "--residents", "40", "--days", "0.1", "--out", str(tmp_path / "m")]) == 0
    line = next(l for l in capsys.readouterr().out.splitlines() if l.startswith("Model use:"))
    assert line.startswith("Model use: mock, no model called")
