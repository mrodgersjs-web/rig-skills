# Session S88 — rig-knowledge Silent Failure, Dual-Query Pattern, Expanded Keywords (2026-08-02)

## Context

Cron-run intel scrape. Skills `gbrain` and `rig-scrape` were not found and skipped. The `rig-knowledge-context` skill was loaded but `rig-knowledge` CLI was not available. GBrain was accessed via direct psycopg2 using the connection string from `~/.gbrain/config.json`.

## rig-knowledge CLI Silent Failure

- `which rig-knowledge` → empty (binary not on cron PATH)
- `rig-knowledge match --repo ... --task ... --format json` → exit code 1, empty stdout AND stderr
- No error message at all — completely silent failure
- Distinct from S83 (bun PATH issue with visible error) and S83 (EPERM with visible error)
- Resolution: skipped rig-knowledge entirely, proceeded with direct psycopg2 GBrain queries

## Dual-Query GBrain Pattern

Two queries run in a single scan:

### Query 1: Tag-filtered
```sql
SELECT p.id, p.slug, p.title, p.compiled_truth, p.content_hash,
       p.updated_at, p.source_uri, p.source_path, t.tag
FROM pages p JOIN tags t ON p.id = t.page_id
WHERE t.tag IN ('gtm','signal','offer','icp') AND p.deleted_at IS NULL
ORDER BY p.updated_at DESC LIMIT 50
```
Result: 50 rows (21 unique slugs — each IntelPacket cycle page has all 4 tags)

### Query 2: Recently updated (since last scan)
```sql
SELECT p.id, p.slug, p.title, p.content_hash, p.updated_at, p.source_uri, p.source_path
FROM pages p WHERE p.deleted_at IS NULL AND p.updated_at > %s
ORDER BY p.updated_at DESC LIMIT 50
```
Result: 4 rows — including 3 100x goal loop runs and 1 IntelPacket cycle that were NOT in the tagged query results (untagged pages)

### Dedup
Same IntelPacket cycle page appeared in both queries. Dedup by slug, keeping first occurrence.

## Initial Schema Error

First GBrain query attempt used `p.content` which does not exist:
```
GBrain ERROR: column p.content does not exist
```
Fix: use `p.compiled_truth` (truncated content preview) and `p.content_hash` (hash field). Full text is in `content_chunks.chunk_text`.

## GBrain Connection

Config at `~/.gbrain/config.json`:
```json
{"engine": "postgres", "database_url": "postgresql://rig128gb@127.0.0.1:5432/gbrain"}
```

Connection via psycopg2:
```python
conn = psycopg2.connect("postgresql://rig128gb@127.0.0.1:5432/gbrain")
```

No password needed — local trust authentication. First attempt with `localhost` (IPv6 ::1) failed with `fe_sendauth: no password supplied`. Using `127.0.0.1` explicitly avoids IPv6 resolution and works.

## Expanded Obsidian Vault Keywords

Used 31 keywords (up from ~10) to filter 181 modified vault files down to 160 intel-relevant ones:

```python
intel_keywords = [
    'gtm', 'signal', 'offer', 'icp', 'intel', 'packet', 'darius', 'tessa', 'alfred',
    'clara', 'outbound', 'campaign', 'prospect', 'vertical', 'cpa', 'law', 'dental',
    'healthcare', 'construction', 'medspa', 'manufacturing', 'linkedin', 'scrape',
    'omniscout', 'fleet', 'commercial', '24h-drive', 'cycle', 'research', 'daily',
    'briefing'
]
```

Notable catches from expanded keywords:
- `Agent Vaults/darius/Daily Packets/2026-08-01.md` — Darius daily GTM packet
- `Agent Vaults/RIG AI Employees/ceo-company-os/clara/Daily Packet/2026-08-01.md` — Clara daily packet
- `Agent Vaults/ralph/linkedin-batch-3-aug5.md` — Ralph LinkedIn batch draft
- `alfred/drafts/tomorrow.json` — Alfred content draft queue
- `Company/ai-employee-forge/runs/iris-intel-2026-08-01.md` — Iris intel run
- `Research/Omniscout/Cards/` — 5 new Omniscout research cards

None of these would have been caught by the original keyword list (`gtm, signal, offer, icp, pricing, outbound, campaign, beachhead, prospects, target`).

## ODS Spec Changes (25 files)

Three major change sets active:
1. **rig-commercial-fleet-14day** (7 specs) — fleet container runtime, delegated authority, enterprise control plane
2. **portfolio-foundry-commercial-v2** (8 specs) — commercial campaign, onboarding, mission control, GTM strategy
3. **automation-foundry-execution-spine** (5 specs) — operating procedures, deterministic verification

## Dedup Results

- Existing fingerprints: 216
- Dedup skipped: 163 (already seen)
- New fingerprints added: 43
- Total fingerprints: 259

## TCC Status

No TCC blocking observed — full vault access via `os.walk()` worked from cron. Consistent with S84's finding that TCC blocking is intermittent.

## Fingerprint Store

Used workdir `.intel-fingerprints.json` (not `~/.rig/intel-dedup-state.json`). Had 216 existing entries — well-populated from prior sessions. The workdir path works when TCC is not blocking.