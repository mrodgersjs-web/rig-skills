# Bulk-Spawning Cron Jobs From a Spec File

Use this recipe when you need to create N cron jobs (typically 5–30) from a JSON spec
that specifies per-job `model`, `provider`, `schedule`, `name`, and `prompt`. The
canonical case is a `_kanban/scrapers_spec.json`-style file with one record per dept
that needs a JAKE-SCRAPE-style substrate cron.

## Why this isn't a `hermes cron create` one-liner per row

`hermes cron create` does **not** accept `--model` or `--provider` flags (verified
2026-07-06). Only the following flags exist:

```
hermes cron create [-h] [--name NAME] [--deliver DELIVER]
                   [--repeat REPEAT] [--skill SKILLS] [--script SCRIPT]
                   [--no-agent] [--workdir WORKDIR]
                   schedule [prompt]
```

The CLI happily creates the job, generates a 12-char-hex ID, and schedules it — but
the resulting record has `model: null, provider: null`. That record is then **stuck on
the cron ticker's default provider/model**, which is whatever `~/.hermes/config.yaml`
resolves to right now (usually `minimax/MiniMax-M3`), not what the spec said.

The existing JAKE-SCRAPE fleet in `~/.hermes/cron/jobs.json` (8 originals + 13 spawned
2026-07-06) all have `model` and `provider` populated, so they were created via the
same CLI-then-patch idiom — not via direct JSON append. Direct JSON append works too
but you have to (a) read all the existing keys to mirror the schema exactly, (b)
generate collision-free 12-hex IDs yourself, (c) acquire the `.tick.lock` file lock,
(d) write atomically. CLI-then-patch is simpler because the CLI does steps a–d.

## The recipe (CLI-then-patch)

```python
#!/usr/bin/env python3
"""Spawn N cron jobs from a JSON spec; patch model/provider after each CLI create."""
import json
import subprocess
from pathlib import Path

SPEC = Path("/Users/rig128gb/.rig/departments/_kanban/scrapers_spec.json")
JOBS = Path("/Users/rig128gb/.hermes/cron/jobs.json")

data = json.loads(SPEC.read_text())
scrapers = data["scrapers"]            # or data itself if it's already a list

for spec in scrapers:
    name, schedule, model, provider = spec["name"], spec["schedule"], spec["model"], spec["provider"]
    prompt = spec.get("prompt") or f"You are Jake PAI running {name}. ..."

    # 1. CLI create — captures the generated 12-hex ID from stdout
    r = subprocess.run(
        ["hermes", "cron", "create", "--name", name, schedule, prompt],
        capture_output=True, text=True, timeout=60,
    )
    job_id = None
    for line in (r.stdout + r.stderr).splitlines():
        if line.startswith("Created job:"):
            job_id = line.split(":", 1)[1].strip().split()[0]
            break
    if r.returncode != 0 or not job_id:
        print(f"FAIL  {name}: {r.stdout}{r.stderr}")
        continue

    # 2. Patch jobs.json — add model, provider, and schedule_display
    jobs = json.loads(JOBS.read_text())
    for j in jobs.get("jobs", []):
        if j.get("id") == job_id:
            j["model"] = model
            j["provider"] = provider
            j["schedule_display"] = schedule
            if isinstance(j.get("schedule"), dict):
                j["schedule"]["display"] = schedule
            break

    # 3. Write atomically — never leave a half-written jobs.json
    tmp = JOBS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(jobs, indent=2))
    tmp.replace(JOBS)

    print(f"OK  {job_id}  {name}  (model={model}, provider={provider})")
```

That's it. Verified 13 ok / 0 failed on 2026-07-06 spawning 13 dept scrapers in one
run.

## Why patch `jobs.json` instead of CLI flags

- The CLI surface is fixed by `hermes_agent/cli.py`'s argparse. Adding `--model`/`--provider`
  would require modifying the `hermes-agent` package, which is **bundled and protected**
  per the skill-protection rules. Patch jobs.json instead.
- The CLI's `last_run_at` / `last_status` / `repeat.completed` fields are then
  populated organically by the ticker once the job fires. If you write jobs.json
  directly, you have to seed those fields or the ticker will treat the job as
  "first-ever run" and may log a misleading state transition.
- The CLI writes the right `created_at` timestamp with the host's local TZ offset
  matching the existing records (e.g. `-06:00` for Mountain). Hand-writing the
  timestamp is a small but real risk of TZ drift.

## Pitfalls

1. **Don't `cron delete` then re-create** — delete-via-CLI emits a state transition
   the ticker may pick up as a "this job disappeared" event, and re-creating
   generates a different ID, which orphans any downstream cron that referenced the
   old ID (e.g. a self-healing monitor). Patch in place.

2. **The CLI allows duplicate `--name`** — the existing fleet already has multiple
   crons named with the same root (e.g. the 8 JAKE-SCRAPE jobs). The ID is the real
   primary key. Don't grep-then-skip by name.

3. **`enabled: true` is the CLI default** — the new job will fire on its first
   `next_run_at`. If you want a "staged but disabled" job (so you can review before
   letting it run), set `enabled: false` in the patch step.

4. **Atomic write is non-negotiable** — the ticker reads `jobs.json` while we're
   patching. Use `tmp.replace(JOBS)` (rename is atomic on macOS APFS) not
   `JOBS.write_text(...)`. If you write directly and crash mid-write, the ticker
   starts logging `JSONDecodeError` on every cycle until you restore.

5. **Verify after the run** — `jq '.jobs[] | select(.name == "...")'` should return
   the new record with `model` and `provider` populated. If they're still `null`,
   the patch step didn't find the ID (means the CLI didn't actually create it, or
   the ticker's prune pass ran between create and patch — extremely rare but
   documented).

6. **`hermes cron create --repeat N`** sets a `times: N` limit. The existing 8
   JAKE-SCRAPE jobs all use `repeat.times: 6` (6-cycle substrate cap). For
   dept-scraper bulk spawns you usually want **no repeat limit** — leave the CLI
   default and the ticker will run forever. Verify `repeat.times` after each create
   and adjust in the patch step if you want a cap.

## Verification recipe

After spawning, confirm the new crons are properly pinned:

```bash
# All crons named JAKE-SCRAPE-* with their effective model/provider
jq '.jobs[] | select(.name | test("JAKE-SCRAPE")) | {name, model, provider, schedule_display, enabled}' \
   /Users/rig128gb/.hermes/cron/jobs.json

# Total cron count delta (before/after)
jq '.jobs | length' /Users/rig128gb/.hermes/cron/jobs.json
```

If the count went up by N and every spec's name appears once with the expected
model/provider, the spawn succeeded. If a name is missing, scroll back through the
script output for `FAIL` lines.

## Cross-references

- Rule #8 in the parent skill — `hermes cron list` does NOT surface provider/model;
  read `jobs.json` directly to verify your patch took.
- `references/cron-pin-pitfalls.md` — the 5 ways pinning fails. The bulk-spawn path
  avoids most of them because the spec carries the right values from the start.
- `scripts/fleet-pinner.py` — read-and-pin tool that *re-pins* existing crons to
  verified providers. Useful as a follow-up if any of the spawned crons end up
  drifting after their first few cycles (M2 monitor territory).