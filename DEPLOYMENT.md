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

## Rollback Procedures

### Staging (DigitalOcean App Platform)

#### List recent deployments
```bash
doctl apps list-deployments 2119eba2-07b6-405f-a962-d40dd6956137 --format ID,Phase,CreatedAt,UpdatedAt
```

#### Rollback to a previous deployment
```bash
# Get deployment ID from list above, then:
doctl apps create-deployment 2119eba2-07b6-405f-a962-d40dd6956137 --wait
```

> **Note:** DO App Platform doesn't have native rollback. To revert:
> 1. Identify the last working commit in GitHub
> 2. Revert or reset to that commit
> 3. Push to trigger new deployment

#### Quick revert via Git
```bash
# Find the last working commit
git log --oneline -10

# Revert the bad commit (creates new commit)
git revert <bad-commit-hash>
git push origin main

# OR reset to previous state (rewrites history - use with caution)
git reset --hard <good-commit-hash>
git push origin main --force
```

#### Rollback database migrations
If a deployment included a bad migration:
```bash
# Connect to staging database
PGPASSWORD=<DB_PASSWORD> psql \
  -h benefits-nav-db-do-user-29214045-0.j.db.ondigitalocean.com \
  -p 25060 -U doadmin -d benefits_navigator

# Check migration history
SELECT * FROM django_migrations ORDER BY applied DESC LIMIT 10;
```

Then locally:
```bash
# Identify the migration to rollback to
python manage.py showmigrations

# Generate reverse migration SQL (review before running!)
python manage.py sqlmigrate <app_name> <migration_name> --backwards
```

> **Warning:** Always backup the database before rolling back migrations. Some migrations are not reversible.

### Local Development

```bash
# Reset to previous state
git checkout <commit-hash>
docker compose down
docker compose build
docker compose up -d
```

---

## Database Backup & Restore

### Staging (DigitalOcean Managed Database)

#### Automatic Backups
DigitalOcean Managed Databases include automatic daily backups with 7-day retention.

**View backups in DO Console:**
https://cloud.digitalocean.com/databases/benefits-nav-db/backups

#### Manual Backup (pg_dump)
```bash
# Full database backup
PGPASSWORD=<DB_PASSWORD> pg_dump \
  -h benefits-nav-db-do-user-29214045-0.j.db.ondigitalocean.com \
  -p 25060 -U doadmin -d benefits_navigator \
  --format=custom --no-owner \
  -f benefits_navigator_$(date +%Y%m%d_%H%M%S).dump

# Data-only backup (no schema)
PGPASSWORD=<DB_PASSWORD> pg_dump \
  -h benefits-nav-db-do-user-29214045-0.j.db.ondigitalocean.com \
  -p 25060 -U doadmin -d benefits_navigator \
  --format=custom --no-owner --data-only \
  -f benefits_navigator_data_$(date +%Y%m%d_%H%M%S).dump
```

#### Restore from Backup

**Restore to staging (destructive):**
```bash
# WARNING: This will overwrite existing data
PGPASSWORD=<DB_PASSWORD> pg_restore \
  -h benefits-nav-db-do-user-29214045-0.j.db.ondigitalocean.com \
  -p 25060 -U doadmin -d benefits_navigator \
  --clean --no-owner \
  benefits_navigator_20240115_120000.dump
```

**Restore to a fresh database:**
```bash
# Create new database first via DO Console, then:
PGPASSWORD=<DB_PASSWORD> pg_restore \
  -h benefits-nav-db-do-user-29214045-0.j.db.ondigitalocean.com \
  -p 25060 -U doadmin -d benefits_navigator_restore \
  --no-owner \
  benefits_navigator_20240115_120000.dump
```

#### Point-in-Time Recovery
For critical data loss within the last 7 days, contact DigitalOcean support or use the Console to restore from a specific backup point.

### Local Development

#### Backup local database
```bash
docker exec benefits_nav_db pg_dump \
  -U benefits_user -d benefits_navigator \
  --format=custom \
  -f /tmp/local_backup.dump

# Copy from container
docker cp benefits_nav_db:/tmp/local_backup.dump ./local_backup.dump
```

#### Restore to local database
```bash
# Copy backup into container
docker cp ./local_backup.dump benefits_nav_db:/tmp/local_backup.dump

# Restore (destructive)
docker exec benefits_nav_db pg_restore \
  -U benefits_user -d benefits_navigator \
  --clean --no-owner \
  /tmp/local_backup.dump
```

