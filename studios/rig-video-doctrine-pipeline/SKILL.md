---
name: rig-video-doctrine-pipeline
description: "Extract transcripts from agentic coding videos (YouTube), analyze for patterns/techniques/workflows, and generate RIG doctrine artifacts: skills, harnesses, agents, and L10 modules. Use when ingesting video knowledge into the RIG operating system."
tags: [rig, doctrine, youtube, knowledge-ingestion, skills, l10, agents, harnesses]
---

# Video → Doctrine Pipeline

<objective>
Turn agentic coding video transcripts into RIG doctrine artifacts.
Accepts YouTube URLs → extracts transcript → analyzes for patterns →
classifies into artifact types → generates and stores RIG artifacts.
</objective>

<when_to_use>
- User shares a YouTube video about agentic coding, AI agents, or coding workflows
- Building knowledge base from video content for RIG departments
- Converting external expertise into reusable RIG skills/harnesses/agents/L10 modules
- Ingesting conference talks, tutorials, or workshop recordings into doctrine
</when_to_use>

## Pipeline Stages

```
Video URL(s)
  ↓
[1] EXTRACT — fetch_transcript.py --text-only --timestamps
  ↓
[2] ANALYZE — LLM pass: identify techniques, patterns, workflows, principles
  ↓
[3] CLASSIFY — map each pattern to artifact type:
     • Skill       → reusable procedure (SKILL.md)
     • Harness     → gate loop / goal harness (.md)
     • Agent       → persona/definition (agent config)
     • L10 Module  → self-evolving Python module (rig-l10/src/)
  ↓
[4] GENERATE — produce typed artifacts from templates
  ↓
[5] STORE — route to canonical locations
  ↓
[6] INDEX — push to GBrain for semantic retrieval
</when_to_use>

## Quick Start

### Single video
```bash
# Step 1: Extract transcript
uv run python3 ~/.hermes/skills/media/youtube-content/scripts/fetch_transcript.py \
  "VIDEO_URL" --text-only --timestamps > /tmp/transcript.txt

# Step 2: Run pipeline (interactive — Claude analyzes and generates)
# Just pass the URL to the agent with this skill loaded
```

### Batch processing
Pass multiple URLs. Pipeline processes each independently, then cross-references
patterns across all videos before generating artifacts (avoids duplicates).

## Artifact Classification Rules

<routing>
When analyzing a transcript, classify each extracted pattern:

### → Skill (SKILL.md)
**Trigger:** A repeatable procedure, workflow, or technique that an agent can follow.
**Examples:** "How to set up a verification loop", "TDD workflow for agents",
"Context window management technique"
**Store to:** `~/.hermes/skills/{skill-name}/SKILL.md`
**Template:** templates/skill-template.md

### → Harness (goal harness)
**Trigger:** A gate loop, quality bar, or verification framework.
**Examples:** "Builder+Verifier closed loop", "Multi-pass review harness",
"Goal loop with kill switch"
**Store to:** `~/.hermes/jake/goal-harnesses/{harness-name}.md`
**Template:** templates/harness-template.md

### → Agent (agent definition)
**Trigger:** A persona, role, or specialized agent pattern.
**Examples:** "Scout agent that explores codebase", "Red team adversarial reviewer",
"Planner agent for decomposition"
**Store to:** `~/.hermes/agents/jtbd/{agent-name}/` or vault
**Template:** templates/agent-template.md

### → L10 Module (Python module)
**Trigger:** A self-evolving, measurable, or algorithmic pattern.
**Examples:** "Confidence calibration engine", "Pattern mining algorithm",
"Automated quality scoring system"
**Store to:** `$HOME/rig-l10/src/{module_name}/`
**Template:** templates/l10-module-template.md

### → Cross-reference (doctrine note)
**Trigger:** A principle, law, or meta-pattern that doesn't fit a single artifact type.
**Store to:** JakeStudio vault or GBrain as knowledge entry
</routing>

## Analysis Pass Structure

When analyzing a transcript, extract these categories:

1. **Techniques** — specific coding/agent methods described
2. **Patterns** — recurring structures (loops, architectures, workflows)
3. **Principles** — underlying laws or heuristics
4. **Tools** — specific tools, libraries, or services mentioned
5. **Anti-patterns** — things to avoid, failure modes
6. **Metrics** — how to measure success, KPIs mentioned
7. **Workflows** — multi-step processes described

For each extracted item, determine:
- **RIG artifact type** (skill/harness/agent/l10/cross-ref)
- **Confidence** (high/medium/low — based on how explicitly described)
- **Novelty** (does RIG already have this? check GBrain first)
- **Priority** (how valuable for RIG operations)

## Integration Points

- **GBrain:** Search before generating to avoid duplicates
- **L10:** New modules follow existing L10 architecture (common.py, cli.py integration)
- **Skills:** Follow create-skill skill format (XML structure, router pattern)
- **Harnesses:** Follow goal-harness-creation skill format
- **Obsidian:** Store analysis notes in JakeStudio vault

## Source Fidelity Tiers

Not all extraction methods are equal. Be explicit about what you're getting:

| Tier | Method | What You Get | What You Miss |
|------|--------|-------------|---------------|
| 🟢 Tier 1 | MCP/API access to gated content | Full lesson text, code, configs, exercises | Nothing — full access |
| 🟡 Tier 2 | Public docs / published curriculum | Lesson text, architecture, principles | Gated code examples, exercises, community |
| 🟡 Tier 3 | YouTube transcript extraction | Spoken content, technique descriptions | Screen recordings, code shown on screen, terminal commands, visual demos |
| 🔴 Tier 4 | Search results / course listings | Curriculum structure, lesson titles, summaries | All actual content |

**Always state which tier you're operating at.** "I extracted this from transcripts" is different from "I accessed the full course." The user needs to know what gaps exist.

**When you hit a gated MCP endpoint:**
1. Ask the user if they have credentials
2. If yes, try: have user log in via Safari → grab session cookie → use cookie for MCP auth
3. Do NOT fight bot detection on browser automation for login forms — it wastes time
4. Do NOT store raw credentials in repos, vault, or ProofPackets

## Pitfalls

1. **Auto-generated transcripts are noisy** — clean before analyzing
2. **Not everything is doctrine** — filter out filler, anecdotes, basic info
3. **Cross-reference first** — check GBrain/skills before creating duplicates
4. **L10 modules need tests** — don't just write stubs, write passing tests
5. **Skills need trigger conditions** — not just content, but WHEN to use
6. **Timestamps lose value** — extract the pattern, not the timestamp
7. **Gated MCP endpoints need session tokens, not basic auth** — most SaaS MCPs use cookie/OAuth auth, not HTTP basic. Fight the auth flow, not the endpoint.
8. **Browser automation on login forms triggers bot detection** — Cloudflare, CAPTCHAs, and anti-bot JS block automated clicks. Use Safari session cookies instead.
9. **Transcripts miss visual content** — code shown on screen, terminal commands, MCP configs, and UI demos are invisible in transcripts. Note the gap explicitly.
10. **Disk space for browser automation** — Browserbase and similar tools write to /tmp. If /tmp is near capacity, browser tools fail silently (empty pages, lost refs). Clean /tmp before long browser sessions.
