---
name: rig-pai-upgrade
description: "Upgrade a named RIG department agent from persona to full PAI operating system. Use when Mike asks to 'make [agent] a real PAI', 'upgrade [agent] substrate', 'give [agent] a command system', or when a department agent has a registry entry but lacks substrate, team model, daily loop, quality contracts, data model, or proof path. Applies to Darius, Ralph, Julie, and any future department head."
tags:
  - rig
  - department-pai
  - agent-upgrade
  - substrate
---

# RIG PAI Upgrade — Persona → Full Department PAI

Repeatable workflow for upgrading any named RIG department agent from a role/persona into a full Department PAI operating system with substrate, command system, team, daily loop, quality contracts, data model, and proof path.

## When To Use

- Named agent exists in Department PAI registry but has only a thin persona prompt
- Agent vault exists but lacks substrate, command system, quality contracts, or proof path
- Doctor passes but the agent can't produce governed, repeatable outputs
- Mike says "upgrade [agent] into a real PAI" or "make [agent] a real revenue commander"
- Agent has a runtime surface with fake cadences, generic tool lists, or motivational text instead of load order + authority + team + quality contracts
- **Research-driven upgrade:** Intel Swarm or research findings need to be applied to an EXISTING PAI (load `references/jake-v2-intel-swarm-upgrade.md` for this pattern)

## Phase 1: Assessment (load all canonical sources in parallel)

### Required reads — batch these in a single turn
1. `$HOME/.rig/agent-doctrine/RIG_AGENT_STANDARDS_DOCTRINE.md`
2. `$HOME/.rig/agent-doctrine/RIG_DEPARTMENT_PAI_SUBSTRATE.md`
3. Agent vault README: `$HOME/Documents/JakeStudio/Agent Vaults/<agent>/README.md`
4. Agent vault `Inputs Required.md`
5. Agent vault `Great Output Examples.md`
6. Agent vault `Work Ledger.md`
7. `$HOME/.jake/l8/jobs.yaml`
8. `$HOME/.jake/l8/capabilities.yaml`

### Required verification commands — batch these
```bash
$HOME/.rig/bin/rig-department-pai show <agent_id> --format json
$HOME/.rig/bin/rig-department-pai doctor --format json
$HOME/.rig/bin/rig-agent-standards status
cat $HOME/.rig/meta-harness/registries/quality_catalog.json | python3 -c "import sys,json; [print(p['id']) for p in json.load(sys.stdin).get('profiles',[])]"
cat $HOME/.rig/meta-harness/registries/department_pai_agents.json
```

### Runtime surface inspection
Read the Hermes agent file:
```bash
$HOME/.hermes/agents/jtbd/<agent>-agent.md
```

### Gap assessment table
Build a table: component → current state → gap → priority

## Phase 2: Artifact Creation (7 PAI notes + 5 vault updates)

### Core PAI artifacts

| # | Artifact | Vault Path | Content |
|---|---|---|---|
| 1 | PAI Substrate | `PAI Substrate.md` | Identity, role, telos, authority (allowed/blocked), Gate-D format, input contract, output contract, load order, memory policy, proof path, daily rhythm, boundaries |
| 2 | Command System | `<Domain> Command.md` | Department-specific target tree, assumptions, maps, stages, indicators, kill/scale rules, constraint log, experiment template |
| 3 | Team Model | `Team Model.md` | Named workers: purpose, allowed tools, inputs, outputs, quality bar, stop conditions, proof requirement, memory scope, dispatch rules |
| 4 | Daily Packet | `Daily Operating Packet.md` | Template for daily output: exec readout, top N moves, team board, pipeline/experiment state, proof links, blockers, kills, scales, Gate-D asks, risks, tomorrow setup |
| 5 | Quality Profiles | `Quality Profiles.md` | All bound profiles with required fields, scoring dimensions (weighted), done criteria, hard blocks |
| 6 | L8 Mapping | `L8 Mapping.md` | Which L8 jobs the agent uses, daily trigger, allowed tools, proof requirement, Gate-D boundary, success metric |
| 7 | Data Model | `Data Model.md` | Obsidian vault structure, GBrain entity model, Supabase schema recommendation, data flow diagram |

### Vault updates (always)

