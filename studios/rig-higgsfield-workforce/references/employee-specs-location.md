# RIG-Higgsfield Employee Spec Location

## Where the full employee markdowns live

All 9 employee specs (5 custom + 4 marketplace) are in:

```
~/Documents/JakeStudio/Company/RIG-Higgsfield-Employees/
  INDEX.md                                      # Master roster, build sequence, credit budget, Gate-D protocol
  custom-employees/
    01-RIG-Vertical-Content-Engineer.md         # 5 assets/run: LinkedIn carousel, IG reel cover, email hero, landing hero, X post
    02-RIG-Sales-Development-Rep.md             # 5 assets/run: case study cover, competitor one-pager, ROI calculator, proposal cover, social proof
    03-RIG-Social-Media-Manager.md              # 11 assets/week: 3 LinkedIn + 3 IG reel + 5 X/Threads posts
    04-RIG-Website-Landing-Page-Producer.md     # 6 assets/run: hero desktop + mobile, feature section, testimonial, pricing tiers, CTA banner
    05-RIG-Customer-Success-Proof-Generator.md  # 5 assets/run: case study cover, results infographic, before/after, testimonial card, one-pager
  marketplace-employees/
    01-AI-Motion-Designer.md                    # ~450 credits/mo: static-to-motion video for social
    02-AI-Product-Photographer.md               # ~220 credits/mo: product/dashboard mockup photography
    03-AI-Cartoon-Animator.md                   # ~845 credits/mo: animated explainers for vertical audiences
    04-AI-Podcast-Producer.md                   # ~212 credits/mo: podcast cover art, audiograms, promo graphics
```

Total: 10 files, 1,329 lines, all following the RIG 12-layer employee contract.

## Automation Scripts Location

```
~/Documents/JakeStudio/Company/RIG-Higgsfield-Skills/scripts/
  rig-vertical-content-pack.sh     # 5 assets per vertical
  rig-brand-asset-pack.sh          # landing page + brand assets
  rig-competitor-social-scan.sh    # 5 competitor analysis cards
  rig-sales-asset-pack.sh          # 5 sales enablement assets per prospect
  rig-weekly-content-calendar.sh   # 11 weekly social post images
  rig-customer-proof-video.sh      # 5 proof/ROI assets per client
```

All scripts are `chmod +x` and tested. 28 images generated successfully across initial runs.

## Higgsfield Platform Config

| Setting | Value |
|---------|-------|
| Account | [REDACTED-EMAIL] (Team plan) |
| CLI Path | `/Users/rig128gb/.hermes/node/bin/higgsfield` |
| Brand Kit ID | `59e28f28-d23b-44b7-841f-6acb99db6481` |
| Primary Model | `nano_banana_2` (Nano Banana Pro, 2K) |
| Layout Model | `marketing_studio_image` (Marketing Studio) |

## Estimated Monthly Credit Usage

| Employee | Credits/Month |
|----------|--------------|
| 5 custom employees | ~1,400 |
| 4 marketplace employees | ~1,727 |
| **Total** | **~3,127/mo** |

Budget $200-400/mo for additional credits above Team plan allotment.
