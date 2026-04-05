"""Resilience metrics and ecosystem scoring."""

from __future__ import annotations

from dataclasses import dataclass

from swarm_probe.simulation import SimulationResult


@dataclass
class ResilienceScore:
    overall: float
    containment: float
    detection: float
    blast_radius: float
    propagation_speed: float
    severity: str

    def to_dict(self) -> dict[str, object]:
        return {
            "overall": round(self.overall, 1),
            "containment": round(self.containment, 1),
            "detection": round(self.detection, 1),
            "blast_radius": round(self.blast_radius, 2),
            "propagation_speed": round(self.propagation_speed, 2),
            "severity": self.severity,
        }


def compute_resilience(
    result: SimulationResult,
    total_agents: int,
) -> ResilienceScore:
    if total_agents <= 1:
        return ResilienceScore(
            overall=100.0,
            containment=100.0,
            detection=100.0,
            blast_radius=0.0,
            propagation_speed=0.0,
            severity="NONE",
        )

    blast_radius = result.total_compromised / total_agents

    active_steps = [s for s in result.steps if s.new_compromised]
    if active_steps:
        propagation_speed = (
            result.total_compromised / (len(active_steps) + 1)
        )
    else:
        propagation_speed = 0.0

    containment = _score_containment(blast_radius)
    detection = _score_detection(result)

    overall = (containment * 0.4 + detection * 0.3 +
               (1.0 - blast_radius) * 100.0 * 0.3)

    severity = _classify_severity(overall)

    return ResilienceScore(
        overall=overall,
        containment=containment,
        detection=detection,
        blast_radius=blast_radius,
        propagation_speed=propagation_speed,
        severity=severity,
    )


def _score_containment(blast_radius: float) -> float:
    if blast_radius <= 0.1:
        return 100.0
    if blast_radius <= 0.25:
        return 80.0
    if blast_radius <= 0.5:
        return 50.0
    if blast_radius <= 0.75:
        return 20.0
    return 0.0


def _score_detection(result: SimulationResult) -> float:
    if not result.alerts:
        return 0.0

    first_alert_step = None
    for step in result.steps:
        if step.alerts_raised:
            first_alert_step = step.step
            break

    if first_alert_step is None:
        return 0.0

    if first_alert_step == 0:
        return 100.0
    if first_alert_step == 1:
        return 75.0
    if first_alert_step <= 3:
        return 50.0
    return 25.0


def _classify_severity(overall: float) -> str:
    if overall >= 80:
        return "LOW"
    if overall >= 60:
        return "MEDIUM"
    if overall >= 40:
        return "HIGH"
    return "CRITICAL"
