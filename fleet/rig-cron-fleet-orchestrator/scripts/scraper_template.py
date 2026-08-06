#!/usr/bin/env python3
"""Substrate-aware web scraper template.

Persists FULL body content (not just metadata), extracts entity pages
with ## Facts fence, enforces blocklist, and writes a per-cycle proof.

Usage:
  python3 scraper_template.py --dept gtm --sources "apollo:https://api.apollo.io/v1/,clay:https://api.clay.com/v1/"

Or `from scraper_template import scrape_sources` from another script.
"""
import argparse, json, urllib.request, urllib.error, time, os
from pathlib import Path
from datetime import datetime, timezone

DEPT_BASE = Path(os.environ.get("RIG_DEPT_BASE", "/Users/rig128gb/.rig/departments"))

# Hard blocklist — DO NOT REMOVE
GLOBAL_BLOCKLIST = ["HED", "IdeaWake", "dec-1783268304352-va5c", "dec-1783268340018-db8f",
                    "Anthony Langeweg", "hed-forge"]

MAX_BODY_BYTES = 1024 * 1024  # 1MB safety cap per source


def safe_scrape(url: str, timeout: int = 8):
    """Returns (status, size, body_text). Never raises."""
    try:
        req = urllib.request.Request(url, method="GET", headers={"User-Agent": "rig-scraper/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
            return (r.status, len(data), data.decode("utf-8", errors="ignore"))
    except urllib.error.HTTPError as e:
        return (e.code, 0, "")
    except Exception:
        return (0, 0, "")


def is_blocked(text: str) -> bool:
    tl = text.lower()
    return any(b.lower() in tl for b in GLOBAL_BLOCKLIST)


def scrape_sources(dept_id: str, sources: list, cycle_label: str = "scraper-cycle"):
    """Scrape each (name, url) pair. Persists metadata + full body + entity page."""
    base = DEPT_BASE / dept_id / "substrate" / "scraped"
    entities_base = DEPT_BASE / dept_id / "substrate" / "entities"
    base.mkdir(parents=True, exist_ok=True)
    entities_base.mkdir(parents=True, exist_ok=True)

    results = []
    total_bytes = 0
    blocklist_hits = []

    for src_name, url in sources:
        if is_blocked(url):
            blocklist_hits.append((src_name, url))
            continue

        status, size, body = safe_scrape(url)
        body_to_save = body[:MAX_BODY_BYTES] if body else ""

        artifact = {
            "source": src_name,
            "url": url,
            "status": status,
            "bytes": size,
            "body_truncated": body_to_save,
            "body_truncated_at": len(body_to_save),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "dept": dept_id,
            "cycle": cycle_label,
        }
        (base / f"{src_name}.json").write_text(json.dumps(artifact, indent=2))

        if size > 1000 and status == 200 and body_to_save:
            (base / f"{src_name}.raw").write_text(body_to_save)

        if size > 1000 and status == 200:
            entity_file = entities_base / f"{src_name}-entity-{int(time.time())}.md"
            facts = (
                "metric: endpoint_responsive\n"
                "value: 1\n"
                "unit: bool\n\n"
                "metric: response_bytes\n"
                f"value: {size}\n"
                "unit: bytes\n\n"
                "metric: body_preserved_bytes\n"
                f"value: {len(body_to_save)}\n"
                "unit: bytes"
            )
            entity_file.write_text(
                "---\n"
                f"type: {dept_id}_entity\n"
                f"source: {src_name}\n"
                f"url: {url}\n"
                f"status: {status}\n"
                f"scraped_at: {datetime.now(timezone.utc).isoformat()}\n"
                f"cycle: {cycle_label}\n"
                "---\n\n"
                f"# {src_name} — {dept_id} entity\n\n"
                "## Facts\n"
                f"{facts}\n\n"
                "## Body preview (first 800 chars)\n"
                "```\n"
                f"{body[:800]}\n"
                "```\n\n"
                "## Provenance\n"
                f"- Source: {src_name} ({url})\n"
                f"- HTTP status: {status}\n"
                f"- Bytes received: {size}\n"
                f"- Body preserved: {len(body_to_save)} bytes\n"
                f"- Raw body: substrate/scraped/{src_name}.raw\n"
                "- Blocklist check: PASSED\n\n"
                "## Notes\n"
                "REAL data scraped from upstream. Body persisted.\n"
            )
            total_bytes += size

        results.append({"source": src_name, "url": url, "status": status, "size": size})

    proof = {
        "schema_version": "rig.scraper.v1",
        "dept": dept_id,
        "cycle": cycle_label,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "sources_attempted": len(sources),
        "sources_succeeded": sum(1 for r in results if r["status"] == 200),
        "blocklist_hits": len(blocklist_hits),
        "total_bytes": total_bytes,
    }
    Path("/Users/rig128gb/.rig/state").mkdir(parents=True, exist_ok=True)
    Path(f"/Users/rig128gb/.rig/state/{dept_id}-scraper-proof.json").write_text(
        json.dumps(proof, indent=2))

    return {"dept": dept_id, "results": results, "proof": proof}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dept", required=True)
    p.add_argument("--sources", required=True, help='comma-separated name:url pairs')
    p.add_argument("--cycle", default="scraper-cycle")
    args = p.parse_args()

    sources = []
    for pair in args.sources.split(","):
        if ":" not in pair:
            continue
        name, url = pair.split(":", 1)
        sources.append((name.strip(), url.strip()))

    result = scrape_sources(args.dept, sources, args.cycle)
    print(json.dumps(result["proof"], indent=2))


if __name__ == "__main__":
    main()
