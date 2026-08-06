# RIG LinkedIn Studio A1/A3/A4 Architecture

## Layer Responsibilities

### A1 Contracts — Deterministic, Pure, Frozen
- Pydantic models: `ConfigDict(strict=True, frozen=True)`, `schema_version="1.0.0"`
- Pure functions only: classification, scoring, detection — no I/O, no external calls
- Constants: COMMENT_BANK, CONFERENCE_REGISTRY, HIGH_IFC_REGISTRY, VERTICAL_CONTEXT
- `CommentCandidate`: frozen, scored candidate with `is_approved` flag
- Every external action (comment, DM, publish) must satisfy all A1 gate constraints

### A2 Gateway — LLM Structured Output
- Prompts LLM with strict JSON schema matching A1 models
- Validates output against A1 schemas before passing to A3

### A3 Workflows — Engine Workers
- `ContainmentGuard`: ALL external actions blocked without approval
- `AuditStore`: every action logged as `AuditRow`
- Engine classes are subclass-isolated via A4 wrapper (subprocess)
- `discover_posts()` → cache file first, sample fallback
- `classify_post()` → deterministic classification into CONFERENCE / HIGH_IFC / GENERAL
- `generate_comment_for_post()` → template-based with 7 Commenty-AI hook types
- `post_comments()` → dry_run (score only) + live (containment-gated)

### A4 Control — Operating System
- `CommentEngineWrapper`: subprocess-isolates A3 engine, manages approval
- `SupervisorConfig`: orchestrates all layers
- `KillSwitch`, `BudgetSwitch`: safety mechanisms
- `ProofWriter`: writes ProofPacket with hashes, gate results, signer
- NEVER bypasses: A1 contracts, A2 gateway, A3 approval graph, ProofPacket, action log, human approval

## Data Flow

```
A4 CommentEngineWrapper.execute()
  → subprocess → A3 ConferenceCommentEngine.run()
    → A1 discover_posts() → classify() → generate_comment() → score_comment()
    → A3 ContainmentGuard.check_action("comment_on_post")
    → A3 AuditRow.log()
  → A4 ProofPacket.write()
```

## Error: langgraph Missing
The A3 `A3_workflows/__init__.py` imports `state_machine.py` which requires
`langgraph`. Install with: `pip install langgraph`
