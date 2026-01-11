# VA Benefits Navigator

AI-powered assistance platform for VA disability claims and appeals.

## Overview

VA Benefits Navigator helps veterans navigate the complex VA benefits system through five core features:

1. **Claims Preparation Assistant** - Upload documents for AI-powered analysis and evidence gap identification
2. **C&P Exam Preparation** - Comprehensive guidance for Compensation & Pension exams with condition-specific guides
3. **Appeals Process Guidance** - Step-by-step workflow for VA appeals (HLR, Supplemental, Board)
4. **Journey Dashboard** - Track your claims journey with timeline, milestones, and deadlines
5. **VA Rating Calculator** - Accurate combined rating calculations using VA Math (38 CFR 4.25)

## Current Status

- **360 tests passing** across all apps
- Security middleware enabled (Audit logging, Security headers, CSP)
- Data retention policies implemented
- Soft-delete with recovery support

## Tech Stack

- **Backend**: Django 5.0, PostgreSQL, Celery, Redis
- **Frontend**: HTMX, Tailwind CSS
- **AI/ML**: OpenAI GPT-3.5-turbo, Tesseract OCR
- **Payments**: Stripe
- **Infrastructure**: Docker, AWS (S3, RDS, Elastic Beanstalk)

## Project Structure

```
benefits-navigator/
├── benefits_navigator/       # Main Django project
│   ├── settings.py          # Django settings (middleware, CSP, etc.)
│   ├── celery.py            # Celery configuration
│   └── urls.py              # Root URL configuration
├── accounts/                 # User authentication and profiles
│   ├── models.py            # User, UserProfile, Subscription
│   └── tests.py             # 28 tests
├── claims/                   # Document upload and AI analysis
│   ├── models.py            # Document, Claim (with soft-delete)
│   ├── tasks.py             # Celery tasks (OCR, cleanup, denial decoder)
│   ├── forms.py             # File validation with magic bytes & page count
│   └── tests.py             # 55 tests
├── appeals/                  # Appeals workflow
│   ├── models.py            # Appeal, AppealGuidance, AppealNote
│   └── tests.py             # 57 tests
├── examprep/                 # C&P exam preparation
│   ├── models.py            # ExamGuidance, ExamChecklist, EvidenceChecklist
│   ├── va_math.py           # VA combined rating calculator
│   └── tests.py             # 49 tests
├── core/                     # Shared utilities and base models
│   ├── models.py            # TimeStampedModel, SoftDeleteModel, AuditLog
│   ├── middleware.py        # AuditMiddleware, SecurityHeadersMiddleware
│   ├── journey.py           # TimelineBuilder for journey dashboard
│   ├── tasks.py             # Data retention enforcement
│   └── tests.py             # Core model tests
├── agents/                   # AI agents (M21 scraper, etc.)
├── templates/                # Django templates (HTMX-powered)
├── static/                   # Static files (Tailwind CSS)
├── media/                    # User uploads
├── docker-compose.yml        # Docker services configuration
├── Dockerfile                # Django app container
└── requirements.txt          # Python dependencies
```

## Prerequisites

- **Docker** and **Docker Compose** installed
- **Python 3.11+** (for local development without Docker)
- **OpenAI API key** (for document analysis)
- **Stripe API keys** (for subscription management)

## Quick Start

### 1. Clone and Setup

```bash
cd benefits-navigator

# Copy environment example
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

### 2. Configure Environment Variables

Edit `.env` and set the following:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-key-here
STRIPE_SECRET_KEY=sk_test_your-stripe-key-here
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-key-here

# Optional (defaults work for local development)
DEBUG=True
SECRET_KEY=your-secret-key-here
```

### 3. Build and Start with Docker

```bash
# Build and start all services
docker-compose up --build

# The application will be available at:
# - Web app: http://localhost:8000
# - Flower (Celery monitor): http://localhost:5555
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
```

### 4. Run Initial Setup

In a new terminal:

```bash
# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static files
docker-compose exec web python manage.py collectstatic --no-input
```

### 5. Access the Application

- **Main app**: http://localhost:8000
- **Django Admin**: http://localhost:8000/admin
- **Celery Flower**: http://localhost:5555

## Local Development (Without Docker)

If you prefer to run services locally:

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Tesseract OCR (for document processing)
# macOS:
brew install tesseract tesseract-lang

# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils

# Windows: Download installer from https://github.com/UB-Mannheim/tesseract/wiki
```

### 2. Start PostgreSQL and Redis

```bash
# Option A: Use Docker for databases only
docker-compose up db redis

# Option B: Install and run locally
# PostgreSQL: https://www.postgresql.org/download/
# Redis: https://redis.io/download
```

### 3. Run Django

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver

# In separate terminals, start Celery
celery -A benefits_navigator worker -l info
celery -A benefits_navigator beat -l info  # For scheduled tasks
```

## Database Models

### Accounts App

- **User** - Custom user model (email-based authentication)
- **UserProfile** - Extended profile (branch of service, disability rating, etc.)
- **Subscription** - Stripe subscription tracking

