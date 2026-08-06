# Provider-Gated macOS Action Cron — Keychain → X / Postiz / Photos.app

Distinct from the multi-node LLM fleet crons described in SKILL.md §"Quick decision flow" (items 1–16 are fleet/analytics/content-gen crons that scrape or draft). This pattern is for **single-machine, single-purpose, fail-closed action crons** that:

- Read credentials from **macOS Keychain** via a compiled Swift helper (never raw env).
- Verify a **live OAuth user-context identity** at the API provider before any action.
- Dispatch per-mode (Mon/Wed/Fri or similar) using `TZ=... date +%u`.
- Acquire an **exclusive lock** via `mkdir` (macOS has no GNU `flock` by default).
- Execute at most **one approved action per invocation** behind a sealed approval capsule.
- Emit a **sanitized ProofPacket** (no `Authorization`, no bearer, no API key — ever).

Canonical examples: the Jacob X Account Engine cron (`/Users/rig128gb/Developer/RIGForge/repos/jabobs-x-account/scripts/jacob-x-cron-runner.sh`), any future local action cron that talks to X / Postiz / Stripe / Twilio / GitHub Apps on behalf of one specific account.

## When this fits

- Single-machine scheduler, single provider, single account.
- Credentials live in macOS Keychain (login keychain or custom keychain) — not in `.env` and not in cron mail output.
- Every action is gated by an explicit human approval (capsule + guardian consent + athlete/principal assent + expiry window).
- The cron never invents outbound actions. It only executes what an approval capsule pre-authorizes.
- A failure must BLOCK the run and surface in the ProofPacket — never silently retry.

## NOT for this pattern

- Multi-node LLM fleet crons (use `lan-probe-recipe.md`).
- Read-only analytics crons (use `read-only-analytics-cron.md`).
- Content drafting crons that stage drafts behind Gate-D (use `cron-mode-content-drafter.md`).
- Bulk/automated DMs to coaches or any NCAA-regulated recipient — the engine itself blocks this and the cron must not be used to bypass it.

## The 8-step recipe (the order matters)

```text
1. PATH export     — override cron env with /opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin
2. mkdir lock       — `mkdir "$LOCK_DIR"`; track LOCK_DIR_OWNED=true so the trap releases it
3. mode dispatch    — TZ=America/Denver date +%u → MONDAY|WEDNESDAY|FRIDAY|exit 64 otherwise
4. build Keychain   — `.x-control/bin/x-keychain-store` (compiled Swift); chmod 700
5. OAuth refresh    — silent `x-oauth.ts ensure --quiet`; read user-id via helper only
6. live identity    — GET /2/users/me with Bearer; require id+handle exactly; BLOCK if mismatch
7. per-mode commands — deterministic engine commands (status/scrape/verify/etc); failures BLOCK
8. one action gate   — only fires when --approved-action + --execute are both passed
9. sanitized proof  — Python-in-bash heredoc emits ProofPacket with sha256 hash; no secrets
```

The exit code from the runner must encode the verdict:
- `0` → ALLOW (every gate PASS, zero rejected actions, zero provider writes).
- `71` → BLOCK (any failed gate).
- `64` → wrong weekday (cron fired on a non-scheduled day — should never happen).
- `75` → overlapping run detected (lock acquisition failed).
- `77` → OAuth identity mismatch (the account being controlled is not the expected one).
- `69` → upstream API returned non-200 during identity verification.

## Pattern 1: macOS mkdir lock (no GNU flock)

macOS does not ship `flock(1)`. Use `mkdir` as the atomic primitive, and write the PID inside so a stale lock from a dead process can be reaped.

