# VA Benefits Navigator - Project Status

**Last Updated:** 2026-01-11 (Critical Bug Fixes & Test Improvements)
**Current Phase:** Phase 3+ - Core Features Complete, All 188 Tests Passing

## Overview

The VA Benefits Navigator is a Django-based web application designed to help veterans navigate the VA benefits system, with a focus on disability claims preparation, C&P exam guidance, appeals assistance, and disability rating calculations.

## What's Built and Working

### Phase 1: Foundation ✅ COMPLETE
- Django 5.0.1 project structure
- PostgreSQL 15 database
- Redis 7 for caching and Celery
- Docker Compose development environment
- Custom User model with email authentication
- User profiles with veteran-specific fields
- Subscription management (Stripe integration ready)
- All containers running successfully

### Phase 2: Document Upload & AI Analysis ✅ COMPLETE
- Document upload system with drag-and-drop
- OCR processing (Tesseract, PyMuPDF)
- AI-powered analysis (OpenAI integration)
- Celery background task processing
- Claims tracking system
- Magic byte file validation for security

### Phase 3: C&P Exam Preparation ✅ COMPLETE
**Content:**
- 4 comprehensive C&P exam guides (General, PTSD, Musculoskeletal, Hearing)
- 46 VA glossary terms with plain-language definitions
- Interactive preparation checklists

**Features:**
- Full CRUD for user checklists
- HTMX-powered task toggling
- Search functionality in glossary

### Phase 3.5: Rating Calculator ✅ NEW - COMPLETE
**Features:**
- Accurate VA Math calculation (38 CFR § 4.25)
- Bilateral factor support (38 CFR § 4.26)
- 2024 compensation rates with dependents
- Step-by-step calculation explanation
- Save/load calculations for logged-in users
- "What if" scenario testing

**Technical:**
- `examprep/va_math.py` - Core calculation engine
- `SavedRatingCalculation` model for persistence
- HTMX real-time calculation updates

### Phase 4: Appeals System ✅ FOUNDATION COMPLETE
- Appeal tracking with workflow states
- Appeal guidance content
- Decision tree for choosing appeal lane
- Document attachment to appeals
- Notes system for appeals

### User Dashboard ✅ COMPLETE
- Overview of documents, checklists, appeals
- Quick action links
- Stats and alerts

### Security Hardening ✅ COMPLETE
- Content-Security-Policy headers (django-csp)
- Rate limiting on auth views (django-ratelimit)
- SECRET_KEY enforcement in production
- Magic byte file validation (python-magic)
- PDF page count validation (max 100 pages)
- Session/CSRF cookie security
- HSTS in production
- **Audit logging middleware** (enabled 2026-01-11)
- **Security headers middleware** (enabled 2026-01-11)

### Journey Dashboard ✅ COMPLETE (Fixed 2026-01-11)
- Claims and appeals timeline view
- Upcoming deadlines tracking
- Stats overview (documents, checklists, appeals)
- Navigation link in header

### Homepage ✅ COMPLETE
- Compelling value proposition
- Feature cards (4 features)
- Trust signals
- Logged-in user quick links

### M21-1 Manual Scraper ✅ NEW - COMPLETE
**Data Scraped:**
- 365 M21 manual sections across 13 Parts
- Discovered via TOC crawling (459 articles found, 365 with valid content)
- Full content, overviews, topics, and cross-references stored

**Coverage by Part:**
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

**Technical:**
- `agents/knowva_scraper.py` - Playwright-based scraper
- `agents/discover_from_toc.py` - TOC crawler for article discovery
- `agents/reference_data.py` - Database-backed M21 data access (updated)
- `agents/management/commands/scrape_m21.py` - Django management command

## Technology Stack

**Backend:**
- Django 5.0.1
- Python 3.11
- PostgreSQL 15
- Redis 7
- Celery 5.3.6 + django-celery-beat 2.6.0

**Frontend:**
- Django templates with Tailwind CSS (CDN)
- HTMX 1.9.10 for interactivity
- django-crispy-forms with crispy-tailwind

**Security:**
- django-csp 3.8
- django-ratelimit 4.1.0
- python-magic 0.4.27
- argon2-cffi for password hashing

**Infrastructure:**
- Docker Compose for local development
- WhiteNoise for static files
- Boto3 for S3 storage (production)

**Key Integrations:**
- Stripe 4.2.0 + dj-stripe 2.8.3
- OpenAI >= 1.40.0
- django-allauth 0.61.1
- Tesseract OCR + PyMuPDF

## Access Points

**Local Development URLs:**
| URL | Description |
|-----|-------------|
| http://localhost:8000/ | Homepage |
| http://localhost:8000/dashboard/ | User Dashboard |
| http://localhost:8000/exam-prep/ | C&P Exam Guides |
| http://localhost:8000/exam-prep/glossary/ | VA Glossary |
| http://localhost:8000/exam-prep/rating-calculator/ | **Rating Calculator (NEW)** |
| http://localhost:8000/claims/ | Document Upload |
| http://localhost:8000/appeals/ | Appeals System |
| http://localhost:8000/admin/ | Django Admin |
| http://localhost:5555/ | Flower (Celery Monitor) |

## Key Files Reference

**New Files (This Session - M21 Scraper):**
```
agents/discover_from_toc.py                   # TOC crawler for article discovery
agents/data/m21_article_ids.json              # 459 discovered article IDs
agents/data/toc_discovered_articles.json      # Full discovery results
```

