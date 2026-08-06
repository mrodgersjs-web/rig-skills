---
name: rig-corpus-distillation-pipeline
description: Distill a primary source corpus into RIG assets.
---

# RIG Corpus→Distillation Pipeline

The pattern for taking a primary source corpus (transcript, scraped
docs, internal knowledge graph, curated content) and producing a complete
set of RIG assets — skills, doctrines, harnesses, L10 rules, plus a
single "load at session start" umbrella skill — with full provenance
back to the source.

## Why this class of work exists

Mike asks to "extract [course/transcript] into RIG assets" or "build a
skill the agent loads every session." The naive answer is to read each
source file and write a SKILL.md per item. The right answer is a 4-stage
pipeline that:

1. Produces a discoverable raw artifact store (full provenance + hashes)
2. Distills via a classification table that maps source phrases to
   existing RIG assets (avoiding duplication)
3. Writes the narrowest-correct asset type per technique (rule vs
   harness vs skill vs doctrine)
4. Seals a single ProofPacket that documents every gate

The pipeline is fully reproducible (pkill-safe, idempotent, retry-aware)
and re-runnable when the corpus grows — appending new content re-runs
only the new tail.

## The 4-stage pipeline (proven: agentic-coding-school 2026-07-29, 165 assets)

### Stage 1: Manifest scrape + raw artifact store

Goal: produce a per-source-class manifest with deterministic content
hashes. Surface: discovered URLs, lesson titles, durations, videoIds,
downloads, external links.

```bash
# Output schema per lesson:
{
  "videoId": "uuid",
  "slug": "class-slug",
  "pageTitle": "...",
  "publishedDate": "...",
  "lessons": [{"name": "...", "duration": "..."}],
  "downloads": [{"label": "...", "url": "...", "type": "pdf|zip|md"}],
  "externalLinks": [{"href": "...", "text": "..."}],
  "relatedVideos": [{"text": "...", "videoId": "..."}]
}
```

Persist per-lesson JSON + per-lesson receipt (`.receipt.json`) under
`<RAW>/lessons/<videoId>.json`. Every receipt has the source URL,
fetch time, engine, engine version, content hash, and run_id.

**Tooling:**
- Authenticated scrapes: `ego-browser` (inherits Mike's session; perfect
  for Skool-style sites). Pattern documented in the agentic-coding-school
  distillation scripts.
- Open scraping: `rig-scrape` gateway + `rig-scraper` CLI.
- HTTPS-only, robots-respecting, byte/time caps, 5GB/day artifact budget.

### Stage 2: Per-source body extraction

For every entry in the manifest, fetch the body content. For video
lessons, this means the page DOM (title, description, dates, related
videos, downloads). For text corpora, the full text.

Output schema per source:
```
{
  "pageTitle", "pageUrl", "videoId",
  "videoTitleInPlayer", "publishedDate", "updatedDate",
  "chapterOutline": [{"heading", "lessons": [{"name", "duration"}]}],
  "downloads": [...],
  "externalLinks": [...],
  "relatedVideos": [...],
  "bodyTextLength", "htmlSize", "scrapedAt"
}
```

**Critical pitfall (ego-browser JS expression wrapping):** the `js()`
helper auto-wraps source in `(function(){...})()`. Top-level `return`
triggers the wrap; intermediate `const` declarations cause TDZ errors
against the trailing object expression. Use single-object-expression
form with no `return`, no top-level `const`, no helpers-as-IIFEs. When
the source is wrapped in another IIFE, the JS evaluates to `null` —
the symptom is empty results.

### Stage 3: Distillation (the classification table)

Every named technique from the corpus gets classified into one of:
- **Existing RIG asset** (no write — patch the existing skill instead)
- **L10 rule** (mechanical constraint, e.g. "stay under 50% context")
- **Goal harness** (recurring loop with gates + kill switch)
- **SKILL.md** (novel procedure)
- **Doctrine** (novel axiom or guardrail)

