---
name: rig-intel-scrape-operations
description: "Operational patterns for rig-intel-scrape cron jobs. Covers GBrain publishing (MCP + direct Postgres), TCC blocking fallbacks, content fingerprinting, and scan gap detection."
version: 1.0.0
---

# RIG Intel Scrape Operations

Operational lessons from running `rig-intel-scrape` as a recurring cron job across 60+ cycles (S55–S73). This captures the patterns that survive across sessions, not the pipeline-specific GTM analysis (which lives in `sales-intelligence/rig-gtm-intel`).

## When to Use

- Running or debugging a `rig-intel-scrape` cron job
- GBrain echo-chamber detection or mitigation
- Content fingerprinting for change detection
- File-writing failures in cron environments with proxy corruption
- Deciding whether to emit [SILENT] vs full scan
- NAS I/O stall mitigation (execute_code SIGTERM, graceful degradation, partial-source packets)
- macOS TCC blocking `~/Documents` from cron context (EPERM, not hang — use vault-inventory.json proxy)
- `rig-knowledge` CLI failing with "env: bun: No such file or directory" in cron (bun PATH fix)
- Building IntelPackets when GBrain MCP `put_page` fails on Unicode content (direct Postgres INSERT fallback)
- Publishing IntelPackets to GBrain via direct psycopg2 when MCP tools fail
- GBrain MCP `list_pages` with tag parameter for tag-filtered queries
- GBrain CLI direct access from cron via `bun ~/.bun/bin/gbrain list --tag <tag>` and `gbrain get <slug>` (S84 — simplest path when MCP unavailable)
- GBrain schema inspection (pages, tags, content_chunks tables)
- Batch splitting for large GBrain page fetches to avoid execute_code 5-min timeout (S84: 52 pages required 2 batches of ~30)
- Cross-source content dedup by SHA-256[:16] of full content bytes (S84: 227 cross-source dupes removed from 1,420 total items)
- TCC blocking is intermittent — always attempt direct vault access first, fall back to vault-inventory.json proxy only on EPERM
- `rig-knowledge` CLI may fail silently from cron (exit 1, no output) — proceed to direct Postgres queries without debugging
- Dual-query GBrain pattern: run both tag-filtered AND recently-updated queries per scan for comprehensive coverage
- Expanded Obsidian vault keyword list (31 keywords including agent names) to catch agent daily packets missed by the original 10-keyword list

## execute_code Progressive Corruption (confirmed S67, 2026-07-30)

**CRITICAL:** When `execute_code` fails with `SyntaxError: unterminated string literal` or `unterminated triple-quoted string`, do NOT retry with similar multi-line content. Each retry produces WORSE corruption — JSON keys from the content start appearing as top-level parameter names in the tool call.

**Observed pattern:**
1. First attempt: clean SyntaxError on a triple-quoted string
2. Second attempt: garbled parameter values (content fragments leak into parameter names)
3. Third attempt: near-total content corruption (pipe characters, dollar signs, section headers all fragment)

**Rule:** After 1 `execute_code` SyntaxError, switch immediately to `write_file` or inline delivery. Do not retry `execute_code` with multi-line strings.

## execute_code SIGTERM on NAS I/O Stall (confirmed S73, 2026-07-30)

**Distinct from the corruption pattern above:** When the NAS mount is stalled, `execute_code` scripts that call `subprocess.run()` against vault paths get SIGTERM'd (exit code -15, no output captured). The 5-minute execute_code timeout kills the whole script when internal subprocess calls hang on I/O.

**Observed pattern:**
1. Script calls `subprocess.run(['gbrain', ...])` — succeeds (bun uses SQLite, not the stalled mount)
2. Script calls `subprocess.run(['find', vault_path, ...])` or `os.path.exists(nas_path)` — hangs indefinitely
3. execute_code 5-min timeout fires → SIGTERM → exit -15, zero stdout captured

**Rule:** During NAS I/O stalls, do NOT use `execute_code` for multi-source scans. Instead:
- Use `terminal` with per-command `timeout=10` (or `timeout 8 <cmd>` shell wrapper) — kills individual hung commands without losing the whole session
- Run each source scan as a separate `terminal` call so one hung source doesn't kill the others
- Use `execute_code` only for pure in-memory data assembly (building JSON/MD from data already collected via terminal calls)

## Graceful Degradation During NAS Stall (S73, 2026-07-30)

When NAS I/O is stalled, 2 of 3 sources (Obsidian vault, ODS git) become inaccessible. The scanner should still produce a valid IntelPacket from the remaining source (GBrain CLI).

**Pattern:**
1. Attempt each source independently with short timeouts
2. For sources that timeout/hang: record `source_status: "stalled_nas_io"` in the envelope
3. Build the packet from whatever sources succeeded
4. Include a `source_status` map in the envelope so downstream consumers know coverage is partial
5. Write output to `/tmp/` first, then `cp` to workdir (single-file copy may succeed even when directory walks hang)
6. If workdir write also hangs: packet in `/tmp/` is still valid; next non-stalled session should copy it

**Echo chamber filter (refined):** Exclude any GBrain page with "intel-packet" or "IntelPacket" in the title from results. This prevents the scanner from reporting its own prior output as new intelligence.

## write_file Success with Markdown Tables (S67, 2026-07-30)

`write_file` successfully wrote a 5,926-byte markdown file containing pipe-delimited tables, dollar signs, and em-dashes. This contradicts the historical C14/C15 pattern where `write_file` corrupted markdown tables.

**Possible explanations:**
- The proxy corruption issue has been partially resolved
- The content shape (no YAML frontmatter, no nested pipe-table-in-cell) avoided the trigger
- The specific combination of special characters in this session did not hit the splitting path

**Revised guidance:** Use heredoc/echo patterns as first choice. `write_file` is now a viable fallback for simple markdown (no frontmatter, no deeply nested tables). Still avoid `write_file` for content with YAML frontmatter or deeply nested pipe structures.

## SILENT Protocol for Cron Runs

When the prior IntelPacket is less than 4 hours old AND found no new intelligence, do a 2-call pre-check before running the full scan:

1. `mcp__gbrain__query("IntelPacket cycle latest", limit=3)` — check if most recent packet found nothing
2. `mcp__gbrain__list_pages(sort="updated_desc", limit=5)` — check for any new pages since last scan

If both confirm no changes, emit `[SILENT]` (nothing else) and stop.

**S67 violation:** Prior packet S62 was 30 min old, found nothing. S67 should have emitted [SILENT] after the pre-check. Instead it ran the full GBrain suite (query + search + salience = 5+ MCP calls).

**Decision criteria:**
- Prior packet under 2h old AND found nothing: SKIP pre-check, emit [SILENT] immediately
- Prior packet 2-4h old AND found nothing: RUN pre-check (2 calls), then decide
- Prior packet over 4h old: ALWAYS full scan (timestamp decay needs updating)
- Any new GBrain page since prior scan: ALWAYS full scan

