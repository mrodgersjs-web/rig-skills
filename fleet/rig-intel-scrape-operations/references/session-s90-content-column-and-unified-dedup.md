# Session S90 — pages.content Pitfall, NULL content_hash, Unified Cross-Source Dedup

**Session:** S90 (cron, 2026-08-02T0254Z)
**Scanner:** rig-gtm-intel cron S90 (meta-harness, GLM-5.2)
**Prior packet:** C48/S89 (2026-08-02T0237Z)

## pages.content Column Does Not Exist

First GBrain query attempted `SELECT p.content FROM pages p` — failed with:

```
psycopg2.errors.UndefinedColumn: column p.content does not exist
```

**Fix:** The correct column is `compiled_truth` (text). Discovered via `information_schema.columns` query:

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'pages'
ORDER BY ordinal_position
```

Returned 33 columns. Key ones for intel scanning:
- `compiled_truth` (text) — full page content
- `content_hash` (text) — SHA-256 hash, frequently NULL on older pages
- `source_uri` (text), `source_path` (text) — provenance
- `frontmatter` (jsonb) — Obsidian frontmatter
- `updated_at` (timestamptz) — last modification

## NULL content_hash on Older Pages

50 pages tagged gtm/signal/offer/icp returned. Many had `content_hash = NULL`, especially:
- IntelPacket cycles C16–C48 (most had NULL hash)
- Some older knowledge/recall pages

**Handling:** Compute hash on-the-fly when NULL:
```python
chash = row['content_hash']
if not chash and row['compiled_truth']:
    chash = hashlib.sha256(row['compiled_truth'].encode()).hexdigest()
```

**False-positive risk:** Older cycles (C16–C33) with NULL hashes appear as "new" because their content_hash was never computed/stored. These are historical, not new activity. Flag in packet summary.

## Unified Cross-Source Dedup Set

Used a single `seen_hashes` Python set across all three sources (GBrain, vault, ODS specs):

```
GBrain: 50 tagged pages → 36 new (14 matched prior C39–C48 hashes)
Vault:  194 modified → 91 new (103 non-GTM or duplicates)
ODS:    60 modified → 59 new (1 duplicate)
Total:  304 candidates → 186 unique (118 deduplicated)
```

This approach automatically catches cross-source duplicates (same content in GBrain page and vault file) without separate cross-source dedup logic.

## Extended Vault Keyword Filter

Added filename-prefix patterns to the S88 keyword list:
- `warm-` — catches warm reply pipeline items (warm-arnold-paulos-dds-magd.md)
- `teaser-` — catches teaser-sent DSO accounts (teaser-zirtual.md)
- `nurture-stale` — catches nurture/stale follow-up items

Result: 91 relevant vault files from 194 modified in 24h. Top entries:
1. RIG Commercial System Handoff 2026-08-01.md (30KB)
2. action-brief-2026-08-01-cycle2.md (4KB, Tim Schulte)
3. 61 teaser-sent DSO pipeline items
4. 4 warm reply items (Arnold Paulos, Vik V., Hamza Asumah, Fabeha Ziyad)

## ODS Spec Path Keyword Filter

Filtered 60 modified files in rig-intelligence/ to 59 relevant spec files using:
```python
spec_keywords = ['spec', 'openspec', 'ods', 'doctrine', 'capability', 'config']
```

Key changes found:
1. LinkedIn Conference Commenting Foundry (4 files: proposal, tasks, spec, done-contract)
2. Portfolio Foundry Commercial v2 (4 files: proposal, tasks, 2 specs)
3. RIG Commercial Fleet 14-day (2 files: tasks, spec)
4. Omniscout 24x7 Learning Loop (1 file: tasks)
5. Automation Foundry doctrine + policies + role_refs + secret-misconfig.json

## Artifacts Written

- `IntelPacket-S90-GTM-INTEL.md` (9.6KB) — full markdown packet
- `IntelPacket-S90-GTM-INTEL.json` (1.4KB) — programmatic summary
- Workdir: `/Users/rig128gb/Documents/JakeStudio/Projects/control-plane/meta-harness/`

## Pipeline Status (unchanged from C48)

- Gate-D frozen 18+ days
- Email dark 31+ days (last send Jul 2)
- LinkedIn session expired (li_at 2026-07-31)
- $0 revenue, 4 unworked replies (oldest 17 days)
- Aug-5 kill switch: WOULD FIRE
- 13 conversation-ready accounts, 0 send-eligible