The classification table is a Python dict mapping source phrases to
canonical RIG assets. Build it from the existing skill index before
writing a single new asset. Example:

```python
EXISTING = {
    "scout, worker, synthesizer": ("tac-scout-worker-synthesizer", "skill"),
    "compaction": ("tac-context-engineering", "skill"),
    "plan mode": ("tac-context-engineering", "skill"),
    "headless": ("tac-headless-automation", "skill"),
    # ... 50+ entries
}
```

The classifier matches case-insensitively on substrings. A technique
that doesn't match any EXISTING entry is "new" and gets a fresh asset
in the narrowest correct type.

### Stage 4: Asset write + umbrella + ProofPacket

For each new technique, write the asset to its canonical RIG path:

```
SKILL.md  →  /Users/rig128gb/.hermes/skills/<slug>.md
harness  →  /Users/rig128gb/.jake/goal-harnesses/<slug>.md
doctrine  → /Users/rig128gb/.rig/agent-doctrine/<cat>/<slug>.md
L10 rule → /Users/rig128gb/rig-l10/rules/<slug>.toml
```

Every new asset includes frontmatter that cites the source URL +
run_id + (for skills) what existing skill it replaces or extends.

**The umbrella skill** is the single most important deliverable. It
sits at `~/.hermes/skills/<corpus>-doctrine.md` and is loaded at session
start. It indexes:
- The canonical L10 rules (with their IDs)
- The most-cited techniques (top 7 by frequency)
- The novel platform-specific gaps (top 7 new assets that don't
  duplicate existing)
- The "what we learned" doctrine (5 things the corpus taught us that
  RIG didn't previously encode)
- The session-start posture (load this skill + the 5 rules + the
  umbrella)

The ProofPacket is sealed at `proof.json` with:
- All changed-asset paths + sha256 hashes
- All gates (manifest scrape, body extraction, distillation, no-secret-leak)
- An honest verdict (typically "done = all(blocking_gates_pass) = TRUE")
- A timestamp

The validation gate is: `validate_<corpus>.py` should report 33/33 PASS
(or whatever the count is) on the validator's structural checks.

## The 5 canonical rules the corpus typically teaches

The agentic-coding-school corpus distilled 5 novel rules that RIG didn't
previously encode as L10 rules. Beyond this specific run, any large
practical-corpus distillation is likely to surface similar mechanical
rules. The expected shape:

1. A context-budget rule (e.g. "stay under 50% context usage")
2. A loop-discipline rule (e.g. "every loop has kill switch + cooldown + verifier")
3. A multi-agent decomposition rule (e.g. "scout/worker/synthesizer")
4. A verifier-independence rule (e.g. "builder ≠ verifier")
5. A persistence-across-resets rule (e.g. "bug fixes write to file")

Codify all 5 as L10 rule TOMLs under `~/rig-l10/rules/acs-*.toml`. They
become enforceable by the RIG loop infrastructure.

## The "session-start umbrella" pattern

The umbrella skill's frontmatter must declare:
- The 5 canonical rules by ID
- The 7 most-cited techniques (with the existing skill that covers
  them, or the new skill that fills the gap)
- The 7 novel platform-specific gaps (new assets the corpus contributed)
- The summary of what the corpus taught (5 takeaways)
- The "what we can do now" implications for the operator

Without the umbrella, the new assets are invisible to the agent. With
the umbrella, the agent loads it at session start and the rules +
techniques are top-of-mind.

## When to load this skill

**Load this skill when:**
- Mike asks to extract a course / book / transcript into RIG
- A new corpus is being added (e.g. a new YouTube channel, a new internal
  wiki, a new book)
- The agent is about to write its 5th+ new skill from a single source
  (the threshold where manual triage becomes wasteful)
- A previous distillation run's output needs to be re-run (the pipeline
  is idempotent; append-only)

