# Quick Start Guide - Benefits Navigator

## What We've Built

✅ **Complete Django Project Structure** with 5 modular apps (accounts, claims, appeals, examprep, core)
✅ **Docker Compose Setup** for local development (PostgreSQL, Redis, Celery)
✅ **360 Tests Passing** across all apps
✅ **Security Middleware** enabled (Audit logging, Security headers, CSP)
✅ **Data Retention Policies** with soft-delete and recovery support
✅ **Journey Dashboard** for tracking claims and appeals timeline

## Start Development in 3 Steps

### Step 1: Add Your API Keys

Edit `.env` file and add:
```bash
OPENAI_API_KEY=sk-your-key-here
STRIPE_SECRET_KEY=sk_test_your-key-here
STRIPE_PUBLISHABLE_KEY=pk_test_your-key-here
```

### Step 2: Start Services

```bash
cd benefits-navigator

# Build and start all services
docker-compose up --build

# Wait for services to start (~30 seconds)
```

### Step 3: Run Initial Setup

In a new terminal:
```bash
# Run database migrations
docker-compose exec web python manage.py migrate

# Create admin user
docker-compose exec web python manage.py createsuperuser

# Create a Site object (required for django-allauth)
docker-compose exec web python manage.py shell -c "from django.contrib.sites.models import Site; Site.objects.get_or_create(id=1, defaults={'domain': 'localhost:8000', 'name': 'VA Benefits Navigator'})"
```

## Access Your Application

- **Main App**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin (use superuser credentials)
- **Celery Monitor (Flower)**: http://localhost:5555
- **Database**: localhost:5432 (user: benefits_user, password: benefits_dev_password_123)
- **Redis**: localhost:6379

## What's Working Now

### Core Features
- ✅ Document Upload & AI Analysis (OCR + OpenAI)
- ✅ C&P Exam Guides (4 guides) with interactive checklists
- ✅ VA Glossary (46 terms)
- ✅ VA Rating Calculator (38 CFR § 4.25 compliant)
- ✅ Appeals System with workflow tracking
- ✅ Journey Dashboard (claims + appeals timeline)
- ✅ User Dashboard with stats and quick actions

### Infrastructure
- ✅ PostgreSQL database with soft-delete support
- ✅ Redis caching and message broker
- ✅ Celery worker for background tasks (OCR, cleanup, data retention)
- ✅ Celery beat for scheduled tasks
- ✅ Admin interface for managing all data
- ✅ Audit logging middleware
- ✅ Security headers middleware (CSP, X-Frame-Options, etc.)

### Security
- ✅ Content-Security-Policy headers
- ✅ Rate limiting on auth views (5/min login, 3/hr signup)
- ✅ Magic byte file validation
- ✅ PDF page count validation (max 100 pages)
- ✅ Secure cookies in production

## Next Development Steps

### High Priority
1. Add more exam guides (TBI, Sleep Apnea)
2. Set up email notifications
3. SMC calculator
4. PDF export for calculations

### Future Phases
- **Stripe subscription flow** - Payment processing
- **AI chat assistant** - Interactive help
- **Mobile optimization** - Responsive design improvements

## Useful Commands

### Django Management

```bash
# Make migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# Django shell
docker-compose exec web python manage.py shell_plus

# Run tests (360 tests)
docker-compose exec web pytest
```

### Docker Management

```bash
# View logs
docker-compose logs -f web
docker-compose logs -f celery

# Restart service
docker-compose restart web

# Rebuild after requirements.txt changes
docker-compose up --build

# Stop all services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v
```

### Database

```bash
# Access PostgreSQL
docker-compose exec db psql -U benefits_user -d benefits_navigator

# Backup database
docker-compose exec db pg_dump -U benefits_user benefits_navigator > backup.sql

# Restore database
docker-compose exec -T db psql -U benefits_user benefits_navigator < backup.sql
```

## Common Issues & Solutions

### Issue: Port already in use

```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process or change port in docker-compose.yml
```

### Issue: Database connection error

