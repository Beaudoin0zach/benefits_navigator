# Changelog

All notable changes to VA Benefits Navigator are documented here.

## [Unreleased]

### Planned
- TBI exam guide
- Sleep Apnea exam guide
- Email notifications
- PDF export for calculations
- SMC calculator

---

## [2026-01-11] - Critical Bug Fixes & Test Improvements

### Fixed
- **Critical: Journey Dashboard Model Mismatches**
  - Fixed `claim.condition` → `claim.title` (field didn't exist)
  - Fixed invalid status values (`decision_received` → `decided`, `processing` → `submitted`)
  - Removed references to non-existent `rating_percentage` field
  - Fixed Appeal model field references (`appeal.condition` → `appeal.conditions_appealed`)
  - Fixed invalid Appeal status queries

- **Critical: Document Cleanup Task Crash**
  - Fixed `cleanup_old_documents` task calling `hard_delete()` on QuerySet
  - Now properly iterates over documents and calls instance method
  - Added file storage cleanup before database deletion

- **Middleware Not Enabled**
  - Enabled `AuditMiddleware` for security audit logging
  - Enabled `SecurityHeadersMiddleware` for additional security headers
  - Fixed URL path pattern (`/claims/documents/` → `/claims/document/`)

- **Journey Features Inaccessible**
  - Added "My Journey" navigation link for authenticated users
  - Journey dashboard now accessible from main navigation

- **File Validation Improvements**
  - Added logging when python-magic is not installed
  - Added PDF page count validation (max 100 pages by default)
  - Improved error handling in file validation

- **ExamChecklist.is_upcoming Property**
  - Now returns `False` when exam is marked as completed

- **get_upcoming_deadlines Query**
  - Fixed to filter out past deadlines (was returning all deadlines)

### Added
- **SoftDeleteManager** - Default manager now excludes soft-deleted records
- **AllObjectsManager** - Access all records including soft-deleted via `Model.all_objects`
- **Data Retention Task** (`core/tasks.py`)
  - `enforce_data_retention()` - Enforces retention policies for audit logs, documents, analyses
  - `create_default_retention_policies()` - Creates default retention policy records
- **Document.mark_completed()** - Now accepts OCR parameters (`ocr_text`, `ocr_confidence`, `page_count`)

### Tests
- Added comprehensive tests for `cleanup_old_documents` task
- Added tests for `decode_denial_letter_task`
- Fixed `AppealGuidance` tests missing required `average_processing_days` field
- Fixed `test_appeal_str_representation` to check display name
- Fixed `test_complete_hlr_workflow` to use correct `timeline_notes` related_name
- Fixed accounts date calculation tests (age, subscription renewal)
- Fixed examprep guidance str representation test
- **All 188 tests now pass**

---

## [2026-01-09] - Rating Calculator & Security

### Added
- **VA Disability Rating Calculator** (`examprep/va_math.py`)
  - Accurate VA Math formula per 38 CFR § 4.25
  - Bilateral factor calculation per 38 CFR § 4.26
  - 2024 compensation rates with dependent calculations
  - Step-by-step calculation explanation
  - Save/load calculations for logged-in users
  - Interactive UI with real-time updates via HTMX

- **Security Hardening**
  - Content-Security-Policy headers via django-csp
  - Rate limiting on authentication views (login: 5/min, signup: 3/hr)
  - SECRET_KEY enforcement in production mode
  - Magic byte file validation in document uploads

- **User Dashboard** (`core/views.py`, `templates/core/dashboard.html`)
  - Overview of documents, checklists, appeals
  - Quick action links
  - Stats and alerts section

- **Additional Glossary Terms**
  - Added 20 new terms (TDIU, SMC, P&T, DIC, etc.)
  - Total glossary now has 46 terms

- **Documentation**
  - Created comprehensive `TODO.md`
  - Updated `START_HERE.md`
  - Updated `docs/PROJECT_STATUS.md`
  - Created `CHANGELOG.md`

### Changed
- Homepage updated with rating calculator feature card
- Homepage grid changed to 4-column layout
- Trust signals updated (46 terms, VA Math badge)
- Fixed URL references (appeals:appeals_home → appeals:home)

### Fixed
- Template NoReverseMatch errors for appeals URLs
- OpenAI client proxy argument error (updated to openai>=1.40.0)
- Appeals migration table missing issue

### Security
- Added `django-csp==3.8` to requirements
- Added CSP middleware to settings
- Configured secure cookies for production
- Added rate-limited auth view classes

---

## [2026-01-09] - Morning Session

### Added
- Enhanced homepage with value proposition
- 4 C&P exam guides loaded from fixtures
- 26 initial glossary terms

### Fixed
- Docker compose configuration
- Database fixture loading errors
- OpenAI API integration

---

## [2026-01-08] - Phase 3 Foundation

### Added
- ExamGuidance model with 8 content sections
- GlossaryTerm model with plain language definitions
- ExamChecklist model for user preparation tracking
- Full admin configuration
- 10 views for exam prep functionality
- HTMX-powered interactive checklists

---

## [2026-01-07] - Phase 2 Completion

### Added
- Document upload system
- OCR processing with Tesseract
- AI-powered document analysis
- Celery background task processing
- Claims tracking system

---

## [2026-01-06] - Phase 1 Foundation

### Added
- Django 5.0.1 project structure
- PostgreSQL 15 database
- Redis 7 for caching
- Docker Compose environment
- Custom User model with email auth
- User profiles with veteran fields
- Stripe integration preparation

---

## Version History

| Date | Version | Summary |
|------|---------|---------|
| 2026-01-09 | 0.4.0 | Rating calculator, security hardening |
| 2026-01-09 | 0.3.1 | Homepage, exam content |
| 2026-01-08 | 0.3.0 | Phase 3 exam prep foundation |
| 2026-01-07 | 0.2.0 | Phase 2 document analysis |
| 2026-01-06 | 0.1.0 | Phase 1 foundation |
