---
name: rig-deviate-design
description: Apply RIG Deviation Engines as a design system methodology — map the 40 abstract physics/nature/cognitive engines to concrete UI design tokens, rules, spacing systems, animation timing, and scoring rubrics. Use when pushing a design system to ±30σ quality using deviation engine principles.
category: rig
---

# rig-deviate-design

Apply RIG Deviation Engines to design systems — translate abstract deviation concepts into concrete design tokens, layout rules, and quality scoring.

## When to use

- Pushing a design system beyond competitor-quality to ±30σ
- Converting abstract design principles into mathematically justified tokens
- Building a scoring rubric for design quality based on deviation engines
- Creating Fibonacci/golden-ratio spacing systems from first principles

## How it works

1. **Map engines to design rules** — Each of the 40 engines gets a concrete design application (see `references/design_system_application.md`)
2. **Derive tokens** — Spacing (Fibonacci), proportions (golden ratio), animation (physical scaling), radii (Fibonacci)
3. **Create scoring rubric** — Weight each rule 0.5–3.0, score screens 0–100, tier: ≥80 internal, ≥85 public, ≥90 ±30σ
4. **Implement in code** — `ThemeExtension` with deviation-derived tokens, enum of engines, rule classes

## Architecture

```
lib/design/
├── deviation_design_system.dart   # Engine enum, DesignRule, scoring rubric
├── design_quality_score.dart      # Per-screen scoring, aggregate reports
lib/theme/
├── mathematical_design.dart       # Fibonacci/golden ratio constants
├── digital_atelier.dart           # ThemeExtension with deviation-derived tokens
```

## Key mappings

- **Engine 34 (Fine-Tuning)** → Fibonacci spacing {3,5,8,13,21,34,55,89}, golden ratio proportions
- **Engine 36 (Speed of Light)** → Animation durations scale with element size
- **Engine 33 (Casimir Pressure)** → Whitespace creates visual tension and focus
- **Engine 37 (Absolute Zero)** → Only animate meaningful state changes
- **Engine 22 (Bee Foraging)** → 60/25/15 visual attention split

## Pitfalls

1. **Dart const Set with doubles fails** — Use `<double>{1, 2, 3}` not `const {1.0, 2.0}`
2. **`clamp(0, 100)` returns `num`** — Use `clamp(0.0, 100.0)` and declare `double`
3. **radiusPill = 999, not Fibonacci 21** — Touch targets need full roundness
4. **sectionGap > screenMargin** — Casimir pressure requires gap (34px) > margin (21px) for hierarchy
5. **Don't duplicate MathematicalDesign** — Check if a sibling agent already created it before writing

## Related skills

- `rig-deviate` — Text variant generation using deviation engines (different application)
- `rig-engines` — Engine metadata exploration (codenames, slugs, layers)
- `rig-score` — Score artifacts against deviation engines
- `rig-deviate-engines` — CLI for engine definitions
