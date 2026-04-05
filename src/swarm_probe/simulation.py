"""Simulation engine — runs probes through ecosystems step by step."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from swarm_probe.agent import AgentState
from swarm_probe.ecosystem import Ecosystem
from swarm_probe.probes.base import Probe


@dataclass
class StepRecord:
    step: int
    messages_sent: int
    new_compromised: list[str]
    new_exposed: list[str]
    alerts_raised: list[str]
    state_snapshot: dict[str, str]


@dataclass
class SimulationResult:
    probe_name: str
    initial_target: str
    steps: list[StepRecord] = field(default_factory=list)
    total_compromised: int = 0
    total_exposed: int = 0
    total_contained: int = 0
    total_clean: int = 0
    propagation_path: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Simulation:
    def __init__(
        self,
        ecosystem: Ecosystem,
        probe: Probe,
        max_steps: int = 10,
    ):
        self.ecosystem = ecosystem
        self.probe = probe
        self.max_steps = max_steps

    def run(self, target_id: str) -> SimulationResult:
        result = SimulationResult(
            probe_name=self.probe.name,
            initial_target=target_id,
        )

        inject_result = self.probe.inject(self.ecosystem, target_id)
        result.propagation_path.append(target_id)

        for step_num in range(self.max_steps):
            step = self._run_step(step_num, result)
            result.steps.append(step)

            if step.messages_sent == 0 and not step.new_compromised:
                break

        counts = self.ecosystem.count_by_state()
        result.total_compromised = counts[AgentState.COMPROMISED]
        result.total_exposed = counts[AgentState.EXPOSED]
        result.total_contained = counts[AgentState.CONTAINED]
        result.total_clean = counts[AgentState.CLEAN]
        result.metadata["inject_result"] = inject_result.metadata

        return result

    def _run_step(self, step_num: int, result: SimulationResult) -> StepRecord:
        compromised_before = set(self.ecosystem.get_compromised())
        messages_sent = 0
        alerts: list[str] = []

        for agent_id in list(self.ecosystem.agents):
            agent = self.ecosystem.get_agent(agent_id)

            if agent.is_compromised():
                neighbors = self.ecosystem.get_neighbors(agent_id)
                msgs = self.probe.propagate(
                    self.ecosystem, agent_id, neighbors,
                )
                messages_sent += len(msgs)

            responses = agent.process()
            for resp in responses:
                if resp.msg_type == "alert":
                    alerts.append(
                        f"[step {step_num}] {agent_id}: {resp.content}"
                    )

        compromised_after = set(self.ecosystem.get_compromised())
        new_compromised = list(compromised_after - compromised_before)
        result.propagation_path.extend(new_compromised)
        result.alerts.extend(alerts)

        exposed = [
            aid for aid, a in self.ecosystem.agents.items()
            if a.state == AgentState.EXPOSED
        ]

        snapshot = {
            aid: a.state.value
            for aid, a in self.ecosystem.agents.items()
        }

        return StepRecord(
            step=step_num,
            messages_sent=messages_sent,
            new_compromised=new_compromised,
            new_exposed=exposed,
            alerts_raised=alerts,
            state_snapshot=snapshot,
        )
