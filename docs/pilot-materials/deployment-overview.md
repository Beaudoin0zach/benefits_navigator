# Benefits Navigator — Deployment Overview

*Technical deployment architecture for pilot partners*

---

## 1. Infrastructure Summary

| Component | Technology | Provider |
|-----------|------------|----------|
| Application | Django 5.0 / Python 3.11 | DigitalOcean App Platform |
| Database | PostgreSQL 15 | DigitalOcean Managed Database |
| Cache/Queue | Redis | DigitalOcean Managed Redis |
| Background Jobs | Celery | DigitalOcean App Platform (Worker) |
| File Storage | Local (transitioning to S3) | DigitalOcean Spaces (planned) |
| DNS/CDN | Cloudflare | Cloudflare |
| Monitoring | Sentry | Sentry.io |

---

## 2. Architecture Diagram

```
                                    ┌─────────────────┐
                                    │   Cloudflare    │
                                    │   (DNS + CDN)   │
                                    └────────┬────────┘
                                             │
                                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                    DigitalOcean App Platform                       │
│                                                                    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │     Web      │    │    Worker    │    │   Migrate    │        │
│  │   (Gunicorn) │    │   (Celery)   │    │  (Pre-deploy)│        │
│  │              │    │              │    │              │        │
│  │  Django App  │    │  Background  │    │  DB Migrate  │        │
│  │              │    │    Tasks     │    │              │        │
│  └──────┬───────┘    └──────┬───────┘    └──────────────┘        │
│         │                   │                                     │
└─────────┼───────────────────┼─────────────────────────────────────┘
          │                   │
          ▼                   ▼
    ┌───────────┐       ┌───────────┐       ┌───────────┐
    │ PostgreSQL│       │   Redis   │       │  OpenAI   │
    │ (Managed) │       │ (Managed) │       │   API     │
    └───────────┘       └───────────┘       └───────────┘
```

---

## 3. Hosting Details

### 3.1 DigitalOcean App Platform

**Why DigitalOcean:**
- SOC 2 Type II certified
- Managed infrastructure (no server maintenance)
- Automatic SSL certificates
- Built-in health checks and auto-restart
- Region: NYC (US East Coast)

**Current Configuration:**

| Service | Instance Size | Count | Resources |
|---------|--------------|-------|-----------|
| Web | basic-xxs | 1 | 0.5 vCPU, 512MB RAM |
| Worker | basic-xxs | 1 | 0.5 vCPU, 512MB RAM |

*Note: Instance sizes will scale based on pilot usage.*

### 3.2 Database

**PostgreSQL 15 (Managed):**
- Automatic daily backups (7-day retention)
- Point-in-time recovery available
- SSL/TLS connections required
- Private networking (not publicly accessible)

### 3.3 Redis

