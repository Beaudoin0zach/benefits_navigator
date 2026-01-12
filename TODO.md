# VA Benefits Navigator - Comprehensive TODO List

**Last Updated:** 2026-01-11
**Updated By:** Claude Code Session

---

## Project Overview

A Django-based web application helping veterans navigate VA disability claims, C&P exams, and appeals. Built with accessibility (WCAG AA) as a core requirement.

---

## Current State Summary

### What's Working
- Docker Compose environment (web, db, redis, celery)
- User authentication (email-based via django-allauth)
- Document upload with OCR and AI analysis
- 7 C&P exam guides (General, PTSD, Musculoskeletal, Hearing, TBI, Sleep Apnea, Mental Health)
- 86 VA glossary terms
- Appeals workflow system
- VA Disability Rating Calculator with accurate VA Math
- **NEW: SMC (Special Monthly Compensation) Calculator**
- **NEW: TDIU Eligibility Calculator**
- **NEW: Secondary Conditions Hub with 40+ condition relationships**
- **NEW: Email notification system (deadline/exam reminders)**
- **NEW: Supportive messaging system**
- User dashboard with journey tracking
- Security hardening (CSP, rate limiting, etc.)

### Tech Stack
- Django 5.0.1 / Python 3.11
- PostgreSQL 15 / Redis 7
- Celery for background tasks
- HTMX + Tailwind CSS frontend
- OpenAI API for document analysis

---

## HIGH PRIORITY (Should Do Next)

### 1. Testing & Quality
- [x] Write unit tests for VA Math calculator (`examprep/va_math.py`) ✅ (2026-01-11) - 80 tests
- [x] Write integration tests for rating calculator views ✅ (2026-01-11) - 45 tests
- [x] Test document upload flow end-to-end ✅ (2026-01-11) - 25 tests
- [x] Run accessibility audit (Lighthouse) ✅ (2026-01-11) - 95-96% on all pages
- [x] Test rate limiting is working correctly ✅ (2026-01-11) - 11 tests
- [x] Verify CSP headers don't break functionality ✅ (2026-01-11) - 25 tests

### 2. Content Additions
- [x] Add TBI (Traumatic Brain Injury) exam guide ✅ (2026-01-11)
- [x] Add Sleep Apnea exam guide ✅ (2026-01-11)
- [x] Add Mental Health (non-PTSD) exam guide ✅ (2026-01-11)
- [x] Add more glossary terms (aim for 75-100 total) ✅ (2026-01-11) - 86 terms
- [x] Add common secondary conditions guide ✅ (2026-01-11)

### 3. User Experience
- [x] Add email notifications for:
  - [x] Document analysis complete ✅ (2026-01-11)
  - [x] Appeal deadline reminders (7 days, 1 day before) ✅ (2026-01-11)
  - [x] C&P exam reminders ✅ (2026-01-11)
- [x] Add PDF export for rating calculations ✅ (2026-01-11)
- [x] Add "share calculation" feature (generate shareable link) ✅ (2026-01-11)

---

## MEDIUM PRIORITY (Nice to Have)

### 4. Rating Calculator Enhancements
- [x] Add SMC (Special Monthly Compensation) calculator ✅ (2026-01-11)
- [x] Add TDIU eligibility checker ✅ (2026-01-11)
- [ ] Historical compensation rates (2020-2024)
- [ ] "Compare scenarios" side-by-side view
- [ ] Import ratings from VA letter (OCR)

### 5. SEO & Marketing
- [ ] Add meta descriptions to all pages
- [ ] Create sitemap.xml
- [ ] Add structured data (JSON-LD) for guides
- [ ] Create robots.txt
- [ ] Add Open Graph tags for social sharing

### 6. Analytics & Monitoring
- [ ] Set up Sentry error tracking (config exists, needs DSN)
- [ ] Add usage analytics (privacy-respecting)
- [ ] Create admin dashboard with stats
- [ ] Monitor Celery task success/failure rates

### 7. Performance
- [ ] Add Redis caching for glossary terms
- [ ] Add Redis caching for exam guides
- [ ] Optimize database queries (add select_related/prefetch_related)
- [ ] Add pagination to document list
- [ ] Lazy load images

---

## LOW PRIORITY (Future Features)

### 8. Premium Features
- [ ] Implement Stripe subscription flow
- [ ] Add premium tier limits enforcement
- [ ] GPT-4 access for premium users
- [ ] Priority support queue
- [ ] Unlimited document storage

### 9. AI Enhancements
- [ ] Chat assistant for claims questions
- [ ] Auto-suggest conditions based on documents
- [ ] Generate personal statements
- [ ] Nexus letter template generator

### 10. Community Features
- [ ] Forum for veterans to share experiences
- [ ] Success stories section
- [ ] VSO directory/finder
- [ ] Buddy statement templates

### 11. Mobile
- [ ] Progressive Web App (PWA) support
- [ ] Mobile-optimized views
- [ ] Push notifications

---

## TECHNICAL DEBT

### Code Quality
- [ ] Add type hints to all Python files
- [ ] Add docstrings to all functions
- [ ] Set up pre-commit hooks (black, ruff)
- [ ] Create API documentation

### Security
- [x] Add Content-Security-Policy headers
- [x] Add rate limiting to auth views
- [x] Fix SECRET_KEY handling for production
- [x] Add file content validation (python-magic)
- [ ] Add CAPTCHA to signup (if spam becomes issue)
- [ ] Implement account lockout after failed logins
- [ ] Add 2FA option

