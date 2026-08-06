# Self-Healing Monitor Cron — Fleet Watchdog Pattern

Distinct from the Doer/Checker/Validator content-generation pattern and the read-only analytics pattern. This is the pattern for a **fleet-watchdog cron** that periodically inspects other crons, writes state-file alerts (no `send_message`, no public action), and is responsible for catching cron drift / stalls / proof-writer failures / blocklist regressions before they cascade.

## When this fits

- A scheduled cron fires every 15-60 minutes and asks "are the other crons healthy?"
- The output is a master `36h-goal-proof.json` (or sprint-equivalent) + N small per-finding alert files
- The monitor is **read-only on crons** — it writes alerts and a sprint proof, never restarts crons, never modifies schedules
- Operator (Mike) reviews the master proof and decides what to act on

Examples: 36h sprint monitor, weekly fleet audit, 1000x cycle drift watch, pre-deploy cron health check.

## The architecture: 5 monitors → 1 master proof

```
M1 Cron Health      → per-cron .alert files  (stalls > 90min, errors)
M2 Provider Drift   → m2-drift-detected.log  (model/provider mismatch)
M3 Blocklist Watch  → m3-blocklist-incident.log + quarantine dir (CRITICAL severity)
M4 Proof Writer     → per-cron .alert files  (proof file missing/stale > 4h)
M5 Outcome Tracker  → m5-outcomes-cycle-N.json (O1/O2/O4/O5/O6 counts)
                   → master sprint proof:   36h-goal-proof.json
                   → per-cycle log:         monitor-cycle-{ts}.log
                   → rolling history:       monitor-history.log (append-only)
```

Each monitor writes its own alert/incident file. The master proof rolls them up. The per-cycle log is human-readable. The history log is one-line-per-cycle, used by the orchestrator for trend detection.

## Cron state inspection — the jobs.json contract

**`hermes cron list` does NOT surface `provider`, `model`, `prompt`, `origin`, or `last_error` fields.** It only shows: id, name, schedule, repeat count, next_run_at, last_run_at, last_status. The text format is bordered boxes. `--format json` is rejected with `unrecognized arguments`.

**`hermes cron status <id>` does not exist** — positional IDs raise `unrecognized arguments`.

**The source of truth is `/Users/rig128gb/.hermes/cron/jobs.json`** — every cron job is a dict with the full schema:

```json
{
  "id": "4ca73ece55fa",
  "name": "DARIUS — Daily GTM Lead Engine (1000x/4h)",
  "schedule": "every 240m",
  "repeat": "5/13",
  "next_run_at": "2026-07-06T15:34:16.670698-06:00",
  "last_run_at": "2026-07-06T11:34:16.670698-06:00",
  "last_status": "ok",
  "last_error": null,
  "provider": "rig-96gb-lan",
  "model": "rig-96gb-reasoner:latest",
  "prompt": "You are Jake PAI running ...",
  "origin": {"platform": "telegram", "chat_id": "8634072195", "user_id": "8634072195"},
  "paused_at": null,
  "no_agent": false,
  ...
}
```

Read it directly for M2 drift detection:

```bash
# Get all cron states for a fleet
python3 /tmp/inspect_jobs.py --ids 4ca73ece55fa,b6cba84bd3f3,... > /tmp/cron_states.json
```

```python
# /tmp/inspect_jobs.py
import json, sys
from pathlib import Path
ids = set(sys.argv[1].split(",")) if "--ids" in sys.argv else None
data = json.loads(Path("/Users/rig128gb/.hermes/cron/jobs.json").read_text())
out = []
for j in data.get("jobs", []):
    if ids and j.get("id") not in ids:
        continue
    out.append({
        "id": j.get("id"),
        "name": j.get("name"),
        "last_run_at": j.get("last_run_at"),
        "last_status": j.get("last_status"),
        "last_error": j.get("last_error"),
        "next_run_at": j.get("next_run_at"),
        "provider": j.get("provider"),
        "model": j.get("model"),
    })
print(json.dumps(out, indent=2))
```

**Pitfall:** in some sessions the outer dict has `"jobs"` key, in others it's a top-level array. Defensive: `data.get("jobs", data if isinstance(data, list) else [])`.

## The age computation

Cycle interval needs `now - last_run_at` in minutes. Tirith blocks `cat jobs.json | python3`, and `execute_code` is blocked in cron mode, so:

```bash
# Pattern: write python script via write_file, run via terminal
python3 /tmp/inspect_jobs.py --ids <id1,id2> > /tmp/cron_states.json
# Then read /tmp/cron_states.json with read_file
# Compute ages in the monitor's main code (also write-only)
```

The monitor's main loop uses `datetime.fromisoformat()` to compute age in minutes from the cron state. Always include both `last_run_at` (string) and `age_min` (number) in alert files so the operator can audit.

## Stall vs cadence — the rule that matters

**A cron is NOT a stall just because `last_run_at` is old.** A 240m-cadence cron firing every 4 hours will always look ~240m old between firings. The real stall signal is:

