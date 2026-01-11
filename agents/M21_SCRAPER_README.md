# M21-1 Manual Scraper

A comprehensive web scraping solution for VA's M21-1 Adjudication Procedures Manual from KnowVA.

## Overview

The M21-1 is VA's internal manual for processing claims. It contains critical information about how VA applies laws and regulations. This scraper:

- ✅ Scrapes current M21-1 content from VA's official KnowVA system
- ✅ Handles JavaScript-rendered pages with Playwright
- ✅ Parses structured content (parts, subparts, chapters, sections, topics)
- ✅ Stores content in Django models for easy access by AI agents
- ✅ Supports automated scheduled scraping with Celery
- ✅ Rate-limits requests to be respectful of VA servers
- ✅ Tracks scraping jobs and handles errors gracefully

## Quick Start

### 1. Install Dependencies

```bash
# Install Playwright and browser
pip install -r requirements.txt
playwright install chromium

# Or just the scraping dependencies
pip install playwright beautifulsoup4 lxml
playwright install chromium
```

### 2. Run Database Migrations

```bash
python manage.py makemigrations agents
python manage.py migrate
```

### 3. Scrape Known Articles

```bash
# Scrape all known M21-1 articles
python manage.py scrape_m21 --all

# Scrape a specific article by ID
python manage.py scrape_m21 --article-id 554400000181474

# Scrape by reference
python manage.py scrape_m21 --reference I.i.1.A

# Scrape specific parts
python manage.py scrape_m21 --parts I II III
```

## Usage

### Management Command Options

```bash
python manage.py scrape_m21 [options]

Options:
  --article-id ID          Scrape specific article ID
  --reference REF          Scrape by M21-1 reference (e.g., I.i.1.A)
  --all                    Scrape all known articles
  --parts I II III         Scrape specific parts
  --force                  Force re-scrape even if exists
  --dry-run               Show what would be scraped
  --headless              Run browser in headless mode (default)
  --no-headless           Show browser window (for debugging)
  --rate-limit SECONDS    Delay between requests (default: 3.0)
  --import-from-file FILE Import article IDs from JSON file
```

### Example Workflows

#### Initial Setup: Scrape All Known Content

```bash
# Dry run to see what will be scraped
python manage.py scrape_m21 --all --dry-run

# Actually scrape (will take 10-20 minutes for all known articles)
python manage.py scrape_m21 --all
```

#### Update Specific Sections

```bash
# Force update a specific section
python manage.py scrape_m21 --reference V.ii.1.A --force

# Update all Part V (Rating Process) sections
python manage.py scrape_m21 --parts V --force
```

#### Import from File

```bash
# Create a JSON file with article IDs
cat > my_articles.json << 'EOF'
{
  "I.i.1.A": "554400000181474",
  "I.i.1.B": "554400000181476",
  "V.ii.1.A": "554400000182145"
}
EOF

# Import and scrape
python manage.py scrape_m21 --import-from-file my_articles.json
```

### Discovering Article IDs

#### Method 1: TOC Crawler (Recommended)

The most comprehensive method crawls the M21-1 Table of Contents page to discover all article IDs:

```bash
# Run TOC discovery (discovers ~550 articles)
python agents/discover_from_toc.py

# Output files created:
# - agents/data/toc_discovered_articles.json (all discovered)
# - agents/data/m21_article_ids.json (M21-related filtered)
```

The TOC page (article ID: 554400000073398) contains links to all M21 sections.

#### Method 2: Legacy Discovery Script

For targeted discovery:

```bash
# Attempt automated discovery
python agents/discover_article_ids.py

# Show manual discovery guide
python agents/discover_article_ids.py --manual-guide

# Run with visible browser (for debugging)
python agents/discover_article_ids.py --no-headless
```

#### Manual Discovery Steps

1. Visit https://www.knowva.ebenefits.va.gov
2. Search for "M21-1"
3. Navigate to a section you want
4. The URL will look like:
   ```
   .../content/554400000181474/M21-1-Part-I-Subpart-i-Chapter-1-Section-A...
   ```
5. The article ID is `554400000181474`
6. Add to `agents/data/m21_article_ids.json` or `agents/knowva_scraper.py`

### Celery Tasks (Automated Scraping)

For production deployment, use Celery for scheduled scraping:

```python
from agents.tasks import scrape_m21_all_known, update_stale_m21_sections

# Scrape all known articles (run weekly)
scrape_m21_all_known.delay()

# Update sections older than 30 days (run daily)
update_stale_m21_sections.delay(days_old=30)

# Scrape specific article
from agents.tasks import scrape_m21_section
scrape_m21_section.delay('554400000181474', force_update=False)
```

#### Celery Beat Schedule

Add to `benefits_navigator/celery.py`:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'scrape-m21-weekly': {
        'task': 'agents.tasks.scrape_m21_all_known',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2 AM
    },
    'update-stale-m21-daily': {
        'task': 'agents.tasks.update_stale_m21_sections',
        'schedule': crontab(hour=3, minute=0),  # Daily 3 AM
        'kwargs': {'days_old': 30}
    },
}
```

### Using Scraped Data

#### Query M21 Sections

```python
from agents.models import M21ManualSection

