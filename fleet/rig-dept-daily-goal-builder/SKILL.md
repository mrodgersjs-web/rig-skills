---
name: rig-dept-daily-goal-builder
description: Per-department RIG daily-goal cron that writes a fixed batch of fresh substrate (entities + topics) against the dept's existing scraped corpus, with proof-packet sealing, dept-verifier gate, and freshness score >= target. USE WHEN running a cron that fires against ~/.rig/departments/<dept>/, must hit a fixed entity/topic count, needs to keep fresh-content pct above a target across cycles, requires word-boundary blocklist checking against short tokens, or wants per-artifact sha256 proof sealed to ~/.rig/departments/<dept>/proof/. NOT for fleet provider-pinning (use rig-cron-fleet-orchestrator), single-shot scraping (use scripts/scraper_template.py under rig-cron-fleet-orchestrator), or ad-hoc research (use Research skill).
---

# rig-dept-daily-goal-builder

Class-level doctrine for a cron whose job is "produce N entities + M topics of fresh substrate for one RIG department per cycle, prove it, and gate it against the dept verifier."

This is a distinct class from `rig-cron-fleet-orchestrator` (which orchestrates provider pinning across heterogeneous local nodes) and from research skills (which do ad-hoc, open-ended exploration). A daily-goal cron has:

- A fixed per-day deliverable (e.g. 50 entities + 25 topics)
- A freshness floor (e.g. ≥ 40% fresh = new artifacts / total)
- An existing scraped corpus to draw from (`substrate/scraped/*.raw`)
- A per-dept verifier gate (`verifier.py`) that scores against the dept's `north_star` metric
- A proof packet sealed per cycle under `proof/daily-cycle-{ts}.json`

## When to use

- The cron message names a `dept` (legal, sales, finance, security, ...) and an entity/topic target
- Source queue lives in `~/.rig/departments/queues/<dept>.json`
- The dept has a `pai.json` (owner, telos, north_star, blocklist, skills catalog) and a `verifier.py`
- Existing scraped substrate is available under `substrate/scraped/*.raw` (full bodies preserved)
- Freshness score must compound across cycles (yesterday's cycle = today's seed floor)

## Class-level rules

### 1. Probe before you generate — read existing artifacts, don't overwrite

Before the cycle runs, list what already exists in `substrate/entities/` and `substrate/patterns/`. The pre-existing count is the denominator for fresh-pct math. Use `Path.glob` (cheap, deterministic) and treat:

```python
pre = [p for p in ENT_DIR.glob("*.md")] + [p for p in PAT_DIR.glob("*.md")]
# subtract what you're about to write so you measure the actual prior corpus
pre_count = len(pre) - len(will_write_this_cycle)
```

Pitfall: counting the just-written files in the pre-existing pool makes fresh-pct trend toward 100% artificially. Always subtract your own writes before computing the floor.

### 2. Deterministic content variant picking via article-num-mod-N

When composing entity pages that combine a primary source (e.g. GDPR Art. N) with secondary artifacts (DP checklist items, contract template variants), pick variants with a stable modulo formula so two cron runs on the same input produce identical pages — and a verifier can re-run a hash check:

```python
# DP_ITEMS has 12 entries, CONTRACT_VARIANTS has 5
dp_picks = [DP_ITEMS[(art_num * 3 + i) % len(DP_ITEMS)] for i in range(3)]
cv_picks = [CONTRACT_VARIANTS[(art_num + i) % len(CONTRACT_VARIANTS)] for i in range(3)]
```

Never use `random.choice()` or `hashlib.md5(os.urandom(...))` for variant picking — it breaks reproducibility and makes proof hashes non-deterministic.

### 3. **Blocklist matcher: word-boundary, never substring**

Substring matching false-flags legitimate text. Real case: GDPR Art. 27 contains "establish**ed**" which substring-matches blocklist token "**HED**". False-flag rate goes through the roof on legal/medical corpora where short tokens are embedded in normal English.

