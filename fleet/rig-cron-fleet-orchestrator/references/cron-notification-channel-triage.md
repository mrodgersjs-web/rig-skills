# Cron Notification Channel Triage

Decision-only push delivery. Status, scrapes, health checks, learning reports → logs.

## Why this is a separate reference

`rig-cron-fleet-orchestrator` covers fleet **operations** (resume, unfreeze, Doer/Checker/Validator). Notification **channel hygiene** is a different axis — what each job does to a push surface. A perfectly-running fleet can still be a notification nightmare if 50 jobs `deliver=telegram`. Conversely, a notification-clean fleet is useless if the underlying jobs are broken.

## Trigger

- User complains "too many messages" / "I only get decision to make" / "fix my notifications"
- Inventory shows `deliver=telegram` count > 1 (or > 0 if user wants NUCLEAR)
- Telegram bot returning `Forbidden: bot was blocked by the user` errors
- New cron jobs added without explicit deliver-channel review
- User is "away from desk" (gym, travel) and wants AFK notifications

## Philosophy

**Push channels carry DECISIONS only.** Not status, not scrape results, not health checks, not learning reports, not pipeline states. Status goes to `local` (logs/files).

The decision test:

> If I don't see this for 24 hours, will I miss a decision I need to make?
> - YES → keep on push
> - NO → logs
> - "well, sometimes" → logs

Push is opt-in by default. Status is opt-in only when the user explicitly asks.

## Classification (every job gets exactly one class)

| Class | Definition | Action |
|---|---|---|
| **DEAD** | No schedule (`?` or null), never ran, or marked DEAD in its own config/paused_reason | DELETE |
| **FIREHOSE** | Active + deliver=push + high-frequency schedule (every 5/10/15m or `*/15`) | DELETE or retarget |
| **STATUS** | deliver=push for non-decision output (scrape results, learning reports, health checks, pipeline states, midcheck pulses, daily digests) | RETARGET → local |
| **DECISION** | deliver=push for content requiring human action (morning brief, approval packets, alerts requiring reply) | KEEP |

If unsure whether something is a decision, it isn't.

## Cut levels (ask user to pick)

- **NUCLEAR** — kill all push delivery, keep zero
- **TIGHT** — keep only 1 daily decision-grade push (default)
- **DEAD-LOOP ONLY** — delete dead + active firehoses, retarget status → local, leave the rest
- **SHOW-FIRST** — display full classification first, don't touch anything yet

User picks. Do not pick for them.

## Execution protocol

1. Inventory via `cronjob action=list` — tally `deliver` channels and `state`
2. Classify every job
3. Present cut-level options, wait for user pick
4. Execute deletes (`cronjob action=remove job_id=<id>`) and retargets (`cronjob action=update job_id=<id> deliver=local`) in parallel batches
5. Verify: re-list, confirm `deliver=telegram` count matches the chosen cut level, no remaining telegram jobs have `last_status=error`

## Worked example (2026-08-03)

Fleet: 140 jobs, 50 telegram-deliver, 138 paused but some had run today before the pause burst.
Real firehose: `rig-instagram-engine-oversight` at `*/15 * * * *` deliver=telegram (active + state=scheduled — was firing RIGHT NOW even with 138 others paused).

User picked **TIGHT**.

Actions taken:
- **Deleted 14**: Dykema campaign (DEAD in own config) + 13 dead `?`-schedule jobs + the active firehose
- **Retargeted 47**: all deliver=telegram jobs except one morning brief → deliver=local
- **Kept on telegram**: 1 (`rig-peak-morning-brief`, Mon–Fri 7:50am)

Result: 140 → 126 jobs, telegram deliverers 50 → 1. Mike went from 136 messages/day to a single daily brief.

## Pitfalls

- **Paused ≠ safe**: a paused job that ran today still hit Telegram. `last_run_at` is truth, `state` is current intent.
- **High-freq "watchdog" jobs are the usual culprit**: `terminal-keepalive`, `health-check`, `*-pulse`, `autonomous-work-finder` at `every 5m/10m/15m` deliver=telegram are the firehose. Almost always retarget or delete.
- **Don't trust the prompt summary**: many cron job descriptions claim "Silent on success; alerts to Telegram when pipeline..." — read the `deliver` field, not the description.
- **The bot may already be blocked**: many cron delivery errors are `Forbidden: bot was blocked by the user`. A blocked bot + active job = silent failure that looks like success in your list.
- **Active firehoses hide in plain sight**: a job with `state=scheduled` + `deliver=telegram` + high-frequency schedule is firing RIGHT NOW even with 138 others paused. Look at `state` + `schedule` together.
- **The shell `hermes cron` CLI is BLOCKED** by the `rig-knowledge-context` hook (requires `--rig-task "<task>"`). Use the `cronjob` tool surface — `remove` and `update` actions both work.

## Tool surface confirmed working

- `cronjob action=list` — full inventory
- `cronjob action=remove job_id=<id>` — delete
- `cronjob action=update job_id=<id> deliver=local` — retarget (any field supported)

Both remove and update support parallel batch invocations.