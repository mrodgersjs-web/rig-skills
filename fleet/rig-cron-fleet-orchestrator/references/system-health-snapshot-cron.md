# System Health Snapshot Cron — 5-Check Panel, Tiered Escalation

Distinct from the content/engagement analytics cron (`read-only-analytics-cron.md`) and the self-healing fleet watchdog (`self-healing-monitor-cron.md`). This is the pattern for a **lightweight, fast-cadence system-health probe** that answers one question every cycle: *is the platform healthy enough to keep running the other crons?* It produces a tiered status (HEALTHY / WARNING / CRITICAL) and writes a date+hour proof file for trend inspection.

## When this fits

- A cron fires every 15–60m and asks "are the basics still working?" (disk, rate limits, queue, cron jobs, error log)
- The output is consumed by a daily-briefing cron, a dashboard, and a human (only on CRITICAL)
- The cron is a *detector*, not a *fixer* — it surfaces issues, doesn't repair them
- Tiered escalation matters: a single WARNING should NOT page anyone, but a CRITICAL should

Examples: Ralph department health monitor (every 30m), platform-level capacity probe, post-pipeline heartbeat, daily ops "is the train still moving" check.

## Why this is NOT `read-only-analytics-cron.md`

The content/engagement analytics cron answers "what are the post metrics looking like?" — that's a content-pipeline question. The system-health snapshot answers "is the host even up to run the content pipeline?" — that's a *precondition* question. Different schema, different escalation semantics, different cadence.

Concrete differences:

| Aspect | read-only-analytics-cron | system-health-snapshot-cron |
|---|---|---|
| What it measures | Engagement, reach, conversion | Disk %, queue depth, cron health, error counts |
| Schema | Long content taxonomy | Short fixed 5-check panel |
| Escalation tier | None (always writes proof, no human action) | HEALTHY / WARNING / CRITICAL — CRITICAL pages |
| Cadence | 6h or daily | 15m to 1h |
| When output is empty | Report as data limitation (Postiz `[]`) | Report the disk pressure / queue starvation explicitly |
| Active fix authority | None | None — detector only, fixes belong in ops cron |

## The 5-check panel that survives

Pick a stable set of checks at the start; don't grow the panel every cycle. Standard RIG-department health panel:

```python
HEALTH_CHECKS = [
    "disk_space",      # df -h /, alert if >85% (WARNING) or >95% (CRITICAL)
    "rate_limits",     # provider quota or 429 counters, warn if approaching cap
    "postiz_queue",    # postiz posts:list | wc -l, CRITICAL if 0 when expected > 0
    "cron_jobs",       # hermes cron list or jobs.json count vs expected
    "recent_errors",   # tail of today's error log, FAIL if non-zero count exceeds threshold
]
```

Keep the panel fixed for ≥30 cycles before adding a new check. The value is *trend over time*, not breadth. Adding a check retroactively breaks trend continuity.

## The 3-tier escalation model

```text
HEALTHY   → write proof, return summary, no human action
WARNING   → write proof, log to ops log, surface in next daily briefing
             DO NOT page anyone, DO NOT pause jobs, DO NOT auto-fix
CRITICAL  → write proof + diagnostic report, alert Mike, pause non-essential jobs
             (only when scope is bounded and reversible)
```

Tier rules learned the hard way:

1. **WARNING is the silent default.** A 93% disk on a 30m cadence is *expected* — most cron-cycles on a real machine will be WARNING on disk. If WARNING paged, you'd page 23×/day. WARNING is a *trend signal* for the daily briefing, not an alert.

2. **CRITICAL is the exception, not the escalation of WARNING.** WARNING does not auto-promote to CRITICAL just because the number is high. CRITICAL has its own threshold (e.g. disk >95% with active write failures, queue 0 when expected ≥10, cron jobs 0/N when daemon claims healthy, error count > 5/min sustained). The two tiers are independent.

