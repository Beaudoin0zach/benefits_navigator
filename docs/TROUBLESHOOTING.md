# Troubleshooting Guide

Common issues and their solutions for the VA Benefits Navigator project.

## Docker Issues

### Docker Command Not Found

**Error:**
```
zsh: command not found: docker-compose
```

**Cause:** Docker Desktop not running or docker commands not in PATH

**Solution:**
```bash
# 1. Start Docker Desktop
open -a Docker

# 2. Wait for Docker to fully start (check menu bar icon)

# 3. Use full path to docker
/Applications/Docker.app/Contents/Resources/bin/docker compose up -d

# OR add to PATH permanently
echo 'export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

### Obsolete docker-compose.yml Version Field

**Error:**
```
WARN[0000] the attribute 'version' is obsolete, it will be ignored
```

**Cause:** Modern Docker Compose doesn't require version field

**Solution:**
Remove the `version: '3.9'` line from the top of `docker-compose.yml`

**Fixed in:** `docker-compose.yml` (line 1 removed)

---

### Invalid Healthcheck Format

**Error:**
```
service "db" has neither an image nor a build context specified: invalid compose project
healthcheck.test must start either by "CMD", "CMD-SHELL" or "NONE"
```

**Cause:** Used `CMD-FAIL` instead of `CMD` in healthcheck test

**Solution:**
Change healthcheck format in `docker-compose.yml`:

```yaml
# Before (incorrect)
healthcheck:
  test: ["CMD-FAIL", "pg_isready", "-U", "benefits_user"]

# After (correct)
healthcheck:
  test: ["CMD", "pg_isready", "-U", "benefits_user", "-d", "benefits_navigator"]
```

**Fixed in:** `docker-compose.yml:15`

---

### Port Already in Use

**Error:**
```
Error response from daemon: Ports are not available: exposing port TCP 0.0.0.0:8000 -> 0.0.0.0:0: listen tcp 0.0.0.0:8000: bind: address already in use
```

**Cause:** Another process is using the port

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill the process
kill -9 [PID]

# Or change port in docker-compose.yml
# services:
#   web:
#     ports:
#       - "8001:8000"  # Use 8001 instead of 8000
```

---

### Container Fails to Start

**Error:**
```
Container benefits_nav_web exited with code 1
```

**Cause:** Various reasons (dependency issues, syntax errors, etc.)

**Solution:**
```bash
# Check logs for specific error
docker compose logs web

# Common fixes:
# 1. Rebuild container
docker compose up --build -d

# 2. Clear volumes and restart
docker compose down -v
docker compose up -d

# 3. Check requirements.txt for conflicts
docker compose exec web pip list
```

---

## Python Dependency Issues

### Stripe Version Conflict

**Error:**
```
ERROR: Cannot install stripe==8.2.0 and dj-stripe==2.8.3 because these package versions have conflicting dependencies.

The conflict is caused by:
    dj-stripe 2.8.3 depends on stripe<5.0.0 and >=3.0.0
```

**Cause:** dj-stripe 2.8.3 requires stripe<5.0.0, but requirements.txt had 8.2.0

**Solution:**
Change `stripe==8.2.0` to `stripe==4.2.0` in `requirements.txt:31`

```bash
# Rebuild container with updated requirements
docker compose up --build -d
```

**Fixed in:** `requirements.txt:31`

---

### Missing django-celery-beat

**Error:**
```
ModuleNotFoundError: No module named 'django_celery_beat'
```

**Cause:** Package listed in INSTALLED_APPS but not in requirements.txt

**Solution:**
Add `django-celery-beat==2.6.0` to `requirements.txt`

**Note:** Version 2.5.0 doesn't support Django 5.0, use 2.6.0+

```bash
# Rebuild container
docker compose up --build -d
```

**Fixed in:** `requirements.txt:14`

---

### Package Installation Fails

**Error:**
```
ERROR: Could not find a version that satisfies the requirement [package]
```

**Cause:** Package version doesn't exist or is incompatible

**Solution:**
```bash
# Check available versions
pip index versions [package]

# Update requirements.txt with compatible version
# Then rebuild
docker compose up --build -d
```

---

## Database & Migration Issues

### Migration Dependency Error

**Error:**
```
ValueError: Dependency on app with no migrations: accounts
```

**Cause:** ExamPrep migrations depend on accounts app, but accounts has no initial migration

**Solution:**
```bash
# Generate migrations for ALL apps first
docker compose exec web python manage.py makemigrations

# Then apply all migrations
docker compose exec web python manage.py migrate
```

