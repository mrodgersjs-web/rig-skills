---
name: rig-site-forensics
description: Trace where a RIG website is deployed, find old versions, and recover lost site content across Vercel, Cloudflare Pages, GitHub, and local directories. Use when Mike says a site "changed", "disappeared", "is wrong", or asks "where is the old version".
category: devops
---

# RIG Site Forensics

Trace, recover, and restore RIG websites across fragmented deployment infrastructure.

## When to Load

- Mike says a site "changed" or "disappeared"
- Need to find which Vercel project / CF Pages project serves a domain
- Need to recover an old version of a deployed site
- Domain was moved between projects and content swapped
- Mike says "we had the right one N days/weeks ago" and wants a rollback
- Interior routes return 404 but the homepage works (URL rewrite regression)

## RIG Site Map (update as projects change)

### Current Domain → Project Mapping (verified 2026-07-06)

| Domain | Vercel Project | GitHub Repo | Type | Vercel Project ID |
|---|---|---|---|---|
| **rodgersintelligence.com** | **site-v2** (current) | RIGIntelligence/rig-design-studio | Static HTML, noir design | **prj_A60q76PLNwVTi0OUYimBk9n1ui33** |
| mikerodgers.tech | (check Namecheap DNS) | — | — | — |
| rig-audit.rodgersintelligence.com | — | — | Subdomain | — |

### Historical Projects (domains may have moved)

| Vercel Project | ID | What it served | Status |
|---|---|---|---|
| rig-website | prj_Z55uzvJj2wbKR6h1ONcztlQJHqvN | Next.js — "AI Operations for the Enterprise" with booking/assessment/CO AI Law | Superseded by site-v2 |
| rig-os-site | prj_fBhcHFZWnEIjmoAAgcTDbcWnVAeO | Earlier 25,711-byte "AI is not a tool you buy" site | Replaced by site-v2 (late June 2026) |
| mike-rodgers-site | — | "The Fixer" personal site | Now on Cloudflare Pages only |
| rig-empire | — | RIG Intelligence Lab (agent marketplace) | — |

### Vercel Accounts

| Account | Team ID | Notes |
|---|---|---|
| michael-rodgers-projects-e4209a00 | team_4uvtoN6Mzf0JCzyR3ySQvXc5 | Primary team (token may expire) |
| rodgemd1-9353 | — | CLI auth account |

### GitHub Accounts

| Account | Use |
|---|---|
| RIGIntelligence | Primary org — public + private repos |
| rodgemd1-lgtm | Personal — older repos, some RIG infra |

## Investigation Procedure

### Step 1: Check what's live NOW

```bash
# DNS
dig rodgersintelligence.com +short

# HTTP headers (shows Vercel vs CF Pages)
curl -sI https://rodgersintelligence.com | grep -i "server\|x-vercel\|cf-ray"

# Title
curl -s https://rodgersintelligence.com | grep -o '<title>[^<]*</title>'

# Size — does it match local?
curl -sS https://<domain>/index.html -L -o /tmp/live.html
wc -c /tmp/live.html
```

### Step 2: Find the Vercel project

```bash
# List all deployments (works even when API token is expired)
npx vercel ls

# Check specific project's .vercel/project.json in local repos
find ~/Developer -maxdepth 4 -name "project.json" -path "*/.vercel/*" 2>/dev/null | xargs cat

# Check RIG-Estate-Map backups
ls ~/Desktop/RIG-Estate-Map/vercel_backup/
cat ~/Desktop/RIG-Estate-Map/vercel_backup/<project>.json
```

### Step 3: Identify the production deployment that serves the domain

This is the **canonical "what is live right now"** answer — gives the exact deployment ID and `createdAt` timestamp.

```bash
vercel inspect <domain> -F json 2>&1 | head -50
# Returns: id (dpl_...), name, url, target: production, createdAt, aliases, builds
```

Use `createdAt` (epoch ms) to correlate with `vercel ls` entries and Mike's local file timestamps.

### Step 4: Byte-exact match local source to live

The single most decisive diagnostic when "live looks wrong" — answers: is the live site stale or fresh?

```bash
curl -sS https://<domain>/index.html -L -o /tmp/live.html
md5 /tmp/live.html ~/Developer/<repo>/site-v2/index.html
# If md5 matches → live IS local working tree, problem is local or routing, NOT a stale deploy
# If md5 differs → there's a stale deploy OR local isn't what's deployed
```

