# Fresh-Pct Math — Worked Examples and Audit

The fresh-pct metric tells you what fraction of today's deliverable is genuinely new vs carried-forward from prior cycles. The dept's `pai.json` declares the floor (typically 0.40 = 40%). Tracking it correctly across cycles prevents the cron from silently regressing into "everything is fresh because nothing's persisted."

## The formula

```
fresh_count        = artifacts written this cycle
pre_existing_count = total artifacts on disk BEFORE this cycle's writes
total_today        = fresh_count + pre_existing_count
fresh_pct          = fresh_count / total_today
```

Critical: `pre_existing_count` must NOT include the artifacts you're about to write. Always compute it *before* the writes, or subtract your own writes before computing the denominator.

## Worked example — legal cycle, 2026-07-06

Pre-existing on disk before cycle:

```
entities/:
  - legal-contract_templates-entity-1.md
  - legal-gdpr-entity-2.md
  - legal-dp_checklist-entity-3.md
  - gdpr-info-entity-1783303299.md
  - gdpr-info-entity-1783303507.md
  - llm-patterns-1783303355.md
  - llm-patterns-1783303532.md
  - rocketlawyer-entity-1783303299.md
  - rocketlawyer-entity-1783303508.md
patterns/:
  - candidates-cycle-1.md

total pre-existing = 10
```

Cycle plan: 50 entities + 25 topics = 75 fresh writes.

After writes:

```
fresh_count       = 75
pre_existing      = 10
total_today       = 75 + 10 = 85
fresh_pct         = 75 / 85 = 0.8824 = 88.24%
target ≥ 0.40     → PASS
```

## Multi-cycle drift (correct behavior)

```
cycle 1:  pre=10  writes=75  total=85   fresh=88.24%  PASS
cycle 2:  pre=85  writes=75  total=160  fresh=46.88%  PASS
cycle 3:  pre=160 writes=75  total=235  fresh=31.91%  FAIL (< 40%)
```

If cycle 3 fails, the answer is NOT to write fewer artifacts — that defeats the cron. The right answers:

1. **Bump the per-cycle write target up** (e.g. 100 entities + 50 topics instead of 50+25) so fresh-count grows faster than pre-existing
2. **Or prune stale pre-existing artifacts** that are no longer load-bearing (the verifier can flag them)
3. **Or accept the drift** and report `fresh_pct: 0.32, target_met: false` honestly — that's a signal that the dept substrate has matured and the cron should rebalance

What you do NOT do: inflate `fresh_count` by writing throwaway files, or deflate `pre_existing_count` by deleting real ones silently.

## The "fake freshness" audit

Run this query weekly to detect crons that are gaming fresh-pct:

```python
from pathlib import Path
import json
from datetime import datetime, timedelta

ENT = Path("~/.rig/departments/<dept>/substrate/entities").expanduser()
PAT = Path("~/.rig/departments/<dept>/substrate/patterns").expanduser()
PROOF = Path("~/.rig/departments/<dept>/proof").expanduser()

now = datetime.now()
# Anything modified in last 24h = potential today's write
recent = []
for p in ENT.glob("*.md"):
    age = now - datetime.fromtimestamp(p.stat().st_mtime)
    if age < timedelta(hours=24):
        recent.append((p.name, age.total_seconds() / 3600))

# Cross-reference against today's proof packet
proof_files = sorted(PROOF.glob("daily-cycle-*.json"))
if proof_files:
    latest = json.loads(proof_files[-1].read_text())
    claimed_fresh = latest["artifacts"]["entity_count"] + latest["artifacts"]["topic_count"]
    print(f"Claimed fresh this cycle: {claimed_fresh}")
    print(f"Files modified in last 24h: {len(recent)}")
    if len(recent) > claimed_fresh * 1.1:
        print(f"⚠️  Suspicious: more files modified than claimed ({len(recent)} vs {claimed_fresh})")
```

If `len(recent)` > `claimed_fresh`, either:
- Another cron is writing into the same dir (cross-talk)
- The dept's builder is over-generating
- An external scrape (RAG, Recall ingestion) is staging artifacts into entities/

## Common mistakes

1. **Counting the just-written files in pre-existing** — makes fresh-pct trend toward 100% artificially.
2. **Using absolute file count instead of relative** — pre-existing is whatever was on disk when the cron started; subtract your own writes.
3. **Forgetting patterns/** — entities and patterns are different dirs. Both contribute to fresh-pct.
4. **Globbing with the wrong extension** — `.md` is the dept standard; if a cron writes `.markdown` it's invisible to the glob.
5. **Writing to a temp dir then moving** — if the move fails, the temp dir contains 75 files that don't count toward pre-existing on the next cycle.

## Cross-reference

Used in `dept_cycle_builder.py` (`fresh_count`, `pre_count`, `fresh_pct` calculation block) and in `rig-dept-daily-goal-builder` SKILL.md §1 and §8.