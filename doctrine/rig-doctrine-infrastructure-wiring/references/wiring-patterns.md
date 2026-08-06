# Doctrine Wiring — Exact Patch Patterns

## 1. Unified Doctrine Index — Add Category Entry

Find the category header (e.g., `### Category E: Convergence Core`) and add a row:

```markdown
| E8 | Spec Name | `~/.rig/path/to/SPEC.md` | One-line purpose | When to load |
```

If creating a new category, insert before the next category header:

```markdown
### Category F: New Category Name

| # | File | Path | Purpose | When to Load |
|---|------|------|---------|--------------|
| F1 | File Name | `~/.rig/path/FILE.md` | Purpose | Trigger |
```

## 2. Unified Doctrine Index — Add to Session Type Load Orders

Each session type block looks like:

```markdown
### Session Type: <Name>

\`\`\`text
1. This index: ...
2. ...
...
N. Quality standard doctrine: ...
\`\`\`
```

Add before the closing ` ``` `:

```markdown
N+1. New doctrine name:  ~/.rig/path/to/FILE.md
```

**The 8 session types (in order):**
1. Coding / Implementation
2. Multi-Agent / Hermes Conductor
3. Production Compilation / Codex
4. GTM / Outreach / Campaigns
5. Scraping / Data Ingestion
6. Skill Ingestion / OpenClaw
7. Public Content / Brand
8. Quick Answer (optional — conversational only)

## 3. Meta-Harness Boot Contract

Add a bullet in the `## Contract` section:

```markdown
- New doctrine is global doctrine for all RIG/Jake/department work. Load `/path/to/FILE.md` plus index. Brief description.
```

## 4. Agent Team Bootstrap

Add to `## Required Boot Stack` numbered list. Insert after the last current
item and renumber:

```markdown
N. `/path/to/NEW_FILE.md`
N+1. `/path/to/INDEX.md`  (if applicable)
```

## 5. Department PAI Substrate

Add to the substrate components list (near top of file):

```markdown
- new-component: description and path from `~/.rig/path/FILE.md`
```

## 6. Cursor Rule

Create `.cursor/rules/<descriptive-name>.mdc`:

```yaml
---
description: One-line description
globs:
alwaysApply: true
---

# Title

Core content. Include:
- The invariant/law
- Quick reference table
- Required behaviors
- Connection to canonical source
```

## Verification Pattern

```bash
# Count references across all infrastructure
for f in \
  ~/.rig/agent-doctrine/RIG_UNIFIED_DOCTRINE_INDEX.md \
  ~/.rig/meta-harness/BOOT_CONTRACT.md \
  ~/.rig/agent-doctrine/RIG_AGENT_TEAM_BOOTSTRAP_DOCTRINE.md \
  ~/.rig/agent-doctrine/RIG_DEPARTMENT_PAI_SUBSTRATE.md \
  ~/.cursor/rules/<name>.mdc; do
  echo "$(basename $f): $(grep -c '<keyword>' $f 2>/dev/null || echo 0)"
done
```