**Modified Files (This Session):**
```
agents/reference_data.py         # Added database-backed M21 functions
agents/services.py               # Updated imports for DB functions
agents/management/commands/scrape_m21.py  # Fixed NULL constraint, duplicate handling
agents/knowva_scraper.py         # Updated KNOWN_ARTICLE_IDS
```

**Previous Session Files (Rating Calculator):**
```
examprep/va_math.py                           # VA Math calculation engine
templates/examprep/rating_calculator.html     # Calculator UI
templates/examprep/saved_calculations.html    # Saved calculations list
```

## Database State

**Migrations:** All applied successfully
**Models:**
- accounts: User, UserProfile, Subscription
- claims: Document, Claim
- examprep: ExamGuidance, GlossaryTerm, ExamChecklist, SavedRatingCalculation
- appeals: Appeal, AppealGuidance, AppealDocument, AppealNote
- agents: M21ManualSection (365 records), M21TopicIndex, M21ScrapeJob

**Fixtures Available:**
- `examprep/fixtures/glossary_terms.json` (26 terms)
- `examprep/fixtures/additional_glossary_terms.json` (20 terms)
- `examprep/fixtures/exam_guides.json` (4 guides)

## Security Headers (Verified Working)

```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com; ...
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
```

## VA Math Accuracy (Verified)

```
Test: 50% + 30% → 65% raw → 70% rounded ✓
Test: 70% + 50% + 30% → 89.5% → 90% ✓
Test: 10% + 10% bilateral → 20.9% → 20% ✓
Test: 70% with spouse → $1,862.28/month ✓
```

## Test Coverage

**188 tests passing** across all apps:
- accounts: 28 tests
- claims: 55 tests
- appeals: 57 tests
- examprep: 49 tests

## Known Issues

None currently. All critical bugs have been resolved (2026-01-11).

## What's Pending

See `TODO.md` for comprehensive task list. Key items:

**High Priority:**
1. Write tests for rating calculator
2. Add more exam guides (TBI, Sleep Apnea)
3. Set up email notifications
4. Accessibility audit

**Medium Priority:**
1. SEO optimization
2. SMC calculator
3. Analytics setup

**Future:**
1. Stripe subscription flow
2. AI chat assistant
3. Mobile optimization

## Session Handoff Notes

### Completed This Session (2026-01-11)

1. **Critical Bug Fixes**
   - Fixed Journey Dashboard model field mismatches (`claim.condition` → `claim.title`)
   - Fixed invalid status values (`decision_received` → `decided`, `processing` → `submitted`)
   - Fixed `cleanup_old_documents` task calling `hard_delete()` on QuerySet
   - Fixed Document.mark_completed() to accept OCR parameters

2. **Security Middleware Enabled**
   - Enabled `AuditMiddleware` for security audit logging
   - Enabled `SecurityHeadersMiddleware` for additional headers
   - Fixed URL path in middleware (`/claims/documents/` → `/claims/document/`)

3. **Soft-Delete Infrastructure**
   - Added `SoftDeleteManager` (default, excludes deleted records)
   - Added `AllObjectsManager` (access all records including deleted)
   - Updated cleanup tasks to use `all_objects`

4. **Data Retention**
   - Created `core/tasks.py` with `enforce_data_retention()` task
   - Added PDF page count validation in file uploads

5. **Test Fixes**
   - Fixed AppealGuidance tests (missing `average_processing_days`)
   - Fixed appeal str representation test
   - Fixed timeline_notes related_name
   - Fixed date calculation tests (age, subscription renewal)
   - All 188 tests now pass

6. **Navigation**
   - Added "My Journey" link for authenticated users

### Completed Previous Session (2026-01-10)
1. **M21-1 Scraper - Complete TOC Discovery**
   - Created `agents/discover_from_toc.py` to crawl TOC and find all article IDs
   - Discovered 459 M21-related articles (vs. initial 29 known)
   - Scraped 365 articles with valid content

2. **Fixed Scraper Issues**
   - Fixed `part_number` NULL constraint for chapter-only articles
   - Fixed duplicate reference handling with IntegrityError fallback
   - Added better error recovery and logging

3. **Updated AI Agent Data Access**
   - Updated `agents/reference_data.py` with database-backed functions
   - Added `get_m21_section_from_db()`, `search_m21_in_db()`, `get_m21_sections_by_part()`
   - Agents now query database first, fall back to JSON files

4. **New Data Files Created**
   - `agents/data/m21_article_ids.json` (459 IDs)
   - `agents/data/toc_discovered_articles.json` (full discovery results)

### For Next Session
1. Test AI agents with new M21 database data
2. Consider building topic indices from scraped content
3. Add TBI and Sleep Apnea exam guides
4. Set up email notifications
5. Plan production deployment

### Gotchas to Remember
- ~95 articles have empty/historical content (expected)
- Some articles have duplicate M21 references (handled gracefully)
- Scraping takes ~45 min for all 459 articles at 1.5s rate limit
- TOC article ID: 554400000073398 (for future discovery runs)

## Quick Start for New Session

```bash
# Start services
cd /Users/zachbeaudoin/benefits-navigator
docker compose up -d

# Verify everything works
curl -I http://localhost:8000/  # Should return 200

# Check logs if issues
docker compose logs -f web

# Access calculator
open http://localhost:8000/exam-prep/rating-calculator/
```
