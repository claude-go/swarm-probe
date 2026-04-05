"""Pre-built scenarios for testing ecosystems."""

from __future__ import annotations

from swarm_probe.agent import Agent, AgentRole
from swarm_probe.ecosystem import Ecosystem


def build_corporate_ecosystem() -> Ecosystem:
    """10-agent corporate ecosystem with realistic topology."""
    eco = Ecosystem(name="corporate")

    agents = [
        Agent("admin-1", AgentRole.ADMIN, trust_threshold=0.7),
        Agent("coord-1", AgentRole.COORDINATOR, trust_threshold=0.5),
        Agent("coord-2", AgentRole.COORDINATOR, trust_threshold=0.5),
        Agent("worker-1", AgentRole.WORKER, trust_threshold=0.4),
        Agent("worker-2", AgentRole.WORKER, trust_threshold=0.4),
        Agent("worker-3", AgentRole.WORKER, trust_threshold=0.4),
        Agent("worker-4", AgentRole.WORKER, trust_threshold=0.3),
        Agent("validator-1", AgentRole.VALIDATOR, trust_threshold=0.6),
        Agent("validator-2", AgentRole.VALIDATOR, trust_threshold=0.6),
        Agent("monitor-1", AgentRole.MONITOR, trust_threshold=0.8),
    ]

    for agent in agents:
        eco.add_agent(agent)

    eco.connect("admin-1", "coord-1")
    eco.connect("admin-1", "coord-2")
    eco.connect("coord-1", "worker-1")
    eco.connect("coord-1", "worker-2")
    eco.connect("coord-2", "worker-3")
    eco.connect("coord-2", "worker-4")
    eco.connect("worker-1", "worker-2")
    eco.connect("worker-3", "worker-4")
    eco.connect("validator-1", "coord-1")
    eco.connect("validator-2", "coord-2")
    eco.connect("monitor-1", "admin-1")
    eco.connect("monitor-1", "validator-1")
    eco.connect("monitor-1", "validator-2")

    return eco


def build_flat_ecosystem(n: int = 6) -> Ecosystem:
    """Flat ecosystem where all agents connect to each other."""
    eco = Ecosystem(name="flat")

    for i in range(n):
        role = AgentRole.WORKER if i < n - 1 else AgentRole.MONITOR
        eco.add_agent(Agent(f"agent-{i}", role, trust_threshold=0.4))

    for i in range(n):
        for j in range(i + 1, n):
            eco.connect(f"agent-{i}", f"agent-{j}")

    return eco


def build_star_ecosystem(hub_count: int = 1, spoke_count: int = 5) -> Ecosystem:
    """Star topology with hub(s) and spokes."""
    eco = Ecosystem(name="star")

    for h in range(hub_count):
        eco.add_agent(Agent(f"hub-{h}", AgentRole.COORDINATOR, trust_threshold=0.5))

    for s in range(spoke_count):
        eco.add_agent(Agent(f"spoke-{s}", AgentRole.WORKER, trust_threshold=0.4))
        for h in range(hub_count):
            eco.connect(f"hub-{h}", f"spoke-{s}")

    return eco
