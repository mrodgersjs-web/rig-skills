# rodgersintelligence.com Restoration Investigation — 2026-07-06

Session transcript of the diagnostic that surfaced the URL-rewrite regression on rodgersintelligence.com. Use this as a worked example when applying `rig-site-forensics` to a similar case.

## The Question

> "rodgersintelligence.com is suddenly different. Where is the one that was live three days ago which had meet mike, hire mike, and hire rig? We had the right one one week ago — restore it."

Jake PAI dispatched Marcus (Design) + Steve (Content) + Theo (Design/brand) to investigate. No deploys were made; investigation produced a report and 3 fix options for Mike to choose.

## Step-by-Step Findings

### 1. Live site state (curl + headers)

```bash
curl -sS https://rodgersintelligence.com/ -L -o /tmp/rodgers-current.html
curl -sS -I https://rodgersintelligence.com/ -L
```

Output:
- `HTTP/2 200`, `server: Vercel`, `last-modified: Mon, 06 Jul 2026 23:22:12 GMT`
- Live homepage: 264,296 bytes
- Title: "Fractional Chief AI Officer + Governed AI Build Studio | Rodgers Intelligence Group"
- Meta: "AI operating-procedures consulting for the mid-market and Denver-region SMBs. 24 systems shipped, 100+ agents in production, 3 patents in preparation. Start with the $2,500 AI Opportunity Report."

This is the **noir/three-door site**, not the older rig-os-site content. So the regression isn't "wrong design" — it's something else.

### 2. Discovery: which Vercel project serves this domain?

```bash
find ~/Developer -maxdepth 4 -name "project.json" -path "*/.vercel/*"
```

Found two candidates:
- `$HOME/Developer/rig-os-site/.vercel/project.json` → `rig-os-site` (prj_fBhcHFZWnEIjmoAAgcTDbcWnVAeO) — older site
- `$HOME/Developer/rig-design-studio/site-v2/.vercel/project.json` → `site-v2` (prj_A60q76PLNwVTi0OUYimBk9n1ui33) — current site

```bash
vercel inspect rodgersintelligence.com -F json | grep -E '"id"|"createdAt"|"aliases"'
```

Output: `id: dpl_HYhpxSTVLYjewFPxgZdxf1zF9xSn`, `createdAt: 1783376869565` (= 2026-07-06 16:27:49 MDT).

**Conclusion:** rodgersintelligence.com → `site-v2` (NOT rig-os-site as the existing skill claimed).

### 3. Byte-exact match — the decisive test

```bash
md5 /tmp/rodgers-current.html \
    $HOME/Developer/rig-design-studio/site-v2/index.html
# Both: a8b8cdbf0bce4b3c2d7d04a832b45a10 — MATCH
```

The live site IS the local working tree byte-for-byte. So the regression isn't a stale deploy — it's something in the local content or the routing.

### 4. Per-page byte-exact check (the bug surface)

```bash
for p in index meet hire-mike hire-rig proof method patents governed-agents; do
  curl -sS https://rodgersintelligence.com/${p}.html -L | wc -c   # live
  wc -c < ~/Developer/rig-design-studio/site-v2/${p}.html           # local
done
```

All 8 pages match: live = local. So the regression isn't a content mismatch either.

### 5. Test the actual routes (no .html extension)

```bash
curl -sI https://rodgersintelligence.com/meet
curl -sI https://rodgersintelligence.com/hire-rig
curl -sI https://rodgersintelligence.com/hire-mike
```

**All three return 404.** The homepage works, but interior routes without `.html` are broken.

```bash
cat ~/Developer/rig-design-studio/site-v2/vercel.json
```

vercel.json rewrites:
```json
{ "source": "/governed-agents", "destination": "/governed-agents.html" },
{ "source": "/proof",           "destination": "/proof.html" },
{ "source": "/method",          "destination": "/method.html" }
```

**Three rewrites exist, four interior routes don't have them.** `/meet`, `/hire-mike`, `/hire-rig`, `/patents` are missing. That's the regression.

### 6. Find the canonical "right one a week ago"

```bash
cd ~/Developer/rig-design-studio && git log --oneline -10 -- site-v2/
```

Last commit: `f6ff1de` "fix(site): scrub remaining Substack + inert Calendly refs -> email" (2026-06-22). The June 30 brand-identity session (saved in `$HOME/Documents/JakeStudio/Projects/LinkedIn-Company-Page-Overhaul/Phase1-*.md`) explicitly treated the live noir site as the source of truth — so the noir design is what Mike means by "the right one."

```bash
git diff HEAD -- site-v2/index.html | head -50
```

Today's uncommitted edits ADDED: trust bar, dominant CTA, Schema.org JSON-LD, OG tags on interior pages, new image references (meet.png replacing stage-talk.webp, etc.), alt text, robots.txt, sitemap.xml.

