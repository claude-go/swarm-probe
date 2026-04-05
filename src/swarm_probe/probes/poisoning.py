"""Data poisoning probe — corrupts shared data through compromised agent."""

from __future__ import annotations

from swarm_probe.agent import Message
from swarm_probe.ecosystem import Ecosystem
from swarm_probe.probes.base import Probe, ProbeResult


class DataPoisoningProbe(Probe):
    name = "data_poisoning"
    description = (
        "Compromises an agent and has it broadcast corrupted data to all "
        "neighbors. Tests whether validators detect tampered data and "
        "whether poisoned data cascades through the ecosystem."
    )

    def __init__(self, poison_payload: str | None = None):
        self.poison_payload = poison_payload or "POISONED_DATA: metric=999.99"

    def inject(self, ecosystem: Ecosystem, target_id: str) -> ProbeResult:
        target = ecosystem.get_agent(target_id)
        target.compromise()

        neighbors = ecosystem.get_neighbors(target_id)
        messages: list[Message] = []

        for neighbor_id in neighbors:
            msg = Message(
                sender_id=target_id,
                content=self.poison_payload,
                msg_type="data",
                metadata={"probe": self.name, "poisoned": True},
            )
            neighbor = ecosystem.get_agent(neighbor_id)
            neighbor.receive(msg)
            messages.append(msg)

        return ProbeResult(
            probe_name=self.name,
            target_id=target_id,
            success=True,
            messages_sent=messages,
            metadata={"neighbors_poisoned": len(neighbors)},
        )

    def propagate(
        self, ecosystem: Ecosystem, source_id: str, neighbors: list[str],
    ) -> list[Message]:
        source = ecosystem.get_agent(source_id)
        if not source.is_compromised():
            return []

        messages: list[Message] = []
        for neighbor_id in neighbors:
            msg = Message(
                sender_id=source_id,
                content=self.poison_payload,
                msg_type="data",
                metadata={
                    "probe": self.name,
                    "poisoned": True,
                    "hop_from": source_id,
                },
            )
            neighbor = ecosystem.get_agent(neighbor_id)
            neighbor.receive(msg)
            messages.append(msg)

        return messages
