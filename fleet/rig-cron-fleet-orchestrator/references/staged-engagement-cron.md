# Staged-Engagement Cron — Outward Action Held at the Gate

A third sub-class of cron work, distinct from the two recipes already in this skill:

- `staged-output-idempotency.md` — **content-generation** crons that write a durable, audited artifact (drafts, briefs, articles) and re-running on the same date is a corruption risk.
- `read-only-analytics-cron.md` — **read-only** crons that observe external state (Postiz metrics, social APIs, server health) and never touch the world.
- **This file** — **staged-engagement** crons whose *purpose* is to act outward (send, like, comment, connect, DM) but whose execution is held at one or more gates: Gate-D approval, scheduler pause, placeholder source data, or missing live session. The cron writes a **manifest of intended actions**, not a content artifact, and emits zero executed actions.

## When this fits

- A scheduled "shift" cron (e.g. US/EU/APAC engagement shift on a 24/7 LinkedIn department) whose spec says "do N likes, N comments, N connection requests" but whose blast radius is real-world sends.
- The cron fires, recognizes the system is in a held state, and must produce a *structured manifest* of what it *would* have done — for human review and Gate-D approval — without doing any of it.
- The orchestrator / human uses the manifest to decide what to approve, then a separate cron (or a one-shot run) executes the approved subset.

Examples: LinkedIn engagement shifts (Ralph US/EU/APAC), B2B cold-outreach batches, GTM DM cadences, ABM connection requests, social-liking campaigns.

## The held-state triggers

A staged-engagement cron should hold all action and write a manifest when **any** of these is true:

