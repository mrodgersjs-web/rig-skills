# Fleet Freeze / Unfreeze Pattern

**Source:** 2026-07-24 emergency freeze verification session
**Scope:** Multi-node RIG fleet — macOS (launchd) + Linux (systemd) + Hermes cron + user cron + Docker + QNAP containers

---

## The Three Operational States

| State | Cron | Launchd/systemd | Containers | Bill |
|---|---|---|---|---|
| **FULL RUN** | All active | All loaded | All running | Max |
| **FROZEN** | All paused | All unloaded/masked | All stopped | Zero |
| **PARTIAL** | Selective | Selective | Selective | Controlled |

"Frozen" does not mean "everything off." It means **zero active work, zero outward action, zero spend**. Infrastructure services (Ollama server daemon, PostgreSQL, Docker daemon itself) can remain loaded — only the work-executing processes are paused.

---

## Freeze Verification Checklist (Phase 0 — read-only)

Run all checks in parallel. Each is read-only.

```bash
# 1. Hermes cron — all stores
hermes cron list  # count total vs active
# Verify: total = 107, active = 0 on control Mac
# Verify: total = 76, active = 0 on seoresearch profile

# 2. Fleet Hermes crons — SSH to each node
for node in rig-36gb rig-48gb rig-96gb rig-256gb blackwell; do
  ssh $node 'hermes cron list 2>/dev/null || echo "Hermes not on this node"' &
done
wait

# 3. User crontabs on fleet nodes
for node in rig-36gb rig-48gb rig-96gb rig-256gb; do
  ssh $node "crontab -l 2>/dev/null | grep -Ev '^[[:space:]]*(\$|#)'" &
done
wait

# 4. launchd on control Mac
launchctl list | awk 'NR>1 {print $3}' | rg '^(com\.rig\.|ai\.rig\.|com\.herm'

# 5. launchd on fleet (macOS nodes)
for node in rig-36gb rig-48gb; do
  ssh $node "launchctl list | awk 'NR>1 {print \$3}' | rg 'com\.rig\.'" &
done
wait

# 6. systemd on Blackwell
ssh rig-blackwell 'systemctl list-units --type=service --state=running | rg rig-'

# 7. Docker containers on all nodes
docker ps  # control Mac
for node in rig-36gb rig-48gb rig-96gb rig-256gb; do
  ssh $node 'docker ps 2>/dev/null || echo "Docker not available"' &
done
wait
# QNAP via docker context
docker --context qnap ps

# 8. Active Codex automations
rg -l '^status = "ACTIVE"' ~/.codex/automations/*/automation.toml 2>/dev/null
```

---

## Breach Categorization

| Severity | What it means | Example |
|---|---|---|
| **CRITICAL** | Actively burning RAM/GPU/spend | Blackwell GLM service consuming 73GB |
| **HIGH** | Can act outward or was missed in original freeze | Active Codex automation, loaded LobeHub LaunchAgents |
| **MEDIUM** | Local-only service, no external effect | Ollama LaunchAgent on rig-36gb |
| **LOW** | Config drift, not a live process | Stray YAML key in config.yaml |

---

## Unfreeze Sequencing (Path C — Selective, Recommended)

**Principle:** Unfreeze in severity order. Fix the restart-chain problem before unblinding the service. Restore value, not just activity.

### Step 1: Fix restart chains FIRST (prevent re-freeze)

The most common reason a frozen service re-enables itself: a **drop-in override** or **watchdog timer** restarts it after the freeze.

```bash
# Blackwell: find all drop-ins on the target service
ssh rig-blackwell 'systemctl cat rig-llama-glm52-reap50-q3-tp3.service'
# Look for: Drop-In entries in [Install] section
# If Drop-In exists: examine the drop-in file contents

# Example: always-on-repair.conf restart loop
# /etc/systemd/system/rig-llama-glm52-reap50-q3-tp3.service.d/always-on-repair.conf
# This overrides ExecStart= and adds a restart timer. Remove or disable it FIRST.

# Option A: Remove the drop-in (permanent)
ssh rig-blackwell 'sudo rm -f /etc/systemd/system/rig-llama-glm52-reap50-q3-tp3.service.d/always-on-repair.conf'

# Option B: Disable the watchdog timer that triggers the drop-in
ssh rig-blackwell 'sudo systemctl stop watchdog-timer-name'
ssh rig-blackwell 'sudo systemctl disable watchdog-timer-name'

# Reload systemd before proceeding
ssh rig-blackwell 'sudo systemctl daemon-reload'
```

### Step 2: CRITICAL — Restore the highest-value service

```bash
# Blackwell GLM service — permanent disable, not runtime mask
ssh rig-blackwell 'sudo systemctl disable --now rig-llama-glm52-reap50-q3-tp3.service'
# Verify it's stopped:
ssh rig-blackwell 'systemctl is-active rig-llama-glm52-reap50-q3-tp3.service'
# Should return: inactive

# If you want it running (not frozen):
ssh rig-blackwell 'sudo systemctl enable --now rig-llama-glm52-reap50-q3-tp3.service'
```

### Step 3: HIGH — Restore scheduled automation

```bash
# Pause Codex automation (not delete — preserves the config)
# Edit ~/.codex/automations/rig-lobehub-local-agent-monitor/automation.toml
# Change: status = "ACTIVE" → status = "PAUSED"

# Restore LobeHub LaunchAgents (macOS)
for svc in com.rig.lobehub-rig.shadow-worker com.rig.agent-os-server \
  com.rig.meta-harness.temporal-dev com.rig.keepawake \
  com.rig.meta-harness.worker com.rig.lobe-gateway \
  com.rig.meta-harness.jake-founder-heartbeat com.rig.meta-harness.jake-value-loop \
  com.rig.lobehub-rig.arr-worker; do
  launchctl bootstrap gui/$UID/$svc 2>/dev/null || true
done

# Restore user cron
crontab -e
# Uncomment the heartbeat/worker line
```

