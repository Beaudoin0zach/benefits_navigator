# Understanding M21 Article IDs and Scraping

## What is an Article ID?

An **article ID** is the numeric identifier that KnowVA uses to identify each M21-1 section.

### Example URL Breakdown:

```
https://www.knowva.ebenefits.va.gov/system/templates/selfservice/va_ssnew/help/customer/locale/en-US/portal/554400000001018/content/554400000177422/M21-1-Part-VIII...
                                                                                                                                         |___________________|
                                                                                                                                              Article ID
```

**Article ID**: `554400000177422`

This ID is what your scraper needs to fetch that specific M21 section.

## How the Scraper Works

### What It Does:
1. Takes an article ID (like `554400000177422`)
2. Constructs the full KnowVA URL
3. Uses Playwright to render the JavaScript-heavy page
4. Extracts the content, title, and metadata
5. Saves it to your Django database

### What It Does NOT Do:
- **Does not automatically discover all sections**
- You must provide the article IDs for sections you want
- Cannot recursively crawl all M21 links (KnowVA structure prevents this)

## Your Screenshot Explained

When you showed the screenshot with all the blue links in the M21-1 table of contents:

- ✓ Each blue link = 1 separate M21 section
- ✓ Each section has a unique article ID in its URL
- ✗ The scraper does NOT automatically get all of these
- ✗ Full M21-1 has 200-500+ sections (depending on how you count subsections)

## Current Status

### You Have Successfully Scraped: **11 Sections**

#### Part I - Claimants' Rights (3 sections)
- M21-1.I.i.1.A - Duty to Notify and Duty to Assist
- M21-1.I.i.1.B - Due Process
- M21-1.I.i.2.A - Power of Attorney (POA)

#### Part II - Claims Intake (4 sections)
- M21-1.II.iii.1.A - Applications for Benefits
- M21-1.II.iii.1.B - Screening Applications
- M21-1.II.iii.1.C - Substantial Completeness
- M21-1.II.iii.2.A - Intent to File (ITF)

#### Part III - Evidence Development (1 section)
- M21-1.III.ii.2.B - Service Treatment Records (STRs)

#### Part IV - Medical Examinations (1 section)
- M21-1.IV.i.1.A - Duty to Assist With Medical Exams

#### Part V - Rating Decisions (1 section)
- M21-1.V.ii.4.A - Effective Dates for Benefits

#### Part VIII - Special Claims (1 section)
- M21-1.VIII.i.1.A - Herbicide Exposure (Agent Orange)

## How to Add More Sections

### Option 1: Use Your High-Priority List (Recommended)

I created `agents/data/high_priority_articles.json` where you can add more article IDs:

```json
{
  "V.iii.2.A": {
    "article_id": "123456789012345",
    "title": "Service Connection Requirements",
    "priority": "high"
  }
}
```

### Option 2: Extract Article IDs Manually from KnowVA

1. **Visit the M21-1 page**: https://www.knowva.ebenefits.va.gov/
2. **Navigate to the section you want** (use the blue links in the table of contents)
3. **Right-click the link** and select "Copy Link Address"
4. **Extract the article ID** from the URL:
   ```
   https://.../content/554400000177422/...
                       ^^^^^^^^^^^^^^^^
                       This is the article ID
   ```
5. **Add to your JSON file**:
   ```json
   {
     "VIII.i.1.B": {
       "article_id": "554400000177422",
       "title": "Section Title Here"
     }
   }
   ```
6. **Run the scraper**:
   ```bash
   python manage.py scrape_m21 --article-id 554400000177422
   ```

### Option 3: Use the Discovery Tool (Limited)

The discovery tool can find some article IDs automatically:

```bash
python agents/discover_article_ids.py
```

**Note**: This only finds articles directly linked from the main TOC page (usually 4-10 articles). It cannot recursively discover all sections due to KnowVA's structure.

## Available Scraping Scripts

### 1. Test Scraper (1 article)
```bash
./test_scraper.sh
```
Quick test with a single article to verify scraper is working.

### 2. Starter Articles (8 articles)
```bash
./scrape_starter_articles.sh
```
Scrapes the 8 foundational articles (Parts I and II).

### 3. High-Priority Articles (4 articles)
```bash
./scrape_priority_articles.sh
```
Scrapes the most valuable sections for claims assistance (Parts III, IV, V, VIII).

### 4. Individual Article
```bash
source venv/bin/activate
python manage.py scrape_m21 --article-id 554400000177422
```
Scrape a single article by its ID.

### 5. Bulk Import from JSON
```bash
python manage.py scrape_m21 --import-from-file agents/data/your_file.json
```
Scrape multiple articles from a JSON file (but one-at-a-time scripts are more reliable).

## Recommended Approach for Scaling

Instead of trying to scrape all 200-500 M21 sections, focus on the sections most relevant to your veterans benefits app:

### High-Value M21 Parts to Target:

1. **Part I - Claimants' Rights** ✅ (You have all starter sections)
2. **Part II - Claims Intake** ✅ (You have all starter sections)
3. **Part III - Evidence Development** ⚠️ (1 of ~30 sections scraped)
   - Focus: Records requests, evidence evaluation
4. **Part IV - Medical Examinations** ⚠️ (1 of ~20 sections scraped)
   - Focus: C&P exam procedures, DBQ requirements
5. **Part V - Rating Decisions** ⚠️ (1 of ~50 sections scraped)
   - Focus: Service connection, evaluation criteria, combined ratings
6. **Part VI - Decision Notices** 🔲 (0 sections scraped)
   - Focus: Decision letter requirements, reasons and bases
7. **Part VII - Appeals** 🔲 (0 sections scraped)
   - Focus: Notice of Disagreement, Board appeals
8. **Part VIII - Special Claims** ⚠️ (1 of ~40 sections scraped)
   - Focus: PTSD, TBI, MST, radiation exposure, presumptive conditions

### Strategy:

1. **Identify the specific topics your AI agents need** (e.g., "PTSD service connection", "combined ratings calculation", "effective dates")
2. **Navigate to those sections on KnowVA** and extract the article IDs
3. **Add them to a custom JSON file** in `agents/data/`
4. **Scrape them one at a time** using the management command or a custom script

This targeted approach gives you the most value with the least effort.

## Viewing Your Scraped Content

### Django Admin:
```bash
python manage.py runserver
```
Visit: http://localhost:8000/admin
Navigate to: **Agents** → **M21 Manual Sections**

### Command Line Status:
```bash
python check_m21_status.py
```

### Python Shell:
```bash
python manage.py shell
```
```python
from agents.models import M21ManualSection

# List all sections
for section in M21ManualSection.objects.all():
    print(f"{section.reference} - {section.title}")

# Get a specific section
section = M21ManualSection.objects.get(reference='M21-1.V.ii.4.A')
print(section.content)

# Search content
sections = M21ManualSection.objects.filter(content__icontains='service connection')
```

## Summary

- **Article ID** = the numeric part of the KnowVA URL
- **Your scraper** = works perfectly for individual articles when you provide the ID
- **11 sections scraped** = covering the most foundational M21 content
- **To get more** = manually extract article IDs from the sections you need
- **Best strategy** = target high-value sections relevant to your app, not all 500+

You have a working scraper with solid foundational content. Focus on adding sections as your AI agents need them rather than trying to scrape everything at once.
