# Classification guide — how to fill intake.json

This guide turns the raw transcript into the structured `intake.json` fields.
The dept-routing matrix at the end is the canonical answer to "which dept?"

## `verdict` — useful / filler / blocked

**`useful`** — the source contains at least one of: a named framework,
specific numbers, a concrete client anecdote, a quotable line, an attributed
failure mode. ~70% of YT creator content falls here for the GTM dept.

**`filler`** — the source is recognizable content but adds nothing not already
in the substrate. Generic founder pep-talk, obvious advice ("focus on the
customer"), motivational framing with no specifics. Still ingest — but tag
as filler so downstream agents don't elevate it.

**`blocked`** — ingestion failed and the artifact set is incomplete. Tag in
intake.json AND in DIGEST.md. Don't mark "useful" just because you got part
of the transcript.

## `primary_dept` — pick ONE

Use the dept-routing matrix below. When a source crosses 3+ depts, primary is
the one that gets the framework or main thesis, not the secondary applications.

## `target_dept` — pick all that apply

Almost always > 1. A founder-level GTM video is gtm-primary but has sales
application, linkedin application, content application. List all.

## `useful_for` — concrete, not aspirational

Each bullet must name a specific downstream artifact or conversation. Bad:

- "could be useful for content marketing"

Good:

- "Content dept substrate: 'positioning rewrites price 10× without product change' angle — 90-second LinkedIn script + carousel"
- "Sales dept substrate: cost-of-inaction reframing for 'we can't justify the budget' objections"
- "LinkedIn dept substrate: case study on LinkedIn-account-ban risk, anchored to the '4 banned accounts' story"

Three to five bullets is the right range.

## `top_quotes` — verbatim or clearly marked

Curate 3-8 lines. Aim for variety:

- one **shocking stat** (number + scenario)
- one **framework-level claim** (the overarching thesis)
- one **attributed failure mode** (concrete scenario)
- one **reframing** (takes a familiar idea and turns it)
- one **CTA or summary line** (what the creator wants you to do)

When cleaning ASR errors, note the cleanings in DIGEST.md "Things to verify".

## `framework_acronym` and `framework_steps`

Fill when the source names a framework. The session's primary example:
PACE = Pain, Audience, Channel, Expansion. If the source names no framework,
leave both blank but still ingest.

## `next_action`

`schedule_cron` when there's a follow-up pipeline to propose (almost always).

`none` when the source is one-off / low-volume.

Free-form string for unusual cases (e.g. "manual review", "compare against
existing X framework").

## `ingestion_tool`

Note which path was used. If yt-dlp failed and youtube-transcript-api
succeeded, say so explicitly — that fact is useful for ops debugging.

---

## Dept routing matrix

| Source topic | Primary dept | Common secondary |
|---|---|---|
| B2B SaaS GTM / paid acquisition / positioning | gtm | sales, content, linkedin |
| Cold email / outbound / lead list quality | gtm | sales |
| ABM / account tiering / personalization | gtm | sales |
| Sales methodology / objections / closing | sales | gtm |
| Pricing / packaging / expansion | sales | gtm |
| LinkedIn growth / personal brand | linkedin | content |
| LinkedIn as channel / LinkedIn ads | linkedin | gtm |
| LinkedIn content format / hooks / carousels | linkedin | content |
| Content marketing / SEO / copywriting | content | linkedin, gtm |
| Newsletter / Substack / long-form | content | — |
| Founder productivity / operating cadence | (skip) | — |
| Macroeconomic / geopolitical | (skip — out of scope) | — |
| AI dev / agent building / infra | research | (varies) |

**Default when in doubt: `gtm`.** B2B SaaS substrate work routes there most
often, and gtm accepts cross-dept material as secondary.

---

## Common mistakes (real sessions)

### Calling everything "useful"

If everything is useful, nothing is. Reserve `useful` for sources that
genuinely add substrate value. Generic founder pep-talk = `filler`.

### Primary dept = "research"

There is no "research" dept in the substrate routing. If a source is purely
research / academic, classify by the dept it informs (e.g. a paper on pricing
elasticity = sales-primary), or skip the intake entirely.

### Top quotes that are summaries, not quotes

Top quotes must be lines the **creator actually said**, not paraphrases.
"Positioning can rewrite your price 10×" is a quote. "The speaker argues for
positioning-first thinking" is a paraphrase and doesn't belong in `top_quotes`.

### useful_for that doesn't name a downstream artifact

Every useful_for bullet should be answerable to "and then what?" If the
bullet ends at "useful for X", it's not concrete enough — name the artifact
(post, carousel, framework PDF, discovery doc, etc.).