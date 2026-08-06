# Bulk Resume + Delivery Rewire After Emergency Freeze

When a fleet-wide emergency freeze pauses 50–128 cron jobs and the operator wants them all back — especially with a delivery channel change (e.g. `local` → `telegram`) — this is the operational recipe.

## When to use

- Emergency freeze was applied (e.g. `Emergency fleet freeze requested by Mike`) and the operator says "bring up all jobs"
- Operator wants all active jobs to deliver to Telegram (or another IM channel) so they can monitor from mobile
- Need to categorize jobs by function (revenue, social, infrastructure) and resume the right ones

## Recipe

### Step 1: Inventory via `cronjob(action='list')`

Returns up to 128 jobs. Read the full list. Categorize each by:

| Category | Signals |
|----------|---------|
| Revenue/GTM | `gtm`, `outreach`, `email`, `enrichment`, `revenue`, `deal` |
| LinkedIn | `linkedin`, `alfred`, `ralph`, `comment`, `engagement`, `dykema` |
| X/Twitter | `x-`, `twitter`, `xurl` |
| Infrastructure | `node-ops`, `heartbeat`, `health`, `healer`, `monitor`, `vercel` |
| Content | `content`, `draft`, `hook`, `carousel`, `article` |

### Step 2: Resume in batches of 10

The `cronjob` tool is one-action-per-call. Use parallel tool calls:

```python
# 10 parallel resume calls per turn
cronjob(action='resume', job_id='abc123')
cronjob(action='resume', job_id='def456')
# ... up to 10 per assistant turn
```

### Step 3: Switch delivery to Telegram

After resuming, update delivery in a second pass (also parallel):

```python
cronjob(action='update', job_id='abc123', deliver='telegram')
cronjob(action='update', job_id='def456', deliver='telegram')
```

### Step 4: Keep high-frequency jobs local

Jobs running every 1–15 minutes should stay `deliver: local` to avoid Telegram spam:
- Health checks (every 2m)
- Intel scrapes (every 5m)
- GTM monitors (every 5m)
- Healers (every 15m)
- Gateway keepalives (every 15m)
- Fleet controllers (every 5m)

### Step 5: Create autonomous work-finder loop

If the operator is going AFK (gym, meeting, sleep), create a keep-compounding cron:

```
Schedule: every 45m
Deliver: telegram
Skills: [rig-operator-doctrine, gbrain]
```

The prompt should:
1. Check for errored jobs and diagnose
2. Scan GBrain/Obsidian for new signals
3. Find the SINGLE highest-impact work item
4. Execute it without asking (operator pre-approved)
5. Report: fleet status, action taken, next opportunity, blockers

## Pitfalls

1. **Telegram bot may be blocked** — multiple jobs showing `Forbidden: bot was blocked by the user` means the operator needs to unblock the bot in Telegram before delivery works. Always check `last_delivery_error` on existing Telegram-delivered jobs.

2. **Jobs with `?` schedule never fire** — some jobs have `"schedule": "?"` which means they're dispatch-triggered, not cron-triggered. Don't try to resume these expecting them to run on a timer.

3. **Two passes needed** — `cronjob` tool can't resume AND update delivery in one call. Plan for: Turn 1 (resume batch), Turn 2 (update delivery batch), repeat.

4. **Don't resume scrape-substrate jobs blindly** — 5GB substrate scrapers (JAKE-SCRAPE-*) may have been intentionally paused due to disk space or provider issues. Check `paused_reason` before resuming.

5. **`paused_reason` reveals intent** — jobs paused with reasons like `lobehub-opt:outward_erroring` or `unknown_provider_blackwell_vllm` have known failure modes. Fix the underlying issue or leave them paused.

## Worked example (2026-07-29 session)

- 128 total cron jobs, ~70 paused from July 23 emergency freeze
- Resumed 42 revenue/LinkedIn/infrastructure jobs in 4 batches of 10
- Switched 9 active RIG Forge + LinkedIn jobs from `local` to `telegram`
- Created 3 new X/Twitter posting jobs (X Daily Post, X Engagement, X Mentions Monitor)
- Created 1 autonomous work-finder loop (every 45m)
- Total time: ~5 minutes across 6 assistant turns
