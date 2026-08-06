# Intel-Scan Infrastructure Gate

**Pattern:** Pre-flight dependency probes for information-gathering crons (GBrain crawl, pattern-library queries, Obsidian vault scan, source-repo introspection).

## The Problem

An intel-scan cron that doesn't verify its dependencies first will:
1. Attempt work against dead endpoints (GBrain HTTP probe to nonexistent ports = noise)
2. Report "zero findings" when the real answer is "infrastructure is down"
3. Produce low-confidence IntelPackets that look like genuine results rather than diagnostic alerts

## Pre-Flight Probe Sequence

Run these in order, **ABORT IF ALL CRITICAL DEPS DOWN**:

### 1. GBrain HTTP Reachability

```bash
curl -s http://localhost:<port>/health -m 2 || echo "DEAD:$?"
```

Probe ports: `54261, 3427, 9090, 54321, 3000`. If none respond, also check if the bun process exists:
```bash
pgrep -fla 'gbrain.*serve' | head -5
lsof -i :<probe_port>
```

**If bun is alive but no HTTP:** GBrain's gateway is not exposing a public endpoint. Use `gbrain query` CLI instead (`/Users/rig128gb/.bun/bin/gbrain query --tag gtm --limit 50 --format json`). If CLI also fails, report as `SERVICE_REACHABLE_NO_HTTP (evidence_score=0.3)`.

### 2. rig-knowledge CLI Existence & Path

```bash
which rig-knowledge 2>/dev/null || echo "MISSING"
ls -la /Users/rig128gb/.rig/bin/rig-knowledge* 2>/dev/null || echo "NO_BINARY"
```

Expected paths (try in order): `~/.rig/bin/rig-knowledge`, `/Users/rig128gb/.rig/bin/rig-knowledge`. The pipeline variant is `rig-knowledge-pipeline` — different tool, separate skill (`rig-knowledge-context`). If neither exists, note the gap and fall back to manual vault scan.

### 3. Obsidian Vault Accessibility

```bash
find /Users/rig128gb/Documents/JakeStudio -name "*.md" -mtime -7 2>/dev/null | head -50
```

If `find` returns empty AND Obsidian is running (`pgrep -f "Obsidian.app"`), the cron process context may not have access to JakeStudio paths. Report as `NO_FILES_IN_LAST_7D (evidence_score=0.1)`.

### 4. Source Repo / Workdir Existence

```bash
test -d <meta-harness-or-task-dir> && echo "EXISTS" || echo "MISSING"
ls </Users/rig128gb/Documents/JakeStudio/Projects/> 2>&1 | head -5
```

If the repo was deleted in a prior cleanup cycle, produce `DESTROYED_OR_MISSING (evidence_score=0.0)` and recommend path recovery or cron target update.

## IntelPacket Schema for Infra Alerts

When dependencies are down but you still want to log the scan:

| Field | Value for infra alert |
|-------|----------------------|
| source_uri | `gbrain (local bun, port unknown)` / `obsidian (vault path)` / `<meta-harness>/ODS specs` |
| change_type | `SERVICE_REACHABLE_NO_HTTP` / `NO_FILES_IN_LAST_7D` / `DESTROYED_OR_MISSING` |
| evidence_score | **0.3** for alive-but-inaccessible services; **0.1** for empty-directory scans; **0.0** for destroyed resources |
| content_hash | *(empty — no content to hash)* |

## Reporting Format

In the cron's final output:
- List all probes taken and their results
- Report total new IntelPackets count (low-confidence infra alerts only, NOT actual intel)
- Under "Recommended Fixes for Next Cron Cycle": list actionable items with specific commands to try next run
- If evidence_score < 0.5 across ALL packets → append `*Silent — no actionable IntelPackets produced this cycle.*`

## When to Return [SILENT]

Return exactly `[SILENT]` when:
- ALL dependency probes failed (nothing attempted)
- OR all produced packets have evidence_score < 0.5 AND the operator explicitly prefers silence over infra noise

Otherwise, report findings normally even if confidence is low. **The value of a LOW-confidence packet is knowing WHAT infrastructure is broken,** not what intel was missing.