**Best Practice:** Always run `makemigrations` without app name first to catch all changes

---

### Migration Conflict

**Error:**
```
Conflicting migrations detected
```

**Cause:** Multiple developers or branches created migrations for same app

**Solution:**
```bash
# Show migration graph
docker compose exec web python manage.py showmigrations

# Option 1: Delete conflicting migration files and remake
rm accounts/migrations/0002_*.py
docker compose exec web python manage.py makemigrations

# Option 2: Merge migrations
docker compose exec web python manage.py makemigrations --merge
```

---

### Database Connection Failed

**Error:**
```
django.db.utils.OperationalError: FATAL: password authentication failed for user "benefits_user"
```

**Cause:** Database credentials mismatch or database not ready

**Solution:**
```bash
# 1. Verify containers are healthy
docker compose ps

# 2. Check database logs
docker compose logs db

# 3. Verify environment variables match
# In docker-compose.yml, ensure web and db service credentials match

# 4. Restart database
docker compose restart db

# 5. If persistent, recreate database
docker compose down -v
docker compose up -d
```

---

### Can't Drop Tables

**Error:**
```
django.db.utils.OperationalError: cannot drop table because other objects depend on it
```

**Cause:** Foreign key relationships prevent table deletion

**Solution:**
```bash
# Nuclear option: Reset entire database
docker compose down -v
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

---

## Authentication Issues

### Superuser Creation Missing Username

**Error:**
```
TypeError: UserManager.create_superuser() missing 1 required positional argument: 'username'
```

**Cause:** Custom User model uses email as USERNAME_FIELD but didn't have custom UserManager

**Solution:**
Implement custom UserManager in `accounts/models.py`:

```python
from django.contrib.auth.models import AbstractUser, BaseUserManager

