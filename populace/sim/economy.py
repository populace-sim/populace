"""Money between people: loans, and paying some of it back.

Ported verbatim from Alive, less tabs.

A debt is not a number in a ledger somewhere; it is a thing two people both
know about. Every obligation here is written to BOTH of them, so neither can
be wrong about it on their own, and so "Friday - that's what you said last
Friday" is something the other one can actually say.

Nothing in this module decides anything. Whether a loan is
made is a person's decision, taken in a conversation; this is only the
bookkeeping underneath it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ..state.resident import Resident as Character


def obligations_between(
    debtor: "Character", creditor_id: str, kind: str | None = None
) -> list[dict[str, Any]]:
    """What this person owes that person, oldest first."""
    return [
        o
        for o in debtor.obligations.get("owes", [])
        if o.get("to") == creditor_id and (kind is None or o.get("kind") == kind)
    ]


def add_obligation(
    debtor: "Character",
    creditor: "Character",
    kind: str,
    amount: float,
    day: int,
    due_day: int | None = None,
    where: str | None = None,
) -> dict[str, Any]:
    """Put a debt in both their heads.

    A tab is added to rather than piled up: a second sandwich is more owed to
    the same shop, not a second arrangement with it.
    """
    amount = round(float(amount), 2)
    existing = obligations_between(debtor, creditor.id, kind)
    if kind == "tab" and existing:
        entry = existing[0]
        entry["amount"] = round(float(entry["amount"]) + amount, 2)
        entry["due_day"] = due_day
        entry["overdue_noted"] = False
        _mirror(creditor, entry)
        return entry

    entry = {
        "kind": kind,
        "to": creditor.id,
        "from": debtor.id,
        "amount": amount,
        "day": int(day),
        "due_day": due_day,
        "where": where,
        "overdue_noted": False,
    }
    debtor.obligations.setdefault("owes", []).append(entry)
    creditor.obligations.setdefault("owed", []).append(dict(entry))
    return entry


def _same_debt(theirs: dict[str, Any], entry: dict[str, Any]) -> bool:
    """Is this the creditor's copy of *this* debt?

    **The day is part of the key.** Matching on who and what alone treats two
    loans from the same person as one debt, so settling the first deleted the
    creditor's record of the second: in Alive a resident finished a twelve-day mock gate
    owing another forty dollars that the lender had no record of. The gate has
    always asked "a debt one of them does not know about is not a debt" and it
    took a run in which somebody borrowed twice to make it fire.
    """
    return (
        theirs.get("from") == entry["from"]
        and theirs.get("kind") == entry["kind"]
        and theirs.get("day") == entry["day"]
    )


def _mirror(creditor: "Character", entry: dict[str, Any]) -> None:
    """Keep the creditor's copy of a debt in step with the debtor's."""
    for theirs in creditor.obligations.get("owed", []):
        if _same_debt(theirs, entry):
            theirs.update(
                {"amount": entry["amount"], "due_day": entry["due_day"],
                 "overdue_noted": entry["overdue_noted"]}
            )
            return
    creditor.obligations.setdefault("owed", []).append(dict(entry))


def settle(debtor: "Character", creditor: "Character", amount: float) -> float:
    """Put money against what is owed, oldest debt first.

    Returns what was actually applied, which is never more than the debt.
    Handing somebody twenty against forty is not nothing, and both of them
    remember it as not nothing.
    """
    left = round(float(amount), 2)
    applied = 0.0
    for entry in list(obligations_between(debtor, creditor.id)):
        if left <= 0:
            break
        take = min(left, float(entry["amount"]))
        entry["amount"] = round(float(entry["amount"]) - take, 2)
        left = round(left - take, 2)
        applied = round(applied + take, 2)
        if entry["amount"] <= 0.009:
            debtor.obligations["owes"].remove(entry)
            _drop_mirror(creditor, entry)
        else:
            entry["overdue_noted"] = False
            _mirror(creditor, entry)
    return applied


def _drop_mirror(creditor: "Character", entry: dict[str, Any]) -> None:
    creditor.obligations["owed"] = [
        o for o in creditor.obligations.get("owed", []) if not _same_debt(o, entry)
    ]


def loan_cap(lender: "Character", borrower_id: str, config) -> float:
    """The most this person would put in that person's hand."""
    caps = list(config.economy["loan_cap_by_stage"])
    stage = lender.trust_stage(borrower_id, config.trust["thresholds"])
    ceiling = float(caps[max(0, min(stage, len(caps) - 1))])
    return min(ceiling, float(config.economy["loan_max"]))