Repeat for every important interior page (meet.html, hire-rig.html, hire-mike.html, proof.html, method.html, patents.html, governed-agents.html).

### Step 5: Find old deployments

```bash
# Old Vercel deployment URLs still work even after domain move
# Pattern: <project>-<hash>.vercel.app
# From `npx vercel ls` output, check each URL:
curl -s "https://<old-deployment-url>.vercel.app" | grep -o '<title>[^<]*</title>'

# The "olive" pattern: rig-website-olive.vercel.app
# These are Vercel's internal deployment aliases
```

**Limitation (verified 2026-07-06):** `vercel ls` only shows the most recent ~11 deploys by default. There is no `--limit` flag in Vercel CLI 54.18.0. Historical deploys older than that are not queryable from the CLI without their deployment ID. Wayback Machine (`https://archive.org/wayback/available?url=<domain>&timestamp=YYYYMMDD`) is the fallback — but RIG domains are often not crawled by archive.org. Both `vercel ls` and Wayback failed for the 2026-07-06 rodgersintelligence.com investigation; only the local repo + the byte-exact md5 comparison gave the answer.

### Step 6: Find the canonical "right one N days ago"

When Mike says "we had the right one N days ago", the canonical anchor is the **last committed state of the source repo** (HEAD of branch) — NOT the most recent local file (often uncommitted work-in-progress), NOT the `.prior*.html` files (those are intermediate authoring drafts marked `<meta name="robots" content="noindex">`), and NOT the most recent Vercel deploy (could be a thrash fix that broke things).

```bash
git log --all --pretty=format:"%h %ai %s" -- site-v2/ | head -20
git show HEAD:site-v2/index.html | wc -c   # canonical "before" byte count
```

If Mike wants to revert to a specific commit, the workflow is:
```bash
git checkout <commit-hash> -- site-v2/
cd site-v2 && vercel --prod
```

### Step 7: Search GitHub

```bash
# Both accounts
gh repo list RIGIntelligence --limit 200 --json name,description,updatedAt
gh api user/repos?per_page=100 --jq '.[] | "\(.name) | \(.updated_at[:10])"'

# Search for specific content
gh search repos "rodgersintelligence" --json name,fullName
gh search repos "rig-website" --json name,fullName
```

### Step 8: Search local filesystem

```bash
# Find Next.js projects
find ~/Developer -maxdepth 3 -name "next.config*" -not -path "*/node_modules/*"

# Find Vercel configs
find ~/Developer -maxdepth 4 -name ".vercel" -type d

# Search for content
grep -rl "search term" ~/Developer/ --include="*.html" --include="*.tsx" 2>/dev/null | grep -v node_modules
```

### Step 9: Cloudflare Pages

```bash
npx wrangler pages project list
# Check CF Pages URLs: <project>.pages.dev
```

## Common Pitfalls

