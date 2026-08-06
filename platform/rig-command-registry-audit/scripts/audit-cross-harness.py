#!/usr/bin/env python3
"""
audit-cross-harness.py — Cross-harness command registry audit.

Run from anywhere. Reads the 5 harness command directories, scores with the R
formula, ranks the top-N, and prints a coverage matrix.

Usage:
    ./audit-cross-harness.py            # default top-100
    ./audit-cross-harness.py --top 50   # top-50
    ./audit-cross-harness.py --matrix   # just coverage matrix
    ./audit-cross-harness.py --json out.json  # write JSON

Skill: rig-command-registry-audit
"""

import argparse
import json
import re
import sys
from pathlib import Path

HARNESS_DIRS = {
    'hermes':   Path.home() / '.hermes' / 'commands',
    'claude':   Path.home() / '.claude' / 'commands',
    'codex':    Path.home() / '.codex' / 'commands',
    'pi':       Path.home() / '.pi' / 'prompts',
    'opencode': Path.home() / '.opencode' / 'rules',
}

SKIP_TOKENS = ('.bak', '.l8bak', 'README', 'CU2')


def discover():
    """Return {name: {harness: content}}."""
    out = {}
    for h, d in HARNESS_DIRS.items():
        if not d.exists():
            continue
        for f in sorted(d.glob('*.md')):
            if any(x in f.name for x in SKIP_TOKENS):
                continue
            try:
                content = f.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            out.setdefault(f.stem, {})[h] = content
    return out


def score(content):
    """R formula: 7-feature composite."""
    frequency = 0.0  # caller fills from coverage
    doctrine_kw = ['goal-loop', 'iqrsqpi', 'proof packet', 'gate', 'lattice',
                   'phronema', 'deviation engine']
    doctrine_hit = sum(1 for k in doctrine_kw if k in content.lower())
    doctrine = 1.0 if doctrine_hit >= 2 else (0.5 if 'USE WHEN' in content else 0.0)
    skill = 1.0 if re.search(r'\*\*Skill:?\*\*?\s*`[^`]+`', content) else 0.0
    invocation = 0.6 if re.search(r'--\w+|```bash', content) else 0.0
    wglq = 0.4 if re.search(r'WGLL|What Good Looks Like', content, re.IGNORECASE) else 0.0
    examples = 0.3 if re.search(r'##\s+Examples', content, re.IGNORECASE) else 0.0
    use_when = 0.3 if 'USE WHEN' in content else 0.0
    return doctrine, skill, invocation, wglq, examples, use_when


def score_total(doctrine, skill, invocation, wglq, examples, use_when,
                files_with_cmd, total_harnesses):
    frequency = len(files_with_cmd) / total_harnesses
    diffusion = min(0.5, len(files_with_cmd) * 0.10)
    return round(
        0.30 * frequency
        + 0.25 * doctrine
        + 0.15 * skill
        + 0.10 * invocation
        + 0.10 * wglq
        + 0.05 * examples
        + 0.05 * use_when
        + 0.10 * diffusion,
        3,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--top', type=int, default=100)
    ap.add_argument('--matrix', action='store_true')
    ap.add_argument('--json', type=str)
    args = ap.parse_args()

    found = discover()
    total_harnesses = len(HARNESS_DIRS)

    scores = {}
    for name, by_harness in found.items():
        files = list(by_harness.keys())
        canonical = next(iter(by_harness.values()))
        d, s, i, w, e, u = score(canonical)
        R = score_total(d, s, i, w, e, u, files, total_harnesses)
        scores[name] = {
            'R': R,
            'doctrine': d,
            'skill': s,
            'invocation': i,
            'wglq': w,
            'examples': e,
            'use_when': u,
            'files': files,
        }

    ranked = sorted(scores.items(), key=lambda x: -x[1]['R'])
    top = ranked[:args.top]

    if args.matrix:
        print(f"\n{'='*60}\nCROSS-HARNESS COMMAND COVERAGE MATRIX\n{'='*60}")
        print(f"Total commands: {len(found)}")
        print(f"Top-{args.top} threshold: R >= {top[-1][1]['R'] if top else 'N/A'}")
        for h in HARNESS_DIRS:
            n = sum(1 for x in found.values() if h in x)
            print(f"  {h:10s}: {n} commands")
        coverage = {'all_5': 0, 'in_4': 0, 'in_3': 0, 'in_2': 0, 'in_1': 0}
        for name, v in scores.items():
            cnt = len(v['files'])
            coverage[f'in_{cnt}'] = coverage.get(f'in_{cnt}', 0) + 1
        print(f"\nTop-{args.top} coverage:")
        for k, v in coverage.items():
            print(f"  {k}: {v}")
        return

    print(f"\n{'='*60}\nTOP-{args.top} UNIVERSAL COMMANDS\n{'='*60}")
    for i, (k, v) in enumerate(top, 1):
        print(f"{i:3d}. R={v['R']:.3f}  {','.join(v['files']):40s}  {k}")

    if args.json:
        with open(args.json, 'w') as f:
            json.dump({'ranked': [(k, v) for k, v in top], 'total': len(found)}, f, indent=2)
        print(f"\n-> {args.json}")


if __name__ == '__main__':
    main()
