"""examples/llm_helpdesk.py: the model-backed helpdesk, tested with no model.

Its limits and its failures with scripted replies; its HTTP path against a
stdlib server speaking the OpenAI protocol; and a mock ISP run end to end,
the agent's calls logged and the report naming who answered.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from populace.agents.protocol import Message

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "examples" / "llm_helpdesk.py"


def _module():
    spec = importlib.util.spec_from_file_location("llm_helpdesk_under_test", FILE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


H = _module()


class Ctx:
    def __init__(self):
        self.actions, self.logged = [], []

    def resolve(self, note="", kind=None):
        self.actions.append(("resolve", kind))
        return 1

    def credit(self, amount, reason=""):
        self.actions.append(("credit", amount))

    def dispatch(self, at, fixes=True, note="", kind=None):
        self.actions.append(("dispatch", at, kind))

    def promise(self, what, by_day, kind=None):
        self.actions.append(("promise", by_day, kind))

    def note(self, text):
        self.actions.append(("note", text))

    def log(self, record):
        self.logged.append(record)


class Scripted:
    """A chat that answers from a list, and keeps what it was asked."""

    def __init__(self, *texts):
        self.texts = list(texts)
        self.asked = []

    async def __call__(self, system, user, facts):
        self.asked.append((system, user))
        return H.ChatResult(self.texts.pop(0))


def _msg(text, problems, channel="text", day=2, time="11:00", thread=()):
    return Message(service="northline", channel=channel,
                   customer={"name": "Ann Reed", "number": "555-1", "address": "4 Elm Street"},
                   text=text, thread=list(thread), day=day, time=time, problems=problems)


def _run(agent, message, ctx):
    return asyncio.run(agent.handle(message, ctx))


def test_the_prompt_shows_the_account_a_helpdesk_would_see():
    chat = Scripted('{"reply": "Let me look.", "actions": []}')
    _run(H.LlmHelpdesk(chat), _msg("My bill is huge", ["a Northline bill of $184.60 when it is usually $39",
                                                        "no internet"]), Ctx())
    system, user = chat.asked[0]
    assert "customer support agent for Northline Internet" in system
    assert "Customer: Ann Reed, 555-1, 4 Elm Street" in user
    assert "Latest bill: $184.60 (plan price $39.00)" in user
    assert "Line status (live): down (no internet)" in user
    assert "Day 2: 0 of 8 visits booked" in user


def test_an_account_with_nothing_wrong_says_so():
    chat = Scripted('{"reply": "All fine here.", "actions": []}')
    reply = _run(H.LlmHelpdesk(chat), _msg("My internet is out!", []), Ctx())
    _, user = chat.asked[0]
    assert "Line status (live): working normally" in user and "Latest bill: $39.00, as usual" in user
    assert reply.text == "All fine here." and reply.end, "a text is one exchange"


def test_the_desk_does_only_what_a_desk_can_and_logs_the_rest():
    ctx = Ctx()
    asked = [
        {"do": "resolve", "kind": "internet"},                 # a line needs an engineer
        {"do": "credit", "amount": 100},                       # over the cap
        {"do": "dispatch", "at": "Day 2 22:00"},               # after hours
        {"do": "dispatch", "at": "Day 1 10:00"},               # in the past
        {"do": "promise", "what": "fixed", "by_day": 1},       # a day already gone
        {"do": "reboot"},                                      # no such action
        {"do": "credit", "amount": 10, "reason": "the trouble"},
        {"do": "dispatch", "at": "Day 3 09:00", "kind": "internet"},
        {"do": "promise", "what": "working again", "by_day": 3, "kind": "internet"},
    ]
    agent = H.LlmHelpdesk(Scripted(json.dumps({"reply": "Sorted.", "actions": asked})))
    _run(agent, _msg("Still no internet", ["no internet"]), ctx)
    assert ctx.actions == [("credit", 10.0), ("dispatch", "Day 3 09:00", "internet"), ("promise", 3, "internet")]
    refused = ctx.logged[0]["refused"]
    assert len(refused) == 6
    assert any("engineer" in r["why"] for r in refused)
    assert agent.diary[3] == ["09:00 Elm Street"]


def test_a_full_diary_refuses_another_visit():
    agent = H.LlmHelpdesk(Scripted(*['{"reply": "Booked.", "actions": [{"do": "dispatch", "at": "Day 3 09:00"}]}'] * 3),
                          visits_per_day=2)
    ctxs = [Ctx() for _ in range(3)]
    for ctx in ctxs:
        _run(agent, _msg("No internet", ["no internet"]), ctx)
    assert [len(c.actions) for c in ctxs] == [1, 1, 0]
    assert ctxs[2].logged[0]["refused"][0]["why"] == "Day 3 is fully booked"


def test_a_garbled_reply_is_retried_once():
    chat = Scripted("Sure! Here you go", '{"reply": "Sorry about that, Ann.", "actions": []}')
    ctx = Ctx()
    reply = _run(H.LlmHelpdesk(chat), _msg("Hello?", ["no internet"]), ctx)
    assert reply.text == "Sorry about that, Ann."
    assert "not one JSON object" in chat.asked[1][1]
    assert [c["attempt"] for c in ctx.logged[0]["calls"]] == [1, 2]


def test_two_garbled_replies_fail_the_contact_out_loud():
    ctx = Ctx()
    with pytest.raises(H.AgentModelError):
        _run(H.LlmHelpdesk(Scripted("nope", "still nope")), _msg("Hello?", []), ctx)
    assert ctx.logged[0]["failed"]


def test_a_call_can_go_on_and_a_text_cannot():
    agent = H.LlmHelpdesk(Scripted('{"reply": "Which address?", "actions": [], "end": false}',
                                   '{"reply": "Which address?", "actions": [], "end": false}'))
    assert not _run(agent, _msg("Hi", [], channel="call"), Ctx()).end
    assert _run(agent, _msg("Hi", [], channel="text"), Ctx()).end


# The HTTP path, against a stdlib server that speaks the OpenAI protocol

class _FakeOpenAI(BaseHTTPRequestHandler):
    seen: list[dict] = []
    reply = '{"reply": "An engineer is booked for tomorrow at nine.", "actions": [{"do": "dispatch", "at": "Day 3 09:00", "kind": "internet"}], "end": true}'

    def do_POST(self):  # noqa: N802 - stdlib name
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        type(self).seen.append(body)
        out = {"id": "x1", "object": "chat.completion", "created": 0, "model": body["model"],
               "choices": [{"index": 0, "finish_reason": "stop",
                            "message": {"role": "assistant", "content": type(self).reply}}],
               "usage": {"prompt_tokens": 900, "completion_tokens": 40, "total_tokens": 940}}
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


def test_the_live_path_speaks_the_openai_protocol(fake_server):
    agent = H.make_agent(model_url=fake_server, model="qwen3-32b", mock=False)
    ctx = Ctx()
    reply = _run(agent, _msg("My internet is down", ["no internet"]), ctx)
    body = _FakeOpenAI.seen[0]
    assert body["model"] == "qwen3-32b"
    assert body["messages"][0]["role"] == "system" and "4 Elm Street" in body["messages"][1]["content"]
    assert body["response_format"] == {"type": "json_object"}
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert reply.text.startswith("An engineer")
    assert ctx.actions == [("dispatch", "Day 3 09:00", "internet")]
    assert ctx.logged[0]["calls"][0]["tokens_in"] == 900
    assert agent.describe()["model"] == "qwen3-32b"


def test_the_cli_loads_it_from_its_file(fake_server):
    from populace.cli import _agents_from
    mock = _agents_from([f"northline={FILE}"])["northline"]
    live = _agents_from([f"northline={FILE}"], model_url=fake_server, mock=False)["northline"]
    assert type(mock.chat).__name__ == "MockChat"
    assert type(live.chat).__name__ == "OpenAIChat"
    with pytest.raises(SystemExit):
        _agents_from(["northline=nowhere.py"])


# End to end, in mock

def test_the_isp_demo_runs_with_it_and_the_report_says_who_answered(tmp_path):
    from populace.demos import isp
    from populace.observe.report import render
    from populace.sim.run import run_town, ticks_for_days

    asyncio.run(isp.build(tmp_path / "isp", residents=60, seed=7))
    result = asyncio.run(run_town(tmp_path / "isp", ticks_for_days(1), mock=True, run_id="t",
                                  agents={"northline": H.make_agent(mock=True)}))
    run_dir = Path(result["run_dir"])
    contacts = [json.loads(line) for line in (run_dir / "contacts.jsonl").read_text().splitlines()]
    calls = [json.loads(line) for line in (run_dir / "agent_calls.jsonl").read_text().splitlines()]
    answered = [c for c in contacts if not c.get("failed")]
    assert answered and len(calls) == len(answered)
    assert all(c["service"] == "northline" and c["resident"] for c in calls)
    assert json.loads((run_dir / "agents.json").read_text())["northline"]["kind"] == "language model"
    text = render(run_dir)
    assert "Answered by: `LlmHelpdesk`" in text
    assert "The agent's own model:" in text