#### Clone staging data to local
```bash
# Dump staging
PGPASSWORD=<DB_PASSWORD> pg_dump \
  -h benefits-nav-db-do-user-29214045-0.j.db.ondigitalocean.com \
  -p 25060 -U doadmin -d benefits_navigator \
  --format=custom --no-owner \
  -f staging_clone.dump

# Restore to local
docker cp staging_clone.dump benefits_nav_db:/tmp/staging_clone.dump
docker exec benefits_nav_db pg_restore \
  -U benefits_user -d benefits_navigator \
  --clean --no-owner \
  /tmp/staging_clone.dump
```

> **Note:** Scrub sensitive data after cloning staging to local if needed.

---

## CI/CD Pipeline

### Current Setup

Deployments are handled automatically by DigitalOcean App Platform:

| Trigger | Action |
|---------|--------|
| Push to `main` | Auto-deploy to staging |
| Pull request | No automated checks (recommended to add) |

Configuration: `.do/app.yaml` with `deploy_on_push: true`

### Deployment Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Push to     │────▶│  DO App      │────▶│  Build &     │
│  main branch │     │  Platform    │     │  Deploy      │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                     ┌───────────────────────────┼───────────────────────────┐
                     ▼                           ▼                           ▼
              ┌─────────────┐            ┌─────────────┐            ┌─────────────┐
              │   Migrate   │            │    Web      │            │   Worker    │
              │   (Job)     │            │  (Django)   │            │  (Celery)   │
              └─────────────┘            └─────────────┘            └─────────────┘
                     │
                     ▼
              PRE_DEPLOY
              (runs first)
```

### Recommended: GitHub Actions Workflow

Create `.github/workflows/ci.yml` to run tests before merging:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  PYTHON_VERSION: "3.11"

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - name: Install dependencies
        run: |
          pip install ruff
      - name: Run linter
        run: ruff check .

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-django pytest-cov
      - name: Run tests
        env:
          DATABASE_URL: postgres://test_user:test_pass@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
          CELERY_BROKER_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key-not-for-production
          DEBUG: "True"
        run: |
          pytest --cov=. --cov-report=xml -m "not e2e and not slow"
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml
          fail_ci_if_error: false

  e2e:
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-playwright
          playwright install chromium --with-deps
      - name: Run E2E tests
        env:
          DATABASE_URL: postgres://test_user:test_pass@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test-secret-key-not-for-production
        run: |
          pytest -m e2e --headed=false
```

### Running Tests Locally

```bash
# Unit tests only
docker compose exec web pytest -m "not e2e and not slow"

# All tests including slow
docker compose exec web pytest -m "not e2e"

# E2E tests (requires Playwright)
docker compose exec web pytest -m e2e

# With coverage
docker compose exec web pytest --cov=. --cov-report=html
```

### Branch Protection (Recommended)

Configure in GitHub repo settings (`Settings > Branches > Add rule`):

| Setting | Value |
|---------|-------|
| Branch name pattern | `main` |
| Require pull request | ✓ |
| Require status checks | ✓ (select `lint` and `test` jobs) |
| Require branches up to date | ✓ |
| Include administrators | Optional |

### Manual Deployment

If auto-deploy is disabled or you need to trigger manually:

```bash
# Via doctl
doctl apps create-deployment 2119eba2-07b6-405f-a962-d40dd6956137

# Force rebuild (clears build cache)
doctl apps create-deployment 2119eba2-07b6-405f-a962-d40dd6956137 --force-rebuild
```

### Disable Auto-Deploy

To require manual deployments, update `.do/app.yaml`:

```yaml
services:
  - name: web
    github:
      deploy_on_push: false  # Changed from true
```

Then apply:
```bash
doctl apps update 2119eba2-07b6-405f-a962-d40dd6956137 --spec .do/app.yaml
```

### Monitoring Deployments

```bash
# Watch deployment progress
doctl apps list-deployments 2119eba2-07b6-405f-a962-d40dd6956137 --format ID,Phase,Progress,CreatedAt

# Get deployment details
doctl apps get-deployment 2119eba2-07b6-405f-a962-d40dd6956137 <deployment-id>

# View build logs
doctl apps logs 2119eba2-07b6-405f-a962-d40dd6956137 --type build
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
