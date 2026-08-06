---
name: rig-github-issue-writer
description: "Create structured GitHub issues from bug reports, feature suggestions, and user feedback. Maintains consistent issue format with source attribution, overview, requirements, and considerations. Integrates with screenshot automation for visual evidence. Use when encountering bugs or receiving feature requests."
tags: [rig, github, issues, project-management, automation]
source: "The Ideal Agentic Setup — Yaron Been (https://www.youtube.com/watch?v=NRrj6qEymBY)"
extracted: "2026-07-22"
---

# GitHub Issue Writer

<objective>
Turn bug reports, feature suggestions, and user feedback into structured GitHub issues
with consistent format: source attribution, overview, requirements, and considerations.
Automatically assigns priority and sprint. Integrates screenshot evidence.
</objective>

<when_to_use>
- When encountering a bug during development
- When receiving feedback from a design partner or user
- When you notice something that needs to be tracked
- When you have a feature suggestion to document
</when_to_use>

<prerequisites>
- A GitHub repository configured for the project
- `gh` CLI authenticated
- (Optional) Screenshot tool configured for evidence capture
</prerequisites>

<process>
## Steps

1. **Capture the issue context**
   - What was the expected behavior?
   - What actually happened? (for bugs)
   - What is the suggestion? (for features)
   - Who reported it? (source attribution)

2. **Check for existing repo**
   ```bash
   gh repo view --json nameWithOwner 2>/dev/null
   ```
   If no repo, ask user which repo to target.

3. **Construct the issue body**
   ```markdown
   ## Source Attribution
   - **Reported by:** {source — self, design partner, user name}
   - **Date:** {date}
   - **Context:** {what they were doing when they noticed}

   ## Overview
   {2-3 sentence summary of the issue or feature request}

   ## Requirements
   - {requirement 1}
   - {requirement 2}
   - {requirement 3}

   ## Considerations
   - {edge case, dependency, or constraint}
   - {alternative approaches considered}
   - {impact on other features}

   ## Evidence
   {Screenshot, log output, or reproduction steps}
   ```

4. **Assign priority and labels**
   ```bash
   gh issue create \
     --repo {owner/repo} \
     --title "{concise title}" \
     --body "{issue body}" \
     --label "{priority}" \
     --assignee "@me"
   ```

   Priority mapping:
   - **Blocker**: Production down, data loss, security issue
   - **High**: Feature broken, significant UX issue
   - **Medium**: Feature request, minor bug, improvement
   - **Low**: Nice to have, cosmetic, future consideration

5. **Add to project board** (if configured)
   ```bash
   gh issue edit {number} --add-project "{project name}"
   ```

6. **Return issue link**
   ```
   ✅ Issue #{number} created: {url}
   Priority: {priority} | Labels: {labels}
   ```
</process>

<screenshot_integration>
## Screenshot Automation (Optional)

For visual evidence, configure a screenshot tool that:
1. Captures screen region
2. Annotates with arrows/numbers
3. Offers 3 options:
   - Copy image to clipboard
   - Save locally + copy path
   - Upload to image host + copy URL

Then paste the image URL/attachment into the issue's Evidence section.
</screenshot_integration>

<success_criteria>
- Issue created with all 4 sections populated
- Priority assigned based on impact
- Source attribution included
- Evidence attached (screenshot, logs, repro steps)
- Issue link returned
</success_criteria>

<pitfalls>
1. **No source attribution** — always note who reported it
2. **Vague descriptions** — require specific expected vs actual behavior
3. **Wrong priority** — blocker = production down, not "I really want this"
4. **No evidence** — at minimum include reproduction steps
5. **Duplicate issues** — search before creating: `gh issue list --search "keyword"`
</pitfalls>

<references>
- Source video: https://www.youtube.com/watch?v=NRrj6qEymBY (16:20-20:04)
- Related: github-issues skill (basic issue creation)
- Related: gh-axi (GitHub operations CLI)
</references>
