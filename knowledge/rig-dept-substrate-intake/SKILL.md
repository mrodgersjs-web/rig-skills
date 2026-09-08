---
name: rig-dept-substrate-intake
description: "Canonical RIG department-substrate intake workflow. Takes a raw source (YouTube URL, blog post, podcast episode, research paper) and produces the standard intake artifact set — raw input + cleaned transcript + intake.json (structured classification) + DIGEST.md (human digest) — routed to the right department (gtm, sales, linkedin, content, research). Includes yt-dlp vs youtube-transcript-api selection, auto-sub overlap-collapse cleaning, URL sanitization, and the follow-up cron proposal pattern. Use when the parent agent delegates with 'intake this [source] for the [dept] substrate', 'classify and digest', or any variation of the substrate-ingest pattern."
platforms: [linux, macos]
---

# RIG Department Substrate Intake

## When to use

Use when the parent agent delegates a substrate-intake task. The signature is:

> "Ingest this [source] into the [dept] substrate. Capture metadata + transcript/text, classify, drop intake.json + DIGEST.md, and propose a follow-up cron."

Sources seen in practice:
- YouTube URL → GTM / sales / linkedin / content substrate
- Podcast RSS feed → research / content substrate
- Substack / blog post → content / sales substrate
- arXiv paper → research substrate
- Twitter thread / LinkedIn post → content substrate (lightweight intake)

This umbrella owns the **artifact schema and the workflow**, not the source-specific fetch logic. Source-specific fetch lives in `youtube-content` (YouTube), `source-corpus-extraction` (batch), etc.

## The canonical artifact set

Every intake drops the following into:

```
$HOME/.rig/departments/{dept}/substrate/raw/intake-YYYY-MM-DD/{slug}/
├── {video_or_source_id}.{ext}         # raw input (yt-dlp output, untouched)
├── {video_or_source_id}.info.json      # raw metadata dump (untouched)
├── transcript.txt                      # cleaned plain text (when applicable)
├── transcript_timestamped.txt          # cleaned cues with timestamps (when applicable)
├── transcript_paragraphs.txt           # chunked for skim-read (when applicable)
├── intake.json                         # structured classification (see schema below)
├── DIGEST.md                           # human-readable digest
└── _*.py                               # cleaner scripts — kept for re-runs
```

For non-YouTube sources, swap `transcript*` files for whatever the source produced (article text, paper body, etc.).

## Workflow

1. **Pick the source-specific fetch tool.** For YouTube: prefer `yt-dlp` (gives metadata + auto-subs in one call), fall back to `youtube-transcript-api` via `uv`. For blogs: `web_extract` or `curl`. For papers: arXiv endpoint.
2. **Sanitize the URL** before persisting. Strip tracking tokens (`?is=`, `&si=`, `&feature=share`, etc.) — keep only `?v=VIDEO_ID`. Record the dropped params in `url_sanitized_note`.
3. **Fetch into the dated intake folder.** Use `--write-info-json --write-auto-sub --sub-langs en --skip-download` for YouTube.
4. **Clean the transcript** with `scripts/clean_auto_subs.py` (YT) or equivalent. Verify the cleaned output is in the right word-count range for the source length (see pitfall below).
5. **Classify.** Identify: framework acronym if any, primary dept, secondary depts, verdict (useful / filler / blocked), useful_for list, top 3-8 quotable lines, next_action.
6. **Write `intake.json`** using the schema below.
7. **Write `DIGEST.md`** using the template in `references/intake-template.md`.
8. **Propose a follow-up cron** (NOT schedule it). Write the proposal into the DIGEST.md's "Follow-up cron recommendation" section. The proposal must name: source dir, output dir, target schema, and the skill specs that need ratification before activation.
9. **Verify** the artifact set: all 10 files present, transcript in the right word-count range, intake.json validates, DIGEST.md has all sections.

## intake.json schema

