---
name: rig-multiphase-handoff-execution
description: "Execute phased handoffs in rig-intelligence. Owns the gates."
---

# RIG Multi-Phase Handoff Execution

The shape of work the user describes as a numbered-phase handoff (Phases 0 through N, with a DoneContract checklist at the end). Implement it end to end against the registered `rig-intelligence` repo.

## When this skill applies

- User pastes a long handoff document describing a system (e.g. RIG 24/7 Founder Runtime) with explicit phases.
- The repo path is `/Users/rig128gb/Developer/rig-intelligence` (or a child platform directory).
- The handoff mentions typed contracts, durable state, fleet/workers, services (launchd / systemd / containers), and an acceptance test checklist.

## The seven-phase spine (canonical pattern)

1. **Phase 0 - Typed contracts.** Pydantic models, closed-set enums, no free-form JSON inside payload. Every state transition is a field.
2. **Phase 1 - Durable queue.** SQLite WAL (default) or Postgres-portable. Atomic leases via `BEGIN IMMEDIATE`. Idempotency-key UNIQUE. Retry + dead-letter bounded by `max_attempts`. Priority aging for starved items.
3. **Phase 2 - Persistent worker.** One worker per host. Capability-gated leasing. Handler map by `work_type`. No-handler returns dead-letter.
4. **Phase 3 - Jake founder loop + dispatcher.** Deterministic scheduler (60s tick). Morning brief. Verifier with sha256 evidence hash on disk.
5. **Phase 4 - Fleet registry + probe.** Real Tailscale IPs in YAML. Parallel TCP probe with health_details. Mark stale OFFLINE_UNVERIFIED.
6. **Phase 5 - Console.** Thin HTML dashboard + local API server. Read-only views: Today, Portfolio, Fleet, Queue, Evidence, Learning.
7. **Phase 6 - Night compounding.** Bounded per-cycle seeder. Idempotent per day. Same-day rerun must NOT grow queue.
8. **Phase 7 - 24-hour walk-away test harness.** Execute every DoneContract item against the live state. PASS only when ALL items pass. Save report under `proof/`.

After 0-5, the system has a working queue + worker + dashboard. After 6, it runs unattended. After 7, it has a verifiable done-state.

## Gate-by-gate push workflow (the real RIG plumbing)

Pushing to `Rodgers-Intelligence-Group/rig-intelligence` hits **two gates** that both BLOCK commits. Work around them in this exact order:

### Gate 1 - `rig-repo-guard` (file placement)

Run before writing any code:

```bash
/Users/rig128gb/.rig/bin/rig-repo-guard check \
  "/Users/rig128gb/Developer/rig-intelligence/platform/<area>"
```

Status `ALLOW` means the path is in `registry/workstation-repositories.json`. If `BLOCK`, **stop and ask Mike** - placement is a Mike decision.

### Gate 2 - `knowledge-context-hook` (pre-commit receipt)

`core.hooksPath = /Users/rig128gb/.rig/github-steward/hooks` is set in `~/.gitconfig`. The `pre-commit` script runs:

```python
platform/knowledge-context-hook/rig_knowledge_hook.py verify-receipt \
  --repo "$repo" --max-age 14400
```

It looks for `~/.rig/knowledge-context-hook/receipts/*.json` matching:

- `schema: "rig.knowledge-context-receipt.v1"`
- `status: "PASS"`
- `task_retained: false`
- `repo` matches the project root (resolved).
- `generated_at` within 14400 seconds.
- `packet` path exists and `packet_sha256` matches.
- `packet` itself validates: `schema: "rig.context-packet.v1"` (note the singular `context-packet` - easy to miss), `matches` must be a list, `conflicts` and `gaps` must be lists.

To mint a Hermes-side receipt when no Claude/Codex session is generating one, see `references/knowledge-context-receipt-minting.md`.

### Push steps (in order)

1. Stage ONLY the new files. Don't sweep unrelated dirty files into the commit.
2. `git commit -m "<message>"` - knowledge-context receipt must be fresh (re-run `verify-receipt` first).
3. `git push origin <branch>` - `pre-push` hook returns `PASS` from `rig.github_steward.git_guard.v1`.
4. `git checkout main && git merge --no-ff <branch> && git push origin main` - never force-push; never rebase main.