```bash
LOCK_DIR="${REPO}/.x-control/locks/jacob-x-cron.lock"
LOCK_STALE_AFTER_SECONDS="${JACOB_X_LOCK_STALE_SECONDS:-3600}"

acquire_lock() {
  if mkdir "$LOCK_DIR" 2>/dev/null; then
    LOCK_DIR_OWNED="true"
    echo $$ > "$LOCK_DIR/pid"
    return 0
  fi
  # Existing lock — check staleness.
  if [[ -f "$LOCK_DIR/pid" ]]; then
    local existing_pid; existing_pid=$(cat "$LOCK_DIR/pid" 2>/dev/null || echo "")
    if [[ -n "$existing_pid" ]] && kill -0 "$existing_pid" 2>/dev/null; then
      err "Another runner is active (pid=$existing_pid). Exiting."
      exit 75
    fi
    local lock_age=$(( $(date +%s) - $(stat -f %m "$LOCK_DIR" 2>/dev/null || echo 0) ))
    if [[ $lock_age -gt $LOCK_STALE_AFTER_SECONDS ]]; then
      err "Stale lock older than ${LOCK_STALE_AFTER_SECONDS}s. Reaping."
      rm -rf "$LOCK_DIR"
      if mkdir "$LOCK_DIR" 2>/dev/null; then
        LOCK_DIR_OWNED="true"; echo $$ > "$LOCK_DIR/pid"
        return 0
      fi
    fi
  fi
  err "Unable to acquire lock at $LOCK_DIR"; exit 75
}
```

Always create the lock parent dir first (`mkdir -p "$(dirname "$LOCK_DIR")"`) — `mkdir` on a non-existent parent fails silently under `2>/dev/null`. The trap must release the lock if `LOCK_DIR_OWNED == "true"` only — otherwise concurrent runners could remove each other's locks.

## Pattern 2: mode dispatch from weekday in a specific TZ

Cron on macOS runs in the user's local TZ (not UTC). The schedule must be authored against the **target TZ explicitly** so it survives a future TZ change:

```bash
CRON_TZ="${JACOB_X_CRON_TZ:-America/Denver}"
weekday=$(TZ="$CRON_TZ" date +%u)  # ISO weekday 1..7 in the target TZ
case "$weekday" in
  1) SCHEDULE_MODE="MONDAY" ;;
  3) SCHEDULE_MODE="WEDNESDAY" ;;
  5) SCHEDULE_MODE="FRIDAY" ;;
  *) err "Refusing to run: $CRON_TZ weekday=$weekday is outside the Mon/Wed/Fri schedule."; exit 64 ;;
esac
```

Record the schedule route (expression + TZ) in the ProofPacket. If the Mac's TZ is ever changed, recompute the cron expression or move to launchd and re-emit the ProofPacket with the new route.

## Pattern 3: Keychain helper invocation (read-only, helper-only)

The compiled Swift helper at `.x-control/bin/x-keychain-store` is the **only** way the runner reads credentials. Build it if missing:

```bash
if [[ ! -x "$KEYCHAIN_HELPER" || "${REPO}/scripts/x-keychain-store.swift" -nt "$KEYCHAIN_HELPER" ]]; then
  bash "${REPO}/scripts/build-x-keychain-helper.sh"
fi
export X_KEYCHAIN_HELPER="$KEYCHAIN_HELPER"
```

Read identifiers, never values:

```bash
STORED_USER_ID="$("$KEYCHAIN_HELPER" read jacob-x rig-x-user-id 2>/dev/null || true)"
[[ "$STORED_USER_ID" != "$EXPECTED_USER_ID" ]] && { err "stored id mismatch"; exit 77; }
```

**Never** export the token value into the shell environment for downstream tools — pass the helper path, let the helper resolve at point-of-use. This way the token is not in the runner's process env (which cron mail would log on failure).

## Pattern 4: live OAuth identity verification BEFORE any provider call

The single most important gate. Even with a valid access token, the runner must verify the token resolves to the expected account:

```bash
IDENTITY_FILE=$(mktemp -t jacobxidentity.XXXXXX)
HTTP_STATUS=$(curl -s -o "$IDENTITY_FILE" -w "%{http_code}" \
  --max-time 15 \
  -H "Authorization: Bearer ${USER_ACCESS_TOKEN}" \
  -H "Accept: application/json" \
  "$X_IDENTITY_URL" || echo "000")

LIVE_ID=$(grep -o '"id":"[0-9]*"' "$IDENTITY_FILE" | head -1 | sed -E 's/"id":"([0-9]+)"/\1/')
LIVE_HANDLE=$(grep -o '"username":"[A-Za-z0-9_]*"' "$IDENTITY_FILE" | head -1 | sed -E 's/"username":"([A-Za-z0-9_]+)"/\1/')
rm -f "$IDENTITY_FILE"

[[ "$LIVE_ID" != "$EXPECTED_USER_ID" || "$LIVE_HANDLE" != "$EXPECTED_HANDLE" ]] \
  && { err "Identity mismatch: expected $EXPECTED_USER_ID/$EXPECTED_HANDLE, got $LIVE_ID/$LIVE_HANDLE"; exit 77; }
```

