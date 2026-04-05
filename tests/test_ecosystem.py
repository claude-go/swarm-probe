"""Tests for Ecosystem."""

import pytest

from swarm_probe.agent import Agent, AgentRole, AgentState
from swarm_probe.ecosystem import Ecosystem


def test_add_agent():
    eco = Ecosystem()
    agent = Agent("a1", AgentRole.WORKER)
    eco.add_agent(agent)
    assert "a1" in eco.agents
    assert eco.get_agent("a1") is agent


def test_get_agent_not_found():
    eco = Ecosystem()
    with pytest.raises(KeyError):
        eco.get_agent("missing")


def test_connect_agents():
    eco = Ecosystem()
    eco.add_agent(Agent("a1", AgentRole.WORKER))
    eco.add_agent(Agent("a2", AgentRole.WORKER))
    eco.connect("a1", "a2")
    assert len(eco.connections) == 1


def test_connect_missing_agent():
    eco = Ecosystem()
    eco.add_agent(Agent("a1", AgentRole.WORKER))
    with pytest.raises(ValueError):
        eco.connect("a1", "missing")


def test_get_neighbors_bidirectional():
    eco = Ecosystem()
    eco.add_agent(Agent("a1", AgentRole.WORKER))
    eco.add_agent(Agent("a2", AgentRole.WORKER))
    eco.add_agent(Agent("a3", AgentRole.WORKER))
    eco.connect("a1", "a2")
    eco.connect("a1", "a3")

    neighbors = eco.get_neighbors("a1")
    assert set(neighbors) == {"a2", "a3"}

    neighbors_a2 = eco.get_neighbors("a2")
    assert "a1" in neighbors_a2


def test_get_neighbors_unidirectional():
    eco = Ecosystem()
    eco.add_agent(Agent("a1", AgentRole.WORKER))
    eco.add_agent(Agent("a2", AgentRole.WORKER))
    eco.connect("a1", "a2", bidirectional=False)

    assert "a2" in eco.get_neighbors("a1")
    assert "a1" not in eco.get_neighbors("a2")


def test_count_by_state():
    eco = Ecosystem()
    eco.add_agent(Agent("a1", AgentRole.WORKER))
    eco.add_agent(Agent("a2", AgentRole.WORKER))
    eco.add_agent(Agent("a3", AgentRole.WORKER))

    eco.get_agent("a2").compromise()
    counts = eco.count_by_state()

    assert counts[AgentState.CLEAN] == 2
    assert counts[AgentState.COMPROMISED] == 1


def test_get_compromised():
    eco = Ecosystem()
    eco.add_agent(Agent("a1", AgentRole.WORKER))
    eco.add_agent(Agent("a2", AgentRole.WORKER))
    eco.get_agent("a1").compromise()

    assert eco.get_compromised() == ["a1"]
    assert eco.get_clean() == ["a2"]


def test_reset():
    eco = Ecosystem()
    eco.add_agent(Agent("a1", AgentRole.WORKER))
    eco.get_agent("a1").compromise()
    eco.reset()
    assert eco.get_agent("a1").state == AgentState.CLEAN
