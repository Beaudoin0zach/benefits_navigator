# Security Invariants

This document defines security invariants that must be maintained across all code changes.
These are enforced by CI checks in `.github/workflows/security-checks.yml`.

## PHI/PII Protection

### 1. No PHI Stored in OCR Fields

**Invariant:** Raw OCR text must never be persisted to the database.

| Model | Prohibited Fields | Required Metadata Fields |
|-------|-------------------|-------------------------|
| `claims.Document` | `ocr_text` | `ocr_length`, `ocr_status` |
| `agents.DecisionLetterAnalysis` | `raw_text` | — |
| `agents.RatingAnalysis` | `raw_text` | — |

**Rationale:** OCR text contains Protected Health Information (PHI). The Ephemeral OCR
Refactor (PR 6) removed these fields. Text is now extracted in-memory during processing
and discarded after AI analysis.

**CI Check:** `scripts/check_security_invariants.py` scans for prohibited field names.

### 2. AI Outputs Must Be Schema-Validated

**Invariant:** All AI/LLM responses must be validated via Pydantic schemas before persistence.

**Implementation:**
- Use `agents/ai_gateway.py` → `gateway.complete_structured()` for validated responses
- Schemas defined in `agents/schemas.py`
- Returns `Result[StructuredResponse[T]]` — check `result.is_success` before use

**CI Check:** Manual review required; no automated check currently.

### 3. No PII in Logs

**Invariant:** Logs must not contain PII (names, SSNs, file numbers, medical info).

**Prohibited patterns in logging statements:**
- `request.body`, `request.POST`, `request.data`
- `ocr_text`, `raw_text`, `document_text`
- `prompt`, `completion`, `response.choices`
- `ssn`, `file_number`, `date_of_birth`

**CI Check:** `scripts/check_security_invariants.py` scans for logging pitfalls.

### 4. Sentry PII Protection

**Invariant:** Sentry must not send default PII in production.

```python
# settings.py - REQUIRED configuration
sentry_sdk.init(
    send_default_pii=False,  # MUST be False
    # ...
)
```

**CI Check:** `scripts/check_security_invariants.py` verifies Sentry configuration.

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

## Verification

Run security checks locally:

```bash
python scripts/check_security_invariants.py
```

CI runs these checks on every PR and push to main.

---

## Adding New Invariants

1. Document the invariant in this file
2. Add automated check to `scripts/check_security_invariants.py` if possible
3. Update CI workflow if needed
4. Add regression test to `tests/test_regression_tripwires.py`