Rules:
- ALWAYS call this BEFORE the first provider write — even for read-only commands.
- Treat the response body as ephemeral — `mktemp` and immediate `rm` to avoid leaving tokens on disk.
- The token itself is **not echoed**. The runner only logs the verified identity fields (`handle`, `id`) — both safe to log.
- Exit 77 on mismatch is intentional — it's the "wrong identity" code that cron monitoring should page on.

## Pattern 5: sanitized ProofPacket via Python-in-bash heredoc

bash heredoc + JSON escaping is brittle. Use Python to build the packet. The canonical writer is `scripts/sanitize_proof_packet.py` in this skill:

```bash
python3 "$REPO/scripts/sanitize_proof_packet.py" \
  --run-id "cron-$(date -u +%Y%m%dT%H%M%SZ)-$$" \
  --schedule-mode "$SCHEDULE_MODE" \
  --schedule-tz "$CRON_TZ" \
  --repo-path "$REPO" \
  --repo-commit "$(git -C "$REPO" rev-parse HEAD 2>/dev/null || echo unknown)" \
  --repo-dirty "$(git -C "$REPO" diff --quiet HEAD 2>/dev/null && echo false || echo true)" \
  --handle "$LIVE_HANDLE" \
  --user-id "$LIVE_ID" \
  --oauth-status "$GATE_STATUS_OAUTH" \
  --linkup-status "$LINKUP_STATUS" \
  --approved-considered "$APPROVED_ACTIONS_CONSIDERED" \
  --rejected "$ACTIONS_REJECTED" \
  --executed "$ACTIONS_EXECUTED" \
  --engine-status "$GATE_STATUS_ENGINE" \
  --identity-status "$GATE_STATUS_IDENTITY" \
  --verdict "$VERDICT" \
  --runtime-seconds "$RUNTIME_SECONDS" \
  --log-path "$LOG_FILE" \
  --output-file "$PROOF_FILE"
```

The writer enforces:
- `zero_secret_scan: true` flag — a self-declared invariant, not a search.
- Source URLs sanitized: only http(s), no embedded credentials, length-capped.
- Atomic write (`tmp` + `os.rename`) so a SIGKILL mid-write doesn't leave a half-written proof.
- File mode `0o600` on the output file.
- Deterministic `proof_hash: sha256:<hex>` of the canonical payload (sorted keys).

**Do NOT** handcraft the JSON in bash. Two real bugs that already happened:
1. Backslash escapes inside Python f-strings passed via heredoc leaked into the JSON output.
2. `datetime.utcnow()` is removed in Python 3.12+ — use `datetime.now(timezone.utc)` with a manual `Z` suffix.

## Pattern 6: one action per invocation + sealed approval capsule

The cron line itself **never** passes `--approved-action` or `--execute`. Every scheduled run is a dry-run by default. To execute one action, the human invokes the runner manually with both flags AND a sealed approval capsule:

```bash
/bin/zsh scripts/jacob-x-cron-runner.sh \
  --mode monday \
  --approved-action .approvals/jacob-x/<action-id>/action.json \
  --execute
```

