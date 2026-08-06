---
name: rig-linkedin-studio-engine-builder
description: "Build LinkedIn Studio A1A3A4 engines."
---

# RIG LinkedIn Studio Engine Builder

Use this skill when building any new engine (commenting, engagement, DM,
publishing) on top of the RIG LinkedIn Studio codebase at
`products/legacy/linkedin-studio/`. Encodes the layered architecture pattern,
template hygiene rules, scoring alignment, and cache-failover conventions.

## Architecture Layers

### A1 Contracts — `linkedin_studio/A1_contracts/`
Deterministic, pure. No external state, no A2/A3/A4 imports.
- Pydantic models with `ConfigDict(strict=True, frozen=True)`, `schema_version`
- Pure functions: `classify_post()`, `score_comment()`, `detect_conference_post()`
- Constants: `COMMENT_BANK`, `CONFERENCE_REGISTRY`, `HIGH_IFC_REGISTRY`
- **Template hygiene**: every placeholder in templates must appear in the
  replacements dict. Values must NOT start with articles ("the") when the
  template also starts with that article (avoids "the the ...").
- **Scoring**: `score_comment` must check VALUES (`.values()`) of
  VERTICAL_CONTEXT dicts, not just KEYS, since templates use values.

### A2 Gateway — `linkedin_studio/A2_gateway/`
Structured-output LLM gateway. Validates LLM output against A1 models.

### A3 Workflows — `linkedin_studio/A3_workflows/`
Engine workers. ALL external side-effects MUST pass through ContainmentGuard.
- `discover_posts()`: cache file first, sample post fallback for dry-run
- `post_comments()`: dry_run (score only) + live (containment-gated)
- AuditRow logging for every action
- **Requires `langgraph` installed** — A3 `__init__.py` imports langgraph

### A4 Control — `linkedin_studio/A4_control/`
Wrapper scripts compose A1+A2+A3. NEVER bypasses A1 contracts, A3 approval
graph, ProofPacket, action log, or human approval.

## 7 Commenty-AI Hook Types
announcement, session, speaker, attendee, sponsor, afterparty,
individual_post. Replace banned `fire_cycle` patterns with these.

## Scoring
```
hook_relevance = 25 * (data_point_refs + rig_insight_refs)
tone_fit       = 100 - (jargon * 15)
anti_generic   = 100 - (banned * 20)
specificity    = 50 + 15(has_num) + 20(has_domain) + 15(20<=wc<=60)
total          = avg(4 scores)
approved       = total >= 70.0 AND anti_generic >= 40.0
```

## Out-of-Tree Import Path
```python
sys.path.insert(0, str(STUDIO_SRC))
```
