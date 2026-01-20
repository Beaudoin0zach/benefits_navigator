# Benefits Navigator — Claude Code Guide

## Project Summary
Django 5.0 app deployed on DigitalOcean App Platform, using OpenAI API (GPT-3.5-turbo default).
Celery + Redis for async document processing. PostgreSQL database. Stripe for subscriptions.

**Two user flows:**
- **Path A:** Veterans (B2C end-user flow) — document upload, AI analysis, denial decoding, statement generation
- **Path B:** VSOs (B2B caseworker/advocate flow) — case management, shared documents, veteran invitations

## Non-negotiables
- Treat all user data as sensitive. Avoid logging PII.
- Never store raw prompts/responses containing PII unless explicitly required and securely handled.
- Assume prompt injection is possible; sanitize/validate any model outputs before using them.
  - All user input goes through `sanitize_user_input()` in `agents/services.py`
- Prefer small, test-backed changes. Avoid broad refactors.
- PII fields (`va_file_number`, `date_of_birth`) use `EncryptedCharField` from `core/encryption.py`

## How to work (required workflow)
1. Find the exact entry points for Path A and Path B (routes/views/templates).
2. Identify the boundary contract(s) between the paths and any shared modules.
3. Use the existing `BaseAgent` class in `agents/services.py` for all OpenAI calls.
4. Before changing logic, add tests:
   - path-level tests (URLs/views)
   - unit tests for eligibility/routing logic
   - tests for OpenAI wrapper parsing/validation (mock model output)
5. After changes: run `pytest` and lint.

## Output requirements for every task
- What changed and why
- Files modified
- Tests run and results
- Remaining risks / TODOs

---

# Architecture (current)

## Path A (Veterans)

### Entry Points
| Route | View | File |
|-------|------|------|
| `/` | `home()` | `core/views.py` |
| `/dashboard/` | `dashboard()` | `core/views.py` |
| `/journey/` | `journey_dashboard()` | `core/views.py` |
| `/claims/upload/` | `document_upload()` | `claims/views.py` |
| `/claims/` | `document_list()` | `claims/views.py` |
| `/claims/document/<pk>/` | `document_detail()` | `claims/views.py` |
| `/agents/decision-analyzer/` | `decision_analyzer()` | `agents/views.py` |
| `/agents/evidence-gap/` | `evidence_gap_analyzer()` | `agents/views.py` |
| `/agents/statement-generator/` | `statement_generator()` | `agents/views.py` |

### Data Flow
1. **Document Upload:** User uploads → `Document` model created → Celery task `process_document_task()` queued
2. **Processing Pipeline:** OCR (Tesseract) → AI Analysis (OpenAI) → Results stored in `Document.ai_summary`
3. **Agent Tools:** User input → `BaseAgent._call_openai()` → Parsed JSON response → stored in agent-specific models

### Models Used
- `claims/models.py`: `Document`, `Claim`
- `agents/models.py`: `AgentInteraction`, `DecisionLetterAnalysis`, `EvidenceGapAnalysis`, `PersonalStatement`, `RatingAnalysis`
- `core/models.py`: `JourneyStage`, `UserJourneyEvent`, `Milestone`
- `accounts/models.py`: `UsageTracking`, `Subscription`

### OpenAI Usage
- `agents/services.py`: `DecisionLetterAnalyzer`, `DenialDecoderService`, `EvidenceGapAnalyzer`, `PersonalStatementGenerator`
- `claims/services/ai_service.py`: Document analysis
- All calls go through `BaseAgent._call_openai()` which tracks tokens and costs

### Outputs (what the user gets)
- OCR text extraction with confidence scores
- AI-generated document summaries (JSON in `Document.ai_summary`)
- Decision letter analysis: conditions granted/denied, appeal options, deadlines
- Evidence gap analysis: missing evidence, readiness score (0-100), recommendations
- Personal statement drafts for VA claims

---

## Path B (VSOs)

### Entry Points
| Route | View | File |
|-------|------|------|
| `/vso/` | `dashboard()` | `vso/views.py` |
| `/vso/cases/` | `case_list()` | `vso/views.py` |
| `/vso/cases/new/` | `case_create()` | `vso/views.py` |
| `/vso/cases/<pk>/` | `case_detail()` | `vso/views.py` |
| `/vso/cases/<pk>/notes/add/` | `add_case_note()` | `vso/views.py` |
| `/vso/invitations/` | `invitations_list()` | `vso/views.py` |
| `/vso/invitations/new/` | `invite_veteran()` | `vso/views.py` |
| `/vso/invite/<token>/` | `accept_invitation()` | `vso/views.py` |

### Data Flow
1. **Case Creation:** VSO creates case → links to veteran user → assigns caseworker
2. **Document Sharing:** Veteran shares document → `SharedDocument` created → VSO reviews
3. **Analysis Sharing:** Veteran shares AI analysis → `SharedAnalysis` created → VSO adds notes

### Models Used
- `vso/models.py`: `VeteranCase`, `CaseNote`, `SharedDocument`, `SharedAnalysis`
- `accounts/models.py`: `Organization`, `OrganizationMembership`, `OrganizationInvitation`

