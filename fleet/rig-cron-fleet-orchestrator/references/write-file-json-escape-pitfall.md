# The `write_file` JSON-Escape Pitfall

`write_file` is the cron-mode default for producing JSON artifacts (proof files, manifest files, status reports). It is **not** a JSON-aware tool — it writes the content verbatim, and its built-in lint only surfaces the **first** JSON parse error. Several common composition patterns break JSON silently or with confusing offsets.

## The 4 failure modes (with examples)

### 1. Straight double-quotes inside a JSON string value

```python
# WRONG — the embedded double-quote terminates the string
{"comment_text": "She said \"AI is the future\" and left"}
#                     ^                    ^
#                     starts string         ends string early
#                     error: Expecting ',' delimiter
```

**Fix:** Build the payload in Python via `json.dump`, which handles the escaping. If you must hand-write the JSON, escape every inner double-quote as `\"` and verify with `json.loads(open(path).read())`.

### 2. Python list comprehensions and f-strings that look like code

```python
# WRONG — write_file does not expand Python expressions
{"ids": [{"id": x, "name": f"item-{x}"} for x in range(5)]}
# write_file writes the literal text above; no expansion happens
```

**Fix:** Build the payload in Python via `json.dump`. Don't try to embed code-shaped strings inside the JSON content.

### 3. Unescaped backslashes

```python
# WRONG — Windows path with single backslashes
{"path": "C:\Users\mike\data.json"}
#                   ^ ^ ^  ← JSON treats these as escape sequences
#                   \U is not a valid escape → error or wrong value
```

**Fix:** Either double-escape (`"C:\\Users\\mike\\data.json"`) or, again, build in Python and let `json.dump` handle it.

### 4. Trailing commas

```python
# WRONG — JSON does not allow trailing commas
{"id": "x", "count": 5,}
#                       ^  ← error
```

**Fix:** `json.dump` does not produce trailing commas. Don't hand-edit the output.

## The canonical fix: build in Python, verify, write

Pattern that survives every failure mode above:

```python
import json
import os
from pathlib import Path

payload = {
    "agent_id": "comment-writer",
    "batch": "am",
    "comment_count": 8,
    "comments": [
        {
            "comment_id": "am-c01",
            "rank": 1,
            "comment_text": (
                "She said AI is the future and left, "
                "but the receipts say otherwise. "
                "The MIT NANDA 95% pilot-fail number "
                "is the actual benchmark."
            ),
        },
        # ... more drafts ...
    ],
    "gate_d_status": "STAGED",
}

path = Path("$HOME/.hermes/jake/ralf-department/proof/daily/comments_am_2026-07-07.json")
path.parent.mkdir(parents=True, exist_ok=True)

# Write with explicit ensure_ascii=False so multi-byte content survives
with open(path, "w", encoding="utf-8") as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)

# Verify by re-parsing
with open(path, "r", encoding="utf-8") as f:
    parsed = json.load(f)

assert parsed["comment_count"] == len(parsed["comments"]), "draft count mismatch"
assert parsed["gate_d_status"] == "STAGED"

print(f"OK: wrote {os.path.getsize(path)} bytes; {parsed['comment_count']} comments")
```

The triple — `json.dump` + `ensure_ascii=False` + `json.load` re-parse — is the audit loop. Skip the re-parse and you will discover the bug at the next consumer.

## For cron-mode jobs: how to run this in cron

`execute_code` is BLOCKED in cron mode (see `read-only-analytics-cron.md` §"Cron-mode runtime constraints"). So:

1. **Write** the script to `/tmp/build_drafts.py` via `write_file`.
2. **Run** it via `terminal` with `python3 /tmp/build_drafts.py`.
3. The script handles `json.dump` + re-parse + audit.

This is the same `write_file` + `terminal python3` two-step the other cron references document.

## Built-in lint: useful but not enough

`write_file`'s post-write lint catches `JSONDecodeError` and reports:

```json
{
  "lint": {
    "status": "error",
    "output": "JSONDecodeError: Expecting ',' delimiter (line 37, column 506)"
  }
}
```

Note: the line/column is the **first** parse error, not the only one. If you have a quote-escape problem in line 12 *and* a trailing comma in line 40, the lint will only show line 12. Fix in order; re-write; re-lint.

The lint also only reports `JSONDecodeError` and similar syntax errors. It does NOT catch:

- Wrong field types (`"comment_count": "8"` instead of `8`)
- Missing required fields
- Semantic mistakes (a draft that says "agree" despite the `no_agreement: true` flag)
- Banned words in the content (you need a separate audit pass for that)

The mechanical audit (banned-word scan, required-field check) is your responsibility, not the linter's.

## The re-parse check is the only proof

After `write_file` reports `lint: ok`, the **only** way to know the file is consumable by the next stage is to re-parse it:

```python
import json
with open(path, "r", encoding="utf-8") as f:
    parsed = json.load(f)
```

If the re-parse succeeds AND the field-level checks pass, the file is consumable. Anything less is hope.

## Don't try to embed code in JSON content

If you find yourself wanting to write something like:

```json
{"summary": "The cron ran [f\"{count} drafts\"] successfully"}
```

…stop. The `write_file` tool will write the literal `[f"{count} drafts"]` text, not the expanded version. Either:

- Build the string in Python first and embed the resolved value, OR
- Use a sentinel like `__COUNT__` and replace it after writing.

The Python-build-via-`json.dump` idiom eliminates this class of bug entirely. Use it.

## See also

- `cron-mode-content-drafter.md` — the most common cron that hits this pitfall
- `read-only-analytics-cron.md` §"Cron-mode runtime constraints" — execute_code is blocked in cron mode; the workaround is the `write_file` + `terminal python3` two-step
- `staged-output-idempotency.md` — the stage-aware guard depends on `json.load` succeeding on the prior file; the re-parse check makes that contract honest
