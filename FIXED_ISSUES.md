# Fixed Issues

## Issue 1: "NOT NULL constraint failed: agents_m21scrapejob.target_parts"

**Problem**: The scraper was failing with a database constraint error when trying to create a scrape job.

**Root Cause**: The `target_parts` field was receiving `None` instead of an empty list `[]` when no parts were specified.

**Fix Applied**: Updated `agents/management/commands/scrape_m21.py` line 111:
```python
# Before:
target_parts=options.get('parts', []),

# After:
target_parts=options.get('parts') or [],
```

This ensures that even if `options.get('parts')` returns `None`, we use an empty list `[]` instead.

**Status**: ✅ FIXED

## How to Test

Run the test script:
```bash
./test_scraper.sh
```

Or manually:
```bash
source venv/bin/activate
python manage.py scrape_m21 --article-id 554400000181474
```

You should see output like:
```
=== M21-1 Scraping Job ===
Articles to scrape: 1
...
[1/1] Scraping article 554400000181474...
  Saved: M21-1.I.i.1.A - Description and General Information on Duty...
...
=== Scraping Complete ===
Successful: 1
```

## Verification

Check that the data was saved:
```bash
python manage.py shell
>>> from agents.models import M21ManualSection
>>> M21ManualSection.objects.count()
1
>>> section = M21ManualSection.objects.first()
>>> print(section.reference, section.title)
M21-1.I.i.1.A Description and General Information on Duty to Notify...
```

Or view in Django admin:
```bash
python manage.py runserver
# Visit: http://localhost:8000/admin
# Navigate to: Agents > M21 Manual Sections
```

## Next Steps

Now you can scrape all starter articles:
```bash
python manage.py scrape_m21 --import-from-file agents/data/starter_article_ids.json
```

This will scrape 8 sections and should take about 30-40 seconds.

## Issue 2: JSON Import Reading Wrong Data

**Problem**: When using `--import-from-file`, the command was trying to scrape dict objects instead of article IDs.

**Root Cause**: The JSON parser was using `list(data.values())` which returned the entire dict values, not extracting the `article_id` field.

**Fix Applied**: Updated `agents/management/commands/scrape_m21.py` lines 259-276 to properly extract `article_id` from nested dict structures.

**Status**: ✅ FIXED

## Issue 3: Bulk Scraping Failures

**Problem**: When scraping multiple articles via import file, all articles failed with "Insufficient content" errors, even though individual scrapes work.

**Root Cause**: Potential rate limiting or timing issues when scraping multiple articles rapidly.

**Workaround**: Created `scrape_starter_articles.sh` which scrapes articles one at a time with delays between each request.

**Status**: ⚠️ WORKAROUND AVAILABLE

**Recommended Approach**:
```bash
# Instead of:
# python manage.py scrape_m21 --import-from-file agents/data/starter_article_ids.json

# Use:
./scrape_starter_articles.sh
```

This script:
- Scrapes 8 starter articles one at a time
- Adds 2-second delays between requests
- Shows progress and success/failure count
- More reliable than bulk import