1. **Vercel API token expires frequently** — Use `npx vercel ls` as fallback; it uses CLI auth which is more stable
2. **Domain move swaps entire site** — Moving a domain from Vercel project A to project B changes ALL content, not just the route being fixed
3. **Manual-deploy projects have no git** — `rig-website` had `gitRepo: null`; source code is only in local filesystem or Vercel's build cache
4. **`vercel ls` shows deployment URLs** — Old deployments are still accessible at their `*.vercel.app` URLs even after domain moves
5. **Multiple Vercel accounts** — `rodgemd1-9353` (CLI auth) vs `team_4uvtoN6Mzf0JCzyR3ySQvXc5` (API); token may work for one but not the other
6. **Mike describes sections by function, not literal text** — "Meet Mike" might be an `#origin` section; "Hire Mike" might be a `/book` page; search for related terms too
7. **rodgemd1-lgtm `gh api user/repos`** — Returns repos for the authenticated user, which IS rodgemd1-lgtm when that's the active gh account
8. **`.prior*.html` files are NOT canonical backups** — They're intermediate authoring drafts marked `<meta name="robots" content="noindex">`. DO NOT restore from them; use the last committed state. (Added 2026-07-06 — rodgersintelligence.com investigation found meet.prior.html was 53,865 bytes with noindex, vs the canonical committed meet.html at HEAD `f6ff1de` from 2026-06-22.)
9. **Interior 404 ≠ stale deploy** — When homepage (`/index.html`) works but interior routes return 404, suspect missing `vercel.json` rewrites, NOT a deployment mismatch. Check the `rewrites` array and compare to canonical patterns: `{ "source": "/<route>", "destination": "/<route>.html" }`. rodgersintelligence.com had this exact bug on 2026-07-06 — rewrites existed for `/governed-agents`, `/proof`, `/method` but NOT for `/meet`, `/hire-mike`, `/hire-rig`, `/patents`.
10. **Canonical URLs must match the routable URL** — If HTML has `<link rel="canonical" href=".../meet">` but no rewrite makes `/meet` serve `meet.html`, Google sees a soft-404 mismatch. The 2026-06-22 committed state used no-`.html` canonicals (relied on rewrites); a later uncommitted edit switched to `.html` canonicals while the rewrites were never added. Both must be updated together.
11. **`git status` after a long gap shows the real edit history** — A repo with hundreds of uncommitted changes is normal during Mike's site iteration cycles. Don't assume committed state reflects the live site. The diff between HEAD and the working tree is the actual surface area for the regression. (Verified 2026-07-06 — rig-design-studio had 467 files uncommitted since HEAD `f6ff1de`.)
12. **Mike does thrash deploys when stuck** — `vercel ls` for a "broken" RIG site may show 8-15 deploys in a single day, all by `rodgemd1-9353`. This signals Mike is iterating manually trying to fix something — don't assume the latest deploy is the intended state. Get Mike to articulate what the intended state IS, then compare to it.
13. **The session-search prior-corpus is the fastest context-loader** — Before any file inspection, search session history for "rodgersintelligence" or the target domain. Earlier sessions often extracted the brand identity, ran design audits, or explicitly stated what the live site "is supposed to be." This avoids re-doing work and surfaces Mike's prior intent.

## "Site is live but assets 404" — diagnostic triage (added 2026-07-06)

When Mike says "the site is live but the HTML renders with broken `<img>` / `<video>` / `<source>` tags", do NOT start by hunting the original asset files. The fix is almost always upstream of the bundle. Walk this triage:

### Tier 1 — Is the right project even responding?

**Symptom:** every static asset URL (`img/foo.webp`, `reels/bar.mp4`, etc.) returns `200 OK` but `content-type: text/html` and a body of ~20–60KB instead of the expected binary.

**Cause:** the domain's DNS/proxy is pointing at a DIFFERENT Vercel or Cloudflare Pages project than the one Mike expects. That wrong project is serving its own SPA shell (or an `index.html`) with a generous catch-all, so every unknown path returns the shell with `200 text/html`.

**Diagnostic:**
```bash
curl -sS https://<domain>/img/agents-130.webp -I --max-time 10
# Look at content-type — anything other than image/webp means wrong project (or wrong bundling)
curl -sS https://<domain>/img/agents-130.webp --max-time 10 | grep -o '<title>[^<]*</title>'
# If the title is NOT "Mike Rodgers" / RIG Intelligence / etc., it's the wrong project
```

**Fix:** move the domain to the correct project (Type 2 restoration playbook), or fix DNS, or redeploy the right project. Do NOT proceed to asset hunting until the right project is responding.

### Tier 2 — Is the apex DNS even healthy?

**Symptom (Cloudflare-proxied):** `https://<domain>/` returns Cloudflare's "Error 1001: DNS resolution error" page, but `https://www.<domain>/` works fine. Or `curl` returns `LibreSSL/3.3.6: error:1404B410:SSL routines:ST_CONNECT:sslv3 alert handshake failure` on apex but works on `www`.

**Cause:** Cloudflare SSL/TLS encryption mode is "Full" or "Full (Strict)" but no origin cert is provisioned at the apex, OR the apex A/AAAA records point to a CNAME setup that requires `www` to resolve first. Cloudflare Edge Certificates only auto-provision for the apex when DNS is correct.

**Diagnostic:**
```bash
dig <domain> +short @1.1.1.1
dig <domain> NS +short
curl -sS --resolve "<domain>:443:<expected-ip>" -I https://<domain>/ --max-time 10
# Compare to curl -sS -I https://www.<domain>/
```

