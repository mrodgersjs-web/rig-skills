# Session S83: TCC Blocking Fallback Workflow (2026-07-31)

## Context

Running `rig-intel-scrape` as a scheduled cron job. The `gbrain` and `rig-scrape` skills were not found. The `rig-knowledge-context` skill was loaded via the job invocation.

## TCC Blocking Discovery

Every attempt to access `~/Documents/JakeStudio/` from the cron context failed with `[Errno 1] Operation not permitted`:
- `os.listdir("~/Documents/JakeStudio")` → EPERM
- `os.listdir("~/Documents")` → EPERM  
- `ls -la ~/Documents/JakeStudio` → "Operation not permitted"
- `subprocess.run(["ls", ...])` → same error

This is macOS TCC (Transparency, Consent, and Control) blocking the cron process from accessing the user's Documents directory. Unlike NAS I/O stalls (which hang indefinitely), TCC blocking fails **immediately** with EPERM.

**Key distinction:**
- NAS I/O stall: `os.listdir()` hangs → timeout → no output
- TCC blocking: `os.listdir()` → immediate `[Errno 1] Operation not permitted`

## Accessible Data Sources (Confirmed from Cron)

### 1. Vault Inventory (Proxy for Obsidian Vault)
- **Path:** `~/.rig/knowledge-system/state/vault-inventory.json`
- **Schema:** `rig.vault-inventory.v1` with `root`, `generatedAt`, `totalMarkdown`, `counts` (curated/candidate/raw/generated/excluded), and `paths` (per-tier file path arrays)
- **S83 values:** 65,143 total markdown files; 16 curated, 49,720 candidate, 15,151 raw, 206 generated, 50 excluded
- **Generated:** 2026-07-30T01:18:23 (by `rig-knowledge scan` in a foreground session)
- **Usage:** Keyword-filter all paths for `gtm|signal|offer|icp`, exclude `youtube/` and `qnap-ingest/` for high-signal set. S83 found 731 high-signal paths.

### 2. ICP Registry
- **Path:** `~/Developer/rig-gtm-studio-v2/openspec/specs/icp-registry/named-icp-registry.json`
- **Schema:** `rig.icp_registry.v1` with `entries` array (350 entries), `source_counts` dict
- **S83 values:** 350 entries; sources: approve_queue=537, apollo_targets=200, fired_comments=38, cockpit_replies=4, war_rooms=0
- **Warm/replied entries:** 4 (Arnold Paulos DDS, Vik V., Fabeha Ziyad, Hamza Asumah MD)
- **Backup files:** 5 backup JSONs created same day (2026-07-31T11:52), indicating active modification

### 3. Competitor Scanner Artifacts
- **Path:** `~/.rig/node-ops/artifacts/YYYY-MM-DD/`
- **File pattern:** `competitor_weakness_scanner_r*.md` and `extract_competitor_weaknesses_from_reviews_docs_an_r*.md`
- **S83 (2026-07-31):** 4 files, sizes 5.3-6.4KB, generated 04:59-10:08 UTC
- **Content:** Competitor weaknesses by vertical (Healthcare, Dental, Construction, Legal, CPA, Manufacturing, MedSpa)
- **Evidence score:** 0.60 (generated content, not verified against live competitor data)

### 4. OpenSpec Specs (rig-gtm-studio-v2)
- **Base:** `~/Developer/rig-gtm-studio-v2/`
- **Warm Lead specs:** `openspec/changes/warm-lead-linkedin-engine/`, `warm-lead-engine/`, `warm-lead-supply-edge/`
- **Wayfinder specs:** `openspec/changes/rig-wayfinder-ten-route-control-plane/`
- **ICP registry spec:** `openspec/specs/icp-registry/spec.md`
- **All updated 2026-07-31** — active development

### 5. GTM Agentic Ops State
- **Path:** `~/.rig/gtm-agentic-ops/`
- **Proof files:** `proof/*.json` (21 proof files, latest 2026-07-23)
- **NOTE:** `config/revenue-motions.json` and `revenue/latest-right-customer-queue.json` were NOT found at expected paths — these may have moved or been renamed

### 6. Ads/Offering Specs
- **Path:** `~/Developer/rig-gtm-studio-v2/ads/prep/2026-07-31/gate-spec.json`
- **Path:** `~/Developer/rig-gtm-studio-v2/offerings/landing/TRACKING-SPEC.md`

## IntelPacket Output Structure (S83)

Written to `~/.rig/intel-packets/` (NOT the specified workdir under `~/Documents/`):

```
~/.rig/intel-packets/
├── IntelPacket-S63-GTM-INTEL-20260731T185227Z.md    # Human-readable report
├── IntelPacket-S63-GTM-INTEL-20260731T185227Z.json  # Machine-readable JSON
└── (dedup state at ~/.rig/intel-dedup-state.json)
```

### Schema
```json
{
  "schema": "rig.intelpacket.v1",
  "packet_id": "IntelPacket-S63-GTM-INTEL-{timestamp}",
  "generated_at": "ISO timestamp",
  "scan_date": "YYYY-MM-DD",
  "scanner": "rig-intel-scrape-cron",
  "workdir": "...",
  "keywords": ["gtm", "signal", "offer", "icp"],
  "summary": {
    "total_sources_scanned": N,
    "unique_entries_after_dedup": N,
    "duplicates_removed": N,
    "new_entries": N,
    "modified_entries": N,
    "existing_entries": N,
    "avg_evidence_score": 0.X
  },
  "blockers": ["..."],
  "entries": [
    {
      "source_uri": "file://...",
      "content_hash": "16-hex-chars",
      "change_type": "new|modified|existing",
      "evidence_score": 0.0-1.0,
      "tier": "gtm|signal|offer|icp",
      "title": "...",
      "summary": "...",
      "scanned_at": "timestamp"
    }
  ]
}
```

### Dedup State
```json
{
  "schema": "rig.intel-dedup.v1",
  "updated_at": "ISO timestamp",
  "fingerprints": {
    "content_hash": "source_uri"
  }
}
```

## S83 Statistics

- 23 sources scanned, 23 unique entries (0 duplicates — first run with this dedup state)
- 4 new, 11 modified, 8 existing
- Avg evidence score: 0.683
- Blockers: 4 (TCC, bun PATH, no psql, GTM state files not found)
