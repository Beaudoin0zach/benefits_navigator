# Benefits Navigator - Deployment & Operations Guide

## Environments

### Local Development
- **URL:** http://localhost:8000
- **Database:** PostgreSQL via Docker (port 5432)
- **Redis:** Docker (port 6379)
- **Flower (Celery monitor):** http://localhost:5555

### Staging (DigitalOcean App Platform)
- **URL:** https://benefits-navigator-staging-3o4rq.ondigitalocean.app
- **App ID:** `2119eba2-07b6-405f-a962-d40dd6956137`
- **Region:** NYC

---

## Local Development

### Start all services
```bash
docker compose up -d
```

### View logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f celery
docker compose logs -f web
```

### Rebuild after code changes
```bash
docker compose build celery && docker compose up -d celery
docker compose build web && docker compose up -d web
```

### Access local database
```bash
docker exec -it benefits_nav_db psql -U benefits_user -d benefits_navigator
```

### Reset usage limits (for testing)
```bash
docker exec benefits_nav_db psql -U benefits_user -d benefits_navigator -c "UPDATE accounts_usagetracking SET documents_uploaded_this_month = 0;"
```

### Environment variables
- File: `.env` (used by docker-compose)
- Key variables:
  - `OPENAI_API_KEY` - Required for AI analysis
  - `FEATURE_ORGANIZATIONS=true` - Enable Path B (VSO Platform)

---

## Staging (DigitalOcean)

### Prerequisites
Install doctl CLI:
```bash
brew install doctl
doctl auth init  # Enter your DO API token
```

### Check deployment status
```bash
doctl apps list-deployments 2119eba2-07b6-405f-a962-d40dd6956137 --output json | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data:
    print(f\"Phase: {data[0].get('phase')}\")"
```

### View logs
```bash
# Web service
doctl apps logs 2119eba2-07b6-405f-a962-d40dd6956137 web

# Worker (Celery)
doctl apps logs 2119eba2-07b6-405f-a962-d40dd6956137 worker

# Follow logs
doctl apps logs 2119eba2-07b6-405f-a962-d40dd6956137 worker --follow
```

### Force redeploy
```bash
doctl apps create-deployment 2119eba2-07b6-405f-a962-d40dd6956137 --force-rebuild
```

### Connect to staging database
```bash
# Get password from DO Console or use:
# doctl databases get benefits-nav-db --output json
PGPASSWORD=<DB_PASSWORD> psql \
  -h benefits-nav-db-do-user-29214045-0.j.db.ondigitalocean.com \
  -p 25060 \
  -U doadmin \
  -d benefits_navigator
```

### Check/update app spec
```bash
# Get current spec
doctl apps get 2119eba2-07b6-405f-a962-d40dd6956137 --output json

# Update spec (see .do/app.yaml for template)
doctl apps update 2119eba2-07b6-405f-a962-d40dd6956137 --spec .do/app.yaml
```

---

## Managed Services

### Database (PostgreSQL)
- **Host:** benefits-nav-db-do-user-29214045-0.j.db.ondigitalocean.com
- **Port:** 25060
- **User:** doadmin
- **Database:** benefits_navigator
- **SSL:** Required

### Valkey (Redis-compatible)
- **Host:** db-valkey-nyc3-98037-do-user-29214045-0.k.db.ondigitalocean.com
- **Port:** 25061
- **Protocol:** rediss:// (SSL required)

Get connection URL:
```bash
doctl databases connection d13ae1d1-e114-4174-999c-be584026ec14 --output json
```

---

## Environment Variables (Staging)

### App-level (inherited by all components)
| Variable | Type | Description |
|----------|------|-------------|
| DJANGO_SETTINGS_MODULE | Plain | `benefits_navigator.settings` |
| DEBUG | Plain | `False` |
| STAGING | Plain | `True` |
| SECRET_KEY | Secret | Django secret key |
| DATABASE_URL | Secret | PostgreSQL connection string |
| REDIS_URL | Secret | Valkey connection string |
| CELERY_BROKER_URL | Secret | Valkey connection string |
| OPENAI_API_KEY | Secret | OpenAI API key |
| SENTRY_DSN | Secret | Sentry error tracking |

### Path B Feature Flags
| Variable | Value | Description |
|----------|-------|-------------|
| FEATURE_ORGANIZATIONS | True | Enable organizations |
| FEATURE_ORG_ROLES | True | Role-based permissions |
| FEATURE_ORG_INVITATIONS | True | Team invitations |
| FEATURE_CASEWORKER_ASSIGNMENT | True | Case assignment |
| FEATURE_ORG_ADMIN | True | Admin dashboard |

### Worker-specific (must be set explicitly)
DO App Platform does NOT inherit app-level secrets to workers. These must be set at worker level:
- REDIS_URL
- CELERY_BROKER_URL
- OPENAI_API_KEY

---

## Common Issues & Fixes

### AI analysis not saving
**Symptom:** Document shows "completed" but ai_summary is NULL

**Fix:** Ensure `claims/tasks.py` has explicit save before `mark_completed()`:
```python
document.ai_summary = ai_result['analysis']
document.ai_model_used = ai_result['model']
document.ai_tokens_used = ai_result['tokens_used']
document.save(update_fields=['ai_summary', 'ai_model_used', 'ai_tokens_used'])  # This line!
document.mark_completed(duration=duration)
```

### Worker not receiving tasks
**Symptom:** Tasks queued but worker logs show no activity

**Causes:**
1. Worker missing CELERY_BROKER_URL (check worker-level envs)
2. Web service missing CELERY_BROKER_URL (tasks can't be queued)

**Fix:** Ensure both app-level AND worker-level have REDIS_URL and CELERY_BROKER_URL set.

### Invalid OpenAI API key
**Symptom:** 401 error in Celery logs

**Fix:**
- Local: Update `.env` file, then `docker compose down celery && docker compose up -d celery`
- Staging: Update via doctl spec or DO Console

### Celery SSL connection error
**Symptom:** `ValueError('A rediss:// URL must have parameter ssl_cert_reqs...')`

**Fix:** Ensure `settings.py` has SSL config for Celery (already implemented):
```python
if CELERY_BROKER_URL.startswith('rediss://'):
    CELERY_BROKER_USE_SSL = {'ssl_cert_reqs': ssl.CERT_REQUIRED}
```

---

## Key URLs

### Staging
- Home: https://benefits-navigator-staging-3o4rq.ondigitalocean.app
- Health check: https://benefits-navigator-staging-3o4rq.ondigitalocean.app/health/
- Document upload: https://benefits-navigator-staging-3o4rq.ondigitalocean.app/claims/upload/
- Organizations: https://benefits-navigator-staging-3o4rq.ondigitalocean.app/accounts/organizations/

### Local
- Home: http://localhost:8000
- Document upload: http://localhost:8000/claims/upload/
- Organizations: http://localhost:8000/accounts/organizations/
- Flower (Celery): http://localhost:5555
- Django Admin: http://localhost:8000/admin/

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    DO App Platform                       │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Web       │  │   Worker    │  │   Migrate   │     │
│  │  (Django)   │  │  (Celery)   │  │   (Job)     │     │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┘     │
│         │                │                              │
│         ▼                ▼                              │
│  ┌─────────────────────────────────────────────┐       │
│  │              Valkey (Redis)                  │       │
│  │         (Task Queue & Results)               │       │
│  └─────────────────────────────────────────────┘       │
│         │                                               │
│         ▼                                               │
│  ┌─────────────────────────────────────────────┐       │
│  │           PostgreSQL Database                │       │
│  └─────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

---

## Dual-Path Development

### Path A - Direct-to-Veteran (B2C)
- Freemium model with usage limits
- Individual Stripe billing
- Usage tracking

### Path B - VSO Platform (B2B)
- Organization management
- Role-based access (Admin, Caseworker, Viewer)
- Team invitations
- Case assignment
- Organization billing (future)

Feature flags in `benefits_navigator/settings.py` control which path is active.
