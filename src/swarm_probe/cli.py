"""CLI for swarm-probe."""

from __future__ import annotations

import argparse
import sys

from swarm_probe.probes.injection import InstructionInjectionProbe
from swarm_probe.probes.trust import TrustManipulationProbe
from swarm_probe.probes.poisoning import DataPoisoningProbe
from swarm_probe.reporter import report_json, report_text
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
        choices=list(SCENARIOS),
        help="Pre-built scenario to test",
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
        "--all-probes",
        action="store_true",
        help="Run all probes against the scenario",
    )

    args = parser.parse_args(argv)

    if args.all_probes:
        return _run_all_probes(args)

    return _run_single(args)


def _run_single(args: argparse.Namespace) -> int:
    ecosystem = SCENARIOS[args.scenario]()
    probe = PROBES[args.probe]()
    target = args.target or _default_target(ecosystem)

    sim = Simulation(ecosystem, probe, max_steps=args.steps)
    result = sim.run(target)

    total = len(ecosystem.agents)
    if args.json:
        print(report_json(result, total))
    else:
        print(report_text(result, total))

    return 0


def _run_all_probes(args: argparse.Namespace) -> int:
    for probe_name, probe_cls in PROBES.items():
        ecosystem = SCENARIOS[args.scenario]()
        probe = probe_cls()
        target = args.target or _default_target(ecosystem)

        sim = Simulation(ecosystem, probe, max_steps=args.steps)
        result = sim.run(target)

        total = len(ecosystem.agents)
        if args.json:
            print(report_json(result, total))
        else:
            print(report_text(result, total))
        print()

    return 0


def _default_target(ecosystem) -> str:
    from swarm_probe.agent import AgentRole
    for aid, agent in ecosystem.agents.items():
        if agent.role == AgentRole.WORKER:
            return aid
    return next(iter(ecosystem.agents))


if __name__ == "__main__":
    sys.exit(main())