## macOS TCC Blocking ~/Documents from Cron (confirmed S83, 2026-07-31)

**Distinct from NAS I/O stall:** When running as a scheduled cron job, macOS TCC (Transparency, Consent, and Control) blocks access to `~/Documents/JakeStudio/` entirely — even when the NAS mount is healthy. `os.listdir()` raises `[Errno 1] Operation not permitted`, and `ls` returns `Operation not permitted`. This is a **permissions** issue (fails fast), not an I/O issue (hangs indefinitely).

**Affected paths:** Everything under `~/Documents/JakeStudio/` — Obsidian vault, ODS specs, meta-harness workdir, existing IntelPackets stored in the vault.

**NOT affected:** `~/.rig/`, `~/Developer/`, `/tmp/` — these remain accessible from cron.

**Mitigation pattern (confirmed S83):**
1. Use `~/.rig/knowledge-system/state/vault-inventory.json` as a **proxy** for vault state — contains all 65K+ markdown file paths with tier classification (curated/candidate/raw/generated/excluded), generated by `rig-knowledge scan` in a foreground session. Accessible from cron via `~/.rig/`.
2. Read intel data from `~/Developer/rig-gtm-studio-v2/` (ICP registry, OpenSpec specs, outreach configs) — on local SSD, not TCC-blocked.
3. Read competitor scanner artifacts from `~/.rig/node-ops/artifacts/YYYY-MM-DD/` — accessible.
4. Write IntelPacket output to `~/.rig/intel-packets/` instead of the specified workdir under `~/Documents/`.
5. Write dedup state to `~/.rig/intel-dedup-state.json`.
6. For prior IntelPackets stored in the vault: use path-level SHA-256 fingerprints (hash the path string itself) since content is inaccessible. Flag these with `evidence_score: 0.40` and note TCC blocking in the summary.

**shell-init error:** When cron starts with a stale CWD (e.g., workdir under `~/Documents/`), `shell-init: error retrieving current directory: getcwd: cannot access parent directories` appears. Fix: `cd ~` at the start of every terminal/execute_code call.

See `references/session-s83-tcc-blocking-fallback.md` for the full S83 fallback workflow, accessible data source map, and IntelPacket structure used.

## rig-knowledge CLI: bun PATH Requirement in Cron (confirmed S83, 2026-07-31)

The `rig-knowledge` CLI at `~/bin/rig-knowledge` is a bun script (`#!/usr/bin/env bun`). In cron environments, `bun` is not in the default PATH. It lives at `~/.bun/bin/bun`.

**Fix:** Prepend bun to PATH when invoking rig-knowledge from cron:
```python
env = os.environ.copy()
env["PATH"] = f"{os.path.expanduser('~/.bun/bin')}:{env.get('PATH','')}"
subprocess.run([os.path.expanduser("~/.bun/bin/bun"), os.path.expanduser("~/bin/rig-knowledge"), "doctor", "--format", "json"], env=env)
```

**Note:** Even with bun in PATH, `rig-knowledge doctor` will fail with `EPERM: operation not permitted, scandir '~/Documents/JakeStudio/Knowledge/Patterns'` when TCC blocks `~/Documents`. The `rig-knowledge scan` command that generates `vault-inventory.json` must be run from a foreground session with Documents access. Cron can only READ the pre-generated inventory file.

## psycopg2 Available in Cron via pip Install (confirmed S83-cycle42, 2026-07-31)

**CORRECTED:** The previous claim (S73) that psycopg2 is unavailable from cron is **WRONG**. `pip3 install psycopg2-binary --quiet` succeeds from the cron execute_code environment, and psycopg2 connects to the GBrain Postgres database successfully.

**GBrain config location:** `~/.gbrain/config.json` contains `"database_url": "postgresql://rig128gb@127.0.0.1:5432/gbrain"`.

**Install + connect pattern:**
```python
import subprocess, json, hashlib
from datetime import datetime, timezone

# Install psycopg2 if not available
subprocess.run(['pip3', 'install', 'psycopg2-binary', '--quiet'], capture_output=True, timeout=30)

import psycopg2
conn = psycopg2.connect("postgresql://rig128gb@127.0.0.1:5432/gbrain")
cur = conn.cursor()
```

**Note:** `psql` CLI binary is NOT available (not on PATH), but psycopg2 Python package works after install. Use `execute_code` (not `terminal`) for all Postgres operations.

**Fallback ladder for GBrain access from cron:**
1. GBrain MCP tools (`mcp__gbrain__list_pages`, `mcp__gbrain__get_page`, `mcp__gbrain__search`) — preferred for reads
2. GBrain MCP `put_page` — works for writes BUT fails on Unicode content (see section below)
3. Direct psycopg2 to Postgres — reliable for both reads and writes (install psycopg2-binary first)
4. `vault-inventory.json` at `~/.rig/knowledge-system/state/` — pre-generated inventory for file paths only
5. Local SSD sources under `~/Developer/` and `~/.rig/` — ICP registry, competitor artifacts, GTM state

## GBrain CLI Direct Access from Cron (confirmed S84, 2026-07-31)

**New simpler path:** The GBrain CLI (`~/.bun/bin/gbrain`) works directly from cron via `bun`. No need for MCP tools, psycopg2, or psql. This is the simplest access method when MCP tools are unavailable.

**Commands:**
```python
BUN = os.path.expanduser("~/.bun/bin/bun")
GBRAIN = os.path.expanduser("~/.bun/bin/gbrain")

# List pages by tag (returns tab-separated: slug, type, date, title)
result = subprocess.run([BUN, GBRAIN, "list", "--tag", "gtm", "-n", "100"],
                       capture_output=True, text=True, timeout=30)

# Get full page content by slug
result = subprocess.run([BUN, GBRAIN, "get", slug],
                       capture_output=True, text=True, timeout=15)

# Keyword search (returns: [score] slug -- title + preview)
result = subprocess.run([BUN, GBRAIN, "search", "gtm"],
                       capture_output=True, text=True, timeout=30)
```

**Output parsing for `list --tag`:** Each line is tab-separated: `slug\ttype\tdate\ttitle`. Parse with `line.split('\t')`.

**Batch splitting required:** Fetching 52 pages via `gbrain get` one-at-a-time exceeds the 5-minute `execute_code` timeout. Split into batches of ~30 slugs per `execute_code` call. Save intermediate results to `/tmp/` between batches.

**Fallback ladder for GBrain access from cron (updated S84, S87-cycle47):**
1. GBrain CLI via `bun ~/.bun/bin/gbrain` — simplest, works from cron (S84 confirmed)
2. GBrain MCP tools (`mcp__gbrain__list_pages`, `mcp__gbrain__get_page`, `mcp__gbrain__search`) — preferred when available
3. GBrain MCP `put_page` — works for writes BUT fails on Unicode content
4. Direct psycopg2 to Postgres — reliable for both reads and writes (install psycopg2-binary first)
5. `vault-inventory.json` at `~/.rig/knowledge-system/state/` — pre-generated inventory for file paths only
6. Local SSD sources under `~/Developer/` and `~/.rig/` — ICP registry, competitor artifacts, GTM state