3. **The script's tier output is advisory, not gating.** Treat the script's `status: CRITICAL` as a *prompt to verify*, not as a permission to pause. The cron must independently confirm CRITICAL conditions before pausing jobs. Why: a misconfigured `df` parser can return `99%` on an empty mount; pausing jobs on that signal is destructive.

4. **CRITICAL alert destination is a Mike-visible channel**, not a debug log. Decide the channel when the cron is built. If no channel exists, do not silently upgrade WARNING to a fake CRITICAL — instead, fail the cron with `exit 1` and a clear "no alert channel configured" message in the proof file.

## Cron-mode runtime constraints (inherited)

All cron-mode constraints from `read-only-analytics-cron.md` apply unchanged:

- `execute_code` is BLOCKED → use `write_file` + `terminal python3`
- Pipe-to-interpreter is BLOCKED → redirect output to `/tmp/` first, then run a separate Python script that reads the file
- No user is present → decide the WARNING vs CRITICAL policy at cron-build time
- `[SILENT]` and content are mutually exclusive → return one or the other
- `write_file` is not JSON-aware → build payloads with `json.dump(..., ensure_ascii=False)` and re-parse to verify
- `report_generated_at_utc` is the actual time; the filename's `HH` is the scheduled slot

The read-only cron-mode skill warning is most relevant here when checking cron jobs via `hermes cron list` — it's ~1200 lines, pipe to `/tmp/cron-list-current.txt` first, then grep per ID with `^  ` anchor. See `self-healing-monitor-cron.md` §"Cron state inspection — the jobs.json contract" for the full recipe and the `data.get("jobs", data if isinstance(data, list) else [])` defensive pattern.

## Diagnostic-report archival pattern (CRITICAL only)

When CRITICAL fires, save a separate diagnostic report — not the same file as the periodic proof:

```
~/.hermes/jake/<dept>/state/health/diagnostic_<YYYY-MM-DD>T<HHMM>.json
~/.hermes/jake/<dept>/state/health/diagnostic_<YYYY-MM-DD>T<HHMM>.md
```

Why two files: the JSON is for the alert channel / downstream tooling; the `.md` is for Mike reading on his phone. The `.md` should be human-readable: top offenders with sizes, reclaimable totals, a one-paragraph diagnosis, and a numbered action list.

Do NOT overwrite prior diagnostic files. CRITICAL may fire multiple times in a window; the operator wants to diff them, not see the latest one only.

## Disk-pressure deep-dive (the most common WARNING)

`du -sh` on the top 8–10 cache and app-data dirs is the canonical next step when disk > 90%. The `~/.cache` and `~/Library/Application Support/Google` dirs are the two highest-leverage reclaim targets on a typical macOS dev machine. Always include in the diagnostic report:

| Path | Pattern | Reclaim safety |
|---|---|---|
| `~/.cache/uv` | `uv cache clean` | Safe — uv re-downloads on demand |
| `~/.cache/codex-runtimes` | Recreate on next model run | Safe — runtime is regenerable |
| `~/.cache/huggingface/hub` | Manual — keep models in active use | Needs review — slow to re-download |
| `~/.npm` | `npm cache clean --force` | Safe — npm re-downloads on install |
| `~/Library/Application Support/Google/Chrome/Default/Service Worker` | Browser clears on restart | Safe — rebuilt by sites |
| `~/Library/Application Support/Google/Chrome/Default/IndexedDB` | Site data | Mostly safe — clears with browser reset |
| `~/Downloads` | Manual review | Needs review — may contain active work |
| `~/Library/Developer/Xcode/DerivedData` | `rm -rf` safe | Safe — rebuilt by Xcode |
| `~/Library/Caches/ms-playwright` | Older versions only | Safe — keep latest, drop older |
| `~/.cargo` | `cargo cache --autoclean` | Mostly safe — keeps registry index |

The report should produce a `reclaim_potential_gb` field summing the safe rows. Mike uses this number to decide whether to schedule a cleanup or escalate to "expand the disk."

## Trend tracking across cycles

The `state/health/` directory holds:

