---
name: rig-cron-fleet-orchestrator
description: Operator-grade cron fleet orchestration across heterogeneous local AI nodes. Pin crons to valid live providers (NOT stale config files), persist substrate to disk as proof, run independent Doer/Checker/Validator cron trios, and write durable local status JSON after every cycle. USE WHEN running parallel cron swarms across local Ollama/Ollama-MLX nodes, scraping substrate for agent fleets, validating that provider names from config.yaml actually exist before pinning, building independent quality-gate cron trios, or recovering when a live API dashboard (Paperclip/Linear) breaks mid-sprint. NOT for generic cron syntax, single-model single-machine workflows, or doing the work directly in the agent loop (use task-agent delegation instead).
---

# rig-cron-fleet-orchestrator

The RIG operating doctrine for cron job fleets that span **multiple local AI nodes** with **heterogeneous models**. Distinct from a single-machine cron job because you have to (1) prove which nodes are actually live before pinning them, (2) persist substrate to disk because live dashboards break, and (3) enforce Doer / Checker / Validator separation because a cron that builds AND grades itself is unauditable.

## When to use

- Running N parallel cron jobs across `rig-128gb-local`, `rig-256gb-lan`, `rig-96gb-lan`, `blackwell-vllm` etc.
- Scraping substrate (5GB targets) into per-dept dirs for agent fleets
- An API dashboard (Paperclip / Linear / etc.) is your "truth" surface and you have learned the hard way it isn't
- You need ≥3 quality gates (syntax/schema/semantic) that are independent of the thing they grade
- A cron keeps failing on a provider name you thought was registered
- You want to add self-healing (drift detection + auto-pin) without making the system self-destruct
- Building a self-healing monitor cron that watches other crons (M1 stalls, M2 drift, M3 blocklist, M4 proof writer, M5 outcomes)

## Class-level rules (learned the hard way)

### 1. Probe the LAN before you trust the config

**The YAML lies. The socket doesn't.**

A `~/.hermes/config.yaml` may list providers that point at IPs that no longer respond. Always:

```python
import socket, urllib.request
# Probe the candidate IPs at the actual port, not just the config.
for ip in ips:
    try:
        s = socket.create_connection((ip, 11434), timeout=2); s.close()
        req = urllib.request.Request(f"http://{ip}:11434/api/tags")
        with urllib.request.urlopen(req, timeout=3) as r: ...
    except: pass  # DOWN — do NOT pin this
```

Then update the cron provider field with the verified IP+port, **not** the provider-name string from config (which may not exist as a registered provider).

### 2. Persist the full body, never just metadata

A "scraper" that writes `{"status":200, "bytes": 12345}` and throws the body away is a counter, not a scraper. If you want to grade the scraped content later (verifier), promote to L7 patterns, or feed it into entity pages, the body has to be on disk:

```python
raw_path = base / f"{src_name}.raw"
raw_path.write_text(body_to_save)   # up to 1MB per source
```

### 3. Doer / Checker / Validator = three cron jobs, three different models

If a cron builds AND grades itself it is unauditable. Force three independent jobs per critical workflow:

- **Doer** — produces the artifact, writes proof, never inspects itself
- **Checker** — runs mechanical/structural checks (`py_compile`, JSON parse, YAML schema, grep for `eval|exec|shell=True`), writes PASS/FAIL
- **Validator** — runs semantic checks (AntiGeneric score, blocklist grep, business rules), writes PASS/WEAK/FAIL/CRITICAL

Three different cron IDs, three different `provider` fields preferred, three different time slots. The only place they converge is the proof directory.

### 4. State files, not live dashboards

When Paperclip's API server crashed mid-sprint, the **only** thing that held was the local JSON proof files. **Always** persist:

- Per-cron proof: `/Users/rig128gb/.rig/state/{cron}-proof.json`
- Per-cycle sprint proof: `/Users/rig128gb/.rig/state/{sprint}-cycle-{N}.json`
- Per-dept substrate index: `/Users/rig128gb/.rig/departments/_REGISTRY.py`

Live dashboards are view surfaces. Disk is truth.

### 5. The 8-layer substrate pattern

Each LLM substrate needs:

