# VA Benefits Navigator — TODO & Audit Tracker

**Last Updated:** 2026-02-11
**Updated By:** Claude Code P0 Fix Session

---

## Audit Summary (2026-02-09)

Full audit performed across 7 areas. See `docs/AUDIT_2026_02_09.md` for complete findings.

| Area | Status | Critical | Needs Work |
|------|--------|----------|------------|
| Security | CRITICAL | 4 | 3 |
| Data Integrity | CRITICAL | 2 | 1 |
| Test Coverage | NEEDS WORK | 0 | 4 |
| Production Readiness | NEEDS WORK | 1 | 2 |
| Accessibility (WCAG AA) | NEEDS WORK | 3 | 4 |
| Code Quality & Deployment | CRITICAL | 2 | 5 |
| **Totals** | | **12** | **19** |

**Production-Readiness Score: 7.0 / 10** (was 5.5 before P0 fixes on 2026-02-11)

---

## P0 — CRITICAL (Fix Before Veterans Use This)

All P0 code fixes completed 2026-02-11. Manual credential rotation still required.

### Security: Secrets Exposure
- [x] **Add deployment configs to .gitignore** — `.env.docker`, `app-spec-fixed.yaml`, `.do/app.yaml`, `docker-compose.yml` (2026-02-11)
- [x] **Create deployment config templates** — `app-spec.yaml.template` and `docker-compose.yml.template` with `CHANGE_ME` placeholders (2026-02-11)
- [ ] **Revoke all exposed credentials** — SECRET_KEY, FIELD_ENCRYPTION_KEY, DATABASE_URL, REDIS_URL, OpenAI key, Sentry DSN
  - Action: Rotate every key in DO Console + service dashboards, re-encrypt PII with new FIELD_ENCRYPTION_KEY
- [ ] **Scrub git history** — Use `git-filter-repo` or BFG to remove all commits containing secrets

### Data Integrity: Regulatory Accuracy
- [x] **Add 2025 & 2026 VA compensation rates** — `examprep/va_math.py` (2026-02-11)
  - 2025: 2.5% COLA (verified against va.gov), 2026: 2.8% COLA
  - Base rates, dependent rates (2024-2026), SMC rates all updated
  - `AVAILABLE_RATE_YEARS` updated to [2026..2020], default year = 2026
  - Year-aware dependent rate lookup via `DEPENDENT_RATES_BY_YEAR`
  - SMC rates updated in `examprep/va_special_compensation.py` with `SMC_RATES_BY_YEAR`
- [x] **Fix supplemental claim deadline** — `appeals/models.py:293-301` (2026-02-11)
  - `save()` now checks `appeal_type == 'supplemental'` → sets `deadline = None`
  - HLR and Board appeals still get 1-year auto-deadline
  - Tests added: `test_supplemental_no_deadline`, `test_supplemental_clears_existing_deadline`

### Production Readiness: Crash Safety
- [x] **Add `acks_late=True` to Celery tasks** — `claims/tasks.py`, `core/tasks.py` (2026-02-11)
  - All 3 claims tasks and 6 core user-data tasks now have `acks_late=True`

### Code Quality: CI Pipeline
- [x] **Add pytest job to GitHub Actions** — `.github/workflows/tests.yml` (2026-02-11)
  - Runs `pytest --cov=. --cov-report=xml -x -q` on push/PR to main
  - PostgreSQL 15 service, pip caching, coverage artifact upload

---

## P1 — HIGH PRIORITY (Fix Within 1 Week)

### Security
- [ ] **Fix VSO IDOR risk** — `vso/views.py`
  - Add `organization=org` filter to all `get_object_or_404` calls
  - Multi-org users can switch via session without per-request re-verification
  - Add security tests for cross-organization access attempts
- [ ] **Encrypt `ai_summary` field** — `claims/models.py:105`
  - AI analysis results stored as plaintext JSON; may contain extracted PII
  - Add `EncryptedJSONField` or redact PII patterns before storage
- [ ] **Resolve conflicting deployment configs**
  - Both `.do/app.yaml` and `app-spec-fixed.yaml` exist for same environment
  - Delete the deprecated one, document which is canonical

### Database
- [ ] **Add indexes to agent models** — `agents/models.py`
  - `AgentInteraction`, `DecisionLetterAnalysis`, `EvidenceGapAnalysis` lack composite indexes
  - Add: `[user, created_at]`, `[user, agent_type]`

### Testing
- [ ] **Add Celery task tests** — `core/tasks.py` has 6 tasks with zero test coverage
  - `enforce_data_retention`, `enforce_pilot_data_retention`, `notify_pilot_users_before_retention`
  - `cleanup_old_health_metrics`, `check_processing_health`
