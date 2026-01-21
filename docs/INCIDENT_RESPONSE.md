# Incident Response Runbook

This document provides procedures for responding to system incidents, handling alerts, and conducting post-mortems.

## Table of Contents

1. [Severity Levels](#severity-levels)
2. [Escalation Procedures](#escalation-procedures)
3. [Alert Runbooks](#alert-runbooks)
4. [Post-Mortem Template](#post-mortem-template)
5. [Contact Information](#contact-information)

---

## Severity Levels

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| **SEV1 - Critical** | Service down, data breach, or security incident | Immediate (< 15 min) | Database down, suspected breach, all workers dead |
| **SEV2 - High** | Major feature broken, significant degradation | < 1 hour | Document processing < 80%, no Celery workers |
| **SEV3 - Medium** | Partial degradation, non-critical feature broken | < 4 hours | Processing rate 80-90%, queue backlog > 50 |
| **SEV4 - Low** | Minor issues, cosmetic bugs | Next business day | Single task timeout, minor UI issue |

---

## Escalation Procedures

### Initial Response

1. **Acknowledge** the alert within the response time window
2. **Assess** the severity and scope of the incident
3. **Communicate** status to stakeholders
4. **Mitigate** immediate impact if possible
5. **Investigate** root cause
6. **Resolve** the incident
7. **Document** actions taken

### Escalation Path

```
Level 1: On-Call Engineer
    |
    v (after 15 min unresolved SEV1/SEV2)
Level 2: Engineering Lead
    |
    v (after 30 min unresolved SEV1)
Level 3: CTO / Incident Commander
    |
    v (data breach or legal implications)
Level 4: Legal / Compliance Team
```

### Communication Templates

**Initial Alert (Slack/Email):**
```
[SEV{N}] {Title}
Status: Investigating
Impact: {Brief description of user impact}
Start Time: {ISO timestamp}
Next Update: {Time}
```

**Status Update:**
```
[SEV{N}] {Title} - Update
Status: {Investigating/Mitigating/Resolved}
Impact: {Current user impact}
Actions Taken: {Bulleted list}
Next Steps: {What we're doing next}
Next Update: {Time}
```

**Resolution:**
```
[SEV{N}] {Title} - RESOLVED
Duration: {Start to end time}
Root Cause: {Brief description}
Resolution: {What fixed it}
Follow-up: {Link to post-mortem if SEV1/SEV2}
```

---

## Alert Runbooks

### System Health Critical

**Alert:** `System Health Critical`
**Severity:** SEV1
**Triggered when:** Overall health status is "unhealthy"

**Steps:**
1. Check the health endpoint: `curl https://app.example.com/health/?full=1`
2. Identify which component is unhealthy
3. Follow the specific runbook for that component below

### Database Connection Failed

**Alert:** `Database connection failed`
**Severity:** SEV1

**Steps:**
1. Check DigitalOcean database status in control panel
2. Verify connection string in environment variables
3. Check if connection pool is exhausted:
   ```bash
   python manage.py dbshell
   SELECT count(*) FROM pg_stat_activity;
   ```
4. If pool exhausted, restart web workers:
   ```bash
   doctl apps create-deployment <app-id>
   ```
5. If database down, check DigitalOcean status page and open support ticket

### Redis Connection Failed

**Alert:** `Redis connection failed`
**Severity:** SEV2

**Steps:**
1. Check DigitalOcean Redis status
2. Verify REDIS_URL environment variable
3. Test connection:
   ```bash
   redis-cli -u $REDIS_URL ping
   ```
4. Check memory usage - may need to flush cache:
   ```bash
   redis-cli -u $REDIS_URL INFO memory
   ```
5. If persistent issue, restart Redis or provision new cluster

### Celery Workers Critical

**Alert:** `Celery Workers Critical` or `No Celery workers responding`
**Severity:** SEV2

**Steps:**
1. Check worker logs in DigitalOcean App Platform
2. Verify worker is running:
   ```bash
   doctl apps list-deployments <app-id>
   ```
3. Check for OOM kills in logs
4. Restart worker component:
   ```bash
   doctl apps create-deployment <app-id> --force-rebuild
   ```
5. If workers keep dying, check for memory leaks or infinite loops in tasks

### Document Processing Degraded/Critical

**Alert:** `Document Processing Critical` (< 80%) or `Degraded` (< 90%)
**Severity:** SEV2/SEV3

**Steps:**
1. Check recent failed documents:
   ```python
   from claims.models import Document
   Document.objects.filter(status='failed').order_by('-created_at')[:10]
   ```
2. Check for common error patterns in ProcessingFailure:
   ```python
   from core.models import ProcessingFailure
   ProcessingFailure.get_failure_stats(hours=24)
   ```
3. Check OpenAI API status: https://status.openai.com/
4. If OpenAI down, enable maintenance mode or queue bypass
5. If OCR failures, check Tesseract installation and dependencies

### Task Queue Backlog

**Alert:** `Task Queue Backlog Critical` (> 100) or `Warning` (> 50)
**Severity:** SEV3

**Steps:**
1. Check queue length:
   ```bash
   redis-cli -u $REDIS_URL LLEN celery
   ```
2. Check if workers are processing:
   ```bash
   celery -A benefits_navigator inspect active
   ```
3. If workers idle but queue full, check for task serialization errors
4. Scale up workers temporarily if needed
5. Consider task prioritization if specific tasks are backing up

### Long-Running Task

**Alert:** `Long-Running Task Critical` (> 10 min) or `Warning` (> 5 min)
**Severity:** SEV3

**Steps:**
1. Identify the task:
   ```bash
   celery -A benefits_navigator inspect active
   ```
2. Check if task is stuck or legitimately slow
3. If stuck, revoke the task:
   ```bash
   celery -A benefits_navigator control revoke <task-id> --terminate
   ```
4. Investigate why task is slow (large document, API timeout, etc.)
5. Consider adding task timeout if not present

### Anomalous Download Activity

**Alert:** `Anomalous Download Activity` or `Elevated Download Activity`
**Severity:** SEV2 (Critical) / SEV3 (Warning)

**Steps:**
1. Identify the user from alert details
2. Check if legitimate (VSO bulk review, user exporting their data):
   ```python
   from core.models import AuditLog
   AuditLog.objects.filter(
       action='document_download',
       user_id=<user_id>
   ).order_by('-timestamp')[:50]
   ```
3. If suspicious:
   - Temporarily disable user account
   - Review downloaded documents
   - Check for automated access patterns (uniform timing)
4. If confirmed malicious:
   - Permanently disable account
   - Notify affected veterans if their data was accessed
   - Engage legal/compliance team
   - File incident report

### Multiple Users Same IP

**Alert:** `Multiple Users Same IP`
**Severity:** SEV3

**Steps:**
1. Check if IP is a known corporate/VPN IP (VSO office)
2. Review user accounts associated with IP
3. If legitimate shared office, add IP to allowlist
4. If suspicious, investigate for credential sharing or automated access

---

## Post-Mortem Template

Use this template for all SEV1 and SEV2 incidents.

```markdown
# Post-Mortem: {Incident Title}

**Date:** {YYYY-MM-DD}
**Severity:** SEV{N}
**Duration:** {Start time} to {End time} ({X hours Y minutes})
**Author:** {Name}
**Reviewers:** {Names}

## Summary

{2-3 sentence summary of what happened and impact}

## Impact

- **Users affected:** {Number or percentage}
- **Functionality affected:** {List of features}
- **Data impact:** {Any data loss or corruption}
- **Financial impact:** {If applicable}

## Timeline

All times in UTC.

| Time | Event |
|------|-------|
| HH:MM | {Event description} |
| HH:MM | Alert triggered |
| HH:MM | On-call acknowledged |
| HH:MM | Root cause identified |
| HH:MM | Mitigation applied |
| HH:MM | Incident resolved |

## Root Cause

{Detailed technical explanation of what caused the incident}

## Resolution

{What was done to resolve the incident}

## What Went Well

- {Bullet points of things that worked}

## What Went Poorly

- {Bullet points of things that didn't work}

## Action Items

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| {Action} | {Name} | {Date} | {Open/In Progress/Done} |

## Lessons Learned

{Key takeaways and how we'll prevent this in the future}

## References

- {Links to relevant logs, dashboards, or documentation}
```

---

## Contact Information

> **Note:** Update this section with actual contact information before deployment.

### On-Call Schedule

| Role | Primary | Backup |
|------|---------|--------|
| On-Call Engineer | TBD | TBD |
| Engineering Lead | TBD | TBD |
| CTO | TBD | TBD |

### External Contacts

| Service | Support Link | Status Page |
|---------|-------------|-------------|
| DigitalOcean | https://cloud.digitalocean.com/support | https://status.digitalocean.com/ |
| OpenAI | https://help.openai.com/ | https://status.openai.com/ |
| Sentry | https://sentry.io/support/ | https://status.sentry.io/ |
| Stripe | https://support.stripe.com/ | https://status.stripe.com/ |

### Communication Channels

- **Slack:** #incidents (for real-time coordination)
- **Email:** incidents@example.com (for external stakeholders)
- **Status Page:** status.example.com (for user communication)

---

## Appendix: Setting Up Alerting

### Environment Variables

Add to your `.env` or DigitalOcean App Platform environment:

```bash
# Alert recipients (comma-separated)
ALERT_EMAIL_RECIPIENTS=oncall@example.com,engineering@example.com

# Slack webhook for alerts (optional)
SLACK_ALERT_WEBHOOK=https://hooks.slack.com/services/XXX/YYY/ZZZ

# Alert channels to use
ALERT_CHANNELS=email,slack,sentry
```

### Celery Beat Schedule

Add to `settings.py` or your Celery Beat configuration:

```python
CELERY_BEAT_SCHEDULE = {
    'run-monitoring-checks': {
        'task': 'core.tasks.run_monitoring_checks',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'check-download-anomalies': {
        'task': 'core.tasks.check_download_anomalies_task',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

### Custom Thresholds

Override default thresholds in `settings.py`:

```python
ALERT_THRESHOLDS = {
    'processing_success_rate_warning': 90.0,
    'processing_success_rate_critical': 80.0,
    'failures_per_hour_warning': 5,
    'failures_per_hour_critical': 10,
    'min_workers_warning': 1,
    'min_workers_critical': 0,
    'queue_length_warning': 50,
    'queue_length_critical': 100,
    'task_age_warning': 300,  # 5 minutes
    'task_age_critical': 600,  # 10 minutes
    'downloads_per_hour_warning': 50,
    'downloads_per_hour_critical': 100,
}
```
