---
name: rig-triple-review
description: "Run 3 independent adversarial reviewers in parallel, each with a different critical lens. Findings are merged, deduplicated by confidence, and returned as a prioritized action list. Use when you need multi-perspective feedback on a plan, feature, code change, or strategy."
tags: [rig, review, adversarial, parallel-agents, quality]
source: "The Ideal Agentic Setup — Yaron Been (https://www.youtube.com/watch?v=NRrj6qEymBY)"
extracted: "2026-07-22"
---

# Triple Review

<objective>
Spin 3 independent adversarial reviewers in parallel, each with a different critical lens.
They never see each other's work. Findings are merged, deduplicated by confidence,
and returned as a single prioritized action list.
</objective>

<when_to_use>
- After writing a plan or spec before implementation
- After a code change before committing
- After a strategy proposal before presenting
- When you need multi-perspective feedback fast
- When you suspect blind spots in your work
</when_to_use>

<prerequisites>
- An artifact to review (plan, code, strategy, feature spec)
- Access to delegate_task or parallel agent spawning
</prerequisites>

<process>
## Steps

1. **Define the 3 reviewers dynamically**
   Based on the artifact type, the LLM selects 3 appropriate reviewer personas:

   For product/strategy:
   - **Skeptical Reader**: A potential buyer/user who questions everything
   - **Domain Expert**: A technical expert who finds feasibility issues
   - **Target Audience**: A business guru (Hormozi/Tim Ferriss/Naval lens)

   For code:
   - **Security Adversary**: Finds vulnerabilities and attack surfaces
   - **Performance Skeptic**: Finds bottlenecks and scaling issues
   - **Maintainability Reviewer**: Finds complexity and tech debt

   For plans:
   - **Premortem Agent**: Assumes the plan failed, explains why
   - **Constraint Checker**: Finds resource/dependency/assumption violations
   - **Scope Critic**: Finds scope creep, ambiguity, and missing definitions

2. **Spawn all 3 in parallel**
   Each reviewer receives:
   - The artifact to review
   - Their specific critical lens
   - The instruction: "Find problems only. No fixes. No suggestions. Just issues."
   - Max findings: 15 per reviewer

3. **Collect findings**
   Each reviewer returns:
   ```
   - Issue: {description}
   - Severity: critical | high | medium | low
   - Location: {file/section/line if applicable}
   - Evidence: {why this is a problem}
   ```

4. **Merge and deduplicate**
   - Combine all findings
   - If 2+ reviewers flagged the same issue independently → auto-promote to highest priority
   - Deduplicate by semantic similarity
   - Max 15 findings total

5. **Prioritize into tiers**
   ```
   🔴 Fix Before You Ship — must address before any next step
   🟡 Should Fix — important but not blocking
   🟢 Nice to Fix — improvements for later
   ```

6. **Return the action list**
   Format:
   ```markdown
   ## Triple Review Results

   ### 🔴 Fix Before You Ship
   1. {finding} — flagged by {reviewers}

   ### 🟡 Should Fix
   2. {finding} — flagged by {reviewers}

   ### 🟢 Nice to Fix
   3. {finding} — flagged by {reviewers}

   **Summary:** {N} findings across {M} reviewers. {X} auto-promoted (flagged by all 3).
   ```
</process>

<success_criteria>
- 3 independent reviewers spawned and completed
- Findings merged and deduplicated
- Prioritized into 3 tiers
- Auto-promotion rule applied (all 3 flag = highest priority)
- Max 15 findings returned
</success_criteria>

<pitfalls>
1. **Reviewers seeing each other's work** — spawn them independently, no shared context
2. **Reviewers suggesting fixes** — explicitly instruct "problems only, no fixes"
3. **Too many findings** — cap at 15, prioritize by impact not count
4. **Same severity for everything** — force the 3-tier system
5. **Generic feedback** — require specific file/section references
</pitfalls>

<references>
- Source video: https://www.youtube.com/watch?v=NRrj6qEymBY (9:27-11:53)
- Related: rig-stress-test (deeper sequential analysis)
- Related: council (multi-perspective decision making)
</references>