### Claims App

- **Document** - Uploaded documents with OCR and AI analysis results
- **Claim** - Optional grouping of documents (for organizing multiple docs per claim)

### Appeals App

- **Appeal** - Appeal case tracking (will integrate with Viewflow)

### Exam Prep App

- **ExamGuidance** - C&P exam preparation content
- **ExamChecklist** - User's personalized exam prep checklists

## Key Features & Architecture

### Asynchronous Document Processing

Documents are processed asynchronously using Celery:

1. User uploads document → saved to storage
2. Celery task triggered → OCR extraction (Tesseract)
3. AI analysis → OpenAI GPT-3.5-turbo analyzes extracted text
4. Results saved → user notified

```python
# Example task (to be implemented in Phase 2)
@shared_task
def process_document_task(document_id):
    document = Document.objects.get(id=document_id)
    # Run OCR
    text = ocr_service.extract_text(document.file)
    # Analyze with AI
    analysis = ai_service.analyze_document(text)
    # Save results
    document.ai_summary = analysis
    document.mark_completed()
```

### Feature Gating (Free vs Premium)

Settings for tier limits:

```python
# Free tier
FREE_TIER_DOCUMENTS_PER_MONTH = 3
FREE_TIER_MAX_STORAGE_MB = 100

# Premium tier
PREMIUM_UNLIMITED_DOCUMENTS = True
PREMIUM_GPT4_ACCESS = False  # Can enable for premium users
```

### Accessibility First

- WCAG AA compliant
- Semantic HTML
- Screen reader friendly
- Keyboard navigable
- High contrast color scheme

## Development Workflow

### Running Tests

```bash
# Run all tests
docker-compose exec web pytest

# Run with coverage
docker-compose exec web pytest --cov=. --cov-report=html

# Run specific app tests
docker-compose exec web pytest accounts/tests/
```

### Database Migrations

```bash
# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate

# View migration SQL
docker-compose exec web python manage.py sqlmigrate accounts 0001
```

### Django Shell

```bash
# Access Django shell
docker-compose exec web python manage.py shell_plus

# Example: Create a test user
from accounts.models import User
user = User.objects.create_user(email='test@example.com', password='testpass123')
```

### Code Quality

```bash
# Format code with Black
black .

# Lint with Ruff
ruff check .

# Type checking (if using mypy)
mypy .
```

## API Integrations

### OpenAI Configuration

```python
# settings.py
OPENAI_API_KEY = env('OPENAI_API_KEY')
OPENAI_MODEL = 'gpt-3.5-turbo'  # or 'gpt-4' for premium
OPENAI_MAX_TOKENS = 4000
```

### Stripe Configuration

```python
# settings.py
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')
STRIPE_PRICE_ID = env('STRIPE_PRICE_ID')  # Set in Stripe dashboard
```

## Deployment

### AWS Elastic Beanstalk (Recommended for MVP)

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init -p python-3.11 benefits-navigator

# Create environment
eb create benefits-nav-prod

# Deploy
eb deploy

# Set environment variables
eb setenv OPENAI_API_KEY=sk-xxx STRIPE_SECRET_KEY=sk-xxx
```

### Environment Variables for Production

```bash
DEBUG=False
SECRET_KEY=<generate-strong-secret-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://host:6379/0
USE_S3=True
AWS_STORAGE_BUCKET_NAME=your-bucket-name
SENTRY_DSN=https://xxx@sentry.io/xxx  # For error tracking
```

## Monitoring & Logging

### Celery Monitoring with Flower

Access at http://localhost:5555 to:
- Monitor active tasks
- View task history
- Inspect task details
- Manage workers

### Logs

```bash
# View logs
docker-compose logs -f web
docker-compose logs -f celery
docker-compose logs -f db

# Django logs
tail -f logs/django.log
```

### Sentry Integration

For production error tracking, configure Sentry:

```python
# settings.py
SENTRY_DSN = env('SENTRY_DSN', default='')
if SENTRY_DSN and not DEBUG:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration()],
    )
```

## Security Considerations

- **Sensitive Data**: VA file numbers, medical info encrypted at rest
- **File Uploads**: Validated by type, size limited to 50MB
- **API Keys**: Stored in environment variables, never committed
- **HTTPS**: Required in production
- **CSRF Protection**: Enabled on all forms
- **Rate Limiting**: Implemented on upload endpoints

## Next Steps

After foundation setup (current phase):

1. **Phase 2**: Implement document upload and AI analysis pipeline
2. **Phase 3**: Build C&P exam prep content and pages
3. **Phase 4**: Integrate Django-Viewflow for appeals workflow
4. **Phase 5**: Add Stripe subscription payment flow
5. **Phase 6**: Security audit and testing
6. **Phase 7**: Beta testing and launch

## Contributing

This is currently a solo project. Contribution guidelines TBD.

## License

Proprietary - All rights reserved

## Support

For issues or questions:
- Email: support@benefitsnavigator.com
- GitHub Issues: (to be added)

---

Built with ❤️ for veterans