```json
{
  "youtube_id": "m0LcuCjx0qA",
  "url": "https://youtube.com/watch?v=m0LcuCjx0qA",
  "url_sanitized_note": "Original URL carried a privacy-tracking token (is=ABC123), dropped from the stored URL field.",
  "ingested_at": "2026-07-07T00:55:59Z",
  "title": "...",
  "channel": "...",
  "uploader_id": "@handle",
  "upload_date": "20251006",
  "length_seconds": 1835,
  "length_human": "30:35",
  "view_count": 14426,
  "like_count": 531,
  "channel_follower_count": 5450,
  "language": "en",
  "transcript_chars": 23541,
  "transcript_words": 4411,
  "classification": "B2B SaaS GTM framework: PACE (Pain, Audience, Channel, Expansion)",
  "topic": "Founder-level B2B SaaS go-to-market strategy",
  "target_dept": ["gtm", "sales", "linkedin", "content"],
  "primary_dept": "gtm",
  "verdict": "useful",
  "useful_for": [
    "GTM dept substrate: PACE framework as a 4-step diagnostic for stuck B2B SaaS GTM",
    "Sales dept substrate: cost-of-inaction objection framing"
  ],
  "top_quotes": [
    "...",
    "...",
    "..."
  ],
  "framework_acronym": "PACE",
  "framework_steps": ["Pain", "Audience", "Channel", "Expansion"],
  "next_action": "schedule_cron",
  "files_written": [
    "transcript.txt (clean, deduped plain text)",
    "transcript_timestamped.txt (raw cues, 1284 cues)",
    "transcript_paragraphs.txt (chunked readable)",
    "m0LcuCjx0qA.en.vtt (raw auto-subs from yt-dlp)",
    "m0LcuCjx0qA.info.json (raw yt-dlp metadata dump)"
  ],
  "raw_artifacts_retained": true,
  "ingestion_tool": "yt-dlp 2026.06.09 (system); youtube-transcript-api NOT needed",
  "sanitization": "Removed query-string tracking token from stored url; no PII embedded in transcript aside from creator self-disclosure."
}
```

Field semantics:
- `target_dept` — every dept this intake is relevant to (one or more).
- `primary_dept` — single most-relevant dept.
- `verdict` — `useful`, `filler`, or `blocked`. Use `blocked` if ingestion failed and write a `blocker` field explaining.
- `next_action` — `schedule_cron` if there's a follow-up pipeline to propose; otherwise `none` or a free-form string.
- `framework_acronym` / `framework_steps` — only when the source contains a named framework.

See `references/intake-template.md` for the full DIGEST.md template.

## Pitfalls (read these — they're from real sessions)

### YouTube auto-sub overlap duplication

YouTube's auto-generated captions emit **progressive-overlap cues**: each cue carries the previous cue's words PLUS the new tail. If you concatenate raw segments, a 30-minute monologue produces ~71,000 chars of garbage where words repeat 3× back-to-back.

Real session example (Denis Shatalin PACE video, 30:35):
- Raw cues concatenated: 71,071 chars (broken)
- Consecutive-dup cue removal only: 47,384 chars (still broken)
- Macro-repeat collapse + inline phrase-collapse: 23,541 chars / 4,411 words (correct)

The script `scripts/clean_auto_subs.py` handles both passes. Sanity check: a clean 30-min monologue is ~3,500-5,500 words. Anything dramatically larger = the dedup pass missed something.

### Don't fall back to youtube-transcript-api when yt-dlp is available

`yt-dlp` returns metadata + auto-subs in one call. `youtube-transcript-api` returns only transcript segments. If you fall back unnecessarily, you lose view counts, channel info, upload date — and the parent prompt usually asks for those. Reserve the fallback for actual yt-dlp failures.

### URL tracking tokens leak privacy

YouTube URLs sometimes carry `?is=ABC`, `&si=XYZ`, `&feature=share` tokens. Strip them before persisting to substrate. Keep them in a `url_sanitized_note` for traceability. Don't throw them away.

### "Mid8 figures" / "saskcam" / ASR artifacts

Auto-generated captions are noisy. When curating the top_quotes list, lightly clean obvious ASR errors:
- `mid8 figures` → `mid-8 figures`
- `saskcam` → `saascamp`
- `1 to 3 mil error` → `1 to 3M ARR`
- `cost of connection` → `cost of inaction`

But mark them in DIGEST.md's "Things to verify" section — don't present cleaned quotes as verbatim unless you can listen-confirm them.

### Don't summarize. Report verbatim.

When the parent prompt says "report verbatim everything, don't summarize", honor it. The substrate is meant to be lossless; downstream agents do the synthesis. The intake.json + DIGEST.md artifact set IS the report — write everything to disk, then echo the key facts in the chat reply.

### Don't schedule the follow-up cron

The parent prompt almost always says "don't create the cron yet; just write the recommendation to the digest". Honor that. The cron activation is a separate step that requires skill-spec ratification. The DIGEST.md proposal must name:
- Source dir (which raw intake dir to scan)
- Output dir (where derived artifacts land)
- Target schema (what fields the cron emits)
- Skill specs that need to be ratified before activation (with paths)

## Department routing matrix

| Source topic | Primary dept | Common secondary depts |
|---|---|---|
| B2B SaaS GTM / paid acquisition / positioning | gtm | sales, content, linkedin |
| Cold email / outbound / lead list | gtm | sales |
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

When in doubt, default to **gtm** — it's the most-frequent intake target for B2B SaaS substrate work, and the gtm dept accepts cross-dept material as secondary routing.

## Files in this umbrella

- `scripts/clean_auto_subs.py` — auto-sub overlap-collapse cleaner (YT VTT → clean transcript)
- `references/intake-template.md` — DIGEST.md template + per-section guidance
- `references/classification-guide.md` — how to choose `verdict`, `primary_dept`, top_quotes