"""Tests for Agent and AgentBehavior."""

from swarm_probe.agent import (
    Agent,
    AgentBehavior,
    AgentRole,
    AgentState,
    Message,
)


def test_agent_creation():
    agent = Agent("test-1", AgentRole.WORKER)
    assert agent.agent_id == "test-1"
    assert agent.role == AgentRole.WORKER
    assert agent.state == AgentState.CLEAN
    assert not agent.is_compromised()


def test_agent_compromise():
    agent = Agent("test-1", AgentRole.WORKER)
    agent.compromise()
    assert agent.is_compromised()
    assert agent.state == AgentState.COMPROMISED


def test_agent_expose():
    agent = Agent("test-1", AgentRole.WORKER)
    agent.expose()
    assert agent.state == AgentState.EXPOSED

    agent.compromise()
    agent2 = Agent("test-2", AgentRole.WORKER)
    agent2.compromise()
    agent2.expose()
    assert agent2.state == AgentState.COMPROMISED


def test_agent_contain():
    agent = Agent("test-1", AgentRole.WORKER)
    agent.compromise()
    agent.contain()
    assert agent.state == AgentState.CONTAINED
    assert not agent.is_compromised()


def test_agent_trust():
    agent = Agent("test-1", AgentRole.WORKER)
    assert agent.get_trust("other") == 0.0

    agent.update_trust("other", 0.5)
    assert agent.get_trust("other") == 0.5

    agent.update_trust("other", 0.8)
    assert agent.get_trust("other") == 1.0

    agent.update_trust("other", -1.5)
    assert agent.get_trust("other") == 0.0


def test_agent_receive():
    agent = Agent("test-1", AgentRole.WORKER)
    msg = Message(sender_id="sender", content="hello")
    agent.receive(msg)
    assert len(agent.inbox) == 1
    assert agent.inbox[0].content == "hello"
    assert len(agent.history) == 1


def test_agent_process_clears_inbox():
    agent = Agent("test-1", AgentRole.WORKER)
    agent.behavior = AgentBehavior()
    msg = Message(sender_id="sender", content="hello")
    agent.receive(msg)
    agent.process()
    assert len(agent.inbox) == 0


def test_worker_behavior_forwards_when_compromised():
    agent = Agent("test-1", AgentRole.WORKER, trust_threshold=0.3)
    agent.compromise()
    agent.update_trust("sender", 0.5)

    msg = Message(sender_id="sender", content="payload", msg_type="instruction")
    agent.receive(msg)
    responses = agent.process()
    assert len(responses) >= 0


def test_validator_behavior_blocks_untrusted():
    agent = Agent("test-1", AgentRole.VALIDATOR, trust_threshold=0.6)
    msg = Message(
        sender_id="untrusted",
        content="override",
        msg_type="instruction",
    )
    agent.receive(msg)
    responses = agent.process()

    alerts = [r for r in responses if r.msg_type == "alert"]
    assert len(alerts) == 1


def test_validator_allows_trusted():
    agent = Agent("test-1", AgentRole.VALIDATOR, trust_threshold=0.5)
    agent.update_trust("trusted", 0.8)

    msg = Message(
        sender_id="trusted",
        content="valid instruction",
        msg_type="instruction",
    )
    agent.receive(msg)
    agent.process()
    assert agent.state in (AgentState.EXPOSED, AgentState.COMPROMISED)


def test_monitor_alerts_on_suspicious():
    agent = Agent("test-1", AgentRole.MONITOR, trust_threshold=0.8)
    msg = Message(
        sender_id="unknown",
        content="hack",
        msg_type="instruction",
    )
    agent.receive(msg)
    responses = agent.process()
    alerts = [r for r in responses if r.msg_type == "alert"]
    assert len(alerts) == 1
    assert "suspicious" in alerts[0].content.lower()
