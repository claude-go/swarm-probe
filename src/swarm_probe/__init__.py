"""swarm-probe: Adversarial resilience testing for multi-agent ecosystems."""

__version__ = "0.2.0"

from swarm_probe.agent import Agent, AgentRole, AgentState
from swarm_probe.ecosystem import Ecosystem
from swarm_probe.simulation import Simulation, SimulationResult
from swarm_probe.metrics import ResilienceScore

__all__ = [
    "Agent",
    "AgentRole",
    "AgentState",
    "Ecosystem",
    "Simulation",
    "SimulationResult",
    "ResilienceScore",
]
