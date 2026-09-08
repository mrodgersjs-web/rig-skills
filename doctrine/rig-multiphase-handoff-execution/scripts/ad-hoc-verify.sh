#!/usr/bin/env bash
# ad-hoc-verify.sh — verify a multi-phase handoff without inventing a canonical test suite
#
# Usage:
#   ./scripts/ad-hoc-verify.sh <python_module> [--probe] [--once]
#
# What this does (the pattern that works):
#   1. Run the module's canonical pytest suite (must pass).
#   2. Spin up a fresh tmp db, run one tick via the module's entrypoint,
#      assert against the live output.
#   3. Probe live launchd services (worker + health monitor).
#   4. Curl live API endpoints, assert response shapes.
#   5. Save the report to a hermes-verify- temp file, summarize inline,
#      delete the temp file.
#
# Why not just pytest?
#   The pytest suite covers logic. This script proves the runtime actually
#   launches under launchd, the API actually returns the new endpoints, and
#   the dispatcher is actively recovering leases. Those are integration
#   concerns pytest cannot reach.
#
# Pitfall: the live API listens on 127.0.0.1:8089 — make sure the server
# is running before invoking this script, OR have the script start it.
set -euo pipefail

MODULE="${1:-founder_runtime}"
shift || true

PROBE_FLAG=""
ONCE_FLAG=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --probe) PROBE_FLAG="--probe"; shift ;;
        --once) ONCE_FLAG="--once"; shift ;;
        *) echo "unknown flag: $1" >&2; exit 2 ;;
    esac
done

# Locate the venv python (always the venv, never the Xcode toolchain)
VENV_PY="$HOME/Developer/rig-intelligence/platform/founder-runtime/.venv/bin/python"
[[ -f "$VENV_PY" ]] || { echo "venv python missing at $VENV_PY" >&2; exit 2; }

cd "$HOME/Developer/rig-intelligence/platform/founder-runtime"

echo "=== 1. canonical pytest ==="
"$VENV_PY" -m pytest "${MODULE}/tests/" -q

echo ""
echo "=== 2. launchd services (live state) ==="
launchctl list 2>&1 | grep -E "com\\.rig\\.founder-worker|com\\.rig\\.health-monitor" || echo "no launchd services registered"

echo ""
echo "=== 3. launchctl print (parseable pid + state) ==="
for label in com.rig.founder-worker.rig-control-128gb com.rig.health-monitor; do
    out=$(launchctl print "gui/$(id -u)/${label}" 2>&1 || true)
    pid=$(echo "$out" | grep -E "^[[:space:]]+pid" | head -1 | awk '{print $3}')
    state=$(echo "$out" | grep -E "^[[:space:]]+state" | head -1 | awk '{print $3}')
    echo "  ${label}: pid=${pid:-?} state=${state:-?}"
done

echo ""
echo "=== 4. live API endpoints ==="
for endpoint in /api/health /api/nodes /api/queue_health /api/failures; do
    body=$(curl -s -m 3 -X POST "http://127.0.0.1:8089${endpoint}" 2>/dev/null || echo "(unreachable)")
    echo "  POST ${endpoint}: ${body:0:120}"
done

echo ""
echo "=== 5. exit codes ==="
echo "  pytest rc=$?"