| Trigger | How to detect |
|---|---|
| **System-level pause** | The connection-automation / DM / outreach script's header text or audit file says `DM SENDING IS PAUSED` with a dated incident. Check the project's `LINKEDIN_CRON_AUDIT.md` or equivalent doctrine doc. |
| **Gate-D not granted** | No `APPROVE <run_id>` phrase has been typed for this run. Default is denied. |
| **Source data is placeholder** | The prospect/contact list has rows like `"Placeholder: AI/SaaS Founder #1"`, or fields are `[STAGED]`, or the `priority_score` is 0 across the board. The dm-specialist pattern in the ralf-department explicitly refuses to personalize against placeholders (anti-fabrication rules 1, 2, 4, 5). |
| **Live session not confirmed** | The browser/CLI session has no recent successful probe (e.g. cookie refresh > 6h ago, or a `last_status` error on the session cron). |
| **Per-action quota reached** | The DB-of-record shows today's count for this action_type is at or above the daily cap. A clean re-run the next day resets the cap. |
| **Multi-scheduler disagreement** | A scheduled action is held at one gate but allowed at another (e.g. launchd is `--dry` but a manual invocation isn't). The cron must apply the **strictest** of the gates it can see. |

**Rule:** if any single trigger is true, **all** outward actions are held. The cron writes the manifest and emits `[SILENT]` for the run.

## The 4-LinkedIn-scheduler topology (worked example)

For any cron that touches LinkedIn, the gate is not a single switch — it's a 4-way AND:

1. **Hermes cron** — `~/.hermes/cron/jobs.json` — look at the `paused_at` field on the relevant DM / outreach job. If populated, that job is held.
2. **macOS launchd** — `launchctl list | grep linkedin` — for each DM agent, check whether the script path includes a `--dry` flag. `--dry` = preview only, never send.
3. **System crontab** — `crontab -l` — check the system-level crontab for any direct outreach jobs that bypass the Hermes cron scheduler.
4. **Department daemon** — e.g. `~/.hermes/jake/ralf-department/daemon/ralph-24-7.pid` and its `daemon-state.json` — the long-running daemon may have its own outbound queue and its own gate.

**The cron must check all four, not just the one it lives in.** A single green light is not enough. The strictest gate wins. Record which gate held the run in the manifest's `blockers_summary`.

## The manifest schema

Write a JSON manifest that captures *what the cron would have done* and *why it didn't*. This is the human-reviewable artifact that the orchestrator indexes.

```json
{
  "schema_version": 1,
  "date": "YYYY-MM-DD",
  "agent": "<engine-name>",
  "shift": "US|EU|APAC|<custom>",
  "shift_window_mt": "HH:MM-HH:MM MT (or local)",
  "generated_at_utc": "<iso8601>",
  "generated_at_mt": "<iso8601>",
  "node": "<rig-...>",
  "coordinate": "L#-D#-A#-step",
  "intent": "one-sentence summary of what the shift is for",
  "system_state": {
    "<key>": "<verifiable fact: PID, paused_at, last_refresh, etc.>"
  },
  "deliverable_status": {
    "actions_executed": 0,
    "actions_staged": { "<action_type>": N, ... },
    "all_actions_gated_by": "Gate-D + paused scheduler + placeholder data"
  },
  "daily_caps": {
    "<action>_per_day_cap": N,
    "<action>_planned_<shift>": N,
    "actual_<action>_sent_today": N,
    "under_cap_<action>": true
  },
  "stages": {
    "<action_type_1>": [
      {
        "rank": 1,
        "name": "[STAGED — filled at Gate-D review]",
        "headline": "...",
        "country": "...",
        "company": "...",
        "profile_url": "[STAGED — populated by leadgen-expert at send-time]",
        "personalized_note_draft": "...",
        "personalization_anchors": ["real first name", "real company", "verified post"],
        "blocked_by": "DM_SENDING_PAUSED_<date> + placeholder data + Gate-D",
        "expected_send_window_mt": "after Gate-D approval",
        "human_like_delay_pre_send_s": 75
      }
    ],
    "<action_type_2>": [...]
  },
  "eu_trends_for_tomorrow": [...],   // optional: trend signals captured
  "stealth_rules_honored": {
    "delay_range_seconds": "30-120",
    "daily_caps_enforced": true,
    "human_like_patterns": "jittered delays, varied phrasings"
  },
  "blockers_summary": [
    "<one sentence per held gate, with date / PID / file path>"
  ],
  "gate_d_request": {
    "required": true,
    "scope": "Approve the N staged <action_type>. Each needs verified <fields> before send.",
    "approval_format": "APPROVE <run_id> or per-request approval",
    "owner": "Mike (Gate-D)"
  },
  "what_this_shift_did_not_do": [
    "Did not send any <action>.",
    "Did not execute the live stealth-browser or connection-automation scripts.",
    "Did not write to engagement.db (other than reading today's action counts).",
    "Did not fabricate any names, companies, post URLs, or post content."
  ],
  "next_safe_action": "Mike reviews the manifest. After approval, leadgen-expert fills [STAGED] fields with verified identities. Then Gate-D triggers the send script with --dry=false override."
}
```

The `actions_executed: 0` field is the most important line. It is a positive, non-ambiguous statement of what the cron did. A future audit can grep for `"actions_executed": 0` to find every held-state run.

## The "[STAGED]" discipline

Every field that would normally be a real name / real company / real post URL / real commenter URN must be the literal string `"[STAGED — to be filled at Gate-D review]"` or `"[STAGED]"`. **Never** use a plausible-sounding fake. The 2026-07-03 fabricated-content incident is exactly what this discipline prevents: a template with `[first name]` / `[company]` / `[recent post]` filled in by a generator that "sounded right" but was invented.

The `personalization_anchors` list is the contract: it names the fields that *must* be verified before the manifest can be acted on. A Gate-D reviewer reads this list and confirms each one before typing `APPROVE <run_id>`.

## Engagement DB schema gotchas (read before writing queries)

The `~/.hermes/skills/linkedin-studio/data/engagement.db` SQLite DB has these column-name gotchas that bite cron writers who assume generic names:

| Table | Column you might expect | Actual column |
|---|---|---|
| `connection_requests` | `sent_at` | `timestamp` |
| `comments_posted` | `posted_at` | `timestamp` |
| `activity_log` | `action_type` | `action_taken` |
| `monitor_targets` | `region` / `country` | **DOES NOT EXIST** — these columns are absent |
| `audience_contacts` | `region` / `country` | **DOES NOT EXIST** — must add or filter post-hoc |

To get today's counts for cap reconciliation:

```sql
SELECT COUNT(*) FROM connection_requests WHERE date(timestamp)='YYYY-MM-DD';
SELECT COUNT(*) FROM comments_posted      WHERE date(timestamp)='YYYY-MM-DD';
SELECT action_taken, COUNT(*) FROM activity_log
  WHERE date(timestamp)='YYYY-MM-DD' GROUP BY action_taken;
```

**A cron that wants region/country filtering (e.g. "EU commenters only") cannot do it at the DB layer** — those columns don't exist. Filter post-hoc from the fetched list using the commenter's `last_active` timezone or `location` field, which is *not* in the DB either. This is a known schema gap; until it's filled, region filtering is a post-fetch concern, not a query concern.

## Worked example: Ralph's EU engagement shift, 2026-07-06

A scheduled cron at 14:00 MT (start of the EU shift) fires the EU engagement burst. The spec says: 10 comments on EU creator posts, replies to all EU commenters on Mike's posts, 5 personalized connection requests to EU CEO/CTO, 20 likes, monitor EU trends for tomorrow.

**Cron observes at start:**

1. `~/.hermes/jake/ralf-department/LINKEDIN_CRON_AUDIT.md` → "DM SENDING IS PAUSED due to fabricated content incident (2026-07-03)" — system-level hold.
2. `launchctl list | grep linkedin` → DM agents loaded, all carry `--dry` flag.
3. `ps -ef | grep ralph` → `ralph-24-7.sh` running (PID 10539) but its DM subsystem is bound to the same gate.
4. `sqlite3 engagement.db "SELECT COUNT(*) FROM audience_contacts"` → 17 rows, all `priority_score=0`, all `source=dm_outreach`, all placeholder-looking names.
5. `sqlite3 engagement.db "SELECT COUNT(*) FROM monitor_targets"` → 0 rows.
6. `head ~/.hermes/jake/ralf-department/proof/daily/dm_log_2026-07-06.json` → prior `dm-specialist` run at 20:09 UTC was `run_mode: "no-op-blocked"` for the same reasons.

**Cron writes `~/.hermes/jake/ralf-department/proof/daily/engagement_eu_2026-07-06.json`** with:

- `actions_executed: 0`
- `actions_staged: { connections: 5, comments: 10, likes: 20 }`
- 5 connection objects, each with `[STAGED]` for name / company / country / profile_url, a real `personalized_note_draft` (template, not fabricated), and a `personalization_anchors` list naming the verification fields.
- 10 comment objects, each with `[STAGED]` for post URL and post author.
- 20 like objects, each with `[STAGED]` for post URL and post author, and a jittered `human_like_delay_pre_react_s` (45–92s).
- `blockers_summary` with one bullet per held gate, citing date and file path.
- `gate_d_request` with scope and approval format.
- `next_safe_action` pointing at the human-review workflow.

**Cron emits `[SILENT]` for the run.** The orchestrator routes the manifest to the human-review queue. The cron does not retry, does not re-write, and does not claim any actions were taken.

## Anti-patterns to avoid

- **Filling `[STAGED]` with "plausible" data.** A name that "sounds right" is exactly the 2026-07-03 failure mode. Leave the fields as `[STAGED]` or refuse to run.
- **Hiding the held state in fine print.** A manifest that says "shift ran successfully" while `actions_executed: 0` and `deliverable_status.blocked_by: "..."` is lying. Make the held state loud: top-level `run_mode: "no-op-blocked"`, an empty `actions_taken: []`, and a per-row `actions_skipped: [{ reason: "..." }]` block.
- **Silently passing because "nothing changed."** The cron produces the manifest *every* time it runs in a held state. Repeated `[SILENT]` runs without a manifest means the system has no audit trail of why nothing happened.
- **Bypassing the cap check because "we're under cap."** Under cap is necessary but not sufficient. Gate-D, source data, and live session are independent gates — pass all of them or hold all actions.
- **Trusting a single scheduler's "green" status.** The 4-LinkedIn-scheduler topology means you must check all of them. A clean Hermes cron with a paused launchd agent still doesn't send.
- **Claiming the manifest itself is the "send."** A manifest is a *staging artifact*. It is not the action. Until Gate-D fires and the live execution script is invoked with `--dry=false`, nothing has been sent.
- **Writing Python expressions into JSON.** A `write_file` call with `{"x": i+1 for i in range(20)}` is invalid JSON; the parser fails and the cron errors out. Expand any list comprehensions into explicit dict objects before writing. The `read-only-analytics-cron.md` cron-mode constraints (#1, #2) are still in force.

## See also

- `staged-output-idempotency.md` — content-generation crons that produce audited artifacts
- `read-only-analytics-cron.md` — read-only metrics-snapshot crons; shares the cron-mode runtime constraints (#1, #2, #3)
- SKILL.md §3 — Doer / Checker / Validator separation (this sub-class is Doer-only; Checker/Validator aren't relevant because nothing was built)
- `cron-pin-pitfalls.md` — for provider/model pinning failures (different failure class)
- SKILL.md §9–§12 — M2 auto-fix, M3 blocklist, and the history-log overwrite trap apply if the held-state triggers an alert that the self-healing monitor picks up
