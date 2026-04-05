"""SARIF 2.1.0 reporter for CI/CD integration."""

from __future__ import annotations

import json
from typing import Any

from swarm_probe.metrics import compute_resilience
from swarm_probe.simulation import SimulationResult


_SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json"
_SARIF_VERSION = "2.1.0"


def report_sarif(
    results: list[tuple[SimulationResult, int]],
    tool_version: str = "0.1.0",
) -> str:
    rules: list[dict[str, Any]] = []
    sarif_results: list[dict[str, Any]] = []

    for result, total_agents in results:
        score = compute_resilience(result, total_agents)
        rule_id = f"swarm/{result.probe_name}"

        if rule_id not in [r["id"] for r in rules]:
            rules.append(_build_rule(rule_id, result.probe_name, score.severity))

        sarif_results.append(_build_result(rule_id, result, score, total_agents))

    sarif = {
        "$schema": _SARIF_SCHEMA,
        "version": _SARIF_VERSION,
        "runs": [{
            "tool": {
                "driver": {
                    "name": "swarm-probe",
                    "version": tool_version,
                    "informationUri": "https://github.com/claude-go/swarm-probe",
                    "rules": rules,
                },
            },
            "results": sarif_results,
        }],
    }

    return json.dumps(sarif, indent=2)


def _build_rule(
    rule_id: str, probe_name: str, severity: str,
) -> dict[str, Any]:
    return {
        "id": rule_id,
        "name": probe_name,
        "shortDescription": {
            "text": f"Ecosystem resilience: {probe_name}",
        },
        "defaultConfiguration": {
            "level": _severity_to_level(severity),
        },
    }


def _build_result(
    rule_id: str,
    result: SimulationResult,
    score,
    total_agents: int,
) -> dict[str, Any]:
    return {
        "ruleId": rule_id,
        "level": _severity_to_level(score.severity),
        "message": {
            "text": (
                f"Ecosystem resilience score: {score.overall:.1f}/100 "
                f"[{score.severity}]. "
                f"Blast radius: {score.blast_radius:.0%} "
                f"({result.total_compromised}/{total_agents} agents). "
                f"Propagation path: {' → '.join(result.propagation_path)}."
            ),
        },
        "properties": {
            "score": score.to_dict(),
            "probe": result.probe_name,
            "target": result.initial_target,
            "total_agents": total_agents,
            "compromised": result.total_compromised,
            "alerts": len(result.alerts),
            "steps": len(result.steps),
        },
    }


def _severity_to_level(severity: str) -> str:
    mapping = {
        "CRITICAL": "error",
        "HIGH": "error",
        "MEDIUM": "warning",
        "LOW": "note",
    }
    return mapping.get(severity, "warning")
