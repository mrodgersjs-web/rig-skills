---
name: rig-doctrine-infrastructure-wiring
description: >
  Wire new doctrine, subsystem specs, or major capabilities into the RIG agent
  infrastructure. Use when adding a new doctrine file, convergence subsystem,
  policy bundle, or capability that ALL RIG agents (Jake, Hermes, Claude, Codex,
  department agents, workers) must load. Covers the 6 mandatory infrastructure
  points and the exact patch patterns for each.
trigger_conditions:
  - "User says 'wire this into all agents' or 'make all agents load this'"
  - "New doctrine file created that needs to be globally loaded"
  - "New convergence subsystem or policy bundle added"
  - "User says 'all department agents should load this' or 'this is now mandatory'"
  - "After creating a major new spec that needs to be in every session's load order"
  - "After building a new subsystem that Jake and all RIG agents must know about"
---

# RIG Doctrine Infrastructure Wiring Skill

## Purpose

When a new doctrine, subsystem spec, policy bundle, or capability is created
that ALL RIG agents must load, there are **6 mandatory infrastructure points**
that need updating. Miss any one and some agents won't load it.

This skill is the checklist and exact procedure for each point.

---

## The 6 Infrastructure Points

| # | What | File | What to Add |
|---|------|------|-------------|
| 1 | **Unified Doctrine Index** | `~/.rig/agent-doctrine/RIG_UNIFIED_DOCTRINE_INDEX.md` | Category entry + load order lines in ALL session types |
| 2 | **Meta-Harness Boot Contract** | `~/.rig/meta-harness/BOOT_CONTRACT.md` | Contract bullet in the "## Contract" section |
| 3 | **Agent Team Bootstrap** | `~/.rig/agent-doctrine/RIG_AGENT_TEAM_BOOTSTRAP_DOCTRINE.md` | Line item in "## Required Boot Stack" numbered list |
| 4 | **Department PAI Substrate** | `~/.rig/agent-doctrine/RIG_DEPARTMENT_PAI_SUBSTRATE.md` | Component in the substrate components list |
| 5 | **Cursor Rule** | `.cursor/rules/<name>.mdc` | New `.mdc` file with `alwaysApply: true` |
| 6 | **Session Type Load Orders** | In the Unified Doctrine Index | Add to each applicable session type's load order block |

---

## Step-by-Step Procedure

> **Reference:** `references/wiring-patterns.md` has exact copy-paste patch patterns for each infrastructure point.

### Step 1: Create the Doctrine/Spec File

Write the actual doctrine file at its canonical path under `~/.rig/agent-doctrine/`
or `~/.rig/convergence/<subsystem>/`. This is the source of truth.

### Step 2: Add to Unified Doctrine Index — Category Catalog

Open `~/.rig/agent-doctrine/RIG_UNIFIED_DOCTRINE_INDEX.md`. Find the appropriate
category (A through E, or create a new category if needed). Add a row to the
category table:

```markdown
| E8 | New Spec Name | `~/.rig/path/to/SPEC.md` | One-line purpose | When to load |
```

**Pitfall:** The category header must match exactly. Common names:
- `### Category A: Core Doctrine`
- `### Category B: Agent-Specific Doctrine`
- `### Category C: Policy Bundles`
- `### Category D: Operating Procedures`
- `### Category E: Convergence Core`

### Step 3: Add to Session Type Load Orders

In the same Index file, add a numbered line to **each applicable session type's**
load order block. The session types are:

1. Coding / Implementation (Claude Code, Cursor, OpenCode, Aider)
2. Multi-Agent / Hermes Conductor
3. Production Compilation / Codex
4. GTM / Outreach / Campaigns
5. Scraping / Data Ingestion
6. Skill Ingestion / OpenClaw
7. Public Content / Brand
8. Quick Answer (no build, no deploy, no external action)

**Pattern for adding a line:**
```markdown
13. New doctrine name:  ~/.rig/path/to/FILE.md
```

