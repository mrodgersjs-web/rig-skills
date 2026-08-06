# Source Intake-Gap Handling (Verified Silence vs. Unscanned)

A cycle report MUST distinguish **checked-and-empty** from **not-checked**. Conflating the two leads downstream sessions to either waste work rescanning a known-silent source or trust unstated evidence about one they never checked at all — both break proof integrity.)

## What is verified silence?

The cron visited the source in this cycle, applied the window/filter it would use for extraction today's cycle), and the result contained zero extractable entities/topics. Evidence recorded on disk (proof entry + report line with timestamp). The contract §9 "use a builder script" does NOT change: when checked-and-empty yields no new substrate, you seal proof showing `checked_empty_source` = [source-url], 0 writes, verifier gate runs against whatever was produced this cycle — including the empty set]. Freshness floor is per-dept per-cycle; one silent cycle doesn't break compounding. Future cycles still re-check (the source may produce later), today's seed pool stays what it is.)

Real case: data dept 2026-07-07, pgvector commits window Jul 1–8. GitHub page showed "No commits history"; verified empty with commit-window URL in report. Correct handling — not an error, but a verified finding that must be logged so the next agent doesn't think the scan was skipped.)

## What is a NOT-checked? Source A returns nothing; due to failure/restart/missing tool, you never visit source B. The proof MUST leave source B absent (not marked as empty). Why: tomorrow's session sees "source A checked-empty; source B not listed" and knows exactly what still needs checking. Marking unchecked source as verified empty would suppress the re-check — that's a cover-up by omission.)

## Writing it in proof/report

- Cycle report line per source, e.g.:
  pgvector (checked Jul 1–8 on repo commits → zero new; openalex works search?search=… retrieved none this cycle). One checked-and-empty is "no signal this cycle." Unretrieved sources are a gap — don't state the gap as fact.

- Proof.json fields to carry:
```jsonc{intake_check": {checked_sources: [{url, window_or_filter, visited_at, result_summary}],unchecked_sources: [url...]}  ← verified_empty list of urls that were checked-and-empty THIS cycle only — next cycle they go back unchecked unless intentionally persisted)

- Report tone rule: write evidence, not excuses. "pgvector commit log Jul1–8 showed No commits history" is correct; "scan skipped due to compression fallback" in proof is wrong (the failure reason explains why you didn't scan; it doesn't make the source empty — mark it unscanned instead).

## Overclaiming recovered counts after session loss

Context-compression can lose intermediate entity scorecards/cycle log content. A prior turn may have written a cycle-log JSON showing N entities ingested, but this window cannot re-read or verify that file against vault/pgvector state — you CANNOT safely cite those counts as "done" in today's report either. Correct moves: 1) note the unverified number with caveat ("a previous session observed X, unverifiable here"), 2) defer durable writes until user-session with vault/profile access can confirm what already lives there (Gate-D), and 3) log the intake gap explicitly so the operator isn't flying blind when resuming.)

## Cross-ref
- Class skill SKILL.md §9 source preservation/scan discipline + "verified silence" added in this cycle's patch; blocklist false positive fix is `blocklist-word-boundary.md`; verifier shape contract is `dept-verifier-gate.md`.)