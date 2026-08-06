# Comment-Reply Discovery Gate — Inbox Empty + Auth Broken

A fourth sub-class of cron work, distinct from the three recipes already in this skill:

- `staged-output-idempotency.md` — content-generation crons that write a durable, audited artifact.
- `read-only-analytics-cron.md` — read-only crons that observe external state and never touch the world.
- `staged-engagement-cron.md` — staged-engagement crons that *would* act outward (send, like, comment, connect, DM) and produce a manifest of intended actions when held.
- **This file** — comment-reply / discovery crons whose purpose is to *act* on a list of inbound comments, but the inbound list is empty (no upstream watcher staged comments) AND the auth gate is broken (the browser session can't reach LinkedIn). The right output is a **diagnostic report** with concrete recovery steps, NOT a manifest of intended replies and NOT a fabricated reply.

## When this fits

- A scheduled "Reply Specialist" cron (e.g. Ralph's Comment Reply Specialist, or any dept-cron whose job is to discover and reply to LinkedIn post comments on a 90-minute SLA) fires.
- The script named in the cron prompt (e.g. `comment_reply.py`) is a **reply-only executor** — it consumes a JSONL of comments and posts replies. It does NOT discover comments and does NOT authenticate.
- Discovery upstream is implicit: the cron prompt assumes the agent (or a sibling watcher) has already populated the inbox DB.
- The inbox DB is empty AND the auth gate is broken. The cron has nothing to reply to AND no way to discover anything.

## The two-layer diagnostic (always run both)

A no-op comment-reply cron has two independent failure layers. Run this diagnostic at the top of every cycle before attempting any reply:

```bash
# Layer 1: Inbound inbox
sqlite3 ~/.hermes/jake/ralf-department/memory/working/engagement.db \
  "SELECT COUNT(*) FROM incoming_comments;"

# Layer 2: Auth gate
python3 -c "
import json
p = '~/.hermes/skills/linkedin-studio/cookies/linkedin_cookies.json'
c = json.load(open(p))
names = [x.get('name') for x in c]
print('Has li_at:', 'li_at' in names)
print('Total cookies:', len(names))
print('Names:', names)
"
```

| Layer 1 result | Layer 2 result | Cron action |
|---|---|---|
| Inbox ≥ 1 | `li_at` present | **Normal path.** Pass the JSONL to the executor script. |
| Inbox ≥ 1 | `li_at` missing | **Auth gate blocks reply.** Even though comments are queued, the executor will fail. Hold and report. |
| Inbox = 0 | `li_at` present | **Discovery failed.** Auth works but no upstream watcher staged comments. Discovery is the agent's job (use StealthBrowser or Playwright to fetch and stage). |
| Inbox = 0 | `li_at` missing | **Both layers broken.** The exact case in this reference. Hold and report. |

## The "comment_reply.py is a reply-only executor" trap

A common cron's prompt says "Check for new comments on recent posts." That phrasing implies the script does discovery. **It does not.** The script is a JSONL-consumer. Before running it, verify its arg signature:

```bash
~/.hermes/jake/ralf-department/skills/comment_reply.py --help
```

If the script's `parser.error` says "either `--comments` or `--post-url + --text` required," it has no built-in discovery mode. The cron prompt and the script's actual capability are mismatched. The discovery step is the agent's responsibility, not the script's.

If you run the script with `--comments <empty.jsonl>` or with no arguments, it either errors or returns `{success:0, error:0, blocked:0}` — a vacuous success that hides the actual problem (no inbox, no auth).

## Postiz is not a comment source

For LinkedIn, `postiz posts:list` shows publish state and `releaseURL` (the public post URL), but `postiz analytics:post <id>` returns `[]` for engagement data. **Postiz does not surface LinkedIn comments.** The "Alfred Monitor comments" agent's prompt that says "Check Postiz for recent post engagement" is misleading — Postiz is a scheduler, not a comment store.

To discover comments, the agent must use the StealthBrowser (the same auth that requires `li_at`) or a separate comment-scraper. There is no passive comment-discovery source.

## The `li_at` cookie — what it is and how to recover it

`li_at` is LinkedIn's primary authentication cookie. Without it, every LinkedIn request is redirected to login. The cookie file lives at:

```text
~/.hermes/skills/linkedin-studio/cookies/linkedin_cookies.json
```

A valid LinkedIn session typically has 8-10 cookies. The required one is `li_at`. Common cookie sets without `li_at` (e.g. only `JSESSIONID`, `lang`, `bcookie`, `bscookie`, `lidc`, `sdui_ver`, `timezone`, `__cf_bm`) indicate the session was captured at a redirect or before auth completed.

**Recovery is manual.** No automated path can produce `li_at` without a fresh browser session. The ralf-department doctrine (per `cron_runs.log`):

> "No automated path can produce li_at without a fresh browser session. Manual LinkedIn login required to refresh li_at and unblock all four engagement lanes (replies, connections, likes, DMs)."

To refresh:

1. Open LinkedIn in a real browser (Chrome/Safari on the Mac).
2. Log in with the Mike Rodgers account.
3. Export cookies via a browser extension (EditThisCookie, Cookie-Editor, etc.) in JSON format.
4. Write/merge into `~/.hermes/skills/linkedin-studio/cookies/linkedin_cookies.json`.
5. Verify with the Layer 2 diagnostic above.
6. The next cron cycle should clear the gate.

## What the cron should output (instead of fabricating)

When both layers are broken, the right output is a **diagnostic report**, not a reply, not a manifest. The report has four sections:

1. **Discovery** — what recent posts exist (from `postiz posts:list`), their publish dates, whether any fall in the 2-hour window.
2. **Inbox check** — `SELECT COUNT(*) FROM incoming_comments;` and the result.
3. **Auth gate** — cookie names, `Has li_at: <bool>`, the count of missing required cookies.
4. **Recommended action** — one specific human step (refresh `li_at` via manual login), not a wishlist.

Use the `cron_runs.log` line format if your cron writes one (e.g. `[ISO] cron <name> | status: no-op (<reason>) | <evidence> | actions=0/0/0/0 | <lane1/lane2/...> | reason: <one sentence>`).

## Worked example: Ralph's Comment Reply cron, 2026-07-09 04:34 UTC

**Cron observes at start:**

```text
postiz posts:list (last 2h window)        → 0 PUBLISHED posts in window
postiz posts:list (last 24h)              → 2 PUBLISHED, 1 QUEUE
sqlite3 engagement.db "SELECT COUNT(*) FROM incoming_comments"  → 0
linkedin_cookies.json (8 cookies, no li_at) → li_at MISSING
engagement_runner.py 04:33 UTC log line   → "login gate blocked, 4th consecutive cycle"
```

**Cron writes diagnostic report** with the four sections above and emits `[SILENT]` for the run.

**Cron does NOT:**

- Run `comment_reply.py` with a fake/empty JSONL
- Run `comment_reply.py` with a fabricated post URL and reply text "to test"
- Claim any reply was made
- Suggest the system is healthy

## Anti-patterns to avoid

- **Running the executor script with a fake JSONL "to confirm it works."** A dry-run with a test post URL is fine for first-time validation, but never as a recurring cron action. It hides the actual no-op and burns audit-log entries.
- **Claiming the system is healthy because dry-run returned `{success:1}`.** A successful dry-run proves only that the script doesn't crash; it proves nothing about whether the cron is doing its job.
- **Fabricating reply text to "show progress."** A reply that wasn't sent is zero progress. Worse, a stored draft that *looks* like a sent reply is the 2026-07-03 fabrication incident in miniature.
- **Treating the cron prompt's "check for new comments" as the script's job.** The script is an executor. Discovery is upstream. If the upstream is broken, fix the upstream; don't pretend the executor does discovery.
- **Diagnosing auth without diagnosing the inbox.** A reply-only cron can be no-op'd by either layer. Always check both. A cycle that fixes `li_at` but leaves the inbox empty will still be a no-op.
- **Burning rate-limit budget on a failed reply attempt.** The executor's `assert_within_rate_limit("reply", logger)` will increment the day's `reply` counter even on a failed auth attempt in some implementations. Don't try the reply "to see what happens" — check the gate first.
- **Re-running the executor with `--dry-run` and reporting success.** Dry-run success is a script-syntax check, not a cron-success check. A cron whose real work is "reply to inbound comments" cannot claim success on a dry-run with no inbound comments.

## See also

- `staged-engagement-cron.md` — the manifest pattern for crons held at a gate. Different output (manifest vs. diagnostic) but shares the "don't fabricate, don't hide the held state" discipline.
- `staged-output-idempotency.md` — content-generation crons that produce audited artifacts.
- `read-only-analytics-cron.md` — read-only metrics-snapshot crons; shares the cron-mode runtime constraints (execute_code blocked, pipe-to-interpreter blocked).
- `cron-pin-pitfalls.md` — provider/model pinning failures (different failure class — that's about WHICH node the cron runs on, not whether the cron can act).
- SKILL.md §3 — Doer / Checker / Validator separation. A comment-reply cron that can't reply is effectively Doer-only with a hard upstream gate; Checker/Validator aren't relevant because nothing was built.
- SKILL.md §9–§12 — M2 auto-fix, M3 blocklist, and the history-log overwrite trap apply if the held-state triggers an alert that the self-healing monitor picks up.
