---
name: rig-knowledge-ingestion
description: Scrape, process, and ingest knowledge (YouTube transcripts, arXiv papers, web content) into agent vaults. Use when building knowledge bases for department agents or need to research a domain at scale.
tags:
  - rig
  - knowledge
  - scraping
  - youtube
  - research
---

# RIG Knowledge Ingestion

## When To Use
- Building knowledge bases for department agents
- Scraping YouTube transcripts at scale
- Processing arXiv papers
- Researching a domain (AI consultants, GTM, etc.)

## Architecture

### Pipeline
```
Sources → Scrape → Extract → Chunk → Tag → Route → Store → Index → Use
```

### Storage Layers
- **Raw:** `~/rig-knowledge-raw/{department}/` (JSON files)
- **Processed:** `~/Documents/JakeStudio/Agent Vaults/{agent}/Knowledge/` (Obsidian notes)
- **Semantic:** GBrain (auto-syncs from Obsidian every 5 min)
- **Backup:** QNAP (rsync)

### Script
`~/bin/rig_department_knowledge_engine.py`

## Usage

### Scrape YouTube
```bash
python3 ~/bin/rig_department_knowledge_engine.py --department darius --sources youtube --max-per-source 25
```

### Scrape arXiv
```bash
python3 ~/bin/rig_department_knowledge_engine.py --department darius --sources arxiv --max-per-source 30
```

### Scrape Web
```bash
python3 ~/bin/rig_department_knowledge_engine.py --department darius --sources web --max-per-source 15
```

### All Sources
```bash
python3 ~/bin/rig_department_knowledge_engine.py --department darius --sources youtube,arxiv,web --max-per-source 20
```

## YouTube Scraping

### What Gets Captured
- Video title
- Transcript text (auto-generated captions)
- Video metadata (views, likes, publish date)
- Channel info

### Expected Yield
- ~15KB per video transcript
- ~50% of videos have English transcripts
- 100 queries × 25 videos = ~1,250 transcripts attempted
- Actual yield: ~500-600 transcripts with content

### Best Practices
1. Use specific queries (not generic)
2. Include year in queries for freshness
3. Run multiple query batches for coverage
4. Check raw JSON count vs processed notes count

## arXiv Scraping

### What Gets Captured
- Paper title, authors, abstract
- Full text (when available)
- Categories, keywords

### Limitations
- API can be slow/timing out
- Full papers are large (500KB+ each)
- Abstracts are small (~2KB each)

### Best Practice
- Use abstracts only for initial scrape
- Download full papers for top performers

## Web Scraping

### What Gets Captured
- Page title, URL
- Main content text
- Code blocks, examples

### Limitations
- DuckDuckGo search returns HTML that basic parser can't extract
- Need Firecrawl or Tavily for proper web content extraction
- JavaScript-rendered pages need headless browser

### Best Practice
- Use direct URLs when possible
- Use Firecrawl/Tavily for search-based scraping
- Fall back to curl + basic parsing for simple pages

## Processing Pipeline

### Step 1: Raw JSON
Each scrape produces JSON files with:
- Source URL
- Content text
- Metadata
- Timestamp

### Step 2: Obsidian Notes
Processed notes with YAML frontmatter:
```yaml
---
date: "2026-07-06"
type: "knowledge-note"
source: "youtube"
url: "https://..."
title: "Video Title"
tags: [gtm, sales, dental]
---
```

### Step 3: GBrain Sync
Automatic sync every 5 minutes via daemon.

### Step 4: QNAP Backup
```bash
rsync -avz ~/rig-knowledge-raw/darius/ qnap-ts:/share/ZFS532_DATA/rig-department-data/knowledge-raw/darius/
```

## Per-Department Knowledge Maps

### Darius (GTM/Sales)
- YouTube: B2B sales, cold email, RevOps, pipeline, pricing, discovery calls
- arXiv: Marketing, sales optimization, pricing strategy
- Web: Best practices, case studies, competitor analysis

### Steve (Strategy)
- YouTube: Strategy frameworks, positioning, competitive analysis
- arXiv: Game theory, decision theory, organizational behavior
- Web: Case studies, strategy frameworks

### Iris (Market Intel)
- YouTube: Market research, competitive intelligence, signal detection
- arXiv: Information retrieval, NLP, market analysis
- Web: Industry reports, competitor data

### Ralph (Content)
- YouTube: Content marketing, LinkedIn, copywriting
- arXiv: Communication, persuasion, social media
- Web: Content frameworks, engagement patterns

## Cron Integration

### Daily (3am)
```bash
python3 ~/bin/rig_department_knowledge_engine.py --department darius --sources youtube --max-per-source 10
```

### Weekly (Monday)
```bash
python3 ~/bin/rig_department_knowledge_engine.py --department darius --sources youtube,arxiv,web --max-per-source 20
```

## Pitfalls
1. **YouTube transcripts not available** — ~50% of videos lack English captions
2. **arXiv API slow** — can timeout, use smaller batches
3. **Web scraping needs better tools** — DuckDuckGo HTML parsing insufficient
4. **Raw vs processed gap** — 1,627 attempted → 231 raw → 215 processed
5. **Disk space** — 206MB for 215 notes, scale accordingly
6. **QNAP SSH** — needs Remote Login enabled on 96GB Studio

## Quality Checks
```bash
# Count raw transcripts
find ~/rig-knowledge-raw/{dept}/youtube -name "*.json" | wc -l

# Count processed notes
find ~/Documents/JakeStudio/Agent Vaults/{agent}/Knowledge -name "*.md" | wc -l

# Check disk usage
du -sh ~/rig-knowledge-raw/{dept}/

# Sync to QNAP
rsync -avz ~/rig-knowledge-raw/{dept}/ qnap-ts:/share/ZFS532_DATA/rig-department-data/knowledge-raw/{dept}/
```

## References
- `~/bin/rig_department_knowledge_engine.py` — Main scraper script
- `~/bin/rig_knowledge_cron_runner.py` — Daily cron runner
- `~/rig-knowledge-raw/` — Raw data storage
- `~/Documents/JakeStudio/Agent Vaults/*/Knowledge/` — Processed notes
