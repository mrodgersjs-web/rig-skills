# macOS 26 Quirks for RIG Runtime Operations

These came up while running the founder-runtime on a macOS 26.5.1 control plane. Capture them so the next session doesn't waste a turn rediscovering.

## launchctl output format

`launchctl list` on macOS 26+ returns **JSON**, not the text columns older docs describe:

```bash
$ launchctl list com.rig.founder-worker.rig-control-128gb
{
	"StandardOutPath" = "/Users/rig128gb/.rig/founder-runtime/logs/worker.rig-control-128gb.out.log";
	"LimitLoadToSessionType" = "Aqua";
	...
}
```

If your code parses `launchctl list` as whitespace-split text, it will get one big JSON blob and choke. **Use `launchctl print <label>`** instead — that returns parseable lines with `pid = <int>` and `state = <word>`:

```bash
$ launchctl print gui/$(id -u)/com.rig.founder-worker.rig-control-128gb | grep -E "pid|state"
    state = running
    pid = 32319
```

Pattern for parsing:

```bash
out=$(launchctl print "gui/$(id -u)/${label}")
pid=$(echo "$out" | grep -E '^[[:space:]]+pid' | head -1 | awk '{print $3}')
state=$(echo "$out" | grep -E '^[[:space:]]+state' | head -1 | awk '{print $3}')
```

`launchctl print` accepts a session-qualified label (`gui/UID/...`) which is what you want for user agents.

## `python3` on PATH is the Xcode toolchain

```bash
$ which python3
/usr/bin/python3
$ file /usr/bin/python3
/usr/bin/python3: Mach-O 64-bit executable arm64
$ /usr/bin/python3 -c "import sys; print(sys.executable)"
/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app/Contents/MacOS/Python
```

The Xcode Python **does not have your venv deps installed**. For any RIG runtime command, always invoke:

```bash
<runtime>/.venv/bin/python -m <module> ...
```

For launchd services, the `ProgramArguments` should call `.venv/bin/<entrypoint>` directly — never `python3`.

## `BaseHTTPRequestHandler.store` is read as instance attribute

`founder_runtime.api` sets `Handler.store = store` at the class level, but every `do_POST` reads it as `self.store`. Python resolves `self.store` against the **instance** dict first, so:

- Setting `Handler.store = store` (class attribute) is **not enough** for the handler instance.
- Setting `f.store = store` on the Fake request object is what works.

When testing handlers in isolation, your Fake must do:

```python
class Fake:
    pass
f = Fake()
f.store = store  # INSTANCE attribute, not class
f.path = "/api/..."
# ... other attrs BaseHTTPRequestHandler needs
Handler.do_POST(f)
```

The Handler reads `self.store`, `self.path`, `self.command`, `self.headers` (Content-Length), and via `log_message` it tries `self.requestline` and `self.client_address`. Stubbing all of these on the instance is safer than relying on class-level defaults.

## `dispatcher` writes audit_log as JSON string

The dispatcher records ticks via:

```python
append_audit(store, actor="dispatcher", action="tick", target=None, detail=result)
```

where `result` is a dict like `{"items_leased": 1, "queue": {...}}`. The `detail` column gets `json.dumps(result)` — so the JSON lives as a **string** inside the audit row. LIKE filters work for substring matches (`LIKE '%expired_leases_recovered%'`), but anything finer (filter by `items_leased >= 5`) requires `json_extract()` (SQLite 3.38+) or parsing `detail` in Python.

## macOS launchd KeepAlive.Crashed + ThrottleInterval = 10

When you `kill -9` a worker with `KeepAlive.Crashed=true`, launchd restarts it within ~3 seconds. If you check too quickly after the kill, you'll see the old PID still listed — give it a moment.

To verify the restart actually happened:

```bash
launchctl print "gui/$(id -u)/<label>" | grep -E "pid|state|last exit"
```

The `last exit code` should match the signal (e.g. `last exit code = -9` for SIGKILL) and `pid` should be a different number than before the kill.

## `mark_offline_stale_nodes` must filter `last_heartbeat IS NOT NULL`

A freshly-registered node has `last_heartbeat = NULL`. If your `mark_offline_stale_nodes` query uses `(julianday('now') - julianday(last_heartbeat)) * 86400 > ?` without an `IS NOT NULL` guard, it will immediately mark every new node as stale. The fix:

```sql
WHERE status IN ('ONLINE', 'DRAINING')
  AND last_heartbeat IS NOT NULL
  AND (julianday('now') - julianday(last_heartbeat)) * 86400 > ?
```

## Venv python + macOS launchd plist

When you write a launchd plist that calls `.venv/bin/python`, the plist needs `ProgramArguments` to be the absolute path. macOS launchd does NOT inherit the user's PATH the way a shell would. The canonical pattern:

```xml
<key>ProgramArguments</key>
<array>
    <string>/Users/rig128gb/Developer/rig-intelligence/platform/founder-runtime/.venv/bin/python</string>
    <string>-m</string>
    <string>founder_runtime.worker</string>
    <string>--node-id</string>
    <string>rig-control-128gb</string>
</array>
```

Or wrap with a small shell script in `.venv/bin/<name>` and call that:

```xml
<key>ProgramArguments</key>
<array>
    <string>/Users/rig128gb/Developer/rig-intelligence/platform/founder-runtime/.venv/bin/<entrypoint></string>
    <string>--node-id</string>
    <string>rig-control-128gb</string>
</array>
```

The wrapper script:

```bash
#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")" && pwd)"
exec "$HERE/python" -m founder_runtime.worker "$@"
```

The wrapper approach is more debuggable (you can `bash -x .venv/bin/<entrypoint>` to see what it exec'd) and survives venv relocations better than hardcoded paths.

## Observed: macOS launchd stdout/stderr logging

`StandardOutPath` and `StandardErrorPath` create the file with mode 0600 (owner read/write only). The Hermes runtime groups permissions may make this awkward when Mike wants to inspect logs from a non-agent account. Document the mode at install time.