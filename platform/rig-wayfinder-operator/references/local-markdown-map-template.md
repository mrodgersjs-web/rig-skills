# Local-Markdown Wayfinder Map Template

Copy this template, replace `<angle-bracket>` placeholders, save as `WAYFINDER_MAP.md` co-located with your artifact.

## When to use this template

Use the **local-markdown tracker** (this template) when:

- Mike says "chart a map" / "let's plan this out" with no other context
- No GitHub issue tracker has been provided for the repo
- The map needs to survive across multiple Hermes profiles
- You want git-diffable audit trail
- The artifact directory doesn't have a working GitHub remote

Use a GitHub issue tracker when:

- The repo is on GitHub with active issue management
- Mike explicitly says "open issues" or references existing issue numbers
- Other collaborators need to subscribe to ticket updates

---

## The Template

```markdown
# Wayfinder Map — <short-name>

## Destination

<one or two lines: what reaching the end of this map looks like. Every session orients to this before claiming a ticket.>

## Notes

<domain context; skills every session should consult; standing preferences for this effort; RIG context like JakeStudio paths, GBrain connection, or model defaults>

## Decisions so far

<!-- the index — one line per closed ticket: enough to judge relevance, then zoom the link for detail -->

- [<closed ticket name>](<artifact-link>) — <one-line gist of the answer>

## Not yet specified

<!-- fog of war: in-scope decisions you can tell are coming but can't yet ticket. Graduates as the frontier advances. -->

- <dim view of question 1>
- <dim view of question 2>

## Out of scope

<!-- work ruled beyond the destination. Closed, never graduates. -->

- <thing explicitly excluded> — <reason>

## Open tickets

- **<Ticket N name>** — <the question>. (type: research | prototype | grilling | task; HITL | AFK)
- **<Ticket M name>** — <the question>. (type: ...; ...)
```

---

## Worked Example (from 2026-07-30 Council Core Map)

```markdown
# Wayfinder Map — Buzz as RIG Strategy & Innovation OS

## Destination

A working set of Buzz persona packs + workflow chains that turn it into the governing
nervous system for RIG Strategy, GTM, Product Dev, and Content departments — running
debate council, 24/7 competitive intel scraping, daily learnings digest, PRD generation,
LinkedIn content pipeline, wayfinder plan design, and Hermes/Claude/Codex usage
monitoring. Done = multiple persona packs deployed and one end-to-end workflow chain
running unattended with output into the Desktop inbox.

## Notes

- Skills to consult: wayfinder (active), council (for debate), BeCreative (ideation),
  loom (recurring work), primo-search (Node intel).
- Hard constraint: 65GB free disk; 97% full — any new data storage must be scoped.
- Standing preference: dashboard in Buzz Desktop client, never surface straight to chat
  unless user-approved.

## Decisions so far

- [Council Core debate pack deployed](council_live_output.txt) — 5 personas
  (Marcus/Iris/Otto/Vera/Casper) with distinct lenses, temps, and report formats.
  Verified live: 23KB of substantive dissent on a sample dental PRD, max Jaccard
  similarity 0.16 (healthy).

## Not yet specified

- Exact intel source priority list (LinkedIn API, X, arXiv, GitHub Trending, HN, ...)
- Debate council composition for which domains (PRD review, wayfinder plan review, ...)
- Hermes/Claude/Codex monitoring: log file locations, frequency, alert thresholds
- Ollama model selection for each persona
- Approval workflow before external publishing
- Storage tier policy (Postgres for live, NAS for archive, /tmp throwaway)

## Out of scope

- Replacing Hermes / Claude Code / Codex (we route through them, not replace them)
- Custom LLM architecture from scratch (we fine-tune on RIG data, not train new models)
- Mobile / voice surfaces for Buzz (Tauri desktop only)

## Open tickets

- **Ticket 1** — Map setup: Create live wayfinder:map index, link Jake's Vault as single
  source of truth, set up daily-learnings inbox layout. (type: task, AFK)
- **Ticket 3** — Intel pipeline: 24/7 web scraping for competitive moat. 8-12 sources,
  scrape cadence, dedup/storing, signal classification. (type: research, AFK)
```

---

## Pitfalls

### Don't duplicate the open tickets list in Decisions

`Decisions so far` is the *index of completed work*. `Open tickets` is the *current state of the frontier*. They serve different purposes:

- Decisions = audit trail of what was decided and why
- Open tickets = what's takeable right now

### Don't put artifacts in the map body

The map is an **index**, not a store. Link to artifacts (`[name](path)`), don't paste their contents in. The Council Core map links to `council_live_output.txt` rather than pasting 23KB of council reports.

### Don't pre-slice the fog

`Not yet specified` is coarser than tickets. Don't try to break it into ticket-sized pieces prematurely. The fog graduates as the frontier reaches it.

### Don't forget the Out of scope section

If you catch yourself thinking "we could also do X" and X isn't actually in the destination, it belongs in `Out of scope`, not `Not yet specified`. The destination fixes the scope.

---

## Git workflow

After every ticket closes, run from the artifact directory:

```bash
git add WAYFINDER_MAP.md
git commit -m "wayfinder: close <ticket name>"
```

This gives you `git log --oneline WAYFINDER_MAP.md` as the audit trail.
