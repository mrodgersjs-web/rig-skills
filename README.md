# RIG Skills — 33 Specialized Agent Skills for Governed AI Systems

RIG (Rodgers Intelligence Group) is an operating system for running fleets of AI agents — coding agents, GTM agents, content agents, and department-level autonomous operators — under a shared governance model. **RIG Skills** is the public collection of [Claude Code / Anthropic Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) that encode how those agents actually operate: how they orchestrate cron fleets across heterogeneous nodes, how they hand off work between phases without losing state, how they verify their own output before calling it done, and how they delegate real authority (spend limits, approval gates) from a human principal to a named agent.

Every skill in this repo is a `SKILL.md` file (plus, where relevant, `references/`, `scripts/`, and `templates/` subdirectories) written to the [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) spec: YAML frontmatter (`name`, `description`, trigger conditions) followed by markdown instructions the agent reads on demand. They are harness-agnostic — the same file format works unmodified across Claude Code, Codex, and Hermes.

These skills were extracted directly from a production multi-agent system that runs GTM, content, and engineering operations continuously. They are opinionated, battle-tested, and occasionally reference internal tools (GBrain, Obsidian vaults, Supabase schemas, Postiz, Composio) that you will need to swap for your own equivalents — but the *patterns* (cron-trio verification, proof-packet sealing, gate-based delegation, adversarial review panels) generalize to any agent fleet.

**Total: 33 skills across 8 categories.**

## Table of Contents

