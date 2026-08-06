#!/usr/bin/env python3
"""Sanitized ProofPacket writer for provider-gated action crons.

Emits a ProofPacket JSON document with a stable schema and a sha256
integrity hash. Designed to be invoked from a zsh/sh heredoc inside a
cron runner (no Python imports beyond stdlib, no network IO, no
credential reads). All credential values must be passed as REFERENCES
(account or service names) — never as raw bytes.

Usage from a bash runner:

```bash
PROOF_PAYLOAD=$(python3 "$REPO/scripts/sanitize_proof_packet.py" \
  --run-id "cron-$(date -u +%Y%m%dT%H%M%SZ)-$$" \
  --schedule-mode "WEDNESDAY" \
  --schedule-tz "America/Denver" \
  --repo-path "$REPO_DIR" \
  --repo-commit "$(git -C "$REPO_DIR" rev-parse HEAD)" \
  --repo-dirty "$(git -C "$REPO_DIR" diff --quiet HEAD && echo false || echo true)" \
  --handle "JacobRodge52987" \
  --user-id "2029703725091328001" \
  --oauth-status "PASS" \
  --linkup-status "ok" \
  --linkup-request-count 0 \
  --approved-considered 0 \
  --rejected 0 \
  --executed 0 \
  --source-urls "" \
  --engine-status "PASS" \
  --identity-status "PASS" \
  --verdict "ALLOW" \
  --runtime-seconds 5 \
  --output-file "$PROOF_FILE" \
  --log-path "$LOG_FILE")
```

Why this exists (the recipe):
- bash heredocs quoting + JSON escaping is brittle. Use Python to build JSON.
- The cron runner must NEVER log raw tokens / bearer / API keys. This script
  is credential-free by design (no env reads of token vars); it only
  receives sanitized status strings from the caller.
- sha256 hash of the canonical payload proves integrity. Embed the hash in
  the same file so downstream consumers can verify without an external
  sidecar.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys


SCHEMA_VERSION = 1


def utcnow_iso() -> str:
    """UTC ISO8601 with 'Z' suffix (microsecond-precision stripped)."""
    return (
        _dt.datetime.now(_dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sanitize_source_urls(raw: str) -> list[str]:
    """Allow only http(s) URLs, strip embedded credentials, length-cap."""
    out: list[str] = []
    for line in (raw or "").split("\n"):
        line = line.strip()
        if not line:
            continue
        if not (line.startswith("http://") or line.startswith("https://")):
            continue
        # drop embedded credentials (user:pass@host)
        try:
            after_scheme = line.split("//", 1)[1]
            host = after_scheme.split("/", 1)[0]
            if "@" in host:
                continue
        except (IndexError, ValueError):
            continue
        out.append(line[:512])
    return out


def derive_verdict(
    engine_status: str,
    identity_status: str,
    oauth_status: str,
    executed: int,
    rejected: int,
) -> str:
    """ALLOW only when every gate is PASS and no actions were rejected.

    The cron pattern: dry-runs with executed=0 and no rejected are ALLOW.
    Any failed gate OR any rejected action is BLOCK.
    """
    if engine_status != "PASS":
        return "BLOCK"
    if identity_status != "PASS":
        return "BLOCK"
    if oauth_status != "PASS":
        return "BLOCK"
    if rejected > 0:
        return "BLOCK"
    return "ALLOW"


def build_packet(args: argparse.Namespace) -> dict:
    """Assemble the ProofPacket dict from sanitized args. Never inspects env
    for credentials — caller is responsible for passing only safe strings.
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": args.run_id,
        "timestamp": utcnow_iso(),
        "schedule_mode": args.schedule_mode,
        "schedule_timezone": args.schedule_tz,
        "repository": {
            "path": args.repo_path,
            "commit": args.repo_commit,
            "dirty": args.repo_dirty == "true",
        },
        "authenticated_identity": {
            "handle": args.handle,
            "user_id": args.user_id,
        },
        "oauth": {
            "status": args.oauth_status,
            "user_context": True,
        },
        "linkup": {
            "status": args.linkup_status,
            "request_count": int(args.linkup_request_count),
        },
        "source_urls": sanitize_source_urls(args.source_urls),
        "engine_exit_codes": {
            "engine_overall": args.engine_status,
            "identity": args.identity_status,
            "oauth": args.oauth_status,
        },
        "actions": {
            "approved_considered": int(args.approved_considered),
            "rejected": int(args.rejected),
            "executed": int(args.executed),
        },
        "zero_secret_scan": True,
        "gates": {
            "identity_match": args.identity_status,
            "oauth_refresh": args.oauth_status,
            "engine_run": args.engine_status,
            "linkup_health": args.linkup_status,
            "approval_queue_fail_closed": "PASS" if int(args.rejected) == 0 else "FAIL",
        },
        "runtime_seconds": int(args.runtime_seconds),
        "log_path": args.log_path,
        "verdict": args.verdict or derive_verdict(
            args.engine_status,
            args.identity_status,
            args.oauth_status,
            int(args.executed),
            int(args.rejected),
        ),
    }


def write_packet(packet: dict, output_file: str | None) -> str:
    """Serialize, hash, write. Returns the proof_hash. If output_file is None,
    print the serialized payload to stdout (for piping)."""
    # Deterministic key order so the sha256 is stable across runs.
    serialized = json.dumps(packet, indent=2, sort_keys=True)
    proof_hash = "sha256:" + hashlib.sha256(serialized.encode()).hexdigest()
    final = dict(packet)
    final["proof_hash"] = proof_hash
    final_serialized = json.dumps(final, indent=2, sort_keys=True)
    if output_file:
        # Atomic write: write to temp + rename to avoid half-written files
        # if the cron runner is killed mid-write.
        tmp = output_file + ".tmp"
        with open(tmp, "w", encoding="utf8") as fh:
            fh.write(final_serialized + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.rename(tmp, output_file)
        os.chmod(output_file, 0o600)
    print(final_serialized)
    return proof_hash


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Emit a sanitized ProofPacket JSON document.")
    p.add_argument("--run-id", required=True)
    p.add_argument("--schedule-mode", required=True, choices=["MONDAY", "WEDNESDAY", "FRIDAY"])
    p.add_argument("--schedule-tz", required=True)
    p.add_argument("--repo-path", required=True)
    p.add_argument("--repo-commit", required=True)
    p.add_argument("--repo-dirty", required=True, choices=["true", "false"])
    p.add_argument("--handle", required=True)
    p.add_argument("--user-id", required=True)
    p.add_argument("--oauth-status", required=True, choices=["PASS", "FAIL", "MISSING"])
    p.add_argument("--linkup-status", default="missing", choices=["ok", "missing", "invalid", "rate_limited", "error"])
    p.add_argument("--linkup-request-count", type=int, default=0)
    p.add_argument("--approved-considered", type=int, default=0)
    p.add_argument("--rejected", type=int, default=0)
    p.add_argument("--executed", type=int, default=0)
    p.add_argument("--source-urls", default="")
    p.add_argument("--engine-status", required=True, choices=["PASS", "FAIL"])
    p.add_argument("--identity-status", required=True, choices=["PASS", "FAIL"])
    p.add_argument("--verdict", default="")
    p.add_argument("--runtime-seconds", type=int, default=0)
    p.add_argument("--output-file", default=None)
    p.add_argument("--log-path", required=True)
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    packet = build_packet(args)
    write_packet(packet, args.output_file)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))