```
L1 Working  → ephemeral
L2 Episodic → JSONL or SQLite
L3 Semantic → entity pages with `## Facts` fence
L4 Procedural → skills catalog
L5 Reflective → self-scored episodes
L6 Strategic → strategic memory
L7 Crystallized → promoted patterns after 3+ verified episodes + conf>0.85
```

L7 should be **empty** until real evidence accumulates. Don't auto-fill it with "candidate" garbage — that defeats the entire point.

### 6. Cron prompt model must match the live node's loaded model

If the cron prompt says `model="rig-96gb-reasoner:latest"` and you pin provider=`rig-96gb-lan`, the cron will pull whatever is the `/api/tags` default on that node — NOT what you wrote. Always verify the model string exists on the target node:

```bash
curl http://192.168.68.79:11434/api/tags | jq '.models[].name'
```

### 7. **Staged-output cron re-runs overwrite audited work**

Content-generation crons (LinkedIn drafts, blog posts, email sequences, weekly briefs) write to a dated file like `proof/daily/drafts_2026-07-06.json` and a downstream Checker/Validator cron audits it. **Re-running the Doer cron on the same date** — manually, after a schedule shift, or once a transient error clears — silently overwrites audited output, breaks Doer/Checker/Validator separation, and can lose the human's review state.

Detection before you start (fast idempotency check):

```python
from pathlib import Path
import json
p = Path(f"proof/daily/drafts_{date}.json")
if p.exists():
    data = json.loads(p.read_text())
    if data.get("drafts") and data.get("via_selection"):
        # Output already exists and is complete. Do NOT overwrite.
        return "[SILENT]"  # cron delivers nothing; orchestrator moves on
```

Fix: add a stage-aware guard at the top of every content-generation Doer cron:

| Stage of `drafts_{date}.json` | Cron action |
|---|---|
| File missing | Generate, run selection, write the file. Normal path. |
| File exists, no `via_selection` | Stalled. Either resume selection or re-generate — never silent. |
| File exists, has `via_selection`, no audit present | Generate only what's missing. Don't re-run the divergent phase. |
| File exists, has `via_selection`, audit present | Return `[SILENT]`. Work is staged. |
| File exists, has `via_selection`, audit present, Mike approved | Return `[SILENT]`. Work shipped. |
| New date | Different file. Always generate. |

Pair the guard with a process lock when the cron can be triggered by both schedule and manual invocation:

```python
import fcntl, os
lock_path = f"/tmp/{os.path.basename(__file__)}.{date}.lock"
lock_fd = open(lock_path, "w")
try:
    fcntl.flock(lock_fd, fcntl.LOCK_NB | fcntl.LOCK_EX)
except BlockingIOError:
    return "[SILENT]"  # another invocation is in flight
try:
    ...  # do the work
finally:
    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    lock_fd.close()
    os.unlink(lock_path)
```

Why this matters: an audited, staged draft set is **evidence**, not a scratch file. Re-generating on top of it destroys the audit chain, and a cron that emits "[SILENT]" while actually having clobbered the file mid-write is worse than one that errors loudly. The cron should treat dated output as append/immutable once a Checker has run against it.

See `references/staged-output-idempotency.md` for the full recipe and a worked example.

### 8. **`hermes cron list` does NOT surface provider/model — read `jobs.json` directly**

For self-healing monitors that detect M2 provider drift: `hermes cron list` shows bordered-box text with id, name, schedule, next_run_at, last_run_at, last_status only. **`--format json` is rejected** with `unrecognized arguments`. **There is no `hermes cron status <id>`** — positional IDs raise `unrecognized arguments`.

The source of truth is `/Users/rig128gb/.hermes/cron/jobs.json` — every cron is a dict with `id, name, schedule, repeat, next_run_at, last_run_at, last_status, last_error, provider, model, prompt, origin, paused_at, no_agent, ...`.

Read jobs.json directly to detect drift, prompt shape, origin (Telegram chat_id), and last_error. See `references/self-healing-monitor-cron.md` §"Cron state inspection — the jobs.json contract" for the read script and the `data.get("jobs", data if isinstance(data, list) else [])` defensive pattern.

### 9. **Stall ≠ old** — threshold separate from cadence

A 240m-cadence cron always looks ~240m old between firings. The real stall signal is `(now - last_run_at) > threshold_min` where `threshold_min ≈ 1.1 × cadence_min`. Set the threshold per cron to "just over 1 missed cycle." Always include `cadence_min` in the alert file so the operator can interpret age correctly. See `references/self-healing-monitor-cron.md` §"Stall vs cadence" for the threshold table.

### 10. **M3 blocklist quarantine is NEVER auto-fixed**

The blocklist watch monitor moves the offending file to a quarantine dir, appends to an incident log with HIGH severity, and stops. It does NOT modify the file contents, re-send, re-stage, or touch the contact. If 3+ incidents fire in 60min, log CRITICAL but do not halt — operator decides whether to extend window, halt, or stop. See `references/self-healing-monitor-cron.md` §"Blocklist quarantine."

### 11. **M2 auto-fix is gated on reversibility + scoped operator instruction**

Only M2 (provider drift) has auto-fix authority in a self-healing monitor, and only when the drift is reversible (provider/model string swap) AND the operator has not pinned the cron intentionally. If the active-goal.json `fleet_nodes_used` lists the current provider (e.g. `rig-96gb-lan` for the 36h-sprint fleet), the drift to `minimax/MiniMax-M3` is INTENTIONAL — log it as `DRIFT_DETECTED_OPERATOR_PINNED` and skip the fix. Document the pin reason in the alert file.

### 12. **History-log overwrite trap**

The rolling history log (e.g. `monitor-history.log`) is one-line-per-cycle and **append-only**. Using `write_file` on a partially-read file destroys the unobserved tail. Always use `terminal` with `echo ... >> file` to append. If you accidentally overwrite, restore from the cycle log, append a `# NOTE: tail lost on cycle-N overwrite` comment, and continue. See `references/self-healing-monitor-cron.md` §"The history-log overwrite trap."

