# Compound-Cycle Gap Identification & Idempotency

Companion to `compound-cycle-state-pattern.md`. The state-pattern reference covers
how `_state.json` evolves across cycles; this reference covers **how the operator
chooses what the next compound cycle should produce** and the **idempotency
discipline** that prevents duplicate writes from corrupting the compound ledger.

## The gap-identification problem

After cycle N lands, the operator must answer one question before cycle N+1:

> Given the prior cycles' outputs (entity filenames, topic slugs, scraped source
> coverage), what is the smallest set of **net-new artifacts** that compounds the
> substrate without duplicating?

A naive answer (re-run the same source list, re-emit the same entities) produces
zero fresh_pct and burns a cycle. The honest answer is gap-driven: enumerate what
the prior cycles **did not** produce and target those.

## Step 1 — Enumerate the prior substrate

Read these three signals before writing any new artifact:

```bash
# 1. Existing entity filenames
ls ~/.rig/departments/<dept>/substrate/entities/ | sort

# 2. Existing pattern slugs (just the slug portion)
ls ~/.rig/departments/<dept>/substrate/patterns/ \
  | sed -E 's/^<dept>-topic-//; s/-compound-[a-z0-9]+\.md$//' \
  | sort -u

# 3. The cycles[] array — what each cycle produced
jq '.cycles[] | {cycle, entities, topics, fresh_pct}' \
  ~/.rig/departments/<dept>/goals/_state.json
```

The first two give you the **filename set**; the third gives you the **count
trajectory** (was the previous cycle a v(N-1) baseline or another compound?).

## Step 2 — Classify existing entities by angle

Most compound cycles add a new **angle** on the same source domain. For the legal
dept this looks like:

| Cycle | Angle | Filename marker | Coverage |
|---|---|---|---|
| v1 (baseline) | GDPR Articles 1-50 | `legal-art-NN-gdpr.md` | article-level |
| v2-compound | GDPR Recitals + OpenAlex works | `legal-recital-NN-...compound-...` | preamble + academic |
| v3-compound | High-impact recitals + adjacent-regime works | `legal-recital-NN-...compound-v3.md` | selected recitals + AI/NIS2/DORA |
| v4+ (future) | SCC module-specific DPAs, NIS2 sector-specific TOMs, etc. | `...-compound-v4.md` | regime-specific |

Other depts have their own angle taxonomy. The pattern is the same: **each cycle
fills a distinct angle bucket**, not a fresh artifact with the same angle.

## Step 3 — Build the gap list

Concrete recipe (legal dept, after v2-compound):

```python
# What v2-compound produced
prior_recitals = {1, 23, 49, 75, 83}  # from ls + sed
prior_work_ids = {"W2938574745", "W3104571892", ...}  # 15 IDs

# Candidate gap set — recitals not yet covered
all_high_impact_recitals = {4, 7, 22, 26, 30, 39, 47, 49, 75, 78}  # 10 picks
gap_recitals = all_high_impact_recitals - prior_recitals
# gap_recitals = {4, 7, 22, 26, 30, 39, 47, 78}  # 8 gaps; v3 picks these

# Same exercise for adjacent-regime topics
prior_topics = {"academic-evidence", "cloud-dpa", "multi-tenant",
                "verifiable-compliance", "iot-dpa", "grc-framework",
                "nis2-dpa", "tpms-vendor", "compliance-roi",
                "recitals-framework"}
adjacent_regime_gaps = {"ai-act", "nis2-cadence", "dora",
                        "eprivacy", "uk-dpf"}  # 5 picks, distinct from prior
```

Generalizing: **the gap set is `candidate_set − prior_set`** for each angle bucket.

## Step 4 — Idempotency: skip-if-exists

The previous worker (`build_daily_cycle.py`) overwrites existing files. For
compound cycles this is catastrophic: re-running v3 after a partial v3 success
would zero the cumulative fresh_pct and corrupt the cycles[] ledger. **Always
skip files that already exist.**

```python
# In the cycle writer
def write_if_new(path, text):
    if path.exists():
        # Re-run safety: do NOT overwrite, do NOT include in cycles[] counts
        return False
    path.write_text(text, encoding="utf-8")
    return True
```

And only count entities/topics that were **actually written this run**, not
entities that were already on disk:

```python
written = []
for r in NEW_RECITALS:
    text = make_recital_entity(r, cycle, now)
    if block_check(text):
        blocked_hits.append((f"recital-{r['n']}",))
        continue
    path = ENT_DIR / f"legal-recital-{r['n']}-gdpr-compound-v3.md"
    if not write_if_new(path, text):
        continue
    written.append({"path": str(path), "sha256": sha(text), "bytes": len(text)})
```

This is what made cycle v3 in the legal dept a clean 20+5 net-new increment
on top of v2's 20+10, instead of a destructive overwrite.

## Step 5 — Honest gap framing for missing writes

The cron prompt's 8-step spec describes 4 write layers (local substrate, GBrain,
Supabase, Obsidian). In practice, not all 4 are always reachable:

- **GBrain on `127.0.0.1:3131`** — `/health` returns ok, but `/api/entities`
  POST returns 404 (endpoint not exposed). Verify with a probe before claiming
  a successful write. Log the skip as `gbrain: skipped (endpoint not exposed)`.
- **Supabase** — requires the per-dept MCP wrapper or a remote OAuth token. If
  not configured, log `supabase: skipped (no remote write path configured)`.
- **Obsidian vault** — `~/Documents/JakeStudio/Department PAI/<dept>/` may
  not have the per-dept subdir yet. `mkdir -p` first.
- **Local substrate** — always works. This is the hard dependency.