| # | File | What to update |
|---|---|---|
| 8 | Runtime surface | Full PAI load order, team dispatch, quality contracts, revenue/department discipline |
| 9 | `README.md` | Reference all new PAI notes with wikilinks |
| 10 | `Work Ledger.md` | Add upgrade entry: date, work description, artifact hashes |
| 11 | `Inputs Required.md` | Expand with validation rules, escalation, standing queries |
| 12 | `What Good Looks Like.md` | Concrete great/weak examples and hard blocks tied to department |

### Department-specific command system patterns

- **GTM/Sales (Darius):** $10M ARR Command — target tree, ICP map, offer ladder, channel portfolio, pipeline stages, leading indicators
- **Content/LinkedIn (Ralph):** Content Craft Command — voice calibration, hook bank, audience map, publishing cadence, quality scoring
- **W2 Career (Julie):** Career Search Command — opportunity scoring, application pipeline, interview prep framework, comp-fit tracking
- **Future departments:** Adapt the command system to the department's telos and KPIs

## Phase 3: Parallel Delegation Strategy

For 7+ artifacts, use `delegate_task` batch mode (up to 3 concurrent):
- **Batch 1:** PAI Substrate + Command System + Team Model (largest files)
- **Batch 2:** Daily Packet + Quality Profiles + L8 Mapping
- **Direct:** Data Model + Runtime surface + vault updates (smaller, need exactness)

**Critical:** Pass exact file content to each subagent. Don't let subagents improvise — they add filler, change structure, or invent content.

## Phase 4: Verification

### Required verification commands
```bash
$HOME/.rig/bin/rig-department-pai show <agent_id> --format json
$HOME/.rig/bin/rig-department-pai doctor --format json
$HOME/.rig/bin/rig-agent-standards status
```

### Artifact verification
- All files exist in vault directory (`ls -la`)
- SHA256 hashes computed for every artifact (`shasum -a 256`)
- File sizes recorded

### ProofPacket
Create at: `Agent Vaults/<agent>/Proof/YYYY-MM-DD-<agent>-pai-upgrade.proof.json`

Required fields: artifacts (path, hash, bytes), sources, gates (name, command, exit_code, headline, status), verdict, proof_hash, timestamp.

### Ad-hoc verification script
Create temp `hermes-verify-*.py` under `/var/folders/...` that checks:
1. ProofPacket parses as JSON
2. All required fields present
3. Verdict is TRUE
4. All gates PASS
5. All artifacts exist with correct hashes and sizes
6. Proof hash is non-empty and valid
7. Department PAI doctor passes
Clean up script after running.

## Pitfalls

- **Don't create fake daily cadences.** Real daily rhythm is cycle-based (intel → pipeline → experiments → priority → team → quality → packet → memory), not "5:00 AM — Market scrape".
- **Don't mix persona with PAI.** Runtime surface should be load order + authority + team + quality contracts, not motivational text or aspirational tool lists.
- **Don't skip the doctor.** If `rig-department-pai doctor` fails, fix registry/database first.
- **Don't count staged pipeline as revenue.** Every revenue discipline section must enforce this hard block.
- **Don't forget the Gate-D format.** Substrate must define the exact Gate-D activation packet structure.
- **Don't create quality profiles not in the catalog.** If a profile is `proposed`, define it locally and note it's proposed. Quality catalog is authority.
- **Don't skip vault README update.** Future agents need to find the new PAI notes.
- **Don't skip Work Ledger entry.** Every upgrade is a work trace.
- **Subagent content drift.** Pass exact file content. Don't let subagents improvise.
- **Don't claim upgrade because the prompt sounds strong.** Upgrade is verified only when all artifacts exist with hashes and doctor passes.

## Verification Checklist

```
[ ] All 7 PAI notes exist in vault
[ ] All 5 vault files updated
[ ] Runtime surface upgraded
[ ] All artifacts have SHA256 hashes
[ ] Department PAI doctor: PASS
[ ] Agent standards status: PASS
[ ] ProofPacket created and sealed
[ ] Ad-hoc verification script: PASS
[ ] Obsidian memory checkpoint captured
[ ] Work Ledger has upgrade entry
```

## Example: Darius Upgrade (2026-07-05)

12 artifacts, all gates pass:
- 7 PAI notes (Substrate, $10M ARR Command, Team Model, Daily Packet, Quality Profiles, L8 Mapping, Data Model)
- 1 runtime surface upgrade
- 4 vault updates (README, Work Ledger, Inputs Required, What Good Looks Like)
- ProofPacket: `Agent Vaults/darius/Proof/2026-07-05-darius-pai-upgrade.proof.json`