## Don't capture these in the skill (they become persistent wrong rules)

- Provider names that work today (they'll rot). The skill teaches the **technique** (probe the LAN), not specific names.
- "Paperclip is broken" — the lesson is "live dashboards aren't truth," not "Paperclip-specific fix."
- Specific cron counts from this session — those are date-bound.
- Specific fleet cron IDs (4ca73ece55fa, etc.) — date-bound; the structure is reusable, the IDs aren't.

## Push-channel hygiene (decision-only delivery)

21. Audit / notification-channel triage: cron fleet is spamming push channels
    (Telegram, SMS) with status instead of decisions — OR user says "fix my
    notifications" / "I only get decision to make" / "if we have that many
    cron jobs we need to cut a lot out"?
    → Read `references/cron-notification-channel-triage.md`. Push channels
    carry DECISIONS only (morning brief, approval packets, alerts requiring
    reply); everything else (scrape results, learning reports, health checks,
    pipeline states, midcheck pulses, daily digests) goes to `local`. Four
    cut levels (NUCLEAR / TIGHT / DEAD-LOOP ONLY / SHOW-FIRST) — TIGHT is
    default (1 daily decision-grade push). Use the `cronjob` tool surface
    for delete/update (shell `hermes cron` CLI is BLOCKED by the
    `rig-knowledge-context` hook — requires `--rig-task "<task>"`).
    Cross-references item 19 (bulk-resume-delivery-rewire) — the resume flow
    can re-create a notification firehose if you don't apply this lens first.
    Distinct from #9 (fleet watchdog) — this is the *channel hygiene* axis,
    not the operational or monitoring axis.

## Quick decision flow

```
1. Need cron jobs across N local AI nodes?
   → Read `references/lan-probe-recipe.md` first.
2. Need scrapers that fill dept substrate dirs?
   → Use `scripts/scraper_template.py` and persist full body.
3. Need quality gates?
   → Use the 3-job Doer / Checker / Validator pattern.
4. Need fleet self-healing?
   → Write a separate cron that probes + re-pins providers (read-only mode).
5. Dashboards broke mid-sprint?
   → Status JSON is your truth. Persist + re-read after every cycle.
6. Content-generation cron re-running on the same date?
   → Read `references/staged-output-idempotency.md` and gate the Doer
     with a stage-aware guard + process lock before generating.
7. Read-only analytics / metrics-snapshot cron (Postiz, social APIs, server health)?
   → Read `references/read-only-analytics-cron.md` for the
   proof-file schema, the Postiz data-availability trap, the
   cron-mode runtime constraints (execute_code + pipe-to-interpreter blocks),
   the "materially-unchanged cycles" pattern (delta vs prior window +
   comparison_to_previous_window block), the two-layer blocker diagnosis,
   the daemon-running-but-cron-jobs-not-registered diagnostic, the
   `good_news` executive-summary block, `hours_since_publish` per published
   post, and the schedule-slot filename convention (HH = slot, not actual
   run time).
8. Daily content-generation cron that needs to mass-produce variants per topic
   (e.g. 20 hooks/topic, 5 patterns × 4 each, top-3 selection)?
   → Read `rig-content-quality-engine/references/daily-hook-generation.md`
   for the spec, output schema, empirical pattern-performance table,
   RIG-domain coverage checks, and the 5 pitfalls (apostrophe-in-Python,
   score inflation, Curiosity Gap as the structural floor, etc.).
   → Also applies: the cron-mode runtime constraints in
   `references/read-only-analytics-cron.md` (execute_code blocked,
   pipe-to-interpreter blocked) — use `write_file` + `terminal python3` instead.
9. Fleet-watchdog / self-healing monitor cron that inspects other crons
   (M1 stalls, M2 provider drift, M3 blocklist, M4 proof writer, M5 outcomes)?
   → Read `references/self-healing-monitor-cron.md` for the 5-monitor architecture,
   the `~/.hermes/cron/jobs.json` contract (hermes cron list does NOT surface
   provider/model), stall-vs-cadence rule, blocklist quarantine protocol,
   outcome path probing, the history-log overwrite trap, and the auto-fix
   policy table per monitor.
   → Cross-references the cron-mode runtime constraints in
   `references/read-only-analytics-cron.md` and the drift-handling recipe in
   `references/cron-pin-pitfalls.md`.
10. Staged-engagement / outreach cron whose *purpose* is to act outward
    (send, like, comment, connect, DM) but is held at a gate — DM-pipeline
    paused (e.g. 2026-07-03 incident), Gate-D not granted, placeholder
    source data, or no live browser session?
    → Read `references/staged-engagement-cron.md` for the 4-LinkedIn-scheduler
    topology, the held-state trigger list, the `[STAGED]` discipline, the
    `engagement_eu_{date}.json` manifest schema, the engagement.db column-name
    gotchas, and the anti-patterns (filling [STAGED] with "plausible" data,
    hiding the held state, bypassing cap check on a single gate, claiming
    the manifest is the send). Distinct from #7 (analytics) and #8
    (content-gen): a staged-engagement cron writes a *manifest of intended
    actions* and emits `actions_executed: 0` + `[SILENT]`.
    → Also applies: the cron-mode runtime constraints in
    `references/read-only-analytics-cron.md` (execute_code blocked,
    pipe-to-interpreter blocked) and the no-Python-expressions-in-JSON
    pitfall (write_file doesn't expand list comprehensions).
11. Need to bulk-create N cron jobs (5–30) from a JSON spec that specifies
    per-job model, provider, schedule, and prompt — e.g. a kanban
    `scrapers_spec.json` with one record per dept?
    → Read `references/bulk-cron-spawn-from-spec.md`. Key fact: the
    `hermes cron create` CLI does NOT accept `--model`/`--provider` flags,
    so you must create-via-CLI then patch `jobs.json` directly. Covers the
    recipe, why-patch-not-CLI, and 6 pitfalls (atomic write, duplicate
    names allowed, enabled default, etc.).
12. Agent-mode content-drafting cron that produces multiple text artifacts
    per cycle (LinkedIn comments, hooks, captions, reply threads) and
    STAGES them behind Gate-D — i.e. drafts are written to proof but the
    cron never publishes, sends, or acts outward?
    → Read `references/cron-mode-content-drafter.md`. Distinct from #8
    (selection / top-3) and #10 (manifest of intended actions): this
    cron *drafts* content (multiple artifacts per cycle, each with a
    value-add taxonomy: insight / data / question), runs a banned-word
    + voice self-audit, and writes a proof file marked
    `gate_d_status: STAGED`. Covers the batch-label convention
    (am/pm/eve × 3x daily), the `human_like_delay_pre_post_s` field, the
    pattern-anchoring discipline (cite `audience_patterns.json` IDs), and
    the **`write_file` JSON-escape pitfall**: `write_file` does not
    expand Python list comprehensions, does not auto-escape quotes, and
    the built-in lint only surfaces the *first* parse error. The safe
    idiom is to build the payload in Python via `json.dump(..., ensure_ascii=False)`
    and re-parse to verify before claiming done.
    → Also applies: the cron-mode runtime constraints in
    `references/read-only-analytics-cron.md` (execute_code blocked,
    pipe-to-interpreter blocked) — use `write_file` + `terminal python3`.
13. Wrote JSON via `write_file` and got a `JSONDecodeError` from the
    built-in lint, OR wrote a draft that the next cycle can't parse?
    → Read `references/write-file-json-escape-pitfall.md` for the
    specific failure modes (straight double-quotes inside string values,
    unescaped backslashes, Python expressions that look like code but
    aren't expanded by `write_file`) and the canonical fix.
- `references/daily-data-intel-scrape-pipeline-cron.md` — daily data-intel pipeline cron: scrape pg/Supabase source → classify freshness threshold → deterministic per-entity 6-gate audit sequence (blocklist filter enforced zero-tolerance) → compound approved entities into vault "Decisions / Topics" dirs + dated note template with cycle-counter increment only-after-compound-confirmed ≥1 entity. Includes the live-failure 2026-07 lesson: every scheduled pipeline must inspect actual disk state BEFORE any tool invocation regardless what compacted summary claims, and zero-payload-runs MUST log explicit entity-counts (all zero truthfully better than omitted). Cross-referenced from quick-decision-flow item 14.
- `references/provider-gated-macos-cron.md` — single-machine, single-provider, fail-closed action cron (X / Postiz / Stripe / GitHub Apps / Twilio) on behalf of one specific account, with Keychain-only credentials, live OAuth user-context identity verification, sealed-approval-capsule gate, and sanitized ProofPacket. Covers the 8-step recipe, the macOS `mkdir` lock (no GNU `flock`), the sanitize_proof_packet.py writer, the macOS Photos.app read-only bridge (incl. Mac Absolute Time epoch conversion + originals-vs-derivatives path resolution), and the voice-profile-from-posts technique with anchor-post exclusion. Cross-referenced from quick-decision-flow item 17.
    → **Read `references/daily-data-intel-scrape-pipeline-cron.md` first.** This pattern differs from the analytics-snapshot cron (#7 — read-state-no-ingest) and content-generator crons (#8/#12 — generate-not-import-external-source): a data pipeline ingests, freshness-classifies entities relative stale-vs-today cutoff, individual-gate-audits every record against blocklist/rules before persistent-store-entry, compound output-counts logged per run with explicit-zero-payload-differentiation-from-successful-run-marker (file-presence-alone not progress-signal — live failure 2026-07: identical "stuck at load" daily logs written +5 rounds without entity-counts declared so empty-runs indistinguishable successful-small-batch-looking-at-log-existence-not-content-evidence-work-done-vs-reused-template-narrative).
    → **Critical pitfall added to this umbrella from live failure in 2026-07 session: the "compaction-summary bleed" mode.** Compacted context summaries contain stale task-lists + error-transcripts earlier windows; those read reference-history NOT today's-instructions-but-agents routinely re-executed confirmed-bad terminal commands (paths-missing scripts misnamed syntax-garbled from compaction boundary loss) without verifying disk reality first. **Enforced rule:** every scheduled pipeline run must inspect actual disk state (most-recent daily log tail, verify expected executables exist AND names match reference via `ls`/search — file-not-found config-state-find-correct-file-then-run never re-attempt-wrong-name-first, payload directory contents body-read-not just metadata-stubs) **BEFORE ANY tool invocation** regardless what compacted summary claims about work pending. Zero-payload-runs MUST log explicit entity-counts (all zero truthfully better omitted making-log-presence-indistinguishable-from-successful-run) + rejected-reasons-per-gate cycle-counter-increment only-after actual-compound confirmed ≥1-entity; session ends after delivery confirms success OR verified-blocker documented evidence-backed-not guessed-without checking.

15. Comment-reply / discovery cron (LinkedIn or similar) where the inbound
    inbox is empty AND the browser auth cookie (e.g. LinkedIn `li_at`) is
    missing — the executor script (e.g. `comment_reply.py`) is reply-only
    and cannot discover comments itself, the inbox SQLite is empty, and
    the auth gate blocks the StealthBrowser?
    → Read `references/comment-reply-discovery-gate.md` for the two-layer
    diagnostic (inbox `SELECT COUNT(*)` + cookie `Has li_at` check), the
    "executor is reply-only" trap, the "Postiz is not a comment source"
    trap, the recovery protocol (manual LinkedIn login → export cookies →
    write to `linkedin_cookies.json`), the diagnostic-report output
    schema (Discovery / Inbox / Auth / Recommended action), and the
    anti-patterns (running the executor with a fake JSONL, dry-run
    reported as success, fabricated reply text, burning rate-limit
    budget on a failed auth attempt). Distinct from #10 (staged
    manifest of intended actions) — this is a diagnostic, not a
    manifest. Cross-references the cron-mode runtime constraints in
    `references/read-only-analytics-cron.md`.
16. System-health snapshot cron (e.g. Ralph department health monitor) that
    runs every 15–60m and produces a 5-check tiered status (HEALTHY /
    WARNING / CRITICAL) — disk space, rate limits, postiz queue, cron
    jobs, recent errors — and pages Mike on CRITICAL?
    → Read `references/system-health-snapshot-cron.md`. Covers the
    fixed 5-check panel rule (don't grow the panel retroactively —
    trend continuity matters), the 3-tier escalation model (WARNING
    is the silent default, CRITICAL is independent of WARNING
    thresholds, the script's tier is advisory not gating), the
    CRITICAL diagnostic-report archival pattern (separate `.json` +
    `.md` pair under `state/health/diagnostic_*.{json,md}`), the
    disk-pressure deep-dive table (the top reclaim targets on a
    typical macOS dev machine and their safety), the trend-tracking
    discipline (every cycle is a date+time-stamped file; daily
    briefing computes `tier_streak_hours`), and 7 anti-patterns
    (promoting WARNING to CRITICAL on feel, auto-pausing on CRITICAL
    without scope check, treating exit code as verdict, etc.).
    Distinct from #7 (content analytics) and #9 (fleet watchdog) —
    this is the *precondition* check, not the content or fleet layer.
    Cross-references the cron-mode runtime constraints in
    `references/read-only-analytics-cron.md`.
17. Single-machine, single-provider, fail-closed action cron that talks
    to a SaaS provider (X, Postiz, Stripe, GitHub Apps, Twilio, etc.)
    on behalf of ONE specific account, with credentials in macOS
    Keychain and a sealed-approval-capsule gate before every provider
    write — e.g. the Jacob X Account Engine cron
    (`scripts/jacob-x-cron-runner.sh`)?
    → **Read `references/provider-gated-macos-cron.md` first.**
    Distinct from #1–16: this is NOT a multi-node LLM fleet cron,
    NOT a read-only analytics cron, NOT a content-drafting cron, and
    NOT an engagement-manifest cron. It's an *action* cron — it
    can post, follow, like, comment, or publish on the provider —
    but every action is gated by (a) live OAuth user-context
    identity verification, (b) a sealed approval capsule with
    guardian + athlete/principal + media-rights consent, and (c)
    per-run content ceilings (0 DMs, 1 post, 2 replies, 3 follows,
    2 likes, 1 repost, 1 media upload). Covers the 8-step recipe
    (PATH → mkdir lock → mode dispatch → Keychain → OAuth refresh
    → live identity → per-mode commands → one action gate →
    sanitized ProofPacket), the macOS `mkdir` lock (no GNU `flock`),
    the `TZ=... date +%u` mode dispatch, the cron-line-never-passes
    `--execute` rule, the sanitize_proof_packet.py writer (replaces
    hand-crafted bash heredoc JSON), the macOS Photos.app read-only
    bridge via `sqlite3` CLI (incl. Mac Absolute Time epoch
    conversion + originals-vs-derivatives path resolution), the
    voice-profile-from-posts technique with anchor-post exclusion,
    and the AI-image exclusion policy for minor accounts. Distinct
    Distinct from #12 (drafts-only) and #10 (manifest of intended actions): this
    pattern actually executes provider writes when
    `--execute` + `--approved-action` are both passed — which the
    cron line never does.
19. Bulk **resume + delivery rewire** after an emergency freeze paused 50+ jobs, and the operator wants them all back with Telegram (or other IM) delivery — e.g. "bring up all jobs" or "wire everything to Telegram so I can monitor from the gym"?
    → Read `references/bulk-resume-delivery-rewire.md`. Covers: inventory + categorize (revenue/LinkedIn/X/infrastructure), resume in batches of 10 parallel calls, switch delivery in a second pass, keep high-frequency (≤15m) jobs local, create an autonomous work-finder loop for AFK scenarios. Pitfalls: Telegram bot may be blocked (check `last_delivery_error`), `?`-schedule jobs never fire on cron, two passes needed per job (resume then update), don't blindly resume substrate scrapers. Cross-references item 19 (freeze/unfreeze) and item 18 (jake-cron-monitor). Distinct from #20 (launchd/systemD/Docker freeze) — this is the Hermes-cron-layer bulk operational restore.
20. Fleet **emergency freeze or unfreeze** across all nodes — macOS launchd, Linux systemd, Hermes cron, user cron, Docker, QNAP containers — including breach categorization (CRITICAL/HIGH/MEDIUM/LOW), restart-chain diagnosis (drop-in overrides, systemd timers, WatchPaths, `@reboot` cron), runtime-mask-vs-permanent-mask distinction (the `--runtime` flag is ephemeral; a watchdog timer or `always-on-repair.conf` drop-in will override it within 90 seconds), the three bringup paths (A: full restore, B: clean handoff-doc build, C: selective, always-choose-C), and the restart-chain-before-unfreeze sequencing rule?
    → Read `references/fleet-freeze-unfreeze-pattern.md`. Covers the complete 8-component freeze verification checklist (parallel read-only probe), breach categorization table, the runtime-mask trap with Blackwell `always-on-repair.conf` worked example, the 6 restart-chain paths, the `--runtime mask` vs permanent disable distinction, the canonical 12 Hermes cron jobs to selectively restore, and the Path C sequencing (fix restart chains FIRST, then restore by CRITICAL→HIGH→MEDIUM severity). Distinct from #9 (fleet watchdog / monitoring layer) — this is the operational command layer.

18. Per-node **JAKE cron-health monitor** pinned to ONE specific Ollama node
    (e.g. `127.0.0.1:11434`) whose primary job is node-health + Docker watch
    + substrate processing through the local model, AND whose primary
    steady state is **idle** (most cycles find 0 fresh substrate)?
    → Read `references/jake-cron-monitor.md`. Covers the 3-mode cycle
    (idle / real-work / degraded), the idle-proof schema with
    `verdict` + `cycle_output_written_this_pass` + reused-paths fields,
    the **`escalation_age_cycles` counter** that monotonically increments
    while a persistent issue (e.g. cron asks for `ornith:35b` but node
    only has `ornith:9b`) remains un-actioned by the operator, the
    **pre-inference dual-probe** (`/v1/chat/completions` AND `/api/tags`
    AND `/api/version` — a 404 on the OpenAI-compat path does NOT mean
    the node is dead), the Docker filter-via-empty-string discipline
    (don't trust `docker ps` exit code), the 1-line orchestrator status
    file schema (`status`, `escalation_age_cycles`), and the explicit
    distinction between **idle is honest** vs **degraded is escalation**.
    Distinct from #7 (analytics) and #9 (fleet watchdog) — this is a
    *single-node cycle-monitor*, not a multi-cron inspector and not an
    external-data reader. Cross-references the cron-mode runtime
    constraints in `references/read-only-analytics-cron.md` and the
    model-missing → explicit-disclosure discipline in
    `references/cron-pin-pitfalls.md` §"Model not found — explicit
    disclosure, never silent."

## See also

- `references/lan-probe-recipe.md` — parallel probe of ollama + GBrain + Paperclip ports
- `references/cron-pin-pitfalls.md` — the 5 ways pinning fails (stale IP, wrong provider, missing model, etc.)
- `references/staged-output-idempotency.md` — stage-aware guard pattern for content-generation Doer crons whose output is audited then staged for human approval
- `references/staged-engagement-cron.md` — staged-engagement / outreach cron pattern: writes a manifest of intended actions (`actions_executed: 0`, `[STAGED]` fields) when the run is held at any of: DM-pipeline pause, Gate-D, placeholder source data, or no live session. Covers the 4-LinkedIn-scheduler topology, engagement.db column gotchas, and the `[STAGED]` discipline. Cross-referenced from quick-decision-flow item 10.
- `references/bulk-cron-spawn-from-spec.md` — bulk-create recipe for N crons from a JSON spec (CLI-then-patch idiom). The `hermes cron create` CLI does NOT accept `--model`/`--provider` flags, so each job is created via CLI then patched into `jobs.json`. Cross-referenced from quick-decision-flow item 11.
- `references/cron-mode-content-drafter.md` — agent-mode content-drafting cron pattern: 3x daily value-add drafts (e.g. LinkedIn comments), per-draft value-add taxonomy, batch labels (am/pm/eve), banned-word + voice self-audit, `gate_d_status: STAGED` discipline. Distinct from #8 (mass-variant with selection) and #10 (manifest of actions). Cross-referenced from quick-decision-flow item 12.
- `references/write-file-json-escape-pitfall.md` — the `write_file` JSON-escape failure modes (straight double-quotes inside string values, Python expressions not expanded, lint only shows first parse error) and the canonical fix (build payload in Python via `json.dump`, re-parse to verify, audit banned words *after* writing). Cross-referenced from quick-decision-flow item 13.
- `references/read-only-analytics-cron.md` — read-only metrics-snapshot cron pattern (Postiz + engagement.db + daily proof file), incl. the cron-mode runtime constraints, the **blocklist-strict-word-boundary discipline** (substring false positives on common English like 'identification' / 'threaded'), and the **honest no-op → real-work compounding transition** (read prior proof, don't widen window, don't swap models, name the delta, never duplicate).
- `references/comment-reply-discovery-gate.md` — comment-reply / discovery cron pattern: when the inbound inbox is empty AND the `li_at` auth cookie is missing, output a diagnostic report (not a fabricated reply, not a manifest). The executor script (e.g. `comment_reply.py`) is reply-only — it does NOT discover comments. Postiz is NOT a comment source. The fix is a manual LinkedIn login to refresh `li_at`. Cross-referenced from quick-decision-flow item 15.
- `references/autonomous-work-finder-loop.md` — the 7-step recipe for the recurring AFK work-finder cron: read jobs.json directly (CLI blocked by rig-knowledge-context wrapper), categorize errors by pattern matching, fix fixable ones, check GBrain IntelPackets via direct Postgres, check GTM state files, identify and execute highest-impact action (typically: consolidate unworked reply drafts into an Approval Packet), record the cycle in GBrain, report. Includes the error categorization table, fixable-vs-unfixable decision matrix, the Approval Packet pattern, and the `last_error` can be `None` pitfall.
- `references/bulk-resume-delivery-rewire.md` — bulk resume + delivery rewire after emergency freeze: categorize jobs, resume in parallel batches, switch delivery channel, keep high-frequency local, create autonomous work-finder loop. Cross-referenced from quick-decision-flow item 19.
- `references/fleet-freeze-unfreeze-pattern.md` — fleet freeze/unfreeze pattern: 8-component verification checklist, breach categorization (CRITICAL/HIGH/MEDIUM/LOW), runtime-mask trap, restart-chain enumeration, three bringup paths, Path C as default. Cross-referenced from quick-decision-flow item 19.
- `references/self-healing-monitor-cron.md` — fleet-watchdog cron pattern (M1-M5 monitors, jobs.json contract, stall-vs-cadence rule, blocklist quarantine, history-log overwrite trap). Cross-referenced from quick-decision-flow item 9.
- `references/system-health-snapshot-cron.md` — system-health snapshot cron pattern: 5-check tiered status (HEALTHY/WARNING/CRITICAL), CRITICAL diagnostic-report archival, disk-pressure deep-dive. Distinct from #7 (content analytics) and #9 (fleet watchdog) — this is the *precondition* check. Cross-referenced from quick-decision-flow item 16.
- `references/daily-hook-generation.md` (under `rig-content-quality-engine`) — daily Hook Specialist cron spec (5 patterns × 4 hooks, top-3, output schema, 5 pitfalls). Cross-referenced from quick-decision-flow item 8.
- `references/cron-notification-channel-triage.md` — notification-channel hygiene: cuts cron fleets from spam to decision-only push delivery. Classification table (DEAD/FIREHOSE/STATUS/DECISION), four cut levels (NUCLEAR/TIGHT/DEAD-LOOP ONLY/SHOW-FIRST), worked example. Cross-referenced from quick-decision-flow item 21.
- `scripts/scraper_template.py` — substrate-aware web scraper with full-body persistence
- `scripts/fleet-pinner.py` — read-and-pin tool that reads jobs.json and re-pins to verified providers