- [Deviation Engines](#deviation-engines) (1)
- [Operating Doctrine](#operating-doctrine) (6)
- [Content & Media Studios](#content--media-studios) (4)
- [Agent Engineering](#agent-engineering) (3)
- [Go-To-Market](#go-to-market) (3)
- [Fleet Operations](#fleet-operations) (4)
- [Knowledge Systems](#knowledge-systems) (4)
- [Platform Tools](#platform-tools) (8)
- [Usage](#usage)
- [License](#license)

## Deviation Engines

*`engines/`* — Skills that apply the RIG Deviation Engine framework — pushing generated output away from the generic LLM median toward distinctive, high-signal artifacts.

| Skill | Description |
|---|---|
| [`rig-deviate-design`](engines/rig-deviate-design/SKILL.md) | Apply RIG Deviation Engines as a design system methodology — map the 40 abstract physics/nature/cognitive engines to concrete UI design… |

## Operating Doctrine

*`doctrine/`* — Skills that encode RIG's governance model: verification loops, adversarial review, phased handoffs, and delegated authority (Gate-D).

| Skill | Description |
|---|---|
| [`rig-agent-gate-d-delegation`](doctrine/rig-agent-gate-d-delegation/SKILL.md) | Delegate Gate-D authority from Mike to a named RIG agent (Darius, Eleanor, Nadia, etc.) so the agent can take specific… |
| [`rig-cross-family-verify`](doctrine/rig-cross-family-verify/SKILL.md) | Iterative cross-family adversarial review loop. |
| [`rig-doctrine-infrastructure-wiring`](doctrine/rig-doctrine-infrastructure-wiring/SKILL.md) | Wire new doctrine, subsystem specs, or major capabilities into the RIG agent infrastructure. |
| [`rig-multiphase-handoff-execution`](doctrine/rig-multiphase-handoff-execution/SKILL.md) | Execute phased handoffs in rig-intelligence. |
| [`rig-stress-test`](doctrine/rig-stress-test/SKILL.md) | 5-phase sequential adversarial review panel. |
| [`rig-triple-review`](doctrine/rig-triple-review/SKILL.md) | Run 3 independent adversarial reviewers in parallel, each with a different critical lens. |

## Content & Media Studios

*`studios/`* — Skills that run RIG's creative and content production lines — AI workforce orchestration, LinkedIn studio engines, teaser pages, and video-to-doctrine pipelines.

| Skill | Description |
|---|---|
| [`rig-higgsfield-workforce`](studios/rig-higgsfield-workforce/SKILL.md) | RIG x Higgsfield AI Employee Workforce. |
| [`rig-linkedin-studio-engine-builder`](studios/rig-linkedin-studio-engine-builder/SKILL.md) | Build LinkedIn Studio A1A3A4 engines. |
| [`rig-strategy-teaser`](studios/rig-strategy-teaser/SKILL.md) | RIG see-themselves strategy-teaser production line (v2). |
| [`rig-video-doctrine-pipeline`](studios/rig-video-doctrine-pipeline/SKILL.md) | Extract transcripts from agentic coding videos (YouTube), analyze for patterns/techniques/workflows, and generate RIG doctrine artifacts:… |

## Agent Engineering

*`engineering/`* — Skills for building and upgrading the agents themselves — swarm-based app builds and persona-to-PAI (Personal AI) upgrades.

| Skill | Description |
|---|---|
| [`rig-agent-swarm-app-build`](engineering/rig-agent-swarm-app-build/SKILL.md) | Orchestrate parallel agent swarms to build complete applications — research, design system, screens, features, tests, distribution. |
| [`rig-department-agent-upgrade`](engineering/rig-department-agent-upgrade/SKILL.md) | Upgrade named RIG department agents from persona/role into full PAI operating systems — substrate, goals, loops, skills, harnesses,… |
| [`rig-pai-upgrade`](engineering/rig-pai-upgrade/SKILL.md) | Upgrade a named RIG department agent from persona to full PAI operating system. |

## Go-To-Market

*`gtm/`* — Skills that run go-to-market operations: 24/7 outbound engines, full GTM departments, and LinkedIn content-as-growth-channel operations.

| Skill | Description |
|---|---|
| [`rig-gtm-24-7-operations`](gtm/rig-gtm-24-7-operations/SKILL.md) | Operate a 24/7 GTM engine with hourly cron scheduling, Telegram reporting, and multi-channel outreach automation. |
| [`rig-gtm-operations`](gtm/rig-gtm-operations/SKILL.md) | Run a full GTM department — prospect sourcing, email outreach, pipeline management, conference prep, conversion optimization, AND the… |
| [`rig-linkedin-ops`](gtm/rig-linkedin-ops/SKILL.md) | Set up and operate a LinkedIn content department as an AI agent team. |

## Fleet Operations

*`fleet/`* — Skills for orchestrating distributed cron jobs and scraping across a fleet of local AI nodes and RIG departments.

| Skill | Description |
|---|---|
| [`rig-cron-fleet-orchestrator`](fleet/rig-cron-fleet-orchestrator/SKILL.md) | Operator-grade cron fleet orchestration across heterogeneous local AI nodes. |
| [`rig-dept-daily-cycle-operator`](fleet/rig-dept-daily-cycle-operator/SKILL.md) | Operate any RIG department's `daily-goal` cron when it fires — the 8-step base spec (scrape → entities → patterns → GBrain + Supabase +… |
| [`rig-dept-daily-goal-builder`](fleet/rig-dept-daily-goal-builder/SKILL.md) | Per-department RIG daily-goal cron that writes a fixed batch of fresh substrate (entities + topics) against the dept's existing scraped… |
| [`rig-intel-scrape-operations`](fleet/rig-intel-scrape-operations/SKILL.md) | Operational patterns for rig-intel-scrape cron jobs. |

## Knowledge Systems

*`knowledge/`* — Skills for ingesting, distilling, and routing raw source material (video, web, papers) into structured department knowledge bases.

| Skill | Description |
|---|---|
| [`rig-corpus-distillation-pipeline`](knowledge/rig-corpus-distillation-pipeline/SKILL.md) | Distill a primary source corpus into RIG assets. |
| [`rig-dept-substrate-intake`](knowledge/rig-dept-substrate-intake/SKILL.md) | Canonical RIG department-substrate intake workflow. |
| [`rig-knowledge-engine`](knowledge/rig-knowledge-engine/SKILL.md) | Per-department knowledge ingestion pipeline for RIG agents. |
| [`rig-knowledge-ingestion`](knowledge/rig-knowledge-ingestion/SKILL.md) | Scrape, process, and ingest knowledge (YouTube transcripts, arXiv papers, web content) into agent vaults. |

## Platform Tools

*`platform/`* — General-purpose operational tooling: session memory, schema provisioning, Docker stacks, site forensics, and cross-harness command auditing.

| Skill | Description |
|---|---|
| [`rig-close-session`](platform/rig-close-session/SKILL.md) | Auto-session memory: encodes session knowledge into repo-committed files so the next session starts informed. |
| [`rig-command-registry-audit`](platform/rig-command-registry-audit/SKILL.md) | Rank/port commands across 5 RIG harnesses. |
| [`rig-docker-stack`](platform/rig-docker-stack/SKILL.md) | Start and manage the RIG agentic tools Docker stack (n8n, LangFuse, Dify) via Colima on macOS. |
| [`rig-github-issue-writer`](platform/rig-github-issue-writer/SKILL.md) | Create structured GitHub issues from bug reports, feature suggestions, and user feedback. |
| [`rig-memory-os`](platform/rig-memory-os/SKILL.md) | Use the local RIG Memory OS for scoped event capture, context retrieval, future intentions, and speculative predictions. |
| [`rig-site-forensics`](platform/rig-site-forensics/SKILL.md) | Trace where a RIG website is deployed, find old versions, and recover lost site content across Vercel, Cloudflare Pages, GitHub, and local… |
| [`rig-supabase-schema-provisioning`](platform/rig-supabase-schema-provisioning/SKILL.md) | Provision Supabase Postgres schemas from RIG cron/JAKE-SETUP tasks when no `supabase-helper` CLI or `psql` binary exists on the host. |
| [`rig-wayfinder-operator`](platform/rig-wayfinder-operator/SKILL.md) | Run wayfinder maps in RIG. |

## Usage

These are [Agent Skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills) — self-contained instruction sets an AI coding agent loads on demand when a task matches the skill's trigger description. Installation is just placing the skill directory where your harness looks for skills.

### Claude Code

Copy the skill directory (the `SKILL.md` plus any `references/`, `scripts/`, or `templates/` subdirectories) into your project or user skills folder:

```bash
# Project-scoped (this repo/project only)
cp -R engines/rig-deviate-design .claude/skills/rig-deviate-design

# User-scoped (available across all projects)
cp -R doctrine/rig-triple-review ~/.claude/skills/rig-triple-review
```

Claude Code auto-discovers skills in `.claude/skills/` and `~/.claude/skills/` and loads the relevant one when your prompt matches its `description` trigger.

### Codex

Codex reads skills from `~/.codex/skills/` (or a project-local `.codex/skills/`) using the same `SKILL.md` format:

```bash
cp -R fleet/rig-cron-fleet-orchestrator ~/.codex/skills/rig-cron-fleet-orchestrator
```

### Hermes

Hermes resolves skills from `~/.hermes/skills/` — this is the original source layout these skills shipped from:

```bash
cp -R gtm/rig-gtm-operations ~/.hermes/skills/rig-gtm-operations
```

### Bulk install

To install every skill in a category at once:

```bash
git clone https://github.com/mrodgersjs-web/rig-skills.git
cp -R rig-skills/doctrine/* ~/.claude/skills/
```

Each skill's `description` frontmatter field doubles as its trigger condition — the agent reads all installed skill descriptions up front and only loads the full `SKILL.md` body for the one(s) matching the current task, so installing skills you don't need costs negligible context.

> **Note:** several skills reference internal RIG infrastructure by name (GBrain, Obsidian vault paths, Supabase project conventions, `~/.rig/departments/`, Postiz, Composio). Treat these as worked examples of the *pattern* — cron-trio verification, proof-packet sealing, entity-schema conventions, gate-based delegation — and adapt the concrete tool names to your own stack.

## License

MIT — see [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## Note on GTM skills

The `gtm/` category (rig-gtm-operations, rig-gtm-24-7-operations, rig-linkedin-ops) contains operational credentials (Telegram bot tokens, Google Ads API keys, Stripe keys, Apollo API keys) and is excluded from this public release. These skills are available on request with credentials scrubbed.

## Stats

- **120 files** across 8 categories (engines, doctrine, studios, engineering, fleet, knowledge, platform)
- **GTM category excluded** — contains live operational credentials
- PII-redacted: emails, phones, internal paths, network addresses scrubbed
