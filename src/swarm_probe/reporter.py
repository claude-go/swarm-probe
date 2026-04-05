"""Output reporters for simulation results."""

from __future__ import annotations

import json
from typing import Any

from swarm_probe.metrics import compute_resilience
from swarm_probe.simulation import SimulationResult


def report_text(result: SimulationResult, total_agents: int) -> str:
    score = compute_resilience(result, total_agents)
    lines = [
        f"{'='*60}",
        f"  SWARM-PROBE RESILIENCE REPORT",
        f"{'='*60}",
        f"",
        f"  Probe: {result.probe_name}",
        f"  Target: {result.initial_target}",
        f"  Agents: {total_agents}",
        f"  Steps: {len(result.steps)}",
        f"",
        f"  SCORE: {score.overall:.1f}/100  [{score.severity}]",
        f"",
        f"  Containment:        {score.containment:.0f}/100",
        f"  Detection:          {score.detection:.0f}/100",
        f"  Blast radius:       {score.blast_radius:.0%}",
        f"  Propagation speed:  {score.propagation_speed:.1f} agents/step",
        f"",
    ]

    lines.append(f"  Propagation path:")
    for i, agent_id in enumerate(result.propagation_path):
        prefix = "  [0]" if i == 0 else f"  [{i}]"
        lines.append(f"    {prefix} {agent_id}")

    if result.alerts:
        lines.append(f"")
        lines.append(f"  Alerts ({len(result.alerts)}):")
        for alert in result.alerts:
            lines.append(f"    ! {alert}")

    lines.append(f"")
    lines.append(f"  Final state:")
    if result.steps:
        last = result.steps[-1]
        for aid, state in sorted(last.state_snapshot.items()):
            marker = _state_marker(state)
            lines.append(f"    {marker} {aid}: {state}")

    lines.append(f"{'='*60}")
    return "\n".join(lines)


def report_json(result: SimulationResult, total_agents: int) -> str:
    score = compute_resilience(result, total_agents)
    data: dict[str, Any] = {
        "probe": result.probe_name,
        "target": result.initial_target,
        "total_agents": total_agents,
        "score": score.to_dict(),
        "propagation_path": result.propagation_path,
        "alerts": result.alerts,
        "counts": {
            "compromised": result.total_compromised,
            "exposed": result.total_exposed,
            "contained": result.total_contained,
            "clean": result.total_clean,
        },
        "steps": len(result.steps),
    }
    return json.dumps(data, indent=2)


def _state_marker(state: str) -> str:
    markers = {
        "clean": "[OK]",
        "exposed": "[!!]",
        "compromised": "[XX]",
        "contained": "[~~]",
    }
    return markers.get(state, "[??]")
