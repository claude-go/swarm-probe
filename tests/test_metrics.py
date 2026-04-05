"""Tests for resilience metrics."""

from swarm_probe.metrics import (
    ResilienceScore,
    compute_resilience,
    _score_containment,
    _score_detection,
    _classify_severity,
)
from swarm_probe.simulation import SimulationResult, StepRecord


def _make_result(
    compromised: int = 1,
    exposed: int = 0,
    contained: int = 0,
    clean: int = 9,
    steps_with_compromised: int = 1,
    alerts: list[str] | None = None,
    alert_step: int | None = None,
) -> SimulationResult:
    result = SimulationResult(
        probe_name="test",
        initial_target="t1",
        total_compromised=compromised,
        total_exposed=exposed,
        total_contained=contained,
        total_clean=clean,
        alerts=alerts or [],
    )

    for i in range(max(steps_with_compromised, 1)):
        new_comp = ["x"] if i < steps_with_compromised else []
        step_alerts = []
        if alert_step is not None and i == alert_step:
            step_alerts = ["alert!"]

        result.steps.append(StepRecord(
            step=i,
            messages_sent=1,
            new_compromised=new_comp,
            new_exposed=[],
            alerts_raised=step_alerts,
            state_snapshot={},
        ))

    return result


def test_compute_resilience_clean():
    result = _make_result(compromised=1, clean=9)
    score = compute_resilience(result, total_agents=10)
    assert score.blast_radius == 0.1
    assert score.containment == 100.0
    assert score.severity in ("LOW", "MEDIUM")


def test_compute_resilience_half_compromised():
    result = _make_result(compromised=5, clean=5)
    score = compute_resilience(result, total_agents=10)
    assert score.blast_radius == 0.5
    assert score.containment == 50.0
    assert score.severity in ("MEDIUM", "HIGH", "CRITICAL")


def test_compute_resilience_all_compromised():
    result = _make_result(compromised=10, clean=0)
    score = compute_resilience(result, total_agents=10)
    assert score.blast_radius == 1.0
    assert score.containment == 0.0
    assert score.severity == "CRITICAL"


def test_detection_with_early_alert():
    result = _make_result(
        compromised=3,
        clean=7,
        alerts=["alert!"],
        alert_step=0,
    )
    score = compute_resilience(result, total_agents=10)
    assert score.detection == 100.0


def test_detection_no_alerts():
    result = _make_result(compromised=3, clean=7)
    score = compute_resilience(result, total_agents=10)
    assert score.detection == 0.0


def test_single_agent():
    result = _make_result(compromised=1, clean=0)
    score = compute_resilience(result, total_agents=1)
    assert score.overall == 100.0


def test_containment_scores():
    assert _score_containment(0.05) == 100.0
    assert _score_containment(0.2) == 80.0
    assert _score_containment(0.4) == 50.0
    assert _score_containment(0.6) == 20.0
    assert _score_containment(0.9) == 0.0


def test_severity_classification():
    assert _classify_severity(90) == "LOW"
    assert _classify_severity(70) == "MEDIUM"
    assert _classify_severity(50) == "HIGH"
    assert _classify_severity(20) == "CRITICAL"


def test_score_to_dict():
    score = ResilienceScore(
        overall=75.5,
        containment=80.0,
        detection=50.0,
        blast_radius=0.3,
        propagation_speed=1.5,
        severity="MEDIUM",
    )
    d = score.to_dict()
    assert d["overall"] == 75.5
    assert d["severity"] == "MEDIUM"
