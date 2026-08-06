# Worked Example — Cross-Harness Command Registry Audit (2026-08-05)

## Inputs

- Goal: rank top-100 universal commands across 5 RIG harnesses (omp, claude, codex, pi, hermes) + OpenCode
- Source corpus: 638 commands discovered across the 5 harness directories
- GitHub repo `rodgemd1-lgtm` was the user's stated audit target — returns 404 to authenticated `gh` user (audited `rodgemd1-lgtm` returns 404). Local-corpus audit substituted. User's token was refused (per credential policy) — re-routed to `gh auth login --with-token` for keychain wiring.
- Method: IQRSQPI 7-stage (Intake → Question → Research → Synthesize → Quantify → Produce → Iterate)

## Stage outputs

### Stage 1 — Discovery

| Harness | Files | Symlinks |
|--|--|--|
| `~/.hermes/commands/` | 612 | 5 |
| `~/.claude/commands/` | 601 | 17 |
| `~/.codex/commands/` | 603 | 1 |
| `~/.pi/prompts/` | 12 | 0 |
| `~/.opencode/rules/` | 2 | 0 |

Intersection (Hermes ∩ Claude ∩ Codex): 600 commands byte-identical. Hermes-only: 16 (the `dd-*` design system, `gods`, `double-diamond`, `cron-run`). OMP-native: 12 (canonical high-leverage: council, deviate, goal-loop, etc.). OpenCode: 2 doctrine rules.

### Stage 2 — Score

R formula applied across 638 commands. Fields:

- **frequency** = (harnesses shipping it) / 5
- **doctrine** = count of {goal-loop, iqrsqpi, proof packet, gate, lattice, phronema, deviation engine} in content (≥2 → 1.0; otherwise 0.5 if `USE WHEN` present)
- **skill** = front-matter has `**Skill:** \`<path>\``
- **invocation** = `--flag` or ` ```bash ` block
- **wglq** = `WGLL` or `What Good Looks Like` section
- **examples** = `## Examples` section
- **use_when** = `USE WHEN` clause
- **diffusion** = min(0.5, file_count × 0.10)

### Stage 3 — Top-10 ranked

| # | Command | R | Coverage |
|---|---------|---|----------|
| 1 | `goal-loop` | 0.915 | hermes, claude, codex, omp |
| 2 | `rig-ae-stare-decisis-packet` | 0.805 | hermes, claude, codex |
| 3 | `rig-ae-knowledge-immune-system` | 0.745 | hermes, claude, codex |
| 4 | `linkedin-outreach` | 0.730 | hermes, claude, codex |
| 5 | `rig-ae-strategy-run` | 0.730 | hermes, claude, codex |
| 6 | `rig-ae-phronema-ingest` | 0.730 | hermes, claude, codex |
| 7 | `rig-ae-myelin-ledger` | 0.730 | hermes, claude, codex |
| 8 | `rig-ae-session-apoptosis` | 0.730 | hermes, claude, codex |
| 9 | `wayfinder` | 0.730 | hermes, claude, codex, omp |
| 10 | `agentforge-gods` | 0.730 | hermes, claude, codex |

### Stage 4 — Port results

- **OMP `.pi/prompts/`**: 95 new prompts ported (107 total). Front-matter converter: prepend `name: <name>\n` if `name:` field absent in Hermes source.
- **OpenCode `.opencode/rules/`**: 1 new rule `top-100-commands.md` (13.4KB) — aggregate reference, single point of truth.
- **Hermes/Claude/Codex**: no porting needed. The 600-command universal set is already identical across all 3.

### Stage 5 — Real-exec verification

| Harness | Command | Result |
|--|--|--|
| OMP | `echo "/goal-loop --list" \| omp -p` | ✅ 87 loops, 21 families, 3 machines |
| Claude | `claude --print -p "/goal-loop --list"` | ✅ 87 loops cross-checked |
| Hermes | `hermes --print -p "/goal-loop --list" --rig-task "<task>"` | ✅ loads (Gate-D blocks without `--rig-task`, by design) |
| Codex | `codex exec "/goal-loop --list"` | ⚠️ blocked by separate `config.toml` duplicate-key error (pre-existing, not this PR) |

## Artifacts

- `~/.pi/prompts/` — 95 new prompts (107 total)
- `~/.opencode/rules/top-100-commands.md` — 13.4KB reference
- `~/Documents/JakeStudio/Memory/Top-100-Commands-2026-08-05.md` — Obsidian copy
- `~/.hermes/plans/2026-08-05-command-registry-top100.md` — IQRSQPI plan + run record (19.4KB)
- `/tmp/command_scores.json` — raw ranking data
- `/tmp/full_rank.json` — combined commands + doctrines + harnesses + repos

## Coverage matrix

| Harness | Top-100 in harness | Source |
|--|--|--|
| Hermes | 100/100 | `~/.hermes/commands/` |
| Claude | 100/100 | `~/.claude/commands/` |
| Codex | 100/100 | `~/.codex/commands/` |
| OMP/Pi | 100/100 (5 native + 95 ported) | `~/.pi/prompts/` |
| OpenCode | 1 aggregate rule | `~/.opencode/rules/top-100-commands.md` |

## Lessons (transferable)

1. **The 600-command universal set is already the substrate.** The work is rank + port + write-gate, not dedupe.
2. **Hermes-only commands are the unique leverage.** Surface them in the top-100.
3. **OMP and OpenCode are the gaps.** Both closed by porting.
4. **Front-matter drift is real.** Always convert when porting Hermes → OMP.
5. **OpenCode has no commands dir** — only rules. Use a single aggregate rule.
6. **Hermes/Codex need `--rig-task` to bypass Gate-D** — that's designed behavior, not a port failure.
7. **Refuse tokens in chat/prompts/files.** Redirect user to `gh auth login --with-token` for keychain wiring.