**psycopg2 connection options (confirmed S87-cycle47, 2026-08-01):**
- TCP: `psycopg2.connect("postgresql://rig128gb@127.0.0.1:5432/gbrain")` — documented, works
- TCP no-auth: `psycopg2.connect("postgresql://localhost:5432/gbrain")` — documented, works
- **Unix socket: `psycopg2.connect("dbname=gbrain user=rig128gb host=/tmp")`** — works as alternative when TCP port is unavailable or connection-closed errors occur

**Multi-tag retrieval with array_agg (confirmed S87-cycle47):** To get all tags per page in a single query (avoids N separate tag lookups):
```sql
SELECT p.id, p.slug, p.title, p.updated_at, p.content_hash, p.source_uri, p.source_path,
       array_agg(t.tag) as tags,
       LEFT(p.compiled_truth, 500) as content_preview
FROM pages p
JOIN tags t ON t.page_id = p.id
WHERE t.tag ~* '(gtm|signal|offer|icp)'
AND p.deleted_at IS NULL
GROUP BY p.id, p.slug, p.title, p.updated_at, p.content_hash, p.source_uri, p.source_path, p.compiled_truth
ORDER BY p.updated_at DESC
LIMIT 50
```
The `~*` regex operator matches all four tag patterns in one pass. `array_agg` returns a Postgres array of tag strings per page.

## TCC Blocking is Intermittent (confirmed S84, 2026-07-31)

**S83 reported TCC blocking all access to `~/Documents/JakeStudio/` from cron.** S84 (same day, later cron run) had **NO TCC blocking** — `os.walk()` and `find` both worked normally on the vault path. This means:

- TCC blocking is **intermittent**, not permanent
- It may be triggered by specific cron process contexts (e.g., launchd label, sandbox profile)
- The S83 fallback patterns (vault-inventory.json proxy, `/tmp/` output) should be kept as fallbacks, not assumed permanent
- Always attempt the direct path first; fall back only when EPERM is received

**GBrain server contention:** S84 found 64 concurrent `gbrain serv` processes running. The server log showed "Timed out waiting for PGLite lock". Despite this, `gbrain list` and `gbrain get` CLI commands worked (they may bypass the server and access PGLite directly). If CLI commands start failing, check `ps aux | grep gbrain` for process proliferation.

## Fingerprint Store Path — Both Locations Work (confirmed S84)

S83 established `~/.rig/intel-dedup-state.json` as the canonical dedup state path. S84 used `.intel-fingerprints.json` in the workdir (`~/Documents/JakeStudio/Projects/control-plane/meta-harness/`). Both work when TCC is not blocking.

**Recommendation:** Use `~/.rig/intel-dedup-state.json` as primary (always accessible from cron, even during TCC blocking). If the workdir is accessible and has an existing `.intel-fingerprints.json`, merge it into the canonical path.

## Large IntelPacket Handling (confirmed S84, 2026-07-31)

When scanning all three sources (GBrain + vault + ODS specs), the packet can exceed 1,000 items and 800KB. Patterns for managing this:

1. **Cross-source dedup by content_hash** — 227 of 1,420 items were cross-source duplicates (same content in GBrain and vault files). Dedup by SHA-256[:16] of full content bytes.
2. **Filter ODS specs aggressively** — 10,683 files modified in 24h under `rig-intelligence/`, but only 1,342 matched GTM keywords. Still large. Consider further filtering by directory (e.g., `platform/legacy/` produced 616 files of low intel value).
3. **Evidence scoring** — Score = tag_count * 0.25 + content_length_factor * 0.25 + base. GBrain pages with 4 tags score 1.0; vault files score 0.8-0.9; ODS spec files score 0.8-1.0.

## Fingerprint Dedup — Canonical Local-SSD Path (confirmed S83, 2026-07-31)

The fingerprint registry path has drifted across sessions. S83 established `~/.rig/intel-dedup-state.json` as the canonical path — it is on local SSD (not NAS, not TCC-blocked), survives across cron runs, and does not require Documents access.

**S83 also used file-content hashing** (`hashlib.sha256(file_bytes).hexdigest()[:16]`) for accessible files, which is more robust than `title + summary` hashing because it detects actual content changes. For inaccessible files (TCC-blocked), path-level hashing (`hashlib.sha256(path_string.encode()).hexdigest()[:16]`) was used as a fallback with reduced evidence scores.

**Updated working pattern:**
1. Load `~/.rig/intel-dedup-state.json` at scan start (local SSD, always accessible from cron)
2. For each accessible source file: compute SHA-256[:16] of actual file bytes
3. For inaccessible files (TCC-blocked): compute SHA-256[:16] of the path string, flag with `evidence_score: 0.40`
4. If `source_uri` key exists with matching hash: skip as duplicate
5. If hash is new: mark as new/modified, add to registry
6. Save updated registry to `~/.rig/intel-dedup-state.json` after scan

## First-Run Baseline Effect (confirmed S91, 2026-08-02)

When the fingerprint store is empty or missing (first run against a new path, post-reboot /tmp cleanup, or path drift), **every item classifies as `new`**. This is expected baseline behavior, not a discovery.

**Rule:** If `len(existing_fingerprints) == 0` AND `total_packets > 100`, note in the packet summary that this is a **baseline run** — all items are first-of-record. Do not report the full count as "new findings." The next cycle against the same fingerprint store will produce meaningful new/updated counts.

**S91 observed:** 923 total, 923 new, 0 updated — classic baseline run. The fingerprint store was at `/tmp/rig-intel-scrape-fingerprints.json` (yet another path).

**Fingerprint path drift (cumulative):**

| Session | Path | Notes |
|---------|------|-------|
| S73 | `/tmp/.intel-state/fingerprints.json` | NAS write fallback |
| S83 | `~/.rig/intel-dedup-state.json` | Recommended canonical |
| S84 | `.intel-fingerprints.json` in workdir | TCC-accessible |
| S89 | `.intel-fingerprints.json` (dual structure) | List + dict entries |
| S91 | `/tmp/rig-intel-scrape-fingerprints.json` | Flat dict, /tmp |

**Recommendation stands:** Use `~/.rig/intel-dedup-state.json` as primary (survives reboots, always accessible from cron). /tmp paths lose state across reboots, guaranteeing periodic false "all new" baseline runs.

See `references/session-s91-fingerprint-baseline-and-path-drift.md` for S91 details, flat-dict fingerprint format, and psycopg2 availability note.

## GBrain Echo Chamber Detection