**Workaround for testing during outage:** route through the browser tool (different TLS stack than macOS LibreSSL). For automated checks, prefer `https://www.<domain>/` paths if `www` is provisioned.

**Fix:** in Cloudflare dashboard → SSL/TLS → set encryption mode to "Flexible" temporarily, OR provision an origin cert at the apex, OR add an apex A record via Cloudflare (orange-clouded) so the universal SSL cert covers it.

### Tier 3 — Does the bundle actually contain the referenced files?

**Diagnostic (fast):**
```bash
# All asset references across all HTML
cd <site-root>
grep -rhoE '(src|href|poster|data-src)="[^"]*\.(mp4|webp|png|jpg|jpeg|svg|json|woff2?|ico|pdf|mp3|wav)"' \
  --include='*.html' . 2>/dev/null \
  | sed -E 's/^(src|href|poster|data-src)="//; s/"$//' \
  | sort -u > /tmp/all_assets.txt

# Compare against actual files
grep -vE '^(data:|https?://|#|javascript:|mailto:|tel:|\$)' /tmp/all_assets.txt \
  | while read p; do
      [ -e "$p" ] || echo "MISSING: $p"
    done
```

**Categorize each missing asset by fix type:**

| Pattern | Fix |
|---|---|
| Filename doesn't exist in bundle, but exists in source archive | `copy` from archive |
| Reference says `.webp` but file on disk is `.png` | `rename` (or ship both + patch HTML) |
| Reference points to `f1/assets-web/X.webp` but bundle ships `f1/` as a symlink OR not at all | `symlink-fix` or `copy-tree` |
| Reference points to filename that doesn't exist ANYWHERE on the Mac | `regenerate` (use Higgsfield / image_generate) |
| Reference is decorative (`srcset`, fallback) and a sensible default exists | `patch-html` to use the default |

### Tier 4 — Where the originals live

For `rodgersintelligence.com`-class builds, the canonical source archive is consistently:

```
~/RIG-Inbox/Direct-Transfer/Michaels-MacBook-Pro-2/Home-mikerodgers/Downloads/RIG Website (4)/uploads/
~/RIG-Inbox/Direct-Transfer/Michaels-MacBook-Pro-2/Home-mikerodgers/rig-site-assets/{reels,stills}/
~/rigintelligence-repos/rig-site-assets/{reels,stills}/
~/rigintelligence-repos/rig-site-assets/hero-{poster.jpg,reel.mp4}
~/Desktop/RIG-Estate-Map/_cf_migrate/mike-rodgers-site/assets/   # personal portrait variants
~/Library/Mobile Documents/com~apple~CloudDocs/Desktop/_ARCHIVE/completed-projects/rig-website-{images,videos}-*/
```

When a missing asset isn't in the bundle, search the archives above first. If absent there, check the staging uploader's `uploads/` directory (everything from `hf_YYYYMMDD_HHMMSS_*.{png,webp,mp4}` and named reels like `V4.1-deviation-lattice-rotate.mp4`, `V3-meet-mike-environmental.mp4`, etc. — those versioned filenames are stable).

### Tier 5 — Asset substitution matrix

| Missing filename in bundle | Best replacement from archive | Notes |
|---|---|---|
| `img/deviation-cover.webp` | `IMG-B1-deviation-cover.png` (in archive) | Rename to .webp or patch HTML |
| `img/mike-portrait.webp` | `mike-hero-final.webp` (in archive) | Direct match |
| `reels/hiremike-turn.mp4` | `reels/climb.mp4` or `cluster-tour.mp4` | Closest semantic match |
| `reels/rig-film.mp4` | `reels/rig.mp4` or `monogram.mp4` | Edit HTML to swap reference |
| `reels/rig-mike.mp4` | any hf_*.png of Mike → JPEG-encode | Decorative fallback |
| `uploads/hf_<uuid>.webp` (when only .png exists) | same path, `.png` extension | Patch HTML src to drop `.webp` suffix |
| `assets-web/1.1-mission-control-hero.webp` | `f1/assets-web/1.1-mission-control-hero.webp` | Ensure `f1/` dir is included in deploy |

### Tier 6 — `libreSSL 3.3.6` macOS TLS failure workaround

