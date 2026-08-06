# Workflow: Process Single Video

## Required Reading
- templates/skill-template.md (for skill outputs)
- templates/harness-template.md (for harness outputs)
- templates/agent-template.md (for agent outputs)
- templates/l10-module-template.py.md (for L10 outputs)

## Process

### Step 1: Extract Transcript
```bash
uv run python3 ~/.hermes/skills/media/youtube-content/scripts/fetch_transcript.py \
  "VIDEO_URL" --text-only --timestamps
```
Save output to `/tmp/video-doctrine-{video_id}.txt`

### Step 2: Search for Duplicates
Before analyzing, check GBrain for existing coverage:
```
gbrain query "topic from video title" limit 5
gbrain search "key terms from video" limit 5
```
Also check existing skills:
```
skills_list() → scan for overlapping names/descriptions
```

### Step 3: Analyze Transcript
Read the transcript and extract structured knowledge:

**Categories to extract:**
1. **Techniques** — specific methods (e.g., "context window management via file hierarchy")
2. **Patterns** — recurring structures (e.g., "builder+verifier closed loop")
3. **Principles** — laws/heuristics (e.g., "one agent, one prompt, one purpose")
4. **Tools** — specific tools/libraries mentioned
5. **Anti-patterns** — things to avoid
6. **Metrics** — success measurements
7. **Workflows** — multi-step processes

For each extracted item, record:
```
- Name: {descriptive name}
- Type: skill | harness | agent | l10 | cross-ref
- Confidence: high | medium | low
- Novelty: new | extends-existing | duplicate
- Priority: critical | high | medium | low
- Quote: {relevant transcript excerpt}
- Context: {why this matters for RIG}
```

### Step 4: Generate Artifacts
For each high-priority, non-duplicate item:

**Skills:**
- Load template from `templates/skill-template.md`
- Fill with extracted content
- Write to `~/.hermes/skills/{skill-name}/SKILL.md`
- Include trigger conditions, process steps, pitfalls, verification

**Harnesses:**
- Load template from `templates/harness-template.md`
- Define gates with evidence requirements
- Write to `~/.hermes/jake/goal-harnesses/{harness-name}.md`

**Agents:**
- Load template from `templates/agent-template.md`
- Define identity, mission, capabilities, rules
- Write to vault or agents directory

**L10 Modules:**
- Load template from `templates/l10-module-template.py.md`
- Implement core algorithm with tests
- Write to `/Users/rig128gb/rig-l10/src/{module_name}/`
- Add to L10 CLI registration

### Step 5: Index in GBrain
For each generated artifact:
```
gbrain put_page slug="doctrine/skills/{name}" content="{artifact frontmatter + summary}"
gbrain add_link from="doctrine/skills/{name}" to="{source-video-page}"
```

### Step 6: Create Summary Note
Write a JakeStudio vault note:
```
~/Documents/JakeStudio/Doctrine/Video Extractions/{date}-{video-slug}.md
```
Contains: video info, extracted patterns count, artifacts generated, links.

## Success Criteria
- Transcript extracted and non-empty
- At least 3 patterns identified
- At least 1 artifact generated and stored
- GBrain entries created
- Summary note written to vault

## Quality Checks
- Artifact has valid YAML frontmatter
- Skill has trigger conditions + process steps + pitfalls
- Harness has gates with evidence requirements
- Agent has identity + mission + rules + escalation
- L10 module has tests that pass
