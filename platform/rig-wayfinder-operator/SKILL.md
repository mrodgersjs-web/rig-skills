---
name: rig-wayfinder-operator
description: Run wayfinder maps in RIG. Override, parallel sessions.
category: rig
source_repo: local
version: 1.0.0
---

# rig-wayfinder-operator

Mike's operator overlay for the user-installed Matt Pocock wayfinder skill. The base skill defines the *rules* (one ticket per session, chart then resolve, etc.). This skill encodes the *RIG-specific operational patterns* that emerged from running real maps against real infrastructure.

**Do not modify `matt-pocock-wayfinder`** — it's user-installed and protected. This skill extends it; the base skill governs.

## Triggers

Load this skill when Mike says any of:
- "wayfinder", "chart a map", "let's plan this out", "open a ticket", "claim ticket"
- "where are we on the map?", "frontier", "fog of war", "decisions so far"
- "do another ticket in this session", "run tickets in parallel"
- "complete ticket N", "close the map"

## The 5 RIG-Specific Patterns

### 1. Local-markdown tracker (default, not GitHub issues)

When Mike says "chart a map" or "let's plan this out" with no other context, the map lives as a **local markdown file**, not GitHub issues. Reasoning:

- Survives across all 3 Hermes profiles (default/work/play)
- Git-diffable for audit
- No dependency on GBrain/Postgres being up
- Co-locates with the artifact (e.g., `WAYFINDER_MAP.md` next to the council pack in `$HOME/buzz/examples/council-core/`)
- The user can `cat` it from any terminal session

Map file template (proven in 2026-07-30 Council Core map):

```markdown
# Wayfinder Map — <short name>

## Destination
<one or two lines: what reaching the end looks like>

## Notes
<domain; skills every session should consult; standing preferences; RIG context>

## Decisions so far
- [<ticket name>](<artifact-link>) — <one-line gist of the answer>

## Not yet specified
<fog of war: in-scope but not sharp enough to ticket>

## Out of scope
<ruled-out work, with reasons>

## Open tickets
- **<Ticket N>** — <Question>. (type: research/prototype/grilling/task, AFK/HITL)
```

**Why this template works**: the `Open tickets` section duplicates what's in the tracker — but it's the local view a session sees without querying. Tickets are also tracked as live child issues elsewhere (or as markdown sub-files). For local-only maps, the `Open tickets` section IS the tracker.

### 2. Operator-override protocol for the one-ticket-per-session rule

The base wayfinder rule is hard: **never resolve more than one ticket per session.** Mike tested this in the 2026-07-30 Council Core map by asking me to do Ticket 4 after Tickets 1 and 2. My correct response was:

1. State the rule verbatim from the skill
2. Explain *why* it exists (decision hygiene, compaction safety, auditability, parallelism)
3. Offer **three paths**: do it here (override), spawn fresh session (correct), or abandon wayfinder framing (escape hatch)
4. Mike chose spawn-fresh. That's the most common resolution.

**Protocol when Mike asks to do another ticket in the same session:**

```
Acknowledge the request. State the rule. Explain the actual reasoning (not "because the
skill says so"). Give Mike three options:
  A) "Override wayfinder" — break the discipline for this session, do it here
  B) "New session" — spawn Hermes/Codex/Claude in a new tab, hand it the map file
  C) "Skip wayfinder" — treat the new task as a normal coding task, no map framing

Wait for explicit choice. Do not auto-override.
```

**When override IS appropriate:**
- Mike explicitly says "override wayfinder" or "do it here anyway"
- The ticket is small enough that decision quality won't degrade
- It's the last ticket on the map and the discipline argument weakens
- Mike has just explained reasoning and chosen override despite understanding it

**When override is NOT appropriate:**
- Mike hasn't been told the rule yet (educate first)
- Multiple tickets remain on the frontier (auditability breaks)
- Memory pressure is already >85% (compaction risk)
- Mike is frustrated — overriding into poor work makes it worse