```
stall = (now - last_run_at) > threshold_min AND state == "scheduled" AND last_status != "ok_in_flight"
```

Use a **separate threshold from cadence**:

| Cadence (m) | Stall threshold (m) | Note |
|---|---|---|
| 15 | 25 | Tight — covers 1 missed cycle + slack |
| 30 | 50 | Covers 1 missed cycle + slack |
| 60 | 90 | Standard — covers 1 missed cycle |
| 240 | 270 | Just over 1 cadence; "missed 1 cycle" alert |
| 1440 | 1500 | Just over 1 cadence |

Set the threshold ≈ 1.1× cadence. If `last_status` is `"error"`, the cron is a stall regardless of age — escalate separately.

**Always include cadence_min in the alert file** so the operator can interpret age correctly. From the cycle-55/56 fleet audit: 4 of 5 crons showed ages 100-165m on a 240m cadence — these were NORMAL scheduler behavior, not stalls. The alert files say "within cadence" to make this explicit.

## Blocklist quarantine — never auto-fix

The M3 monitor must NOT auto-fix a blocklist hit (e.g. HED, IdeaWake). The rule is:

```
On hit:
  1. MOVE file from outbound/staged/{date}/{slug}.json → quarantine dir
  2. APPEND to m3-blocklist-incident.log
  3. SEVERITY = HIGH
  4. NEVER touch the source file's contents
  5. NEVER re-send or re-stage the contact
  6. Log time, file, pattern, slug. Operator decides next action.
```

If 3+ incidents fire in 60min: log CRITICAL, do not halt. The user decides whether to extend window, halt, or stop.

## Proof-writer freshness

For each cron that has an associated proof file (e.g. `gtm-engine-proof.json`):

- If file missing: STALE
- If file exists: check mtime. `stale = age_min > threshold_min` (default 240m = 4h)
- If cron is scheduled AND proof is stale: alert

The "missing file" case often indicates the cron is running but not writing proof — a silent regression. The "stale file" case indicates the cron ran but produced no new content.

**Don't conflate missing proof with cron failure.** A cron with `last_status=ok` and missing proof is a "writer regression" — the cron runs but the proof-write step has been removed or broken. Different alert language.

## Outcome path probing (M5)

The cron prompt usually names a path like `out/ads/proof-packet.json` but the canonical filesystem path may differ. Don't hard-code — probe multiple candidate paths:

```python
import os, glob
candidates = [
    "/Users/rig128gb/Developer/rig-gtm-studio-v2/out/ads",
    "/Users/rig128gb/Developer/rig-os-agency/out/ads",
    "/Users/rig128gb/out/ads",
]
exists = [c for c in candidates if os.path.isdir(c)]
```

For O1 (staged outbound), scan date-prefixed subdirectories:

```python
import glob
for date_dir in glob.glob("/path/outbound/staged/2026-07-*"):
    files = glob.glob(f"{date_dir}/*.json")
    # includes INDEX.json in count if present
```

For O2 (calls), `outbound/calls/{date}.json` files may not exist as directories at all — empty count = 0, no fallback.

For O5 (doctor), the JSON includes a `fail_count` and per-gate `status` — capture the same fingerprint each cycle so trend detection works.

For O6 (atlas), just `os.path.exists()` + `os.path.getsize()` + `os.path.getmtime()` — three numbers, easy to roll up.

## The history-log overwrite trap

**The rolling history log (`monitor-history.log`) is one-line-per-cycle and is appended.** Using `write_file` to "update" it destroys the tail you didn't observe. Always use `terminal` with `cat >> file` to append, never `write_file` on a log you're appending to.

```bash
echo "$(date +%H:%M) cycle=${CYCLE} monitor=ok o1=${O1} o2=${O2} ..." >> /Users/rig128gb/.rig/state/monitor-history.log
```

If you accidentally overwrite (e.g. read with offset/limit, then write_file the wrong contents): restore from a known-good cycle log (every cycle writes a full `monitor-cycle-{ts}.log`), reconstruct the line for the prior cycle, append a `# NOTE: tail lost on cycle-N overwrite` comment, then continue.

**Always `cat` the file before any destructive write operation** — if it grows unexpectedly, stop and use append-only tooling.

## Per-monitor runtime constraints (cron mode)

Same as `read-only-analytics-cron.md`:

1. `execute_code` is BLOCKED — use `write_file` + `terminal python3 /tmp/script.py`
2. Pipe-to-interpreter is BLOCKED by Tirith — redirect to temp file, then run a separate `python3 /tmp/script.py`
3. No `send_message` — your final response is auto-delivered to the cron destination
4. No `[SILENT]` mixed with content — either report or `[SILENT]` alone
5. No user is present to approve Gate-D — pre-decide your auto-fix policy per monitor

**Auto-fix policy by monitor:**

