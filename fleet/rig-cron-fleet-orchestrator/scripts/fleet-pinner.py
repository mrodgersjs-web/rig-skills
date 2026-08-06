#!/usr/bin/env python3
"""Fleet pinner — read jobs.json and re-pin to verified live providers.

Use when:
- cron jobs are erroring on stale provider names
- you've added a new node to the fleet
- you want to redistribute cron load across providers

This is the FAILSAFE to `cronjob action=update` when the CLI isn't
available or when you want to pin many crons at once.
"""
import json, socket, urllib.request
from pathlib import Path

JOBS_PATH = Path("/Users/rig128gb/.hermes/cron/jobs.json")

# Update this dict when you add/remove nodes. Format:
# provider_name: (ip, port, default_model, [all_loaded_models])
WORKING_PROVIDERS = {
    "rig-96gb-lan": ("192.168.68.79", 11434, "rig-96gb-reasoner:latest",
                     ["rig-96gb-reasoner:latest", "rig-96gb-coder:latest", "rig-96gb-daily:latest"]),
    "minimax":       (None, None, "MiniMax-M3", ["MiniMax-M3"]),  # paid API
}

# Which provider should host which model? Order = preference.
MODEL_TO_PROVIDER = [
    ("rig-96gb-reasoner:latest",  "rig-96gb-lan"),
    ("rig-96gb-daily:latest",     "rig-96gb-lan"),
    ("rig-96gb-coder:latest",     "rig-96gb-lan"),
    ("MiniMax-M3",                "minimax"),
    ("mimo-v2.5-pro",             "minimax"),
]


def find_provider_for_model(model: str):
    """Return (provider, model) tuple for the requested model. Falls back to rig-96gb-lan / rig-96gb-daily."""
    for m, p in MODEL_TO_PROVIDER:
        if m == model:
            return (p, m)
    return ("rig-96gb-lan", "rig-96gb-daily:latest")


def pin_all_jobs(distribute_models: bool = True):
    """Re-pin every cron job to a valid provider. Writes jobs.json in place."""
    jobs = json.loads(JOBS_PATH.read_text())
    pinned = []
    for j in jobs.get("jobs", []):
        if distribute_models and j.get("model"):
            new_prov, new_model = find_provider_for_model(j["model"])
        else:
            new_prov, new_model = "rig-96gb-lan", "rig-96gb-reasoner:latest"

        old_prov, old_model = j.get("provider"), j.get("model")
        if old_prov != new_prov or old_model != new_model:
            j["provider"] = new_prov
            j["model"] = new_model
            j["last_error"] = None
            j["last_status"] = "ok"
            pinned.append({
                "id": j["id"], "name": j.get("name", "")[:50],
                "from": f"{old_prov}/{old_model}",
                "to":   f"{new_prov}/{new_model}",
            })

    JOBS_PATH.write_text(json.dumps(jobs, indent=2))
    return pinned


def probe_provider(name: str) -> bool:
    """Verify the provider IP responds. Silent on success."""
    info = WORKING_PROVIDERS.get(name)
    if not info:
        return False
    ip, port, _, _ = info
    if not ip:
        return True  # paid API
    try:
        s = socket.create_connection((ip, port), timeout=2); s.close()
        req = urllib.request.Request(f"http://{ip}:{port}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as r:
            return True
    except:
        return False


def main():
    print("=" * 70)
    print("FLEET PINNER — Re-pin crons to verified providers")
    print("=" * 70)

    print("\nProbing working providers...")
    for name, info in WORKING_PROVIDERS.items():
        ok = probe_provider(name)
        marker = "OK  " if ok else "DOWN"
        if info[0] is None:
            print(f"  {marker} {name:<20} (paid API — trusted)")
        else:
            print(f"  {marker} {name:<20} {info[0]}:{info[1]}")

    print("\nRe-pinning all jobs (distribute_models=True)...")
    pinned = pin_all_jobs(distribute_models=True)
    print(f"\nPinned {len(pinned)} jobs:")
    for p in pinned:
        print(f"  {p['id']} {p['name']}")
        print(f"    FROM: {p['from']}")
        print(f"    TO:   {p['to']}")


if __name__ == "__main__":
    main()
