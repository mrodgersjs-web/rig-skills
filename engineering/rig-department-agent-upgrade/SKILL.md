---
name: rig-department-agent-upgrade
description: Upgrade named RIG department agents from persona/role into full PAI operating systems — substrate, goals, loops, skills, harnesses, quality profiles, data models. Use when building or upgrading any department agent.
tags:
  - rig
  - department-pai
  - agent-upgrade
  - darius
---

# RIG Department Agent Upgrade

## When To Use
- Upgrading a named agent from persona to full PAI
- Building substrate, goals, loops for a department agent
- Creating team models and worker definitions
- Setting up data models and memory policies

## Upgrade Checklist

### Per Agent (5 files)
1. **Substrate Upgrade.md** — Identity, outcome, ARR mechanism, boundaries, quality gates
2. **Daily Weekly Monthly Goals.md** — Goal cadence tied to $10M ARR
3. **Loop Contracts.md** — 3 recurring loops with metrics and proof
4. **Skill Harness Map.md** — Skills and harnesses with quality gates
5. **Source Intelligence Map.md** — Source families, scrape queries, evidence gaps

### System Infrastructure (10 files)
1. `registry.yaml` — System registry, paths, operating law
2. `agents.yaml` — All department agents
3. `goals.yaml` — Daily/weekly/monthly goals per agent
4. `sources.yaml` — Source families and record schema
5. `examples.yaml` — Normalized example schema
6. `processes.yaml` — Process pattern schema
7. `skills.yaml` — Skill candidate schema
8. `harnesses.yaml` — Harness contract schema
9. `loops.yaml` — Loop contract schema
10. `memory_policy.yaml` — Memory promotion ladder

### Templates (3 files)
1. Daily Command Packet template
2. Weekly Revenue Review template
3. Monthly ARR Review template

### Doctor Script
`doctor.py` — Validates all artifacts exist and pass checks

## Agent Vault Structure
```
~/Documents/JakeStudio/Agent Vaults/{agent}/
├── README.md
├── Inputs Required.md
├── Great Output Examples.md
├── What Good Looks Like.md
├── Work Ledger.md
├── Substrate Upgrade.md
├── Daily Weekly Monthly Goals.md
├── Loop Contracts.md
├── Skill Harness Map.md
├── Source Intelligence Map.md
├── PAI Substrate.md (for upgraded agents)
├── Team Model.md (for upgraded agents)
├── Quality Profiles.md (for upgraded agents)
├── Knowledge/
│   └── {topic}/
├── Content/
│   ├── LinkedIn/
│   ├── Newsletter/
│   └── ...
├── Intel/
│   └── competitors/
├── Missions/
│   └── meeting-prep/
└── Proof/
```

## Substrate Upgrade Template

```yaml
---
date: "YYYY-MM-DD"
type: "substrate-upgrade"
tags: [rig, department-pai, {agent}]
ai-first: true
agent: "{agent}"
department: "{department}"
---

# {Agent} Substrate Upgrade

## Agent Identity
- ID: {agent}
- Display Name: {Name}
- Department: {Department}
- Telos: {Telos}

## Department Outcome
{What this department produces for RIG}

## ARR Mechanism
{How this department contributes to $10M ARR}

## Allowed Work Surfaces
- Local filesystem
- Obsidian vault
- GBrain
- Web search
- Local tools

## Gate-D Boundaries
No public claims, sends, publishes, deploys, or provider writes without Mike approval.

## Required Inputs
1. Task brief
2. Source evidence
3. Quality profile
4. Gate-D boundary
5. Proof path

## Output Families
- Research artifacts
- Strategy documents
- Execution plans
- Quality scores
- Proof packets

## Skills
| Skill | Use When | Quality Gate |
|---|---|---|
| {skill} | {trigger} | {gate} |

## Harnesses
| Harness | Job | Proof Command |
|---|---|---|
| {harness} | {job} | {command} |

## Loop Contracts
| Loop | Cadence | Metric |
|---|---|---|
| {loop} | {cadence} | {metric} |

## Quality Gates
- {gate_1}
- {gate_2}

## Memory Promotion Policy
- Promote: good_example, weak_example, decision, pattern, work_trace
- Never: raw secrets, unverified claims, public claims without source
```

## Goals Template

```yaml
---
date: "YYYY-MM-DD"
type: "goals"
tags: [rig, department-pai, {agent}]
---

# {Agent} Goals

| Cadence | Goal | ARR Mechanism |
|---|---|---|
| Daily | {daily_goal} | {mechanism} |
| Weekly | {weekly_goal} | {mechanism} |
| Monthly | {monthly_goal} | {mechanism} |

## Lead Measures
- {measure_1}
- {measure_2}

## Proof Artifacts
- {artifact_1}
- {artifact_2}
```

## Loop Contracts Template

```yaml
---
date: "YYYY-MM-DD"
type: "loop-contracts"
tags: [rig, department-pai, {agent}]
---

# {Agent} Loop Contracts

## {loop_name}
- Cadence: {daily|weekly|monthly}
- Objective: {objective}
- Metric: {metric}
- Max Runtime: {minutes}
- Allowed Tools: {tools}
- Stop Conditions: {conditions}
- Outputs: {outputs}
- Proof Required: true
```

## Parallel Execution Strategy

### Batch 1 (subagent): System infrastructure
- Registry YAML files
- Doctor script
- Templates

### Batch 2 (subagent): Agent vault files (4 agents)
- 5 files × 4 agents = 20 files

### Batch 3 (subagent): Agent vault files (4 agents)
- 5 files × 4 agents = 20 files

### Batch 4 (subagent): Agent vault files (3 agents)
- 5 files × 3 agents = 15 files

### Batch 5 (subagent): Templates + doctor + project note

## Verification
```bash
# Run doctor
python3 ~/.rig/department-substrate-flywheel/doctor.py

# Check agent status
rig-department-pai show {agent} --format json
rig-department-pai doctor --format json

# Check L8 integration
jake-l8 doctor
```

## Pitfalls
1. **Darius has different file names** — PAI Substrate vs Substrate Upgrade (create both)
2. **12 agents × 5 files = 60 files** — use parallel subagents
3. **Registry YAML must parse** — validate with doctor
4. **Goals must tie to ARR** — no generic goals
5. **Loops need metrics** — no loops without measurable outcomes

## References
- `~/.rig/agent-doctrine/RIG_AGENT_STANDARDS_DOCTRINE.md`
- `~/.rig/agent-doctrine/RIG_DEPARTMENT_PAI_SUBSTRATE.md`
- `~/.rig/department-substrate-flywheel/doctor.py`
- `~/Documents/JakeStudio/Agent Vaults/`
