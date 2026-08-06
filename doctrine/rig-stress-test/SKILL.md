---
name: rig-stress-test
description: "5-phase sequential adversarial review panel. Each phase attacks from a different angle: find flaws, imagine failure, argue opposition, find contradictions, then synthesize a verdict. Use when you need deep adversarial analysis of a plan, strategy, or major feature."
tags: [rig, review, adversarial, stress-test, strategy]
source: "The Ideal Agentic Setup — Yaron Been (https://www.youtube.com/watch?v=NRrj6qEymBY)"
extracted: "2026-07-22"
---

# Stress Test

<objective>
Run a 5-phase sequential review panel that attacks an artifact from every angle.
Each phase is a distinct adversarial lens. The final verdict synthesizes all phases
into prioritized tiers: Must Fix / Should Fix / Worth Knowing / Just Noise.
</objective>

<when_to_use>
- Before committing to a major architectural decision
- Before presenting a strategy to stakeholders
- When triple-review found issues but you need deeper analysis
- When the stakes are high and you can't afford blind spots
- Before a major refactor or migration
</when_to_use>

<prerequisites>
- An artifact to stress-test (plan, strategy, architecture, feature spec)
- Willingness to hear harsh criticism
</prerequisites>

<process>
## Steps

### Phase 1: Adversarial Review
**Lens:** Find every flaw, every unstated assumption.
```
Prompt: "You are a senior adversarial reviewer. Find every flaw, every unstated
assumption, every gap in this plan. Do not be constructive. Do not hedge.
Do not suggest fixes. Just find problems. Sort by file/section.
Rank by impact, not count. A single critical flaw outweighs 10 style issues."
```

### Phase 2: Pre-Mortem Analysis
**Lens:** Imagine failure and explain what went wrong.
```
Prompt: "It is 6 months from now. This plan/feature/strategy has failed completely.
Write a detailed post-mortem explaining what went wrong. Be specific about
which decisions led to failure, which assumptions were wrong, and which
risks materialized. Write as if you are the project lead explaining to
the board why this happened."
```

### Phase 3: Steel Man Opposition
**Lens:** Argue the strongest case AGAINST this approach.
```
Prompt: "You fundamentally disagree with this approach. Argue the strongest
possible case against it — with real conviction, not strawmen. Use evidence,
precedent, and logical reasoning. Your goal is to convince the decision-maker
that this is the wrong path. Be specific and cite concrete concerns."
```

### Phase 4: Contradiction Hunt
**Lens:** Find where stated goals conflict with actual decisions.
```
Prompt: "Examine this artifact for internal contradictions. Find places where:
- Stated goals conflict with proposed actions
- Success metrics contradict the chosen approach
- Constraints are acknowledged but then violated
- Different sections assume incompatible things
List each contradiction with the specific conflicting statements."
```

### Phase 5: Verdict Synthesis
**Lens:** Combine all findings into actionable tiers.
```
Prompt: "Synthesize findings from all 4 previous phases into a single verdict.
Categorize every finding into exactly one tier:

🔴 MUST FIX — blocking issues that prevent success
🟡 SHOULD FIX — important issues that reduce quality/risk
🔵 WORTH KNOWING — concerns to monitor but not act on now
⚪ JUST NOISE — low-impact, stylistic, or opinion-based

Rules:
- If multiple phases flagged the same issue, it auto-promotes
- A single critical flow outweighs 10 style needs
- Sort by impact, not count
- Be specific — reference files, sections, decisions
- Max 20 findings total across all tiers"
```
</process>

<success_criteria>
- All 5 phases completed sequentially
- Each phase produces distinct findings (not duplicates of previous phases)
- Final verdict has all 4 tiers populated (or explicitly empty)
- Auto-promotion applied for cross-phase consensus
- Findings reference specific files/sections/decisions
- Max 20 findings total
</success_criteria>

<pitfalls>
1. **Being too constructive** — the explicit instruction is "do not hedge, do not suggest fixes"
2. **Duplicate findings across phases** — each phase must attack from a DIFFERENT angle
3. **Vague findings** — require specific file/section/decision references
4. **Too many findings** — cap at 20, prioritize by impact
5. **Skipping phases** — all 5 are mandatory, each reveals different blind spots
6. **Using this for small changes** — reserve for high-stakes decisions (use triple-review for routine)
</pitfalls>

<references>
- Source video: https://www.youtube.com/watch?v=NRrj6qEymBY (11:53-13:53)
- Related: rig-triple-review (faster parallel review for routine changes)
- Related: god-nemesis (adversarial verification)
- Related: grill-me (relentless interview)
</references>
