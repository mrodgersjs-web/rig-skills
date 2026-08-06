# LAN Probe Recipe — Find Live Nodes Before You Trust the Config

The YAML config file lists providers. The providers point at IPs. **The IPs may be stale.** Always probe the LAN before pinning any cron job.

## The one-liner (Python, parallel, ~30s)

```python
import socket, urllib.request, json
from concurrent.futures import ThreadPoolExecutor

def probe(ip, ports=(11434, 11435, 3131, 3737)):
    out = {"ip": ip, "ports": {}}
    for port in ports:
        try:
            s = socket.create_connection((ip, port), timeout=0.5); s.close()
            out["ports"][port] = "OPEN"
        except: pass
    return out if out["ports"] else None

candidates = [f"192.168.68.{i}" for i in range(1, 255)]
with ThreadPoolExecutor(max_workers=30) as ex:
    live = [r.result() for r in (ex.submit(probe, ip) for ip in candidates) if r.result()]
```

## Then list loaded models on each live host

```python
def models(ip, port=11434):
    try:
        with urllib.request.urlopen(f"http://{ip}:{port}/api/tags", timeout=3) as r:
            return [m["name"] for m in json.loads(r.read()).get("models", [])]
    except: return None

for host in live:
    if 11434 in host["ports"] or 11435 in host["ports"]:
        port = 11434 if 11434 in host["ports"] else 11435
        host["models"] = models(host["ip"], port)
```

## Save the fleet map

Write the result to `/Users/rig128gb/.rig/state/fleet-map.json` so every cron scheduler + verifier can read it without re-probing.

```python
import json
from pathlib import Path
Path("/Users/rig128gb/.rig/state/fleet-map.json").write_text(
    json.dumps({"nodes": live, "scanned_at": iso_now()}, indent=2))
```

## Why this matters

In one session, the active `config.yaml` had `rig-36gb-lan → 192.168.68.67:11435` — but `.67` was unreachable. The cron kept failing every cycle because I trusted the config string. Five minutes of LAN scanning would have caught it on day 1.

**Treat the config file as an inventory, not a status.** It tells you what's POSSIBLE. The LAN tells you what's ALIVE.

## Common gotcha

`rig-128gb-local` may resolve to **multiple** live IPs (loopback + `.80` + `.88` etc). Pick loopback unless you specifically need the LAN one — loopback is fastest and most reliable.
