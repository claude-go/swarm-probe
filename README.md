# swarm-probe

[![PyPI version](https://img.shields.io/pypi/v/swarm-probe)](https://pypi.org/project/swarm-probe/)

Adversarial resilience testing for multi-agent ecosystems.

Everyone tests individual AI agents. Nobody tests what happens when thousands of agents interact — and one gets compromised. **swarm-probe** simulates adversarial attacks against multi-agent ecosystems and measures collective resilience.

## Why

AI agents don't exist in isolation. They form ecosystems — coordinators, workers, validators, monitors — connected through trust relationships. A single compromised agent can cascade through an entire organization.

Current tools test agents one at a time. swarm-probe tests the **ecosystem**.

## Install

```bash
pip install swarm-probe
```

## Quick Start

```bash
# Test a corporate ecosystem with instruction injection
swarm-probe corporate --probe injection --target worker-1

# Test with trust manipulation (builds fake trust, then exploits)
swarm-probe corporate --probe trust --target worker-1

# Run all probes against a scenario
swarm-probe corporate --all-probes

# JSON output for CI/CD
swarm-probe corporate --probe injection --json
```

## What It Does

1. **Builds an ecosystem** — agents with roles (worker, coordinator, validator, admin, monitor), trust relationships, and behavioral rules
2. **Injects a probe** — compromises one agent with an adversarial attack
3. **Simulates propagation** — watches how the attack spreads through trust relationships step by step
4. **Scores resilience** — containment, detection, blast radius, propagation speed

## Probes

| Probe | Description |
|-------|-------------|
| `injection` | Compromises an agent with malicious instructions, measures propagation via trust |
| `trust` | Builds fake trust through benign messages, then exploits elevated trust |
| `poisoning` | Feeds corrupted data through a compromised agent to neighbors |

## Scenarios

| Scenario | Description |
|----------|-------------|
| `corporate` | 10-agent hierarchy: admin, coordinators, workers, validators, monitor |
| `flat` | Fully connected mesh — worst case for propagation |
| `star` | Hub-and-spoke — tests single point of failure |

## Resilience Score

```
============================================================
  SWARM-PROBE RESILIENCE REPORT
============================================================

  Probe: trust_manipulation
  Target: worker-1
  Agents: 10
  Steps: 10

  SCORE: 56.0/100  [HIGH]

  Containment:        50/100
  Detection:          50/100
  Blast radius:       30%
  Propagation speed:  1.0 agents/step

  Propagation path:
      [0] worker-1
      [1] worker-2
      [2] coord-1

  Alerts (8):
    ! [step 2] validator-1: ALERT: suspicious instruction from coord-1
============================================================
```

## Scoring

- **Containment** (40%): How well the ecosystem limited the blast radius
- **Detection** (30%): How quickly validators/monitors raised alerts
- **Blast Radius** (30%): Percentage of agents compromised

| Score | Severity |
|-------|----------|
| 80-100 | LOW |
| 60-79 | MEDIUM |
| 40-59 | HIGH |
| 0-39 | CRITICAL |

## Python API

```python
from swarm_probe import Agent, AgentRole, Ecosystem, Simulation
from swarm_probe.probes import InstructionInjectionProbe
from swarm_probe.metrics import compute_resilience

# Build your ecosystem
eco = Ecosystem(name="my-system")
eco.add_agent(Agent("hub", AgentRole.COORDINATOR))
eco.add_agent(Agent("w1", AgentRole.WORKER))
eco.add_agent(Agent("w2", AgentRole.WORKER))
eco.connect("hub", "w1")
eco.connect("hub", "w2")

# Run a probe
probe = InstructionInjectionProbe()
sim = Simulation(eco, probe, max_steps=10)
result = sim.run("w1")

# Score it
score = compute_resilience(result, total_agents=len(eco.agents))
print(f"Score: {score.overall}/100 [{score.severity}]")
```

## Zero Dependencies

Pure Python. No external dependencies. Works with Python 3.10+.

## Related

- [agent-probe](https://github.com/claude-go/agent-probe) — Adversarial testing for individual AI agents
- [clawhub-bridge](https://github.com/claude-go/clawhub-bridge) — Security scanning for AI agent skills

## License

MIT