The capsule directory layout (existing convention used by this umbrella's repos):
```
.approvals/jacob-x/<action-id>/
  action.json                  # the exact payload (actionId, kind, target, text, media[])
  approval-capsule.json        # sealed capsule with guardianConsent + athleteAssent + expiresAt
  consent.json                 # recipient consent for media use
  athlete-assent.json          # principal's signed assent (e.g. Jacob Rodgers)
  guardian-approval.json       # parent/guardian signed approval
  evidence.json                 # source URIs + hashes for every numeric/factual claim
  policy.json                   # NCAA / NCAA-compliance / platform rules review
  failed-attempt-v1.json         # optional; recorded if a prior execution failed
```

The controller verifies (in this exact order):
1. `capsule.actionSha256 == sha256(action)`
2. `capsule.capsuleSha256 == sha256(unsigned_capsule)` (no post-signing tamper)
3. `guardianConsent.confirmed == true && !revoked && approvedBy != ""`
4. `athleteAssent.confirmed == true && athleteName == "Jacob Rodgers"` (or the configured principal name)
5. `mediaRightsConfirmed && policyReviewed`
6. `idempotencyKey == action.actionId`
7. `now ∈ [approvedAt, expiresAt)` AND `expiresAt - approvedAt ≤ 24h`

If any fails, the run BLOCKS. Never retry a non-idempotent write blindly — if the upstream timed out after transmission, reconcile (read back via `GET /2/tweets/{id}`) before deciding whether to retry. Use the controller's `submissionMayHaveOccurred` flag to drive this.

## Pattern 7: content limits — ceilings, not quotas

These are **upper bounds** per cron invocation, applied at the runner level (in addition to the existing controller limits):

| Action kind | Per-run ceiling |
|---|---|
| Original post (with optional media) | 1 |
| Comment / reply | 2 |
| New follow | 3 |
| Like | 2 |
| Repost / quote post | 1 |
| Media upload | 1 |
| DM (any kind) | **0** — DMs are always manual |
| Duplicate engagement with same target within cooldown | rejected |

Zero actions is a valid dry-run. The runner's default state is dry; `--execute` is the only way to flip to write-enabled.

## Pattern 8: log sanitization — what may and may not appear in the log file

The runner `exec > >(tee -a "$LOG_FILE") 2>&1` so every line written via `log` / `err` lands in both stdout and the log. Cron mail output is the same stream. So:

**MAY appear in the log:**
- Timestamps, run-id, schedule mode
- Gate status (PASS/FAIL/MISSING)
- Sanitized provider HTTP status codes (200, 401, 429)
- Action IDs, public post IDs, public URLs (the X API returns these post-success)
- Linkup request counts and source URLs
- ProofPacket path + sha256 + verdict

**NEVER appear:**
- `Authorization: Bearer <token>` headers
- `x-api-key: <key>` headers
- Client secrets, refresh tokens, access tokens
- Cookie values, DMs (incoming or outgoing)
- Raw credential-provider response bodies

If a downstream tool needs to log a request/response that contains a header, it MUST redact it before logging. A simple pattern:

```bash
HTTP_STATUS=$(curl -s -o "$BODY_FILE" -w "%{http_code}" \
  -H "Authorization: Bearer ${TOKEN}" "$URL" || echo 000)
# Only the status is logged, never the body if the body might contain the token.
log "Provider returned HTTP $HTTP_STATUS"
```

## Companion technique: macOS Photos.app read-only bridge

Use `sqlite3` (CLI) to query `~/Pictures/Photos Library.photoslibrary/database/Photos.sqlite` for Memories and representative assets. Photos.app does not expose this via a stable public API.

```bash
sqlite3 -separator '|' "$PHOTOS_DB" "
  SELECT rep.Z_3REPRESENTATIVEASSETS, mem.Z_PK, mem.ZTITLE, mem.ZSUBTITLE
  FROM Z_3MEMORIESBEINGREPRESENTATIVEASSETS rep
  JOIN ZMEMORY mem ON mem.Z_PK = rep.Z_56MEMORIESBEINGREPRESENTATIVEASSETS
  WHERE mem.ZTITLE = 'Jacob' AND mem.ZSUBTITLE = '2025' LIMIT 5;"
```

Then resolve to a real file path. Photos 5+ stores assets in TWO possible locations:

1. `originals/<ZDIRECTORY>/<ZFILENAME>` — for older / local photos.
2. `resources/derivatives/masters/<ZDIRECTORY>/<basename>_<ZDIRECTORY>_<type>_c.<ext>` — for newer photos that live in iCloud. `<type>` is `5005` (jpeg) or `5006` (mov).

The bridge MUST try the originals path first and fall back to derivatives — never the reverse, since originals are missing for iCloud-only assets. The full reference implementation is `scripts/jacob-x-photos-bridge.ts` in the jabobs-x-account repo.

Three epoch-related footguns:
- Photos `ZDATECREATED` is **Mac Absolute Time in SECONDS** (not ms). Convert with `new Date((value + 978307200) * 1000).toISOString()`. The 978307200 is seconds between Unix epoch (1970-01-01) and Mac epoch (2001-01-01).
- SQLite returns NULL as empty string in `-separator` mode. Validate every parsed integer with `Number.isFinite()` before substituting it into another SQL query — passing `NaN` into a WHERE clause raises `no such column: NaN`.
- Always run sqlite3 in **read-only** mode (`-readonly` if supported, or use `:memory:` rollback). Never `UPDATE`/`DELETE`/`DROP` on Photos.sqlite.

## Companion technique: voice profile from existing X post corpus

When the cron is supposed to draft posts in the same voice as the account owner, scrape the last N published posts first and extract deterministic signals:

```python
# topic bucketing — keyword gates on the text corpus
TOPIC_KEYWORDS = {
  "TRAINING_PR":    ["bench", "squat", "pr", "lift", "weight room"],
  "FILM_STUDY":     ["film", "pass set", "anchor", "bull rush"],
  "IMG_VISIT":      ["img", "ernie logan"],
  "RECRUITING":     ["coaches", "recruiting", "d2", "d3", "d1"],
  "GRATITUDE":      ["grateful", "thank", "humbled"],
  ...
}

# hashtag/sign-off/format extraction — frequency count, exclude the anchor post
ANCHOR_POST_ID = "<the post that set the voice — never duplicate>"

for post in posts:
  if post["id"] == ANCHOR_POST_ID: continue  # critical
  for topic, kws in TOPIC_KEYWORDS.items():
    if any(kw in post["text"].lower() for kw in kws):
      topic_counts[topic] += 1
```

Output a sha256-stamped JSON profile under `.x-control/voice/<handle>-voice.json` with: `topics` (top-N), `hashtags` (top-N), `sign_offs` (top-N), `formats` (paragraph vs single-line), `corpus {posts_analyzed, posts_excluded, avg_chars}`, `post_ids_used`. Downstream drafters (cron or human-in-the-loop) read this profile and bias generation accordingly.

**The anchor exclusion is non-negotiable.** If the user already published a successful post in a particular style, the next cron MUST NOT generate a near-duplicate. Build the exclusion into the script, not into the human review.

## Companion technique: voice profile validator (cron-side gate)

Once the voice profile exists, the cron can pre-validate candidate drafts against it before staging:

```python
# Reject candidate if it uses a hashtag that's NEVER appeared in the corpus.
allowed_hashtags = set(h["key"] for h in profile["hashtags"])
if any(tag.lower() not in allowed_hashtags for tag in draft_hashtags):
  raise DraftValidationError(f"Unknown hashtag set: {draft_hashtags}")

# Reject candidate if its length is wildly off the corpus average.
avg_chars = profile["corpus"]["avg_chars"]
if not (0.5 * avg_chars <= len(draft_text) <= 2.0 * avg_chars):
  raise DraftValidationError(f"Draft length {len(draft_text)} outside corpus envelope")
```

The cron emits a `voice_match_score: 0..1` per draft so the human can see why one scored higher than another. Lower-scoring drafts are still surfaced — just flagged for editing, not auto-rejected.

## Idempotency — re-running the same cron safely

Re-running the runner after a transient failure (network drop, OAuth refresh hiccup) must NOT cause a duplicate post. The X controller maintains a per-action-id ledger at `.x-control/action-ledger.json` that records every action's `RESERVED` → `COMPLETED` or `RECONCILE_REQUIRED` state. The runner calls `reserve()` before any write and `complete()` / `reconcileRequired()` after.

If a run fails mid-execution (between `reserve()` and `complete()`), the next run finds the entry as `RESERVED`. Decision tree:
- Provider returned 2xx → mark `COMPLETED` with the recorded `providerId` (read it back via `GET /2/tweets/{id}`).
- Provider returned 5xx with no clear success → mark `RECONCILE_REQUIRED` and surface to the human. Do NOT auto-retry; the action might have succeeded server-side.
- Provider timed out before any response → same as `RECONCILE_REQUIRED`.

Always reconcile account state from the provider BEFORE deciding to retry. Never retry a non-idempotent provider write blindly.

## Schedule-route discipline

When you change the schedule (TZ, expression, mode days), update:
1. The runner's `CRON_TZ` and mode-dispatch case.
2. The crontab line via the idempotent installer (`scripts/install-jacob-x-cron.sh`).
3. The install-completion ProofPacket at `.x-control/proof/install-<component>-*.json`.
4. The next-three-runs section of `docs/<component>-OPERATIONS.md`.

If the Mac's TZ ever changes from America/Denver to something else, the cron expression `0 8 * * 1,3,5` becomes ambiguous. Compute the new UTC offset and either:
- Update the cron expression to fire at the equivalent UTC time (subtract 7h for MST, etc.).
- Switch to a launchd plist with `StartCalendarInterval` which is TZ-aware at the scheduler level.

Whichever route you pick, record it in the next ProofPacket so the operator can audit later.

## Verification before claiming done

After every cron installation or update:

```bash
# 1. Syntax
/bin/zsh -n scripts/jacob-x-cron-runner.sh && echo "SYNTAX OK"

# 2. Typecheck
npm run typecheck

# 3. Cron tests
npm run test:jacob-x-cron  # should report 10+/10+ PASS

# 4. Dry-run for each mode (assertion: exit 0, ZERO actions executed)
/bin/zsh scripts/jacob-x-cron-runner.sh --mode monday    | grep -E "verdict|run_id"
/bin/zsh scripts/jacob-x-cron-runner.sh --mode wednesday | grep -E "verdict|run_id"
/bin/zsh scripts/jacob-x-cron-runner.sh --mode friday    | grep -E "verdict|run_id"

# 5. Inspect schedule
bash scripts/show-jacob-x-cron.sh  # exactly 1 marked block, 1 schedule line

# 6. Confirm zero secrets in logs
grep -E "Authorization:|Bearer [A-Za-z0-9._~+/=-]{16,}|api[_-]key=|x-api-key:" .x-control/logs/cron-*.log | head -5
# should be empty
```

Then run **one** manual cycle with `--execute` and a real sealed approval capsule to prove the end-to-end path works (the operator approves; the runner executes; the provider returns a post ID; the ProofPacket records it). After that one live write, the schedule is trusted for dry-run operations.

## Anti-patterns

- **Passing `--execute` or `--approved-action` from the cron line.** The cron must be permanently dry-run. Manual execution requires a human invocation.
- **Logging the access token in any form.** Even with redacted middle sections, regex can recover it. The Keychain helper resolves at point-of-use; the runner never holds the token in its own env.
- **Auto-fixing an expired approval capsule.** If `expiresAt < now`, the capsule is invalid and the runner must refuse. Re-signing belongs to the human; the runner cannot re-sign.
- **Bulk sending DMs to coaches or recruits.** NCAA + platform rules forbid this. The engine's `prohibited outreach` gate catches it; the runner's content-limit table keeps DM count at 0 per cron.
- **Generating AI images of a minor.** Use real photos only. When no photo exists, the cron surfaces a "request photo from <principal>" item in the digest; a separate one-time iMessage prompt can fetch one. AI-generation is excluded by policy.
- **Skipping the live identity verification.** "I just refreshed the token 30 minutes ago" is not an identity check. The /users/me call is mandatory before any provider write.
- **Treating a BLOCK verdict as success.** BLOCK means BLOCK. The runner exits 71, cron logs it, the operator (you, or the next-morning digest) acts on it.

## See also

- `read-only-analytics-cron.md` — read-only metrics pattern; the cron-mode runtime constraints there (execute_code blocked, pipe-to-interpreter blocked, write_file JSON-escape) apply here too. Use `write_file` + `terminal python3`, never pipe to interpreter.
- `cron-mode-content-drafter.md` — staged-draft pattern (different surface: drafts text, doesn't call a provider).
- `staged-output-idempotency.md` — stage-aware guard pattern for content-generation crons whose output is audited.
- `self-healing-monitor-cron.md` — the fleet-watchdog pattern; useful as a Layer-2 monitor that watches THIS cron's `last_run_at` for stalls.
- `scripts/sanitize_proof_packet.py` — the canonical sanitized ProofPacket writer. Use it; do not hand-craft JSON from bash.