Use lookaround regex instead:

```python
import re
def block_check(text: str, blocklist: list[str]) -> bool:
    low = text.lower()
    for b in blocklist:
        # (?<![A-Za-z0-9]) and (?![A-Za-z0-9]) = ASCII word boundary
        # re.escape guards against regex metachars in the term
        if re.search(r"(?<![A-Za-z0-9])" + re.escape(b.lower()) + r"(?![A-Za-z0-9])", low):
            return True
    return False
```

Always test the matcher against a known-bad input AND a known-good input before shipping the cron. If a verifier.py exists in the dept (`~/.rig/departments/<dept>/verifier.py`), check whether *it* also substring-matches — if so, fix the verifier too with the same regex upgrade; otherwise the cron will write artifacts the verifier rejects.

### 4. Schema, not prose — every entity has a Facts fence

Each entity page MUST carry a YAML frontmatter + `## Facts` block that lists `metric / value / unit / period` rows. The verifier and the L7-promotion gate parse this block; if it's missing or free-form, the page is a draft, not an artifact:

```markdown
---
type: legal_entity
kind: gdpr_article
article: Art. 5
cluster: principles
source: gdpr-info
url: https://gdpr-info.eu/art-5-gdpr/
owner: Vera Jr
scraped_at: 2026-07-06T21:28:22Z
cycle: daily-goal-v1
fresh: true
---

## Facts
metric: article_number
value: 5
unit: ordinal
metric: regulation_ref
value: Regulation (EU) 2016/679
unit: celex
```

### 5. Update `_state.json`, don't fork a new schema

The dept already has a `goals/_state.json` with `entity_target`, `topic_target`, `fresh_pct_target`, `today_count`, `week_count`. The cron overwrites today's fields (`today_count`, `last_run_at`, `fresh_pct`, `entities_written`, `topics_written`, `blocklist_hits`) and increments `week_count`. Do NOT introduce a new state file or a new schema version — the dashboard cron reads the existing shape.

### 6. Proof packet — sealed, sorted, sha256-per-artifact

After every cycle, write `~/.rig/departments/<dept>/proof/daily-cycle-{YYYYMMDD-HHMMSS}.json` with:

```json
{
  "schema_version": 1,
  "run_id": "<dept>-daily-<ts>",
  "agent": "<dept>-daily-cycle-builder",
  "coordinate": "L4-D1-A3-I2",
  "artifacts": {"entities": [{"path", "sha256", "bytes"}, ...], "topics": [...]},
  "blocklist": {"enforced": [...], "hits": [...], "check_passed": bool},
  "freshness": {"fresh_count", "pre_existing_count", "fresh_pct", "target_fresh_pct", "target_met"},
  "gate": {"metric", "verifier", "verdict": "PASS|FAIL"}
}
```

Write with `json.dumps(..., indent=2, sort_keys=True)` for deterministic hashes. Sort keys so re-running the script on the same input produces byte-identical proof.

### 7. Run the dept verifier at the end — it's the gate

After writing artifacts, run `python3 ~/.rig/departments/<dept>/verifier.py '{"stub":"cycle-N-..."}'` and capture the JSON verdict. If the verdict is anything other than `PASS`, mark the proof packet `verdict: FAIL` and write a `_state.json` `state: "HALT"` rather than `ACTIVE`. Do not deliver a "cycle complete" report if the verifier rejected the artifacts.

### 8. Compound, don't reset

Every cycle's `today_count` becomes the next cycle's seed floor. The pattern is:

```
cycle-N entities written:  50 fresh
cycle-N+1 pre-existing:   50 (from N) + 10 (from older seeds) = 60
cycle-N+1 fresh:          50 new
cycle-N+1 fresh-pct:      50 / (60 + 50) = ~45%
```

