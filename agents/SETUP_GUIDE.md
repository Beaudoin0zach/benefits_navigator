# M21 Scraper Setup Guide

Quick guide to get the M21-1 scraper up and running.

## Step 1: Activate Virtual Environment

```bash
cd /Users/zachbeaudoin/benefits-navigator
source venv/bin/activate
```

## Step 2: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Step 3: Run Database Migrations

```bash
# Create migrations for new M21 models
python manage.py makemigrations agents

# Apply migrations
python manage.py migrate
```

## Step 4: Test the Scraper

### Quick Test - Scrape One Article

```bash
# Dry run to see what would happen
python manage.py scrape_m21 --article-id 554400000181474 --dry-run

# Actually scrape (will take ~10-15 seconds)
python manage.py scrape_m21 --article-id 554400000181474

# Check if it worked
python manage.py shell
>>> from agents.models import M21ManualSection
>>> section = M21ManualSection.objects.first()
>>> print(section.reference, section.title)
>>> exit()
```

### Scrape Starter Articles

```bash
# Import from the starter file (8 articles)
python manage.py scrape_m21 --import-from-file agents/data/starter_article_ids.json

# This will take about 30-40 seconds (8 articles × 3 second rate limit)
```

## Step 5: Verify in Django Admin

```bash
# Create superuser if you haven't already
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Visit http://localhost:8000/admin
# Navigate to Agents > M21 Manual Sections
# You should see the scraped content!
```

## Step 6: Build Topic Indices (Optional)

```bash
python manage.py shell
>>> from agents.tasks import build_m21_topic_indices
>>> build_m21_topic_indices()
>>> exit()
```

## Step 7: Set Up Automated Scraping (Optional)

Add to `benefits_navigator/celery.py`:

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    # Scrape all known M21 sections weekly
    'scrape-m21-weekly': {
        'task': 'agents.tasks.scrape_m21_all_known',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2 AM
    },
    # Update stale sections daily
    'update-stale-m21': {
        'task': 'agents.tasks.update_stale_m21_sections',
        'schedule': crontab(hour=3, minute=0),  # Daily 3 AM
        'kwargs': {'days_old': 30}
    },
    # Rebuild topic indices weekly
    'rebuild-m21-topics': {
        'task': 'agents.tasks.build_m21_topic_indices',
        'schedule': crontab(hour=4, minute=0, day_of_week=1),  # Monday 4 AM
    },
}
```

Then start Celery beat:

```bash
# In terminal 1: Start Celery worker
celery -A benefits_navigator worker --loglevel=info

# In terminal 2: Start Celery beat scheduler
celery -A benefits_navigator beat --loglevel=info
```

## Troubleshooting

### "playwright: command not found"

```bash
# Make sure Playwright is installed
pip install playwright
playwright install chromium
```

### "No module named 'playwright'"

```bash
# Activate virtual environment first
source venv/bin/activate
pip install playwright
```

### Scraping fails or times out

```bash
# Run with visible browser to see what's happening
python manage.py scrape_m21 --article-id 554400000181474 --no-headless

# Increase rate limit if VA is rate-limiting you
python manage.py scrape_m21 --all --rate-limit 5.0
```

### Docker Setup

If using Docker, add Playwright installation to your Dockerfile:

```dockerfile
# Install Playwright and dependencies
RUN pip install playwright
RUN playwright install --with-deps chromium
```

## Next Steps

1. **Discover More Articles**: Use the discovery script to find more M21 sections
   ```bash
   python agents/discover_article_ids.py
   ```

2. **Scrape All Known Content**: Once you have article IDs
   ```bash
   python manage.py scrape_m21 --all
   ```

3. **Integrate with AI Agents**: Use the M21 content in your claims analysis agents
   ```python
   from agents.models import M21TopicIndex

   # Get service connection guidance for AI context
   topic = M21TopicIndex.objects.get(topic='service_connection')
   sections = topic.sections.all()[:3]

   context = "\n\n".join([
       f"**{s.reference} - {s.title}**\n{s.overview}"
       for s in sections
   ])
   ```

4. **Keep Content Updated**: Schedule regular scraping or run manually
   ```bash
   # Update sections older than 30 days
   python manage.py shell
   >>> from agents.tasks import update_stale_m21_sections
   >>> update_stale_m21_sections(days_old=30)
   ```

## Reference

- Full documentation: `agents/M21_SCRAPER_README.md`
- Known article IDs: `agents/knowva_scraper.py` (KNOWN_ARTICLE_IDS)
- Starter articles: `agents/data/starter_article_ids.json`

## Quick Commands Reference

```bash
# Scrape one section
python manage.py scrape_m21 --article-id 554400000181474

# Scrape by reference
python manage.py scrape_m21 --reference I.i.1.A

# Scrape all known
python manage.py scrape_m21 --all

# Scrape specific parts
python manage.py scrape_m21 --parts I II V

# Force re-scrape (update existing)
python manage.py scrape_m21 --all --force

# Dry run (see what would be scraped)
python manage.py scrape_m21 --all --dry-run

# Import from file
python manage.py scrape_m21 --import-from-file path/to/articles.json
```

## Support

If you run into issues:
1. Check `agents/M21_SCRAPER_README.md` for detailed troubleshooting
2. Look at scrape job records in Django admin
3. Run with `--no-headless` to debug visually
4. Check if KnowVA site structure has changed
