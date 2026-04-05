"""Base probe interface for swarm-probe."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from swarm_probe.agent import Message
from swarm_probe.ecosystem import Ecosystem


@dataclass
class ProbeResult:
    probe_name: str
    target_id: str
    success: bool
    messages_sent: list[Message] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Probe(ABC):
    name: str = "base"
    description: str = ""

    @abstractmethod
    def inject(self, ecosystem: Ecosystem, target_id: str) -> ProbeResult:
        ...

    @abstractmethod
    def propagate(
        self, ecosystem: Ecosystem, source_id: str, neighbors: list[str],
    ) -> list[Message]:
        ...