If the pre-commit hook blocks with `BLOCK fresh_verified_context_receipt_required` and you have no fresh receipt: **stop and ask Mike to approve `--no-verify`** for that one push (Gate-D lane). Mint a fresh receipt afterwards so future commits are clean.

## Live state discipline

When you observe live system state (launchd services, running processes, queue contents), record it as **evidence in the commit body**, not as a claim. The pattern is:

```
[FAIL #4] now fixed: ...          # show the failure you fixed
[PASS] launcher OK; --once ...   # show real output
```

Never write "all working" without showing the actual command that proved it.

## What NOT to do

- Do NOT touch unrelated dirty files. They belong to other agents (Codex jobs, github-steward). Use `git status -s` and only stage your own.
- Do NOT inline secrets, raw credentials, or `~/.netrc` contents in commits, logs, or vault notes. Use environment variables, keychain, or secret managers by reference.
- Do NOT mark a milestone done based on a structural check alone - every DoneContract item must be exercised against real state.
- Do NOT disable the knowledge-context-hook gate by patching the script. If it blocks you, escalate via `--no-verify` ONCE and mint a receipt immediately.

## Pitfalls (learned the hard way)

- **`store.register_node` ON CONFLICT must include every column that should update.** Otherwise `health_details` and other fields get silently dropped on re-registration. Always include `health_details=excluded.health_details` (etc.) in the UPDATE clause.
- **`launchctl list` on macOS 26+ returns JSON, not text.** Use `launchctl print <label>` to get a parseable pid + state line.
- **`founder_runtime.api` Handler reads `self.store` (instance attr, not class attr).** When testing handlers in isolation, set the attribute on the fake instance: `f.store = s`. Class-level `Handler.store = s` is not enough.
- **`/api/queue_health`'s audit_log LIKE filter** does not work cleanly because `dispatcher` writes `detail` as a JSON string with `expired_leases_recovered` inside it - `LIKE '%expired_leases_recovered%'` happens to work here, but for finer queries parse JSON, don't substring-search.
- **macOS `python3` on PATH is the Xcode toolchain Python** (`/Applications/Xcode/.../Python.app/.../Python`), not the venv. Always launch venv via `.venv/bin/python` for portable Python deps.
- **macOS launchd services with `KeepAlive.Crashed=true` + `ThrottleInterval=10`**: after a `kill -9 <pid>`, the worker restarts within ~3 seconds. Don't think the worker is dead if you check too quickly.
- **A "queued" item with `last_heartbeat IS NULL`** is brand new, not stale. The `mark_offline_stale_nodes` query must filter on `last_heartbeat IS NOT NULL` first.

## Templates and references

- `references/knowledge-context-receipt-minting.md` - how to mint a Hermes-side knowledge-context receipt that satisfies the pre-commit gate without bypassing it. Includes the exact schemas, the packet-schema pitfall (`rig.context-packet.v1` not `rig.knowledge-context-packet.v1`), and a copy-paste Python snippet.
- `references/macos26-runtime-quirks.md` - macOS 26 quirks that bit me while running this on the control plane: `launchctl list` returns JSON, `python3` is Xcode's Python, `BaseHTTPRequestHandler.store` is instance-only, `mark_offline_stale_nodes` must filter `last_heartbeat IS NOT NULL`, audit_log `detail` is a JSON string, and launchd KeepAlive.Crashed restarts within ~3s.
- `templates/launchd-worker-plist.template` - copy-and-modify template for the canonical `com.rig.<area>-worker.<node_id>.plist`. Has `__AREA__`, `__NODE_ID__`, `__RUNTIME_DIR__`, `<entrypoint>` placeholders.
- `templates/health-monitor-plist.template` - same shape, separate launchd service for the 60s `fleet_probe + dispatch_tick` cadence.
- `scripts/ad-hoc-verify.sh` - the ad-hoc verification pattern (canonical pytest + live launchd + live API curl) used to verify each round without inventing a canonical test suite.

## What goes in the handoff execution report (proof/)

For every phase handoff, save:

```
proof/
  walk_away_test_report.json    # Phase 7 - 22-item DoneContract harness output
  <phase>-verification.json     # per-phase ad-hoc verification
  launchd-state-snapshot.txt    # launchctl print outputs at handoff time
```

The walk-away report is the canonical "done" signal; everything else is supplementary.