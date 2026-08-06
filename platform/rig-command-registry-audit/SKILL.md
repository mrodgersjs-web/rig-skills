---
name: rig-command-registry-audit
description: "Rank/port commands across 5 RIG harnesses."
tags: [rig, command-registry, cross-harness, audit, rank, port]
---

# rig-command-registry-audit

Class-level skill for ranking, porting, and verifying the RIG command registry across all 5 harnesses. The `command-registry` umbrella skill is user-owned and covers designing new commands; this skill covers the complementary audit/optimize/port workflow on existing commands.

## When to use

- Optimizing the cross-harness command registry
- Producing a top-N ranked reference for a multi-agent fleet
- Promoting Hermes-only commands to OMP/OpenCode
- Verifying commands actually execute (not just file-exist) across harnesses
- Closing coverage gaps (e.g., OMP has 12 prompts vs Hermes's 600+)

## The 5-stage workflow

### Stage 1 — Discovery

Scan all 5 harness command locations. Skip backups, READMEs, and tooling artifacts:

```python
HARNESS_DIRS = {
    'hermes':   '~/.hermes/commands/',
    'claude':   '~/.claude/commands/',
    'codex':    '~/.codex/commands/',
    'pi':       '~/.pi/prompts/',         # pi/OMP uses 'prompts' not 'commands'
    'opencode': '~/.opencode/rules/',     # opencode uses rules, not commands
}

def discover():
    union = set()
    for h, d in HARNESS_DIRS.items():
        for f in Path(d).glob('*.md'):
            if any(x in f.name for x in ['.bak', '.l8bak', 'README', 'CU2']):
                continue
            union.add(f.stem)
    return union
```

### Stage 2 — Score (R formula)

```python
def score(cmd, files_with_cmd, content):
    """
    R = 0.30·frequency + 0.25·doctrine + 0.15·skill + 0.10·invocation
      + 0.10·wglq + 0.05·examples + 0.05·use_when + 0.10·diffusion
    """
    frequency = len(files_with_cmd) / 5.0
    doctrine_hit = sum(1 for k in ['goal-loop','iqrsqpi','proof packet','gate','lattice','phronema','deviation engine']
                       if k in content.lower())
    doctrine = 1.0 if doctrine_hit >= 2 else (0.5 if 'USE WHEN' in content else 0.0)
    skill = 1.0 if re.search(r'\*\*Skill:?\*\*?\s*`[^`]+`', content) else 0.0
    invocation = 0.6 if re.search(r'--\w+|```bash', content) else 0.0
    wglq = 0.4 if re.search(r'WGLL|What Good Looks Like', content, re.IGNORECASE) else 0.0
    examples = 0.3 if re.search(r'##\s+Examples', content, re.IGNORECASE) else 0.0
    use_when = 0.3 if 'USE WHEN' in content else 0.0
    diffusion = min(0.5, len(files_with_cmd) * 0.10)
    return (0.30*frequency + 0.25*doctrine + 0.15*skill + 0.10*invocation
            + 0.10*wglq + 0.05*examples + 0.05*use_when + 0.10*diffusion)
```

**Bounds:** R ∈ [0, 1.0]. Default rank threshold: include all (sort by R desc). Top-100 reference typically lands at R ≥ 0.58.

### Stage 3 — Rank

```python
ranked = sorted(scores.items(), key=lambda x: -x[1]['R'])
top = ranked[:N]  # N=100 default
```

### Stage 4 — Port (cross-harness file propagation)

For each command in the top-N, ensure it exists in each harness. Front-matter conventions differ between harnesses:

| Harness | Source format | Port target | Front-matter conversion |
|--|--|--|--|
| **Hermes** | `description: ...` only | `~/.hermes/commands/<name>.md` | canonical prose |
| **Claude** | mirror | `~/.claude/commands/<name>.md` | symlink or copy |
| **Codex** | mirror | `~/.codex/commands/<name>.md` | symlink or copy |
| **OMP/PI** | port | `~/.pi/prompts/<name>.md` | prepend `name: <name>` if missing |
| **OpenCode** | aggregate | `~/.opencode/rules/<name>.md` | single rule per file |

**Front-matter rule for OMP/PI ports:** Hermes uses `description: ...` only. OMP/PI requires `name: <name>` + `description: ...` (the CLI parses `name` as the prompt identifier). When porting Hermes → OMP, prepend `name: <name>\n` if the `name:` field is absent.

```python
def adapt_to_omp(content, name):
    fm_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if fm_match:
        fm, body = fm_match.group(1), content[fm_match.end():]
        if not re.search(r'^name:\s', fm, re.MULTILINE):
            fm = f"name: {name}\n{fm}"
        return f"---\n{fm}\n---\n{body}"
    return f"---\nname: {name}\ndescription: /{name} from universal top-100.\n---\n\n{content}"
```

### Stage 5 — Verify (real execution, not file existence)

**Anti-pattern:** Files-exist check ONLY. That proves the file is there, not that the command works.

Always run at least one real exec per harness:

```bash
# OMP — verify (real parsing of the prompt)
echo "/<command> --list" | omp -p

# Claude — verify (loads from ~/.claude/commands/)
claude --print -p "/<command> --list"

# Hermes — verify (requires Gate-D proof-work, by design)
hermes --print -p "/<command> --list" --rig-task "<task description>"

# Codex — verify
codex exec "/<command> --list"
```

A command that *exists* in 5 harnesses but *executes* in 0 is not universal — it's a positioning failure.

### Coverage matrix

```python
coverage[c] = {harness for harness in HARNESS_DIRS if <name>.md in harness}
```

If `coverage[c]` excludes a harness, that's a port target. If `coverage[c]` is 5-of-5, the command is canonical.

## Pitfalls

- **Front-matter drift** — `description:` field differs between harnesses; Hermes concatenates USE WHEN + NOT for inline, OMP wants `name:` + `description:` split. Always convert when porting.
- **OpenCode uses rules, not commands** — there's no `.opencode/commands/` directory. The aggregate is a single `top-100-commands.md` rule that points to canonical files.
- **Hermes/Codex Gate-D** — running these without `--rig-task "<task>"` triggers the rig-knowledge-context block. That's designed behavior, not a port failure. Use a real task description when verifying.
- **Pre-existing harness errors** — Codex may have a separate `config.toml` parse error (e.g. duplicate key). That's not a port issue; document it and move on.
- **The 600-command universal set is already the substrate** — Hermes/Claude/Codex already share ~600 identical files. The work is rank + port + write-gate, not dedupe.

## Default output

```
Top-100 ranked commands written to:
  ~/.opencode/rules/top-100-commands.md
  ~/Documents/JakeStudio/Memory/Top-100-Commands-<date>.md

Score formula: R = ...
Coverage: 100/100 in 4 harnesses, 1 rule reference in OpenCode
Real verifications: 5 (file-system, OMP exec, Claude exec, front-matter, cross-harness)
```

## Related skills

- `command-registry` — user-owned, designing new commands. NOT editable; use `hermes curator adopt command-registry` to opt in.
- `rig-goal-design` — designing new goal loops, harnesses, chains
- `rig-status-verification` — verify claims against disk state before reporting
- `rig-iqrsqpi` — the 7-stage production workflow this audit follows

## Worked example

See `references/audit-cross-harness-2026-08-05.md` for the full 2026-08-05 run:
- 638 commands scored across 5 harnesses
- 95 commands ported to OMP `.pi/prompts/`
- 1 OpenCode rule `top-100-commands.md` (13.4KB)
- OMP `goal-loop --list` verified: 87 loops, 21 families, 3 machines
- Claude `goal-loop --list` verified: same 87 loops cross-checked
