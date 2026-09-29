"""The mock gate, and proof that each of its checks can fail."""

from __future__ import annotations

from populace.sim.gate import run_gate


async def test_the_gate_passes_on_a_week(tmp_path):
    result = await run_gate(days=7, seed=7, workdir=tmp_path)
    assert result["passed"], result["failures"]
    assert all(n > 0 for n in result["kinds"].values())


async def test_the_gate_notices_two_runs_that_differ(tmp_path):
    result = await run_gate(days=0.5, seed=7, second_seed=8, workdir=tmp_path)
    assert any("differ" in f for f in result["failures"])


async def test_the_gate_notices_something_that_never_happened(tmp_path):
    def drop_the_hires(run_dir, town_dir):
        path = run_dir / "events.jsonl"
        kept = [l for l in path.read_text().splitlines() if '"kind": "hired"' not in l]
        path.write_text("\n".join(kept) + "\n")

    result = await run_gate(days=7, seed=7, workdir=tmp_path, mutate=drop_the_hires)
    assert any("never happened: hired" in f for f in result["failures"])
    assert any("differ" in f for f in result["failures"]), "and the tampered run no longer matches"
