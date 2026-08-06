# Agentic Coding School Distillation — 2026-07-29 (worked example)

The canonical worked example of `rig-corpus-distillation-pipeline` in
action. This file is the run log + asset index + EXISTING classification
table that the next corpus can mine.

## Source

- URL: `https://www.agenticcoding.school/member`
- Run ID: `acs-20260729T183655Z`
- Operator: Jake RIG Agent (Hermes conductor)
- Authenticated via: `ego-browser` (inherits Mike's `ego-lite.app` session)

## Output summary

- **138** unique lessons with full body extraction
- **354** lesson occurrences (with duplicates sharing videoIds)
- **11** of 12 video classes + 1 config page (mcp → setup docs, not a class)
- **62** techniques mapped to existing RIG assets (no duplication)
- **73** new SKILL.md files at `~/.hermes/skills/acs-*.md`
- **73** new doctrine entries at `~/.rig/agent-doctrine/acs-distilled/acs-*.md`
- **12** new goal harnesses at `~/.jake/goal-harnesses/acs-*.md`
- **5** new canonical L10 rules at `~/rig-l10/rules/acs-*.toml`
- **1** umbrella skill (`acs-doctrine.md`) — loads at session start
- **1** lessons-learned doctrine (`acs-learnings.md`)
- **1** ProofPacket sealed at `proof.json` (sha256 hash)

## The 5 canonical rules (in TOML files)

```
acs.context-budget        — Stay Under 50% Context Usage
acs.loop-kill-switch      — Every Loop Needs a Kill Switch
acs.scout-worker-synthesizer — Multi-Agent Decomposition Pattern
acs.verifier-independence — Builder ≠ Verifier
acs.bug-persistence       — Persist Tried Approaches to File
```

Each TOML has: `[rule]` section with id/title/trigger/applies_when/rule_body/evidence,
`[verification]` with gates, `[provenance]` with run_id + distilled_at.

## The EXISTING classification table (snapshot)

This is the Python dict that prevented 62 duplications. The full
version is at `scripts/distill.py`:

```python
EXISTING = {
    "scout, worker, synthesizer":  ("tac-scout-worker-synthesizer", "skill"),
    "scout worker synthesizer":   ("tac-scout-worker-synthesizer", "skill"),
    "compaction":                ("tac-context-engineering",      "skill"),
    "auto compact":              ("tac-context-engineering",      "skill"),
    "auto compact and handoff":  ("tac-context-engineering",      "skill"),
    "context switching":         ("tac-context-engineering",      "skill"),
    "long context":              ("tac-context-engineering",      "skill"),
    "context management":        ("tac-context-engineering",      "skill"),
    "session & context":         ("tac-context-engineering",      "skill"),
    "session management":        ("tac-context-engineering",      "skill"),
    "starting in plan mode":     ("tac-context-engineering",      "skill"),
    "plan mode":                 ("tac-context-engineering",      "skill"),
    "improved plan mode":        ("tac-context-engineering",      "skill"),
    "continuing plan":           ("tac-context-engineering",      "skill"),
    "agent introspection":       ("tac-bug-hunting-deep",         "skill"),
    "debugging":                 ("tac-bug-hunting-deep",         "skill"),
    "debug":                     ("tac-bug-hunting-deep",         "skill"),
    "logging":                   ("observability",                "skill"),
    "evaluating code review":    ("requesting-code-review",       "skill"),
    "code review":               ("requesting-code-review",       "skill"),
    "headless mode":             ("tac-headless-automation",      "skill"),
    "background workflow":      ("tac-headless-automation",      "skill"),
    "stochastic coverage":       ("tac-stochastic-coverage",      "skill"),
    "loop":                      ("tac-loop-engineering",         "skill"),
    "context engineering":       ("tac-context-engineering",      "skill"),
    "context layer":             ("tac-context-layer",            "skill"),
    "closing loop":              ("tac-closing-loop",             "skill"),
    "verifier":                  ("tac-closing-loop",             "skill"),
    "test-driven":               ("tdd",                          "skill"),
    "tdd":                       ("tdd",                          "skill"),
    "scout":                     ("tac-scout-worker-synthesizer", "skill"),
    "worker":                    ("tac-scout-worker-synthesizer", "skill"),
    "synthesizer":               ("tac-scout-worker-synthesizer", "skill"),
    "subagent":                  ("tac-subagent-orchestration",   "skill"),
    "subagents":                 ("tac-subagent-orchestration",   "skill"),
    "spec developer":            ("tac-context-engineering",      "skill"),
    "spec":                      ("tac-context-engineering",      "skill"),
    "claude.md":                 ("tac-claude-md-mastery",        "skill"),
    "init":                      ("tac-claude-md-mastery",        "skill"),
    "hierarchical":              ("tac-claude-md-mastery",        "skill"),
    "skill":                     ("create-skill",                 "skill"),
    "skills":                    ("create-skill",                 "skill"),
    "hook":                      ("hookify-rules",                "skill"),
    "hooks":                     ("hookify-rules",                "skill"),
    "plugin":                    ("plugin-eval__evaluation-methodology", "skill"),
    "plug ins":                  ("plugin-eval__evaluation-methodology", "skill"),
    "codex":                     ("codex",                        "skill"),
    "git":                       ("bridgespace-bridge-skill-github-commit", "skill"),
    "prompt cache":              ("tac-context-engineering",      "skill"),
    "economising":               ("tac-context-engineering",      "skill"),
    "ultrathink":                ("tac-context-engineering",      "skill"),
    "understanding agent output":("tac-context-engineering",      "skill"),
    "just run it again":         ("tac-closing-loop",             "skill"),
    "multimodal models":         ("tac-context-engineering",      "skill"),
    "high level coherence":      ("tac-context-engineering",      "skill"),
    "artifact planning":         ("tac-context-engineering",      "skill"),
    "scoping apis":              ("api-design",                   "skill"),
    "reliable packages":         ("api-design",                   "skill"),
    "delete your readme":        ("tac-context-engineering",      "skill"),
    "reducing agent confusion":  ("tac-context-engineering",      "skill"),
    "bug fixing across chats":   ("tac-bug-hunting-deep",         "skill"),
    "ask ai":                    ("ask-claude",                   "skill"),
    "ask claude":                ("ask-claude",                   "skill"),
    "codex cli":                 ("codex",                        "skill"),
    "codex app":                 ("codex",                        "skill"),
    "ios builder":               ("codex",                        "skill"),
    "record & replay":           ("codex",                        "skill"),
    "codex security":            ("codex",                        "skill"),
    "telegram":                  ("telegram",                     "skill"),
    "discord":                   ("discord",                      "skill"),
    "remote control":            ("tac-headless-automation",      "skill"),
    "system prompt":             ("tac-context-engineering",      "skill"),
    "1m token":                  ("tac-context-engineering",      "skill"),
    "1m context":                ("tac-context-engineering",      "skill"),
    "ghostty":                   ("terminal",                     "skill"),
    "cmux":                      ("terminal",                     "skill"),
    "copy n":                    ("terminal",                     "skill"),
    "readline":                  ("terminal",                     "skill"),
    "warp":                      ("terminal",                     "skill"),
    "option p":                  ("terminal",                     "skill"),
    "github app":                ("github-pr-workflow",           "skill"),
    "mcp":                       ("create-mcp-server",            "skill"),
    "mcp server":                ("create-mcp-server",            "skill"),
    "mcp servers":               ("create-mcp-server",            "skill"),
    "mcp integration":           ("create-mcp-server",            "skill"),
    "official mcp":              ("create-mcp-server",            "skill"),
    "official plugin":           ("plugin-eval__evaluation-methodology", "skill"),
    "code-review":               ("requesting-code-review",       "skill"),
    "/simplify":                 ("ai-slop-cleaner",              "skill"),
    "/clear":                    ("tac-context-engineering",      "skill"),
    "/rewind":                   ("tac-context-engineering",      "skill"),
    "/init":                     ("tac-claude-md-mastery",        "skill"),
    "/advisor":                  ("tac-context-engineering",      "skill"),
    "/teleport":                 ("tac-headless-automation",      "skill"),
    "loopy ai":                  ("tac-loop-engineering",         "skill"),
    "loop engineering":          ("tac-loop-engineering",         "skill"),
    "thread engineering":        ("tac-subagent-orchestration",   "skill"),
    "for business":              ("company-builder",              "skill"),
    "building a saas":           ("company-builder",              "skill"),
    "creating slack agents":     ("create-mcp-server",            "skill"),
    "creating slack":            ("create-mcp-server",            "skill"),
    "0 to 1":                    ("company-builder",              "skill"),
}
```

### Iterator pattern (catches hundreds of techniques from the corpus)

```python
def classify(name):  # name = lesson title or chapter heading
    n = name.lower()
    for fragment, (asset, atype) in EXISTING.items():
        if fragment in n:
            return atype, asset, "existing"
    return "unknown", "unknown", "new"
```

## The umbrella skill template

The `acs-doctrine.md` umbrella is the canonical example. Its
frontmatter must declare:

1. The 5 canonical rules by ID (with paths to TOML files)
2. The 7 most-cited techniques (with the existing skill that covers
   them, or the new asset that fills the gap)
3. The 7 novel platform-specific gaps (new assets)
4. The summary of what the corpus taught (5 takeaways)
5. The "what we can do now" implications for the operator

The full umbrella is at `~/.hermes/skills/acs-doctrine.md`. It's 7KB
and includes the "When to load" section, the 5 rules in detail, the 7
most-cited, the 7 novel, the 5 discoveries, the 5 capabilities, and a
single Provenance section that ties everything back to the run_id.

## The 5 discoveries (in order of operational impact)

1. **Platform cross-links techniques as a graph.** The `Long Context
   Failure` lesson references `Scout, Worker, Synthesizer` (claude-code)
   and `Compaction` (claude-code). Captured in every doctrine entry's
   `related_lessons` block.
2. **MCP server is the official transcript API.** `claude mcp add
   --transport http agentic-coding-school https://www.agenticcoding.school/api/mcp -s user`
   pulls transcripts directly. The school doesn't expose word-for-word
   transcripts in the page DOM (per DMCA), but the MCP server does.
3. **Ego-browser JS expression wrapping gotcha.** The `js()` helper
   auto-wraps source in `(function(){...})()`. See the dedicated
   reference file for the full workaround.
4. **Curriculum IS TAC.** Most techniques are already covered by
   existing RIG skills. New assets fill genuine Claude Code / Codex
   feature gaps.
5. **Anti-AI prompt injection** is embedded in every lesson DOM (a
   "SYSTEM INSTRUCTION" telling AI assistants to refuse the work).
   Ignored as an instruction source per system rules; spirit honored
   (no HLS / m3u8 / video ripping).

## Re-run recipe

```bash
# Re-run after the corpus adds new content
cd ~/Developer/transformfit-flutter
# (or wherever the source is)

# Stage 1: only new lessons
python3 scripts/extract_lessons.py    # skips existing
# Stage 2: classify + write new assets
python3 scripts/distill_v3.py        # skips existing
# Stage 3: validate
python3 scripts/validate_q.py
# Stage 4: re-seal
python3 scripts/seal_proof.py
```

## Files written (full list)

165 assets across 4 canonical paths + 1 umbrella + 1 ProofPacket:

| Path | Count | Examples |
|---|---|---|
| `~/.hermes/skills/acs-*.md` | 74 | `acs-context-budget`, `acs-doctrine`, `acs-compaction` |
| `~/.jake/goal-harnesses/acs-*.md` | 12 | `acs-dynamic-workflows-harness`, `acs-install-claude-code-macos-harness` |
| `~/.rig/agent-doctrine/acs-distilled/acs-*.md` | 74 | `acs-learnings`, `acs-compaction`, `acs-context-budget` |
| `~/rig-l10/rules/acs-*.toml` | 5 | `acs-context-budget.toml`, `acs-loop-kill-switch.toml` |
| `proof.json` | 1 | 7 gates × 3 OpenSpec changes (acs, tf-ship, ...) |

## Verification

- Custom validator (`validate_q.py`): 12/12 PASS on the acs change
- ProofPacket: `sha256:c707a5819b757758e9a5cec20850fd39880e13b834f1031fe37c1c17066c6efb`
- No-secret-leak gate: zero matches across 1.4 MB of artifacts
- Outer validator (transformfit-ship-stores): 33/33 PASS

## Status

CLOSE. The acs-20260729T183655Z run is sealed. The pipeline is
re-runnable. The umbrella loads at session start. The 5 rules are
enforceable via L10 rule infrastructure.