"""CLI for swarm-probe."""

from __future__ import annotations

import argparse
import sys

from swarm_probe.probes.injection import InstructionInjectionProbe
from swarm_probe.probes.trust import TrustManipulationProbe
from swarm_probe.probes.poisoning import DataPoisoningProbe
from swarm_probe.reporter import report_json, report_text
from swarm_probe.sarif import report_sarif
from swarm_probe.scenarios import (
    build_corporate_ecosystem,
    build_flat_ecosystem,
    build_star_ecosystem,
)
from swarm_probe.simulation import Simulation


PROBES = {
    "injection": InstructionInjectionProbe,
    "trust": TrustManipulationProbe,
    "poisoning": DataPoisoningProbe,
}

SCENARIOS = {
    "corporate": build_corporate_ecosystem,
    "flat": build_flat_ecosystem,
    "star": build_star_ecosystem,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="swarm-probe",
        description="Adversarial resilience testing for multi-agent ecosystems",
    )
    parser.add_argument(
        "scenario",
        nargs="?",
        choices=list(SCENARIOS),
        help="Pre-built scenario to test",
    )
    parser.add_argument(
        "--file",
        help="Load custom ecosystem from YAML/JSON file",
    )
    parser.add_argument(
        "--probe",
        choices=list(PROBES),
        default="injection",
        help="Probe type (default: injection)",
    )
    parser.add_argument(
        "--target",
        help="Target agent ID (default: first worker)",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=10,
        help="Max simulation steps (default: 10)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of text",
    )
    parser.add_argument(
        "--sarif",
        action="store_true",
        help="Output SARIF 2.1.0 for CI/CD integration",
    )
    parser.add_argument(
        "--output",
        help="Write output to file instead of stdout",
    )
    parser.add_argument(
        "--all-probes",
        action="store_true",
        help="Run all probes against the scenario",
    )

    args = parser.parse_args(argv)

    if not args.scenario and not args.file:
        parser.error("either scenario or --file is required")

    if args.all_probes:
        return _run_all_probes(args)

    return _run_single(args)


def _run_single(args: argparse.Namespace) -> int:
    ecosystem = _load_ecosystem(args)
    probe = PROBES[args.probe]()
    target = args.target or _default_target(ecosystem)

    sim = Simulation(ecosystem, probe, max_steps=args.steps)
    result = sim.run(target)

    total = len(ecosystem.agents)
    output = _format_output([(result, total)], args)
    _write_output(output, args.output)

    return 0


def _run_all_probes(args: argparse.Namespace) -> int:
    all_results: list[tuple] = []

    for _, probe_cls in PROBES.items():
        ecosystem = _load_ecosystem(args)
        probe = probe_cls()
        target = args.target or _default_target(ecosystem)

        sim = Simulation(ecosystem, probe, max_steps=args.steps)
        result = sim.run(target)
        all_results.append((result, len(ecosystem.agents)))

    output = _format_output(all_results, args)
    _write_output(output, args.output)

    return 0


def _format_output(
    results: list[tuple], args: argparse.Namespace,
) -> str:
    if args.sarif:
        return report_sarif(results)

    parts: list[str] = []
    for result, total in results:
        if args.json:
            parts.append(report_json(result, total))
        else:
            parts.append(report_text(result, total))

    return "\n\n".join(parts)


def _write_output(output: str, filepath: str | None) -> None:
    if filepath:
        with open(filepath, "w") as f:
            f.write(output)
    else:
        print(output)


def _load_ecosystem(args: argparse.Namespace):
    if args.file:
        from swarm_probe.loader import load_ecosystem
        return load_ecosystem(args.file)
    return SCENARIOS[args.scenario]()


def _default_target(ecosystem) -> str:
    from swarm_probe.agent import AgentRole
    for aid, agent in ecosystem.agents.items():
        if agent.role == AgentRole.WORKER:
            return aid
    return next(iter(ecosystem.agents))


if __name__ == "__main__":
    sys.exit(main())