So freshness drifts DOWN as cycles accumulate — that's correct and intended. The target (≥40%) is a floor, not a goal to maximize. If fresh-pct climbs above 70% after several cycles, you're either not actually writing durable artifacts or the pre-existing seed floor is too small. Audit `substrate/entities/` and `substrate/patterns/` weekly.

### 9. Source preservation first, page synthesis second

The cron should NOT scrape the live web every cycle. The existing scraped bodies (`substrate/scraped/*.raw`) are the persistent truth. Use those bodies for lookup (`grep -oE "Art\. [0-9]+"` etc.) and synthesize structured entity pages from the catalog you extract, not from fresh HTTP calls. If the source corpus is missing or stale, that's a separate upstream-scraper problem and gets logged in `proof/`, not silently re-fetched.

### 10. Use a builder script, not ad-hoc write_file calls

The cron should call one Python builder that:
1. Reads the source catalog (extracted from scraped corpus)
2. Generates all 50 + 25 pages in memory
3. Block-checks the full batch
4. Writes only the passing set to disk
5. Computes fresh-pct
6. Writes proof + state
7. Prints a 1-line summary

Single-purpose Python scripts are easier to re-run, easier to debug, and easier to re-trigger from `hermes cron run` than a 50-step in-loop session.

**Cron-mode execution pitfall:** in the scheduled-cron profile, `execute_code` is BLOCKED ("cron jobs run without a user present to approve it"). Use `terminal` with `python3 -c '...'` or `python3 << 'PYEOF'` heredocs instead. Bash heredocs inside `for` loops also cannot use zsh-style `${VAR,,}` lowercase expansion; precompute the slug in python and pass via env or per-iteration heredoc. Hit on finance cycle 2026-07-06: 10/10 `pricing_model-${CODE,,}-${SLUG}.md` expansions failed with `bad substitution` before switching to a python loop with `str.lower()`.

## Don't capture these in the skill

- Specific GDPR article titles — date-bound to a corpus; the *pattern* is reusable, the corpus is not
- The `gdpr-info.eu` URL or any specific upstream — they rot; the technique (extract catalog from existing `.raw`) does not
- A specific entity count like "50" — that's per-dept in `pai.json` / `_state.json`, not a global constant
- A specific verifier verdict text — the dept may rename its `north_star` metric

## Quick decision flow

```
1. Cron message names a dept + entity/topic target + freshness target?
   → You're in this class. Read pai.json + _state.json + verifier.py first.
2. Source queue exists but scraped bodies are missing?
   → Don't run the cycle. Log upstream-scraper-gap in proof/ and stop.
   → Don't silently re-scrape from cron-mode; that's a separate upstream job.
3. Blocklist contains tokens ≤3 chars (HED, US, AI, EU)?
   → Always use word-boundary regex (§3). Substring matcher will false-flag.
4. dept's verifier.py substring-matches the blocklist too?
   → Upgrade the verifier's matcher with the same word-boundary regex.
   → Otherwise you'll write 50 artifacts that the verifier rejects.
5. fresh-pct has been climbing above 70% across cycles?
   → Either writes aren't durable (check schema/§4) or pre-existing floor is small.
   → Audit the entities/ and patterns/ dirs before claiming success.
6. Run after artifacts written?
   → Always end with: verifier verdict check → proof packet → _state update.
```

## See also

- `references/blocklist-word-boundary.md` — full recipe for the word-boundary matcher with worked examples (GDPR Art. 27, common false-positive tokens)
- `references/fresh-pct-math.md` — worked freshness score computations across multiple cycles, plus the audit query that detects "fake freshness"
- `references/dept-verifier-gate.md` — pattern for reading `verifier.py`, catching its blocklist substring bug, and patching it before the cron fires
- `references/finance-entity-triad.md` — finance-dept-specific entity composition (formula + pricing model + runway forecast triad per page) and 80-entity working rotation
- `scripts/dept_cycle_builder.py` — generic dept-agnostic builder template (catalog + checklist + variants → 50 + 25 pages with proof + state)