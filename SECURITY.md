# Security Policy & Audit Status

**Last Updated:** 2026-02-09
**Last Audit:** 2026-02-09 (see `docs/AUDIT_2026_02_09.md`)

---

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability in VA Benefits Navigator, please report it responsibly.

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please email security concerns to: **security@vabenefitsnavigator.org**

Or use GitHub's private vulnerability reporting feature if enabled.

### What to Include

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Potential impact** assessment
4. **Suggested fix** (if you have one)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution Target**: Within 30 days for critical issues

---

## Security Architecture

### Authentication & Access Control

| Layer | Implementation | File |
|-------|---------------|------|
| Auth | django-allauth (email-based, no username) | `accounts/views.py` |
| MFA | django-allauth-2fa + django-otp (VSO staff) | `vso/middleware.py` |
| Rate Limiting | django-ratelimit (IP pre-auth, user post-auth) | `accounts/views.py`, `claims/views.py` |
| Session | Django sessions with Argon2 password hashing | `settings.py` |

### Rate Limits

| Endpoint | Rate | Key |
|----------|------|-----|
| Login | 5/min + 20/hr | IP |
| Signup | 3/hr | IP |
| Password Reset | 3/hr | IP |
| Document Upload | 10/min | user |
| Status Polling | 60/min | user |
| AI Agent Submit | 20/hr | user |

### Data Protection

| Data Type | Protection | File |
|-----------|-----------|------|
| VA File Number | `EncryptedCharField` (Fernet AES-256) | `accounts/models.py:174` |
| Date of Birth | `EncryptedDateField` (Fernet AES-256) | `accounts/models.py:185` |
| OCR Text | Ephemeral (not persisted to DB) | `claims/models.py` |
| Media Files | HMAC-SHA256 signed URLs, 30min expiry | `core/signed_urls.py` |
| AI Responses | Pydantic-validated, sanitized input | `agents/ai_gateway.py` |
| GraphQL Output | PII redaction (SSN, VA file, phone, DOB) | `benefits_navigator/schema.py` |

### Security Headers

| Header | Value | Notes |
|--------|-------|-------|
| Content-Security-Policy | Configured per environment | `unsafe-inline` for Tailwind CDN (P2 fix) |
| X-Frame-Options | DENY | Clickjacking protection |
| X-Content-Type-Options | nosniff | MIME sniffing protection |
| HSTS | 1 year (production) | Strict transport security |
| Referrer-Policy | same-origin | Referrer leakage prevention |

### Monitoring & Alerting

| Metric | Warning | Critical |
|--------|---------|----------|
| Processing success rate | < 90% | < 80% |
| Failures per hour | > 5 | > 10 |
| Celery workers | <= 1 | = 0 |
| Queue length | > 50 | > 100 |
| Downloads per user/hour | > 50 | > 100 |

Alert channels: Email, Slack, Sentry (see `core/alerting.py`).

---

## Audit Findings (2026-02-09)

### CRITICAL — Open Issues

**1. Secrets in Version Control**
- **Status:** OPEN — requires immediate remediation
- **Finding:** Production credentials (SECRET_KEY, DATABASE_URL, REDIS_URL, FIELD_ENCRYPTION_KEY, OpenAI API key) hardcoded in `app-spec-fixed.yaml`, `.do/app.yaml`, and `.env`
- **Impact:** Anyone with repo access can decrypt all veteran PII, hijack sessions, abuse API keys
- **Remediation:**
  1. Revoke ALL exposed keys immediately
  2. Rotate FIELD_ENCRYPTION_KEY and re-encrypt PII
  3. Scrub git history with `git-filter-repo`
  4. Add deployment configs to `.gitignore`
  5. Create template files with placeholder values only
  6. Install `detect-secrets` pre-commit hook

**2. VSO Cross-Organization Access (IDOR)**
- **Status:** OPEN
- **Finding:** Multi-org users can switch organizations via session; case queries don't consistently filter by organization
- **Impact:** Potential unauthorized access to another organization's veteran cases
- **Files:** `vso/views.py` — add `organization=org` filter to all `get_object_or_404` calls