- [ ] **Add TDIU/SMC boundary tests** — `examprep/tests.py`
  - Test 59% vs 60% (single), 69%+40% vs 70%+40% (combined)
  - Test extraschedular edge cases
  - Currently only 1 TDIU test and 1 SMC test exist
- [x] **Add supplemental claim deadline test** — `appeals/tests.py` (2026-02-11)

### Accessibility (WCAG AA Critical)
- [ ] **Fix rating calculator form labels** — `templates/examprep/rating_calculator.html:59-62`
  - Spouse checkbox label not associated; screen readers won't announce it
  - Fix: `<label for="has-spouse" ...>`
- [ ] **Fix feedback widget keyboard access** — `templates/core/partials/feedback_widget.html:8-9`
  - Uses `<div onclick>` instead of `<button>` — unreachable by keyboard
- [ ] **Add aria-live to HTMX updates** — `templates/appeals/partials/checklist.html:1`
  - Checklist updates not announced to screen readers
  - Add `aria-live="polite"` to target containers
- [ ] **Add accessible loading states** — `templates/examprep/rating_calculator.html:577`
  - Loading spinners need `role="status"` and `<span class="sr-only">` labels

---

## P2 — MEDIUM PRIORITY (Fix Before Scaling)

### Security & Infrastructure
- [ ] **Build Tailwind to static CSS** — Remove `unsafe-inline` from CSP and CDN SPOF
  - Settings.py:396 has TODO comment about this
  - Use PostCSS/Tailwind CLI to generate minified CSS
  - Include fallback styles for error pages (500.html depends on CDN)
- [ ] **Upgrade web instance sizing** — `basic-xxs` (512MB) at 80-95% utilization
  - Upgrade web service to `basic-xs` (1GB) in deployment config
- [ ] **Fix hardcoded domain fallbacks**
  - `core/tasks.py:362,411,535`: `SITE_URL` falls back to `benefitsnavigator.com` (should be `vabenefitsnavigator.org`)
  - `settings.py:694`: `SUPPORT_EMAIL` hardcoded, make configurable via env var
- [ ] **Consolidate Docker Compose config** — Hardcoded credentials repeated in 4 services
  - Move all secrets to `.env.docker`, use `env_file` only

### Code Quality
- [ ] **Fix bare exception handlers** — 21 instances of `except Exception:` across views
  - `core/views.py`, `agents/views.py`, `claims/views.py`
  - Replace with specific exception types
- [ ] **Standardize import style** — Mixed relative/absolute imports across apps
- [ ] **Add code linting to CI** — black, ruff, isort checks

### Accessibility (WCAG AA Improvements)
- [ ] **Add `aria-required="true"` to required form fields** — All form templates
- [ ] **Add `aria-describedby` for form errors** — Link errors to inputs
- [ ] **Add focus management after HTMX swaps** — Appeals checklist, calculator
- [ ] **Add Escape key handler to feedback widget**

### Performance
- [ ] Add Redis caching for glossary terms
- [ ] Add Redis caching for exam guides
- [ ] Optimize database queries (select_related/prefetch_related in remaining views)
- [ ] Lazy load images in templates

### Content Accuracy
- [ ] **Refine sleep apnea guide language** — `examprep/fixtures/exam_guides_sleep_apnea.json`
  - Change "should receive at least 50%" to "may qualify for 50% if documented CPAP compliance"
- [ ] **Create annual rate update process**
  - Management command or Celery Beat task for Dec 1 annual COLA updates
  - Include SMC and dependent rates

### Monitoring
- [ ] Add usage analytics (privacy-respecting)
- [ ] Create admin dashboard with stats
- [ ] Add daily alert for documents stuck in 'failed' status >24 hours

---

## LOW PRIORITY (Future Features)

### Premium Features
- [ ] Implement Stripe subscription flow
- [ ] Add premium tier limits enforcement
- [ ] GPT-4 access for premium users

### AI Enhancements
- [ ] Chat assistant for claims questions
- [ ] Auto-suggest conditions based on documents
- [ ] Generate personal statements
- [ ] Nexus letter template generator

### Community Features
- [ ] Forum for veterans to share experiences
- [ ] Success stories section
- [ ] VSO directory/finder
- [ ] Buddy statement templates

### Mobile
- [ ] Progressive Web App (PWA) support
- [ ] Mobile-optimized views
- [ ] Push notifications

---

## TECHNICAL DEBT

### Code Quality
- [ ] Add type hints to all Python files
- [ ] Set up pre-commit hooks (black, ruff)
- [ ] Create REST API documentation

