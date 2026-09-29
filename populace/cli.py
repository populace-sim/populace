"""The `populace` command.

    populace new "a suburb of 200 people with a strip mall, a school and a factory"
    populace show towns/westfield
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from . import __version__
from .config import Config, PRESETS


def _config_from(args) -> Config:
    overrides: dict = {}
    if getattr(args, "model_url", None):
        overrides.setdefault("providers", {})["local"] = {"base_url": args.model_url}
    if getattr(args, "model", None):
        # mlx_lm.server routes by this name; llama-server ignores it.
        from .config import ROLES
        overrides["roles"] = {role: {"model": args.model} for role in ROLES}
    return Config.build(getattr(args, "preset", None), overrides)


def cmd_new(args) -> int:
    from .gen.generate import generate
    from .gen.skeleton import slug
    from .gen.spec import parse_description

    config = _config_from(args)
    mock = args.provider == "mock" and not args.model_url and not args.model
    spec = parse_description(args.description, args.seed)
    out = Path(args.out or Path("towns") / slug(spec.name))
    if out.exists() and any(out.iterdir()) and not args.force:
        print(f"{out} already holds a town; pass --force to replace it, or --out somewhere else",
              file=sys.stderr)
        return 2
    if out.exists() and args.force:
        import shutil
        shutil.rmtree(out)
    mode = "mock (free, no model)" if mock else f"local model at {config.provider_settings('local')['base_url']}"
    print(f"Generating {spec.name}: {spec.population} people, persona prose by {mode}")

    def progress(i, n):
        if not mock:
            print(f"  personas: batch {i + 1} of {n}", flush=True)

    town, report = asyncio.run(generate(
        args.description, out, seed=args.seed, mock=mock, config=config,
        use_model_for_spec=args.model_spec and not mock, progress=progress,
    ))
    print(f"Wrote {out}: {report['population']} residents, {report['households']} households, "
          f"{report['places']} places, {report['model_calls']} model calls, {report['seconds']} s")
    print(f"See it with:  populace show {out}")
    return 0


def cmd_show(args) -> int:
    from .observe.show import render
    from .state.town import Town

    town = Town.load(args.town)
    gen_path = Path(args.town) / "runs" / "generate" / "generation.json"
    generation = json.loads(gen_path.read_text()) if gen_path.exists() else None
    text = render(town, residents=args.residents, households=args.households, seed=args.seed,
                  generation=generation, only=args.resident)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)
    return 0


def cmd_gate(args) -> int:
    from .sim.gate import DEFAULT_DESCRIPTION, run_gate

    result = asyncio.run(run_gate(args.description or DEFAULT_DESCRIPTION, args.seed, args.days))
    print(f"Gate: {'PASSED' if result['passed'] else 'FAILED'} - {result['events']} events over "
          f"{result['days']} days, signature {result['signature']}, {result['wall_s']} s")
    for kind, n in result["kinds"].items():
        print(f"  {kind:32} {n}")
    for failure in result["failures"]:
        print(f"  FAIL: {failure}")
    return 0 if result["passed"] else 1


def cmd_prompt_stats(args) -> int:
    from .prompt.stats import measure
    from .state.town import Town

    overrides = {"prompt": {"profile": args.profile}} if args.profile else None
    town = Town.load(args.town, overrides=overrides)
    print(json.dumps(measure(town, args.sample), indent=2))
    return 0


def cmd_inject(args) -> int:
    import json as _json

    from .inject import InjectionRefused, KINDS, inject, label, validate
    from .state.town import Town

    if args.kinds:
        for kind, what in KINDS.items():
            print(f"{kind:18} {what}")
        return 0
    if not args.file:
        print("populace inject: --file is required (or --kinds to list them)", file=sys.stderr)
        return 2
    data = _json.loads(Path(args.file).read_text(encoding="utf-8"))
    raws = data.get("injections", data) if isinstance(data, dict) else data
    if not isinstance(raws, list):
        raws = [raws]
    town = Town.load(args.town)
    bad = 0
    for raw in raws:
        try:
            rec = inject(town, raw) if args.write else validate(raw, town)
            print(f"  ok       {rec['id']}  {label(rec['at'])}  {rec['kind']}")
        except InjectionRefused as exc:
            bad += 1
            print(f"  REFUSED  {raw.get('kind') if isinstance(raw, dict) else raw!r}: {exc}")
    if args.write:
        town.save(full=False)
        print(f"Scheduled {len(raws) - bad}, refused {bad}; saved to {args.town}.")
    else:
        print(f"Dry run: {len(raws) - bad} would be scheduled, {bad} refused. Pass --write to schedule them.")
    return 1 if bad else 0


def cmd_demo(args) -> int:
    from .demos import isp
    from .observe.manifest import build_manifest, headline
    from .observe.report import write
    from .sim.run import run_town, ticks_for_days

    out = Path(args.out or f"towns/isp-{args.residents}")
    if out.exists() and not args.keep:
        import shutil
        shutil.rmtree(out)
    if not (out / "world.json").exists():
        built = asyncio.run(isp.build(out, residents=args.residents, seed=args.seed))
        print(f"Built {out}: {len(built['scheduled'])} injections scheduled, {len(built['refused'])} refused")
        for raw, reason in built["refused"]:
            print(f"  REFUSED {raw.get('kind')}: {reason}")
        if built["refused"]:
            return 1
    if args.setup_only:
        print(f"Set up only. Run it with: populace demo isp --out {out} --keep ...")
        return 0
    overrides: dict = {}
    if args.model_url:
        overrides.setdefault("providers", {})["local"] = {"base_url": args.model_url}
    if args.concurrency:
        overrides.setdefault("providers", {}).setdefault("local", {})["max_concurrency"] = args.concurrency
    if args.model:
        from .config import ROLES
        overrides["roles"] = {role: {"model": args.model} for role in ROLES}
    if args.profile:
        overrides["prompt"] = {"profile": args.profile}
    mock = args.provider == "mock" and not args.model_url and not args.model
    print(f"Running the ISP demo: {args.residents} residents, {args.days} days, "
          f"{'mock (free, no model)' if mock else 'live model'}, preset {args.preset or 'laptop'}")
    agents = {isp.SERVICE_ID: isp.NorthlineSupport(),
              **_agents_from(args.agent or [], model_url=args.model_url, model=args.model, mock=mock)}
    from .sim.run import describe_agent
    who = describe_agent(agents[isp.SERVICE_ID])
    print(f"Northline is answered by {who['agent'].rsplit('.', 1)[-1]}"
          + (f" ({', '.join(str(v) for k, v in who.items() if k != 'agent' and v)})" if len(who) > 1 else ""))

    def progress(report):
        if report.tick == 0 or report.stopped:
            flag = f" STOPPED: {report.stopped}" if report.stopped else ""
            print(f"  Day {report.day} begins{flag}", flush=True)

    result = asyncio.run(run_town(out, ticks_for_days(args.days), mock=mock, preset=args.preset,
                                  overrides=overrides or None, run_id=args.run_id, progress=progress,
                                  agents=agents))
    print(headline(build_manifest(result)))
    print(f"Report: {write(result['run_dir'])}")
    return 1 if result["reports"] and result["reports"][-1].stopped else 0


def cmd_report(args) -> int:
    from .observe.report import render

    run_dir = Path(args.run_dir)
    text = render(run_dir)
    if args.narrate:
        import asyncio

        from .observe.narrate import narrate

        town_config = run_dir.parents[1] / "config.json"
        config = _config_from(args)
        if town_config.exists():
            from .config import Config
            config = Config.load(town_config, overrides=config.raw)
        mock = args.provider == "mock" and not args.model_url and not args.model
        story = asyncio.run(narrate(run_dir, text, config, mock))
        head, rest = text.split("\n## ", 1)
        text = head.rstrip() + "\n\n" + story + "\n## " + rest
    path = Path(args.out) if args.out else run_dir / "report.md"
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {path}")
    return 0


def _agents_from(specs: list[str], model_url: str | None = None, model: str | None = None,
                 mock: bool = True) -> dict:
    """`--agent SERVICE=helpdesk`, `=echo`, `=http://host:port/`, or
    `=path/to/agent.py`: a file with `make_agent(model_url, model, mock)`,
    which is handed the run's own model server (see examples/llm_helpdesk.py)."""
    from .agents import HttpAgent
    from .agents.basic import EchoAgent, HelpdeskAgent

    out = {}
    for spec in specs:
        sid, _, what = spec.partition("=")
        if not sid or not what:
            raise SystemExit(f"--agent wants SERVICE=helpdesk|echo|URL|file.py; got {spec!r}")
        if what == "helpdesk":
            out[sid] = HelpdeskAgent(sid.replace("_", " ").title())
        elif what == "echo":
            out[sid] = EchoAgent()
        elif what.startswith(("http://", "https://")):
            out[sid] = HttpAgent(what)
        elif what.endswith(".py"):
            out[sid] = _agent_from_file(Path(what), model_url=model_url, model=model, mock=mock)
        else:
            raise SystemExit(f"--agent {sid}=: use helpdesk, echo, an http:// URL or a .py file; got {what!r}")
    return out


