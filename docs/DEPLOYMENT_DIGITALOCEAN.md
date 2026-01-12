# Deploying to DigitalOcean App Platform

This guide covers deploying the Benefits Navigator to DigitalOcean App Platform for staging/production.

## Prerequisites

1. DigitalOcean account
2. GitHub repository connected to DigitalOcean
3. `doctl` CLI installed (optional, for command-line deployment)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  DigitalOcean App Platform              │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐   ┌─────────┐   ┌─────────────────────┐   │
│  │   Web   │   │ Worker  │   │  Managed PostgreSQL │   │
│  │ (Django)│   │ (Celery)│   │       (15)          │   │
│  └─────────┘   └─────────┘   └─────────────────────┘   │
│       │             │                   │               │
│       └─────────────┴───────────────────┘               │
│                     │                                   │
│              ┌──────┴──────┐                            │
│              │ Redis Cloud │  (External - free tier)   │
│              └─────────────┘                            │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Set Up Redis (Free Option)

DigitalOcean Managed Redis starts at $15/mo. For staging, use [Redis Cloud](https://redis.com/try-free/) free tier:

1. Sign up at redis.com
2. Create a free database (30MB)
3. Copy the connection URL: `redis://default:PASSWORD@HOST:PORT`

### 2. Deploy via DigitalOcean Console

1. Go to [DigitalOcean Apps](https://cloud.digitalocean.com/apps)
2. Click **Create App**
3. Connect your GitHub repo: `Beaudoin0zach/benefits_navigator`
4. Select branch: `main`
5. DigitalOcean will auto-detect the app spec in `.do/app.yaml`

### 3. Configure Environment Variables

In the App Settings, add these secrets:

| Variable | Value | Type |
|----------|-------|------|
| `SECRET_KEY` | Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` | Secret |
| `OPENAI_API_KEY` | Your OpenAI API key | Secret |
| `REDIS_URL` | Redis Cloud connection URL | Secret |
| `CELERY_BROKER_URL` | Same as REDIS_URL | Secret |
| `SENTRY_DSN` | Your Sentry DSN | Env Var |

### 4. Deploy via CLI (Alternative)

```bash
# Install doctl
brew install doctl

# Authenticate
doctl auth init

# Create app from spec
doctl apps create --spec .do/app.yaml

# List apps
doctl apps list

# Get app ID and deploy
doctl apps create-deployment <app-id>
```

## Post-Deployment Setup

### Run Migrations

```bash
# Via DigitalOcean Console
# Go to App > Console > web component
python manage.py migrate

# Or via doctl
doctl apps console <app-id> web
```

### Create Superuser

```bash
python manage.py createsuperuser
```

### Load Initial Data

```bash
python manage.py loaddata examprep/fixtures/*.json
python manage.py loaddata core/fixtures/supportive_messages.json
```

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key (generate unique for production) |
| `DEBUG` | Yes | Set to `False` for production |
| `ALLOWED_HOSTS` | Yes | App domain (auto-set by DO) |
| `DATABASE_URL` | Yes | PostgreSQL connection (auto-set by DO) |
| `REDIS_URL` | Yes | Redis connection URL |
| `CELERY_BROKER_URL` | Yes | Same as REDIS_URL |
| `OPENAI_API_KEY` | Yes | For AI document analysis |
| `SENTRY_DSN` | No | Error tracking |
| `STRIPE_*` | No | Payment processing (disable for staging) |

## Estimated Costs (Staging)

| Resource | Size | Monthly Cost |
|----------|------|--------------|
| Web Service | basic-xxs (512MB) | $5 |
| Worker Service | basic-xxs (512MB) | $5 |
| PostgreSQL | db-s-dev-database | $7 |
| Redis Cloud | Free tier (30MB) | $0 |
| **Total** | | **~$17/mo** |

## Scaling for Production

For production, upgrade:

```yaml
# In .do/app.yaml
services:
  - name: web
    instance_size_slug: basic-xs  # 1GB RAM
    instance_count: 2              # Multiple instances

  - name: worker
    instance_size_slug: basic-xs
    instance_count: 2

databases:
  - name: db
    size: db-s-1vcpu-1gb          # 1GB RAM, 10GB storage
```

## Health Checks

The app exposes `/health/` endpoint:

```bash
curl https://your-app.ondigitalocean.app/health/
# {"status": "healthy", "database": "ok"}
```

## Troubleshooting

### Build Fails

1. Check build logs in DigitalOcean console
2. Ensure `Dockerfile.prod` exists
3. Verify all dependencies in `requirements.txt`

### Database Connection Issues

1. Check `DATABASE_URL` is set correctly
2. Verify database is running (App > Database > Insights)
3. Run migrations: `python manage.py migrate`

### Static Files Not Loading

1. Ensure `collectstatic` runs during build
2. Check `whitenoise` is in MIDDLEWARE
3. Verify `STATIC_ROOT` and `STATIC_URL` settings

### Celery Worker Not Processing

1. Check worker logs in DigitalOcean console
2. Verify `CELERY_BROKER_URL` points to Redis
3. Test Redis connection: `redis-cli -u $REDIS_URL ping`

## Useful Commands

```bash
# View logs
doctl apps logs <app-id> --component web --follow

# SSH into container
doctl apps console <app-id> web

# Restart app
doctl apps create-deployment <app-id>

# Get app info
doctl apps get <app-id>
```
