"""Agent definition for swarm-probe ecosystems."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentRole(Enum):
    WORKER = "worker"
    COORDINATOR = "coordinator"
    VALIDATOR = "validator"
    ADMIN = "admin"
    MONITOR = "monitor"


class AgentState(Enum):
    CLEAN = "clean"
    EXPOSED = "exposed"
    COMPROMISED = "compromised"
    CONTAINED = "contained"


@dataclass
class Message:
    sender_id: str
    content: str
    msg_type: str = "normal"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Agent:
    agent_id: str
    role: AgentRole
    trust_threshold: float = 0.5
    state: AgentState = AgentState.CLEAN
    trust_scores: dict[str, float] = field(default_factory=dict)
    inbox: list[Message] = field(default_factory=list)
    outbox: list[Message] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    _behavior: AgentBehavior | None = field(default=None, repr=False)

    @property
    def behavior(self) -> AgentBehavior:
        if self._behavior is None:
            self._behavior = DEFAULT_BEHAVIORS.get(
                self.role, AgentBehavior()
            )
        return self._behavior

    @behavior.setter
    def behavior(self, value: AgentBehavior) -> None:
        self._behavior = value

    def receive(self, message: Message) -> None:
        self.inbox.append(message)
        self.history.append({
            "step": "receive",
            "from": message.sender_id,
            "type": message.msg_type,
        })

    def process(self) -> list[Message]:
        responses: list[Message] = []
        for msg in self.inbox:
            result = self.behavior.handle(self, msg)
            if result:
                responses.extend(result)
        self.outbox.extend(responses)
        self.inbox.clear()
        return responses

    def get_trust(self, other_id: str) -> float:
        return self.trust_scores.get(other_id, 0.0)

    def update_trust(self, other_id: str, delta: float) -> None:
        current = self.get_trust(other_id)
        self.trust_scores[other_id] = max(0.0, min(1.0, current + delta))

    def is_compromised(self) -> bool:
        return self.state == AgentState.COMPROMISED

    def compromise(self) -> None:
        self.state = AgentState.COMPROMISED
        self.history.append({"step": "compromised"})

    def expose(self) -> None:
        if self.state == AgentState.CLEAN:
            self.state = AgentState.EXPOSED
            self.history.append({"step": "exposed"})

    def contain(self) -> None:
        self.state = AgentState.CONTAINED
        self.history.append({"step": "contained"})


@dataclass
class AgentBehavior:
    forward_probability: float = 0.0
    validate_incoming: bool = False
    alert_on_suspicious: bool = False

    def handle(self, agent: Agent, message: Message) -> list[Message]:
        if message.msg_type == "instruction" and self.validate_incoming:
            trust = agent.get_trust(message.sender_id)
            if trust < agent.trust_threshold:
                if self.alert_on_suspicious:
                    return [Message(
                        sender_id=agent.agent_id,
                        content=f"ALERT: suspicious instruction from {message.sender_id}",
                        msg_type="alert",
                    )]
                return []

        if message.msg_type == "instruction":
            agent.expose()
            if agent.get_trust(message.sender_id) >= agent.trust_threshold:
                agent.compromise()

        if self.forward_probability > 0 and agent.is_compromised():
            return [Message(
                sender_id=agent.agent_id,
                content=message.content,
                msg_type=message.msg_type,
                metadata={"forwarded_from": message.sender_id},
            )]

        return []


DEFAULT_BEHAVIORS: dict[AgentRole, AgentBehavior] = {
    AgentRole.WORKER: AgentBehavior(forward_probability=0.3),
    AgentRole.COORDINATOR: AgentBehavior(forward_probability=0.7),
    AgentRole.VALIDATOR: AgentBehavior(
        validate_incoming=True,
        alert_on_suspicious=True,
    ),
    AgentRole.ADMIN: AgentBehavior(forward_probability=0.5),
    AgentRole.MONITOR: AgentBehavior(
        validate_incoming=True,
        alert_on_suspicious=True,
    ),
}