### OpenAI Usage
- VSOs view shared AI analyses (read-only access to veteran's `DecisionLetterAnalysis`, `RatingAnalysis`, etc.)
- No direct OpenAI calls from VSO views

### Outputs
- Case dashboard with status metrics, priority cases, win rates
- Case detail with veteran info, conditions, shared documents, notes, deadlines
- Case notes with action items and due dates

---

## Shared Modules / Boundary Contracts

### Shared Functions/Classes
| Module | Purpose |
|--------|---------|
| `core/models.py` | `TimeStampedModel`, `SoftDeleteModel` base classes |
| `core/encryption.py` | `EncryptedCharField`, `EncryptedDateField` for PII |
| `core/middleware.py` | `AuditMiddleware` (logs sensitive operations), `SecurityHeadersMiddleware` |
| `core/context_processors.py` | `user_usage()`, `feature_flags()`, `vso_access()` |
| `agents/services.py` | `BaseAgent` class — all OpenAI calls centralized here |
| `agents/m21_matcher.py` | M21 manual section matching for denial analysis |

### Request/Response Schemas
- **OpenAI calls:** All return `tuple[str, int]` (response_text, token_count)
- **Agent outputs:** Parsed to JSON, stored in model-specific fields
- **Document processing:** Status progression: `uploading` → `processing` → `analyzing` → `completed`/`failed`

### Where Parsing/Validation Occurs
- `agents/services.py`: JSON parsing of OpenAI responses, `sanitize_user_input()` for prompt injection protection
- `claims/tasks.py`: Document status updates, error handling
- `vso/views.py`: Permission checks for organization membership

### Feature Flags (in `settings.py`)
```python
FEATURES = {
    'organizations': env.bool('FEATURE_ORGANIZATIONS', default=False),
    'org_roles': env.bool('FEATURE_ORG_ROLES', default=False),
    'org_invitations': env.bool('FEATURE_ORG_INVITATIONS', default=False),
    'caseworker_assignment': env.bool('FEATURE_CASEWORKER_ASSIGNMENT', default=False),
    'org_billing': env.bool('FEATURE_ORG_BILLING', default=False),
    'org_admin_dashboard': env.bool('FEATURE_ORG_ADMIN', default=False),
}
```

---

# Development

## Running Tests
```bash
pytest                    # All tests
pytest -m "not slow"      # Skip slow tests
pytest -m agent           # Agent tests only
pytest core/              # Specific app
pytest --cov=.            # With coverage
pytest -n auto            # Parallel execution
```

## Test Markers
- `slow` — Long-running tests
- `e2e` — End-to-end tests
- `bdd` — Behavior-driven tests
- `agent` — AI agent tests
- `integration` — Integration tests
- `unit` — Unit tests

## Key Fixtures (`conftest.py`)
- `user` — Standard test user
- `premium_user` — User with active premium subscription
- `authenticated_client` — Logged-in client
- `premium_client` — Premium logged-in client

---

# Deployment (DigitalOcean)

## Services (`.do/app.yaml`)
1. **Web:** Gunicorn Django (basic-xxs, port 8000)
2. **Worker:** Celery (basic-xxs, concurrency=2)
3. **Pre-deploy job:** `python manage.py migrate --noinput`

## Required Environment Variables
```
SECRET_KEY
DATABASE_URL              # postgresql://...?sslmode=require
REDIS_URL                 # rediss://... (SSL)
CELERY_BROKER_URL         # Same as REDIS_URL
FIELD_ENCRYPTION_KEY      # Fernet key for PII encryption
OPENAI_API_KEY
SENTRY_DSN
ALLOWED_HOSTS
```

## Health Check
- `/health/` — Liveness check
- `/health/?full=1` — Full status (database, cache, etc.)

---

# Key Files Reference

| Category | File | Purpose |
|----------|------|---------|
| Config | `benefits_navigator/settings.py` | All Django config, feature flags, OpenAI setup |
| Config | `.do/app.yaml` | DigitalOcean deployment |
| Models | `core/models.py` | Base models, journey, audit |
| Models | `accounts/models.py` | User, subscription, organization |
| Models | `claims/models.py` | Document, Claim |
| Models | `agents/models.py` | AI interactions, M21 manual |
| Models | `vso/models.py` | Case, CaseNote, SharedDocument |
| Views | `core/views.py` | Home, dashboard, journey |
| Views | `claims/views.py` | Document upload/download |
| Views | `agents/views.py` | AI agent interfaces |
| Views | `vso/views.py` | VSO case management |
| Services | `agents/services.py` | **BaseAgent**, all AI agents |
| Services | `claims/services/ai_service.py` | Document analysis |
| Services | `claims/services/ocr_service.py` | Tesseract OCR |
| Tasks | `claims/tasks.py` | Document processing pipeline |
| Tasks | `core/tasks.py` | Maintenance, reminders |
| Security | `core/encryption.py` | Field-level encryption |
| Security | `core/middleware.py` | Audit logging, security headers |
