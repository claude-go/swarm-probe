"""Tests for SARIF reporter."""

import json

from swarm_probe.sarif import report_sarif
from swarm_probe.simulation import SimulationResult, StepRecord


def _make_result(
    probe_name: str = "test_probe",
    compromised: int = 3,
    total: int = 10,
) -> tuple[SimulationResult, int]:
    result = SimulationResult(
        probe_name=probe_name,
        initial_target="target-1",
        total_compromised=compromised,
        total_exposed=1,
        total_contained=0,
        total_clean=total - compromised - 1,
        propagation_path=["target-1", "agent-2", "agent-3"],
        alerts=["alert1"],
    )
    result.steps.append(StepRecord(
        step=0,
        messages_sent=2,
        new_compromised=["agent-2", "agent-3"],
        new_exposed=["agent-4"],
        alerts_raised=["alert1"],
        state_snapshot={},
    ))
    return result, total


def test_sarif_structure():
    result, total = _make_result()
    sarif_str = report_sarif([(result, total)])
    sarif = json.loads(sarif_str)

    assert sarif["version"] == "2.1.0"
    assert "$schema" in sarif
    assert len(sarif["runs"]) == 1

    run = sarif["runs"][0]
    assert run["tool"]["driver"]["name"] == "swarm-probe"
    assert len(run["results"]) == 1


def test_sarif_result_content():
    result, total = _make_result()
    sarif_str = report_sarif([(result, total)])
    sarif = json.loads(sarif_str)

    finding = sarif["runs"][0]["results"][0]
    assert "swarm/" in finding["ruleId"]
    assert "blast radius" in finding["message"]["text"].lower()
    assert finding["properties"]["compromised"] == 3
    assert finding["properties"]["total_agents"] == 10


def test_sarif_multiple_results():
    r1, t1 = _make_result(probe_name="injection", compromised=1)
    r2, t2 = _make_result(probe_name="trust", compromised=5)
    sarif_str = report_sarif([(r1, t1), (r2, t2)])
    sarif = json.loads(sarif_str)

    assert len(sarif["runs"][0]["results"]) == 2
    assert len(sarif["runs"][0]["tool"]["driver"]["rules"]) == 2


def test_sarif_severity_mapping():
    r_low, t_low = _make_result(compromised=1, total=10)
    r_crit, t_crit = _make_result(compromised=10, total=10)

    sarif_low = json.loads(report_sarif([(r_low, t_low)]))
    sarif_crit = json.loads(report_sarif([(r_crit, t_crit)]))

    level_low = sarif_low["runs"][0]["results"][0]["level"]
    level_crit = sarif_crit["runs"][0]["results"][0]["level"]

    assert level_crit == "error"
    assert level_low in ("note", "warning")
