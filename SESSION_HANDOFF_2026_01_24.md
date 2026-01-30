# Session Handoff - January 24, 2026

## What Was Accomplished This Session

### 1. Pilot Mode Implementation (Goals #1 & #2) ✅
**Files Modified:**
- `benefits_navigator/settings.py` - Added pilot mode settings
- `accounts/models.py` - Updated `is_premium` to check pilot mode, added `is_pilot_user`
- `accounts/views.py` - Blocked checkout when `PILOT_BILLING_DISABLED=True`
- `accounts/tests.py` - Added 10+ pilot mode tests
- `core/context_processors.py` - Added `pilot_mode` context processor
- `examprep/views.py` - Added premium gate to `save_calculation`
- `templates/accounts/upgrade.html` - Pilot mode UI
- `.env.example` - Documented new env vars

**New Settings:**
```python
PILOT_MODE = env.bool('PILOT_MODE', default=False)
PILOT_BILLING_DISABLED = env.bool('PILOT_BILLING_DISABLED', default=PILOT_MODE)
PILOT_PREMIUM_ACCESS = env.bool('PILOT_PREMIUM_ACCESS', default=False)
PILOT_PREMIUM_DOMAINS = env.list('PILOT_PREMIUM_DOMAINS', default=[])
PILOT_PREMIUM_EMAILS = env.list('PILOT_PREMIUM_EMAILS', default=[])
PILOT_DATA_RETENTION_DAYS = env.int('PILOT_DATA_RETENTION_DAYS', default=30)
```

### 2. 30-Day Data Retention (Goal #3) ✅
**Files Modified:**
- `core/tasks.py` - Added `enforce_pilot_data_retention()` and `notify_pilot_users_before_retention()`

### 3. Admin Stats Dashboard (Goal #4) ✅
**Files Created/Modified:**
- `core/views.py` - Added `admin_stats_dashboard` view
- `core/urls.py` - Added `/admin/stats/` route
- `templates/core/admin_stats.html` - New dashboard template

**Access:** http://localhost:8000/admin/stats/ (staff only)

### 4. Local Dev Environment
- Docker Compose running
- All migrations applied
- Admin user created: `admin@example.com` / `admin123`

---

## Current Deployment Issue

**Problem:** Celery worker failing on DigitalOcean with "Non-Zero Exit Code"

**Cause:** Missing Redis connection. User's Redis Cloud instance went inactive.

**Solution Options:**
1. Reactivate Redis Cloud at cloud.redis.io
2. Create new Redis at Upstash (free, no inactivity timeout)
3. Add DigitalOcean Managed Redis ($15/mo)

**Then in DigitalOcean App Settings → Worker component, set:**
- `REDIS_URL` = your redis URL (e.g., `rediss://default:password@host:port`)
- `CELERY_BROKER_URL` = same as REDIS_URL

---

## Domain Setup (In Progress)

**Domain:** `vabenefitsnavigator.org` (at Cloudflare)

**DNS Setup Needed:**
1. In DO App: Add domain in Settings → Domains
2. In Cloudflare: Add CNAME record pointing to DO app URL
3. Update `ALLOWED_HOSTS` in `.do/app.yaml`

---

## Environment Variables Needed in DigitalOcean

| Variable | Status | Notes |
|----------|--------|-------|
| `SECRET_KEY` | Set | |
| `DATABASE_URL` | Set | |
| `REDIS_URL` | **NEEDS UPDATE** | Reactivate Redis first |
| `CELERY_BROKER_URL` | **NEEDS UPDATE** | Same as REDIS_URL |
| `OPENAI_API_KEY` | Set | |
| `FIELD_ENCRYPTION_KEY` | **ADD THIS** | `VcnpAwo25DTRbmRcGfYJAIXkTjATUj4IR_jgHomIR7Q=` (or generate new) |
| `SENTRY_DSN` | Set | |
| `ALLOWED_HOSTS` | **UPDATE** | Add `vabenefitsnavigator.org` |

---

## Remaining Launch Goals

- [ ] Fix Redis/Celery deployment issue
- [ ] Complete domain connection
- [ ] Update ALLOWED_HOSTS for new domain
- [ ] Test pilot mode on staging
- [ ] Recruit test users

---

## Quick Commands

```bash
# Start local dev
docker compose up -d

# Check logs
docker compose logs -f web

# Run tests
docker compose exec web pytest

# Generate new encryption key
docker compose exec web python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Files Changed This Session

```
benefits_navigator/settings.py
accounts/models.py
accounts/views.py
accounts/tests.py
core/context_processors.py
core/views.py
core/urls.py
core/tasks.py
examprep/views.py
templates/accounts/upgrade.html
templates/core/admin_stats.html (new)
.env.example
.do/app.yaml (may need ALLOWED_HOSTS update)
```
