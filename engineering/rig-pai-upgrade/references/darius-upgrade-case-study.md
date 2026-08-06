# Case Study: Darius PAI Upgrade (2026-07-05)

## Before State
- Registry entry: EXISTS, active, basic fields (telos, KPIs, hard_blocks, what_good_looks_like)
- Runtime surface (Hermes): Persona-level — fake daily cadence ("5:00 AM — Market scrape"), generic tool list ("Email API", "Ad platforms"), motivational text
- Agent vault: 6 files (README, Inputs Required, Great Output Examples, Work Ledger, Daily Intel Index, misc)
- Quality profiles: 2 of 5 bound (agent_outcome_evaluation_v0, gtm_strategy_v0)
- Department PAI doctor: ALL PASS (infrastructure was ready, agent content was thin)

## Gaps Identified
| Component | State | Gap |
|---|---|---|
| PAI Substrate | Missing | No identity/role/authority/boundaries/load order/memory policy |
| $10M ARR Command | Missing | No revenue target tree, ICP map, offer ladder, channel portfolio |
| Team Model | Missing | No workers defined |
| Daily Control Loop | Fake schedule | No real template with pipeline state, experiments, proof |
| Quality Profiles | 2/5 | Missing gtm_experiment_quality_v0, outreach_quality_v0, revenue_evidence_v0 |
| L8 Mapping | Not bound | L8 jobs exist but Darius usage not mapped |
| Data Model | Missing | No GBrain/Supabase design |

## After State
12 artifacts created, all verification gates pass:

| Artifact | Size | Hash (first 16 chars) |
|---|---|---|
| PAI Substrate.md | 5,770 B | 88fb491738a2b750 |
| 10M ARR Command.md | 8,459 B | 49ec44951d8a2d06 |
| Team Model.md | 8,148 B | 9a2c6feeb3f01dc4 |
| Daily Operating Packet.md | 3,903 B | be28003d6ccbfc6e |
| Quality Profiles.md | 4,307 B | 5946a81db8b1897e |
| L8 Mapping.md | 5,236 B | d41c51631ea86378 |
| Data Model.md | 9,383 B | ef6f6e91e75677a0 |
| darius-agent.md (runtime) | 6,449 B | 578f711198292657 |
| README.md (updated) | 1,840 B | 31ad4db19ff83318 |
| Work Ledger.md (updated) | 3,365 B | 8a8429fd462b313b |
| Inputs Required.md (updated) | 1,548 B | 4918fa9a42e7fd75 |
| What Good Looks Like.md (updated) | 3,286 B | 8f8f0e1184a79034 |

## Verification
- `rig-department-pai doctor`: PASS (20 gates, 0 fail, 0 warn)
- `rig-department-pai show darius`: PASS (active, telos bound, quality profiles bound)
- `rig-agent-standards status`: PASS
- Ad-hoc verification script: PASS (7/7 checks)
- ProofPacket sealed: `sha256:667503f03583d54e7daf2d138031b2c0d40e4556ba9a9a5176e050255ced5d7c`
- Obsidian memory checkpoint: committed (`120bb6f6`)

## Key Decisions
1. **Quality profiles defined locally** — gtm_experiment_quality_v0, outreach_quality_v0, revenue_evidence_v0 are not in the global quality catalog. Defined in Darius's vault as `proposed` profiles. Future: promote to catalog after scoring real artifacts.
2. **Supabase schema deferred** — Data model recommends Supabase tables but notes "start with Obsidian + GBrain, add Supabase when pipeline has 20+ active accounts."
3. **10 workers, not subagents** — Team model defines 10 worker roles but they operate as task dispatch patterns within Darius sessions, not as separate agent processes.
4. **Cycle-based daily rhythm** — Replaced fake clock-based schedule with 8-step cycle (intel → pipeline → experiments → priority → team → quality → packet → memory).

## Delegation Pattern
Used `delegate_task` batch mode for parallel file creation:
- Batch 1 (subagent A): PAI Substrate + Team Model + Quality Profiles
- Batch 2 (subagent B): $10M ARR Command + Daily Operating Packet + L8 Mapping
- Direct: Data Model + Runtime surface + vault updates

Lesson: Pass exact file content to subagents. Don't let them improvise — they add filler or change structure.
