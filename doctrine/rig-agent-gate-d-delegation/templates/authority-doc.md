# Agent Gate-D Delegation — Authority Doc Template

Copy this to `~/.rig/departments/<dept>/<AGENT>-AUTHORITY.md` and fill
in the placeholders. Keep the section structure — future agents
parse this doc by section name.

---

# <AGENT> <DEPT> Authority Scope

**Issued:** <YYYY-MM-DD>
**Issued by:** Mike via Jake PAI
**Authority source:** Mike directive — *"<verbatim quote of Mike's words>"*
**Effective:** Immediately on issuance of token `<TOKEN_ID>`
**Expires:** <YYYY-MM-DD> (≤30 days; renewable)

---

## 1. Purpose

<One paragraph: why Mike is delegating this lane. State the underlying
operational need (e.g. "the GTM lane needs to move without Mike
approving every individual send").>

## 2. <AGENT>'s Lane (Auto-Approved)

| # | Action | Scope | Constraint |
|---|--------|-------|------------|
| 1 | **<action name>** | <exact scope> | <exact constraint> |
| 2 | **<action name>** | <exact scope> | <exact constraint> |
| ... |

## 3. NOT <AGENT>'s Lane (Hard Limits)

| Blocked action | Owner | Reason |
|----------------|-------|--------|
| **<blocked action>** | **<owner>** | <reason> |
| ... |

## 4. Action Protocol

### 4.1 <action name>
1. <preconditions>
2. <command / sequence>
3. <audit log row>
4. <failure / rollback>

## 5. Audit Trail

Every <AGENT> action writes one JSONL row to:
`<absolute path to JSONL>`

Row schema:
```json
{
  "ts": "<ISO-8601>",
  "action": "<action_name>",
  "slug": "<contact slug or contract id>",
  "delegated_by": "Mike via Jake PAI",
  "delegated_to": "<AGENT>",
  "result": "ok | blocked | quarantined | escalated",
  "notes": "<freeform>"
}
```

### Daily digest
A daily roll-up is generated at `<path>` with action counts, total
$ signed, and any escalations to Mike.

### Rollback
If Mike determines the delegation is being abused or over-extended:
- Set `<TOKEN_FILE>` `status` → `REVOKED`.
- All auto-approved actions halt on next cron tick.
- Audit log remains intact for forensics.

## 6. Hand-off Verification

| Owner | Verifies |
|-------|----------|
| **<AGENT>** | Token is `ACTIVE` before each action; contact is in armed cohort |
| **Jake PAI** | Daily digest exists; anomalies flagged |
| **Mike** | Weekly review of audit log + daily roll-ups |

## 7. Related Artifacts

- Token: `<absolute path to token JSON>`
- Audit log: `<absolute path to JSONL>`
- Pre-delegation Gate-D audit: `<absolute path to pre-audit JSON>`
- <staged items>: `<absolute path to staged items>`

---

*This authority is a delegation of trust, not a transfer of ownership.
<AGENT> acts as Mike's designated <DEPT> operator. Mike retains final
say on any action that crosses the limits in §3.*
