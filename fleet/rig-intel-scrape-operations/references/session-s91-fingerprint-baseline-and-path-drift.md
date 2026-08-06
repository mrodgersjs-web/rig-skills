# Session S91 — Fingerprint Baseline Effect, Path Drift to /tmp/

**Session:** S91 (cron, 2026-08-02T~0430Z)
**Scanner:** rig-intel-scrape cron S91 (meta-harness, GLM-5.2)
**Prior packet:** C48/S90 (2026-08-02T0254Z)

## Fingerprint Store Path Drift Continues

This session used `/tmp/rig-intel-scrape-fingerprints.json` — a path not in the
documented list. The skill already tracks path drift across S73–S90:

| Session | Path | Location |
|---------|------|----------|
| S73 | `/tmp/.intel-state/fingerprints.json` | /tmp fallback |
| S83 | `~/.rig/intel-dedup-state.json` | Recommended canonical |
| S84 | `.intel-fingerprints.json` in workdir | TCC-accessible workdir |
| S89 | `.intel-fingerprints.json` (dual structure) | Workdir |
| **S91** | **`/tmp/rig-intel-scrape-fingerprints.json`** | **/tmp flat dict** |

**Problem:** Each path change creates a fresh fingerprint store, causing ALL items
to classify as "new" on the first run against the new path. This is the same
effect as hash formula drift (S89) but caused by store absence rather than
hash space mismatch.

## First-Run Baseline Effect

When the fingerprint store is empty or missing (first run, post-reboot /tmp
cleanup, or path drift to a new location), **every item classifies as `new`**.
This is expected baseline behavior, not a discovery.

**S91 observed:** 923 total packets, 923 new, 0 updated, 0 unchanged. This is a
baseline-establishment run, not a real intelligence burst.

**Rule for future sessions:**
1. If `len(existing_fingerprints) == 0` AND total_packets > 100: note in the
   packet summary that this is a **baseline run** — all items are first-of-record,
   not genuinely new activity.
2. Do not report "923 new items" as a finding — report "baseline established with
   923 fingerprints; next cycle will produce meaningful new/updated counts."
3. Suppress the `new` count in the executive summary when it equals `total_packets`
   and the fingerprint store was empty at scan start.

## Fingerprint Store Format — Simple Flat Dict

S91 used a simplified flat dict `{"key": "hash"}` instead of the S89 dual-structure
format (list + dict entries + meta keys). Both work for dedup; the flat dict is
simpler to load/save but loses metadata (first_seen, title, source).

**Flat dict pattern:**
```python
# Load
previous_fps = json.load(open('/tmp/rig-intel-scrape-fingerprints.json'))
# Check
if key in previous_fps and previous_fps[key] == current_hash:
    change_type = 'unchanged'  # skip
# Save (merge existing + new)
all_fps = {**previous_fps, **new_fps}
json.dump(all_fps, open('/tmp/rig-intel-scrape-fingerprints.json', 'w'))
```

**Tradeoff:** Flat dict is simpler but cannot answer "when was this first seen?"
or "what was the title?" — the S89 dual structure preserves this metadata.

## psycopg2 Already Available (No Install Needed)

This session connected via `psycopg2.connect(host="127.0.0.1", ...)` without
needing `pip3 install psycopg2-binary`. The package was already present in the
execute_code environment. The skill's `subprocess.run(['pip3', 'install', ...])`
guard is harmless (install is a no-op if already present) but not always necessary.

## Output Schema Fragmentation Continues

S91 output used `{"generated_at", "summary": {total_packets, new, updated,
unchanged_skipped, sources}, "packets": [...]}` — yet another schema variant.
This does not match the canonical `rig-intel-scrape` schema (`packet_type`,
`scanner`, `workdir`, `INTEL-YYYY-MM-DD-NNN` IDs) nor the `rig-intel-scrape-
operations` schema. The skill already flags this as an ongoing consolidation
candidate.

## Scan Results (for reference)

- GBrain: 157 unique tagged pages (gtm/signal/offer/icp)
- Obsidian: 201 files modified in 48h, 97 GTM-relevant after keyword filter
- ODS specs: 669 spec files modified in 48h, 13 distinct OpenSpec change sets
- 11 of 13 OpenSpec changes have signed done-contracts
- 2 in-progress: ai-youtube-doctrine-corpus, transformfit-flutter
- 10 24h-Drive IntelPacket cycles tracked (C29–C48)
