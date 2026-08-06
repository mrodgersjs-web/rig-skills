# Compound-Cycle State Pattern

The `cycles[]` array inside `~/.rig/departments/<dept>/goals/_state.json` is the durable evidence trail of every daily cycle in the current day. It is **append-only** — never overwrite, never prune. The state file is the substrate on which the next cycle's "compound" work builds.

## State file shape

```json
{
  "schema": "rig.dept.daily_goal.v1",
  "dept": "legal",
  "owner": "Vera Jr",
  "tier": 3,
  "node": "lite-84",
  "entity_target": 50,
  "topic_target": 25,
  "fresh_pct_target": 0.4,
  "today_count": 105,
  "last_run_at": "2026-07-07T01:30:30Z",
  "state": "ACTIVE",
  "date": "2026-07-06",
  "fresh_pct": 0.9143,
  "entities_written": 70,
  "topics_written": 35,
  "blocklist_hits": 0,
  "cycles": [
    {
      "cycle": "daily-goal-v1",
      "run_id": "legal-daily-20260706212822",
      "entities": 50,
      "topics": 25,
      "fresh_count": 75,
      "fresh_pct": 0.8824,
      "ts": "2026-07-06T21:28:22Z"
    },
    {
      "cycle": "daily-goal-v2-compound",
      "run_id": "legal-daily-20260706222800",
      "entities": 20,
      "topics": 10,
      "fresh_count": 30,
      "fresh_pct": 1.0,
      "ts": "2026-07-07T01:30:30Z"
    }
  ]
}
```

## Cycle transitions

| Cycle | today_count (before) | new entities | new topics | fresh_count | today_count (after) | cumulative fresh_pct |
|---|---|---|---|---|---|---|
| daily-goal-v1 | 0 | 50 | 25 | 75 | 75 | 75/85 = 0.8824 |
| daily-goal-v2-compound | 75 | 20 | 10 | 30 | 105 | 105/115 = 0.9130 |

The `fresh_pct` of each cycle is computed against the new artifacts only — it's 100% fresh from the perspective of the new cycle (because the new cycle writes net-new files). The cumulative `fresh_pct` is what's reported to the daily-goal target.

## The append discipline

When updating `_state.json` for a new cycle:

1. **Read** the current state file with `read_file` (do not trust in-context memory)
2. **Deep-copy** the parsed JSON
3. **Append** a new entry to `cycles[]` — do NOT modify prior entries
4. **Compute** the new `today_count` as `previous_today_count + new_fresh_count`
5. **Recompute** the cumulative `fresh_pct` as `total_fresh_count / (total_entities + total_topics)`
6. **Set** `last_run_at` to the new cycle's ISO timestamp
7. **Write** with `write_file` (this file is small + flat, no jq-patch discipline needed; unlike `36h-goal-proof.json` which has accumulated state that demands jq patching)

## When to NOT append

If the new cycle produced 0 fresh artifacts (all entities were skipped due to blocklist, or all scrapes failed), DO NOT append a cycles[] entry. Instead, log a single audit line:

```json
{"ts":"...","actor":"<agent>","action":"<dept>-daily-cycle","summary":"NOOP: 0 entities produced (all URLs failed or blocklist hit)","run_id":"<run_id>","entity_count":0,"topic_count":0,"fresh_pct":0,"verdict":"NOOP"}
```

NOOP cycles don't appear in `cycles[]` — they appear only in the audit log. This keeps the cycles[] array meaningful (every entry is a real cycle that produced net-new substrate).

## Cross-day behavior

At midnight, the state file rolls over. The new day's `_state.json` starts fresh:

```json
{
  "schema": "rig.dept.daily_goal.v1",
  "date": "2026-07-07",
  "today_count": 0,
  "fresh_pct": 0,
  "cycles": [],
  ...
}
```

The **previous day's** `_state.json` is preserved as `~/.rig/departments/<dept>/goals/_state.<YYYY-MM-DD>.json` for retros. Weekly and monthly aggregations read from these per-day snapshots.

## Cumulative freshness targets

The daily goal target is `fresh_pct ≥ 0.4` (40% of all artifacts written that day must be net-new). The compound-cycle pattern is specifically designed to keep this metric high across multiple cycles per day — each cycle writes fresh artifacts, so the cumulative fresh_pct stays well above 0.4.

If `fresh_pct < 0.4` at end of day, the cron has a problem:
- Either the source queue isn't producing enough new URLs (queue rotation issue)
- Or the entity extraction is duplicating from prior cycles (idempotency check needed)
- Or the agent is rewriting existing files instead of writing new ones

Investigate by diffing the `cycles[]` array entries — if cycles[N] produced 0 fresh_count, the source queue rotated but the entities weren't unique.

## Verifying state across cycles

After each cycle, the ProofPacket's `state_update.sha256` field captures the SHA-256 of the state file at write time. This binds the state snapshot to the ProofPacket. The agent reads this back during retros to reconstruct exactly what the state looked like at each cycle boundary.

## Anti-patterns

1. **Overwriting `cycles[]` entries.** Always append; never modify prior cycles. Prior cycles are evidence.
2. **Computing `today_count` from in-context memory.** Always `read_file` first.
3. **Setting `fresh_pct` to the per-cycle value instead of the cumulative value.** The `fresh_pct` field in `_state.json` is cumulative; the per-cycle value lives inside the `cycles[]` entry.
4. **Skipping the `cycles[]` update on a partial-success cycle.** If the cycle wrote 5 entities but failed at step 5 (Supabase), still append a cycles[] entry with `entities: 5, topics: 0` and let the verdict reflect the partial status.
5. **Reusing the same `cycle` name across runs.** Each invocation must have a unique `cycle` name (use `daily-goal-vN-compound` with N incremented from prior cycle).