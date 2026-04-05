"""Tests for adversarial probes."""

from swarm_probe.agent import Agent, AgentRole, AgentState
from swarm_probe.ecosystem import Ecosystem
from swarm_probe.probes.injection import InstructionInjectionProbe
from swarm_probe.probes.trust import TrustManipulationProbe
from swarm_probe.probes.poisoning import DataPoisoningProbe


def _build_small_eco() -> Ecosystem:
    eco = Ecosystem(name="test")
    eco.add_agent(Agent("w1", AgentRole.WORKER, trust_threshold=0.4))
    eco.add_agent(Agent("w2", AgentRole.WORKER, trust_threshold=0.4))
    eco.add_agent(Agent("v1", AgentRole.VALIDATOR, trust_threshold=0.6))
    eco.connect("w1", "w2")
    eco.connect("w1", "v1")
    return eco


def test_injection_compromises_target():
    eco = _build_small_eco()
    probe = InstructionInjectionProbe()
    result = probe.inject(eco, "w1")

    assert result.success
    assert result.target_id == "w1"
    assert eco.get_agent("w1").is_compromised()
    assert "canary" in result.metadata


def test_injection_propagates():
    eco = _build_small_eco()
    probe = InstructionInjectionProbe()
    probe.inject(eco, "w1")

    neighbors = eco.get_neighbors("w1")
    messages = probe.propagate(eco, "w1", neighbors)

    assert len(messages) == 2
    for msg in messages:
        assert msg.msg_type == "instruction"
        assert probe.canary in msg.content


def test_injection_no_propagate_if_clean():
    eco = _build_small_eco()
    probe = InstructionInjectionProbe()
    neighbors = eco.get_neighbors("w1")
    messages = probe.propagate(eco, "w1", neighbors)
    assert len(messages) == 0


def test_trust_manipulation_builds_trust():
    eco = _build_small_eco()
    probe = TrustManipulationProbe(warmup_rounds=3, trust_boost=0.2)
    result = probe.inject(eco, "w1")

    assert eco.get_agent("w1").is_compromised()
    assert result.metadata["warmup_rounds"] == 3

    w2_trust = eco.get_agent("w2").get_trust("w1")
    assert w2_trust >= 0.6


def test_trust_manipulation_propagates():
    eco = _build_small_eco()
    probe = TrustManipulationProbe(warmup_rounds=3, trust_boost=0.2)
    probe.inject(eco, "w1")

    neighbors = eco.get_neighbors("w1")
    messages = probe.propagate(eco, "w1", neighbors)

    assert len(messages) == 2
    for msg in messages:
        assert msg.msg_type == "instruction"


def test_poisoning_sends_to_neighbors():
    eco = _build_small_eco()
    probe = DataPoisoningProbe()
    result = probe.inject(eco, "w1")

    assert eco.get_agent("w1").is_compromised()
    assert result.metadata["neighbors_poisoned"] == 2


def test_poisoning_propagates():
    eco = _build_small_eco()
    probe = DataPoisoningProbe()
    probe.inject(eco, "w1")

    neighbors = eco.get_neighbors("w1")
    messages = probe.propagate(eco, "w1", neighbors)

    assert len(messages) == 2
    for msg in messages:
        assert msg.msg_type == "data"
        assert msg.metadata.get("poisoned") is True