After 20+ cycles of storing IntelPackets in GBrain via `put_page`, the top 20 salient pages become self-generated intel packets with `emotional_weight=0` and `take_count=0`. This creates a feedback loop:

1. Scanner queries GBrain for GTM intelligence
2. GBrain returns prior intel packets (highest salience)
3. Scanner summarizes prior summaries
4. New packet stored, amplifying the echo

**Detection:** Check `get_recent_salience(limit=20)`. If all top pages are `type: "intel-packet"` or `type: "company"` with zero emotional_weight, the echo chamber is active.

**Mitigation:**
- Use external web searches (Exa, web_search) to inject non-self-generated content
- Read primary-source repo files (`rig-gtm-studio-v2/`) that GBrain only mirrors
- Flag the echo chamber in every packet until external ingestion resumes

## Fingerprint Dedup

Content fingerprinting uses SHA-256 (first 16 hex chars). The hash input formula has varied across sessions:
- `intel-packet-cron` skill: `title + summary`
- `rig-intel-scrape` skill: `source_uri + content[:500]`
- S73 actual: `title + summary` (matching intel-packet-cron)
- S87-cycle47 actual: `source_type:source_id:content_hash:title` (32-char hash, not 16) — includes source_type prefix for cross-source dedup and uses GBrain's `content_hash` field when available. Truncated to 32 chars. This formula causes registry resets when switching from prior formulas because the hash space changes entirely.

**Canonical rule (S73):** Use `title + summary` as hash input. Key the registry by `source_uri`. This is deterministic, doesn't require reading full page content (which may hang on NAS), and aligns with the `intel-packet-cron` schema.

