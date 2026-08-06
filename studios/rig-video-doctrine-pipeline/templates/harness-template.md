# {Harness Name}

**Source:** {video_title} by {creator} — {url}
**Extracted:** {date}
**Type:** {goal-harness | gate-loop | verification-harness}

## Purpose

{What this harness governs — one paragraph}

## Gates

| Gate | Name | Evidence Required | Pass Condition |
|------|------|-------------------|----------------|
| 00 | {Gate name} | {what must be produced} | {pass/fail criteria} |
| 01 | {Gate name} | {what must be produced} | {pass/fail criteria} |
| 02 | {Gate name} | {what must be produced} | {pass/fail criteria} |

## Loop

```
{Entry condition}
  ↓
[Gate 00] → {action} → evidence → {pass/fail}
  ↓
[Gate 01] → {action} → evidence → {pass/fail}
  ↓
[Gate 02] → {action} → evidence → {pass/fail}
  ↓
{Exit condition or escalation}
```

## Kill Switches

- {Condition that immediately stops the loop}
- {Budget/time limit}

## Integration

- **Goal loops served:** {list}
- **Agents governed:** {list}
- **Doctrine reference:** {link}