`curl` on macOS may fail with `error:1404B410:SSL routines:ST_CONNECT:sslv3 alert handshake failure` on Cloudflare-fronted sites, even when the browser opens them fine. This is the LibreSSL ↔ Cloudflare cipher-suite mismatch (especially post-2025 when CF enforces TLS 1.3+). Workarounds:

```bash
# Force a modern TLS profile
curl --tlsv1.3 -I https://<domain>/ 2>&1 | head -5
# (often fails too — CF may negotiate differently than expected)

# Use the browser tool which uses a separate TLS stack
browser_navigate(url="https://<domain>/some/asset.png")

# Use Python with requests (different SSL backend)
$HOME/.hermes/hermes-agent/venv/bin/python3 -c "
import requests
r = requests.get('https://<domain>/path', timeout=15, headers={'User-Agent':'Mozilla/5.0'})
print(r.status_code, r.headers.get('content-type'))
"
```

**Do not** waste iterations trying `--http2`, `--tls-max 1.2`, etc. — none of these reliably resolve LibreSSL ↔ Cloudflare. Move to a different tool.

## Restoration Playbook

### Type 1 — URL rewrite regression (interior 404s, homepage OK)

1. Identify the missing rewrites from `vercel.json`
2. Edit `vercel.json` to add the missing patterns (mirror existing successful ones):
   ```json
   { "source": "/meet",      "destination": "/meet.html" },
   { "source": "/hire-mike", "destination": "/hire-mike.html" },
   { "source": "/hire-rig",  "destination": "/hire-rig.html" },
   { "source": "/patents",   "destination": "/patents.html" }
   ```
3. `cd site-v2 && vercel --prod`
4. Verify all interior routes return 200:
   ```bash
   for p in meet hire-mike hire-rig proof method patents governed-agents; do
     curl -sI https://<domain>/$p | head -1
   done
   ```

### Type 2 — Domain move between Vercel projects

1. Find the old Vercel project (from Estate-Map backup or `vercel ls`)
2. Check if old deployment URL still serves correct content
3. Move domain via Vercel API or dashboard:
   ```bash
   # Remove from current project
   curl -X DELETE -H "Authorization: Bearer $TOKEN" \
     "https://api.vercel.com/v9/projects/<current>/domains/<domain>?teamId=$TEAM"
   # Add to old project
   curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
     -d '{"name":"<domain>"}' \
     "https://api.vercel.com/v9/projects/<old>/domains?teamId=$TEAM"
   ```
4. Verify: `curl -sI https://<domain> | grep x-vercel`

### Type 3 — Revert content to a specific commit

1. Identify the commit Mike wants restored: `git log --all --pretty=format:"%h %ai %s" -- site-v2/ | head -20`
2. **GATE D REQUIRED** — production deploys are irreversible without another deploy. Do not run `vercel --prod` without Mike's typed `APPROVE` per the Jake PAI doctrine.
3. `git checkout <commit-hash> -- site-v2/`
4. `cd site-v2 && vercel --prod`
5. Verify live = expected: `curl -sS https://<domain>/index.html | md5`

### Type 4 — Conservative hybrid (keep content, fix routing + canonicals)

When the issue is "Mike wants the URL behavior back but likes the new content":

1. Add the missing `vercel.json` rewrites (see Type 1)
2. Revert canonical URLs in HTML to the no-`.html` form (matching the original committed state)
3. `cd site-v2 && vercel --prod`
4. Verify routes AND canonicals:
   ```bash
   for p in meet hire-mike hire-rig; do
     echo -n "$p: "; curl -sI https://<domain>/$p | head -1
     curl -s https://<domain>/$p.html | grep -o 'rel="canonical" href="[^"]*"'
   done
   ```

## Related

- `references/rig-site-architecture.md` — domain registry, DNS records, project history
- `references/rig-intelligence-com-restoration-2026-07-06.md` — full transcript of the rodgersintelligence.com investigation (canonical example of this skill in action)
- `scripts/asset-triage.sh` — runnable 6-tier triage: tier-1 wrong-project oracle, tier-2 apex DNS, tier-3 bundle completeness scan, tier-4 archive lookup, tier-5 fix-type categorization. Invoke with `./scripts/asset-triage.sh <domain> <site-root>` before doing any manual asset hunting.