# Get a specific section
section = M21ManualSection.objects.get(reference='M21-1.V.ii.1.A')
print(section.title)
print(section.content)

# Search by keyword
sections = M21ManualSection.objects.filter(
    search_text__icontains='service connection'
)

# Get all rating process sections (Part V)
rating_sections = M21ManualSection.objects.filter(part='V')

# Get topics for a section
section = M21ManualSection.objects.get(reference='M21-1.I.i.1.A')
for topic in section.topics:
    print(f"{topic['code']}: {topic['title']}")
```

#### Use Topic Indices

```python
from agents.models import M21TopicIndex

# Find sections about service connection
service_connection_index = M21TopicIndex.objects.get(topic='service_connection')
sections = service_connection_index.sections.all()

for section in sections:
    print(f"{section.reference} - {section.title}")
```

#### Build Topic Indices

```python
from agents.tasks import build_m21_topic_indices

# Rebuild all topic indices
result = build_m21_topic_indices.delay()
```

## Models

### M21ManualSection

Stores individual M21-1 sections with full content and metadata.

**Fields:**
- `part`, `subpart`, `chapter`, `section` - Hierarchical identifiers
- `reference` - Short reference like "M21-1.I.i.1.A"
- `full_reference` - Full reference like "M21-1, Part I, Subpart i, Chapter 1, Section A"
- `title` - Section title
- `content` - Full section content (HTML/markdown)
- `overview` - Introduction/overview text
- `topics` - JSON array of structured topics within section
- `references` - JSON array of cross-references to other M21-1 sections and CFR
- `article_id` - KnowVA article ID
- `knowva_url` - Original URL
- `scraped_at`, `last_scraped` - Scraping timestamps
- `scrape_status` - Success/failed/stale/pending

### M21TopicIndex

Topic-based index for finding relevant sections.

**Topics:**
- `service_connection` - How VA establishes service connection
- `rating_process` - Rating disabilities and assigning percentages
- `evidence` - Evidence requirements and weighing
- `examinations` - C&P exam procedures
- `effective_dates` - Determining effective dates
- `tdiu` - Total Disability Individual Unemployability
- `special_monthly_compensation` - SMC for severe disabilities
- And more...

### M21ScrapeJob

Tracks scraping jobs for monitoring and debugging.

**Fields:**
- `status` - pending/running/completed/failed/partial
- `total_sections`, `sections_completed`, `sections_failed` - Progress tracking
- `started_at`, `completed_at`, `duration_seconds` - Timing
- `summary` - JSON summary of results
- `error_log` - Errors encountered

## Architecture

### Components

1. **KnowVAScraper** (`agents/knowva_scraper.py`)
   - Core scraping logic using Playwright
   - Handles JavaScript rendering, rate limiting, retries
   - Parses HTML content into structured data

2. **Django Models** (`agents/models.py`)
   - `M21ManualSection` - Stores scraped content
   - `M21TopicIndex` - Organizes sections by topic
   - `M21ScrapeJob` - Tracks scraping jobs

3. **Management Command** (`agents/management/commands/scrape_m21.py`)
   - CLI interface for scraping
   - Handles dry-run, force update, filtering by parts/references

4. **Celery Tasks** (`agents/tasks.py`)
   - Asynchronous scraping tasks
   - Scheduled updates
   - Bulk operations

5. **Article Discoverer** (`agents/discover_article_ids.py`)
   - Helps find new article IDs from KnowVA
   - Provides manual discovery guide

### Data Flow

```
KnowVA Website
      ↓
Playwright Browser (renders JavaScript)
      ↓
KnowVAScraper (extracts content)
      ↓
Structured Data (dict)
      ↓
Django Model (M21ManualSection)
      ↓
PostgreSQL Database
      ↓
AI Agents / Views / API
```

## Current Data Status

**As of January 2026:**
- **459 article IDs discovered** via TOC crawling
- **365 sections scraped** with valid content
- **~95 articles** returned empty/historical content (expected)

### Coverage by Part

| Part | Sections | Description |
|------|----------|-------------|
| I | 9 | Claimants' Rights |
| II | 26 | Intake, Claims Establishment |
| III | 15 | Development Process |
| IV | 15 | Examinations |
| V | 35 | Rating Process |
| VI | 21 | Authorization Process |
| VII | 20 | Dependency |
| VIII | 61 | Special Compensation |
| IX | 23 | Pension |
| X | 65 | Benefits Administration |
| XI | 16 | Death Benefits |
| XII | 21 | DIC/Survivor Benefits |
| XIII | 38 | Eligibility Determinations |

### Data Files

- `agents/data/m21_article_ids.json` - 459 discovered article IDs
- `agents/data/toc_discovered_articles.json` - Full discovery results with metadata

**To refresh:** Run `python agents/discover_from_toc.py` to re-crawl the TOC.

## Troubleshooting

### Playwright Installation Issues

```bash
# Install browsers
playwright install chromium

# Or with dependencies (Linux)
playwright install --with-deps chromium

