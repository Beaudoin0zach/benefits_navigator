# Security Invariants

This document defines security invariants that must be maintained across all code changes.

## Enforcement Locations

| Invariant | Tests | Static Analysis | CI Workflow |
|-----------|-------|-----------------|-------------|
| No PHI in OCR fields | `tests/test_regression_tripwires.py` | `scripts/check_security_invariants.py` | `security-checks.yml` |
| OCR metadata fields exist | `tests/test_regression_tripwires.py` | — | — |
| Sentry PII protection | — | `scripts/check_security_invariants.py` | `security-checks.yml` |
| No PII in logs | — | `scripts/check_security_invariants.py` | `security-checks.yml` |
| Route integrity | `tests/test_regression_tripwires.py` | — | — |
| Dependency vulnerabilities | — | — | `security-checks.yml` (pip-audit) |

---

## PHI/PII Protection

### 1. No PHI Stored in OCR Fields

**Invariant:** Raw OCR text must never be persisted to the database.

| Model | Prohibited Fields | Required Metadata Fields |
|-------|-------------------|-------------------------|
| `claims.Document` | `ocr_text` | `ocr_length`, `ocr_status` |
| `agents.DecisionLetterAnalysis` | `raw_text` | — |
| `agents.RatingAnalysis` | `raw_text` | — |

**Rationale:** OCR text contains Protected Health Information (PHI). The Ephemeral OCR
Refactor removed these fields. Text is now extracted in-memory during processing
and discarded after AI analysis.

**Enforcement:**
- **Tripwire tests:** `tests/test_regression_tripwires.py::TestPHIFieldRemovalInvariants` uses Django model `_meta` to verify DB fields don't exist
- **Static analysis:** `scripts/check_security_invariants.py` scans model files for prohibited field definitions

### 2. AI Outputs Must Be Schema-Validated

**Invariant:** All AI/LLM responses must be validated via Pydantic schemas before persistence.

**Implementation:**
- Use `agents/ai_gateway.py` → `gateway.complete_structured()` for validated responses
- Schemas defined in `agents/schemas.py`
- Returns `Result[StructuredResponse[T]]` — check `result.is_success` before use

**Enforcement:** Manual review required; no automated check currently.

### 3. No PII in Logs

**Invariant:** Logs must not contain PII (names, SSNs, file numbers, medical info).

**Prohibited patterns:**

| Pattern Type | Examples | Severity |
|--------------|----------|----------|
| Request body logging | `logger.info(...request.body...)` | Warning |
| PHI field access in logs | `logger.info(...document.ocr_text...)` | Error |
| PII dict access in logs | `logger.info(...data["ssn"]...)` | Error |

**Enforcement:** `scripts/check_security_invariants.py` scans for:
- Logging calls containing `request.body`, `request.POST`, `request.data`
- Logging calls with PHI field attribute access (`.ocr_text`, `.ssn`, etc.)
- Logging calls with PHI dict key access (`["ssn"]`, `.get("ssn")`)

### 4. Sentry PII Protection

**Invariant:** Sentry must not send default PII in production.

```python
# settings.py - REQUIRED configuration
sentry_sdk.init(
    send_default_pii=False,  # MUST be False
    # ...
)
```

**Enforcement:** `scripts/check_security_invariants.py` scans all settings files for `send_default_pii=True`.

---

## Rate Limiting

### 5. Auth Endpoints Rate Limited

**Invariant:** Authentication endpoints must have rate limits to prevent brute force attacks.

| Endpoint | Rate | Key |
|----------|------|-----|
| Login | 5/min + 20/hr | IP |
| Signup | 3/hr | IP |
| Password Reset | 3/hr | IP |

**Implementation:** `@ratelimit` decorator from `django_ratelimit`.

### 6. AI Endpoints Rate Limited

**Invariant:** AI agent endpoints must have rate limits to prevent abuse.

| Endpoint | Rate | Key |
|----------|------|-----|
| Document Upload | 10/min | user |
| AI Agent Submit | 20/hr | user |
| Status Polling | 60/min | user |

---

## Data Encryption

### 7. PII Fields Encrypted at Rest

**Invariant:** PII fields must use `EncryptedCharField` or `EncryptedDateField`.

| Model | Encrypted Fields |
|-------|-----------------|
| `accounts.UserProfile` | `va_file_number`, `date_of_birth` |

**Implementation:** `core/encryption.py` provides encrypted field types.

---

## Access Control

### 8. Document Access Scoped to Owner

**Invariant:** Users can only access their own documents.

**Implementation:**
- All document queries filter by `user=request.user`
- Signed URLs include user_id validation
- VSO access requires explicit sharing via `SharedDocument`

### 9. VSO Access Requires Organization Membership

**Invariant:** VSO features require valid organization membership.

**Implementation:**
- `@vso_required` decorator checks membership
- Multi-org users must select active organization
- Cases scoped to organization

---

## Route Integrity

### 10. Critical Routes Must Exist

**Invariant:** Named URL patterns and critical paths must resolve correctly.

**Enforcement:** `tests/test_regression_tripwires.py::TestURLResolutionIntegrity` verifies:
- Named URLs resolve without `NoReverseMatch`
- Critical paths resolve to view functions

### 11. Protected Routes Must Require Authentication

**Invariant:** Auth-protected routes must redirect to login with `next=` parameter.

**Enforcement:** `tests/test_regression_tripwires.py::TestRouteHTTPBehavior` verifies:
- Protected routes return 302 redirect
- Redirect URL contains `/login/` or `/accounts/login/`
- Redirect URL includes `next=` parameter

---

## Running Checks Locally

### Security Invariants Script

```bash
# Run all checks
python scripts/check_security_invariants.py

# Verbose output (shows files scanned)
python scripts/check_security_invariants.py --verbose
```

### Regression Tripwire Tests

```bash
# Run tripwire tests only (fast, ~5s)
pytest tests/test_regression_tripwires.py -v

# Run with timing
pytest tests/test_regression_tripwires.py -v --durations=5
```

### Full Security Suite

```bash
# Run all security-related checks
python scripts/check_security_invariants.py && \
pytest tests/test_regression_tripwires.py -v
```

---

## CI Workflows

### security-checks.yml

Runs on push/PR to main and weekly:
- **security-invariants:** Runs `scripts/check_security_invariants.py`
- **dependency-scan:** Runs `pip-audit` for vulnerability scanning
- **bandit:** Runs Bandit SAST (non-blocking)

### benchmarks.yml

Runs on push/PR to main:
- Runs performance benchmark tests
- Uploads results as artifacts for visibility

---

## Adding New Invariants

1. Document the invariant in this file
2. Add automated check to appropriate location:
   - **Database/model invariants:** Add test to `tests/test_regression_tripwires.py`
   - **Code pattern detection:** Add check to `scripts/check_security_invariants.py`
   - **Runtime behavior:** Add integration test
3. Update CI workflow if needed
4. Consider if the check should be blocking (error) or advisory (warning)