### 3. Parallel session pattern (the "many sessions, one map" doctrine)

When Mike says "complete both tickets in parallel using agent swarms" — the correct response is **NOT** to spawn a swarm. It's:

> "Wayfinder is one-ticket-per-session. To run tickets in parallel, *you* (the human) spawn separate Hermes/Codex/Claude sessions — one per ticket — each editing the same map file. The map handles concurrent appends cleanly because each session adds a different `Decisions so far` line."

Why this works:
- Each session has full context for its ticket (no compaction loss)
- The map is the source of truth — append-only `Decisions so far` is conflict-free
- Mike can have 3 tabs open at once, one per ticket
- Audit trail: `git diff WAYFINDER_MAP.md` shows each session's contribution

Anti-pattern: don't dispatch a single subagent to "handle the map." Subagents can't carry session state the way Mike's primary sessions can.

### 4. bash --noprofile --norc escape for long subprocess work

When launching long-running scripts (Ollama calls, council runs, anything >2 minutes) from `terminal(background=true)`, the **Jake hook in `~/.bashrc` intercepts every shell** and prints:

```
Jake RIG Agent online.
Mode: execution body. Hermes conducts. V decides. Mike approves external action.
...
Mission clock started. State your packet.
```

This banner corrupts the actual command's output and makes automation fragile. Fix: launch with `bash --noprofile --norc -c "..."`:

```bash
bash --noprofile --norc -c "cd /path && python3 council_run.py input.md > output.txt 2>&1; echo DONE_\$?"
```

Verified working 2026-07-30 with Ollama + council_run.py + 4-minute 5-persona run. The script ran cleanly; the Jake banner appeared only in `process` tool output (cosmetic, not contaminating).

**Alternative for execute_code sandbox**: subprocess.Popen with `start_new_session=True` does NOT escape the sandbox — the sandbox kills all child processes when execute_code exits. Use the terminal background tool with bash --noprofile --norc instead.

### 5. Ollama Qwen3 thinking-model token budget

The `rig-128gb-qwen36` model (and `qwen3.6:35b-a3b`) are **thinking models**. They emit a `thinking` field containing chain-of-thought tokens BEFORE the actual response. The Ollama `/api/generate` API has a single `num_predict` budget that covers BOTH thinking and response.

**Symptom of wrong budget**: `eval_count` reaches `num_predict`, `done_reason: "length"`, response is empty, all 4000 tokens went to `thinking`.

**Working budget** (verified 2026-07-30):

| Use case | num_predict | Actual thinking | Actual response |
|----------|-------------|-----------------|-----------------|
| "Say OK" sanity test | 100 | ~120c thinking | (empty — too small) |
| Short persona review (1-2k input) | 2000 | 8-12k thinking | (empty — too small) |
| **Real persona review (5k input)** | **4000** | **8-12k thinking** | **2.5-7k response** |
| Long PRD review (5k+ input) | 4000-6000 | 12-16k thinking | 3-7k response |

**Default to `num_predict=4000`** in any Ollama-driven persona/pipeline. Anything less will silently produce empty responses.

**Pitfall in council_run.py type scripts**: hardcoded `max_tokens=600` at the call site will override any function default. Always grep for both `def ... max_tokens=` AND `... max_tokens=N` at call sites when debugging.

**Regex pattern for verdict extraction**: persona reports often use bold markdown like `**VERDICT:**` or backtick code like `` `request_changes` ``. The regex must tolerate both:

```python
re.search(r'\*{0,2}VERDICT:\*{0,2}\s*`?(\w+(?:_\w+)*)`?', text, re.IGNORECASE)
```

## Invocation Quick Reference

