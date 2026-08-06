# Case Study: Jake PAI v2 — Intel Swarm Research → Implementation

**Date:** 2026-07-06
**Type:** Research-driven PAI upgrade (existing PAI, not persona→PAI)
**Source:** Intel Swarm Pod 1 (10 research agents, 1,030 YouTube transcripts, 9 doctrine files)

## Pattern: Research Findings → PAI Improvements

This is a distinct workflow from the persona→PAI upgrade. Here the agent ALREADY has a full PAI, and the goal is to apply structured research findings to improve it.

### Workflow

1. **Read research docs** — Intel Swarm report + synthesized Upgrade Memo
2. **Extract top N improvements** — ranked by impact × feasibility, each with score/source/rationale
3. **Implement each improvement** as a concrete artifact:
   - Python scripts (CLI tools, gates, monitors)
   - YAML crons (daily standup, weekly evolution, outcome measurement)
   - YAML rules (protection rules, load thresholds)
   - SQL schemas (outcome tracking, kill/accelerate views)
   - Markdown templates (decision checklists, standup formats)
4. **Update vault** — main operating system document with all improvements
5. **Update goal-loop-system.md** — new routing rules, delivery gates, crons
6. **Push Paperclip task** — status tracking with full implementation details
7. **Verify all scripts** — run each tool with test inputs, confirm output

### Artifacts Created (Jake v2 example)

| Category | Count | Examples |
|----------|-------|---------|
| Python scripts | 4 | jake-route.py, jake-feedback.py, antiforce-gate.py, memory-quality-gate.py |
| Python monitors | 1 | load-monitor.py |
| YAML crons | 3 | daily-standup.yaml, weekly-evolution.yaml, outcome-measurement.yaml |
| YAML rules | 1 | mike-protection.yaml |
| SQL schemas | 1 | attribution_store.sql (with views) |
| Markdown templates | 1 | decision-checklist.md |
| Vault documents | 2 | Jake Operating System v2.md, goal-loop-system.md |
| Paperclip tasks | 1 | Status tracking task |

### Key Implementation Patterns

**Deterministic routing CLI** — takes task description, scores BMS (0-1), identifies department by keyword matching, checks Gate-D triggers, returns routing decision. Pattern: argparse CLI → scoring function → department lookup → gate check → JSON/text output.

**Weighted scoring gate** — AntiGenericForce pattern: 5 criteria with weights summing to 100, each scored 0-100, weighted average produces total. Threshold-based pass/fail (≥80 = deliverable, 60-79 = raw material, <60 = reject). Missing properties flagged explicitly.

**Graduated load monitor** — tracks multiple metrics (session count, gate skips, low-leverage ratio, decisions), computes composite score, maps to color levels (GREEN/YELLOW/ORANGE/RED) with escalating actions. State persisted to JSON file, daily auto-reset.

**Feedback capture loop** — detects correction patterns in Mike's messages (regex matching), classifies correction type, maps to memory layer (1-7 priority), creates structured record, persists to JSONL. Each record has: id, timestamp, correction, type, layer, promoted flag, verified flag, applied count.

### Readiness Score Pattern

After implementing improvements, score each on a 0-100 scale and compute overall readiness:
- Implementation status (✅/🔲) + quality score
- Overall = weighted average of improvement scores
- Remaining gaps explicitly listed with rationale for why they're deferred

### Pitfalls

- **Don't create crons without testing the script first.** Verify each Python script with real inputs before wiring it into a cron.
- **Don't forget to update goal-loop-system.md.** New crons, routing rules, and delivery gates need to be documented in the central loop system.
- **Don't skip the Paperclip task.** Research-driven upgrades need tracking — the task captures what was done, what remains, and the readiness score.
- **Shell escaping with complex JSON.** When pushing Paperclip tasks with rich markdown descriptions, write JSON to a file first (`/tmp/task.json`) then use `curl -d @file`. Direct heredoc/inline JSON fails with special characters.
