---
name: rig-higgsfield-workforce
description: "RIG x Higgsfield AI Employee Workforce. 6 skills, 5 custom employees, brand kit, CLI orchestration. Use when generating RIG creative assets, content packs, sales materials, or competitor intelligence."
version: 1.0.0
category: rig-operations
---

# RIG Higgsfield Workforce Skill

## When to Use
- Generate creative assets for any RIG vertical
- Create sales asset packs for prospects
- Run weekly content calendars
- Generate brand asset packs for campaigns
- Run competitor social scans
- Create customer proof video assets
- Any Higgsfield.ai creative generation for RIG

## Architecture
Two-tier model: RIG Local Control Plane (Tier 1) + Higgsfield Supercomputer (Tier 2).
Connected via Higgsfield CLI at `/Users/rig128gb/.hermes/node/bin/higgsfield`.

## Account
- **Email:** [REDACTED-EMAIL]
- **Plan:** Team
- **Credits:** ~1,596 (as of Jul 25 2026)
- **Brand Kit ID:** `59e28f28-d23b-44b7-841f-6acb99db6481` (RIG from rodgersintelligence.com)
- **Brand:** Rodgers Intelligence Group, tagline "Strategy first. AI second. Automation third."

## Skills (6 Executable Scripts)

### 1. Vertical Content Pack
```bash
~/Documents/JakeStudio/Company/RIG-Higgsfield-Skills/scripts/rig-vertical-content-pack.sh <vertical> <topic> [output_dir]
```
Generates: LinkedIn carousel, IG reel cover, email hero, landing page hero, X post image (5 assets)
Credits: ~40-60 per run

### 2. Brand Asset Pack
```bash
~/Documents/JakeStudio/Company/RIG-Higgsfield-Skills/scripts/rig-brand-asset-pack.sh <campaign_name> [output_dir]
```
Generates: 4K hero, 5 ad variants (minimalist/data-driven/bold-typography/infographic/cinematic), social banner, presentation cover (8 assets)
Credits: ~30-50 per run

### 3. Competitor Social Scan
```bash
~/Documents/JakeStudio/Company/RIG-Higgsfield-Skills/scripts/rig-competitor-social-scan.sh [output_dir]
```
Generates: 5 competitor analysis cards (Accenture AI, IBM Watson, McKinsey QuantumBlack, Deloitte AI Institute, BCG GAMMA)
Credits: ~10-15 per run

### 4. Sales Asset Pack
```bash
~/Documents/JakeStudio/Company/RIG-Higgsfield-Skills/scripts/rig-sales-asset-pack.sh <prospect_company> <prospect_vertical> [output_dir]
```
Generates: case study cover, competitor one-pager, ROI calculator, proposal cover, social proof (5 assets)
Credits: ~50-80 per run

### 5. Weekly Content Calendar
```bash
~/Documents/JakeStudio/Company/RIG-Higgsfield-Skills/scripts/rig-weekly-content-calendar.sh [week_label] [output_dir]
```
Generates: 3 LinkedIn posts, 3 Instagram reel covers, 5 X/Threads posts (11 assets)
Credits: ~60-100 per run

### 6. Customer Proof Video Pack
```bash
~/Documents/JakeStudio/Company/RIG-Higgsfield-Skills/scripts/rig-customer-proof-video.sh <customer_name> <outcome_metric> [output_dir]
```
Generates: proof cover, testimonial graphic, results dashboard, social snippet (4 assets)
Credits: ~40-60 per run

## Custom AI Employees (5)

| # | Employee | Dept Owner | Skills | Config |
|---|----------|-----------|--------|--------|
| 1 | RIG Vertical Content Engineer | Darius/Ralph/Nico | Content Pack, Brand Pack, Competitor Scan | `employees/RIG-Vertical-Content-Engineer.md` |
| 2 | RIG Sales Development Rep | Darius/Closer | Sales Pack, Content Pack, Competitor Scan | `employees/RIG-Sales-Development-Rep.md` |
| 3 | RIG Website Landing Page Producer | Nadia/Darius | Hero Gen, Brand Pack, Content Pack | `employees/RIG-Website-Landing-Page-Producer.md` |
| 4 | RIG Social Media Manager | Ralph/Nico | Content Calendar, Brand Pack, Competitor Scan | `employees/RIG-Social-Media-Manager.md` |
| 5 | RIG Customer Success Proof Generator | Cora/Nadia | Proof Video, Brand Pack, Content Pack | `employees/RIG-Customer-Success-Proof-Generator.md` |

## Available Higgsfield Models
- **Image:** nano_banana_2 (Nano Banana Pro), marketing_studio_image, seedream_v5_pro, gpt_image_2, flux_2, cinematic_studio_image
- **Video:** seedance_2_0, veo3_1, kling3_0, cinematic_studio_video_3_5, marketing_studio_video
- **Audio:** text2speech_v2, sonilo_music, seed_audio
- **Marketing:** Marketing Studio Image/Video, DTC Ads Engine, brand kits, avatars (20 presets)

## Gate-D Rules
- **Draft generation:** NO approval needed (all scripts produce drafts)
- **Publish to social:** REQUIRES Jake approval
- **Send emails:** REQUIRES Jake approval
- **Deploy to Vercel:** REQUIRES Jake approval
- **Modify CRM:** REQUIRES Jake approval

## Direct CLI Usage
```bash
HF="/Users/rig128gb/.hermes/node/bin/higgsfield"

# Generate a single image
$HF generate create nano_banana_2 --prompt "your prompt" --json

# Check generation status
$HF generate wait <job_id> --json

# List all generations
$HF generate list --json

# Account status
$HF account status --json
```