| Mike says | Action |
|-----------|--------|
| "let's plan this out" / "chart a map" | Load `matt-pocock-wayfinder` skill, run grilling for destination, create local markdown map |
| "complete ticket N" | Read map, claim ticket N, resolve it, append to `Decisions so far`, close it |
| "do another ticket in this session" | Apply operator-override protocol (3 options above) |
| "run tickets in parallel" | Explain parallel session pattern, ask Mike to spawn separate sessions |
| "where are we on the map?" | Read `WAYFINDER_MAP.md` Decisions + Open tickets, summarize frontier |
| "close the map" / "we're done" | Verify destination criteria met, archive map, summarize decisions |
| Mike wants Ollama/council output from a script | Use `bash --noprofile --norc -c "..."` for terminal background |

## Anti-Patterns (Captured from Real Sessions)

### AP-WAYFINDER-SWARM-REQUEST
**Failure**: Mike asks to "do both tickets in parallel using agent swarms." You spawn a swarm of subagents.
**Why it breaks**: Wayfinder is one-ticket-per-session. Subagents can't carry session state. Each subagent's reasoning is independent, destroying the "map accumulates coherent decisions" property.
**Fix**: Explain the parallel session pattern. Each ticket gets its own primary Hermes/Codex/Claude session. The map file is the coordination layer, not a swarm dispatcher.

### AP-COUNCIL-RUN-EMPTY-RESPONSE
**Failure**: Council run script reports `0c` for all 5 personas in 8 seconds each.
**Why it happens**: Hardcoded `max_tokens=600` (or any value <2000) gets overridden by Qwen3 thinking model, leaving 0 tokens for actual response.
**Fix**: Set `num_predict=4000` at both the function default AND the call site. Verify with a single-persona sanity call before launching the full council.

### AP-JAKE-BANNER-IN-CRON-OUTPUT
**Failure**: Output file from `terminal(background=true)` starts with "Jake RIG Agent online..." and includes "Mission clock started. State your packet."
**Why it happens**: `~/.bashrc` sources `~/.rig/shell/rig-agent-access.sh` and `~/.jake/goal-loop-startup.sh` on every interactive bash spawn.
**Fix**: `bash --noprofile --norc -c "..."` strips the Jake init scripts while preserving `PATH` and basic env. Verified clean Ollama + council_run output with this pattern.

### AP-OVERRIDE-WAYFINDER-WITHOUT-ASKING
**Failure**: You skip the operator-override protocol and just do the next ticket because Mike asked.
**Why it breaks**: Mike may not have understood the rule. If you override without explaining, you inherit blame for any quality degradation in the second ticket.
**Fix**: Always run the protocol — state the rule, explain reasoning, give 3 options, wait for explicit choice. If Mike overrides, log it in the map's `## Notes`.

## Verification: When This Skill Is Loaded

If you're about to run wayfinder in RIG context, confirm:

1. **Map file exists** at a sensible co-located path (e.g., `<artifact-dir>/WAYFINDER_MAP.md`)
2. **Map file has all 5 sections** (Destination, Notes, Decisions, Not yet specified, Out of scope)
3. **Tickets have explicit type + HITL/AFK classification** in their description
4. **Prior session's decisions are logged** as one-line entries with artifact links
5. **Frontier is small** (≤5 open tickets) — anything more means the map needs chunking

If any of these fail, fix the map before claiming a ticket. Bad maps produce bad decisions.

## Related Skills

- `matt-pocock-wayfinder` — the base skill, rules and ceremony. Read-only from this skill's perspective.
- `rig-agent-swarms` — for actual parallel execution (NOT for wayfinder ticket dispatch)
- `rig-goal-design` / `command-registry` — for designing new goal loops (different design surface from running wayfinder)
- `rig-doctrine-reality-audit` — useful when a wayfinder map's destination drifts from disk reality

## Real-World Reference

- **2026-07-30 Council Core map** at `$HOME/buzz/examples/council-core/WAYFINDER_MAP.md` — produced Ticket 2 (Council Core pack), Ticket 1 (map setup), and proved the operator-override protocol when Mike asked for Ticket 4 in the same session.