**Don't load for:**
- Single-skill authoring (use the relevant existing skill)
- Knowledge graph curation (use rig-knowledge-stack)
- Reading and summarizing a single doc (use intel-swarm)
- One-off Q&A about a corpus (use the umbrella of the existing corpus)

## Re-runnability

The pipeline is designed to be re-run when the source grows:

- `extract_lessons.py` skips sources already with a `.json` artifact
- `distill_v3.py` skips assets that already exist with newer mtime
  than the source lesson
- The classifier (EXISTING dict) is append-only — new entries can be
  added without breaking old ones
- The validator is idempotent — running it twice produces the same PASS/FAIL

The entry point for a re-run is:

```bash
# Re-runner, safe to invoke when the source has added new content
python3 scripts/extract_lessons.py    # skips existing lessons
python3 scripts/distill_v3.py        # skips existing assets
python3 scripts/validate_q.py        # always idempotent
python3 scripts/seal_proof.py        # re-seals with the new hash
```

## Pre-write checklist

Before writing the first new asset:

- [ ] Read the canonical RIG skill index (`ls ~/.hermes/skills/` + grep)
- [ ] Build the EXISTING classification table from existing skills
- [ ] Decide the narrowest-correct asset type per technique (rule vs
      harness vs skill vs doctrine)
- [ ] Write the umbrella skill's SKILL.md structure FIRST (the index
      the agent will load at session start)
- [ ] Then write the individual assets (skill, doctrine, harness, rule)
- [ ] Persist every asset with a `source:` + `run_id:` + `class:` + `chapter:`
      frontmatter for traceability

## Post-write checklist

- [ ] Every new asset has a source URL + run_id in its frontmatter
- [ ] Custom validator (e.g. `validate_q.py`) reports 33/33 PASS (or your
      count) on the structural checks
- [ ] ProofPacket sealed with all asset hashes + gates + verdict
- [ ] No secret leaks (auth tokens, cookies, signing certs) in any artifact
- [ ] Umbrella skill installed at `~/.hermes/skills/<corpus>-doctrine.md`
- [ ] `obsidian-memory-bridge closeout` committed the run to JakeStudio

## Related Skills

- `rig-scrape` — open-source scraper fleet (LAN-first; doesn't cover
  authenticated scraping)
- `gated-course-scrape` — chrome-CDP over a fresh user-data-dir for paid
  course scraping (used when ego-browser isn't suitable)
- `ego-browser` — Nicolas Beaumann's Chromium browser designed for AI
  agents; inherits Mike's session; the right tool for authenticated
  scrapes of Skool-style sites
- `rig-doctrine-reality-audit` — pitfall #15 captures the OpenSpec
  proposal-vs-spec-folder mismatch that fires in stage 4
- `rig-knowledge-stack` — GBrain + JakeStudio Obsidian + cross-harness
  MCP wiring (the substrate the new assets write into)
- `rig-content-interview-pipeline` — alternative distillation pattern
  for synchronous human interviews (triple-publish to substrate + Obsidian
  + GBrain)

## References

- `references/agentic-coding-school-2026-07-29-run.md` — the canonical
  worked example of this pipeline. 165 RIG assets produced from 138
  unique lessons over 12 classes. Includes the EXISTING classification
  table, the 5 canonical rules as TOML files, the umbrella skill
  template, and the lessons-learned doctrine. Load this when you're
  about to start a new distillation run.
- `references/ego-browser-js-expression-wrapping.md` — the single
  critical pitfall that bit us in stage 2 of the acs run. Use before
  writing any ego-browser scraper that uses the `js()` helper.

## Source

This skill emerged from the 2026-07-29 agentic-coding-school
distillation run (`acs-20260729T183655Z`), which produced 165 RIG assets
from 138 unique lessons across 12 classes in a 4-stage pipeline. The
pattern is reusable for any primary-source corpus → RIG asset
distillation.