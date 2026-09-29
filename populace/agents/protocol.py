"""The envelope an agent receives, what it sends back, and what it may do."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:  # pragma: no cover
    from ..sim.engine import Engine
    from ..state.resident import Resident


@dataclass
class Message:
    """One thing a resident said to a service."""

    service: str                       # the service id
    channel: str                       # "text", "call" or "visit"
    customer: dict[str, Any]           # what a service would know: name, number, address
    text: str                          # the resident's words, this turn
    thread: list[dict[str, str]]       # earlier turns: {"from": "customer"|"agent", "text"}
    day: int
    time: str                          # "HH:MM"
    problems: list[str] = field(default_factory=list)  # open problems at their address

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Reply:
    text: str
    end: bool = False                  # the agent is done with this contact

    @staticmethod
    def of(raw: Any) -> "Reply | None":
        if raw is None:
            return None
        if isinstance(raw, Reply):
            return raw
        if isinstance(raw, str):
            return Reply(raw)
        if isinstance(raw, dict) and isinstance(raw.get("text"), str):
            return Reply(raw["text"], bool(raw.get("end")))
        raise TypeError(f"an agent's reply must be a Reply, a string or {{text, end}}; got {raw!r}")


class Agent(Protocol):
    def handle(self, message: Message, ctx: "AgentContext") -> Reply | str | None: ...


class AgentContext:
    """What an agent may do about a contact. Each call is recorded, turned into
    events in the town, and listed in the run's `contacts.jsonl`."""

    def __init__(self, engine: "Engine", resident: "Resident", service_id: str):
        self._engine = engine
        self._resident = resident
        self.service_id = service_id
        self.actions: list[dict[str, Any]] = []

    @property
    def day(self) -> int:
        return self._engine.town.world.time.day

    def resolve(self, note: str = "", kind: str | None = None) -> int:
        """Mark this customer's open problems resolved - those of one `kind`
        (e.g. "billing"), or every kind the service handles. Returns how many
        were open."""
        self.actions.append({"do": "resolve", "note": note, "kind": kind})
        return sum(1 for p in self._resident.problems if not p.get("resolved")
                   and (kind is None or p.get("kind") == kind))

    def credit(self, amount: float, reason: str = "") -> None:
        if float(amount) <= 0:
            raise ValueError("a credit is a positive amount")
        self.actions.append({"do": "credit", "amount": round(float(amount), 2), "reason": reason})

    def dispatch(self, at: str, fixes: bool = True, note: str = "", kind: str | None = None) -> None:
        """Somebody comes round to the customer's home at `at` ("Day N HH:MM")
        and, if `fixes`, fixes problems of `kind` (or every kind handled)."""
        self.actions.append({"do": "dispatch", "at": at, "fixes": bool(fixes), "note": note, "kind": kind})

    def promise(self, what: str, by_day: int, kind: str | None = None) -> None:
        """Judged the night of `by_day`: kept if the customer's problems of
        `kind` (or every kind handled) are resolved by then."""
        self.actions.append({"do": "promise", "what": what, "by_day": int(by_day), "kind": kind})

    def note(self, text: str) -> None:
        self.actions.append({"do": "note", "text": text})

    def log(self, record: dict[str, Any]) -> None:
        """Anything the agent wants on the record about its own working - a
        model call, an action it declined - written to the run's
        `agent_calls.jsonl` with the time and the customer. Changes nothing
        in the town."""
        world = self._engine.town.world
        self._engine.telemetry.log_agent_call({"day": world.time.day, "tick": world.time.tick,
                                               "service": self.service_id, "resident": self._resident.id,
                                               **record})
