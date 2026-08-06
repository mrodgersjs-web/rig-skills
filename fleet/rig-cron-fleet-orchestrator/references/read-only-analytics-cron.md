# Read-Only Analytics Cron — External Data → Daily Proof File

Distinct from the Doer/Checker/Validator content-generation pattern (see `staged-output-idempotency.md`). This is the pattern for a **read-only cron** that pulls external metrics (Postiz, social APIs, server stats) and writes a date+hour-keyed proof file. The cron never produces artifacts that need human review — it just observes and reports.

## When this fits

- A cron fires every 6h / daily / weekly and asks "what is the current state of X?"
- The output is a JSON proof file under `~/.hermes/jake/<dept>/proof/{daily,weekly,monthly}/`
- No human approval step between cron run and orchestrator pickup
- Downstream crons (dashboards, alerts) read the file but don't grade it

Examples: LinkedIn global analytics, follower growth tracker, server health probe, content-pipeline KPI snapshot, brand-mention scraper.

## The schema that survives

Use a stable top-level shape across every analytics cron in a department. Pick once, keep it:

```json
{
  "schema_version": 1,
  "report_type": "<dept>_<what>_<cadence>",
  "agent": "<engine-name>",
  "report_generated_at_utc": "<iso8601>",
  "report_window": {
    "start_utc": "...", "end_utc": "...", "duration_hours": N,
    "local_time_utc": "...", "local_time_local": "..."
  },
  "data_sources": { "<src>": "<status/notes>" },
  "system_health": { "<key>": "<status/notes>" },
  "global_metrics": { ... },
  "<section_by_topic>": { ... },
  "<alerts>": [],
  "next_recommended_actions": [],
  "thirty_day_target_comparison": { "targets": {...}, "verdict": {...} }
}
```

The `report_type` string should embed the department + what + cadence so files sort correctly and downstream tooling can parse without reading the file. Example: `ralph_global_analytics_6h`.

The `system_health` block is what saves you on quiet days — when analytics is empty because the platform is dead, you want a row that says "daemon dead since YYYY-MM-DD" instead of zero data and a misleading "all green."

## File naming

`{proof_dir}/{cadency_dir}/{report_type}_{YYYY-MM-DD}_{HH}.json` — e.g. `proof/daily/analytics_global_2026-07-06_12.json`.

- **Date-stamped AND hour-stamped** so a 6h cron (00, 06, 12, 18) produces 4 files/day, not 1, and the consumer can see trend within a day.
- Keep cadence-dir (`daily` vs `weekly` vs `monthly`) separate from the time stamp. The orchestrator indexes by directory.
- Don't overwrite — append a new file. The cron is idempotent by definition (read-only) so a missed cycle is a gap, not a corruption.
- **The `HH` in the filename is the SCHEDULED slot, not the actual run time.** A 6h cron scheduled at 00/06/12/18 produces `analytics_global_2026-07-07_00.json` even when the run completed at 00:03. Use `report_generated_at_utc` for the actual time. This makes scheduled-vs-late runs visible at a glance — a file named `analytics_global_2026-07-07_18.json` written at 19:42 UTC means a slot was late.

## Postiz CLI — the source of truth for LinkedIn metrics

```bash
POSTIZ=~/.hermes/node/bin/postiz

# Auth check (always do this first)
$POSTIZ auth:status
# → "Authentication method: API Key (environment variable)  ...  6 integration(s) connected."

# List integrations to get the right IDs
$POSTIZ integrations:list
# → JSON with id, name, identifier, picture, profile per integration
#   - Personal LinkedIn: identifier="linkedin", name="Mike Rodgers"
#   - Company page:      identifier="linkedin-page", name="Rodgers Intelligence Group"

# Page-level analytics (WORKS for company page, returns daily series per metric)
$POSTIZ analytics:platform <integration_id>
# → [{label:"Page Views", data:[{total, date},...], percentageChange}, ...]

# Per-post analytics for personal LinkedIn
$POSTIZ analytics:post <postiz_post_id>
# → []  ← ALWAYS EMPTY for personal LinkedIn accounts
```

**The data-availability trap on Postiz v2:**

| Surface | Page account (`linkedin-page`) | Personal account (`linkedin`) |
|---|---|---|
| `analytics:platform` (page-level) | ✅ 7+ days of daily series for views/clicks/shares/followers/engagement | ❌ Returns `[]` — personal accounts have no platform-level analytics on Postiz v2 |
| `analytics:post` (per-post) | ❌ Returns `[]` | ❌ Returns `[]` — personal LinkedIn doesn't expose per-post metrics via Postiz v2 |
| `posts:list` (publish metadata) | ✅ | ✅ |
| `posts:create / status / delete` | ✅ | ✅ |

