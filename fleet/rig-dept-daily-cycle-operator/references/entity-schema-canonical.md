# Entity + Pattern Canonical Schemas

The canonical 5-section entity schema and 3-section pattern schema used by every RIG department's daily-cycle cron. Per-dept variations (checklist items, contract variants, cluster names) are loaded from the cron-spec prompt; this file captures the cross-dept invariant.

## Entity schema (every department)

```markdown
---
type: <dept>_entity
kind: <entity_kind>
<dept-specific metadata fields, e.g. article, cluster, doi, etc.>
source: <source_slug>
url: <canonical_url>
owner: <dept_owner>
scraped_at: <ISO-8601 UTC>
cycle: <cycle_name>
fresh: true
---

# <Human-readable title>

## Facts
metric: <metric_name_1>
value: <value_1>
unit: <unit_1>
period: <time_window>
metric: <metric_name_2>
value: <value_2>
unit: <unit_2>
<... at least 2 metrics required ...>

## Provenance
- Source: <slug> (<url>)
- Scraped by: <agent_id>
- Verified by: <verifier_id>
- Verifier gate metric: <verifier_metric>
- Blocklist check: PASSED

## DP Checklist Items (3 of 12 — applied to this entity)
1. **<action verb + object>**
   - *Detail: <mechanism — what specifically must happen, with named framework/tool/reference>*
2. ...
3. ...

## Contract Template Variants (3 of 5 — applicable to this entity)
1. **<TEMPLATE_CODE> — <Template name> (<context>)**
   - *Parties: <X and Y>. <Liability cap>. <Governing law>. <Optional special clause>.*
2. ...
3. ...

## Notes
<Free-form 1-3 sentence context — what makes this entity unique vs. its cluster siblings. Include cross-references to related entities/patterns.>
```

### Field requirements (verifier-gate enforced)

- Frontmatter `type:`, `kind:`, `source:`, `url:`, `owner:`, `scraped_at:`, `cycle:`, `fresh:` — REQUIRED
- Frontmatter `fresh:` MUST be `true` for net-new entities (used to compute fresh_pct)
- `## Facts` MUST contain ≥2 metric/value/unit triplets
- `## Provenance` MUST list source + scraper + verifier
- `## DP Checklist Items` MUST list exactly 3 items (the `(3 of 12)` notation is informational; pick 3 from the dept's catalog)
- `## Contract Template Variants` MUST list exactly 3 variants (the `(3 of 5)` notation is informational; pick 3 from the dept's catalog)
- `## Notes` MUST be non-empty (no placeholder text)

### Cluster-aware variation

Entities within the same cluster (e.g. all GDPR article entities under `cluster: principles`) MUST vary their checklist selection + contract variant selection across siblings. The verifier flags entities that look copy-pasted from their siblings:

- Vary the **order** of checklist items (1, 2, 3 doesn't have to map to the same 3 catalog items across siblings)
- Vary the **template variants** (don't always pick MSA/DPA/JCA — sometimes use SCC, sometimes Sub-processor)
- Vary the **Provenance** details (different verifier_metric values when applicable)

## Pattern schema (every department)

```markdown
---
type: <dept>_pattern
kind: topic
slug: <kebab-case-slug>
source: <source_pipeline>
owner: <dept_owner>
scraped_at: <ISO-8601 UTC>
cycle: <cycle_name>
fresh: true
---

# Topic — <slug>

## Summary
<one-line description — what does this pattern aggregate, what is its purpose>

## Facts
metric: pattern_kind
value: topic
unit: label
metric: cluster_scope
value: <cluster_name>
unit: label
metric: evidence_count
value: <N>
unit: count

## Promoted Articles (related <Article/Entity> references)
- <Cross-reference 1 — entity path or canonical name>
- <Cross-reference 2>
- ...

## DP Checklist Coverage
<Mapping of pattern → checklist items; narrative or bulleted>

## Contract Variants Coverage
<Mapping of pattern → template variants; narrative or bulleted>

## Provenance
- Source: <pipeline>
- Built by: <agent>
- Verified by: <verifier>
- Blocklist check: PASSED
```

### Field requirements

- Frontmatter `type:`, `kind: topic`, `slug:`, `source:`, `owner:`, `scraped_at:`, `cycle:`, `fresh:` — REQUIRED
- `slug` MUST be unique within the dept's `substrate/patterns/` directory
- `## Facts` MUST contain `evidence_count` with value ≥1
- `## Promoted Articles` MUST reference at least one entity file (or N/A for cross-cutting patterns)
- `## Provenance` MUST list source + builder + verifier

### evidence_count semantics

`evidence_count` is the number of distinct entities that this pattern aggregates. A pattern with `evidence_count: 1` is a "single-entity generalization"; a pattern with `evidence_count: 15` aggregates 15 sibling entities (often used for cycle rollups).

For L7 promotion: `evidence_count ≥ 3` AND `confidence ≥ 0.85` → pattern is eligible to be promoted to L7-compound in the next cycle's audit.

## Per-dept catalog templates

### Legal (Vera Jr / Eleanor Jr): DP-12 checklist catalog

The 12 standard checklist items for legal entities. Pick any 3 per entity:

1. Confirm processor contract meets Art. 28(3) clauses
2. Confirm security TOMs align to Art. 32 (CIA + resilience)
3. Trigger Art. 33/34 breach playbook for any incident within 72h
4. Anchor data-subject rights in recital-level framework
5. Document TOMs with citation-backed academic evidence
6. Establish tenant isolation architecture in DPA
7. Implement verifiable compliance evidence (third-party attestation)
8. Establish sector-specific TOMs for IoT/connected-device processing
9. Document legitimate interest balancing for surveillance-adjacent processing
10. Establish cross-border transfer mechanism (SCC/DPF/BCR)
11. Establish GRC framework with named roles + risk register
12. Establish compliance ROI tracking with board reporting

### Legal: 5-template contract variant catalog

Pick any 3 per entity:

1. **MSA** — Master Service Agreement (controller-controller or controller-processor)
2. **DPA** — Data Processing Addendum (Art. 28(3) compliance)
3. **JCA** — Joint Controller Agreement (Art. 26)
4. **SCC** — Standard Contractual Clauses (2021 modules for cross-border)
5. **SUB** — Sub-processor Onboarding Addendum (downstream processor terms)

Each variant line follows the format: `<CODE> — <Name> (<context>)` + `*Parties: ...*` clause with party roles, liability cap, governing law, and one optional special clause.

## Filename conventions

- Entities: `<kind>-<identifier>-<cycle-token>-<TS>.md` (e.g. `legal-art-5-gdpr.md`, `legal-work-W2938574745-compliance-compound-1783387873.md`)
- Patterns: `<dept>-topic-<slug>-<cycle-token>-<TS>.md` (e.g. `legal-topic-recitals-framework-compound-1783387873.md`)
- The cycle-token distinguishes cycle-1 from cycle-2 artifacts in the same directory

The timestamp suffix is optional but recommended for compound cycles — it lets you `ls *compound-<TS>*` to find all artifacts from one cycle.