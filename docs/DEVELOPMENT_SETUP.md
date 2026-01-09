# Development Setup Guide

Complete guide to setting up the VA Benefits Navigator development environment.

## Prerequisites

- **Docker Desktop** - Must be installed and running
- **Python 3.11+** - For local development (optional)
- **Git** - For version control

## Quick Start

### 1. Start Docker Desktop

```bash
# Open Docker Desktop on macOS
open -a Docker

# Wait for Docker to fully start (check menu bar icon)
```

### 2. Start All Services

```bash
# Navigate to project directory
cd /Users/zachbeaudoin/benefits-navigator

# Start all containers (use full path on macOS)
/Applications/Docker.app/Contents/Resources/bin/docker compose up -d

# Or add Docker to PATH first (optional)
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
docker compose up -d
```

### 3. Check Container Status

```bash
docker compose ps

# You should see 5 running containers:
# - benefits_nav_db (PostgreSQL)
# - benefits_nav_redis (Redis)
# - benefits_nav_web (Django)
# - benefits_nav_celery (Celery worker)
# - benefits_nav_celery_beat (Celery scheduler)
# - benefits_nav_flower (Celery monitoring)
```

### 4. Run Migrations

```bash
# Apply all database migrations
docker compose exec web python manage.py migrate
```

### 5. Create Superuser

```bash
# Create admin user
docker compose exec web python manage.py createsuperuser

# Enter your email (e.g., Beaudoin0zach@gmail.com)
# Set a secure password
# Username field can be left blank (uses email)
```

### 6. Access the Application

- **Home:** http://127.0.0.1:8000/
- **Admin:** http://127.0.0.1:8000/admin/
- **Flower:** http://127.0.0.1:5555/

## Docker Commands Reference

### Starting & Stopping

```bash
# Start all services
docker compose up -d

# Stop all services (preserves data)
docker compose down

# Stop and remove volumes (⚠️ deletes database)
docker compose down -v

# Restart a specific service
docker compose restart web
```

### Viewing Logs

```bash
# View logs for all services
docker compose logs -f

# View logs for specific service
docker compose logs -f web

# View last 100 lines
docker compose logs --tail=100 web
```

### Running Commands

```bash
# Django management commands
docker compose exec web python manage.py [command]

# Examples:
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py shell
docker compose exec web python manage.py collectstatic

# Access Django shell
docker compose exec web python manage.py shell

# Access PostgreSQL
docker compose exec db psql -U benefits_user -d benefits_navigator

# Access Redis CLI
docker compose exec redis redis-cli
```

### Rebuilding After Changes

```bash
# Rebuild containers after requirements.txt changes
docker compose up --build -d

# Force complete rebuild
docker compose build --no-cache
docker compose up -d
```

## Environment Variables

The project uses environment variables defined in `docker-compose.yml` for development. For production, create a `.env` file:

```env
# Django
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# Redis & Celery
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# OpenAI
OPENAI_API_KEY=your-openai-key

# Stripe
STRIPE_PUBLISHABLE_KEY=your-publishable-key
STRIPE_SECRET_KEY=your-secret-key
STRIPE_WEBHOOK_SECRET=your-webhook-secret

# AWS S3 (for production file storage)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

## Database Management

### Creating Migrations

```bash
# Auto-detect model changes
docker compose exec web python manage.py makemigrations

# Create migration for specific app
docker compose exec web python manage.py makemigrations accounts

# Show migration SQL without applying
docker compose exec web python manage.py sqlmigrate accounts 0001
```

### Viewing Migrations

```bash
# Show all migrations and their status
docker compose exec web python manage.py showmigrations

# Show unapplied migrations
docker compose exec web python manage.py showmigrations --plan
```

### Resetting Database

```bash
# ⚠️ WARNING: This deletes all data

# Stop services and remove volumes
docker compose down -v

# Start services (creates fresh database)
docker compose up -d

# Apply migrations
docker compose exec web python manage.py migrate

# Create new superuser
docker compose exec web python manage.py createsuperuser
```

## Testing

```bash
# Run all tests
docker compose exec web pytest

# Run with coverage
docker compose exec web pytest --cov

# Run specific test file
docker compose exec web pytest claims/tests/test_models.py

# Run specific test
docker compose exec web pytest claims/tests/test_models.py::TestClaimModel::test_creation
```

## Static Files

```bash
# Collect static files (for production)
docker compose exec web python manage.py collectstatic --noinput

# Development uses WhiteNoise - no collection needed
```

## Celery Task Management

### Monitoring with Flower

Access Flower dashboard at http://127.0.0.1:5555/

### Running Tasks Manually

```bash
# Access Django shell
docker compose exec web python manage.py shell

# Import and run task
from claims.tasks import analyze_document_task
result = analyze_document_task.delay(document_id=1)
print(result.id)
```

### Viewing Task Logs

```bash
# Celery worker logs
docker compose logs -f celery

# Celery beat logs (scheduled tasks)
docker compose logs -f celery-beat
```

## Troubleshooting

### Docker Not Found

**Error:** `zsh: command not found: docker-compose`

**Solution:**
```bash
# Use full path
/Applications/Docker.app/Contents/Resources/bin/docker compose

# Or add to PATH
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
```

### Port Already in Use

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:**
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 [PID]

# Or change port in docker-compose.yml
# ports:
#   - "8001:8000"
```

### Database Connection Failed

**Error:** `FATAL: password authentication failed`

**Solution:**
```bash
# Ensure containers are healthy
docker compose ps

# Check database logs
docker compose logs db

# Restart database
docker compose restart db

# If persistent, recreate database
docker compose down -v
docker compose up -d
```

### Permission Errors

**Error:** `Permission denied` when accessing files

**Solution:**
```bash
# Fix file permissions
chmod -R 755 /Users/zachbeaudoin/benefits-navigator

# Fix media directory
docker compose exec web mkdir -p /app/media
docker compose exec web chmod -R 777 /app/media
```

## Development Tips

### Hot Reload

Django's development server automatically reloads when you change Python files. No need to restart the container.

### Installing New Packages

1. Add package to `requirements.txt`
2. Rebuild container:
   ```bash
   docker compose up --build -d
   ```

### Accessing Django Admin

1. Create superuser (see above)
2. Visit http://127.0.0.1:8000/admin/
3. Login with your email and password

### Database Inspection

```bash
# Access PostgreSQL
docker compose exec db psql -U benefits_user -d benefits_navigator

# List tables
\dt

# Describe table
\d accounts_user

# Query data
SELECT * FROM accounts_user;

# Exit
\q
```

## IDE Setup

### VS Code

Recommended extensions:
- Python
- Django
- Docker
- Pylance

### PyCharm

Configure Python interpreter:
1. Settings → Project → Python Interpreter
2. Add Docker Compose interpreter
3. Service: `web`

## Common Tasks Checklist

- [ ] Docker Desktop running
- [ ] Containers started: `docker compose up -d`
- [ ] Migrations applied: `docker compose exec web python manage.py migrate`
- [ ] Superuser created
- [ ] Access http://127.0.0.1:8000/ successfully
- [ ] Access http://127.0.0.1:8000/admin/ successfully

## Next Steps

Once setup is complete:
1. Review [PROJECT_STATUS.md](./PROJECT_STATUS.md) for current state
2. Check [PHASE_3_EXAM_PREP.md](./PHASE_3_EXAM_PREP.md) for Phase 3 details
3. Add content via Django admin
4. Review [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) if issues arise
