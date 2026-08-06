# Staged-Output Idempotency — Content-Generation Cron Guard

The Doer / Checker / Validator pattern (see SKILL.md §3) is built on the assumption that the Doer cron produces a **durable artifact** and never re-touches it. Content-generation crons (LinkedIn drafts, blog posts, weekly briefs, email sequences) violate that assumption the moment a second run lands on the same date: the new run overwrites the staged, audited output, the Checker's prior verdict becomes invalid, and any human review state is lost.

This file is the recipe for making those Doer crons idempotent across re-runs.

## When this matters

- The Doer writes a date-keyed file like `proof/daily/drafts_{YYYY-MM-DD}.json`
- A Checker cron (`quality-auditor`) reads the file and writes a separate `audit_{YYYY-MM-DD}.json`
- A Validator cron (or the human) reads both before publishing
- A second invocation of the Doer can come from: cron schedule drift, manual retry, an "I wonder if today's run finished" trigger, or a transient error that cleared and rescheduled

If the file is the only signal, the second run looks identical to a first run from the orchestrator's perspective. That's the trap.

## Stage-aware guard

Read the file first. Decide what to do based on what's already there.

```python
from pathlib import Path
import json, os, sys, fcntl
from datetime import date

DATE = date.today().isoformat()
PROOF_DIR = Path("~/.hermes/jake/ralf-department/proof/daily").expanduser()
DRAFTS = PROOF_DIR / f"drafts_{DATE}.json"
AUDIT  = PROOF_DIR / f"audit_{DATE}.json"

# --- Process lock so cron schedule + manual retry can't both run ---
LOCK = Path(f"/tmp/lead-writer.{DATE}.lock")
lock_fd = open(LOCK, "w")
try:
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    print("[SILENT]")
    sys.exit(0)

try:
    # --- Stage-aware guard ---
    if DRAFTS.exists():
        data = json.loads(DRAFTS.read_text())
        has_drafts = bool(data.get("drafts"))
        has_via    = bool(data.get("via_selection"))
        has_audit  = AUDIT.exists()

        if has_drafts and has_via and has_audit:
            # Work is staged AND audited. Don't touch it.
            print("[SILENT]")
            sys.exit(0)

        if has_drafts and has_via and not has_audit:
            # Stage 1 done, awaiting Checker. Don't re-run divergent phase.
            # (If you have an idempotent VIA-only resume, call it here.)
            print("[SILENT]")
            sys.exit(0)

        if has_drafts and not has_via:
            # Divergent phase done, selection phase stalled. Resume selection.
            run_via_selection(data)
            DRAFTS.write_text(json.dumps(data, indent=2))
            print(f"[RESUMED] selection for {DATE}")
            sys.exit(0)

    # --- Normal path: file missing or stage 0 ---
    data = generate_chaos_drafts()   # 25 drafts across 5 topics
    data["via_selection"] = run_via_selection(data)
    DRAFTS.parent.mkdir(parents=True, exist_ok=True)
    DRAFTS.write_text(json.dumps(data, indent=2))
    print(f"[DONE] {DATE}: 25 drafts + 3 selected")

finally:
    fcntl.flock(lock_fd, fcntl.LOCK_UN)
    lock_fd.close()
    LOCK.unlink(missing_ok=True)
```

## Decision table

| DRAFTS file | Audit file | Action |
|---|---|---|
| missing | missing | Generate (normal path) |
| exists, no `via_selection` | missing | Resume selection only — don't re-run CHAOS |
| exists, has `via_selection` | missing | Return `[SILENT]` — Checker is owed a turn |
| exists, has `via_selection` | exists | Return `[SILENT]` — staged, audited, ready for human |
| exists, has `via_selection`, **and** Mike approval present | exists | Return `[SILENT]` — shipped |
| New date | n/a | Different file. Always generate. |

## Why the process lock matters

Even with the stage guard, two invocations can race:

1. Schedule fires at 06:00:00 — `flock` acquired, file read, stage=missing, CHAOS starts
2. Mike's dashboard reload triggers a manual retry at 06:00:01 — `flock` would block here, so it returns `[SILENT]`
3. Original invocation writes the file and releases the lock
4. Manual retry's `[SILENT]` is the right answer; the file is fresh

Without the lock, both invocations read `stage=missing`, both run CHAOS, and they race on the final `write_text` — corrupting the file. The lock makes "[SILENT]" deterministic.

## What the cron should emit

`[SILENT]` is the right output when the work is staged. It tells the orchestrator: "I ran, but there's nothing to deliver." If the cron emits a normal report on a re-run, the orchestrator may treat it as a fresh cycle and break downstream state (analytics, scheduling, "what ran today" pages).

If the cron errors during a re-run, the orchestrator should not retry — the file is staged and the Checker's verdict is still valid. Mark the error as a stale-eval and move on.

## Worked example: lead-writer cron, 2026-07-06

A 6am cron fires `lead-writer` to produce 25 LinkedIn drafts. The 6am run generates 25 drafts + runs VIA selection, writes `drafts_2026-07-06.json`. At 10:30am the `quality-auditor` cron reads it, writes `audit_2026-07-06.json` with 5/25 passing gates.

At 11am a backfill job (testing a new prompt) re-invokes the lead-writer cron manually. Without the guard it would:
- Overwrite `drafts_2026-07-06.json` with a different 25 drafts
- Make the prior `audit_2026-07-06.json` point at the wrong drafts
- Lose any human partial-review state

With the guard the manual invocation reads the file, sees `has_drafts + has_via + has_audit`, and returns `[SILENT]`. The audit chain survives.

## Anti-patterns to avoid

- **Appending drafts to a single growing file**: harder to audit, harder to date-key, and the Checker has to re-grade every cycle. Use date-keyed immutable files instead.
- **Writing to a `latest.json` mirror**: you lose the date-keying benefit and the cron has no way to detect "did today's run already happen?"
- **Trusting cron `last_status` to mean "produced new work"**: the scheduler counts a no-op re-run as success. Only the file presence + audit chain tells you what's real.
- **Deleting the file on error to "force a re-run"**: the audit chain breaks and the Checker crashes on the next cycle. Leave the file alone, log the error, escalate.

## See also

- SKILL.md §3 — Doer / Checker / Validator separation
- SKILL.md §4 — state files, not live dashboards (same logic: disk is truth, transient state is not)
- `references/cron-pin-pitfalls.md` §4 — stale `last_status` after a fix, related staleness pattern