### Step 4: MEDIUM — Restore fleet Ollama

```bash
# Start Ollama LaunchAgent on each rig node
for node in rig-36gb rig-48gb; do
  ssh $node 'launchctl bootstrap gui/$UID/com.rig.ollama.server 2>/dev/null || true'
done
```

### Step 5: Restore Hermes cron selectively

**Do NOT restore all 243 crons blindly.** The handoff doc (HERMES_FULL_SYSTEM_HANDOFF.md §11) defines 12 canonical jobs:

| Job | Schedule | Restore? |
|---|---|---|
| `rig-founder-dispatch-tick` | every minute | Yes |
| `rig-signal-ingest` | every 5 minutes | Yes |
| `rig-opportunity-triage` | every 15 minutes | Yes |
| `rig-founder-hourly-review` | hourly | Yes |
| `rig-reserve-queue-refill` | hourly | Yes |
| `rig-node-health-review` | every 5 minutes | Yes |
| `rig-proof-index` | every 15 minutes | Yes |
| `rig-night-compounding` | 20:00–05:00 | Yes |
| `rig-morning-founder-brief` | 06:30 | Yes |
| `rig-daily-learning-closeout` | 23:45 | Yes |
| `rig-weekly-portfolio-review` | Monday 06:00 | Yes |
| `rig-backup-state` | daily | Yes |

**Only restore these.** Everything else was either:
- A temporary debug job
- A stale job pointing at a dead provider
- A duplicate of the canonical job

```bash
# List all paused crons
hermes cron list | rg PAUSED

# Restore selectively by name pattern
hermes cron resume <job-id>
```

---

## The Runtime Mask Trap (Blackwell-specific)

**Symptom:** `systemctl mask --runtime` appears to work, but the service restarts anyway.

**Root cause:** `--runtime` mask is ephemeral — it survives until the next `daemon-reload` or reboot. A watchdog timer or drop-in that runs `systemctl start` on a timer will un-mask it implicitly.

**The always-on-repair.conf pattern:**
```
# /etc/systemd/system/rig-llama-glm52-reap50-q3-tp3.service.d/always-on-repair.conf
[Timer]
OnBootSec=10
OnUnitActiveSec=300
Unit=rig-llama-glm52-reap50-q3-tp3.service

[Install]
WantedBy=multi-user.target
```

This creates a **timer unit** that starts the service after 10 seconds. Even if you `systemctl stop`, the timer fires and restarts it.

**Fix:** Remove the drop-in AND the associated timer unit:
```bash
# Find all units related to the service
ssh rig-blackwell 'systemctl list-units --type=unit --all | rg rig-llama'

# Remove the drop-in dir
ssh rig-blackwell 'sudo rm -rf /etc/systemd/system/rig-llama-glm52-reap50-q3-tp3.service.d/'

# Remove or disable the timer
ssh rig-blackwell 'sudo systemctl disable --now rig-llama-glm52-reap50-q3-tp3.timer 2>/dev/null || true'

# Reload
ssh rig-blackwell 'sudo systemctl daemon-reload'

# Now stop/disable the service permanently
ssh rig-blackwell 'sudo systemctl disable --now rig-llama-glm52-reap50-q3-tp3.service'
```

---

## The Restart Chain Problem

Services can re-enable through multiple restart paths:

1. **Drop-in override** (shown above) — removes `ExecStart=`, replaces with restart loop
2. **WantedBy= in [Install] section** — re-enables on boot even if you `stop`
3. **systemd.timer** — separate timer unit that starts the service on schedule
4. **launchd WatchPaths** — a launchd plist watches a file and restarts when it changes
5. **Cron @reboot** — a cron line with `@reboot` re-launches a daemon after system restart
6. **Hermes cron resume** — `hermes cron resume` re-activates a paused job

**Before unfreezing any service:** enumerate all restart paths, remove or disable the trigger, then stop the service.

---

## Proof Packet Structure for Freeze/Unfreeze

Save to `/Users/rig128gb/Desktop/proof-packet-YYYY-MM-DD/`:

```
proof-packet-YYYY-MM-DD/
  FREEZE_VERIFICATION_REPORT.md   # Phase 0: all node checks
  BREACH_MANIFEST.md              # Categorized breach list
  RECOVERY_ACTIONS.md             # What was done, in order
  PROOF_TIMESTAMP.txt             # `date -Iseconds`
```

The proof packet proves the freeze was verified and the un-freeze was sequenced correctly.

---

## The Three Bringup Paths

| Path | What | Cost | When |
|---|---|---|---|
| **A — Full restore** | Flip everything back on | Same maintenance burden as before | When you want the old system back, unchanged |
| **B — Clean build** | Build the handoff doc system (Hermes cron, PostgreSQL queue, node workers) | Build time | When you want a durable, maintainable system long-term |
| **C — Selective** | Restore only what's valuable + fix known problems | Least | Default choice — always start here |

**Path C is the default.** Path B is a separate project. Path A is "undo the last 2 weeks."

---

## Quick Decision: Should I Unfreeze This?

Ask per-service:

1. **Does this burn money or GPU right now?** → If CRITICAL burn: fix the restart chain, then enable or leave disabled.
2. **Does this produce value when running?** → If yes and restart chain is fixed: enable.
3. **Was this caught in the original freeze sweep?** → If no: audit before re-enabling (it was missed for a reason).
4. **Is there a restart chain that will re-enable it after I stop it?** → Always check drop-ins, timers, and WatchPaths before assuming "stop = stopped."