**Pitfall:** Each session type block ends with a closing ` ``` `. Insert before
the closing fence. Numbering must be sequential within each block.

**Pitfall:** "Quick Answer" may not need heavy doctrine. Only add if the
doctrine is truly universal (like the Convergence Core).

### Step 4: Update Meta-Harness Boot Contract

Open `~/.rig/meta-harness/BOOT_CONTRACT.md`. Find the bullet list in the
"## Contract" section. Add a new bullet:

```markdown
- New doctrine is global doctrine for all RIG/Jake/department work. Load `/path/to/FILE.md` plus any index. Brief description of what it covers and why it's mandatory.
```

### Step 5: Update Agent Team Bootstrap

Open `~/.rig/agent-doctrine/RIG_AGENT_TEAM_BOOTSTRAP_DOCTRINE.md`. Find the
"## Required Boot Stack" numbered list. Add your file(s) after the existing
items. **Renumber all subsequent items** to keep the list sequential.

**Pitfall:** The numbering is easy to get wrong when inserting mid-list.
Always renumber from the insertion point to the end.

### Step 6: Update Department PAI Substrate

Open `~/.rig/agent-doctrine/RIG_DEPARTMENT_PAI_SUBSTRATE.md`. Find the substrate
components list (near the top, under the department agent description). Add a
new bullet:

```markdown
- new-component: description and path references
```

### Step 7: Create Cursor Rule

Create `.cursor/rules/<descriptive-name>.mdc` with:

```yaml
---
description: One-line description of what this rule enforces
globs:
alwaysApply: true
---

# Rule Title

Content that Cursor agents must follow. Include:
- The core invariant or law
- Quick reference table of what to load
- Required behaviors
- Connection to the canonical source file
```

**Pitfall:** `alwaysApply: true` means it loads for EVERY Cursor session.
Only use this for truly universal doctrine. If it's domain-specific, use
`globs` patterns instead.

---

## Verification Checklist

After wiring, verify each point:

```bash
# 1. Index has the new category/entry
grep -c "NewSpec" ~/.rig/agent-doctrine/RIG_UNIFIED_DOCTRINE_INDEX.md

# 2. Boot contract references it
grep -c "NewSpec" ~/.rig/meta-harness/BOOT_CONTRACT.md

# 3. Agent team bootstrap has it
grep -c "NewSpec" ~/.rig/agent-doctrine/RIG_AGENT_TEAM_BOOTSTRAP_DOCTRINE.md

# 4. Department PAI references it
grep -c "NewSpec" ~/.rig/agent-doctrine/RIG_DEPARTMENT_PAI_SUBSTRATE.md

# 5. Cursor rule exists
ls -la ~/.cursor/rules/<name>.mdc

# 6. All session types updated (count should match number of applicable types)
grep -c "New doctrine name" ~/.rig/agent-doctrine/RIG_UNIFIED_DOCTRINE_INDEX.md
```

---

## Pitfalls

### Race Condition: Parallel Subagents Writing to Same File
When dispatching parallel subagents to write specs while also writing directly,
two agents may write to the same file. The last write wins. **Always check file
content (not just existence) after subagents complete.** If a race occurred,
the file will have one version — verify it's the right one.

### Duplicate Numbering in Bootstrap
When inserting into the Agent Team Bootstrap numbered list, the original items
keep their old numbers. You get 8, 9, [new 8, new 9], [old 8, old 9].
**Always renumber from insertion point to end.**

### Missing Session Type
There are 8 session types. If you miss one, agents running under that session
type won't load the new doctrine. The most commonly missed are:
- Skill Ingestion / OpenClaw
- Public Content / Brand

### Generic Purpose Statement
The "When to Load" column in the Index must be specific. Bad: "When needed."
Good: "When verifying artifacts or running gauntlets."

---

## Example: Convergence Core Wiring (2026-07-06)

The RIG Convergence Core v1 was wired into all infrastructure:

**Files created:**
- `~/.rig/agent-doctrine/RIG_CONVERGENCE_CORE_DOCTRINE.md` (247 lines)
- `~/.rig/convergence/powertrain/PATTERN_SKILL_FOUNDRY_SPEC.md` (815 lines)
- `~/.rig/convergence/memory-cortex/SUBSTRATE_MEMORY_CORTEX_SPEC.md` (373 lines)
- `~/.rig/convergence/durable-floor/DURABLE_FLOOR_SPEC.md` (324 lines)
- `~/.rig/convergence/sentinel-prime/SENTINEL_PRIME_SPEC.md` (588 lines)
- `~/.rig/convergence/department-fleet/DEPARTMENT_FLEET_SPEC.md` (340 lines)
- `~/.cursor/rules/rig-convergence-core.mdc` (82 lines)

**Infrastructure points updated:** 6/6
**Session types updated:** 7/8 (Quick Answer excluded — conversational only)
**Total lines wired:** 2,873 lines of specs + 6 infrastructure patches

---

## Final Rule

```text
Every doctrine that governs the fleet must be loadable by every agent in the fleet.
If an agent can't find it, the doctrine doesn't exist for that agent.
Wire it everywhere or wire it nowhere — there is no "most agents will get it."
```
