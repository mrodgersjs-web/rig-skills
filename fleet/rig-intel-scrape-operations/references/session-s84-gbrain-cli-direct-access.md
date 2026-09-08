# Session S84: GBrain CLI Direct Access + Full 3-Source Scan (2026-07-31)

## Context

Running `rig-intel-scrape` as a scheduled cron job. The `gbrain` and `rig-scrape` skills were listed as not found and skipped. The `rig-knowledge-context` skill was loaded via the job invocation. The `rig-knowledge` CLI was not found in PATH.

## Key Discovery: GBrain CLI Works from Cron

Previous sessions (S78, S83) used psycopg2 or psql for direct GBrain access when MCP tools were unavailable. S84 discovered that the GBrain CLI itself (`~/.bun/bin/gbrain`) works directly from the cron environment via `bun`.

### GBrain CLI Commands Used

```python
BUN = "$HOME/.bun/bin/bun"
GBRAIN = "$HOME/.bun/bin/gbrain"

# List pages by tag — returns tab-separated lines
# Format: slug \t type \t date \t title
result = subprocess.run([BUN, GBRAIN, "list", "--tag", "gtm", "-n", "100"],
                       capture_output=True, text=True, timeout=30)

# Get full page content by slug
result = subprocess.run([BUN, GBRAIN, "get", slug],
                       capture_output=True, text=True, timeout=15)

# Keyword search — returns: [score] slug -- title + preview
result = subprocess.run([BUN, GBRAIN, "search", "gtm"],
                       capture_output=True, text=True, timeout=30)
```

### GBrain CLI Help Output (v0.42.65.0)

Key commands:
- `init [--pglite|--supabase|--url]` — Create brain
- `get <slug>` — Read a page
- `put <slug> [< file.md]` — Write/update a page
- `list [--type T] [--tag T] [-n N]` — List pages
- `search <query>` — Keyword search (tsvector)
- `query <question> [--no-expand]` — Hybrid search (RRF + expansion)
- `tags <slug>` — List tags for a page
- `tag <slug> <tag>` — Add tag
- `timeline [<slug>]` — View timeline
- `doctor [--json] [--fast]` — Health check
- `export [--dir ./out/]` — Export to markdown

## TCC Blocking Not Present

Unlike S83 (same day, earlier cron run), S84 had NO TCC blocking. `os.walk()` on `~/Documents/JakeStudio/` worked normally. `find` commands also worked. This confirms TCC blocking is intermittent.

## GBrain Server Contention

- 64 concurrent `gbrain serv` processes found via `ps aux`
- Server log: "Timed out waiting for PGLite lock"
- Despite this, CLI commands (`list`, `get`) worked fine — they may access PGLite directly without going through the server
- GBrain sync cursor: `last_id=404`, updated `2026-07-23T12:09:38` (8 days stale)

## Scan Results

### GBrain (tagged: gtm, signal, offer, icp)
- 52 unique pages across all 4 tags
- All 52 were new/modified (first run with this fingerprint store)
- Tag distribution: gtm=50, signal=22, offer=4, icp=4
- Top content: IntelPacket cycles 16-43 (S55-S84), YouTube GTM intel, Darius daily packets

### Obsidian Vault (last 24h, GTM-relevant)
- 125 files modified in last 24h total
- 26 GTM-relevant files matched keywords
- All 26 were new/modified
- Key files: IntelPacket outputs (S76-S83), cycle 39-41 markdown, fleet health logs

### ODS Specs (last 24h, GTM-relevant)
- 10,683 files modified in last 24h total
- 1,342 matched GTM keywords
- All 1,342 were new/modified
- Top areas: platform/legacy (616), products/legacy (233), rig-coding-desktop (224), wayfinder (25)

### Cross-Source Dedup
- 227 cross-source duplicates removed (identical content in GBrain + vault)
- Method: SHA-256[:16] of full content bytes
- Final unique items: 1,193

## Timeout Management

Fetching 52 GBrain pages via `gbrain get` one-at-a-time in a single `execute_code` call exceeded the 5-minute timeout (exit code -15, zero output captured).

**Fix:** Split into two batches of ~30 slugs each. Save intermediate results to `/tmp/` between batches. Load and merge in a final `execute_code` call.

## IntelPacket Output

- File: `IntelPacket-CRON-IntelScrape-20260731T153702Z.json`
- Size: 864,913 bytes (865 KB)
- Path: `$HOME/Documents/JakeStudio/Projects/control-plane/meta-harness/`
- Schema: `{ packet_id, generated_at, cycle, sources_scanned, tags_scanned, summary, items[] }`
- Each item: `{ source, source_uri, slug, title, page_type, date, tags, content_hash, change_type, evidence_score, content_length, content_preview }`

## Fingerprint Store

- Used `.intel-fingerprints.json` in workdir (NOT `~/.rig/intel-dedup-state.json` as S83 recommended)
- Started with 357 entries, ended with 1,550 entries
- All items marked as "new" (first run with this fingerprint store)
- Future runs should see proper dedup against these fingerprints

## Environment Issues

- Meta-harness startup failed: `PermissionError: [Errno 1] Operation not permitted` on `os.getcwd()` in cron sandbox
- Fix: `cd ~` at start of each terminal call, `os.chdir(os.path.expanduser("~"))` in execute_code
- `rig-knowledge` CLI not found in PATH (not installed or not linked)
- `bun` not in default PATH — must use full path `~/.bun/bin/bun`
- `psql` CLI not available
