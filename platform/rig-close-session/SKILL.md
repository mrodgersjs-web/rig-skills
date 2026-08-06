---
name: rig-close-session
description: "Auto-session memory: encodes session knowledge into repo-committed files so the next session starts informed. Updates AGENTS.md, learnings, tech debt, and handover files. Can run on-demand or auto-trigger on session close. Use at the end of every meaningful coding/agent session."
tags: [rig, session-memory, handover, continuity, agents-md]
source: "The Ideal Agentic Setup — Yaron Been (https://www.youtube.com/watch?v=NRrj6qEymBY)"
extracted: "2026-07-22"
---

# Close Session

<objective>
Encode session knowledge into repo-committed files so the next session starts informed.
AI agents start each session with zero context — this skill bridges that gap by
writing structured memory artifacts that persist across sessions.
</objective>

<when_to_use>
- At the end of every meaningful coding session
- Before switching to a different project
- When context is getting long and you want to preserve learnings
- Auto-trigger: can be wired to fire when a terminal session closes
</when_to_use>

<prerequisites>
- A project directory with git initialized
- An active or recent session with meaningful work done
</prerequisites>

<process>
## Steps

1. **Update AGENTS.md** (purpose + architecture + decisions)
   ```markdown
   # Project: {name}

   ## Purpose
   {What this project does — 2-3 sentences}

   ## Architecture
   {Key components, data flow, tech stack}

   ## Decisions Log
   | Date | Decision | Rationale |
   |------|----------|-----------|
   | {date} | {what was decided} | {why} |
   ```

2. **Update learnings.md** (gotchas + takeaways)
   ```markdown
   # Learnings

   ## {date}
   - {gotcha or takeaway 1}
   - {gotcha or takeaway 2}
   ```

3. **Update tech-debt.md** (known debt items)
   ```markdown
   # Tech Debt

   ## Unresolved
   - [ ] {debt item} — added {date}

   ## Resolved
   - [x] {debt item} — resolved {date}
   ```

4. **Create handover file** (most important artifact)
   ```markdown
   # Handover — {date}

   ## What was done this session
   - {accomplishment 1}
   - {accomplishment 2}

   ## What needs to happen next
   - [ ] {next task 1}
   - [ ] {next task 2}

   ## Context the next session needs
   - {key context: file paths, decisions, blockers, environment state}

   ## Files changed
   - {file}: {what changed and why}
   ```

5. **Commit all changes**
   ```bash
   git add AGENTS.md learnings.md tech-debt.md handover/
   git commit -m "session close: {brief summary}"
   ```

6. **Push if remote exists**
   ```bash
   git push 2>/dev/null || echo "No remote configured"
   ```
</process>

<auto_trigger>
To auto-trigger on session close, wire a shell hook:
```bash
# In .bashrc or .zshrc
function on_session_close() {
  if [ -f "AGENTS.md" ]; then
    echo "Running close-session..."
    # Trigger the skill via your agent
  fi
}
```

Or use a background watcher that detects when the agent process exits
and fires the close-session skill headlessly.
</auto_trigger>

<success_criteria>
- AGENTS.md updated with current project state
- learnings.md has session-specific gotchas
- tech-debt.md reflects any new debt items
- handover/ directory has a dated handover file
- All changes committed to git
</success_criteria>

<pitfalls>
1. **Stale handover files** — always create a NEW dated file, don't overwrite
2. **Too verbose** — handover should be scannable in <2 minutes
3. **Missing "next steps"** — the most valuable part is what needs to happen next
4. **Not committing** — uncommitted handover files are useless to the next session
5. **Forgetting environment state** — note env vars, running services, branch state
</pitfalls>

<references>
- Source video: https://www.youtube.com/watch?v=NRrj6qEymBY (13:55-16:20)
- Related: handoff skill (cross-session handoff)
- Related: context-save / context-restore (gstack)
- RIG equivalent: JakeStudio vault captures + obsidian-memory-bridge
</references>
