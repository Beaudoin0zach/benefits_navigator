# Shared Infrastructure

Infrastructure and features that benefit both Path A (B2C) and Path B (B2B).

## Overview

Shared infrastructure is developed first because:
1. Benefits all users regardless of path
2. Reduces technical debt
3. Required for VSO compliance
4. Improves overall reliability

## Completed

### Security Hardening
- [x] **Media Access Control**
  - Protected document download views
  - Authentication required for all media
  - Ownership verification
  - Audit logging on access
  - X-Sendfile support for production

- [x] **CSP Consolidation**
  - Single CSP source (django-csp)
  - Removed duplicate headers from middleware
  - Removed `unsafe-inline` where possible

- [x] **File Validation**
  - python-magic required (not optional)
  - Magic byte verification
  - MIME type checking
  - Page count limits for PDFs

- [x] **Security Headers**
  - Consolidated to single source
  - X-Content-Type-Options
  - X-Frame-Options
  - Referrer-Policy
  - Permissions-Policy

### Usage Tracking
- [x] **UsageTracking Model**
  - Monthly document counts (auto-reset)
  - Storage tracking (cumulative)
  - AI analysis counts
  - Denial decoder counts
  - Token consumption

- [x] **Limit Enforcement**
  - Checked on upload
  - Checked before expensive operations
  - Clear error messages

### Feature Flags
- [x] **Flag System**
  - Settings-based configuration
  - Environment variable overrides
  - Template context access
  - Decorator for views

### Audit Logging
- [x] **AuditLog Model**
  - User actions tracked
  - IP address captured
  - Resource type and ID
  - Success/failure status

- [x] **AuditMiddleware**
  - Automatic logging for sensitive paths
  - Document operations
  - AI analysis operations

## In Progress

### Health Monitoring
- [ ] **Health Check Endpoints**
  ```
  /health/          # Basic health (returns 200)
  /health/ready/    # Readiness (checks DB, Redis, Celery)
  /health/live/     # Liveness (basic check)
  ```

- [ ] **Monitoring Setup**
  - Celery worker health
  - Redis connection
  - Database connection
  - Queue depth

- [ ] **Alerting**
  - Failed task notifications
  - High error rate alerts
  - Resource exhaustion warnings

## Planned

### Compliance Infrastructure
- [ ] **Privacy Policy Page**
  - What data is collected
  - How it's used
  - How long it's retained
  - User rights

- [ ] **Consent Flow**
  - Explicit consent on signup
  - Record of consent timestamp
  - Ability to withdraw

- [ ] **Retention Policy Enforcement**
  - Configurable retention periods
  - Automated cleanup tasks
  - Audit trail of deletions

### Operational Readiness
- [ ] **Backup/Restore Testing**
  - Documented backup procedure
  - Tested restore procedure
  - RTO/RPO defined

- [ ] **Admin Runbook**
  - Common operations
  - Troubleshooting guide
  - Incident response

- [ ] **Rate Limiting**
  - Per-user rate limits on expensive operations
  - Global rate limits on AI endpoints
  - Configurable limits

### Developer Experience
- [ ] **Local Development**
  - Docker Compose improvements
  - Seed data scripts
  - Feature flag testing guide

- [ ] **Testing**
  - Increase test coverage
  - E2E tests for critical flows
  - Performance benchmarks

## Technical Details

### Health Check Implementation

```python
# core/views.py

def health(request):
    """Basic health check."""
    return JsonResponse({'status': 'ok'})

def health_ready(request):
    """Readiness check - verifies all dependencies."""
    checks = {
        'database': check_database(),
        'redis': check_redis(),
        'celery': check_celery(),
    }

    all_healthy = all(checks.values())
    status = 200 if all_healthy else 503

    return JsonResponse({
        'status': 'ready' if all_healthy else 'not_ready',
        'checks': checks,
    }, status=status)
```

### Retention Policy

```python
# core/models.py

class DataRetentionPolicy(models.Model):
    data_type = models.CharField(choices=[
        ('audit_logs', 'Audit Logs'),
        ('documents', 'Documents'),
        ('analyses', 'AI Analyses'),
    ])
    retention_days = models.IntegerField()
    is_active = models.BooleanField(default=True)
```

```python
# core/tasks.py

@shared_task
def enforce_retention_policies():
    """Celery beat task to clean up old data."""
    for policy in DataRetentionPolicy.objects.filter(is_active=True):
        cutoff = timezone.now() - timedelta(days=policy.retention_days)
        # Delete old records based on policy
```

### Rate Limiting

```python
# Existing rate limiting (django-ratelimit)
@ratelimit(key='user', rate='10/m', method='POST')
def ai_analysis_view(request):
    ...

# Could add token bucket for AI endpoints
```

## Dependencies

Both paths depend on shared infrastructure:

```
Shared Infrastructure
        ↓
   ┌────┴────┐
   ↓         ↓
Path A    Path B
```

**Priority:** Complete shared infrastructure items before path-specific features when possible.
