# Dept Verifier Gate — Reading, Running, and Patching verifier.py

Every RIG dept has its own `~/.rig/departments/<dept>/verifier.py` — a single-purpose Python script that takes a dept-output dict and returns a PASS/FAIL/WEAK verdict. The cron MUST end every cycle by running it and capturing the verdict.

## The contract

Standard verifier shape (all 20 RIG depts follow it):

```python
def verify(dept_output: Dict[str, Any], ctx: Dict[str, Any] = None) -> Dict[str, Any]:
    text = json.dumps(dept_output)
    if is_blocked(text):
        return {
            "verdict": "CRITICAL",
            "metric": "blocklist_violation",
            "evidence": ["blocked term found in output"],
            "promote_to_L7": False,
            "return_to": "quarantine",
        }
    return {
        "verdict": "PASS",
        "metric": "<dept_north_star>",
        "evidence": ["scored against dept gate metric"],
        "promote_to_L7": False,
        "return_to": None,
    }
```

The north-star metric is in `pai.json` under `north_star_metric`. For legal it's `contract_dispute_rate_x_compliance_findings_open`; for finance it's `gross_margin_pct_x_runway_months`; etc.

## How to run it from the cron

```python
import subprocess, json
from pathlib import Path

verifier = Path.home() / ".rig" / "departments" / DEPT / "verifier.py"
result = subprocess.run(
    ["python3", str(verifier), json.dumps({"stub": "cycle-..."})],
    capture_output=True, text=True, timeout=30
)
verdict = json.loads(result.stdout)
```

Why a `{"stub": "..."}` payload: the verifier's `is_blocked` check runs against the *full JSON serialization* of the input. Sending an empty `{}` produces `text = "{}"` which never contains a blocklist term. Sending a stub lets you verify the path is callable AND lets you wrap a real cycle-summary into it for richer checks.

## The substring blocklist bug (catch and patch)

Most verifiers ship with:

```python
def is_blocked(text: str) -> bool:
    text_lower = text.lower()
    return any(term.lower() in text_lower for term in BLOCKLIST)
```

This false-flags legitimate text on any corpus where short tokens embed inside normal English. See `references/blocklist-word-boundary.md` for the full recipe and the regex upgrade.

**Before** running the cron cycle for the first time, grep the verifier:

```bash
grep -n "in text" ~/.rig/departments/<dept>/verifier.py
```

If you see `term.lower() in text_lower`, patch the verifier with the word-boundary version BEFORE the cron writes artifacts. Otherwise the cron will write 50 artifacts the verifier immediately rejects, and you'll waste a cycle.

## Verifier return shapes you should know

| Verdict | Meaning | Cron action |
|---|---|---|
| `PASS` | Artifacts clear all gates | Mark proof `verdict: PASS`, `_state.json state: ACTIVE` |
| `FAIL` | At least one non-critical gate failed | Mark proof `verdict: FAIL`, `_state.json state: HALT`, alert operator |
| `WEAK` | Passes with caveats (low confidence, soft signals) | Mark proof `verdict: WEAK`, keep `_state.json state: ACTIVE`, surface caveats in cycle report |
| `CRITICAL` | Blocklist hit, security breach, or quarantine trigger | Quarantine artifacts to `substrate/quarantine/<cycle>/`, mark `_state.json state: QUARANTINED`, do NOT promote to L7 |

## Don't try to interpret `promote_to_L7`

The verifier returns `promote_to_L7: bool` but the cron should NOT auto-promote. Promotion happens in a separate cron (`m5-pattern-promoter` or similar) that checks `evidence_count >= 3 verified episodes + confidence > 0.85`. The daily-goal cron writes L3 (entity pages) and L4 (skill catalog); promotion to L7 is someone else's job.

## When the verifier doesn't exist

Some depts ship without a verifier.py (rare; usually a sign of incomplete onboarding). In that case:

1. Do not skip the verifier step.
2. Read `pai.json` and write a temporary `verifier.py` that does blocklist + freshness + entity-count checks against the dept's declared north_star metric.
3. Mark the proof packet `verifier: synthesized` so the next session knows it's not the canonical one.
4. Open an onboarding gap in `_state.json` (`"missing_verifier": true`).

## Cross-reference

The blocklist fix is `references/blocklist-word-boundary.md`. The verifier invocation block is in `scripts/dept_cycle_builder.py`. The dept verifier contract is referenced from `rig-dept-daily-goal-builder` SKILL.md §7.