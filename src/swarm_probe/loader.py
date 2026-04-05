"""Load custom ecosystems from YAML/JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from swarm_probe.agent import Agent, AgentBehavior, AgentRole
from swarm_probe.ecosystem import Ecosystem


_ROLE_MAP = {
    "worker": AgentRole.WORKER,
    "coordinator": AgentRole.COORDINATOR,
    "validator": AgentRole.VALIDATOR,
    "admin": AgentRole.ADMIN,
    "monitor": AgentRole.MONITOR,
}


def load_ecosystem(filepath: str) -> Ecosystem:
    path = Path(filepath)
    data = _read_file(path)
    return _parse_ecosystem(data)


def _read_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")

    if path.suffix in (".yaml", ".yml"):
        return _parse_yaml(text)

    return json.loads(text)


def _parse_yaml(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {"agents": [], "connections": []}
    current_section = None
    current_item: dict[str, Any] = {}

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped == "agents:":
            current_section = "agents"
            continue
        elif stripped == "connections:":
            if current_item:
                result[current_section].append(current_item)  # type: ignore[index]
                current_item = {}
            current_section = "connections"
            continue
        elif stripped.startswith("name:") and not line.startswith(" "):
            result["name"] = stripped.split(":", 1)[1].strip()
            continue

        if current_section and stripped.startswith("- "):
            if current_item:
                result[current_section].append(current_item)  # type: ignore[index]
            current_item = {}
            kv = stripped[2:].strip()
            if ":" in kv:
                key, val = kv.split(":", 1)
                current_item[key.strip()] = _parse_value(val.strip())
        elif current_section and ":" in stripped:
            key, val = stripped.split(":", 1)
            current_item[key.strip()] = _parse_value(val.strip())

    if current_item and current_section:
        result[current_section].append(current_item)  # type: ignore[index]

    return result


def _parse_value(val: str) -> Any:
    if val.lower() in ("true", "yes"):
        return True
    if val.lower() in ("false", "no"):
        return False
    try:
        return float(val)
    except ValueError:
        return val


def _parse_ecosystem(data: dict[str, Any]) -> Ecosystem:
    name = data.get("name", "custom")
    eco = Ecosystem(name=name)

    for agent_data in data.get("agents", []):
        agent = _parse_agent(agent_data)
        eco.add_agent(agent)

    for conn_data in data.get("connections", []):
        eco.connect(
            source_id=conn_data["from"],
            target_id=conn_data["to"],
            weight=conn_data.get("weight", 1.0),
            bidirectional=conn_data.get("bidirectional", True),
        )

    return eco


def _parse_agent(data: dict[str, Any]) -> Agent:
    agent_id = data["id"]
    role_str = data.get("role", "worker").lower()
    role = _ROLE_MAP.get(role_str, AgentRole.WORKER)
    trust_threshold = float(data.get("trust_threshold", 0.5))

    agent = Agent(agent_id, role, trust_threshold=trust_threshold)

    behavior_data = data.get("behavior", {})
    if behavior_data:
        agent.behavior = AgentBehavior(
            forward_probability=float(behavior_data.get("forward_probability", 0.0)),
            validate_incoming=bool(behavior_data.get("validate_incoming", False)),
            alert_on_suspicious=bool(behavior_data.get("alert_on_suspicious", False)),
        )

    return agent
