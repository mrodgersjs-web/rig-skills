# Cron Pin Pitfalls — Five Ways Pinning Fails

When you call `cronjob action=update job_id=... model={...}`, the cron job records the provider string and model string verbatim. **But neither string runs anything** — the scheduler looks up the provider name in `~/.hermes/config.yaml` providers block, then sends the model to that provider's `base_url`. If either lookup fails, the cron errors with `Unknown provider` and `next_run_at` keeps ticking but `last_status` becomes "error" forever.

## The five failure modes

### 1. **Stale IP** — provider config still claims an old address

```
Config: rig-36gb-lan → http://192.168.68.67:11435/v1
Reality: 192.168.68.67 times out
Cron error: TimeoutError or socket hang up
```

Fix: probe LAN first (see `lan-probe-recipe.md`), then either edit config.yaml or pin to a provider that points at a live IP.

### 2. **Unknown provider name** — provider string doesn't match config

```
You wrote: provider="blackwell-vllm"
Config has: rig-96gb-lan, rig-48gb-lan, rig-36gb-lan, minimax, xiaomi
Cron error: RuntimeError: Unknown provider 'blackwell-vllm'
```

Fix: only use provider strings that appear in the active `~/.hermes/config.yaml`. Don't assume a provider is registered.

### 3. **Wrong model on a working provider**

```
You wrote: model="fable-qwen3.6-27b:Q4_K_M"
Node at .76 has: rig-256gb-strategy, rig-256gb-daily, fable-qwen3.6-27b
Cron runs anyway but returns wrong/empty content
```

Fix: enumerate the live node's loaded models with `/api/tags` and pick one that's actually present.

### 4. **Stale `last_status: error` after a fix**

After you re-pin a cron, the next cycle **will** succeed — but until it runs, `last_status` still reads "error" from the prior failed cycle, and your Validator-Drift cron will report the fleet as unhealthy.

Fix: explicitly clear `last_error` and reset `last_status` to `"ok"` in `~/.hermes/cron/jobs.json` after pinning. The next cycle's real status will overwrite it within the cadence.

### 5. **Cron pinned to one node that goes down**

If all 24 crons point at the same `rig-96gb-lan` provider and that node reboots, every cron errors simultaneously.

Fix: distribute across multiple working providers and models. Even with limited options, spread:
- Heavy reasoning → `rig-96gb-lan / rig-96gb-reasoner:latest`
- Scraping + scraping checks → `rig-96gb-lan / rig-96gb-daily:latest`
- Code analysis → `rig-96gb-lan / rig-96gb-coder:latest`
- Cheap monitoring + setup → `minimax / MiniMax-M3` (paid, fast)

## The audit script

Run this weekly to catch breakage before the crons do:

```bash
python3 -c "
import json
from pathlib import Path
jobs = json.loads(Path('/Users/rig128gb/.hermes/cron/jobs.json').read_text())['jobs']
broken = [j for j in jobs if j.get('last_status') == 'error']
for j in broken:
    print(f\"{j['id']} | {j['name']} | provider={j.get('provider')} | model={j.get('model')} | err={j.get('last_error','')[:60]}\")
"
```

## When `cronjob` CLI isn't available

In one session the `cronjob` binary wasn't on PATH. **The fallback is to edit `~/.hermes/cron/jobs.json` directly** — every field accepts the same shape. The scheduler picks up changes at next tick.

```python
import json
from pathlib import Path
p = Path("/Users/rig128gb/.hermes/cron/jobs.json")
data = json.loads(p.read_text())
for j in data["jobs"]:
    if j.get("id") == "your-cron-id":
        j["provider"] = "rig-96gb-lan"
        j["model"] = "rig-96gb-reasoner:latest"
        j["last_error"] = None
        j["last_status"] = "ok"
p.write_text(json.dumps(data, indent=2))
```

Use the bundled `scripts/fleet-pinner.py` for the multi-cron variant.
