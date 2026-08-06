# Agent-Mode Content-Drafter Cron — Multi-Artifact Drafts, STAGED Behind Gate-D

The pattern for a **cron job whose job is to produce multiple text drafts per cycle and write them to a proof file, but never act outward** (no publishing, no sending, no commenting live). The cron is a Doer that STAGES — the human (or a downstream cron) decides what ships.

This is a sibling of the Doer/Checker/Validator content-gen pattern in `staged-output-idempotency.md` and the staged-engagement pattern in `staged-engagement-cron.md`, but distinct in three ways:

| Pattern | Output shape | Selection step | Outward action |
|---|---|---|---|
| `staged-output-idempotency.md` (#8) | N variants per topic, top-3 selected | YES (model picks best) | None — drafted and selected |
| `staged-engagement-cron.md` (#10) | Manifest of intended actions | NO — every entry is a plan to act | HELD — `actions_executed: 0` |
| **This pattern (#12)** | N value-add drafts (5–10) | NO — every draft stands on its own | HELD — `gate_d_status: STAGED` |

When #12 fires, the cron produced multiple artifacts where each one is independently usable. There's no "pick the best 3" — the human reviews the batch and approves per-artifact (or rejects the whole batch).

## When this fits

- A cron fires 3x daily (am/pm/eve) and drafts 5–10 LinkedIn comments / reply threads / hook variants / DM openers for the human to review
- Each draft is a complete, shippable artifact
- The cron's job is to populate a queue, not to decide which to ship
- A downstream cron (or the human) reads the proof file, picks, and acts
- Gate-D authority sits with the human, not the cron

Examples: LinkedIn comment-writer (Ralph's dept), hook drafter for content engine, DM opener drafter for cold outreach, reply-thread drafter for engagement ops.

## The schema that survives

Top-level shape:

```json
{
  "agent_id": "<dept>-<function>",
  "agent_name": "<Human-Readable Name>",
  "anti_generic_score_target": ">=80 internal / >=85 public-facing",
  "banned_words_audit": "PASS — none of [<word>, <word>, ...] appear in any draft",
  "batch": "<am|pm|eve>",
  "comment_count": 8,
  "comments": [
    {
      "comment_id": "am-c01",
      "rank": 1,
      "target_post_type": "<what the host post is about>",
      "target_post_topic_guess": "<narrower guess>",
      "value_add_type": "<insight|data|question|combination>",
      "anchored_to": {
        "pattern_ids": ["<id>", ...],
        "use": "<one-line: which fact, applied how>"
      },
      "no_agreement": true,
      "voice_check": "PASS",
      "human_like_delay_pre_post_s": 87,
      "comment_text": "<the draft>"
    }
  ],
  "created_at": "<iso8601>",
  "cron_window": "<am|pm|eve> (<HH:MM MT>)",
  "gate_d_status": "STAGED — no publishing without <human> Gate-D approval",
  "next_action": "Await <next batch>",
  "proof_path": "<absolute path>"
}
```

### Per-draft value-add taxonomy

Every draft must satisfy AT LEAST ONE of:

1. **Adds a unique insight** — a mechanism, a counter-pattern, a non-obvious distinction that the host post did not make
2. **Cites a specific data point** — a number, a stat, a named study, an internal benchmark
3. **Asks a thought-provoking question** — not a softball, not a yes/no, but one that reframes the discussion

Bare agreement, generic praise ("Great post!"), and "I learned a lot from this" filler are **banned** by definition. The `no_agreement: true` field is asserted per draft, not derived — if the cron can't truthfully assert it, the draft doesn't ship.

### Pattern anchoring (the L4 substrate link)

Every draft's `anchored_to` field cites a specific `audience_patterns.json` (or equivalent semantic-layer) fact by its `pattern_id`. This is what makes the drafts *defensible* in a content review: "Why did you write this?" → "Because pattern 7e9e93537f4c says X, and the host post is implicitly arguing not-X."

```json
"anchored_to": {
  "pattern_ids": ["7e9e93537f4c", "7ab4597d849f"],
  "use": "specific-number stat + agent-content 3-5x engagement multiplier"
}
```

The cron that drafts comments should READ the semantic layer (`memory/semantic/*.json`) before drafting, the same way a researcher reads source material. Drafts that don't anchor to a pattern are opinion.

## File naming and idempotency

`{proof_dir}/{cadence_dir}/{agent_short}_{batch}_{YYYY-MM-DD}.json` — e.g. `proof/daily/comments_am_2026-07-07.json`.

- The **batch label** (`am` / `pm` / `eve`) is part of the filename, not a separate column. It tells the consumer which slot the batch belongs to.
- The **date** is the run date, not the post date. Multiple batches per day → multiple files per day.
- **No overwriting on the same (batch, date) tuple.** The stage-aware guard from `staged-output-idempotency.md` rule #7 applies: if the file exists and is well-formed, return `[SILENT]`. The cron's job is to populate a missing slot, not to fight a prior successful run.

Quick guard at the top of the cron:

```python
from pathlib import Path
import json

p = Path(f"proof/daily/comments_{batch}_{date}.json")
if p.exists():
    data = json.loads(p.read_text())
    if data.get("comment_count", 0) >= 5 and data.get("gate_d_status", "").startswith("STAGED"):
        return "[SILENT]"  # already drafted, don't re-run

# Optional: also check whether downstream picked anything up
# (e.g. a `picked_count` field set by a human-reviewer cron)
if data.get("picked_count", 0) > 0:
    return "[SILENT]"  # human has reviewed; do not regenerate
```

The `picked_count` discipline is a separate cron (or human action) that writes the field back into the same proof file. Once the human has picked, regenerating destroys the human's selection state — same lesson as the staged-output rule.

## Voice + banned-word audit (run AFTER writing, not during)

The single most common cron-mode failure in this pattern: drafting "in voice" without a final audit step, and shipping a comment that contains a banned word. The audit is a post-write mechanical check, not a thinking-time habit. The flow:

1. **Draft** all comments in one batch (single LLM pass is fine).
2. **Write** the JSON proof file.
3. **Re-read** the proof file and run the audit:

```python
import json
from pathlib import Path

p = Path(f"proof/daily/comments_{batch}_{date}.json")
data = json.loads(p.read_text())

banned = ["unlock", "empower", "synergy", "leverage", "disrupt", "hustle"]
hits = []
for c in data["comments"]:
    txt = c["comment_text"].lower()
    for w in banned:
        if w in txt:
            hits.append((c["comment_id"], w))

if hits:
    # Patch the offending draft(s) in place, then re-write.
    for cid, w in hits:
        for c in data["comments"]:
            if c["comment_id"] == cid:
                # Replace banned word with a neutral synonym.
                # ... (rule per banned word)
    data["banned_words_audit"] = f"PASS after fix: {[(c,w) for c,w in hits]}"
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
```

4. **Update** the `banned_words_audit` field honestly: "PASS" if no hits, "PASS after fix: [...]" if any drafts needed patching, "FAIL — re-draft" if patching wasn't enough.
5. **Only claim done** after the re-read shows `banned_words_audit: PASS*` and `comment_count == len(comments)`.

This is the same discipline as the voice-check field on every draft. A `voice_check: "PASS"` field that the cron asserted without re-reading is a lie.

## The `human_like_delay_pre_post_s` field (silly but useful)

Each draft carries a `human_like_delay_pre_post_s` integer (typically 60–150 seconds). The number is what a human reviewer would mentally set as the pre-publish wait time — "if I were going to post this, would I post it 90 seconds after reading the host post, or 5 minutes?"

The field is a forcing function for the cron to model human pacing, not a literal sleep duration. If the cron's drafts all carry the same number (e.g. 60s for every draft), the cron is rushing; if they vary appropriately (78, 87, 102, 109, 115, 124 across 8 drafts), the cron is pacing like a human.

## Gate-D discipline

The proof file's `gate_d_status` field is the single source of truth for whether the drafts are armed:

| Status | Meaning | Downstream behavior |
|---|---|---|
| `STAGED` | Drafts written, no human action yet | Downstream picker waits |
| `PICKED` | Human approved N drafts | Downstream may post those N |
| `REJECTED` | Human rejected the whole batch | Downstream drops the file |
| `EXPIRED` | Drafts > 24h old and not picked | Cron may regenerate fresh batch |

A cron that switches the status to `PICKED` on its own is a Gate-D violation. Only the human (or an explicitly human-approved cron) flips the status.

## Anti-patterns

- **Drafting without anchoring.** Every draft must cite a pattern_id. Drafts that don't anchor are opinion and will be rejected at review.
- **Running the banned-word audit in your head during composition.** Always run it as a mechanical post-write check. The thinking-time check is unreliable.
- **Setting `gate_d_status: PICKED` "to make progress."** The whole point of the STAGED discipline is that the cron never arms its own output.
- **Regenerating on a slot that already has drafts.** The stage-aware guard returns `[SILENT]`. The cron's job is to populate missing slots, not to fight the human's review state.
- **Batching all 5–10 drafts as a single LLM response with identical structure.** The drafts are diverse by design (different post archetypes, different value-add types, different anchors). If they read as variations on a template, the cron has slipped into a pattern that the audience will recognize.
- **Forgetting the date in the filename.** A `comments_am.json` (no date) is unauditable. The date is the cycle identity; the batch is the slot within the cycle.
- **Writing `gate_d_status: ""`** instead of an explicit `STAGED`. An empty field is undecidable; the consumer will treat it as "not yet staged" and wait forever.

## Worked example: comment-writer cron, 3x daily

A scheduled cron at 12pm, 3pm, 6pm MT:

1. **Load agent definition** from `agents/functional/comment-writer.json` (or equivalent role file).
2. **Read semantic layer** from `memory/semantic/audience_patterns.json` (or dept equivalent). Get 8–10 patterns.
3. **Draft 5–10 comments** — one per target post archetype, each anchored to 1–2 pattern_ids, each carrying a unique value-add (insight / data / question). Vary the archetypes across batches so am/pm/eve don't repeat the same 8 posts.
4. **Run the voice + banned-word audit** on the draft set in Python. Patch any hits in place.
5. **Write the proof file** to `proof/daily/comments_{am|pm|eve}_{YYYY-MM-DD}.json`.
6. **Return a short report** (not the JSON). The cron system delivers it to the operator; the operator reads, picks, and (separately) arms selected drafts for posting.

The cron's report is short: batch, count, banned-word audit result, file path, "STAGED" status. The human reads the proof file directly, not the cron report.

## See also

- `staged-output-idempotency.md` — for content-generation crons that also have a selection step
- `staged-engagement-cron.md` — for crons that plan outward actions, not drafts
- `read-only-analytics-cron.md` §"Cron-mode runtime constraints" — for the execute_code + pipe-to-interpreter blocks that apply here too
- `write-file-json-escape-pitfall.md` — for the `write_file` JSON-escape failure modes that the drafter cron's payload is most likely to hit
