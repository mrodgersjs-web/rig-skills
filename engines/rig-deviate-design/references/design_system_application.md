# Engine → Design Token Mapping (TransformFit Reference)

Full mapping of 16 applied RIG Deviation Engines to concrete Flutter design tokens.

## Physics Layer (±30σ)

### Engine 31: Quantum Tunneling — Cards bleed, depth layers
- Hero images: `overflow: visible`, extend ≥8px past card edge
- At least one card pair overlaps by ≥4px with z-index separation
- Recovery circle overlaps hero image with shadow for depth

### Engine 32: Pauli Exclusion — Every element visually unique
- No two cards share identical radius + shadow + accent combination
- Recovery card: pill radius + no shadow + purple accent
- Workout card: md radius + low shadow + orange accent
- Nutrition card: lg radius + medium shadow + green accent

### Engine 33: Casimir Pressure — Whitespace creates force
- Hero section: ≥48px vertical whitespace above/below
- CTA buttons: ≥32px clearance on all sides
- Interactive elements: ≥16px breathing room
- `sectionGap` (34px) > `screenMargin` (21px) > `cardGap` (13px)

### Engine 34: Fine-Tuning — Every value mathematically justified
```
Spacing (Fibonacci F4–F11):  3, 5, 8, 13, 21, 34, 55, 89
Radii (Fibonacci):           3, 5, 8, 13, 999(pill)
Typography (golden ratio):   16 × φ⁰, 16 × φ¹, 16 × φ², ...
Card ratios:                 1:0.618 (hero), 1:0.382 (compact)
```

### Engine 35: Hawking Radiation — Empty states emit info
- No workouts: `"Your body hears everything your mind says."` + `"Start with a 5-min warm-up"`
- No nutrition: `"Fuel the machine."` + `"Log your first meal"`
- No blank screens without informational content

### Engine 36: Speed of Light — Animation scales with size
```
Element ≤24px  → 100ms (icons, badges)
Element ≤48px  → 200ms (cards, buttons)
Element ≤100px → 500ms (sections, screens)
Celebration    → 1300ms (PR achievements)
```
Easing: `easeOutCubic` (arrival), `elasticOut` (celebration only), `easeOutQuart` (slides)

### Engine 37: Absolute Zero — Only meaningful motion
- No decorative-only animations
- Score number animates on change ✓ (meaningful)
- Recovery ring fills on load ✓ (meaningful)
- No idle floating/pulsing decorative elements ✗

### Engine 38: Phase Transition — Dramatic threshold changes
- Readiness crosses maintain→deload: full-screen blue tint shift
- PR achieved: explosive celebration animation + color burst
- Streak broken: dramatic fade + recovery prompt

### Engine 39: Bell Entanglement — Connected elements respond
- Mood check-in changes → recovery circle color shifts instantly
- Set logged → progress bar animates immediately
- Nutrition logged → macro rings update in real-time

### Engine 40: Vacuum Fluctuation — Empty states have energy
- Skeleton loaders pulse with `accentPrimary` at 0.3 opacity
- Empty state backgrounds have subtle gradient animation
- Typing indicators have energy/motion

## Cognitive Layer (±20σ)

### Engine 1: Gravity Escape — Break conventions
- Vertical scrolling data viz (not horizontal carousels)
- Floating action elements instead of fixed bottom bar
- Non-standard navigation patterns

### Engine 2: Reality Anchor — Ground truth interaction
- One-tap workout start from home screen
- Zero-friction mood slider (no modal)
- Instant coach response (pre-loaded suggestions)

### Engine 3: Feynman X-Ray — Reveal the science
- Readiness score shows formula: `R = (HRV + Sleep + Strain) / 3`
- Progression algorithm: `"Adding 2.5kg because you hit 3×8 last week"`
- Coach recommendation shows reasoning chain

## Nature Layer (±20σ)

### Engine 21: Ant Colony Pheromone — Usage-adaptive navigation
- Exercise library sorts by recency + frequency
- Bottom nav items reorder based on usage analytics
- Most-used features appear first in lists

### Engine 22: Bee Foraging — 60/25/15 attention split
- Home: Recovery circle = 60%, Workout card = 25%, Quick stats = 15%
- Workout: Active exercise = 60%, Next exercise = 25%, Timer = 15%
- Hero element gets ≥50% of visual attention on each screen

### Engine 23: Slime Mold Network — Self-optimizing layouts
- Dashboard card order is dynamic, not hardcoded
- Most-interacted card floats to top position
- Recently used features appear first