- `health_{YYYY-MM-DD}T<HHMM>.json` — every cycle, append-only
- `health_latest.json` — the most recent, overwritten each cycle
- `health_latest.md` — the most recent, human-readable
- `diagnostic_{YYYY-MM-DD}T<HHMM>.{json,md}` — CRITICAL only

A daily-briefing cron reads `health_latest.json` and surfaces:

- Current tier (HEALTHY / WARNING / CRITICAL)
- Tier trajectory: "WARNING for last 4 cycles (2h)" or "all HEALTHY for 24h"
- Top WARNING or CRITICAL condition with one-sentence summary
- Most recent diagnostic report path (if any)

The trajectory string is the single most useful field — a sustained WARNING with a clear owner is actionable; a fluctuating tier is noise. The briefing cron should compute `tier_streak_hours` itself, not expect each cycle to carry it.

## Anti-patterns

- **Promoting WARNING to CRITICAL because "it feels bad."** The thresholds are numeric; honor them. A 93% disk is WARNING until the writes start failing.
- **Auto-pausing crons on CRITICAL without scope check.** Pausing the wrong job is destructive. The cron should *propose* a pause list and *require* operator confirmation, not execute it. Exception: when the alert channel explicitly grants pause authority, the cron can act — but log every action.
- **Treating the script's exit code as the verdict.** A `WARNING` script can exit 0 just fine. The cron protocol is to read `status` from the proof file, not rely on `$?`.
- **Writing a single `health.json` that gets overwritten.** Like analytics, this is a trend file. Date+time-stamp every cycle.
- **Skipping the `.md` diagnostic on CRITICAL.** A 47-page JSON is unreadable at 2am. The `.md` is the difference between a 5-minute triage and a 50-minute one.
- **Tracking tier without tracking the specific check that drove it.** "WARNING — disk at 93%" is actionable. "WARNING — see details" is not. The proof file must always name the check.
- **Recommending "consider expanding disk" as a real action.** If the disk is full, the reclaim list is the action. "Expand the disk" is a Mike-decision, not a cron recommendation.

## Worked example: ralph-department health monitor, 30m cadence

A scheduled cron every 30m (Ralph's health monitor):

1. Run `python3 ~/.hermes/jake/ralf-department/skills/health_check.py` — the script returns a JSON blob to stdout with status, checks, recommendations
2. Parse the JSON via `write_file` + `terminal python3` (no pipe)
3. Compute `cycle_n = len(list(state/health/health_*.json)) + 1`
4. Write `state/health/health_{YYYY-MM-DD}T<HHMM>.json` with the script's full output + `tier_streak_hours` and `cycle_n`
5. Overwrite `state/health/health_latest.json` with the same payload
6. If tier == CRITICAL: write the `diagnostic_{ts}.{json,md}` pair, alert via the configured channel (currently the cron response itself)
7. If tier == WARNING: log to `state/health/warning-streak.log` (append one line: `HH:MM cycle=N tier=WARNING check=disk_space pct=93`)
8. Final response: short summary table (5 check rows + tier + cycle number + trajectory) OR `[SILENT]` if tier == HEALTHY (the proof file is the value; the response is just a digest)

For this specific cron, the cron brief says "if HEALTHY, continue normal operations and log status" — that maps to emitting the digest summary, NOT `[SILENT]`. `[SILENT]` would suppress the cron delivery. The cron returns a short summary on HEALTHY too. Reserve `[SILENT]` for cycles that produce no useful delta (rare for a 5-check panel).

## See also

- `read-only-analytics-cron.md` — content/engagement analytics cron (sibling pattern, different schema)
- `self-healing-monitor-cron.md` — fleet-watchdog cron (M1-M5 monitors, jobs.json contract, stall-vs-cadence rule)
- `cron-mode-content-drafter.md` — agent-mode content-drafting cron (Gate-D staging pattern)
- `write-file-json-escape-pitfall.md` — the `write_file` JSON-escape failure modes
- SKILL.md quick-decision flow item 7 — read-only analytics / metrics-snapshot cron (parent category)