**Honest report pattern:** in the 6-line summary, separate the always-on writes
from the best-effort ones:

```
Writes: substrate=20 entities+5 topics, obsidian=written (path), 
        gbrain=skipped (endpoint 404), supabase=skipped (no remote path)
```

Do not claim "all 4 layers written" if only 2 actually landed.

## The writer-side blocklist regex

Companion to `references/blocklist-monitor-pattern.md` in
`rig-department-architecture`. That reference covers the **monitor** side
(scanning existing substrate for violations). This is the **writer** side
— what regex to use when **generating** content that should not contain a
blocklist term as a substring.

```python
import re

def block_check(text: str) -> bool:
    """Word-boundary blocklist check for content generation."""
    for b in BLOCKLIST:
        # (?<![A-Za-z0-9]) and (?![A-Za-z0-9]) are ASCII-only lookarounds
        # that match the boundary between any non-alphanumeric char and
        # the term. Crucially, "EDPB" does NOT trip on "HED" because
        # 'D' is alphanumeric and the left-lookaround fails.
        if re.search(
            r"(?<![A-Za-z0-9])" + re.escape(b.lower()) + r"(?![A-Za-z0-9])",
            text.lower()
        ):
            return True
    return False
```

The standard `\b` word-boundary does **not** work here: `\bhed\b` will match
the substring in "headless" (no word boundary between `h-e-d` and the following
character is required because `e`/`d` aren't at a word boundary on the right
side — `\b` only requires a transition, not absence). The custom lookaround
pair `(?<![A-Za-z0-9])...(?![A-Za-z0-9])` requires **both** sides to be
non-alphanumeric, which is the right semantics for "term is a standalone word."

This is the same regex used in `~/.rig/departments/legal/scripts/build_daily_cycle.py`.
Use it in any new compound cycle builder to keep blocklist compliance uniform
across the v(N) series.

## Cycle-skip vs cycle-fail

If the gap list is empty (the prior cycles already covered every angle
the operator planned), **skip the cycle** rather than emit a noop. A noop
cycle:

- Adds 0 to `today_count`
- Sets `fresh_pct` to undefined / no-change
- Clutters the cycles[] array
- Wastes a ProofPacket

Detection:

```python
if not written and not topics_written:
    print("NOOP: no gaps to fill; prior cycles already covered this angle set")
    # Optionally append to audit log only:
    # append_audit({"ts": ..., "action": "legal-daily-cycle", "verdict": "NOOP"})
    return 0
```

If the gap list is non-empty but every entity was **blocked** by the blocklist
check, that's a real failure: log `verdict: FAIL`, append the cycles[] entry
with the blocklist hits in `blocklist.hits`, and surface in the 6-line summary.

## Cycle-name versioning

The cycles[] array accumulates `cycle: daily-goal-vN-compound` entries. The
number N is the compound ordinal (1 for v1 baseline, 2+ for compounds). Each
new cycle:

- Increments N by 1 from the prior cycle's N
- Embeds the N in **every** artifact filename (`...-compound-v3.md`)
- Embeds the N in the cycle frontmatter `cycle:` field

This makes `ls *compound-v3*` and `grep "cycle: daily-goal-v3-compound"` work
as instant cycle-boundary queries.

## Worked example: legal v3-compound, 2026-07-07

Prior state: v1 (50 art entities + 25 topics) + v2-compound (5 recitals + 15
OpenAlex works + 10 compound topics). `today_count: 105`.

Gap analysis:
- Recitals covered: {1, 23, 49, 75, 83} → 5 of 173. Add 10 more high-impact
  recitals (4, 7, 22, 26, 30, 39, 47, 49 [wait — 49 is in prior; replaced
  with 49 still kept as compound extension of same recital], 75 [same], 78).
  Real gap set: {4, 7, 22, 26, 30, 39, 47, 78} + 2 of the prior ones for
  cross-reference density.
- OpenAlex works covered: 15. Add 10 more in adjacent regimes (AI Act, NIS2,
  DORA, ePrivacy, UK DPF, data trusts, federated learning, e-Evidence,
  Polish case law, Schrems II 5yr).
- Topics covered: 10 compound topics. Add 5 adjacent-regime topics
  (ai-act-gdpr-overlap, nis2-incident-cadence, dora-ict-risk-stack,
  eprivacy-cookie-consent, uk-dpf-transatlantic-bridge).

Result: 20 entity files + 5 topic files, all new, all passing blocklist,
all with sha256 hashes. `today_count: 105 → 130`, fresh_pct stays 1.0,
cycles[] grows by 1 entry (v3-compound).

## Anti-patterns

1. **Re-emit prior cycle's entities with new timestamps.** This corrupts the
   cycles[] array — the entry claims 50 fresh entities, but disk has the same
   50 files from v1. Detector: diff v3 entity SHA-256 against v1 entity
   SHA-256; any collision = duplicate.
2. **Write the same topic slug twice across cycles.** Topic slugs must be
   unique. Detector: `ls patterns/ | sort | uniq -d`.
3. **Skip the gap analysis and re-run `build_daily_cycle.py`.** This is the
   v1 baseline writer — re-running it overwrites the v1 artifacts and gives
   you 0 fresh_pct for the new cycle.
4. **Bump N without bumping the content.** `daily-goal-v4-compound` that
   re-runs the v3 entity set is fraud. Each N must produce a new gap set.
5. **Claim the cycle is "PASS" if you skipped writes due to write_if_new.**
   If every entity was already on disk and the cycle wrote 0 files, the cycle
   is NOOP, not PASS. Verdict must reflect what actually happened.
