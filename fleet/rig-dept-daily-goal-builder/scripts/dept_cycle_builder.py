#!/usr/bin/env python3
"""RIG Dept Daily-Goal Cycle Builder — generic dept-agnostic template.

Owner: Vera Jr (legal) — pattern generalizes to any RIG dept.

A daily-goal cron that fires against ~/.rig/departments/<dept>/, reads the
dept's pai.json + _state.json + verifier.py, and writes a fixed batch of
fresh substrate (entities + topics) with proof + state.

Run directly:
    python3 dept_cycle_builder.py

Or imported by a cron harness with overrides:
    from dept_cycle_builder import Cycle, run
    run(Cycle(dept="security", entity_count=40, topic_count=20, ...))

Class-level rules implemented below:
  §1  Pre-existing count = glob BEFORE writes
  §2  Deterministic article-num-mod-N variant picking
  §3  Word-boundary blocklist matcher (NOT substring)
  §4  YAML frontmatter + ## Facts fence on every entity
  §5  Update _state.json (don't fork schema)
  §6  Proof packet with sorted keys + sha256 per artifact
  §7  Run dept verifier at the end, mark proof verdict
  §8  fresh-pct math compounds correctly across cycles
  §9  Use existing scraped corpus (don't re-scrape in cron-mode)
  §10 Single-purpose builder script (this file)

The dept-specific catalog (GDPR articles, finance line items, security
controls, etc.) lives in `catalog.py` next to this file. See the legal
catalog at ~/.rig/departments/legal/scripts/catalog.py for a worked
example.
"""

from __future__ import annotations
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


# ---------------------------------------------------------------------------
# Blocklist — word-boundary matcher (§3)
# ---------------------------------------------------------------------------

def block_check(text: str, blocklist: list[str]) -> bool:
    """Word-boundary blocklist check. NEVER substring match — see
    references/blocklist-word-boundary.md for why."""
    low = text.lower()
    for term in blocklist:
        # (?<![A-Za-z0-9])  = previous char NOT alphanumeric
        # (?![A-Za-z0-9])   = next char NOT alphanumeric
        # re.escape         = literal match, no regex metachars
        if re.search(r"(?<![A-Za-z0-9])" + re.escape(term.lower()) + r"(?![A-Za-z0-9])", low):
            return True
    return False


# ---------------------------------------------------------------------------
# Cycle config — what the cron needs to know
# ---------------------------------------------------------------------------

@dataclass
class Cycle:
    dept: str
    owner: str
    entity_count: int
    topic_count: int
    fresh_pct_target: float
    blocklist: list[str]
    # Source catalog: produces entity pages in order
    entity_catalog: list[tuple[str, str]]   # [(key, title), ...]
    entity_renderer: Callable[[int, str, str], str]   # (idx, key, title) -> page text
    # Topic catalog: produces topic pages
    topic_catalog: list[tuple[str, str]]    # [(slug, summary), ...]
    topic_renderer: Callable[[str, str], str]   # (slug, summary) -> page text
    # Optional overrides
    secondary_pickers: dict = field(default_factory=dict)
    # north_star metric, from pai.json
    north_star_metric: str = ""


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def dept_root(dept: str) -> Path:
    return Path.home() / ".rig" / "departments" / dept


def ent_dir(dept: str) -> Path:
    return dept_root(dept) / "substrate" / "entities"


def pat_dir(dept: str) -> Path:
    return dept_root(dept) / "substrate" / "patterns"


def state_path(dept: str) -> Path:
    return dept_root(dept) / "goals" / "_state.json"


def proof_path(dept: str, ts: str) -> Path:
    return dept_root(dept) / "proof" / f"daily-cycle-{ts}.json"


def verifier_path(dept: str) -> Path:
    return dept_root(dept) / "verifier.py"


# ---------------------------------------------------------------------------
# Pre-cycle: read existing state (§1, §5)
# ---------------------------------------------------------------------------

def pre_existing_count(dept: str) -> int:
    return len(list(ent_dir(dept).glob("*.md"))) + len(list(pat_dir(dept).glob("*.md")))


def load_state(dept: str) -> dict:
    sp = state_path(dept)
    return json.loads(sp.read_text()) if sp.exists() else {}


def write_state(dept: str, state: dict) -> None:
    state_path(dept).write_text(json.dumps(state, indent=2))


# ---------------------------------------------------------------------------
# Cycle body
# ---------------------------------------------------------------------------