| Monitor | Auto-fix allowed | Reason |
|---|---|---|
| M1 Stall | NO — alert only | Restarting is scheduler's job; monitor doesn't own cron lifecycle |
| M2 Drift | YES only if reversible + scoped | Provider/model string swap; irreversible if it breaks the fleet |
| M3 Blocklist | NEVER auto-fix | Quarantine + log; operator decides |
| M4 Proof writer | NO — alert only | Writer regression is a prompt issue; needs human review |
| M5 Outcome | NO | Read-only observation |

**M2 is the only monitor with auto-fix authority, and only for reversible provider/model drift on crons where the expected provider is `minimax/MiniMax-M3`.** When the operator has pinned to `rig-96gb-lan` intentionally (as in the 36h-sprint fleet), M2 reports the drift but does NOT auto-rewire. Document the operator-pin reason in the alert file.

## The window check (sprint monitors only)

Sprint monitors (36h goal, 12h checkpoint, etc.) have an expiry. Before declaring "monitor=ok", check:

```python
from datetime import datetime
now = datetime.fromisoformat("2026-07-06T14:01:15-06:00")
expires = datetime.fromisoformat("2026-07-07T04:00:00-06:00")
if now >= expires:
    # Window expired — trigger closeout
    # 1. Write handoff doc: JULY-36H-HANDOFF-2026-07-07.md
    # 2. Set goal status to CLOSED in active-goal.json
    # 3. Return report; next cron cycle may not run
    pass
```

If the window has hours remaining (e.g. 13.98h), include `hours_remaining` in the master proof so the operator sees "we still have time" at a glance.

## Verification before claiming "monitor=ok"

After writing the master proof, re-read it and check:

- [ ] All M1-M5 monitors ran (no `[SKIPPED]` placeholders in m_stalls / m_drift / m_incidents)
- [ ] `cycle_notes_summary` is a single paragraph that names all counts
- [ ] Per-cron alert files exist for every stall and every proof-stale case
- [ ] `previous_cycle` reference is the immediately prior cycle (not N-2)
- [ ] `window.remaining_h` matches the time-of-cycle calculation
- [ ] `delta_notes` compares the prior cycle and the current cycle on every metric
- [ ] `g1_g7_status` line is present and gates are individually verified
- [ ] The history log was appended (not overwritten)

## Worked example: 36h sprint monitor, 15m cadence

A scheduled cron every 15 minutes that monitors 5 sprint crons + 6 outcomes + 1 blocklist:

1. Read `/Users/rig128gb/.rig/state/36h-goal-active.yaml` and `/Users/rig128gb/.hermes/jake/jake-active-goal-2026-07-05.json` to get active window + cron IDs + outcomes
2. Read `/Users/rig128gb/.hermes/cron/jobs.json` for each of 5 cron IDs → get last_run_at, last_status, provider, model
3. Read `/Users/rig128gb/.rig/state/36h-goal-proof.json` for previous cycle (cycle N-1)
4. Compute ages at `now`
5. M1: write per-cron stall or clear alert files
6. M2: write m2-drift-detected.log (or fixed log if auto-fix applied)
7. M3: scan `outbound/staged/2026-07-*/` for blocklist patterns; on hit, quarantine + log
8. M4: stat each of 5 proof files; write per-cron .alert if stale
9. M5: compute O1 (file count), O2 (calls count), O4 (path probe), O5 (doctor), O6 (atlas exists)
10. Write master `36h-goal-proof.json`
11. Write human-readable `monitor-cycle-{ts}.log`
12. Append one line to `monitor-history.log`
13. Window check: if `now >= expires_at`, trigger closeout
14. Final response: report findings (counts, verdict, window remaining, operator action items)

The full output is on disk; the final response is the human-readable summary.

## Anti-patterns

- **Auto-restarting stalled crons.** The scheduler owns cron lifecycle. The monitor observes and alerts. Don't reach into `jobs.json` to flip `last_status` from "error" to "ok" without operator approval — that's evidence tampering.
- **Auto-fixing M2 drift when the operator has pinned.** If the sprint is on a fleet like `rig-96gb-lan` per `fleet_nodes_used`, the drift to `minimax/MiniMax-M3` is intentional. Document the pin reason; don't auto-rewire.
- **Treating proof-missing as cron-failed.** A cron can run perfectly and not write proof. Different alert.
- **Hard-coding paths in O4/O5 probes.** Multi-path probe; don't trust the cron prompt's claim about file location.
- **Overwriting the history log.** Append only. If you accidentally overwrite, restore from the cycle log and add a `# NOTE` comment.
- **Combining `[SILENT]` with report content.** Pick one. The orchestrator routes on the literal `[SILENT]` token.
- **Returning a 5-paragraph summary when the cycle was stable.** 1 short paragraph + a table of counts. The operator reads 12 of these a day.

## See also

- `read-only-analytics-cron.md` — cron-mode runtime constraints (execute_code blocked, pipe-to-interpreter blocked, no user present)
- `cron-pin-pitfalls.md` — for provider/model drift fixes when auto-fix IS scoped
- `staged-output-idempotency.md` — for the cron-output protection pattern (different problem class)
- `lan-probe-recipe.md` — for fleet health probing
- SKILL.md §4 — "state files, not live dashboards" (every alert file IS a state file)