# Check installation
playwright --version
```

### Scraping Fails

```bash
# Run with visible browser to debug
python manage.py scrape_m21 --article-id 554400000181474 --no-headless

# Check logs
tail -f logs/scraper.log

# Verify article ID is correct
# Visit https://www.knowva.ebenefits.va.gov/system/templates/selfservice/va_ssnew/help/customer/locale/en-US/portal/554400000001018/content/{article_id}/
```

### Rate Limiting

If you get blocked by VA servers:

```bash
# Increase rate limit (wait longer between requests)
python manage.py scrape_m21 --all --rate-limit 5.0

# Scrape in smaller batches
python manage.py scrape_m21 --parts I
# Wait a few hours
python manage.py scrape_m21 --parts II
```

### No Data Extracted

The scraper tries multiple CSS selectors. If content structure changes:

1. Open the page in browser
2. Inspect the HTML structure
3. Update selectors in `KnowVAScraper._parse_page()`

## Best Practices

### Ethical Scraping

- ✅ **Respect rate limits** - Default 3 seconds between requests
- ✅ **Don't overload servers** - Scrape during off-peak hours
- ✅ **Identify yourself** - Uses realistic user agent
- ✅ **Handle errors gracefully** - Retries with exponential backoff
- ✅ **Check robots.txt** - Respect VA's crawling policies

### Data Maintenance

- **Run weekly updates** - M21-1 changes frequently
- **Monitor scrape jobs** - Check `M21ScrapeJob` records for failures
- **Rebuild topic indices** - After adding new sections
- **Version control** - Consider storing content snapshots

### Performance

- **Use Celery for bulk operations** - Don't block web requests
- **Scrape incrementally** - Only update stale sections
- **Cache results** - Don't re-scrape unless necessary

## Integration with AI Agents

The M21 content is designed to be used by AI agents for claims analysis.

### Database-Backed Reference Data (Recommended)

The `agents/reference_data.py` module provides convenient functions that query the database:

```python
from agents.reference_data import (
    get_m21_section_from_db,
    search_m21_in_db,
    get_m21_sections_by_part,
    get_m21_stats,
    get_m21_section,  # Tries DB first, falls back to JSON
    search_m21_sections,  # Tries DB first, falls back to JSON
)

# Get a specific section by reference
section = get_m21_section_from_db('V.ii.2.A')
print(section['title'])
print(section['overview'])
print(section['content'])

# Search by keyword
results = search_m21_in_db('service connection', part_filter='V', limit=10)
for r in results:
    print(f"{r['reference']}: {r['title']}")

# Get all sections for a part
part_v_sections = get_m21_sections_by_part('V', limit=50)

# Get database stats
stats = get_m21_stats()
print(f"Total sections: {stats['total']}")
print(f"By part: {stats['by_part']}")
```

### Using Topic Indices

```python
from agents.models import M21ManualSection, M21TopicIndex

# Find sections about service connection
topic = M21TopicIndex.objects.get(topic='service_connection')
sections = topic.sections.all()[:5]

for section in sections:
    print(f"{section.reference} - {section.title}")
```

### Direct Model Queries

```python
from agents.models import M21ManualSection

# Get a specific section
section = M21ManualSection.objects.get(reference='M21-1.V.ii.1.A')
print(section.content)

# Search by keyword
sections = M21ManualSection.objects.filter(
    search_text__icontains='service connection'
)

# Get all rating process sections (Part V)
rating_sections = M21ManualSection.objects.filter(part='V')
```

### Using in AI Prompts

```python
from agents.reference_data import get_m21_section_from_db
import json

def get_service_connection_guidance():
    """Get M21 guidance on service connection for AI context."""
    sections = [
        get_m21_section_from_db('V.ii.2.A'),  # Direct SC
        get_m21_section_from_db('V.ii.2.B'),  # Presumptive SC
        get_m21_section_from_db('V.ii.2.D'),  # Secondary SC
    ]

    context = []
    for section in sections:
        if section:
            context.append({
                'reference': section['reference'],
                'title': section['title'],
                'overview': section['overview'][:500],
            })

    return context

# Use in AI prompt
guidance = get_service_connection_guidance()
prompt = f"""
Based on VA's M21-1 manual:

{json.dumps(guidance, indent=2)}

Analyze this veteran's claim...
"""
```

## Roadmap

**Completed:**
- [x] Auto-discovery of new sections (TOC crawler)
- [x] Database-backed reference data functions

**Future enhancements:**
- [ ] Full-text search with PostgreSQL FTS or Elasticsearch
- [ ] Change detection (diff previous versions)
- [ ] PDF export of sections
- [ ] API endpoint for M21 content
- [ ] Admin dashboard for scraping management
- [ ] OCR for embedded images/tables
- [ ] Cross-reference link extraction and following
- [ ] Integration with CFR database
- [ ] Build topic indices from scraped content

## Support

For issues:
1. Check the troubleshooting section above
2. Review error logs in `M21ScrapeJob` records
3. Run with `--no-headless` to see what's happening
4. Check if KnowVA site structure has changed

## License

This scraper is for educational and veteran advocacy purposes. The M21-1 manual content is a U.S. Government publication and is in the public domain.
