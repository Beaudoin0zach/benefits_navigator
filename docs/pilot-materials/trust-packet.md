# Benefits Navigator — Trust & Security Overview

*For pilot partners and prospective customers*

---

## Executive Summary

Benefits Navigator (BN) is designed with veteran data protection as a core principle. We process sensitive claim information including medical records, VA decision letters, and personal identifiers. This document explains how we protect that data.

**Key commitments:**
- No permanent storage of raw document text (PHI)
- Field-level encryption for all PII (SSN, VA file numbers, dates of birth)
- Comprehensive audit logging of all sensitive operations
- Explicit user consent required before any AI processing
- Time-limited, cryptographically signed URLs for document access

---

## 1. Security Architecture

### 1.1 Data Classification

| Data Type | Classification | Protection |
|-----------|---------------|------------|
| VA File Number | PII - High | AES-256 encrypted at rest |
| Date of Birth | PII - High | AES-256 encrypted at rest |
| SSN (if captured) | PII - Critical | AES-256 encrypted, masked in UI |
| Medical Records | PHI | Never stored; processed in-memory only |
| Decision Letters | PHI | Never stored; processed in-memory only |
| AI Analysis Results | Derived Data | Stored without source text |

### 1.2 Ephemeral Document Processing

Raw document text (OCR output, decision letter content) is **never persisted to the database**. Our processing pipeline:

1. User uploads document
2. OCR extracts text in memory
3. AI analyzes text and generates structured output
4. Only metadata and AI-derived insights are stored
5. Original text is discarded

This "ephemeral OCR" architecture means a database breach cannot expose raw medical records or decision letter content.

### 1.3 Encryption

**At Rest:**
- All PII fields use AES-256 encryption via Fernet
- Dedicated encryption key separate from application secret
- Key rotation supported without data migration downtime

**In Transit:**
- TLS 1.3 enforced for all connections
- HSTS enabled with 1-year max-age
- No plaintext HTTP allowed

### 1.4 Access Controls

**Authentication:**
- Email-based authentication with secure password requirements
- Optional MFA support for VSO staff accounts
- Session timeout after inactivity

**Authorization:**
- Users can only access their own documents
- VSO staff can only access cases within their organization
- Multi-organization users must explicitly select active org
- Document sharing requires explicit user action

**Document Access:**
- Time-limited signed URLs (default 30 minutes, max 24 hours)
- HMAC-SHA256 cryptographic signatures prevent URL tampering
- URLs include user ID validation to prevent sharing

---

## 2. Privacy Model

### 2.1 AI Processing Consent

Before any AI features can be used, users must explicitly grant consent:

- Consent is opt-in, not opt-out
- Clear explanation of what data is processed
- Consent can be revoked at any time
- Revocation stops all AI processing immediately

### 2.2 Data Minimization

We collect only what's necessary:

| Collected | Not Collected |
|-----------|---------------|
| Email address | Full name (optional) |
| Uploaded documents (temporary) | Home address |
| AI analysis results | Phone number |
| Usage metrics | Location data |

### 2.3 Third-Party Data Sharing

| Third Party | Data Shared | Purpose |
|-------------|-------------|---------|
| OpenAI | Document excerpts (ephemeral) | AI analysis |
| Sentry | Error traces (no PII) | Error monitoring |
| Stripe | Email, subscription status | Payment processing |

**OpenAI specifics:**
- `send_default_pii=False` in Sentry (no user data in errors)
- We do not use OpenAI's training data retention
- Document text sent via API is not stored by OpenAI

---

## 3. Data Retention

### 3.1 Retention Periods

| Data Type | Retention | Rationale |
|-----------|-----------|-----------|
| User accounts | Until deletion requested | User access |
| Uploaded documents (files) | 90 days after upload | Processing window |
| AI analysis results | Until user deletes | User reference |
| Audit logs | 2 years | Compliance, security |
| Session data | 24 hours | Security |

### 3.2 Data Deletion

Users can request complete data deletion:
- All documents and analyses removed
- Account deactivated
- Audit logs retained (anonymized) for security compliance
- Deletion completed within 30 days

---

## 4. AI Usage Disclosure

### 4.1 What AI Does

Benefits Navigator uses OpenAI's GPT models to:

1. **Decision Letter Analysis** — Parse VA decision letters into plain-English summaries, identify granted/denied conditions, and explain appeal options
2. **Evidence Gap Analysis** — Identify missing evidence for claims, suggest documentation to gather
3. **Personal Statement Generation** — Help veterans write compelling nexus statements

### 4.2 AI Limitations

We clearly communicate to users:

- AI analysis is **not legal advice**
- Results should be reviewed by qualified professionals
- AI can make mistakes; always verify important information
- AI cannot access external databases or real-time VA systems

### 4.3 Human Oversight

- VSO staff review AI analyses before taking action
- Users can flag incorrect AI outputs
- All AI interactions are logged for quality review

---

## 5. Incident Response

### 5.1 Incident Classification

| Severity | Description | Response Time |
|----------|-------------|---------------|
| Critical | Data breach, system compromise | 1 hour |
| High | Service outage, security vulnerability | 4 hours |
| Medium | Degraded performance, minor bug | 24 hours |
| Low | Feature request, cosmetic issue | Best effort |

### 5.2 Breach Notification

In the event of a data breach:

1. Affected users notified within 72 hours
2. Clear description of what data was affected
3. Steps users should take to protect themselves
4. Contact information for questions

### 5.3 Contact

Security concerns: security@[yourdomain].com
Privacy questions: privacy@[yourdomain].com

---

## 6. Compliance Posture

### 6.1 Current Status

| Framework | Status |
|-----------|--------|
| SOC 2 Type I | Not yet certified |
| HIPAA | Architecture designed for compliance; BAA available on request |
| VA MOU | Not applicable (no direct VA system integration) |
| State Privacy Laws | CCPA-compliant deletion and access rights |

### 6.2 Roadmap

- Q2 2025: SOC 2 Type I audit
- Q3 2025: HIPAA compliance certification
- Ongoing: Annual penetration testing

---

## 7. Audit Logging

All security-sensitive operations are logged:

### 7.1 Logged Events

**Authentication:**
- Login (success/failure)
- Logout
- Password changes
- Password resets

**Document Operations:**
- Upload
- View
- Download
- Delete
- Share (VSO)

**AI Operations:**
- Analysis requests
- Consent grants/revokes

**VSO Operations:**
- Case creation/updates
- Note additions
- Document reviews

### 7.2 Log Contents

Each audit entry includes:
- Timestamp (UTC)
- User identifier
- Action type
- Resource type and ID
- IP address
- Success/failure status
- Request path

### 7.3 Log Protection

- Logs are append-only (no modification)
- Admin-only deletion (superuser required)
- 2-year retention minimum
- No PII in log details

---

## Appendix A: Security Headers

All responses include:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
Content-Security-Policy: [configured per-page]
```

---

## Appendix B: Rate Limiting

| Endpoint | Limit | Scope |
|----------|-------|-------|
| Login | 5/minute, 20/hour | IP address |
| Signup | 3/hour | IP address |
| Password Reset | 3/hour | IP address |
| Document Upload | 10/minute | User |
| AI Analysis | 20/hour | User |
| Status Polling | 60/minute | User |

---

*Document version: 1.0*
*Last updated: January 2025*