```bash
# Ensure database is healthy
docker-compose ps

# Restart database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### Issue: Migrations not applying

```bash
# Try fake migrations if needed
docker-compose exec web python manage.py migrate --fake

# Or reset database (WARNING: loses all data)
docker-compose down -v
docker-compose up -d db
docker-compose exec web python manage.py migrate
```

### Issue: Static files not loading

```bash
# Collect static files
docker-compose exec web python manage.py collectstatic --no-input

# Check STATIC_ROOT setting
docker-compose exec web python manage.py findstatic admin/css/base.css
```

## Testing the Foundation

### Create a Test User via Django Shell

```bash
docker-compose exec web python manage.py shell_plus
```

```python
# In the shell:
from accounts.models import User

# Create user
user = User.objects.create_user(
    email='veteran@example.com',
    password='testpass123',
    first_name='John',
    last_name='Doe'
)

# Update profile
user.profile.branch_of_service = 'army'
user.profile.disability_rating = 30
user.profile.save()

# Check subscription (should be auto-created with free tier)
print(user.subscription)
print(f"Is premium: {user.is_premium}")  # Should be False
```

### Create Test Document (No file yet, just model)

```python
from claims.models import Document

doc = Document.objects.create(
    user=user,
    file_name='test_medical_record.pdf',
    document_type='medical_records',
    status='completed',
    file_size=1024000,
    ocr_text='Sample extracted text...',
)
```

## Project File Structure Overview

```
benefits-navigator/
├── benefits_navigator/          # Main project settings
│   ├── __init__.py             # Celery app import
│   ├── settings.py             # ✅ Comprehensive Django settings
│   ├── celery.py               # ✅ Celery configuration
│   ├── urls.py                 # Root URLs (to be expanded)
│   └── wsgi.py                 # WSGI application
│
├── accounts/                    # ✅ User management
│   ├── models.py               # User, UserProfile, Subscription
│   ├── admin.py                # Admin configuration
│   └── apps.py
│
├── claims/                      # ✅ Document analysis
│   ├── models.py               # Document, Claim
│   ├── admin.py                # Admin configuration
│   └── apps.py
│
├── appeals/                     # ✅ Appeals workflow
│   ├── models.py               # Appeal (Viewflow TBD)
│   ├── admin.py
│   └── apps.py
│
├── examprep/                    # ✅ C&P exam prep
│   ├── models.py               # ExamGuidance, ExamChecklist
│   ├── admin.py
│   └── apps.py
│
├── core/                        # ✅ Shared utilities
│   ├── models.py               # Base models
│   ├── context_processors.py  # Template context
│   └── apps.py
│
├── templates/                   # Django templates (to be built)
├── static/                      # Static files (CSS, JS)
├── media/                       # User uploads
├── logs/                        # Application logs
│
├── docker-compose.yml          # ✅ Docker services
├── Dockerfile                   # ✅ Django container
├── requirements.txt             # ✅ Python dependencies
├── .env                         # Environment variables
├── .gitignore                   # Git ignore rules
└── README.md                    # ✅ Full documentation
```

## What to Do Next

1. **Test the foundation**: Start Docker and verify all services are running
2. **Create admin user**: Access Django admin and explore the models
3. **Review IMPLEMENTATION_PLAN.md**: Detailed 16-week development roadmap
4. **Start Phase 2**: Begin building the document upload and AI analysis feature

## Questions to Answer Before Phase 2

Refer to `IMPLEMENTATION_PLAN.md` for 23 detailed questions, but the critical ones are:

1. **Pricing Strategy**: What should free tier limits be? (I suggest: 3 documents/month)
2. **AI Analysis Format**: What structured output should OpenAI provide? (see plan for example)
3. **Document Types**: Are the current options sufficient? (medical, service records, decision letters, etc.)
4. **OCR Strategy**: Start with Tesseract (free) or AWS Textract ($0.0015/page)?

---

**You now have a complete Django foundation ready for feature development!** 🎉

Next step: Review the implementation plan and start building Phase 2 (document upload pipeline).