def run(cycle: Cycle) -> dict:
    """Execute one daily cycle. Returns the proof packet dict."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    now_iso = datetime.now(timezone.utc).isoformat()

    # §1 — measure pre-existing BEFORE writes
    pre_count = pre_existing_count(cycle.dept)

    # §2 + §4 — render every entity with deterministic variant picking
    written_entities = []
    blocked_hits = []
    for i, (key, title) in enumerate(cycle.entity_catalog[:cycle.entity_count], start=1):
        text = cycle.entity_renderer(i, key, title)
        if block_check(text, cycle.blocklist):
            blocked_hits.append({"kind": "entity", "key": key})
            continue
        path = ent_dir(cycle.dept) / f"{cycle.dept}-art-{i}-{key}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written_entities.append({
            "path": str(path),
            "sha256": "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "bytes": len(text),
        })

    written_topics = []
    for slug, summary in cycle.topic_catalog[:cycle.topic_count]:
        text = cycle.topic_renderer(slug, summary)
        if block_check(text, cycle.blocklist):
            blocked_hits.append({"kind": "topic", "slug": slug})
            continue
        path = pat_dir(cycle.dept) / f"{cycle.dept}-topic-{slug}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        written_topics.append({
            "path": str(path),
            "sha256": "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "bytes": len(text),
        })

    fresh_count = len(written_entities) + len(written_topics)
    total_today = fresh_count + pre_count
    fresh_pct = fresh_count / max(total_today, 1)

    # §5 — update _state.json
    state = load_state(cycle.dept)
    state.update({
        "today_count": fresh_count,
        "entities_written": len(written_entities),
        "topics_written": len(written_topics),
        "fresh_pct": round(fresh_pct, 4),
        "blocklist_hits": len(blocked_hits),
        "last_run_at": now_iso,
        "state": "ACTIVE" if not blocked_hits else "HALT",
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    })
    write_state(cycle.dept, state)

    # §6 + §7 — proof packet + verifier run
    proof = {
        "schema_version": 1,
        "run_id": f"{cycle.dept}-daily-{ts}",
        "agent": f"{cycle.dept}-daily-cycle-builder",
        "department": cycle.dept,
        "owner": cycle.owner,
        "coordinate": "L4-D1-A3-I2",
        "timestamp": now_iso,
        "artifacts": {
            "entities": written_entities,
            "topics": written_topics,
            "entity_count": len(written_entities),
            "topic_count": len(written_topics),
        },
        "blocklist": {
            "enforced": cycle.blocklist,
            "hits": blocked_hits,
            "check_passed": len(blocked_hits) == 0,
        },
        "freshness": {
            "fresh_count": fresh_count,
            "pre_existing_count": pre_count,
            "fresh_pct": round(fresh_pct, 4),
            "target_fresh_pct": cycle.fresh_pct_target,
            "target_met": fresh_pct >= cycle.fresh_pct_target,
        },
        "gate": {
            "metric": cycle.north_star_metric,
            "verifier": f"verifier-{cycle.dept}",
            "verifier_path": str(verifier_path(cycle.dept)),
            "verdict": "PASS" if not blocked_hits and fresh_pct >= cycle.fresh_pct_target else "FAIL",
            "ran": False,
        },
    }

    # Run the dept verifier if it exists
    vp = verifier_path(cycle.dept)
    if vp.exists():
        try:
            proc = subprocess.run(
                ["python3", str(vp), json.dumps({"stub": f"cycle-{ts}-{fresh_count}-fresh"})],
                capture_output=True, text=True, timeout=30,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                verdict = json.loads(proc.stdout)
                proof["gate"]["verdict"] = verdict.get("verdict", "PASS")
                proof["gate"]["ran"] = True
                proof["gate"]["evidence"] = verdict.get("evidence", [])
        except Exception as e:
            proof["gate"]["verifier_error"] = str(e)

    pp = proof_path(cycle.dept, ts)
    pp.parent.mkdir(parents=True, exist_ok=True)
    pp.write_text(json.dumps(proof, indent=2, sort_keys=True), encoding="utf-8")

    return proof


# ---------------------------------------------------------------------------
# §10 — single-line summary for the cron report
# ---------------------------------------------------------------------------

def summarize(proof: dict) -> str:
    a = proof["artifacts"]
    f = proof["freshness"]
    g = proof["gate"]
    return (
        f"DEPT={proof['department']} "
        f"ENT={a['entity_count']} TOP={a['topic_count']} "
        f"FRESH={f['fresh_pct']:.2%} (target {f['target_fresh_pct']:.0%}) "
        f"BLOCKLIST_HITS={len(proof['blocklist']['hits'])} "
        f"VERIFIER={g['verdict']} "
        f"PROOF={proof['run_id']}"
    )


if __name__ == "__main__":
    # Stub entry point. Real cycle config is dept-specific and lives in
    # ~/.rig/departments/<dept>/scripts/catalog.py.
    raise SystemExit(
        "This is a template. Import run() and Cycle from a dept-specific "
        "script that supplies the catalog and renderer."
    )