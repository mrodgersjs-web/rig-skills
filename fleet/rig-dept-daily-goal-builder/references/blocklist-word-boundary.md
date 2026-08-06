# Blocklist Word-Boundary Matcher — Recipe and Pitfalls

Substring matching (`term in text.lower()`) is the **default** in most RIG dept verifier.py scripts, and it's a latent bug for any dept whose corpus contains normal English with embedded short tokens.

## The trap

```python
BLOCKLIST = ["HED", "US", "AI", "EU", "ID"]
text = "Data was established in the EU and processed under Article 30."
text.lower()                              # "data was established in the eu and processed under article 30."
"HED" in text.lower()                     # wait, no, this returns False...
```

Right, in *that* example `HED` is not in `text.lower()` — but `EU` and `US` are, and they are legitimate English / acronyms, not blocklist hits. The reverse is the real bug:

```python
BLOCKLIST = ["HED"]
text = "Representatives of controllers or processors not established in the Union"
"hed" in text.lower()                     # TRUE — substring matches "establiSHED"
```

Real case from the legal daily cycle, 2026-07-06: GDPR Art. 27 was rejected because the verifier substring-matched `HED` inside `established`. The verifier correctly says "blocklist violation" — but it's wrong; the text is GDPR boilerplate.

## The fix — word-boundary regex

```python
import re

def block_check(text: str, blocklist: list[str]) -> bool:
    low = text.lower()
    for b in blocklist:
        # (?<![A-Za-z0-9])  = previous char NOT alphanumeric
        # (?![A-Za-z0-9])   = next char NOT alphanumeric
        # re.escape(b)      = treat blocklist term as literal, not regex
        if re.search(r"(?<![A-Za-z0-9])" + re.escape(b.lower()) + r"(?![A-Za-z0-9])", low):
            return True
    return False
```

Walkthrough on the Art. 27 case:

```
low           = "...controllers or processors not established in the union..."
term          = "hed"
lookbehind    = position before "hed" is 's' (in "established") → alphanumeric → FAILS
               regex does NOT match → return False → entity passes
```

Walkthrough on a real `HED` hit:

```
low           = "...we found HED in the contract..."
term          = "hed"
lookbehind    = position before "hed" is ' ' → NOT alphanumeric → passes
lookahead     = position after "hed" is ' ' → NOT alphanumeric → passes
               regex matches → return True → block
```

## Edge cases the regex handles correctly

| Case | Substring matcher | Word-boundary regex |
|---|---|---|
| `established` vs `HED` | TRUE (false positive) | FALSE ✓ |
| `shed` vs `HED` | TRUE (false positive) | FALSE ✓ |
| `HED Corp` vs `HED` | TRUE | TRUE ✓ |
| `HEDCO` vs `HED` | TRUE (false positive) | FALSE ✓ |
| `AIShed EU` vs `US` | TRUE (false positive on `us` in `Shed`… actually no, but vs `AI`: TRUE false positive on `ai` in `ais`) | FALSE ✓ |
| `GDPR's HED-references` vs `HED` | TRUE | TRUE ✓ |

## What the regex does NOT handle

- Blocklist terms that ARE meant to be inside larger terms (rare — usually you want them matched as substrings). Solution: keep two lists, `BLOCKLIST_WORD` (use regex) and `BLOCKLIST_SUBSTR` (use substring).
- Non-ASCII content (em-dashes, Chinese, Arabic, emoji). The `[A-Za-z0-9]` class is ASCII-only. If the corpus is multilingual, swap for `\w` (Unicode-aware) or define a project-specific boundary class.
- Terms that contain regex metachars (`HED.FORGE`, `HED[0-9]`). `re.escape()` handles these.

## How to apply to existing verifier.py

Most RIG dept `verifier.py` files have:

```python
def is_blocked(text: str) -> bool:
    text_lower = text.lower()
    return any(term.lower() in text_lower for term in BLOCKLIST)
```

Replace with:

```python
import re
def is_blocked(text: str) -> bool:
    low = text.lower()
    return any(
        re.search(r"(?<![A-Za-z0-9])" + re.escape(term.lower()) + r"(?![A-Za-z0-9])", low)
        for term in BLOCKLIST
    )
```

This is a 1:1 swap — same return shape, same call sites, but no false positives.

## Test before shipping

Before deploying the upgraded matcher:

```python
KNOWN_BAD = ["HED Corp is forbidden", "we used HED-co services", "block HED here"]
KNOWN_GOOD = ["established in the EU", "sheds", "AIs", "HEDCO holdings", "data controllers"]

assert all(block_check(t, ["HED"]) for t in KNOWN_BAD)
assert not any(block_check(t, ["HED"]) for t in KNOWN_GOOD)
```

If the GOOD list trips the matcher, the regex is wrong; check the lookbehind/lookahead class.

## Cross-reference

This recipe is referenced from the dept-daily-goal-builder SKILL.md §3 and applied in the dept_cycle_builder.py script's `block_check` helper.