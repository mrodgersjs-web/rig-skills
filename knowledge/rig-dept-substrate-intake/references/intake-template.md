# DIGEST.md Template (RIG department-substrate intake)

This is the canonical template for `DIGEST.md` in any RIG dept-substrate intake.
Adapt the section headings as needed for the source type (YouTube vs blog vs
paper), but keep the overall structure.

---

```markdown
# DIGEST — `{source_id}`

**Source:** {canonical_sanitized_url}
**Sanitized URL note:** {describe any tracking tokens dropped, e.g. "Original URL carried ?is=ABC123, dropped per substrate protocol."}
**Creator:** {name} ({handle}) · {channel_or_publication} · {any_other_links}
**Title:** "{exact title as published}"
**Length:** {human_duration} ({seconds} s) · upload {YYYY-MM-DD} · ~{view_count} views · {like_count} likes · {follower_count} subs
**Ingested:** {ingested_at_iso8601}
**Ingestion path:** {which tool path was used; e.g. "yt-dlp --write-info-json --write-auto-sub (succeeded on first attempt; youtube-transcript-api fallback NOT triggered)"}

---

## Verdict

{One sentence: useful / filler / blocked. Use 'blocked' if ingestion failed and write a `blocker` field in intake.json explaining.}

---

## Classification

| Field | Value |
|---|---|
| Topic | {2-5 words, plain language} |
| Framework acronym | {if the source names one; e.g. PACE} — {expansion} |
| Primary dept | {gtm / sales / linkedin / content / research} |
| Secondary depts | {list, or "none"} |
| Verdict | useful / filler / blocked |
| Transcript size | {N chars / N words} |

---

## Why it's useful (dept-by-dept)

For each relevant dept, one bullet explaining what the intake feeds. Be concrete:
- which framework / pattern
- which downstream artifact (linkedin post, carousel, battlecard, framework PDF)
- which kind of client conversation it informs

If only one dept is relevant, write a single bullet.

---

## Top {3-8} quotable lines

1. "{verbatim or lightly-cleaned quote}" — {timestamp if available}
2. ...
3. ...

When cleaning ASR errors (e.g. `mid8` → `mid-8`, `saskcam` → `saascamp`), note
the cleanings in the "Things to verify" section. Don't pass cleaned quotes off
as verbatim unless you can listen-confirm them.

---

## Framework anatomy (if the source names one)

ASCII box showing the steps in order, e.g.

```
┌────────────────────────────────────────────────────────────────────────┐
│ PACE — order matters. Skip a step, you stall.                          │
│                                                                        │
│  1. PAIN       Define the specific painful urgent problem you solve.   │
│  2. AUDIENCE   ...                                                    │
│  3. CHANNEL    ...                                                    │
│  4. EXPANSION  ...                                                    │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Failure modes {creator} calls out (cheap to lift)

| Failure mode | Frame to use it in |
|---|---|
| ... | ... |

This is the table the dept substrate wants most — concrete, attributable,
re-routable.

---

## Things to verify (next cron pass)

- **Quote accuracy** — which cleaned quotes should be listen-confirmed before citation
- **Stats** — which numbers need external verification before being cited
- **Companion videos / sources** — which linked references should also be ingested

---

## Follow-up cron recommendation (NOT created yet — awaiting approval)

This section proposes the next-stage pipeline. DO NOT ACTIVATE THE CRON. Write
the proposal here; activation is a separate step requiring skill-spec ratification.

**Goal:** {1 sentence describing what the cron extracts}

**Proposed job name:** {`{dept}-{artifact-type}-extractor`}

**Schedule:** {cron expression + timezone, e.g. "daily 04:30 local, batched"}

**Source:** {which dir to scan, e.g. raw intake tree}

**Output:** {target path + format, e.g. "derived/quotable-frames.jsonl, one frame per line"}

**Per-row schema:** {field list, e.g. `source_video_id`, `frame_type`, `verbatim_quote`, `dept_relevance[]`, `embedding_hash`, `ingested_at`}

**Companion pass:** {name + schema for the second pass}

**Why it's worth scheduling (not just one-shot):**
1. {reason — usually intake volume + dedup necessity}
2. ...
3. ...

**Blocker to schedule:** {what needs Darius / dept-lead sign-off before activation; e.g. "skill specs at $HOME/.rig/departments/{dept}/skills/proposed/{name}/SKILL.md need ratification"}

---

## Files written (this intake)

| Path | Purpose |
|---|---|
| `intake.json` | Structured metadata + classification (machine-readable) |
| `DIGEST.md` | This file (human-readable) |
| `transcript.txt` | Cleaned plain-text transcript (N words, dedup pass + phrase-collapse pass) |
| `transcript_timestamped.txt` | All N cues with timestamps, consecutive-dup cues collapsed |
| `transcript_paragraphs.txt` | Same plain text re-chunked into ~700-char paragraphs for skim-read |
| `{video_id}.{ext}` | Raw input from {source tool} (untouched) |
| `{video_id}.info.json` | Raw metadata dump (untouched) |
| `_*.py` | Cleaner passes — kept for re-runs |

All artifacts under:
`{absolute_path_to_intake_folder}`

---

## Status

- ✅ {tool} fetched {what it fetched}
- ✅ transcript cleaned (N w / N chars)
- ✅ classification emitted
- ✅ `intake.json` written
- ✅ DIGEST.md written
- ⏸ follow-up cron (NOT scheduled — proposal only)

**next_action: schedule_cron** *(pending {dept-lead} approval of the {N} proposed skill specs)*
```

---

## Section-by-section guidance

### "Verdict"

One short paragraph. Useful / filler / blocked. If blocked, this is where you
say *what* blocked and *why* (rate-limit, network, transcript-disabled).

### "Classification"

The 7-row table is mandatory. Don't skip the framework row — leave it blank
if the source doesn't name one.

### "Why it's useful (dept-by-dept)"

Each dept gets a bullet. The bullet must answer: **"what downstream artifact
does this intake feed, and which conversation does it inform?"** Vague
"could be useful for content" is worse than no bullet.

### "Top quotable lines"

3-8 lines. Aim for: memorable phrasing, concrete claims (numbers, scenarios),
and quotable framings the substrate can reuse verbatim or with minimal edit.

### "Framework anatomy"

Skip if the source has no framework. When present, ASCII box > bullet list —
the box renders cleanly in TUI and prints legibly in chat.

### "Failure modes"

This is the highest-value table for substrate users. Concrete failure modes
+ where to apply them = the substrate pays for itself.

### "Things to verify"

Honest list. Quote cleanings, stats, companion videos. Don't omit — the next
session needs to know what wasn't verified.

### "Follow-up cron recommendation"

The parent prompt almost always says "don't create the cron yet; just write
the recommendation to the digest". Honor that. The proposal must include:
source dir, output dir, target schema, skill specs to ratify. Activation is a
separate step.

### "Files written"

Self-explanatory table. The absolute path at the bottom is the link back to
the artifact set.