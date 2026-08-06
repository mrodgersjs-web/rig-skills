---
name: rig-agent-gate-d-delegation
description: "Delegate Gate-D authority from Mike to a named RIG agent (Darius, Eleanor, Nadia, etc.) so the agent can take specific GTM/accounting/operations actions without Mike approving every individual step. Use when Mike says 'Darius has to approve gtm efforts', 'Eleanor can sign under $5K', 'Nadia scores the leads', or any 'delegate X to agent Y with limits' directive. Class-level skill — works for any agent × any action-type delegation, not just GTM."
platforms: [macos, linux]
related_skills:
  - rig-gate-d
  - rig-department-build-out
  - rig-darius-data-analysis
  - rig-status-verification
  - rig-cron-diagnostics
---

# RIG Agent Gate-D Delegation

The pattern for **delegating** Gate-D authority from the human (Mike) to a
named RIG agent. The base `rig-gate-d` skill says: no outward action
without typed human approval. This skill says: there is one path to
delegate that authority to a specific agent, with a typed-phrase token,
hard-coded limits, a JSONL audit log, and an instant revoke switch.

Delegation is not bypass. The token is a typed, scoped, expiring,
audited handoff — Mike is still the principal; the agent acts as
designated operator.

## When to Use

- Mike says "Darius has to approve gtm efforts" / "Eleanor signs <$5K"
  / "Nadia auto-arms hot leads" / "the agent handles X without me"
- A new GTM/accounting/ops lane needs to move at agent speed but still
  under Mike's authority
- A previously manual approval chain (e.g. every cohort arm) becomes
  the bottleneck
- ANY time the directive is "agent X owns action Y, within limits Z"

## The Six-Step Delegation Recipe

When Mike issues a delegation directive, execute ALL SIX steps. Skipping
any one breaks the audit chain.

### Step 1 — Audit current authority surface

Before delegating, prove the lane being delegated. For a GTM delegation
this means: count the cron jobs that touch the lane, classify each
(DELEGATABLE / MIKE_REQUIRED_BRAND / MIKE_REQUIRED_HED / etc.), and
write the pre-delegation snapshot to:

```
~/.rig/departments/<dept>/audit/<agent>-gate-d-current.json
```

The audit schema is the source of truth for "what was the lane before".
Three things MUST be in the file:

1. The full job list with `name`, `provider`, `model`, `state`,
   `last_status`, `current_approval_required` (pre-delegation tag).
2. A policy block showing every action-type → required-approver mapping
   (pre-delegation state).
3. A metadata header with `gate_d_policy_version` so future audits can
   diff versions.

**PITFALL: count from a single source.** Don't manually enumerate
"14 jobs" — load `~/.hermes/cron/jobs.json` and filter. A union filter
(dept-tag, prompt-declared, script-name, persona-name) is the right
shape; the count is always larger than the brief's hand-wave.

### Step 2 — Define the authority scope doc

Write `DARIUS-AUTHORITY.md` (or `<AGENT>-AUTHORITY.md`) with these
sections:

- **Purpose** — quote Mike's exact directive.
- **Lane** — table of allowed actions, each with: action, scope,
  constraint. Be specific. "Outbound send" is not enough; "outbound
  send to any contact in `send-queue-verified.json` with
  `armed_by=<agent>`" is.
- **NOT the lane** — table of hard limits, each with: blocked action,
  owner (who has the veto), reason. Cover: brand artifact, A/V public,
  money threshold, hard-block account classes, cohort-size limits.
- **Action protocol** — per-lane-action, the exact sequence:
  preconditions, command, audit-log row, failure/rollback.
- **Audit trail** — JSONL row schema (ts, action, slug,
  delegated_by, delegated_to, result, notes), daily roll-up cadence,
  revocation method.
- **Hand-off verification** — who verifies the agent is honoring the
  token (the agent itself, Jake PAI, Mike).

### Step 3 — Issue the session-scoped token

Write a token file: `DARIUS-GTM-TOKEN-<date>.json`

Required fields:
```json
{
  "agent": "Darius",
  "dept": "gtm",
  "scope": "send, reply_hot, follow_up_warm, sign_under_5k, decline_inbound",
  "issued_at": "<ISO-8601>",
  "expires_at": "<ISO-8601, 25-30 days out>",
  "issued_by": "Mike via Jake PAI",
  "token_id": "<AGENT>-<DEPT>-<date>-<random8hex>",
  "constraints": ["<each lane constraint as a string>"],
  "audit_log_path": "<absolute path to JSONL>",
  "status": "ACTIVE",
  "directive_source": "<Mike's exact words>",
  "authority_doc": "<absolute path to AUTHORITY.md>",
  "hard_blocks": {
    "<blocked_action>": "<owner + reason>"
  },
  "revocation": {
    "method": "set status=REVOKED in this token file",
    "effect": "all auto-approved actions halt on next cron tick",
    "audit_preserved": true
  }
}
```

The `token_id` must include a random suffix (8 hex chars) so it can't be
re-derived from the date. The `directive_source` quotes Mike verbatim —
this is the legal hook if the delegation is ever challenged.

### Step 4 — Auto-arm the staged actions

For each artifact being delegated (e.g. each contact in a send queue,
each pending contract, each scored lead), perform an **atomic write**:

1. Read original file. Make backup:
   `<file>.bak.<date>-<reason>` (e.g. `2026-07-06-armed-darius`).
2. Add per-item fields: `armed_by`, `armed_at`, `gate_d_delegated_to`,
   `gate_d_delegated_by`, `gate_d_token_id`, `gate_d_delegated_at`.
3. Update top-level status block (e.g. `gate_d.status =
   "DELEGATED_TO_<AGENT>"`).
