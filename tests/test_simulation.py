"""Tests for simulation engine."""

from swarm_probe.agent import Agent, AgentRole, AgentState
from swarm_probe.ecosystem import Ecosystem
from swarm_probe.probes.injection import InstructionInjectionProbe
from swarm_probe.probes.trust import TrustManipulationProbe
from swarm_probe.simulation import Simulation


def _build_chain_eco() -> Ecosystem:
    """a -> b -> c (unidirectional chain)."""
    eco = Ecosystem(name="chain")
    eco.add_agent(Agent("a", AgentRole.WORKER, trust_threshold=0.3))
    eco.add_agent(Agent("b", AgentRole.WORKER, trust_threshold=0.3))
    eco.add_agent(Agent("c", AgentRole.WORKER, trust_threshold=0.3))
    eco.connect("a", "b", bidirectional=False)
    eco.connect("b", "c", bidirectional=False)
    return eco


def test_simulation_runs():
    eco = _build_chain_eco()
    probe = InstructionInjectionProbe()
    sim = Simulation(eco, probe, max_steps=5)
    result = sim.run("a")

    assert result.probe_name == "instruction_injection"
    assert result.initial_target == "a"
    assert len(result.steps) > 0
    assert result.total_compromised >= 1


def test_simulation_propagation():
    eco = _build_chain_eco()
    for aid in eco.agents:
        agent = eco.get_agent(aid)
        for other in eco.agents:
            if other != aid:
                agent.update_trust(other, 0.5)

    probe = InstructionInjectionProbe()
    sim = Simulation(eco, probe, max_steps=5)
    result = sim.run("a")

    assert result.total_compromised >= 1
    assert "a" in result.propagation_path


def test_simulation_with_validator():
    eco = Ecosystem(name="validated")
    eco.add_agent(Agent("w1", AgentRole.WORKER, trust_threshold=0.3))
    eco.add_agent(Agent("v1", AgentRole.VALIDATOR, trust_threshold=0.8))
    eco.connect("w1", "v1")

    probe = InstructionInjectionProbe()
    sim = Simulation(eco, probe, max_steps=5)
    result = sim.run("w1")

    assert eco.get_agent("v1").state != AgentState.COMPROMISED
    assert len(result.alerts) > 0


def test_simulation_stops_when_no_activity():
    eco = Ecosystem(name="isolated")
    eco.add_agent(Agent("alone", AgentRole.WORKER))

    probe = InstructionInjectionProbe()
    sim = Simulation(eco, probe, max_steps=10)
    result = sim.run("alone")

    assert len(result.steps) < 10


def test_simulation_trust_probe():
    eco = Ecosystem(name="trust-test")
    eco.add_agent(Agent("a", AgentRole.WORKER, trust_threshold=0.4))
    eco.add_agent(Agent("b", AgentRole.WORKER, trust_threshold=0.4))
    eco.connect("a", "b")

    probe = TrustManipulationProbe(warmup_rounds=3, trust_boost=0.2)
    sim = Simulation(eco, probe, max_steps=5)
    result = sim.run("a")

    assert result.total_compromised >= 1