### Security
- [ ] Add CAPTCHA to signup (if spam becomes issue)
- [ ] Implement account lockout after failed logins
- [ ] Object storage migration (S3/DO Spaces) for secure file serving
- [ ] Additional VSO invitation verification (beyond email matching)

### Infrastructure
- [ ] Set up database backups
- [ ] Create disaster recovery plan
- [ ] Load test document processing pipeline

---

## COMPLETED

### Pilot/Test User Readiness ✅
- [x] Define and script pilot funnels (2026-01-12)
- [x] Stand up staging environment on DO App Platform (2026-01-12)
- [x] Enable Sentry DSN (2026-01-12)
- [x] Add in-app feedback widget (2026-01-12)
- [x] Provide visible support channel (2026-01-12)
- [x] Disable real billing, gate premium features, 30-day data retention (2026-02-09)
- [x] Add health checks/alerts for Celery and document processing (2026-01-12)

### Testing & Quality ✅
- [x] VA Math calculator unit tests — 80 tests (2026-01-11)
- [x] Rating calculator integration tests — 45 tests (2026-01-11)
- [x] Document upload E2E tests — 25 tests (2026-01-11)
- [x] Lighthouse accessibility audit — 95-96% (2026-01-11)
- [x] Rate limiting tests — 11 tests (2026-01-11)
- [x] CSP header tests — 25 tests (2026-01-11)

### Content ✅
- [x] 7 C&P exam guides: General, PTSD, Musculoskeletal, Hearing, TBI, Sleep Apnea, Mental Health
- [x] 86 VA glossary terms (2026-01-11)
- [x] Secondary conditions hub — 40+ relationships (2026-01-11)
- [x] M21 manual content — comprehensive, updated Jan 2026

### Features ✅
- [x] SMC calculator (2026-01-11)
- [x] TDIU eligibility checker (2026-01-11)
- [x] Historical compensation rates 2020-2026 (2026-02-11, was 2020-2024)
- [x] Compare scenarios side-by-side (2026-02-05)
- [x] Import ratings from VA letter OCR (2026-02-09)
- [x] Email notifications — deadlines, exams, analysis complete (2026-01-11)
- [x] PDF export for rating calculations (2026-01-11)
- [x] Supportive messaging system (2026-01-11)

### SEO & Marketing ✅
- [x] Meta descriptions, sitemap.xml, robots.txt, JSON-LD, Open Graph (2026-01-12)

### Security Hardening ✅
- [x] Content-Security-Policy headers (2026-01-09)
- [x] Rate limiting on all public endpoints (2026-01-09)
- [x] File content validation with python-magic (2026-01-09)
- [x] Field-level PII encryption (EncryptedCharField) (2026-01-09)
- [x] Signed URLs for media access (2026-01-12)
- [x] GraphQL PII redaction (2026-01-12)
- [x] Audit logging middleware (2026-01-12)

### P0 Fixes (2026-02-11) ✅
- [x] Deployment configs added to .gitignore, templates created with CHANGE_ME placeholders
- [x] 2025/2026 VA compensation rates added (base, dependent, SMC) — verified against va.gov
- [x] Supplemental claim deadline bug fixed (38 CFR § 20.204) with tests
- [x] `acks_late=True` added to all Celery tasks handling user data
- [x] pytest CI workflow added (`.github/workflows/tests.yml`)
- [x] Supplemental claim deadline tests added to `appeals/tests.py`

### Infrastructure ✅
- [x] Staging environment on DigitalOcean (2026-01-12)
- [x] Switch to DO Managed Valkey (2026-02-05)
- [x] CELERY_RESULT_EXPIRES auto-cleanup (2026-02-05)
- [x] Celery Beat monitoring tasks scheduled (2026-02-09)

---

## KNOWN LIMITATIONS

- Rating calculator supports 2020-2026 rates (current as of Feb 2026)
- Dependent rate additions available for 2024-2026
- Bilateral factor only supports simple bilateral, not complex multi-limb groupings
- Document OCR may struggle with handwritten text
- OpenAI costs not tracked per-user
- Not HIPAA compliant — educational use only
- Pilot mode with 30-day data retention

---

## CONTRIBUTING

When working on this project:
1. Always run `pytest` before committing
2. Update this TODO.md when completing tasks
3. Follow existing code patterns (see CLAUDE.md)
4. Maintain WCAG AA accessibility
5. All OpenAI calls must go through AI Gateway (`agents/ai_gateway.py`)
6. PII fields must use `EncryptedCharField` from `core/encryption.py`
7. Never commit secrets — use environment variables only
8. Add `acks_late=True` to any new Celery tasks handling user data