4. **Atomic write**: tempfile in same dir → `os.fsync` → `os.replace`.
5. Append one JSONL audit row per item to
   `~/.rig/departments/<dept>/audit/<agent>-actions-<YYYY-MM>.jsonl`.
6. Verify: re-read the file, count items with `armed_by == agent`
   must equal the cohort count.

**PITFALL: never edit-in-place without backup.** If the atomic write
fails halfway, you must be able to roll back to the pre-delegation
state. The backup filename includes the reason and date.

### Step 5 — Re-pin and re-test dependent cron jobs

For every cron that touches the delegated lane:

1. Bump `next_run_at` to force the next tick to pick up the new state.
2. If the script has a known bug (timeout binary missing, --dry flag
   missing, PATH dependency), fix it BEFORE the cron fires.
3. Run a `--dry` / smoke test of the script; require the proof file
   `<fix-name>-<date>.json` under `~/.rig/proof/`.
4. Watch error rate for ≥5 min after the first real run.

**PITFALL: scripts that lack a `--dry` flag will run live.** If the
script doesn't honor `--dry`, your smoke test is actually a live fire —
defeats the purpose of the gate. Either add the flag or don't smoke-test.

### Step 6 — Rollback plan

If the delegation is being abused or over-extended, set
`status: "REVOKED"` in the token file. The next cron tick sees
`status != "ACTIVE"` and halts all auto-approved actions. The audit
log remains intact for forensics.

Document the revocation in the daily roll-up the same day.

## Delegation vs Bypass

| Mechanism | When to use | Audit |
|-----------|-------------|-------|
| **Gate-D approval (base skill)** | One-off, high-stakes, Mike-typed `APPROVE <run_id>` | Per-run proof packet |
| **Agent Gate-D delegation (this skill)** | Recurring lane, Mike has pre-defined scope+limits, agent executes within them | Continuous JSONL + daily roll-up |
| **`--yes` / `--force` / env bypass** | NEVER — doctrine violation | N/A |

Delegation does NOT remove Mike from the loop. Mike is the principal
and the token issuer; the agent is the operator. The audit log + the
25-day expiry + the hard-blocks matrix keep Mike's authority intact.

## Authority Doc / Token / Audit Triad

The three artifacts MUST be created together. Skipping any one creates
a hole:

- **Authority doc** (`<AGENT>-AUTHORITY.md`) — defines WHAT the agent
  can do. Without it, the token has no scope; the agent could claim
  anything was delegated.
- **Token file** (`<AGENT>-<DEPT>-TOKEN-<date>.json`) — proves the
  delegation exists, with a token_id, expiry, and revocation method.
  Without it, the agent's actions have no principal.
- **Audit log** (`<agent>-actions-<YYYY-MM>.jsonl`) — proves what the
  agent DID. Without it, no post-hoc check is possible; the delegation
  is unfalsifiable.

## Verification Checklist

- [ ] Pre-delegation audit file exists and lists the full job surface
- [ ] Authority doc has Lane + NOT-lane + Action protocol + Audit
      trail sections
- [ ] Token has token_id (with random suffix), issued_at, expires_at
      (≤30 days), constraints, hard_blocks, revocation method
- [ ] `directive_source` quotes Mike's words verbatim
- [ ] Atomic write of armed artifacts, with backup before rename
- [ ] JSONL audit log created and one row per armed item
- [ ] All affected cron jobs re-pinned / re-tested / smoke-tested
- [ ] Rollback path tested: flipping `status: "REVOKED"` halts the
      agent on next tick
- [ ] Daily roll-up scheduled (or cron hook to write one)

## Common Pitfalls

1. **Token without an authority doc.** A token with `scope: "send"` is
   meaningless without a doc that says "send to armed contacts only".
   The agent can't reason about limits it doesn't have written down.
2. **No backup before atomic write.** If `os.replace` succeeds but the
   process crashes between backup and verification, you have a
   half-delegated state. Always keep a backup for at least one full
   cron cycle.
3. **Issuing a token with no expiry.** Tokens must expire. 25-30 days
   forces re-confirmation; "ACTIVE forever" is a doctrine violation.
4. **Forgetting the hard-blocks matrix.** "HED anything is forbidden"
   is a MUST-EXIST field, not a "we'll add it later". If the matrix
   is missing, the agent's code has nothing to check against.
5. **Delegating to an agent that doesn't read its own token.** The
   authority doc + token must be in a path the agent's cron/CLI
   actually loads. If the agent code has its own allow-list that
   predates the token, the token is decorative.
6. **Audit log written to a path the operator doesn't tail.** The
   JSONL must be in a watched directory. If nobody's reading it, the
   audit is performative.
7. **Cron re-pin after the fix was actually needed before.** If the
   script bug (e.g. `timeout: command not found`) was the reason a
   previous run failed, fix the script FIRST, then re-pin. Re-pinning
   a broken script just gets you another failed run.
8. **Mixing delegation and bypass.** If the token says "Darius auto-arms
   armed contacts" and the cron ALSO has a `--force` flag, the flag
   re-introduces bypass. Strip all bypass flags from the delegated
   lane.
9. **Quiet revocation.** Setting `status: "REVOKED"` without writing
   a daily roll-up entry means Mike has no record of WHEN or WHY the
   delegation ended. Always log the revocation.

## Related Skills

- `rig-gate-d` — base doctrine; the typed-approval phrase for one-off
  actions
- `rig-department-build-out` — for the broader pattern of building a
  department that needs this delegation
- `rig-darius-data-analysis` — Darius-style GTM analysis class
- `rig-status-verification` — verify any operational status by reading
  disk; applies to the audit log here
- `rig-cron-diagnostics` — for the cron re-pin / fix-script step
- `rig-operator-doctrine` — operator-level view of approvals