class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with email and password"""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with email and password"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    # ... existing fields ...

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # Use custom manager
    objects = UserManager()
```

Then create and apply migration:
```bash
docker compose exec web python manage.py makemigrations accounts
docker compose exec web python manage.py migrate
```

**Fixed in:** `accounts/models.py:13-38`, `accounts/models.py:58`

---

### Can't Login to Admin

**Error:** "Please enter the correct email address and password"

**Cause:** Various reasons

**Solution:**
```bash
# 1. Verify superuser exists
docker compose exec web python manage.py shell
>>> from accounts.models import User
>>> User.objects.filter(is_superuser=True)

# 2. Reset password
docker compose exec web python manage.py changepassword your@email.com

# 3. Create new superuser
docker compose exec web python manage.py createsuperuser

# 4. Check is_staff and is_superuser flags
>>> user = User.objects.get(email='your@email.com')
>>> user.is_staff = True
>>> user.is_superuser = True
>>> user.save()
```

---

## URL & Routing Issues

### Page Not Found (404)

**Error:**
```
Page not found (404)
The empty path didn't match any of these.
```

**Cause:** No URL pattern defined for requested path

**Solution:**
1. Check which URL is being accessed
2. Add URL pattern to appropriate `urls.py`

**Example - Home Page:**
```python
# benefits_navigator/urls.py
from core import views

urlpatterns = [
    path('', views.home, name='home'),  # Add this
    # ... other patterns
]
```

**Fixed in:** `benefits_navigator/urls.py:14`

---

### Reverse URL Not Found

**Error:**
```
django.urls.exceptions.NoReverseMatch: Reverse for 'home' not found
```

**Cause:** URL name doesn't exist or namespace is wrong

**Solution:**
```python
# Check URL configuration
docker compose exec web python manage.py show_urls

# Verify url name in urls.py
# In template, use correct namespace:
{% url 'examprep:guide_list' %}  # With namespace
{% url 'home' %}                  # Without namespace
```

---

## Template Issues

### Template Not Found

**Error:**
```
django.template.exceptions.TemplateDoesNotExist: core/home.html
```

**Cause:** Template file doesn't exist or not in template directory

**Solution:**
```bash
# 1. Verify template exists
ls -la templates/core/home.html

# 2. Check TEMPLATES setting in settings.py
# Ensure 'DIRS': [BASE_DIR / 'templates'],

# 3. Restart Django
docker compose restart web
```

---

### Static Files Not Loading

**Error:** CSS/JS files return 404

**Cause:** Static files not collected or STATIC_URL misconfigured

**Solution:**
```bash
# In development, ensure django.contrib.staticfiles is in INSTALLED_APPS

# Check settings.py
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Collect static files (production)
docker compose exec web python manage.py collectstatic

# Check WhiteNoise is configured (already done in this project)
```

---

## Permission Issues

### Permission Denied (File System)

**Error:**
```
PermissionError: [Errno 13] Permission denied: '/app/media/documents/...'
```

**Cause:** Container doesn't have write permissions

**Solution:**
```bash
# Fix media directory permissions
docker compose exec web mkdir -p /app/media
docker compose exec web chmod -R 777 /app/media

# Or in docker-compose.yml, add volume mount:
volumes:
  - media_files:/app/media
```

---

### Permission Denied (Database)

**Error:**
```
FATAL: role "benefits_user" does not exist
```

**Cause:** Database user not created

**Solution:**
```bash
# Database should be created automatically by docker-compose.yml
# If not, recreate containers:
docker compose down -v
docker compose up -d

# Verify database is healthy:
docker compose ps
```

---

## Celery Issues

### Celery Worker Not Starting

**Error:**
```
kombu.exceptions.OperationalError: Error 111 connecting to redis:6379. Connection refused.
```

**Cause:** Redis not running or not accessible

**Solution:**
```bash
# 1. Check Redis is running
docker compose ps redis

# 2. Test Redis connection
docker compose exec redis redis-cli ping
# Should return PONG

# 3. Restart Redis and Celery
docker compose restart redis celery

# 4. Check Celery logs
docker compose logs celery
```

---

### Tasks Not Executing

**Error:** Tasks submitted but never run

**Cause:** Celery worker not processing tasks

**Solution:**
```bash
# 1. Check Celery worker is running
docker compose ps celery

# 2. Check Celery logs
docker compose logs -f celery

# 3. Verify task is registered
docker compose exec celery celery -A benefits_navigator inspect registered

# 4. Restart worker
docker compose restart celery
```

---

## Common Development Issues

### Import Error After Adding New Model

**Error:**
```
ImportError: cannot import name 'NewModel' from 'app.models'
```

**Cause:** Django development server hasn't reloaded

**Solution:**
```bash
# Restart Django
docker compose restart web

# Or touch any Python file to trigger reload
docker compose exec web touch benefits_navigator/settings.py
```

---

### Changes Not Appearing

**Symptom:** Code changes don't show in browser

**Solution:**
```bash
# 1. Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)

# 2. Clear browser cache

# 3. Check docker volume mount
docker compose ps
# Ensure volume: .:/app is present

# 4. Restart container
docker compose restart web
```

---

## Performance Issues

### Slow Page Load

**Symptom:** Pages take 5+ seconds to load

**Cause:** N+1 queries, missing indexes, or large datasets

**Solution:**
```bash
# 1. Enable Django Debug Toolbar (already in dev)

# 2. Check query count
docker compose exec web python manage.py shell
>>> from django.db import connection
>>> from django.test.utils import override_settings
>>> with override_settings(DEBUG=True):
...     # Run your view code
...     print(len(connection.queries))

# 3. Use select_related and prefetch_related
ExamGuidance.objects.select_related('exam_guide').prefetch_related('related_conditions')

# 4. Add database indexes
class Meta:
    indexes = [
        models.Index(fields=['category', '-created_at']),
    ]
```

---

## Getting Help

If you encounter an issue not covered here:

1. **Check Logs:**
   ```bash
   # All services
   docker compose logs -f

   # Specific service
   docker compose logs -f web
   ```

2. **Django Shell:**
   ```bash
   docker compose exec web python manage.py shell
   # Test imports, query database, etc.
   ```

3. **Database Inspection:**
   ```bash
   docker compose exec db psql -U benefits_user -d benefits_navigator
   ```

4. **Review Recent Changes:**
   ```bash
   git log --oneline -10
   git diff HEAD~1
   ```

5. **Check Documentation:**
   - [PROJECT_STATUS.md](./PROJECT_STATUS.md)
   - [DEVELOPMENT_SETUP.md](./DEVELOPMENT_SETUP.md)
   - [PHASE_3_EXAM_PREP.md](./PHASE_3_EXAM_PREP.md)

## Prevention Tips

1. **Always run migrations after pulling:**
   ```bash
   docker compose exec web python manage.py migrate
   ```

2. **Rebuild after requirements.txt changes:**
   ```bash
   docker compose up --build -d
   ```

3. **Use git branches for experimental work:**
   ```bash
   git checkout -b feature/new-feature
   ```

4. **Commit working state frequently:**
   ```bash
   git add .
   git commit -m "Working state: Phase 3 foundation complete"
   ```

5. **Keep Docker Desktop running:**
   - Docker containers need Docker daemon active
