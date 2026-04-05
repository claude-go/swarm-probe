"""Ecosystem: graph of interconnected agents."""

from __future__ import annotations

from dataclasses import dataclass, field

from swarm_probe.agent import Agent, AgentState


@dataclass
class Connection:
    source_id: str
    target_id: str
    weight: float = 1.0
    bidirectional: bool = True


@dataclass
class Ecosystem:
    name: str = "default"
    agents: dict[str, Agent] = field(default_factory=dict)
    connections: list[Connection] = field(default_factory=list)

    def add_agent(self, agent: Agent) -> None:
        self.agents[agent.agent_id] = agent

    def connect(
        self,
        source_id: str,
        target_id: str,
        weight: float = 1.0,
        bidirectional: bool = True,
    ) -> None:
        if source_id not in self.agents or target_id not in self.agents:
            raise ValueError(f"Both agents must exist: {source_id}, {target_id}")
        self.connections.append(Connection(
            source_id=source_id,
            target_id=target_id,
            weight=weight,
            bidirectional=bidirectional,
        ))

    def get_neighbors(self, agent_id: str) -> list[str]:
        neighbors: list[str] = []
        for conn in self.connections:
            if conn.source_id == agent_id:
                neighbors.append(conn.target_id)
            elif conn.bidirectional and conn.target_id == agent_id:
                neighbors.append(conn.source_id)
        return neighbors

    def get_agent(self, agent_id: str) -> Agent:
        if agent_id not in self.agents:
            raise KeyError(f"Agent not found: {agent_id}")
        return self.agents[agent_id]

    def count_by_state(self) -> dict[AgentState, int]:
        counts: dict[AgentState, int] = {s: 0 for s in AgentState}
        for agent in self.agents.values():
            counts[agent.state] += 1
        return counts

    def get_compromised(self) -> list[str]:
        return [
            aid for aid, a in self.agents.items()
            if a.state == AgentState.COMPROMISED
        ]

    def get_clean(self) -> list[str]:
        return [
            aid for aid, a in self.agents.items()
            if a.state == AgentState.CLEAN
        ]

    def reset(self) -> None:
        for agent in self.agents.values():
            agent.state = AgentState.CLEAN
            agent.inbox.clear()
            agent.outbox.clear()
            agent.history.clear()
            agent.trust_scores.clear()
