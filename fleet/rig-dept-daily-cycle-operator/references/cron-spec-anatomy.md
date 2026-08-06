# Cron Spec Anatomy — `~/.rig/departments/cron-specs/<dept>.cron.json`

Every department's daily-cycle cron reads its spec from this file. The schema is consistent across all 21 departments.

## Full schema (verbatim from legal.cron.json)

```json
{
  "name": "LEGAL — DAILY WORK (every 4h)",
  "schedule": "every 4h",
  "model": "minimax/MiniMax-M3",
  "provider": "minimax",
  "model_name": "MiniMax-M3",
  "prompt": "You are Jake PAI running **LEGAL — DAILY WORK** cron for dept `legal`.\n\n**Goal:** Hit the daily goal at `~/.rig/departments/legal/goals/DAILY-GOAL.md` (entity_target, topic_target, fresh_pct).\n\n**Source queue:** Read `~/.rig/departments/queues/legal.json` for the live URL list. Each URL is a real source pulled from the previous probe.\n\n**STEPS (do ALL 8, do not skip):**\n\n1. **Scrape every URL** in the queue file (urllib.request GET, save body to `~/.rig/departments/legal/substrate/scraped/<src>.raw`, truncated 1MB).\n2. **Extract entities** from each scrape body — for each major claim/fact/metric, write an entity page at `~/.rig/departments/legal/substrate/entities/<src>-entity-<ts>.md` with the standard `---` frontmatter + `## Facts` fence.\n3. **Extract topics/patterns** into `~/.rig/departments/legal/substrate/patterns/candidates-cycle-<cycle>.md`. Each pattern needs: name, evidence_count (default 1), confidence (default 0.5), 3+ bullets.\n4. **GBrain write** — POST entities to `http://127.0.0.1:3131/api/entities` with a JSON body containing dept, source, content, meta.\n5. **Supabase write** — INSERT into `dept_legal_raw` (raw_payload), `dept_legal_entities` (entity_payload), `dept_legal_patterns` (pattern_payload).\n6. **Obsidian write** — create/edit `~/Documents/JakeStudio/Department PAI/legal/<today>.md` with summary of today's run (entity count, pattern count, links).\n7. **Update state** at `~/.rig/departments/legal/goals/_state.json` — add to today_count, set last_run_at.\n8. **ProofPacket** at `~/.rig/state/legal-daily-proof-<cycle>.json` with seal + hash + counts.\n\n**Blocklist enforced every step:** HED, IdeaWake, Anthony Langeweg, hed-forge, dec-1783268304352-va5c, dec-1783268340018-db8f. Skip any URL with these terms; if a payload contains them, quarantine.\n\n**Quality gate:** Verify each entity has `## Facts` fence with at least 2 metric/value/units. Verify each pattern has evidence_count ≥ 1...",
  "repeat": 999
}
```

## Field semantics

| Field | Type | Purpose |
|---|---|---|
| `name` | string | Human-readable cron name (may contain em-dash `—` U+2014 or its 6-char ASCII escape `\u2014` — see `rig-department-architecture` pitfall) |
| `schedule` | string | Cadence expression — `every 4h`, `every 24h`, or cron expression |
| `model` / `model_name` | string | Model identifier for the Hermes scheduler |
| `provider` | string | Provider identifier (e.g. `minimax`, `ollama-cloud`) |
| `prompt` | string | The natural-language task prompt the cron sends to the agent. May reference sealed subsystems (entities, patterns, GBrain, Supabase, Obsidian, state, proof). |
| `repeat` | int | Maximum fire count. `999` = effectively unbounded recurring. Lower values mark bounded runs. |

## Sibling files (every dept reads all four)

| File | Read/Write | Purpose |
|---|---|---|
| `~/.rig/departments/queues/<dept>.json` | READ | Live URL list — `{"sources": [...], "generated_at": "...", "cycle": "..."}` |
| `~/.rig/departments/<dept>/goals/DAILY-GOAL.md` | READ | The per-day target — `entity_target`, `topic_target`, `fresh_pct`, owner, node, telos |
| `~/.rig/departments/<dept>/goals/_state.json` | READ+WRITE | The compounding state — `today_count`, `fresh_pct`, `entities_written`, `topics_written`, `cycles[]` |
| `~/.rig/departments/<dept>/substrate/scraped/*.raw` | WRITE | Raw scraped payloads (truncated to 1MB per spec) |
| `~/.rig/departments/<dept>/substrate/entities/*.md` | WRITE | Extracted entities with canonical 5-section schema |
| `~/.rig/departments/<dept>/substrate/patterns/*.md` | WRITE | Extracted patterns with canonical 3-section schema |

## Owner / node / telos / verifier (from registry)

Every dept also reads from `~/.rig/departments/_REGISTRY.py`:
- **Owner:** the agent persona that owns the dept (e.g. Vera Jr for legal, Darius for GTM, etc.)
- **Node:** the LAN node the cron runs on (e.g. `lite-84` for legal)
- **Telos:** the one-line north star (e.g. "Zero contract disputes + zero compliance gaps")
- **Verifier gate:** the verifier CLI for this dept (e.g. `verifier-legal`)

The cron may not have direct access to the registry file (depends on the Hermes profile) — the DAILY-GOAL.md file usually summarizes these fields in its header so the prompt has them inline.

## Cycle naming convention

Cycles within a day use a versioned naming scheme:

- `daily-goal-v1` — first run of the day (baseline)
- `daily-goal-v2-compound` — second run (extends baseline, 100% fresh from prior cycle)
- `daily-goal-v3-compound` — third run (etc.)
- `daily-goal-vN-compound` — Nth run

The version bump lets the ProofPacket's `cycle` field distinguish baseline from compound runs. Compound runs append to `state.cycles[]` rather than overwriting the prior entry.

## What the prompt does NOT include

The cron spec prompt is intentionally minimal — it states the 8 steps + blocklist + quality gate but does NOT include:
- The canonical entity schema (entities assume the agent knows it from prior training or skill loading)
- The canonical pattern schema (same)
- The ProofPacket hash calculation (same)
- The per-dept checklist catalog (varies per dept)
- The per-dept contract variant catalog (varies per dept)

These are loaded into context via this skill (`rig-dept-daily-cycle-operator`) when the cron fires. If the skill is not loaded, the agent may produce entities with ad-hoc schema that fails the verifier gate.

## Per-dept variation: what changes between cron specs

The 8-step skeleton is identical across depts. What varies:

| Field | legal | finance | content | gtm | ... |
|---|---|---|---|---|---|
| Source URLs | GDPR + OpenAlex | SEC + BLS | RSS + YouTube | LinkedIn + Crunchbase | ... |
| Entity kinds | gdpr_article, gdpr_recital, academic_work | filing, regulation, ticker | article, video, podcast | lead, account, signal | ... |
| Checklist items | DP-12 legal catalog | FIN-12 finance catalog | CT-12 content catalog | GTM-12 outreach catalog | ... |
| Contract variants | MSA, DPA, JCA, SCC, Sub | Loan, NDA, Lease, SaaS, M&A | Edit, Brand, Affiliate | MSA, SoW, Order Form, Renewal | ... |
| Cluster taxonomy | principles, scope, security, rights | revenue, expense, asset, liability | pillar, format, channel | segment, persona, signal | ... |

The class-level skill captures the cross-dept invariant (8 steps, canonical schemas, ProofPacket, blocklist, compound-cycle state). The per-dept specifics live in the cron-spec prompt + the dept's DAILY-GOAL.md + the agent's memory.