**Managed Redis:**
- Used for Celery task queue
- Used for Django cache
- SSL connections (rediss://)
- Automatic failover

---

## 4. Deployment Process

### 4.1 Continuous Deployment

```
Developer Push → GitHub → DigitalOcean Auto-Deploy
                              │
                              ▼
                    ┌─────────────────┐
                    │  Pre-deploy Job │
                    │  (migrations)   │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
              ┌──────────┐     ┌──────────┐
              │   Web    │     │  Worker  │
              │  Deploy  │     │  Deploy  │
              └──────────┘     └──────────┘
```

**Process:**
1. Code pushed to `main` branch
2. DigitalOcean detects push
3. Builds Docker image from `Dockerfile.prod`
4. Runs pre-deploy migration job
5. Deploys new containers (zero-downtime rolling update)
6. Health check validates deployment

### 4.2 Rollback

If a deployment fails:
- Automatic rollback to previous version
- Health check failures trigger rollback
- Manual rollback available in DO console

---

## 5. Backup Strategy

### 5.1 Database Backups

| Type | Frequency | Retention |
|------|-----------|-----------|
| Automated snapshots | Daily | 7 days |
| Point-in-time recovery | Continuous | 7 days |
| Manual backups | On-demand | Until deleted |

### 5.2 Application Data

| Data Type | Backup Method | Recovery |
|-----------|---------------|----------|
| User uploads | Local storage (planned: S3 with versioning) | From backup |
| Code | GitHub repository | Git history |
| Configuration | Environment variables in DO | DO console |

### 5.3 Disaster Recovery

**RPO (Recovery Point Objective):** < 24 hours
**RTO (Recovery Time Objective):** < 4 hours

Recovery procedure:
1. Restore database from backup
2. Redeploy application from GitHub
3. Restore file storage from backup
4. Validate with health checks

---

## 6. Access Controls

### 6.1 Infrastructure Access

| Role | Access Level | Authentication |
|------|--------------|----------------|
| Platform Admin | Full DO console | SSO + MFA |
| Developer | GitHub push | SSH key + MFA |
| Database Admin | Read-only console | SSO + MFA |

### 6.2 Application Access

| Role | Capabilities |
|------|-------------|
| Superuser | Django admin, all data |
| VSO Admin | Organization cases, user management |
| VSO Caseworker | Assigned cases, read-only org data |
| Veteran | Own documents and analyses |

### 6.3 Secrets Management

All secrets stored in DigitalOcean environment variables:

| Secret | Purpose |
|--------|---------|
| `SECRET_KEY` | Django cryptographic signing |
| `FIELD_ENCRYPTION_KEY` | PII field encryption (separate from SECRET_KEY) |
| `DATABASE_URL` | PostgreSQL connection |
| `REDIS_URL` | Redis connection |
| `OPENAI_API_KEY` | AI API access |
| `SENTRY_DSN` | Error monitoring |

---

## 7. Audit Logging

### 7.1 Application Audit Log

All sensitive operations logged to `core_auditlog` table:

```
┌─────────────────────────────────────────────────────────────┐
│                      Audit Log Entry                        │
├─────────────────────────────────────────────────────────────┤
│ timestamp      │ 2025-01-22 14:30:00 UTC                    │
│ user_email     │ veteran@example.com                        │
│ action         │ document_upload                            │
│ resource_type  │ Document                                   │
│ resource_id    │ 1234                                       │
│ ip_address     │ 192.168.1.1                                │
│ user_agent     │ Mozilla/5.0...                             │
│ request_path   │ /claims/upload/                            │
│ success        │ true                                       │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Logged Actions

**Authentication:**
- `login`, `logout`, `login_failed`
- `password_change`, `password_reset`

**Documents:**
- `document_upload`, `document_view`
- `document_download`, `document_delete`

**AI Processing:**
- `ai_analysis`, `denial_decode`
- `ai_decision_analyzer`, `ai_evidence_gap`
- `ai_statement_generator`

**VSO Operations:**
- `case_create`, `case_view`, `case_update`
- `note_add`, `document_share`, `document_review`

**Consent:**
- `ai_consent_grant`, `ai_consent_revoke`

### 7.3 Log Access

- Audit logs viewable in Django admin (read-only)
- Export available for compliance requests
- 2-year retention minimum

---

## 8. Monitoring & Alerting

### 8.1 Health Checks

**Endpoint:** `/health/`

```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected",
  "timestamp": "2025-01-22T14:30:00Z"
}
```

**Full check:** `/health/?full=1` includes queue status

### 8.2 Uptime Monitoring

- DigitalOcean built-in health checks (every 10 seconds)
- Automatic container restart on failure
- Slack/email alerts on downtime

### 8.3 Error Tracking

**Sentry Integration:**
- All unhandled exceptions captured
- No PII in error reports (`send_default_pii=False`)
- Alert on new error types
- Performance monitoring enabled

### 8.4 Metrics Tracked

| Metric | Threshold | Alert |
|--------|-----------|-------|
| Error rate | > 1% | Email |
| Response time (p95) | > 2s | Slack |
| Queue length | > 100 | Slack |
| Worker failures | > 5/hour | Email |

---

## 9. Scalability

### 9.1 Current Capacity

| Resource | Limit | Current |
|----------|-------|---------|
| Concurrent users | ~50 | < 10 |
| Documents/day | ~500 | < 50 |
| AI requests/hour | ~200 | < 20 |

### 9.2 Scaling Path

**Horizontal scaling (easy):**
- Add web instances (load balanced)
- Add worker instances (parallel processing)

**Vertical scaling (medium):**
- Upgrade instance sizes
- Upgrade database tier

**Architectural (if needed):**
- Move file storage to S3/Spaces
- Add read replicas for database
- Implement CDN for static assets

### 9.3 Cost Projection

| Scale | Monthly Cost (est.) |
|-------|---------------------|
| Pilot (current) | ~$50 |
| 100 users | ~$100 |
| 500 users | ~$300 |
| 1000+ users | ~$500+ |

---

## 10. Security Certifications

### 10.1 Infrastructure Provider (DigitalOcean)

- SOC 2 Type II certified
- ISO 27001 certified
- GDPR compliant

### 10.2 Application (Benefits Navigator)

| Certification | Status |
|---------------|--------|
| SOC 2 Type I | Planned Q2 2025 |
| HIPAA | Architecture ready; BAA on request |
| Penetration Test | Planned Q1 2025 |

---

## Appendix: Environment Variables

```bash
# Required for all environments
SECRET_KEY=<django-secret-key>
FIELD_ENCRYPTION_KEY=<fernet-key>
DATABASE_URL=postgresql://...
REDIS_URL=rediss://...
OPENAI_API_KEY=sk-...
ALLOWED_HOSTS=your-domain.com

# Production only
DEBUG=False
SENTRY_DSN=https://...
SECURE_SSL_REDIRECT=True

# Optional
CELERY_BROKER_URL=<same-as-redis>
```

---

*Document version: 1.0*
*Last updated: January 2025*
