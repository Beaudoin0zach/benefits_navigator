# M21 Scraper Quick Reference

## Installation (One-Time Setup)

```bash
source venv/bin/activate
./install_m21_scraper.sh
```

## Common Commands

### Scraping

```bash
# Scrape one article
python manage.py scrape_m21 --article-id 554400000181474

# Scrape starter articles (8 sections)
python manage.py scrape_m21 --import-from-file agents/data/starter_article_ids.json

# Scrape all known articles
python manage.py scrape_m21 --all

# Scrape specific parts
python manage.py scrape_m21 --parts I II V

# Force re-scrape (update existing)
python manage.py scrape_m21 --all --force

# Dry run (preview what would be scraped)
python manage.py scrape_m21 --all --dry-run

# Slow down rate limit (if getting blocked)
python manage.py scrape_m21 --all --rate-limit 5.0
```

### Discovery

```bash
# Find new article IDs automatically
python agents/discover_article_ids.py

# Show manual discovery guide
python agents/discover_article_ids.py --manual-guide
```

## Python/Django Shell

```python
from agents.models import M21ManualSection, M21TopicIndex

# Get a specific section
section = M21ManualSection.objects.get(reference='M21-1.V.ii.1.A')
print(section.title)
print(section.content)

# Search by keyword
sections = M21ManualSection.objects.filter(search_text__icontains='service connection')

# Get all rating sections (Part V)
rating_sections = M21ManualSection.objects.filter(part='V')

# Get service connection guidance
topic = M21TopicIndex.objects.get(topic='service_connection')
sections = topic.sections.all()

# Count scraped sections
total = M21ManualSection.objects.count()
print(f"Total sections: {total}")
```

## Celery Tasks

```python
from agents.tasks import (
    scrape_m21_section,
    scrape_m21_all_known,
    update_stale_m21_sections,
    build_m21_topic_indices
)

# Scrape one section (async)
scrape_m21_section.delay('554400000181474')

# Scrape all known (async)
scrape_m21_all_known.delay()

# Update stale sections
update_stale_m21_sections.delay(days_old=30)

# Rebuild topic indices
build_m21_topic_indices.delay()
```

## Using in AI Agents

```python
from agents.models import M21TopicIndex

def get_m21_context(topic: str, max_sections: int = 3):
    """Get M21 context for AI agents."""
    topic_index = M21TopicIndex.objects.get(topic=topic)
    sections = topic_index.sections.all()[:max_sections]

    return "\n\n".join([
        f"**{s.reference} - {s.title}**\n{s.overview}"
        for s in sections
    ])

# Use in prompt
context = get_m21_context('service_connection')
prompt = f"Based on M21-1:\n\n{context}\n\nAnalyze this claim..."
```

## Available Topics

- `service_connection` - Establishing service connection
- `rating_process` - Rating disabilities
- `evidence` - Evidence requirements
- `examinations` - C&P exams
- `effective_dates` - Effective dates
- `tdiu` - Individual Unemployability
- `special_monthly_compensation` - SMC
- `presumptive` - Presumptive service connection
- `secondary` - Secondary service connection
- `nexus` - Nexus/medical opinions
- `duty_to_assist` - VA's duty to assist
- `combined_ratings` - Combined rating calculations

## Monitoring

```bash
# View in Django admin
python manage.py runserver
# Visit: http://localhost:8000/admin

# Check scrape jobs
# Admin → Agents → M21 Scrape Jobs

# View scraped sections
# Admin → Agents → M21 Manual Sections

# View topic indices
# Admin → Agents → M21 Topic Indices
```

## File Locations

- **Main scraper**: `agents/knowva_scraper.py`
- **Models**: `agents/models.py`
- **Management command**: `agents/management/commands/scrape_m21.py`
- **Celery tasks**: `agents/tasks.py`
- **Discovery script**: `agents/discover_article_ids.py`
- **Starter article IDs**: `agents/data/starter_article_ids.json`
- **Full docs**: `agents/M21_SCRAPER_README.md`

## Troubleshooting

### Playwright not found
```bash
pip install playwright
playwright install chromium
```

### Django not found
```bash
source venv/bin/activate
```

### Scraping fails
```bash
# Debug with visible browser
python manage.py scrape_m21 --article-id 554400000181474 --no-headless

# Increase rate limit
python manage.py scrape_m21 --all --rate-limit 5.0
```

### Check logs
```bash
# View scrape job in Django admin for error details
# Or check Python logs if configured
```

## URLs

- **KnowVA M21-1**: https://www.knowva.ebenefits.va.gov
- **Article URL Format**:
  ```
  https://www.knowva.ebenefits.va.gov/system/templates/selfservice/va_ssnew/help/customer/locale/en-US/portal/554400000001018/content/{article_id}/
  ```

## Example Workflow

```bash
# 1. Install (one time)
./install_m21_scraper.sh

# 2. Scrape starter content
python manage.py scrape_m21 --import-from-file agents/data/starter_article_ids.json

# 3. View results
python manage.py shell
>>> from agents.models import M21ManualSection
>>> M21ManualSection.objects.count()
8
>>> section = M21ManualSection.objects.first()
>>> print(section.reference, section.title)

# 4. Use in your app
>>> from agents.models import M21TopicIndex
>>> topic = M21TopicIndex.objects.get(topic='service_connection')
>>> sections = topic.sections.all()
>>> # Use sections in your AI agents

# 5. Discover more articles
exit()
python agents/discover_article_ids.py

# 6. Scrape discovered articles
python manage.py scrape_m21 --import-from-file agents/data/discovered_m21_articles.json

# 7. Schedule automated updates (optional)
# Edit benefits_navigator/celery.py and add beat schedule
```

## Getting Help

1. **Quick Setup**: `agents/SETUP_GUIDE.md`
2. **Full Documentation**: `agents/M21_SCRAPER_README.md`
3. **Complete Overview**: `M21_SCRAPER_SUMMARY.md`
4. **This Reference**: `agents/QUICK_REFERENCE.md`
