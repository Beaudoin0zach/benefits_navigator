# Codex Overview: DigitalOcean App Platform Celery Worker Deployment Issue

## Problem Summary
A Django + Celery application deployed on DigitalOcean App Platform. The web component works, but the Celery worker keeps failing with various errors.

## Current Architecture
- **Web:** Django + Gunicorn
- **Worker:** Celery (should connect to Redis)
- **Database:** DigitalOcean Managed PostgreSQL
- **Redis:** Upstash (external, uses `rediss://` SSL)
- **Deployment:** DigitalOcean App Platform

## Key Discovery
**DigitalOcean App Platform does NOT read `.do/app.yaml` from the repository** when the app was created via the Console UI. It uses an internal "App Spec" that must be edited via:
1. DO Console → Settings → App Spec → Edit
2. Or `doctl apps update <app-id> --spec <file.yaml>`

We spent hours pushing changes to `.do/app.yaml` that were completely ignored.

## What We've Tried

### Attempt 1: Set secrets via DO Console
- Set `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, etc. as `type: SECRET` in DO Console
- Result: Variables showed as "Encrypted" but were never passed to containers
- Worker failed with `ValueError: SECRET_KEY required`

### Attempt 2: Hardcode secrets in `.do/app.yaml`
- Changed all `type: SECRET` to `value: "actual-value"`
- Result: Still failed - DO wasn't reading the yaml file at all

### Attempt 3: Download and examine DO's actual App Spec
- Downloaded spec from DO Console
- Found: Worker section had NO `envs:` block at all
- Web service had envs, worker inherited nothing from app-level

### Attempt 4: Create corrected App Spec and upload to DO Console
- Created `app-spec-fixed.yaml` with all env vars for all components
- Uploaded via DO Console → Settings → App Spec
- New error: Health check failed with `DisallowedHost` (internal IP not in ALLOWED_HOSTS)

### Attempt 5: Set ALLOWED_HOSTS to "*"
- Changed `ALLOWED_HOSTS` to `*` for all components
- Health check passed
- New error: Redis connection failed

### Attempt 6: Fix Redis SSL
- Original settings used `ssl.CERT_REQUIRED`
- Upstash doesn't provide verifiable certs
- Changed to `ssl.CERT_NONE` in `benefits_navigator/settings.py`
- Pushed to repo

### Attempt 7: Debug worker env vars
- Changed worker `run_command` to: `/bin/sh -c 'echo "=== ENV VARS ===" && env | sort && sleep 300'`
- Result: Worker STILL showed the old Celery command in logs
- Confirmed DO is not picking up App Spec changes

## Current State

### What's Working
- Web component deploys and runs
- Health check passes (with `ALLOWED_HOSTS: "*"`)
- Database connection works
- Code changes from GitHub are deployed (Dockerfile, settings.py)

### What's Not Working
- Celery worker fails to start
- Latest error suggests Redis connection issue OR env vars still missing
- App Spec changes may not be applying

### The Corrected App Spec
File: `/Users/zachbeaudoin/projects/benefits-navigator/app-spec-fixed.yaml`

Key sections:
```yaml
workers:
- dockerfile_path: Dockerfile.prod
  envs:
  - key: DJANGO_SETTINGS_MODULE
    scope: RUN_AND_BUILD_TIME
    value: "benefits_navigator.settings"
  - key: DEBUG
    scope: RUN_AND_BUILD_TIME
    value: "False"
  - key: STAGING
    scope: RUN_AND_BUILD_TIME
    value: "True"
  - key: ALLOWED_HOSTS
    scope: RUN_AND_BUILD_TIME
    value: "*"
  - key: SECRET_KEY
    scope: RUN_AND_BUILD_TIME
    value: "your-secret-key-here"
  - key: DATABASE_URL
    scope: RUN_AND_BUILD_TIME
    value: "postgresql://user:password@host:port/dbname"
  - key: REDIS_URL
    scope: RUN_AND_BUILD_TIME
    value: "rediss://user:password@host:port"
  - key: CELERY_BROKER_URL
    scope: RUN_AND_BUILD_TIME
    value: "rediss://user:password@host:port"
  - key: FIELD_ENCRYPTION_KEY
    scope: RUN_AND_BUILD_TIME
    value: "your-fernet-encryption-key-here"
  - key: OPENAI_API_KEY
    scope: RUN_AND_BUILD_TIME
    value: ""
  github:
    branch: main
    deploy_on_push: true
    repo: Beaudoin0zach/benefits_navigator
  instance_count: 1
  instance_size_slug: basic-xxs
  name: worker
  run_command: celery -A benefits_navigator worker --loglevel info --concurrency 1
```

## Relevant Code

### Celery Configuration (settings.py)
```python
_redis_url = env('REDIS_URL', default='') or 'redis://localhost:6379/0'
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='') or _redis_url
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='') or _redis_url

# SSL for rediss:// connections
if CELERY_BROKER_URL.startswith('rediss://'):
    CELERY_BROKER_USE_SSL = {
        'ssl_cert_reqs': ssl.CERT_NONE,  # Changed from CERT_REQUIRED
    }
    CELERY_REDIS_BACKEND_USE_SSL = {
        'ssl_cert_reqs': ssl.CERT_NONE,
    }
```

### Celery App (celery.py)
```python
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'benefits_navigator.settings')
app = Celery('benefits_navigator')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
```

### Dockerfile.prod
```dockerfile
FROM python:3.11-slim
WORKDIR /app
# ... install deps ...
COPY . /app/

# collectstatic with build-time env vars
RUN SECRET_KEY=build-time-dummy-key \
    DEBUG=False \
    STAGING=False \
    FIELD_ENCRYPTION_KEY=dGhpcy1pcy1hLWR1bW15LWtleS1mb3ItYnVpbGQtb25seQ== \
    ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput --clear || true

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "benefits_navigator.wsgi:application"]
```

## Questions for Analysis

1. **Why might DO App Platform not be applying App Spec changes?**
   - Is there a caching issue?
   - Do we need to force a rebuild?
   - Is there a syntax issue in the YAML?

2. **Is the Celery SSL configuration correct for Upstash?**
   - We're using `ssl.CERT_NONE`
   - The URL is `rediss://` (TLS)
   - Should we add any other SSL options?

3. **Could there be an issue with how Celery loads Django settings?**
   - The worker uses `DJANGO_SETTINGS_MODULE=benefits_navigator.settings`
   - Settings requires `SECRET_KEY` to be present
   - If env var isn't there, it raises ValueError before Celery even starts

4. **Is there something special about DO App Platform workers vs services?**
   - Services get env vars fine
   - Workers seem to not inherit app-level envs
   - Even with explicit component-level envs, they might not work

5. **Should we try a different approach entirely?**
   - Separate Dockerfile for worker with CMD for Celery?
   - Different hosting for just the worker (DO Droplet, Railway, etc.)?
   - Embedded Celery in web process using `--pool=solo`?

## Latest Error
```
We took a deep dive into your logs and found a few things to check out.

- Failed to connect to redis broker
- Missing dependencies
- Incorrect environment variables
- Connection issues
```

The exact error message would be in DO Console → Runtime Logs → worker component.
