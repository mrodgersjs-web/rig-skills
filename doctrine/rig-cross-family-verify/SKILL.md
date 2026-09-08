---
name: rig-cross-family-verify
description: "Iterative cross-family adversarial review loop."
tags: [rig, review, adversarial, cross-family, verification, proofpacket, honest-completion]
---

# Cross-Family Adversarial Verification Loop

<objective>
Run a fresh cross-family review on shipped code. If FAIL, fix the findings,
then run a second cross-family reviewer from a DIFFERENT AI family to
confirm each fix is genuine and to surface any new defects introduced
by the fixes. Seal honest verdicts (PASS or FAIL) in ProofPackets.

This is the verification half of the rigor loop. The other half — `rig-triple-review`
or `rig-stress-test` — produces findings; this skill verifies them.
</objective>

<when_to_use>
- After shipping a non-trivial build (multi-module, security-sensitive,
  GEV-separation-critical, durable, GEV-coupling)
- Before any Gate-D promotion (live deployment, client rollout, provider
  writes)
- When the implementer-aligned tests all pass but you suspect the tests
  validate implementation rather than spec
- When the user says "address the findings, run second cross family, keep going"
- When a prior build was self-attested PASS by implementer-aligned tests
  but a fresh eyes-on review from a different family surfaced defects
- After any phase increment in a multi-phase build (S0, S2, S4, ...)
</when_to_use>

<when_not_to_use>
- Trivial edits (one-line change, doc fix, type annotation)
- Pure scaffolding with no logic
- Visual/UI changes that need human review, not adversarial review
</when_not_to_use>

<prerequisites>
- A built, test-passing artifact (canonical tests green)
- An honest-completion framework in place (ProofPacket shape)
- Access to at least 2 distinct AI model families (Opus, Sonnet, minimax,
  Llama, etc.) — different providers if possible
- A hermes `pi` binary at `$HOME/.hermes/bin/pi` (not the
  Node-based one at `.hermes/node/bin/pi`)
</prerequisites>

<process>

## Step 1: Establish the iteration baseline
- Run canonical test suite (e.g., `python3 -m unittest discover`). Capture
  the pass count.
- Hash all artifact files (`sha256`) for inclusion in the ProofPacket.
- Record baseline state in a ProofPacket skeleton with
  `decision: "PASS (baseline)"` and a clear `baseline` section.

## Step 2: Run the FIRST cross-family review
- Select a reviewer from AI family A (e.g., Anthropic Opus 5).
- Invoke via `pi --provider anthropic --model claude-opus-5 --print`.
- Use `--mode json` for parseable output if the model returns verbose thinking.
- Prompt structure: tell the reviewer the artifact paths, the spec
  invariants, and ask for a verdict (PASS | HOLD | FAIL) plus per-finding
  evidence.
- Capture the full report. DO NOT summarise or interpret; store verbatim.

## Step 3: Honest verdict seal
- If PASS: seal as the final ProofPacket, done.
- If FAIL: seal the FAIL verdict faithfully with all findings. Do NOT
  auto-patch around the verdict. Record:
  - Per-finding severity (blocking | non-blocking)
  - Cross-cutting concerns (GEV separation, Gate-D boundary)
  - Required actions before GO

## Step 4: Address blocking findings
- Group findings by area (auth, retrieval, durability, etc.).
- For each blocking item: locate the specific defect in code, design a
  minimal correct fix, apply, and write a negative test that fails on
  the old behavior and passes on the new.
- The fix must be SPEC-anchored, not just "make the test pass."

## Step 5: Run the SECOND cross-family review
- Select a reviewer from AI family B (DIFFERENT from family A).
- For Opus → minimax, for Sonnet → Llama, etc.
- Cross-family is the whole point — same family reviews tend to share
  blind spots.
- Pass the SAME spec invariants, but ask: "Verify each finding from
  reviewer A is genuinely resolved. Find NEW defects introduced by the
  fixes."
- If the model is verbose (minimax returns thinking blocks), use `--mode json`
  and extract `text` from `message_end` events.

## Step 6: Re-verify both layers
- **Canonical tests** — run the full unittest suite. Capture the count.
  Update tests that asserted defects as correct (the old tests validated
  the bug, not the spec — replace them with negative tests).
- **Focused ad-hoc script** — write a fresh ad-hoc verification script
  targeting the modules changed in Phase 1. Use `tempfile.NamedTemporaryFile`
  with `hermes-verify-` prefix in macOS-safe tempdir
  (`/private/var/folders/.../T/`); clean up after run.
- Both layers MUST show green. If either fails, return to Step 4.

## Step 7: Seal Phase ProofPacket
- New ProofPacket with:
  - Verdict: PASS (Phase N)
  - All blocking items listed with "FIXED — <evidence>"
  - All non-blocking items listed with "FIXED" or "DEFERRED to Phase N+1"
  - Reviewer chain recorded (reviewer A verdict, reviewer B verdict)
  - Test counts: canonical X/Y, ad-hoc Z/W
  - All file hashes
  - Residual risks (explicit, not buried)
  - Gate-D boundary confirmation

## Step 8: Stop and report honestly
- Don't promise next steps that depend on Gate-D authorization
- Don't claim "all green" if any residual risk is non-trivial
- If a blocking item is deferred (e.g., "Phase 2 work"), say so explicitly
- The user wants a real verdict, not optimism
</process>

<success_criteria>
- ≥2 cross-family reviews complete (different AI families)
- All blocking items explicitly addressed with negative tests
- Canonical test count maintained or increased (no test deletion that
  removes a negative test)
- Ad-hoc script covers the changed paths
- Phase ProofPacket sealed with honest verdict
- Gate-D boundary verified unchanged
</success_criteria>

<pitfalls>

1. **Same-family reviewers** — Opus reviewing Opus doesn't help; cross-family
   means different provider + different family.
2. **Skipping the FAIL verdict** — auto-patching around a FAIL to claim PASS
   is the honest-completion-doctrine violation. Seal FAIL; fix; re-verify.
3. **Trusting implementer-aligned tests alone** — tests that pass without
   a spec review often validate the bug. A negative test that fails on
   the bug is what proves the fix.
4. **Skipping new defects** — Phase 1 fixes can introduce new defects.
   The second cross-family review catches those.
5. **Long prompts that time out** — if reviewer model is verbose
   (minimax M3, Opus), use `--mode json` and extract text from
   `message_end` events. Avoid one-mega-character prompts.
6. **Leaving stale `specs/` files** — after Phase 1 the OpenSpec
   `spec.md` should reflect the new corrected behavior, not the
   implementation-aligned old behavior.
7. **Sealing PASS without running canonical + ad-hoc** — both layers must
   be green. A passing test suite with no fresh ad-hoc is implementer-aligned.
8. **Treating `--print` as a pipe** — `pi --print` is a stdout consumer.
   If invoking from a subprocess, capture stdout and parse the LAST
   assistant message, not the first.
</pitfalls>

<references>
- `rig-triple-review` — 3 parallel reviewers in one shot (different lens;
  not iterative)
- `rig-stress-test` — 5-phase sequential panel (deeper than triple-review
  but single-pass; this skill is the verify-loop companion)
- `rig-triple-review` and `rig-stress-test` produce findings; this
  skill verifies them with cross-family eyes.
- honest-completion-doctrine — the "never auto-patch around FAIL" rule
- `adw_prompt.py` / `adw_quality.py` / `adw_build_test.py` (SSSF) — when
  SSSF factory tooling works, these are an option; in practice they
  hit bugs (missing modules, missing scripts) and direct invocation is
  more reliable.
</references>