**3. `ai_summary` Stored Unencrypted**
- **Status:** OPEN
- **Finding:** `claims/models.py:105` stores AI analysis results as plaintext JSON; may contain PII extracted from documents
- **Impact:** PII exposure if database is compromised
- **Fix:** Add `EncryptedJSONField` or pre-storage PII redaction

**4. CSP `unsafe-inline` for Styles**
- **Status:** OPEN (P2 — mitigated by other controls)
- **Finding:** Tailwind CSS loaded via CDN requires `unsafe-inline` in STYLE_SRC
- **Impact:** Reduced XSS protection for style-based attacks
- **Fix:** Build Tailwind to static CSS with PostCSS

### PASS — Verified Secure

- Input sanitization via `sanitize_input()` — all OpenAI calls routed through AI Gateway
- File upload security — magic byte validation, size limits, page limits, extension whitelist
- Rate limiting — comprehensive on all public endpoints
- GraphQL PII redaction — SSN, VA file numbers, phone, DOB patterns caught
- Sentry configured with `send_default_pii=False`
- No PII found in logging statements
- Signed URLs for all media access (HMAC-SHA256, time-limited)
- Audit logging for all sensitive operations
- Non-root user in production Docker container

---

## Security Best Practices

### For Deployers

1. **Never commit secrets** — Use environment variables for all sensitive data
2. **Use HTTPS** — Always deploy with TLS/SSL in production
3. **Keep dependencies updated** — Run `pip-audit` regularly (CI does this automatically)
4. **Set strong SECRET_KEY** — Generate unique random key; never reuse across environments
5. **Set FIELD_ENCRYPTION_KEY** — Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
6. **Configure ALLOWED_HOSTS** — Restrict to your actual domain(s)
7. **Enable MFA for VSO staff** — Required for caseworker accounts
8. **Monitor alerts** — Configure ALERT_EMAIL_RECIPIENTS and SLACK_ALERT_WEBHOOK

### For Contributors

1. **No hardcoded credentials** — Always use environment variables
2. **All OpenAI calls through AI Gateway** — Never import `openai` directly
3. **PII fields use EncryptedCharField** — See `core/encryption.py`
4. **Validate all file uploads** — Magic bytes + extension + size + page count
5. **Add `acks_late=True` to Celery tasks** — Prevents message loss on worker crash
6. **Run `pytest` before committing** — Especially security and rate-limit tests
7. **Never log PII** — Use IDs only in log statements and Celery task args
8. **Use OWASP guidelines** — Be aware of common vulnerabilities

---

## Data Handling

### What We Store

- User account information (email, Argon2-hashed passwords)
- Encrypted PII (VA file number, date of birth — Fernet AES-256)
- Uploaded documents (file system or S3, accessed via signed URLs)
- AI analysis results (JSON summaries)
- Saved calculations and appeal records

### What We Don't Store

- Raw OCR text (ephemeral; processed in memory, only metadata persisted)
- Payment card numbers (handled by Stripe)
- OpenAI API keys in database
- Raw AI prompts/responses containing PII (sanitized before storage)

### Data Retention

- Pilot mode: 30-day retention with 7-day pre-deletion warning
- Production: User data retained until account deletion requested
- Soft-deleted data permanently purged after configured retention period
- Celery task results auto-expire after 1 hour

---

## Compliance Notes

This application is intended for **educational and informational purposes only**.

- **NOT HIPAA compliant** — Not designed for production medical data handling
- **NOT legal advice** — Provides educational guidance on VA claims process
- Veterans should not upload documents containing sensitive medical information to shared deployments
- For production deployments handling sensitive veteran data, additional security measures and compliance requirements apply

---

## Security TODOs

See `TODO.md` for prioritized list. Key remaining items:
- [ ] Revoke and rotate all exposed secrets (P0)
- [ ] Fix VSO IDOR with organization filtering (P1)
- [ ] Encrypt ai_summary field (P1)
- [ ] Build Tailwind to static CSS, remove unsafe-inline (P2)
- [ ] Object storage migration (S3/DO Spaces)
- [ ] Additional VSO invitation verification
- [ ] Account lockout after failed logins
- [ ] CAPTCHA on signup (if spam becomes issue)
