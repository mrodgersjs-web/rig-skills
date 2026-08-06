# Pitfalls — Applying Deviation Engines to Flutter Design Systems

## Dart Language Pitfalls

### 1. `const Set<double>` fails compilation
```dart
// ❌ ERROR: const set element can't override ==/hashCode for double
const fibonacci = {1.0, 2.0, 3.0, 5.0, 8.0};

// ✅ FIX: use final + int literals (coerce to double)
final fibonacci = <double>{1, 2, 3, 5, 8};
```

### 2. `num.clamp()` returns `num`, not `double`
```dart
// ❌ ERROR: argument type 'num' can't be assigned to 'double'
final normalized = (score / max * 100).clamp(0, 100);

// ✅ FIX: use double literals
final double normalized = (score / max * 100).clamp(0.0, 100.0);
```

### 3. `Duration` can't be const with `MathematicalDesign` references
```dart
// ❌ If MathematicalDesign values aren't const, can't use in const context
const durationFast = MathematicalDesign.animFast; // only works if animFast is const

// ✅ Ensure MathematicalDesign fields are `static const`
```

## Design System Pitfalls

### 4. radiusPill should be 999, not Fibonacci 21
Fibonacci 21 is too small for pill-shaped chips/tags on touch screens.
Use 999 for full roundness. The Fibonacci radius applies to cards, inputs, modals — not pills.

### 5. sectionGap must be strictly greater than screenMargin
Casimir Pressure (Engine 33) requires that the gap between sections creates
MORE visual force than the screen margin. If sectionGap ≤ screenMargin,
the hierarchy collapses. Use F(9)=34 for section gap, F(8)=21 for margin.

### 6. Don't duplicate MathematicalDesign across agents
When running parallel agent swarms, check if a sibling already created
`mathematical_design.dart` before writing your own. Re-read the file
before every patch — sibling modifications happen mid-turn.

### 7. Animation duration must be monotonically increasing
The Speed of Light engine (36) requires: fast < normal < slow < celebration.
If you swap any pair, the physical metaphor breaks. Verify ordering in tests.

## Scoring Pitfalls

### 8. Weights must sum consistently across screens
If Engine 34 (Fine-Tuning) has weight 3.0 on the home screen but 2.0 on
the workout screen, the normalized scores aren't comparable. Use consistent
weights across all screens, or normalize per-screen.

### 9. Score of 0.0 on an engine ≠ engine not applied
A screen might score 0.0 on an engine because it genuinely doesn't apply
(e.g., no empty states to score for Hawking Radiation). Distinguish between
"not applicable" (exclude from denominator) and "applied but failing" (score 0).

### 10. Tier thresholds are quality gates, not targets
Don't tune scores to hit 85.0 exactly. The tiers are gates:
- If a screen scores 79, find the lowest-scoring engine and fix it
- If all engines score ≥0.8, you'll naturally land in public-facing tier
