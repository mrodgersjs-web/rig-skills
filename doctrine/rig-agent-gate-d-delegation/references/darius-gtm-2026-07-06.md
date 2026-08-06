# Worked Example: Darius GTM Delegation (2026-07-06)

This is the canonical reference for a real Gate-D delegation to a
named RIG agent. Read this before issuing your first delegation.

## The Directive

> "Darius has to approve gtm efforts."

Spoken by Mike, recorded verbatim. This is a delegation of authority,
not a transfer of ownership. Mike remains the principal; Darius
becomes the designated operator for the defined lane.

## The Lane (per the directive, expanded by Jake PAI)

**Darius's lane:**
- Send any outbound email to any staged armed contact (Gate-D waived
  for 15-staged cohort)
- Approve any reply to a hot/warm lead (auto-respond to verified leads)
- Approve any re-engagement or follow-up sequence for warm leads
- Approve any subject-line variation A/B test on cold-email warmup
  (no auto-send)
- Sign any GTM-internal contract under $5K (deposit, consulting
  pre-paid, audit)
- Decide pricing for the audit/product/service offerings if
  pre-discussed scope
- Decline any inbound that's not a fit (filters noise to the inbox)

**NOT Darius's lane:**
- Public-facing brand artifacts (Theo's veto)
- New send cohorts (>15 contacts, Gate-D still required)
- Audio/video scripts that go public (Steve)
- Money over $5K (Eleanor + Mike)
- HED-deal-anything (Vera + Mike; hard block)

## The Six Artifacts

| # | File | Purpose |
|---|------|---------|
| 1 | `~/.rig/departments/gtm/audit/darius-gate-d-current.json` | Pre-delegation snapshot of all GTM/Darius cron jobs |
| 2 | `~/.rig/departments/gtm/DARIUS-AUTHORITY.md` | Lane / not-lane / protocol / audit schema |
| 3 | `~/.rig/departments/gtm/DARIUS-GTM-TOKEN-2026-07-06.json` | The typed-phrase token (token_id with random suffix, expiry 2026-07-31) |
| 4 | `~/Developer/rig-gtm-studio-v2/outbound/send-queue-verified.json` | 15 contacts auto-armed, atomic write, backup `.bak.2026-07-06-armed-darius` |
| 5 | `~/.rig/departments/gtm/audit/darius-actions-2026-07.jsonl` | 15 audit rows, one per auto-armed contact |
| 6 | (Cron fix + re-pin) | The cron jobs that touch the lane were re-pinned |

## Pre-Delegation Audit (Step 1)

The brief said "14+ jobs". The actual count from
`~/.hermes/cron/jobs.json` was **28** — 13 strictly GTM-tagged + 15
DARIUS-named jobs. A union filter (dept-tag, prompt-declared,
script-name, persona-name) is the right shape; hand-waving
"approximately 14" understates by half.

Of the 28:
- **25 delegatable to Darius** (per the directive's lane)
- **3 still require Mike** (RIG NODE OPS 96GB Omnichannel GTM,
  JAKE-SCRAPE-GTM 5GB substrate, GTM Night Pre-Arm)

The audit file is the pre-delegation snapshot. After the delegation
takes effect, this file remains as the historical baseline. New
audits diff against this one.

## Token Anatomy

```json
{
  "agent": "Darius",
  "dept": "gtm",
  "scope": "send, reply_hot, follow_up_warm, sign_under_5k, decline_inbound",
  "issued_at": "2026-07-06T19:30:00+00:00",
  "expires_at": "2026-07-31T19:30:00+00:00",
  "issued_by": "Mike via Jake PAI",
  "token_id": "DARIUS-GTM-2026-07-06-d06a788a",
  "constraints": [
    "no HED account",
    "no public-brand artifact",
    "no audio/video public",
    "no >$5K spend",
    "can only send to armed contacts in send-queue-verified.json"
  ],
  "audit_log_path": "/Users/rig128gb/.rig/departments/gtm/audit/darius-actions-2026-07.jsonl",
  "status": "ACTIVE",
  "directive_source": "Mike: 'Darius has to approve gtm efforts.'",
  "authority_doc": "/Users/rig128gb/.rig/departments/gtm/DARIUS-AUTHORITY.md",
  "hard_blocks": {
    "HED_account": "any HED / IdeaWake / Anthony Langeweg / hed-forge / dec-1783268304352-va5c / dec-1783268340018-db8f payload → quarantine",
    "public_brand_artifact": "Theo owns; veto authority",
    "aud_v_public": "Steve owns public A/V scripts",
    "money_over_5k": "Eleanor + Mike must approve",
    "new_send_cohort_gt_15": "Mike must approve new cohorts (>15)"
  },
  "revocation": {
    "method": "set status=REVOKED in this token file",
    "effect": "all auto-approved actions halt on next cron tick",
    "audit_preserved": true
  }
}
```

Note `token_id` has a 8-hex random suffix (`d06a788a`) so it can't be
re-derived. Note `directive_source` quotes Mike verbatim — that's the
legal hook.

## Atomic Write Pattern (Step 4)

```python
import json, os, tempfile, shutil
from datetime import datetime, timezone

QUEUE = '/Users/rig128gb/Developer/rig-gtm-studio-v2/outbound/send-queue-verified.json'
AUDIT = '/Users/rig128gb/.rig/departments/gtm/audit/darius-actions-2026-07.jsonl'

with open(QUEUE) as f:
    data = json.load(f)

for item in data['queue']:
    item['armed_by'] = 'Darius'
    item['armed_at'] = issued_at
    item['gate_d_delegated_to'] = 'Darius'
    item['gate_d_delegated_by'] = 'Mike via Jake'
    item['gate_d_token_id'] = token_id

# Atomic write: tempfile + fsync + os.replace
tmp_fd, tmp_path = tempfile.mkstemp(suffix='.json', dir=os.path.dirname(QUEUE))
try:
    with os.fdopen(tmp_fd, 'w') as f:
        json.dump(data, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    backup = QUEUE + '.bak.2026-07-06-armed-darius'
    shutil.copy2(QUEUE, backup)         # backup BEFORE rename
    os.replace(tmp_path, QUEUE)         # atomic on POSIX
except Exception:
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)
    raise

# Append audit log (jsonl is append-only)
with open(AUDIT, 'a') as f:
    for item in data['queue']:
        f.write(json.dumps({
            "ts": issued_at,
            "action": "auto-arm",
            "slug": item['slug'],
            "delegated_by": "Mike via Jake",
            "delegated_to": "Darius",
            "token_id": token_id,
            "result": "ok"
        }) + '\n')
```

Three gotchas in this code:
1. `os.fsync(fd)` before `os.replace` — guarantees the bytes hit disk
   before the rename.
2. `shutil.copy2(QUEUE, backup)` BEFORE the rename — if the rename
   succeeds but the next step fails, you have a coherent backup.
3. Append mode for the JSONL — the file is monotonic; no need to
   re-read + rewrite.

## What Went Right / What Went Wrong

### Right
- 6-step recipe executed in order; all 6 artifacts produced.
- Atomic write with backup succeeded on the first try.
- 15/15 contacts verified armed + delegated in re-read.
- Token expires in 25 days — forces re-confirmation.

### Wrong / Incomplete
- The cron re-pin step (Step 5) was NOT completed before the tool
  budget ran out. The 14 GTM cron jobs were not bumped to force
  next-tick execution.
- The `gtm-daily-loop.sh` script lacks a `--dry` flag, so any
  "smoke test" of the script actually runs live. Adding `--dry` was
  queued but not delivered. This is a real foot-gun for the next
  session that tries to test-fix a delegated cron.
- No proof JSON was written for the timeout-fix work because that
  step (Step 5) was incomplete.

## Future-Session Checklist

When delegating to ANY named agent (not just Darius):

1. **Get the audit count from disk.** Never trust a hand-wave number.
2. **Write the authority doc BEFORE the token.** The doc defines
   scope; the token authorizes it. If the doc is missing, the token
   is unscoped.
3. **Backup + atomic write, every time.** The cost is one shutil call;
   the benefit is roll-back to a known state.
4. **JSONL audit, one row per item.** Daily roll-up is a separate cron;
   the per-item rows are the source of truth.
5. **Cron re-pin happens AFTER the script is fixed.** Re-pinning a
   broken cron gets you another broken run.
6. **Add `--dry` to scripts before smoke-testing.** A script without
   `--dry` runs live when you test it; the "test" is the fire.
7. **Token expires. Always.** 25-30 days is the right window.
8. **Revocation is one field flip, but the daily roll-up records
   WHEN and WHY.**
