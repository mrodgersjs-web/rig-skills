# Contributing to RIG Skills

Thanks for considering a contribution. This repo collects [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) — self-contained instruction files that AI coding agents (Claude Code, Codex, Hermes, and compatible harnesses) load on demand. Contributions that keep skills sharp, portable, and honest about what they do are welcome.

## What belongs here

- **New skills** that fit an existing category (`engines/`, `doctrine/`, `studios/`, `engineering/`, `gtm/`, `fleet/`, `knowledge/`, `platform/`) or justify a new one.
- **Fixes** to existing `SKILL.md` files: broken instructions, stale references, incorrect trigger descriptions, outdated tool names.
- **Generalization patches** that replace a hardcoded internal tool/path with a documented placeholder or configuration point, so the pattern works outside the original RIG deployment.
- **Reference material** (`references/*.md`) that documents a pitfall, API quirk, or operational lesson a skill depends on.

## What doesn't belong here

- Skills or references containing credentials, API keys, personal contact information, or any other secret/PII. If you find any that slipped through, open an issue immediately — don't submit a PR that includes it, even to "fix" it.
- Skills that only make sense with proprietary internal infrastructure and cannot be adapted or documented for external use.
- Low-effort skill stubs with no working instructions, trigger conditions, or examples.

## Skill format

Every skill is a directory named after the skill (`kebab-case`, prefixed `rig-` if it extends RIG doctrine) containing at minimum a `SKILL.md`:

```
category/
  your-skill-name/
    SKILL.md          # required
    references/*.md   # optional — deep-dive docs the skill points to
    scripts/*         # optional — executable helpers the skill invokes
    templates/*        # optional — boilerplate the skill fills in
```

`SKILL.md` must open with YAML frontmatter:

```yaml
---
name: your-skill-name
description: >
  One or two sentences: what the skill does and when an agent should use it.
  Be specific about trigger phrases or conditions — this is what agents match
  against to decide whether to load the full skill body.
---
```

Followed by markdown instructions written for an AI agent, not a human reader — be directive, concrete, and avoid ambiguity about what "done" looks like.

## Submitting a change

1. Fork the repo and create a branch.
2. Add or edit the skill under the correct category directory. If you're adding a new skill, also add its row to the table in `README.md` (category, name, one-line description).
3. Run a plain-text scan for secrets and personal data before opening a PR:
   ```bash
   grep -rIlE '(sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)' .
   ```
4. Open a pull request describing what the skill does, what harness(es) you tested it in, and any internal-tool references you generalized.

## Style notes

- Keep descriptions in the frontmatter under ~400 characters — they're loaded for every agent on every turn, even when the skill body isn't.
- Prefer concrete trigger phrases ("Use when the user says X") over vague ones ("Use for general Y tasks").
- If a skill depends on another skill in this repo, say so explicitly and link it.
- Don't restyle or reformat files you're not otherwise changing — keep diffs focused.

## Questions

Open an issue. If it's about a specific skill's behavior in a specific harness, include the harness name and version.