**Known issues:**
- Fingerprint file path has drifted: `.intel-fingerprints.json` (documented) vs `.intel-state/fingerprints.json` (actual). S73 used `/tmp/.intel-state/fingerprints.json` as fallback when NAS write hung. S87-cycle47 used `.intel-fingerprints.json` in workdir with only 3 prior entries (partial prior state).
- Registry resets across sessions when NAS is stalled (can't read prior state) OR when the hash formula changes between sessions (different hash space = all "new")
- Consider periodic consolidation or migration to a canonical path

**`.intel-fingerprints.json` dual structure (confirmed S89, 2026-08-02):** The file has TWO fingerprint stores that must both be loaded for dedup:
1. `fingerprints` — a **list** of legacy short hashes (e.g., `['014f13ff9e4ce4ee', 'yt-gamma-scaling', ...]`). Typically 15 entries from older sessions.
2. Top-level **dict entries** keyed by full hash (e.g., `"7b79edadf9f9fefddb6e055141cdd5e5": {content_hash, title, source, source_uri, first_seen}`). These are the bulk of the dedup state (400+ entries).
3. Meta keys: `updated_at`, `total_fingerprints`.
**Load both** into a single `existing_fp_set` before dedup. If you only load the `fingerprints` list, you'll get near-zero dedup against the bulk dict entries.

**Hash formula drift → near-zero dedup (confirmed S89, 2026-08-02):** S89 observed 2/390 = 0.5% dedup rate because the prior run (S88, 2026-08-02T01:26:27Z) used GBrain's native `content_hash` field (full SHA-256, 64 chars) while S89 computed `hashlib.sha256(content[:5000]).hexdigest()[:16]` (16-char truncation of first 5KB). Different hash spaces = no overlap. **Rule:** pick one hash formula and use it consistently. The recommended formula is `hashlib.sha256(content[:5000].encode()).hexdigest()[:16]` — deterministic, content-based, and doesn't depend on GBrain's internal hash field.

**Working pattern:**
1. Load `.intel-fingerprints.json` at scan start — merge `fingerprints` list AND top-level dict keys into one `existing_fp_set`
2. For each source, compute SHA-256[:16] of first 5KB of content bytes
3. If hash exists in `existing_fp_set`: skip as duplicate
4. If hash is new: mark new, add to registry (both as dict entry AND append to `fingerprints` list)
5. Save updated registry after scan (try workdir first, `/tmp/` fallback)

## GBrain Postgres Upsert — ON CONFLICT (slug) Fails (confirmed S87, updated S89 2026-08-02)

**Problem:** `INSERT INTO pages ... ON CONFLICT (slug) DO UPDATE` fails with `InvalidColumnReference: there is no unique or exclusion constraint matching the ON CONFLICT specification`. The `slug` column has **no unique constraint**, so Postgres cannot use it for conflict resolution.

**Solution: Check-then-insert-or-update pattern.** Query for the slug first, then branch:

```python
cur.execute("SELECT id FROM pages WHERE slug = %s AND deleted_at IS NULL", (slug,))
existing = cur.fetchone()

if existing:
    page_id = existing[0]
    cur.execute("UPDATE pages SET compiled_truth = %s, updated_at = NOW() WHERE id = %s",
                (full_content, page_id))
else:
    # page_kind CHECK constraint: must be 'markdown', 'code', or 'image'
    # type has no check constraint — 'markdown' matches C47+ pattern
    # generation and chunker_version are required for INSERT to succeed
    cur.execute("""
        INSERT INTO pages (slug, title, compiled_truth, type, page_kind,
                          source_kind, ingested_via, created_at, updated_at,
                          effective_date, generation, chunker_version)
        VALUES (%s, %s, %s, 'markdown', 'markdown', 'put_page',
                'rig-gtm-intel-cron', NOW(), NOW(), NOW(), 1, 1)
        RETURNING id
    """, (slug, title, full_content))
    page_id = cur.fetchone()[0]

# Tags: ON CONFLICT DO NOTHING works (confirmed S89)
for tag in ['gtm', 'signal', 'icp', 'intel-packet']:
    cur.execute("INSERT INTO tags (page_id, tag) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (page_id, tag))
```

**Critical schema details (confirmed S89, 2026-08-02):**
- **`page_kind` has a CHECK constraint:** `CHECK (page_kind = ANY (ARRAY['markdown', 'code', 'image']))`. Using `'intel-packet'` or any other value fails with `CheckViolation`. Always use `'markdown'` for IntelPackets.
- **`compiled_truth` holds FULL content** — the earlier guidance saying it stores "truncated ~500 chars" was WRONG. S89 successfully stored multi-KB IntelPackets in `compiled_truth`. The `content_chunks` table is optional for chunked retrieval but not required for INSERT.
- **`type='markdown'`** matches the C47+ IntelPacket pattern. The older S83 pattern used `type='company'` — both work (no check constraint on `type`), but `'markdown'` is the canonical value for IntelPackets.
- **`generation` and `chunker_version`** columns are required for INSERT — both set to `1` for first-generation content.
- Connection string: `postgresql://rig128gb@127.0.0.1:5432/gbrain` (preferred — `localhost` can fail on IPv6). Trust auth, no password.
- The `tags` table accepts `ON CONFLICT DO NOTHING` — simpler than the `WHERE NOT EXISTS` pattern previously documented.

## GBrain content_chunks Schema (confirmed S87, 2026-08-01)

**Gotcha:** The column is `chunk_index`, NOT `chunk_order`. Postgres error: `column cc.chunk_order does not exist. HINT: Perhaps you meant to reference the column "cc.chunk_index"`.

Key `content_chunks` columns: `id`, `page_id`, `chunk_index` (integer), `chunk_text` (text), `chunk_source`, `embedding` (vector), `model`, `token_count`, `embedded_at`, `created_at`, `language`, `search_vector` (tsvector).

**Query pattern for reading page content:**
```sql
SELECT chunk_text FROM content_chunks cc
JOIN pages p ON cc.page_id = p.id
WHERE p.slug = %s
ORDER BY cc.chunk_index;
```

## GBrain MCP put_page Unicode Failure + Direct Postgres INSERT (confirmed S83-cycle42, 2026-07-31)

**Problem:** The `mcp__gbrain__put_page` MCP tool fails with `Invalid JSON arguments. Invalid control character at: line 1 column N` when the `content` parameter contains Unicode characters such as em-dashes (—), curly quotes, or other non-ASCII characters. The error persists even after replacing em-dashes with `--`.

**Root cause:** The MCP tool's JSON serialization chokes on certain Unicode characters in the content string, producing invalid JSON that the MCP server rejects.

**Solution: Direct Postgres INSERT via psycopg2.** When `put_page` fails, write the IntelPacket directly to the GBrain Postgres database:

```python
import psycopg2, json, hashlib
from datetime import datetime, timezone

# Read GBrain config for connection string
with open(os.path.expanduser('~/.gbrain/config.json'), 'r') as f:
    gbrain_config = json.load(f)
db_url = gbrain_config["database_url"]  # "postgresql://rig128gb@127.0.0.1:5432/gbrain"

conn = psycopg2.connect(db_url)
cur = conn.cursor()

# Compute content hash (SHA-256 of first 8KB)
content_hash = hashlib.sha256(content[:8192].encode()).hexdigest()
now = datetime.now(timezone.utc)

# INSERT into pages table
cur.execute("""
    INSERT INTO pages (source_id, slug, type, title, compiled_truth, timeline,
                       frontmatter, content_hash, created_at, updated_at,
                       source_kind, source_uri, ingested_via, ingested_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
""", (
    "default", slug, "company", title, full_markdown_content, "",
    json.dumps(frontmatter_dict),  # JSONB
    content_hash, now, now,
    "put_page", source_uri, "mcp:put_page", now
))
new_page_id = cur.fetchone()[0]

# INSERT tags (tags table: id, page_id, tag)
for tag in ["gtm", "signal", "offer", "icp", "intel-packet"]:
    cur.execute(
        "INSERT INTO tags (page_id, tag) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (new_page_id, tag)
    )

# Update search_vector for full-text search
cur.execute("UPDATE pages SET search_vector = to_tsvector('english', compiled_truth) WHERE id = %s", (new_page_id,))

conn.commit()
```

**Key schema details for INSERT:**
- `compiled_truth` column holds the full markdown content (including frontmatter)
- `frontmatter` is JSONB — pass a JSON string via `json.dumps(dict)`
- `tags` table has columns: `id` (serial), `page_id` (FK to pages.id), `tag` (text)
- `search_vector` is a tsvector column — must update manually after INSERT: `UPDATE pages SET search_vector = to_tsvector('english', compiled_truth) WHERE id = N`
- `source_id` should be `"default"` for the primary source

**Verification:** After INSERT, verify via `mcp__gbrain__get_page(slug=...)` — the page should be immediately readable via MCP.

**Unicode sanitization for local files:** When writing IntelPackets to local files via `execute_code`, replace em-dashes with `--` and curly quotes with ASCII equivalents to avoid any downstream encoding issues:
```python
content_clean = content.replace('\u2014', '--').replace('\u2013', '-').replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
```

See `references/gbrain-direct-postgres-publish.md` for the full S83-cycle42 publish workflow including schema inspection, INSERT, tag attachment, and search_vector update.

## GBrain MCP list_pages with tag Parameter (confirmed S83-cycle42, 2026-07-31)

When GBrain MCP tools are available, `mcp__gbrain__list_pages(tag="gtm", sort="updated_desc", limit=20)` is the **preferred method** for tag-filtered queries — simpler and more reliable than psql JOINs. Confirmed working for all four target tags: `gtm`, `signal`, `offer`, `icp`.

**Pattern for multi-tag scan:** Call `list_pages` once per tag in parallel (4 calls), then merge/dedup results by page ID. This is faster than a single psql JOIN across all tags.

**For reading full page content:** `mcp__gbrain__get_page(slug="...")` returns the complete `compiled_truth` field with all content. Use this to read prior IntelPackets for comparison.

## GBrain Direct Postgres Query (confirmed S78, 2026-07-31)

When GBrain MCP tools are unavailable (skill skipped, MCP server down), GBrain is a **local Postgres database** queryable directly via `psql`:

```bash
psql -d gbrain -t -A -F "|" -c "SELECT id, slug, title, content_hash, updated_at, source_uri FROM pages WHERE deleted_at IS NULL ORDER BY updated_at DESC LIMIT 20;"
```

### GBrain Schema (S78, 2026-07-31)

**Critical:** The `pages` table does NOT have a `tags` column. Tags are in a separate `tags` table (`id|integer, page_id|integer, tag|text`). To query pages by tag, JOIN `pages` to `tags` on `page_id`:

```sql
SELECT p.id, p.slug, p.title, p.content_hash, p.updated_at, p.source_uri,
       array_agg(t2.tag) as all_tags
FROM pages p
JOIN tags t2 ON t2.page_id = p.id
WHERE t2.tag ILIKE '%gtm%' AND p.deleted_at IS NULL
GROUP BY p.id, p.slug, p.title, p.content_hash, p.updated_at, p.source_uri
ORDER BY p.updated_at DESC LIMIT 30;
```

Key `pages` columns: `id, slug, type, page_kind, title, content_hash, frontmatter(jsonb), created_at, updated_at, deleted_at, source_uri, source_kind, source_path, ingested_via, search_vector(tsvector), emotional_weight, generation`.

## Scan Gap Detection — `find -mmin` Race Condition (confirmed S77, 2026-07-31)

**S75 reported "ZERO modifications" during its 16:00Z–21:00Z window on 2026-07-30.** Seven Company/RIG GTM docs were actually created at 17:56–20:41 UTC that day — squarely within S75's scan window. S75 missed them all, creating a 24-hour blind spot that included a Gate-D batch approval request and a LinkedIn cookie refresh runbook.

**Root cause:** The `find -mmin -N` approach depends on filesystem mtime, which can be affected by:
- File creation time vs mtime differences (some write methods update mtime slightly differently)
- Clock skew between the scan host and the file server (NAS)
- The `find` command executing at a moment when the filesystem cache hasn't flushed new entries
- Boundary timing: files created at the exact scan timestamp may or may not be included

**Mitigation rules:**
1. **Always cross-check**: When a scan reports "zero modifications," verify by running `stat -f "%Sm %N" -t "%Y-%m-%dT%H:%M:%S%z"` on known high-activity directories (e.g., `Company/RIG/`, `Agentic OS/Pipeline/items/`)
2. **Check GBrain ingest timestamps**: `psql -d gbrain -c "SELECT updated_at FROM pages ORDER BY updated_at DESC LIMIT 5"` — if GBrain has pages newer than the scan window start, files were modified that the `find` missed
3. **Recover missed artifacts**: When a prior packet is found to have missed files, include them in the current packet with `change_type: new_file (missed by S<N>)` and first-of-record fingerprints
4. **Never trust "zero changes" from a single source**: Cross-reference GBrain `updated_at`, Obsidian `stat` timestamps, and git log dates before declaring a window dead

## Fleet Health and Cold-Loop Log Reading (confirmed S77, 2026-07-31)

Three log files in `Logs/` provide real-time operational intelligence without needing MCP tools or API calls:

### RIG-FLEET-HEALTH.md
Format: timestamped blocks with per-node ONLINE/OFFLINE status and summary count.
```
[rig-fleet-health · 2026-07-31T17:52:42Z]
- this-host (127.0.0.1:11434) LLM: ONLINE
- blackwell (100.67.126.117) OFFLINE
- summary: 3/6 LLM nodes online
```
**Reading pattern:** `tail -20` to get the latest entry. Compare node count against prior scans to detect degradation. A drop from 4/6 to 3/6 is a CRITICAL operational risk — 50% capacity loss.

### RIG-COLD-LOOP.md
Format: 2-minute tick logs with draft and send counts.
```
[17:55:19Z] cold-loop tick: drafts=      88 sent=    1862
```
**Plateau detection:** When `sent` stops growing across 10+ consecutive ticks AND `drafts` stays constant, the outbound pipeline has frozen. Two failure modes:
- **Queue exhaustion**: all eligible leads have been drafted and sent; no new prospects in the pipeline
- **Rate-limit cap**: provider API limit hit; drafts exist but can't be sent

**Diagnostic:** If `drafts > 0` but `sent` is flat → rate-limit or auth blocker. If `drafts = 0` and `sent` is flat → queue exhaustion, need new prospect ingestion.

### RIG-EXECUTOR.md
Format: timestamped execution logs with task names and hash IDs.
```
[2026-07-31T11:39:36-0600] INFO executed leads_outreach -> 53c7b1cd...
```
**Reading pattern:** `tail -30` to see recent cycles. If executor is cycling but cold-loop is flat, the executor's output isn't reaching the send pipeline — check for failed downstream tasks.

## Goal Loop Proof Packet Reading (confirmed S77, 2026-07-31)

Proof packets live in `Goal Loops/Proofs/proof-<run_id>-<date>.md`. Format:
```yaml
---
type: proof_packet
run_id: <uuid>
agent: goal-loop-engine
verdict: NO_GO  # or GO
---
```
Gates section lists each gate with ✅/❌ and evidence. **NO_GO verdicts** identify failed tool health checks (e.g., `n8n_health`, `supabase_health`) — these are actionable infrastructure failures. Learning episodes live in `Goal Loops/Learnings/learning-<goal_id>-<date>.md` with `memory_layer: episode`.

**Intel scan integration:** Always check `Goal Loops/Proofs/` for packets newer than the prior IntelPacket. A NO_GO verdict with failed infrastructure checks is a high-priority action item.

## GBrain `frontmatter` jsonb Tag Query (confirmed S77, 2026-07-31)

**Alternative to the `tags` table JOIN** (which may not exist in all GBrain instances or may be empty): Query the `frontmatter` jsonb column directly:

```sql
SELECT id, slug, title, content_hash, source_path, updated_at
FROM pages
WHERE (frontmatter ? 'tags' AND (frontmatter->'tags' ?| ARRAY['gtm','signal','offer','icp']))
AND updated_at > NOW() - INTERVAL '24 hours'
AND deleted_at IS NULL
ORDER BY updated_at DESC LIMIT 20;
```

**Note:** In S77 this returned 0 rows — the Obsidian vault files don't consistently have `tags` in their frontmatter, or GBrain's import pipeline doesn't map Obsidian tags to the `frontmatter.tags` jsonb key. The `tags` table JOIN (documented above, confirmed S78) is the preferred method. Use this jsonb query as a fallback when the `tags` table is not present.

**Fallback ladder for tag queries:**
1. `tags` table JOIN (S78 pattern) — most reliable if table exists
2. `frontmatter->'tags'` jsonb query — works if tags were imported into frontmatter
3. `slug LIKE '%gtm%' OR slug LIKE '%signal%'` — crude but catches untagged content
4. Full table scan with `search_vector` tsquery — semantic, not tag-based

See `references/gbrain-schema.md` for full table listing.
See `references/session-s77-scan-gap-and-log-patterns.md` for S75 scan gap recovery details, fleet health degradation event, cold-loop plateau diagnosis, and Goal Loop NO_GO proof packet analysis.

## rig-knowledge CLI Now Functional (confirmed S78, 2026-07-31)

**Previous claim (S73) that `rig-knowledge` CLI does not exist is OUTDATED.** The `rig-knowledge match` command now runs successfully and returns verified Pattern Library context packets:

```bash
rig-knowledge match --repo "$PWD" --task "<task statement>" --stack "<tech>" --limit 5 --format json
```

Returns `rig.context-packet.v1` schema with `matches` (verified patterns with `score`, `why`, `lastVerified`, `sourceRefs`, `proofRefs`), `conflicts`, `gaps`, and `requiredTests`. Use this BEFORE meaningful work to check if prior RIG patterns apply. Only apply `status: verified` patterns. If `gaps` contains `no_verified_pattern_match`, proceed from repository truth.

## rig-knowledge CLI Silent Failure from Cron (confirmed S88, 2026-08-02)

**Beyond the bun PATH issue (S83) and EPERM (S83):** `rig-knowledge` can fail with **exit code 1 and zero output** — no stdout, no stderr, no error message. `which rig-knowledge` returns nothing (binary not on cron PATH at all).

**Observed (S88):**
- `which rig-knowledge` → empty (not found)
- `rig-knowledge match --repo ... --task ... --format json` → exit 1, empty output
- No error message to diagnose from

**Rule:** When `rig-knowledge` fails silently from cron, do NOT spend time debugging it. Proceed directly to psycopg2 direct GBrain queries. The `rig-knowledge` CLI is a convenience layer — all the data it would return is accessible via direct Postgres queries against the `pages` and `tags` tables.

**Successful invocation pattern (confirmed S89, 2026-08-02):** When `which rig-knowledge` returns empty, the binary IS installed at `~/bin/rig-knowledge` but not on the cron PATH. Fix:
```bash
export PATH="$HOME/bin:$HOME/.bun/bin:$PATH"
rig-knowledge match --repo "$PWD" --task "<task>" --limit 5 --format json
```
This successfully returned verified Pattern Library context packets (score 3, status: verified) in S89. The binary requires bun (`~/.bun/bin/bun`) as its interpreter (`#!/usr/bin/env bun`). Both `~/bin` (for the binary) and `~/.bun/bin` (for the bun runtime) must be on PATH.

**`|| echo` exit-code masking pitfall (confirmed S89, 2026-08-02):** When invoking `rig-knowledge match` from cron with a shell fallback like `rig-knowledge match ... 2>/dev/null || echo '{"status":"no_match"}'`, the output `{"status":"no_match"}` is **ambiguous** — it fires on ANY non-zero exit, so you cannot distinguish "ran successfully, no verified patterns found" (exit 0, legitimate `no_verified_pattern_match` gap) from "binary not found / crashed silently" (exit 1, S88 pattern). The `2>/dev/null` also suppresses stderr which may contain the actual error. **Correct pattern:** check exit code explicitly via `subprocess.run()` and inspect `returncode`, `stdout`, and `stderr` separately — do not use shell `|| echo` fallbacks for diagnostic commands.

## Dual-Query Pattern for GBrain Scans (confirmed S88, 2026-08-02)

Run TWO GBrain queries per scan for comprehensive coverage:

1. **Tag-filtered query** — `WHERE t.tag IN ('gtm','signal','offer','icp')` — catches categorized content
2. **Recently-updated query** — `WHERE p.updated_at > <last_scan_timestamp>` — catches untagged but fresh changes (e.g., 100x goal loop runs, ralph cycle engine pages)

The tag-filtered query alone misses pages that were updated but never tagged. The recently-updated query alone misses older tagged pages with no changes. Running both ensures no intel is missed.

**Dedup between the two queries** by page slug — the same page may appear in both result sets. Keep the first occurrence and merge tags from all rows.

## Expanded Intel Keyword List for Obsidian Vault Filtering (confirmed S88, 2026-08-02)

The original keyword list (`gtm, signal, offer, icp, pricing, outbound, campaign, beachhead, prospects, target`) misses agent-specific daily packets and operational intel. Use the expanded list:

```python
intel_keywords = [
    'gtm', 'signal', 'offer', 'icp', 'intel', 'packet', 'darius', 'tessa', 'alfred',
    'clara', 'outbound', 'campaign', 'prospect', 'vertical', 'cpa', 'law', 'dental',
    'healthcare', 'construction', 'medspa', 'manufacturing', 'linkedin', 'scrape',
    'omniscout', 'fleet', 'commercial', '24h-drive', 'cycle', 'research', 'daily',
    'briefing'
]
```

This catches: Darius/Tessa/Alfred/Clara agent daily packets, 24h-drive cycle documents, Omniscout research cards, fleet health logs, and daily briefings — all high-value intel that the original shorter keyword list missed.

## write_file + terminal Pattern for Complex Python Scripts (confirmed S90, 2026-08-02)

When building IntelPackets with `execute_code`, inline Python scripts passed via `terminal(command="python3 -c '...'")` fail when the script contains both single and double quotes, f-strings with nested quotes, or multi-line strings. Shell escaping becomes unreliable and each retry produces different syntax errors.

**Pattern:** Write the full Python script to `/tmp/` using `write_file`, then execute it:

```python
from hermes_tools import write_file, terminal

write_file(path='/tmp/build_intelpacket.py', content=full_script_text)
result = terminal(command='python3 /tmp/build_intelpacket.py 2>&1', timeout=60)
```

**Advantages:**
- No shell quoting issues — the script is written as-is
- Full Python syntax available (f-strings, triple quotes, all quote styles)
- Script can be re-run without rebuilding the command string
- Easier to debug — `/tmp/build_intelpacket.py` can be inspected

**When to use:** Any time an `execute_code` script exceeds ~20 lines or contains nested quotes. Short scripts (<10 lines, no nested quotes) can still use inline `python3 -c`.

## Obsidian Vault Noise Directory Exclusion (confirmed S90, 2026-08-02)

When scanning the Obsidian vault for recently modified files, three directories produce high-volume, low-intel-value results that inflate the scan and bury real intelligence:

```python
skip_dirs = ['Logs/', 'Memory/Agent Sessions/', 'Memory/Agent Realtime/']
if any(skip in rel for skip in skip_dirs):
    continue
```

**Why these directories are noise:**
- `Logs/` — daily log files (29KB each), updated every session, no GTM intel
- `Memory/Agent Sessions/` — 92KB session dumps, updated every session, no GTM intel
- `Memory/Agent Realtime/` — 22KB+3KB current-state files, updated every session, no GTM intel

**Impact:** Excluding these reduced the vault scan from 291 files to 185 files (36% reduction) with zero loss of GTM-relevant intelligence. The `Daily/` and `Research/` directories contain the actual intel and are retained.

## Skill Absence vs Tool Availability

Hermes skills (`gbrain`, `rig-scrape`) may be listed as unavailable in the cron environment. Fallback ladder:
1. Try underlying MCP tools directly (`mcp__gbrain__query`, `mcp__gbrain__search`) — skill absence ≠ MCP tool unavailability
2. If MCP tools also unavailable, use **direct `psql -d gbrain` queries** or psycopg2 (see sections above)
3. For knowledge patterns, try `rig-knowledge match` CLI — but see silent failure pitfall above; proceed to direct Postgres if it fails silently

## GBrain Tag Gap: "offer" and "icp" Return Few Results (updated S78, 2026-07-31)

**Previously (S74–S76):** Tags `offer` and `icp` consistently returned zero pages.
**Updated (S78):** Tagged queries now return 2 pages each for `offer` and `icp` (via the `tags` table JOIN). `gtm` returns 30 pages, `signal` returns 2. This is still a **thin tag set** — the systematic sync gap from ODS/Agentic OS vault to GBrain tags persists, but it is no longer zero.

**Pattern for future scans:** Use the `tags` table JOIN (not `gbrain list --tag`) for tag-filtered queries. Supplement with:
1. Read ODS spec files directly — `offers/`, `pricing-lock.json`, `offer-catalog`
2. Scan Agentic OS Pipeline `/items/*.md` frontmatter tags
3. Use semantic search on gbrain as secondary

## GTM Reply-Debt Escalation Signal (observed S76)

GBrain/intel scans should flag reply-debt when they detect pipeline scorecard KPI "replies_unworked" > 0 with oldest age exceeding thresholds. S76 showed:
- **Reply debt = 92** with oldest at **14+ days** (by end of window). Scorecard lanes: GREAT=4 / WEAK=17.
- GTM reply conversion probability drops non-linearly after ~10 days unworked.
- IntelPackets in sessions where scorecard shows "6 KPI RED" should flag **TRIPWIRE ACTIVE** and prioritize the single highest-ROI immediate action (often HED-style deal follow-up over breadth).

## GBrain `pages.content` Column Does Not Exist (confirmed S90, 2026-08-02)

**Pitfall:** Querying `SELECT p.content FROM pages p` fails with `UndefinedColumn: column p.content does not exist`. The `pages` table has NO `content` column. The correct column for full page content is **`compiled_truth`** (text).

**Full pages table schema (S90 confirmed):**
```
id, source_id, slug, type, page_kind, title, compiled_truth, timeline,
frontmatter(jsonb), content_hash, emotional_weight, created_at, updated_at,
deleted_at, effective_date, effective_date_source, import_filename,
salience_touched_at, last_retrieved_at, contextual_retrieval_mode,
corpus_generation, generation(bigint), search_vector(tsvector),
emotional_weight_recomputed_at, chunker_version(smallint), source_path,
ingested_via, ingested_at, source_uri, source_kind, embedding_signature,
links_extracted_at
```

Key columns for intel scanning: `id`, `slug`, `title`, `compiled_truth` (full content), `content_hash` (may be NULL!), `source_uri`, `source_path`, `updated_at`, `created_at`, `frontmatter` (JSONB).

## NULL content_hash is Pervasive on Older GBrain Pages (confirmed S90, 2026-08-02)

Many GBrain pages — especially older IntelPacket cycles (C16–C48) — have `content_hash = NULL`. When computing dedup fingerprints, always handle NULL:

```python
chash = row['content_hash']
if not chash and row['compiled_truth']:
    chash = hashlib.sha256(row['compiled_truth'].encode()).hexdigest()
```

**Impact on dedup:** Pages with NULL content_hash that were already captured in prior IntelPackets will appear as "new" if the prior packet used a different hash formula or if the hash was never computed. This causes older cycles (C16–C33) to surface as false positives. Flag these with a note: "historical, not new activity" and lower evidence_score.

**Unified cross-source dedup set (S90 pattern):** Use a single `seen_hashes` set across ALL three sources (GBrain, vault, ODS specs). Add each source's content hashes to the same set. This catches cross-source duplicates (same content in GBrain and vault file) automatically:

```python
seen_hashes = set()
# GBrain pages
for row in gbrain_rows:
    chash = row['content_hash'] or hashlib.sha256(row['compiled_truth'].encode()).hexdigest()
    if chash in seen_hashes:
        continue  # cross-source duplicate
    seen_hashes.add(chash)
# Vault files
for vf in vault_files:
    chash = hashlib.sha256(open(vf['path']).read().encode()).hexdigest()
    if chash in seen_hashes:
        continue
    seen_hashes.add(chash)
# ODS specs — same pattern
```

## Extended Vault Keyword Filter with Filename Prefixes (confirmed S90, 2026-08-02)

Beyond the 31-keyword list (S88), filename-prefix patterns catch pipeline items by naming convention:

```python
intel_keywords = [
    'gtm', 'signal', 'offer', 'icp', 'intel-packet', 'commercial', 'dso',
    'scorecard', 'action-brief', 'pipeline', '24h-drive', 'warm-',
    'teaser-', 'nurture-stale'
]
```

The `warm-`, `teaser-`, and `nurture-stale` prefixes match pipeline item filenames directly (`warm-arnold-paulos-dds-magd.md`, `teaser-zirtual.md`, `nurture-stale-arnoldpaulosdds.md`). This caught 91 relevant vault files from 194 modified in 24h.

## ODS Spec Path Keyword Filter (confirmed S90, 2026-08-02)

When scanning `rig-intelligence/` for spec changes, filter by path keywords to reduce noise:

```python
spec_keywords = ['spec', 'openspec', 'ods', 'doctrine', 'capability', 'config']
if any(kw in fpath.lower() for kw in spec_keywords):
    # include
```

This reduced 60 modified files to 59 relevant spec/config/doctrine files — high precision, near-zero noise. Key directories caught: `openspec/changes/*/`, `platform/automation-foundry/docs/`, `platform/automation-foundry/config/`.

## See Also

See `references/session-s83-tcc-blocking-fallback.md` for S83 TCC blocking discovery, accessible data source map from cron, and IntelPacket output structure.
See `references/session-s84-gbrain-cli-direct-access.md` for S84 GBrain CLI direct access from cron, full 3-source scan results, timeout management with batch splitting, and large IntelPacket handling.
See `references/session-s88-silent-failure-and-dual-query.md` for S88 rig-knowledge silent failure, dual-query GBrain pattern, expanded Obsidian keyword list, and 259-fingerprint dedup results.
See `references/session-s89-fingerprint-structure-and-dedup-drift.md` for S89 fingerprint store dual-structure discovery, hash formula drift causing 0.5% dedup rate, recommended canonical hash formula, and rig-knowledge CLI successful invocation with PATH fix.
See `references/session-s90-content-column-and-unified-dedup.md` for S90 pages.content pitfall, NULL content_hash handling, unified cross-source dedup set, and extended vault/ODS keyword filters.
See `references/session-s91-fingerprint-baseline-and-path-drift.md` for S91 first-run baseline effect, fingerprint path drift to /tmp/, flat-dict fingerprint format, and psycopg2 already available without install.

## Related Skills

- `sales-intelligence/rig-gtm-intel` — the full GTM IntelPacket production skill (pipeline analysis, offer conflicts, competitor tracking, dead-account STOP-GATE)
- `rig-knowledge-context` — Pattern Library retrieval via `rig-knowledge` CLI (now functional as of S78)
- `intel-packet-cron` — the cron architecture skill (schema, dedup, ODS scanning, GBrain CLI fallback). Note: two skills define incompatible IntelPacket schemas — pick one at session start.
- `rig-intel-scrape` — defines a canonical IntelPacket schema (`packets[]`, `id: INTEL-YYYY-MM-DD-NNN`, `summary`, `captured_at`) with `scripts/quick-gen.py` and `scripts/verify-intel-packet.py`. **OVERLAP WARNING:** This skill (`rig-intel-scrape-operations`) and `rig-intel-scrape` cover the same operational territory but use incompatible schemas. The workdir-resident `intel_scrape_cron.py` script (stable across S84–S89+) produces `findings[]` / `packet_id` / `total_findings` / `new_findings` / `dedup_skipped` — NOT the canonical `packets[]` / `id: INTEL-...` / `total_packets` form. Future sessions should use `rig-intel-scrape`'s `scripts/quick-gen.py` for packet generation to ensure schema compliance. The `rig-intel-scrape-operations` skill should be treated as the operational-learnings companion, not the schema authority. **Consolidation candidate** for the background curator.
