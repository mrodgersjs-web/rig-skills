# Session S89 — Fingerprint Store Structure and Dedup Hash Drift

**Date:** 2026-08-02T02:11Z
**Packet:** IntelPacket-CRON-IntelScrape-20260802T021134Z
**Delta from last scan:** 0.8 hours (last: 2026-08-02T01:26:27Z)

## Problem: Near-Zero Dedup Rate

S89 observed a 0.5% dedup rate (2/390 candidates skipped) despite the prior scan (S88) running only 45 minutes earlier. Root cause: **hash formula drift** between cron runs.

## Fingerprint Store Structure

The `.intel-fingerprints.json` file at the workdir contains a **dual** structure:

```json
{
  "updated_at": "2026-08-02T01:26:27.191186+00:00",
  "total_fingerprints": 259,
  "fingerprints": [
    "014f13ff9e4ce4ee",
    "127a39579c74db44",
    "yt-gamma-scaling",
    ...
  ],
  "7b79edadf9f9fefddb6e055141cdd5e5": {
    "content_hash": null,
    "title": "IntelPacket Cycle 46 — S87 — 2026-08-01T1833Z",
    "source": "gbrain"
  },
  "87b5552391406306e21a75726d475cde": {
    "content_hash": "85524d27dbca7512...",
    "title": "IntelPacket Cycle 43 — S84 — 2026-07-31T2106Z",
    "source": "gbrain"
  },
  ...
}
```

- `fingerprints` list: 15 legacy short hashes from older sessions
- Top-level dict entries: ~420 entries keyed by full hash with `{content_hash, title, source, source_uri, first_seen}`
- Meta keys: `updated_at`, `total_fingerprints`

**Both stores must be loaded** into a single `existing_fp_set` for dedup. Loading only the `fingerprints` list misses the bulk of the dedup state.

## Hash Formula Drift

| Session | Formula | Hash Length |
|---------|---------|-------------|
| S87-c47 | `source_type:source_id:content_hash:title` | 32 chars |
| S88 | GBrain native `content_hash` field | 64 chars |
| S89 | `hashlib.sha256(content[:5000].encode()).hexdigest()[:16]` | 16 chars |

Different formulas produce different hash spaces → no overlap → near-zero dedup.

## Recommended Canonical Formula

```python
chash = hashlib.sha256(content[:5000].encode()).hexdigest()[:16]
```

- Deterministic: doesn't depend on GBrain's internal hash field
- Content-based: detects actual content changes
- 16-char truncation: compact, collision-resistant enough for dedup

## Dedup Loading Pattern

```python
with open(fp_path) as f:
    fp_data = json.load(f)

existing_fp_set = set()
# Load list entries
for fp in fp_data.get("fingerprints", []):
    existing_fp_set.add(fp)
# Load dict entries (skip meta keys)
meta_keys = {"fingerprints", "updated_at", "total_fingerprints"}
for k in fp_data:
    if k not in meta_keys:
        existing_fp_set.add(k)
```

## GBrain Schema Discovery

Initial query used `p.content` column — **does not exist**. The `pages` table has:
- `compiled_truth` (text) — primary content field
- `content_hash` (text) — GBrain's internal hash
- No `content` column

Full content is in the `content_chunks` table (`chunk_text` column).

This is already documented in the SKILL.md but was hit again in S89, confirming it's a **recurring pitfall** for any new session that doesn't read the schema section first.

## rig-knowledge CLI Success

`rig-knowledge match` ran successfully after adding `~/bin` and `~/.bun/bin` to PATH. Returned two verified patterns:
1. `coding.knowledge.evidence-thresholded-pattern-promotion` (score 3)
2. `coding.knowledge.single-writer-derived-indexes` (score 3)

No gaps returned — patterns matched cleanly.

## Scan Results Summary

| Source | Candidates | New Packets |
|--------|-----------|-------------|
| GBrain (tagged + recent) | 147 | 147 |
| Obsidian Vault | 165 | 164 |
| ODS / rig-intelligence | 78 | 77 |
| **Total** | **390** | **388** |

- Fingerprints before: 435, after: 823
- Delta: 0.8 hours
- Output: 202,905 bytes