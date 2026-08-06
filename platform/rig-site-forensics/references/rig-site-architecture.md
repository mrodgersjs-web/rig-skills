# RIG Site Architecture — As of 2026-07-06

## Vercel Projects (michael-rodgers-projects-e4209a00)

### site-v2 (prj_A60q76PLNwVTi0OUYimBk9n1ui33) — CURRENT for rodgersintelligence.com
- **Framework**: Static HTML (Vercel `@vercel/vc-build`, no framework preset)
- **GitHub**: RIGIntelligence/rig-design-studio (branch `feat/meet-mike-patents-rebuild`)
- **Domains**: rodgersintelligence.com (and `site-v2-one-sable.vercel.app` etc.)
- **Local source**: `~/Developer/rig-design-studio/site-v2/`
- **HEAD commit (as of 2026-07-06)**: `f6ff1de` "fix(site): scrub remaining Substack + inert Calendly refs -> email" (2026-06-22)
- **Working tree**: 467 files uncommitted since HEAD — includes SEO meta tags, Schema.org, trust bar, dominant CTA, new image references
- **Content**: "Fractional Chief AI Officer + Governed AI Build Studio | Rodgers Intelligence Group"
  - Noir design system: `#000` base, `#C8A96E` gold, Cormorant Garamond + Hanken Grotesk + JetBrains Mono
  - 3 doors: Meet Mike · Hire Mike · Hire RIG
  - 8 verticals: Construction · Law · Med Spa · Healthcare · Dentistry · CPA · Services · Manufacturing
  - Hero video + audio beds + film grain + WebGL canvas
  - Pages: index, meet, hire-mike, hire-rig, method, proof, patents, governed-agents, ai-is-a-car, ai-readiness-assessment, denver-ai-consultant, fractional-caio-cost, fractional-caio-guide, plus 8 vertical-*.html
- **Deploy**: `vercel --prod` from `site-v2/`; rewrites in vercel.json for `/governed-agents`, `/proof`, `/method` ONLY — missing for `/meet`, `/hire-mike`, `/hire-rig`, `/patents` (causes 404 on those routes without `.html`)

### rig-website (prj_Z55uzvJj2wbKR6h1ONcztlQJHqvN) — SUPERSEDED
- **Framework**: Next.js (manual deploy, no git repo)
- **Domains**: was www.mikerodgers.tech, rodgersintelligence.com — now points to site-v2
- **Content**: "Rodgers Intelligence Group | AI Operations for the Enterprise"
  - Nav: Method · Services · Proof · CO AI Law · Book a Call
  - Colorado SB 24-205 compliance banner
  - Hero: "95% of AI pilots fail. The other..."
  - Services: AI Opportunity Report, CO AI Law Risk Check, Process Automation Audit, One Workflow Automated, Agent Build Pack, IntOps Program Director, Fractional AI Operator
  - Assessment quiz, booking flow
- **Status**: Domains moved off this project (rig-os-site in early July, then site-v2 in late June). Old deployment still accessible at rig-website-olive.vercel.app

### rig-os-site (prj_fBhcHFZWnEIjmoAAgcTDbcWnVAeO) — SUPERSEDED
- **Framework**: Static HTML
- **GitHub**: RIGIntelligence/rig-os-site
- **Domains**: rodgersintelligence.com briefly (early July 2026, replaced by site-v2 in late June — order may be site-v2 then rig-os-site then back)
- **Content**: "Rodgers Intelligence Group" corporate site
  - Nav: Solutions (Local/Mid-Market/PE/Enterprise) · Industries (Healthcare/Fleet/Manufacturing) · IntOps · Case Studies · Pricing · About · Contact
  - Hero: "AI is not a tool you buy. It is a business function you build."
  - 17 HTML pages including rig-lab.html (agent marketplace)
  - 25,711-byte homepage