### Infrastructure
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Create staging environment
- [ ] Document production deployment (Railway/Render/AWS)
- [ ] Set up database backups
- [ ] Create disaster recovery plan

---

## KNOWN ISSUES

### Bugs
- None currently identified

### Limitations
- Rating calculator uses 2024 rates (need annual update process)
- Bilateral factor only supports simple bilateral, not complex groupings
- Document OCR may struggle with handwritten text
- OpenAI costs not tracked per-user yet

---

## FILE REFERENCE

### Core Files
```
benefits_navigator/
├── settings.py          # Django configuration
├── urls.py              # Main URL routing
├── celery.py            # Celery configuration
└── wsgi.py              # WSGI entry point

examprep/
├── models.py            # ExamGuidance, GlossaryTerm, ExamChecklist, SavedRatingCalculation
├── views.py             # All exam prep views including rating calculator
├── va_math.py           # VA combined rating calculation logic (NEW)
├── urls.py              # URL routing
├── admin.py             # Admin configuration
└── fixtures/            # Glossary terms, exam guides

claims/
├── models.py            # Document, Claim models
├── views.py             # Document upload/analysis views
├── forms.py             # Upload form with validation
└── tasks.py             # Celery tasks for OCR/AI

appeals/
├── models.py            # Appeal, AppealGuidance, etc.
├── views.py             # Appeals workflow views
└── urls.py              # Appeals URL routing

accounts/
├── models.py            # User, UserProfile, Subscription
├── views.py             # Rate-limited auth views
└── managers.py          # Custom user manager

templates/
├── base.html            # Base template with navigation
├── core/
│   ├── home.html        # Homepage
│   └── dashboard.html   # User dashboard
├── examprep/
│   ├── rating_calculator.html  # Rating calculator (NEW)
│   ├── guide_list.html
│   ├── guide_detail.html
│   ├── glossary_list.html
│   └── partials/
│       └── rating_result.html  # HTMX partial (NEW)
└── claims/
    └── document_*.html  # Document templates
```

### Configuration Files
```
docker-compose.yml       # Docker services
Dockerfile              # Web container
requirements.txt        # Python dependencies
.env                    # Environment variables (not in git)
```

---

## ENVIRONMENT VARIABLES NEEDED

```bash
# Required
SECRET_KEY=your-secure-secret-key
DATABASE_URL=postgres://user:pass@host:5432/dbname
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-your-openai-key

# Optional
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
SENTRY_DSN=https://xxx@sentry.io/xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_SECRET_KEY=sk_live_xxx

# Email (for production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=app-password
```

---

## QUICK COMMANDS

```bash
# Start development
docker compose up -d

# View logs
docker compose logs -f web

# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser

# Load fixtures
docker compose exec web python manage.py loaddata examprep/fixtures/*.json

# Django shell
docker compose exec web python manage.py shell_plus

# Run tests
docker compose exec web pytest

# Rebuild after dependency changes
docker compose build web && docker compose up -d
```

---

## SESSION HANDOFF NOTES

### What Was Done This Session (2026-01-11)
**Tier 2 Features Implemented:**

1. **SMC/TDIU Calculators** (`examprep/va_special_compensation.py`)
   - SMC levels K through S with eligibility checks
   - TDIU schedular vs extraschedular determination
   - 2024 compensation rates
   - HTMX-powered real-time calculations

2. **Secondary Conditions Hub** (`examprep/secondary_conditions_data.py`)
   - 8 primary conditions: PTSD, TBI, Back, Knee, Diabetes, Sleep Apnea, Hypertension, Tinnitus
   - 40+ secondary condition relationships with medical rationale
   - Search and category filtering
   - Evidence tips and nexus letter guidance

3. **New Exam Prep Guides** (fixtures):
   - TBI Guide (`exam_guides_tbi.json`)
   - Sleep Apnea Guide (`exam_guides_sleep_apnea.json`)
   - Mental Health Non-PTSD Guide (`exam_guides_mental_health.json`)

4. **Email Notifications** (`core/tasks.py`)
   - Deadline reminders (7 days, 1 day before)
   - C&P exam reminders
   - Document analysis complete notifications
   - User notification preferences
   - HTML and text email templates

5. **Supportive Messaging** (`core/models.py`, `core/templatetags/`)
   - Rotating veteran-friendly messages by journey stage
   - Template tag integration
   - Admin management

### What Was Done Previously (2026-01-09)
1. Fixed security issues (CSP, rate limiting, SECRET_KEY)
2. Built VA Disability Rating Calculator with:
   - Accurate VA Math (38 CFR § 4.25)
   - Bilateral factor support (38 CFR § 4.26)
   - 2024 compensation rates
   - Save/load calculations
   - Step-by-step explanation
3. Updated homepage with calculator feature card
4. Fixed template URL references (appeals:home)

### Recommended Next Steps
1. Run migrations for new models: `python manage.py migrate`
2. Import new fixtures: `python manage.py import_content --fixtures`
3. Load supportive messages: `python manage.py loaddata core/fixtures/supportive_messages.json`
4. Set up Celery beat for scheduled notification tasks
5. Run test suite to verify nothing broke
6. Plan production deployment

### Things to Watch Out For
- Compensation rates need annual update (usually December)
- SMC rates are separate from standard compensation - verify annually
- Celery workers must be running for email notifications
- CSP may need adjusting if adding new external resources
- Rate limiting is IP-based, may need adjustment for shared IPs

---

## CONTRIBUTING

When working on this project:
1. Always run tests before committing
2. Update this TODO.md when completing tasks
3. Follow existing code patterns
4. Maintain WCAG AA accessibility
5. Document any new environment variables