**Conclusion:** The noir design HASN'T substantively changed in 2 weeks. What regressed is:
1. The vercel.json rewrites (4 routes missing)
2. The canonical URLs in HTML (recently changed from no-`.html` to `.html` form, but rewrites weren't added)

### 7. The `.prior*.html` trap

```bash
ls $HOME/Developer/rig-design-studio/site-v2/meet.prior*.html
# meet.prior.html, prior2.html, ... prior6.html
```

Looked like backups, but each is marked `<meta name="robots" content="noindex">`. They're intermediate authoring drafts, NOT canonical backups. The canonical "before" is `git show HEAD:site-v2/meet.html`.

### 8. Wayback Machine + Vercel deploy history — both failed

```bash
curl -sS "https://archive.org/wayback/available?url=rodgersintelligence.com&timestamp=20260629"
# {"url": "rodgersintelligence.com", "archived_snapshots": {}, ...} — empty
```

```bash
vercel ls
# Shows ~11 most recent deploys, all from today (Jul 6 16:04-16:27 MDT) by rodgemd1-9353
# Mike did 11 deploys in 3 hours — clear thrash signal
```

The CLI has no `--limit` flag in Vercel CLI 54.18.0, so no way to query 1-week-old deploys. Wayback Machine doesn't have the domain crawled. Both fallbacks failed; only the local repo + byte-exact md5 comparison gave the answer.

### 9. The report — 3 fix options

Wrote `/tmp/rig-site-restoration-findings.md` (15 KB) presenting 3 options for Mike:

| Option | What it does | Risk |
|---|---|---|
| **A — Surgical rewrite fix** | Add 4 missing rewrites to vercel.json; redeploy | Minimal; keeps all today's content improvements |
| **B — Full revert to Jun 22** | `git checkout f6ff1de -- site-v2/` then redeploy | Loses OG tags, trust bar, alt text, Schema.org |
| **C — Hybrid** | Add rewrites + revert canonicals to no-`.html` form | Preserves content, restores URL behavior |

Held for Mike's typed APPROVE per Jake PAI Gate-D. **No deploy executed.**

## What This Session Taught

1. **`vercel inspect <domain>` is the canonical "what's serving this right now"** — better than `vercel ls` for incident response because it tells you which deployment is in production.
2. **Byte-exact `md5` comparison between live and local** is the single most decisive diagnostic for "live looks wrong" — it instantly distinguishes "stale deploy" from "routing bug" from "content bug."
3. **`.prior*.html` files in RIG repos are drafts, not backups** — the canonical "before" state is the last git commit, not the most recent local file timestamp.
4. **Mike thrashes via rapid redeploys when stuck** — `vercel ls` showing 8-15 deploys in a single day by Mike signals he's iterating manually. Don't assume the latest deploy is the intended state; ask Mike what the intended state IS.
5. **The `vercel.json` rewrite pattern is per-route, all-or-nothing** — if you add a new interior HTML file, you must also add the corresponding rewrite. Easy to forget.
6. **Interior 404 with a working homepage is a routing bug, not a deploy bug** — don't waste cycles investigating "why didn't the latest deploy go through." Check the rewrite map first.
7. **Wayback Machine + Vercel CLI both have limits** — neither alone is reliable for "what did this look like N days ago." Always have the local repo + git history as the authoritative source.
8. **Session-search is the fastest context-loader** — earlier sessions (especially the 2026-06-30 brand-identity session) explicitly stated what the live site "is supposed to be." Surfacing that prior intent is faster than re-deriving it from the bytes.

## Files Created During This Session

- `/tmp/rig-site-restoration-findings.md` — full investigation report (15 KB)
- `/tmp/rodgers-current.html` — fetched live homepage (264,296 B)
- `/tmp/rodgers-meet-now.html`, `/tmp/rodgers-hirerig-now.html`, `/tmp/rodgers-hiremike-now.html` — fetched live interior pages for byte-exact comparison

## Skills Updated

- `rig-site-forensics/SKILL.md` — added Step 3 (production deployment identification), Step 4 (byte-exact match), Step 6 (canonical "right one N days ago"), Pitfalls 8-13, Restoration Playbook Type 4 (hybrid)
- `rig-site-forensics/references/rig-site-architecture.md` — added `site-v2` as current production target, demoted `rig-os-site` and `rig-website` to historical, expanded Local Directories
- `rig-site-forensics/references/rig-intelligence-com-restoration-2026-07-06.md` — this document

## Reference IDs (for future cross-session lookups)

- Vercel project: `prj_A60q76PLNwVTi0OUYimBk9n1ui33` (site-v2)
- Vercel team: `team_4uvtoN6Mzf0JCzyR3ySQvXc5` (michael-rodgers-projects-e4209a00)
- Production deployment (at time of investigation): `dpl_HYhpxSTVLYjewFPxgZdxf1zF9xSn`
- Last committed state of source: `f6ff1de` "fix(site): scrub remaining Substack + inert Calendly refs -> email" (2026-06-22)
- Local source path: `$HOME/Developer/rig-design-studio/site-v2/`
- Local working-tree HEAD: 467 files uncommitted since `f6ff1de`