### rig-empire
- **GitHub**: RIGIntelligence/rig-empire
- **Content**: "RIG Intelligence Lab — Stop Learning AI. Start Operating It."
  - Agent marketplace, Skool community, YouTube hub
  - 408 agents, 935 skills

## Cloudflare Pages Projects

### mike-rodgers-site (mike-rodgers-site.pages.dev)
- **GitHub**: RIGIntelligence/mike-rodgers-site
- **Content**: "Mike Rodgers — The Fixer | Chief AI Officer"
  - Sections: Hero, Origin, Pattern, System, Why Now, 100 Days, Ask Me (Jake AI), Panel (hiring legends), Fit Check
  - Has headshot images, app.js (51KB), styles.css
  - V8.4 restore commit + RIG V10 readiness overlay

## GitHub Repos — Site-Related

| Repo | Account | Description |
|---|---|---|
| **rig-design-studio** | RIGIntelligence | **CURRENT** noir/three-door site source for rodgersintelligence.com |
| rig-os-site | RIGIntelligence | Earlier 25,711-byte "AI is not a tool" version (superseded) |
| mike-rodgers-site | RIGIntelligence | "The Fixer" personal site (CF Pages) |
| rig-empire | RIGIntelligence | Intelligence Lab / agent marketplace |
| rig-os-agency | RIGIntelligence | Next.js agency dashboard (has /agency/offerings with "Three Doors") |
| awwward-site-enabler | RIGIntelligence | Design studio toolkit (private) |
| RIGIntelligence | RIGIntelligence | Profile front door (README only) |

## Local Directories

| Path | What |
|---|---|
| `~/Developer/rig-design-studio/site-v2/` | **CURRENT** site source for rodgersintelligence.com (noir, three doors, 8 verticals) |
| `~/Developer/rig-design-studio/vulk-fullsite/` | Earlier Vue/React experimental version (now historical) |
| `~/Developer/rig-os-site/` | Earlier corporate site source (superseded) |
| `~/Developer/rig-os-agency/` | Agency dashboard (Next.js) — separate from site |
| `~/Developer/rig-gtm-studio-v2/offerings/` | Static HTML offerings (Hire RIG / Hire Mike / Meet Mike doors) |
| `~/Developer/open-design-v15/design-systems/rig-mike-rodgers/` | Design tokens only |
| `~/Developer/RIG-Vault/sites/rodgersintelligence/` | Empty placeholder (just `src/blog/posts/`) |
| `~/Desktop/RIG-Estate-Map/vercel_backup/` | JSON backups of Vercel project configs |

## Key Lessons

### Domain moves swap everything (verified multiple times in July 2026)
On July 3, a session moved rodgersintelligence.com from rig-website to rig-os-site. This replaced the ENTIRE site content — not just the routes being fixed. Always check what a domain move will break before executing it.

### Site-v2 took over from rig-os-site around late June 2026
The handoff doc in `~/Developer/rig-design-studio/HANDOFF.md` (dated 2026-06-15) says rodgersintelligence.com was "rolled back to the OLD Next.js page" at that point. The noir site-v2 was promoted to production AFTER that handoff — the exact transition date isn't logged, but the 2026-07-06 investigation confirmed site-v2 is the current production target.

### `.prior*.html` files are drafts, not backups
Files like `meet.prior.html`, `meet.prior2.html`...`meet.prior6.html` in `site-v2/` look like backups but are actually intermediate authoring drafts (marked `<meta name="robots" content="noindex">`). The canonical "right" version of a file is its committed state in git, not the timestamped `.prior` file.

### Multiple candidate "rodgersintelligence" directories
Searching for `rodgersintelligence` returns: `rig-design-studio/site-v2/` (current), `rig-os-site/` (superseded), `RIG-Vault/sites/rodgersintelligence/` (empty), `RIGIntelligence/` (README only), `strategy-studio-pro/out/sessions/rodgers_intelligence_group/`. Always use `vercel inspect <domain>` to get the authoritative answer for "what serves this domain right now."