def _agent_from_file(path: Path, **kw):
    import importlib.util

    if not path.exists():
        raise SystemExit(f"--agent: no such file {path}")
    spec = importlib.util.spec_from_file_location(f"populace_agent_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module          # dataclasses in the file look themselves up here
    spec.loader.exec_module(module)
    make = getattr(module, "make_agent", None)
    if not callable(make):
        raise SystemExit(f"--agent: {path} has no make_agent(model_url, model, mock)")
    return make(**kw)


def cmd_run(args) -> int:
    from .config import LOW_FIDELITY_PRESETS
    from .sim.run import run_town, ticks_for_days

    overrides: dict = {}
    if args.model_url:
        overrides.setdefault("providers", {})["local"] = {"base_url": args.model_url}
    if args.model:
        from .config import ROLES
        overrides["roles"] = {role: {"model": args.model} for role in ROLES}
    if args.profile:
        overrides["prompt"] = {"profile": args.profile}
    mock = args.provider == "mock" and not args.model_url and not args.model
    ticks = args.ticks if args.ticks is not None else ticks_for_days(args.days)
    if args.preset in LOW_FIDELITY_PRESETS:
        print(f"PRESET {args.preset.upper()}: LOW FIDELITY. About one resident thinks per tick; "
              "for smoke runs only.")
    print(f"Running {args.town} for {ticks} ticks, "
          f"{'mock (free, no model)' if mock else 'local model'}, preset {args.preset or 'laptop'}")

    def progress(report):
        if args.quiet:
            return
        flag = f" STOPPED: {report.stopped}" if report.stopped else ""
        print(f"  Day {report.day} {report.tick:02d}: {report.calls} calls, "
              f"{report.residents_thinking} thinking, {report.events} events, "
              f"{report.wall_ms / 1000:.1f}s{flag}", flush=True)

    agents = _agents_from(args.agent or [], model_url=args.model_url, model=args.model, mock=mock)
    out = asyncio.run(run_town(args.town, ticks, mock=mock, preset=args.preset,
                               overrides=overrides or None, run_id=args.run_id, progress=progress,
                               agents=agents))
    from .observe.manifest import build_manifest, headline
    manifest = build_manifest(out)
    print(headline(manifest))
    print(f"Logs: {out['run_dir']}")
    print(f"Report: populace report {out['run_dir']}")
    return 1 if out["reports"] and out["reports"][-1].stopped else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="populace",
        description="A town of AI people, generated from a sentence and run headless.",
    )
    parser.add_argument("--version", action="version", version=f"populace {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="command")

    new = sub.add_parser("new", help="generate a town from a description")
    new.add_argument("description", help='e.g. "a suburb of 200 people with a strip mall and a school"')
    new.add_argument("--out", help="directory for the town (default towns/<name>)")
    new.add_argument("--seed", type=int, default=0, help="same description and seed, same town")
    new.add_argument("--provider", choices=("mock", "local"), default="mock",
                     help="who writes persona prose: mock (free templates) or the local model")
    new.add_argument("--model-url", help="an OpenAI-compatible endpoint, e.g. http://pc:8080/v1")
    new.add_argument("--model", help="model name to request (mlx_lm.server needs the repo id)")
    new.add_argument("--model-spec", action="store_true",
                     help="also ask the model to read the description (falls back to the rules)")
    new.add_argument("--preset", choices=sorted(PRESETS), default=None)
    new.add_argument("--force", action="store_true", help="replace a town already in --out")
    new.set_defaults(func=cmd_new)

    show = sub.add_parser("show", help="print a readable listing of a town")
    show.add_argument("town", help="the town's directory")
    show.add_argument("--resident", help="print one resident's full sheet, by id (r017) or full name")
    show.add_argument("--residents", type=int, default=10)
    show.add_argument("--households", type=int, default=8)
    show.add_argument("--seed", type=int, default=0, help="which sample to show")
    show.add_argument("--out", help="write to a file instead of the terminal")
    show.set_defaults(func=cmd_show)

    run = sub.add_parser("run", help="run a town headless")
    run.add_argument("town")
    run.add_argument("--days", type=float, default=1.0)
    run.add_argument("--ticks", type=int, default=None, help="overrides --days")
    run.add_argument("--provider", choices=("mock", "local"), default="mock")
    run.add_argument("--model-url", help="an OpenAI-compatible endpoint, e.g. http://pc:8080/v1")
    run.add_argument("--model", help="model name to request (mlx_lm.server needs the repo id)")
    run.add_argument("--preset", choices=sorted(PRESETS), default=None)
    run.add_argument("--profile", choices=("frontier", "compact"))
    run.add_argument("--run-id", default=None)
    run.add_argument("--quiet", action="store_true")
    run.add_argument("--agent", action="append", metavar="SERVICE=helpdesk|echo|URL|file.py",
                     help="who answers a registered service (repeatable)")
    run.set_defaults(func=cmd_run)

    gate = sub.add_parser("gate", help="run the mock determinism gate")
    gate.add_argument("--days", type=float, default=7)
    gate.add_argument("--seed", type=int, default=7)
    gate.add_argument("--description", default=None)
    gate.set_defaults(func=cmd_gate)

    stats = sub.add_parser("prompt-stats", help="measure the decision prompt's parts on a town")
    stats.add_argument("town")
    stats.add_argument("--profile", choices=("frontier", "compact"))
    stats.add_argument("--sample", type=int, default=None)
    stats.set_defaults(func=cmd_prompt_stats)
    demo = sub.add_parser("demo", help="run a packaged demo: isp")
    demo.add_argument("name", choices=("isp",))
    demo.add_argument("--out", help="the town directory (default towns/isp-<residents>)")
    demo.add_argument("--keep", action="store_true", help="reuse the town in --out instead of rebuilding it")
    demo.add_argument("--setup-only", action="store_true", help="build the town and its schedule, do not run")
    demo.add_argument("--residents", type=int, default=200)
    demo.add_argument("--days", type=float, default=4)
    demo.add_argument("--seed", type=int, default=7)
    demo.add_argument("--provider", choices=("mock", "local"), default="mock")
    demo.add_argument("--model-url", help="an OpenAI-compatible endpoint, e.g. http://127.0.0.1:8080/v1")
    demo.add_argument("--model", help="model name to request")
    demo.add_argument("--concurrency", type=int, help="calls at once to the model server")
    demo.add_argument("--preset", choices=sorted(PRESETS), default=None)
    demo.add_argument("--profile", choices=("frontier", "compact"))
    demo.add_argument("--run-id", default=None)
    demo.add_argument("--agent", action="append", metavar="SERVICE=helpdesk|echo|URL|file.py",
                      help="answer a service with another agent, e.g. northline=examples/llm_helpdesk.py "
                           "(default: the rule-based NorthlineSupport)")
    demo.set_defaults(func=cmd_demo)
    inj = sub.add_parser("inject", help="schedule places, events and services into a town (dry run by default)")
    inj.add_argument("town", nargs="?", help="the town directory")
    inj.add_argument("--file", help="a JSON list of injections, or {\"injections\": [...]}")
    inj.add_argument("--write", action="store_true", help="schedule them (default: only check)")
    inj.add_argument("--kinds", action="store_true", help="list the kinds of injection")
    inj.set_defaults(func=cmd_inject)
    report = sub.add_parser("report", help="write a plain-language report of one run")
    report.add_argument("run_dir", help="a run directory: <town>/runs/<run_id>")
    report.add_argument("--out", help="where to write it (default: report.md in the run directory)")
    report.add_argument("--narrate", action="store_true",
                        help="add a model-written retelling at the top, labelled as such")
    report.add_argument("--provider", choices=("mock", "local"), default="mock")
    report.add_argument("--model-url", help="an OpenAI-compatible endpoint for --narrate")
    report.add_argument("--model", help="model name to request for --narrate")
    report.set_defaults(func=cmd_report)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