So **Postiz is the publish-metadata source of truth** (post_id, release_id/URN, publish date, content) but **NOT the engagement-metrics source of truth** for personal LinkedIn profiles. The page account gives you page-level totals only.

If you need per-post engagement for personal LinkedIn: either (a) read it from the live page via stealth browser (post URL → scrape impressions/likes/comments from the post's social-actions bar), or (b) accept that the analytics output will be "metadata only" and report that as a known limitation in `system_health`.

## Engagement DB as a fallback source

`~/.hermes/skills/linkedin-studio/data/engagement.db` is a 41-table SQLite DB with prior readback data. It's the best you have for legacy engagement numbers but it's only useful if a previous readback cron was running.

The relevant tables for analytics:

| Table | What it gives you | Watch out |
|---|---|---|
| `published_posts` | Legacy post URN + hook_type + pillar + cta_type | Only 4 rows in the audit; doesn't include the Postiz-published posts |
| `post_metrics` | impressions, likes, comments, reposts, follows, engagement_rate per post per capture time | Stale if the readback worker died |
| `post_engagement` | Older `captured_at` series with same fields | Often empty for the active campaign |
| `linkedin_post_metrics` | The 6-gate scoreboard output, not engagement | Don't confuse with engagement metrics |
| `connection_requests` | Connection sent + accepted + verified + accepted_at | Empty if connection-automation never ran |
| `follows_log` | `followed_at`, `name`, `headline` — profile URL keyed UNIQUE | Often the only signal that any outreach ever happened |
| `profile_snapshots` | `captured_at`, `followers`, `connections`, `posts_count` | Empty if no profile-snapshot cron has run |
| `comments_posted`, `activity_log` | Should be appended by every cron | Both empty in a dead-department state |

Query pattern for "latest metric per post":

```sql
SELECT post_urn, MAX(captured_at) AS last_capture
FROM post_metrics
GROUP BY post_urn;
```

Then for each post_urn, fetch the row with `MAX(captured_at)`. SQLite doesn't have a clean DISTINCT-ON, so do two queries or a window function.

## Blocklist quarantine — strict word-boundary, NOT substring

When a cron watches a blocklist (HED, IdeaWake, Anthony Langeweg, hed-forge, dec-* tokens, etc.) over scraped substrate, the obvious grep is `grep -iE "HED|..."` — but that catches **substring false positives** aggressively. Live example from the 2026-07-14 cron monitor on `~/.rig/departments/*/substrate/scraped/`:

| Substring pattern | Hits in a clean security/strategy corpus | Why it hit |
|---|---|---|
| `HED` | appears in `THREADED`, `HEADER`, `identification` substrings | common English words |
| `IDEA` | appears in `identification`, `IDEAS`, `IDEAL` | academic vocabulary |
| `AWA` | appears in `awareness`, `awaiting` | common vocabulary |

The cron MUST use **word-boundary or quoted-regex** patterns:

```bash
# WRONG — false positives on every English corpus
grep -iE "HED|IdeaWake|Anthony Langeweg|hed-forge|dec-1783268304352-va5c" *.raw

# RIGHT — \b on short tokens, literal on multi-word strings
grep -iE "\bHED\b|\bIdeaWake\b|Anthony Langeweg|hed-forge|dec-1783268304352-va5c|dec-1783268340018-db8f" *.raw
```

**Discipline when hits fire:**

1. Run BOTH the substring scan AND the strict scan.
2. If strict=0 but substring=N, the report MUST distinguish them: `"blocklist_substring_false_positives": N, "blocklist_quarantines": 0, "action": "none_required_strict_check"`. Do NOT count substring hits as quarantines — that's how you turn a clean run into a fake incident.
3. If strict>0, quarantine the matching file(s) per the M3 blocklist protocol (class-level rule #10).
4. Log the false-positive categories (e.g. `["identification","threaded","preferred"]`) in the proof file so the operator can audit the discipline.

**Where this shows up in the proof schema:**

```json
{
  "blocklist_quarantine": {
    "scanned_against": ["HED","IdeaWake","Anthony Langeweg","hed-forge","dec-1783268304352-va5c","dec-1783268340018-db8f"],
    "substring_matches_initial": 6,
    "strict_word_boundary_matches": 0,
    "false_positive_categories": ["identification","threaded","preferred"],
    "matches": 0,
    "action": "none_required_strict_check"
  }
}
```

`matches` is the field downstream consumers should read — it is the strict count, not the substring count.

## Honest no-op → real-work compounding transition

A cron monitor that runs every 2h on the same substrate root will frequently encounter cycles where the prior cycle had zero new substrate (< 2h window) and the current cycle has 5+ new files. The honest no-op prior cycle and the real-work current cycle MUST both be honest in their own proof — and the current cycle MUST read the prior cycle's proof before writing its own.

**The pattern:**

1. **Read prior proof first.** `cat ~/.rig/state/24x7-ops/<node>-proof.json` — confirm `prior_proof_was_honest_no_op`, `delta_from_prior_cycle`, and `prior_outputs_read`.
2. **Do NOT widen the scrape window** to manufacture work. If the < 2h window returns zero files, report zero files, not "expanded to 6h and found 3."
3. **Do NOT silently swap models** if the cron asks for `ornith:35b` and the node only has `ornith:9b`. Run inference on `ornith:9b`, label the output `ornith:9b`, and explain in the proof why. (Class-level rule #6 — "Cron prompt model must match the live node's loaded model" — applies here too.)
4. **When prior cycle was no-op and current has work:** explicitly mark the proof as `compounded_on_cycle_N`, list the prior cycle's entities that informed the current run, and note the delta. Don't pretend the prior cycle never happened; don't re-derive its facts.
5. **Always compound, never duplicate.** If the prior cycle already wrote `entities/threat-patterns-cycle-2026-07-14.md` for a different node, write THIS cycle's entity as `entities/threat-patterns-cycle-2026-07-14-node-<N>.md` with a `prior_cycle_compounded: true` flag in the frontmatter. Future cycles compound on both.
6. **Quality gate carries across cycles.** Every new entity must still have `## Facts` fence + `evidence_count >= 1` + `confidence >= 0.5` + 3 bullets. The "cycle 4 had no work" never becomes an excuse to relax the gate in cycle 5.

**Why this matters:** the orchestrator reads prior cycle proofs to decide if a cron is healthy. A monitor that flips between "zero work" and "fabricated 17 entities" without an honest delta is indistinguishable from a monitor that's gone rogue. The compounding block in the proof is the audit signal.

## Cron-mode runtime constraints (READ THIS FIRST)

When a cron job runs, several tools that work in interactive mode are restricted. Plan around them **before** writing the script:

1. **`execute_code` is BLOCKED.** The error reads:
   > BLOCKED: execute_code runs arbitrary local Python (including subprocess calls that bypass shell-string approval checks). Cron jobs run without a user present to approve it. Use normal tools instead.
   Fix: use `write_file` to create the script, then `terminal` to run it.

2. **Pipe-to-interpreter is BLOCKED by Tirith security scan.** Commands like `postiz posts:list | python3 -c "..."` raise:
   > Security scan — [HIGH] Pipe to interpreter: postiz | python3: Command pipes output from 'postiz' directly to interpreter 'python3'. Downloaded content will be executed without inspection.
   Fix: redirect to a temp file first, then run a separate `python3 /tmp/script.py` that reads the file. The full pattern:

   ```bash
   # Step 1: write the tool output to a temp file
   ~/.hermes/node/bin/postiz posts:list > /tmp/postiz_posts_list.json 2>&1
   # Step 2: write a python script that reads the file (NOT a pipe)
   # (use write_file)
   # Step 3: run it
   python3 /tmp/ralph_aggregate.py
   ```

3. **No user is present to answer questions or approve steps.** Decide a policy for every "should I?" moment ahead of time:
   - "Should I bootstrap the empty `connection_requests` table?" — NO, just report it as unmeasurable. Bootstrapping is a separate decision.
   - "Should I run stealth browser readback for the 4 untracked posts?" — NO, just report it as a known gap with the next-action pointer. That's a different cron.
   - "Should I retry on a transient error?" — YES, with a bounded attempt count, and log every attempt.

4. **No `[SILENT]` and then content.** The cron brief says either report findings or return `[SILENT]` alone. Don't combine them in the same output. The orchestrator routes based on the literal token.

5. **Deliver the report as the final response.** Don't try to `send_message` to a user — there isn't one. The system delivers the response to the cron destination automatically.

6. **`[SILENT]` means return the literal token only.** When the cron brief says "if there's nothing new, respond with exactly `[SILENT]`", the orchestrator routes on that literal token. Combine `[SILENT]` with content and the orchestrator treats it as a report and delivers. The two are mutually exclusive: either write the proof file and emit a summary, OR emit `[SILENT]` alone (e.g. when the stage-aware guard above short-circuits).

   A read-only analytics cron almost never returns `[SILENT]` — its job is to write the proof file every cycle, even on quiet days. The proof file IS the value; the response is just a digest. Reserve `[SILENT]` for the rare case where the proof file would be a duplicate of the prior file (which shouldn't happen with date+hour filenames, but could happen if the cron is triggered twice in the same slot).

7. **`write_file` is the JSON-output tool but it is NOT JSON-aware.** The tool writes the content verbatim; its built-in lint only reports the **first** JSON parse error; it does not expand Python list comprehensions, f-strings, or expressions that look like code. The four common failure modes (straight double-quotes inside JSON string values, unescaped backslashes, trailing commas, code-shaped strings) all surface as `JSONDecodeError: Expecting ',' delimiter (line N, column M)` at a misleading offset. The canonical fix is to **build the payload in Python via `json.dump(..., ensure_ascii=False)` and re-parse to verify** before claiming done. See `write-file-json-escape-pitfall.md` for the four failure modes with examples, the audit loop, and the `write_file` + `terminal python3` two-step that fits cron mode.

## Verification before claiming "done"

After writing the proof file, re-read it and check:

- [ ] `os.path.getsize(path)` is > 1 KB (a 200-byte file usually means an empty result you didn't notice)
- [ ] All required top-level keys are present (run a Python check: `missing = [k for k in required if k not in data]`)
- [ ] `report_generated_at_utc` is in the current cycle (not from a stale run that someone re-ran)
- [ ] `system_health` row honestly describes any data limitation you saw
- [ ] Alerts include both red flags AND green confirmations (negative-only reports are unauditable)
- [ ] `next_recommended_actions` points at the next cron, not a vague "monitor this"

## Worked example: ralph global analytics, 6h cadence

A scheduled cron every 6h:

1. `~/.hermes/node/bin/postiz auth:status` → confirm 6 integrations connected
2. `~/.hermes/node/bin/postiz integrations:list` → identify the personal-LinkedIn and page-LinkedIn IDs
3. `~/.hermes/node/bin/postiz posts:list` → snapshot all post metadata (published + queue)
4. `~/.hermes/node/bin/postiz analytics:platform <page_id>` → snapshot page-level series
5. `~/.hermes/node/bin/postiz analytics:post <post_id>` for each published post → note as `[]`
6. `sqlite3 ~/.hermes/skills/linkedin-studio/data/engagement.db "..."` → pull legacy metrics, follows, connection counts
7. Compute: totals, by-pillar, by-hook, by-timezone (UTC hour → US/EU/APAC window), comment-to-like ratio, viral flag (≥10K impressions), 30-day target deltas
8. Write to `~/.hermes/jake/ralf-department/proof/daily/analytics_global_{YYYY-MM-DD}_{HH}.json`
9. Final response: short summary of the report (TL;DR table + posts published this window + critical findings + action items). The system delivers the response — the user is reading the cron job output, not the raw JSON.

## Anti-patterns

- **Confusing page-level analytics with per-post analytics.** They answer different questions. Page-level tells you "your company page got 5 views today." Per-post tells you "post X got 200 impressions." Don't average them or substitute one for the other.
- **Treating zero engagement as a publishing failure.** Zero engagement on a 30-min-old post is normal. Zero engagement on a 30-day-old post is a problem. Always include `published_at` and let the report compute age.
- **Writing a single "analytics.json" that gets overwritten.** A 6h cron firing 4x/day needs 4 files/day, otherwise the orchestrator can't see trend within a day.
- **Hiding data limitations in fine print.** If a metric is unmeasurable, put it in `system_health` as a red flag. Don't bury it in `notes` inside `global_metrics`.
- **Re-running the readback worker from inside the analytics cron.** That's a different job. The analytics cron observes; a separate readback cron fills gaps.
- **Filling `next_recommended_actions` with generic advice** ("post more, engage more"). The actions should be specific, timeable, and ownable: "Re-enable LinkedIn daemon: ralphctl start" not "be more active on LinkedIn."
- **Letting a "materially unchanged" cycle read as a green run.** When the prior window and current window have the same alerts and same shipping state, the report MUST say "MATERIALLY UNCHANGED" explicitly with concrete deltas (alerts count change, action items count change, new vs. persistent alerts). Otherwise the orchestrator can't distinguish "no change" from "I didn't look" and the consumer can't tell whether to act. See §"Materially-unchanged cycles" below.

## Materially-unchanged cycles

When the data pipeline is frozen (engagement loop dead, daemon unhealthy, source data stale), every cycle produces the same report. That is a real signal — the consumer needs to know nothing moved, AND they need to know HOW MUCH time has passed since the freeze started. The report should carry:

```json
{
  "global_metrics": {
    "delta_vs_previous_6h_window": {
      "new_published_posts": 0,
      "impressions_delta": 0,
      "likes_delta": 0,
      "comments_delta": 0,
      "followers_delta": 0,
      "verdict": "ZERO MOVEMENT — analytics pipeline frozen since YYYY-MM-DD; <what still works>"
    }
  },
  "comparison_to_previous_window": {
    "previous_window_utc": "...",
    "previous_report": "<path to prior proof file>",
    "previous_alerts_count": 7,
    "current_alerts_count": 9,
    "previous_recommended_actions_count": 6,
    "current_recommended_actions_count": 9,
    "state_change": "MATERIALLY UNCHANGED — <one-sentence>. <count> new alerts this window: <what changed>."
  }
}
```

Rules:

- **The deltas are zero-or-numeric, not "null".** A `null` delta is unauditable; a `0` is honest. The pipeline froze; report `0`, not `null`.
- **List the prior proof file path** in `comparison_to_previous_window.previous_report` so the operator can diff it.
- **Alert count and action-item count deltas** are the cheapest signal that something actually changed in the state. If the counts are the same and the verdicts are the same, the cycle is materially unchanged.
- **`state_change` distinguishes "same as before" from "new this cycle"** explicitly. Without it, the report reads identically across cycles and the orchestrator can't tell when the consumer has been seeing the same red flags for 14 days straight.

## The two-layer blocker pattern

When the report shows BOTH:

1. A source-side data limitation (e.g. "Postiz personal-LinkedIn analytics returns `[]`"), AND
2. A system-side operational issue (e.g. "Ralph daemon unhealthy, 0/15 crons registered"),

…then the report must diagnose them as **two independent blockers**, not one. Both must be fixed to resume analytics-grade reporting. The `executive_summary.blocker` field should explicitly call out the two layers:

```json
{
  "blocker": "Two layers: (1) <source-side> (e.g. Postiz personal-LinkedIn account has no per-post analytics coverage), AND (2) <system-side> (e.g. Ralph daemon cron jobs are not registered, so no engagement loop is running). Both must be fixed to resume analytics-grade reporting."
}
```

The temptation is to fix the system-side blocker and assume the data will flow. It won't — the source-side blocker is independent and persistent until the source itself changes (e.g. switch accounts, use stealth-browser readback, pay for a Marketing API tier). Naming both prevents the operator from "fixing" one and declaring victory.

## The daemon-process-running-but-cron-jobs-not-registered diagnostic

A common dead-department state:

```bash
$ ps -p $(cat ~/.hermes/jake/<dept>/daemon/ralph-24-7.pid)
  PID TTY           TIME CMD
10539 ??         0:00.11 bash ralph-24-7.sh
# process is alive

$ bash ~/.hermes/jake/<dept>/daemon/health-check.sh
# ❌ Daemon process: NOT running   ← health-check disagrees
# ⚠️ 0/15 cron jobs registered
```

The bash process is alive but the launchd plist never started, and `hermes cron register` was never run. The two are separate failure modes:

| State | Bash PID | launchd plist | Hermes cron jobs | Health check |
|---|---|---|---|---|
| Healthy | alive | loaded | N/N registered | green |
| Cron-jobs-not-registered (THIS pattern) | alive | not loaded | 0/N | red (1 issue) |
| Daemon-truly-dead | dead | may be loaded | may still be registered | red (different issue) |
| Both broken | dead | not loaded | 0/N | red (multiple issues) |

The analytics cron must distinguish these in `system_health`:

```json
{
  "system_health": {
    "daemon_process_pid": 10539,
    "daemon_health_check_status": "UNHEALTHY (1 issue detected per health-check.sh)",
    "daemon_cron_jobs_registered": "0/15 — <list of unregistered jobs>",
    "diagnostic": "Daemon bash process exists (PID 10539) but launchd plist not active and 0/15 cron jobs registered with Hermes. Bash process is a stale orphan from a prior session, not a managed launchd service."
  }
}
```

The fix is `<dept>ctl register && <dept>ctl restart` — both steps required.

## Disk-space alert from health-check

`health-check.sh` reports disk usage. Capture it in the report:

```json
{
  "system_health": {
    "disk_space_warning": "Volume 99% full (1.8Ti/1.8Ti) — log rotation / archive cleanup needed"
  }
}
```

A 99% disk is a critical alert, not a soft warning — log files will start failing to write and the next cron cycles will lose their proof. Promote to alerts list and `next_recommended_actions`:

```json
{
  "alerts": ["⚠️ Disk space: volume 99% full (1.8Ti/1.8Ti) — log rotation needed to prevent pipeline failures."],
  "next_recommended_actions": ["[MED] Disk cleanup: archive logs >30 days old (volume 99% full)"]
}
```

## The `good_news` block in executive_summary

A balanced executive summary needs explicit green confirmations, not just a `shipping_status: green` flag. Pattern:

```json
{
  "executive_summary": {
    "headline": "<one sentence>",
    "shipping_status": "🟡 YELLOW — <reason>",
    "data_status": "🔴 RED — <reason>",
    "system_status": "🔴 RED — <reason>",
    "blocker": "<two-layer diagnosis if applicable>",
    "good_news": [
      "<concrete positive: e.g. 'Postiz publish pipeline functional: 6 posts live, 43 queued through August 5'>",
      "<next-positive: e.g. 'Next post on schedule: day_01 at 2026-07-07 14:30 UTC'>",
      "<baseline-positive: e.g. 'Page-level analytics still working (3 clicks, 3 page views, 1 organic follower all-time)'>"
    ]
  }
}
```

Three good-news items is the right density: shipping, scheduling, and at least one piece of evidence the system is still partially working. More than three starts to read as spin; fewer than two is too sparse.

## `hours_since_publish` per published post

Each published post in the report should carry `hours_since_publish` alongside `publish_date_utc`:

```json
{
  "post_id": "cmr40qz0c01mgp",
  "publish_date_utc": "2026-07-06T15:00:00.000Z",
  "hours_since_publish": 9.05
}
```

This makes the "is this post too new to have engagement?" question answerable at a glance. A post with `hours_since_publish: 1.2` and zero engagement is normal; `hours_since_publish: 240` and zero engagement is a signal. The cron should compute the field at report time using `now - publish_date_utc`, not bake it into the source file.

## Evolving schema across cycles

The schema in §"The schema that survives" is the **stable skeleton**. Real cycles add new fields when they surface new questions:

| Field | Added when | Why |
|---|---|---|
| `data_sources.<src>_in_window` | Cron starts counting per-cycle activity | Distinguishes "this cycle" from "all time" without forcing the consumer to compute |
| `global_metrics.delta_vs_previous_<window>` | Frozen state needs explicit "no change" | See §"Materially-unchanged cycles" |
| `comparison_to_previous_window` | Frozen state needs operator diff signal | See §"Materially-unchanged cycles" |
| `top_performing_postiz_posts` | Postiz-published posts exist alongside legacy `post_metrics` | Preserves the older ranking while adding the newer source |
| `<key>_<unit>:<count>` | A specific KPI (e.g. viral threshold) becomes important | Keeps the threshold as data, not a magic number in the consumer |
| `days_into_<window>`, `days_remaining_in_<window>` | 30-day pacing | Lets the consumer see "behind / on / ahead of target" without recomputing |

Add fields when a new question is being asked. Don't pre-add them — the proof file is the record of what the system observed, not a wishlist. If a field would always be `null` for the last 7 cycles, remove it; the absence of a field IS the signal that the question isn't being asked.

## See also

- `staged-output-idempotency.md` — for content-generation crons that write audited files
- `cron-pin-pitfalls.md` — for provider/model pinning failures (different failure class)
- `lan-probe-recipe.md` — for fleet health probing (orthogonal)
- `write-file-json-escape-pitfall.md` — the `write_file` JSON-escape failure modes and the `json.dump` + re-parse fix that applies to every cron in this file
- `cron-mode-content-drafter.md` — for content-drafting crons that STAGE behind Gate-D (sibling of #7 / #8 / #10 in the SKILL quick-decision flow)
- SKILL.md §4 — "state files, not live dashboards" (the analytics file IS a state file; same logic)
