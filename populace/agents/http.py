"""Agents over HTTP, standard library only.

`HttpAgent(url, timeout)` posts `{"message": {...}}` and expects back
`{"text": "...", "end": false, "actions": [{"do": "resolve"}, ...]}`; the
actions are the same as `AgentContext`'s methods. A server that does not answer
within the timeout is a failed contact, said to the resident, never a hang.

`serve(agent, port)` wraps any Python agent in such a server, for trying the
HTTP path locally: `python examples/http_agent_server.py`.
"""

from __future__ import annotations

import asyncio
import json
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .protocol import AgentContext, Message, Reply


class AgentUnreachable(RuntimeError):
    pass


class HttpAgent:
    def __init__(self, url: str, timeout: float = 5.0):
        self.url = url
        self.timeout = float(timeout)

    def _post(self, body: bytes) -> dict[str, Any]:
        request = urllib.request.Request(self.url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise AgentUnreachable(f"{self.url}: {exc}") from exc

    async def handle(self, message: Message, ctx: AgentContext) -> Reply | None:
        body = json.dumps({"message": message.to_dict()}).encode("utf-8")
        try:
            data = await asyncio.wait_for(asyncio.to_thread(self._post, body), self.timeout + 1)
        except asyncio.TimeoutError as exc:
            raise AgentUnreachable(f"{self.url}: no answer in {self.timeout:.0f} s") from exc
        for act in data.get("actions") or []:
            kind = act.get("do")
            if kind == "resolve":
                ctx.resolve(act.get("note", ""), act.get("kind"))
            elif kind == "credit":
                ctx.credit(act["amount"], act.get("reason", ""))
            elif kind == "dispatch":
                ctx.dispatch(act["at"], act.get("fixes", True), act.get("note", ""), act.get("kind"))
            elif kind == "promise":
                ctx.promise(act["what"], act["by_day"], act.get("kind"))
            elif kind == "note":
                ctx.note(act.get("text", ""))
            else:
                raise AgentUnreachable(f"{self.url}: unknown action {kind!r}")
        return Reply.of(data)


class _Recorder:
    """An AgentContext stand-in on the server side: it only records."""

    def __init__(self, day: int):
        self.day = day
        self.actions: list[dict[str, Any]] = []

    def resolve(self, note: str = "", kind: str | None = None) -> int:
        self.actions.append({"do": "resolve", "note": note, "kind": kind})
        return 0

    def credit(self, amount: float, reason: str = "") -> None:
        self.actions.append({"do": "credit", "amount": amount, "reason": reason})

    def dispatch(self, at: str, fixes: bool = True, note: str = "", kind: str | None = None) -> None:
        self.actions.append({"do": "dispatch", "at": at, "fixes": fixes, "note": note, "kind": kind})

    def promise(self, what: str, by_day: int, kind: str | None = None) -> None:
        self.actions.append({"do": "promise", "what": what, "by_day": by_day, "kind": kind})

    def note(self, text: str) -> None:
        self.actions.append({"do": "note", "text": text})


def serve(agent: Any, port: int = 8765, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    """Start a server for `agent` in a background thread; returns it (call
    `.shutdown()` to stop)."""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length") or 0)
            payload = json.loads(self.rfile.read(length) or b"{}")
            message = Message(**payload["message"])
            ctx = _Recorder(message.day)
            reply = agent.handle(message, ctx)
            if asyncio.iscoroutine(reply):
                reply = asyncio.run(reply)
            reply = Reply.of(reply)
            body = json.dumps({"text": reply.text if reply else "", "end": bool(reply and reply.end),
                               "actions": ctx.actions}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # quiet
            pass

    server = ThreadingHTTPServer((host, port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
