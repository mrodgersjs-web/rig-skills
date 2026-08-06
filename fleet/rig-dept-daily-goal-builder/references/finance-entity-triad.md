# Finance Dept — Entity Triad Pattern

Reference for `rig-dept-daily-goal-builder` when the cron target is the **finance** department (`~/.rig/departments/finance/`). Discovered/validated on cycle `1783387806` (2026-07-06).

## Why finance is different from other RIG departments

Other depts (legal, sales, design) have a corpus of *discrete documents* (GDPR articles, sales playbooks, design systems) that map 1:1 to entity pages. Finance has continuous *formulas*, *pricing models*, and *forecasts* — none of which have a natural "page" in the source. The cron must synthesize the catalog from first principles + scraped sources.

## The triad: each entity carries all three layers

Every finance entity page should compose:

1. **Unit Economics Formula** — the math (ARR, LTV, CAC, GM%, NRR, churn, payback, burn multiple, rule of 40, etc.)
2. **Pricing Model Linkage** — which Stripe price shapes drive the inputs (per-seat vs usage vs tiered vs flat)
3. **Runway Forecast Application** — how the formula slots into the 3-statement model and runway calculation

Why all three in one page: the verifier + L7-promoter can score an entity on coverage (does it have a formula?), pricing fit (does it apply to a pricing archetype?), and forecast utility (does it move the runway model?). Without the triad the entity is just trivia.

## Working composition for 80 entities / cycle

| Group | Count | Examples |
|---|---|---|
| Unit-economics formulas | 20 | ARR, MRR, LTV, CAC, LTV/CAC, CAC_PAYBACK, GROSS_MARGIN, NRR, GRR, CHURN_RATE, ANNUAL_CHURN, ARPU, QUICK_RATIO, MAGIC_NUMBER, RULE_OF_40, PAYBACK_PERIOD, BURN_MULTIPLE, RUNWAY_MONTHS, BREAK_EVEN_CAC, EXPANSION_MRR |
| Pricing models | 20 | FLAT_RATE, PER_SEAT, PER_API_CALL, TIERED_USAGE, FREEMIUM, FREE_TRIAL, REVERSE_TRIAL, PLG_USAGE, VOLUME_DISCOUNT, PER_FEATURE_TIER, PER_OUTCOME, PER_ACTIVE_USER, HYBRID, CONSUMPTION, ANNUAL_PREPAY, MARKETPLACE_FEE, PER_NODE, PER_WORKFLOW, ENTERPRISE_TIERED, CREDITS_PACK |
| Runway forecasts | 20 | BOOTSTRAP_RUNWAY, SEED_RUNWAY, SERIES_A/B_RUNWAY, GROWTH_RUNWAY, ZERO_BURN, DEFAULT_ALIVE/DEAD, SCENARIO_BULL/BEAR/BASE, CASH_FLOW_3STMT, HEADCOUNT_MODEL, COGS_FORECAST, GROSS_PROFIT_FORECAST, OPEX_FORECAST, EBITDA_FORECAST, FREE_CASH_FLOW, BRIDGE_TO_PROFIT, REVENUE_RAMP |
| Stripe ops | 20 | SUBSCRIPTION_LIFECYCLE, PRORATION, INVOICE, PAYMENT_INTENT, SIGMA_METRICS, TAX, BILLING_PORTAL, CONNECT, REVENUE_RECOG, DUNNING, QUOTE, WEBHOOKS, USAGE_RECORDS, TRIAL, MULTI_SUB, DISCOUNT, TAX_ID, REPORTING, RADAR, ATLAS |

Rotation target: ≥50% fresh per cycle. With 80 entities per cycle and prior-corpus compounding (~91 cumulative after first cycle), fresh-pct drifts toward ~88% on the second cycle, then ~52% by the third — comfortably above the 40% floor.

## Worked example (formulas group)

```
name: "Annual Recurring Revenue"
unit_economics_formula: "ARR = MRR × 12"
pricing_model_linkage: "annual_equivalent = (monthly_price × 12) if cadence=month
                       = annual_price        if cadence=year"
runway_forecast_application: "target_arr_24mo = current_arr × (1 + growth_rate)^24
                              implied_cac_budget = target_arr_24mo × max_cac_pct_of_arr (typically 0.4-0.6)"
worked_example: "500 customers × $833/mo = $415K MRR → ARR = $4.98M"
source_citations: ["stripe-docs (live)", "github: edjiney/SaaS-Unit-Economics-Model"]
```

Same triad applies to a pricing-model entity (formula = how ARR decomposes per tier; pricing = tier matrix; forecast = which mix maximizes runway) and a forecast entity (formula = the projection math; pricing = which mix it assumes; runway = the resulting cash picture).

## Sources

- **Stripe docs** (live): primary source for pricing + billing lifecycle + Sigma metrics
  - `https://stripe.com/docs/api`
  - `https://stripe.com/docs/billing`
  - `https://stripe.com/docs/revenue-recognition`
- **saas-unit-economics GitHub cluster** (real): 61-repo result set; fetch ~30 per cycle for variety
  - query: `https://api.github.com/search/repositories?q=saas+unit+economics&per_page=30`
  - rotating subset keeps topics fresh across cycles

## Worked cron-output snapshot (cycle 1783387806)

```
Entities: 80 (20+20+20+20)
Topics: 40 (30 GitHub-derived + 10 RIG-derived patterns)
Freshness: 100% (this-cycle-only writes)
Verifier: PASS (tier-3, north_star=gross_margin_pct_x_runway_months)
Blocklist: PASS (strict word-boundary grep, 0 matches)
Proof: /Users/rig128gb/.rig/departments/finance/proof/proofpacket-cycle-1783387806.json
Obsidian: /Users/rig128gb/Documents/JakeStudio/Department PAI/finance/cycle-1783387806-finance-daily.md
```

## Pitfalls specific to finance

1. **GitHub search returns variable counts** — `?q=saas+unit+economics+model` returns 12 repos; broaden to `?q=saas+unit+economics` for 61 repos. Use the broader query to get 30 unique repos for the topics layer.
2. **Don't merge topics and entities** — topics live in `substrate/patterns/candidates-cycle-{ts}.md`; entities live in `substrate/entities/cycle-{ts}/`. The verifier reads them separately.
3. **Source citations must be real** — "Stripe docs (live, fetched 2026-07-06)" is fine; "various SaaS blogs" is not. The L7 promoter checks for `source:` and `url:` in the frontmatter.
4. **Cumulative-entity math** — `cumulative_entities = prior_cumulative + this_cycle_writes`. The finance `_state.json` had 11 prior entities; cycle wrote 80; cumulative = 91.
5. **Compound via pattern reuse** — each cycle's GitHub repo subset becomes input to the next cycle's formula/predictor; rotate the subset (don't always pick top 30 by stars).

## Reuse for other dept crons

The triad (formula + pricing model + runway forecast) is finance-specific, but the **composition strategy** generalizes:

- **GTM dept**: triad = signal + play + outcome
- **Sales dept**: triad = objection + talk-track + win-condition
- **Product dept**: triad = feature + JTBD + metric
- **Content dept**: triad = hook + format + channel-fit

When the cron pattern generalizes, lift it into the parent SKILL.md so other dept cycles can copy.