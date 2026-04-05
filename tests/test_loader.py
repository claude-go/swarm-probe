"""Tests for ecosystem loader."""

import json
import tempfile
from pathlib import Path

from swarm_probe.agent import AgentRole
from swarm_probe.loader import load_ecosystem


def test_load_json():
    data = {
        "name": "test-eco",
        "agents": [
            {"id": "a1", "role": "worker", "trust_threshold": 0.4},
            {"id": "a2", "role": "validator", "trust_threshold": 0.7},
        ],
        "connections": [
            {"from": "a1", "to": "a2"},
        ],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False,
    ) as f:
        json.dump(data, f)
        f.flush()
        eco = load_ecosystem(f.name)

    assert eco.name == "test-eco"
    assert len(eco.agents) == 2
    assert eco.get_agent("a1").role == AgentRole.WORKER
    assert eco.get_agent("a2").role == AgentRole.VALIDATOR
    assert len(eco.connections) == 1

    Path(f.name).unlink()


def test_load_yaml():
    yaml_content = """name: yaml-test

agents:
  - id: hub
    role: coordinator
    trust_threshold: 0.5
  - id: spoke-1
    role: worker
    trust_threshold: 0.3
  - id: monitor
    role: monitor
    trust_threshold: 0.8

connections:
  - from: hub
    to: spoke-1
  - from: monitor
    to: hub
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False,
    ) as f:
        f.write(yaml_content)
        f.flush()
        eco = load_ecosystem(f.name)

    assert eco.name == "yaml-test"
    assert len(eco.agents) == 3
    assert eco.get_agent("hub").role == AgentRole.COORDINATOR
    assert eco.get_agent("monitor").role == AgentRole.MONITOR
    assert len(eco.connections) == 2

    Path(f.name).unlink()


def test_load_example_microservice():
    eco = load_ecosystem("examples/microservice.yaml")
    assert eco.name == "microservice-cluster"
    assert len(eco.agents) == 6
    assert len(eco.connections) == 7
    assert eco.get_agent("api-gateway").role == AgentRole.COORDINATOR
    assert eco.get_agent("auth-service").role == AgentRole.VALIDATOR


def test_default_values():
    data = {
        "agents": [
            {"id": "minimal"},
        ],
        "connections": [],
    }

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False,
    ) as f:
        json.dump(data, f)
        f.flush()
        eco = load_ecosystem(f.name)

    agent = eco.get_agent("minimal")
    assert agent.role == AgentRole.WORKER
    assert agent.trust_threshold == 0.5

    Path(f.name).unlink()
