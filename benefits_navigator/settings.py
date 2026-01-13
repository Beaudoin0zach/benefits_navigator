"""
Django settings for benefits_navigator project.
"""

import os
from pathlib import Path
import environ

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, True),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1', '0.0.0.0']),
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Read .env file if it exists
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
# In production, this MUST be set via environment variable
# For staging, we allow a default key if DO Console fails to pass secrets
STAGING_FALLBACK_KEY = '***ROTATED_FALLBACK_KEY***'
SECRET_KEY = env('SECRET_KEY', default='') or STAGING_FALLBACK_KEY

import warnings
if not SECRET_KEY or SECRET_KEY == STAGING_FALLBACK_KEY or SECRET_KEY.startswith('django-insecure'):
    if not env.bool('DEBUG', default=False) and not env.bool('STAGING', default=False):
        raise ValueError("SECRET_KEY must be set in production!")
    warnings.warn("Using insecure SECRET_KEY - set SECRET_KEY in .env for production")
    SECRET_KEY = STAGING_FALLBACK_KEY  # Ensure we have a valid key

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

# ALLOWED_HOSTS - special handling for staging/production
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# In staging mode, allow all hosts to handle DO App Platform internal IPs
if env.bool('STAGING', default=False):
    ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',

    # Third-party apps
    'django_htmx',
    'widget_tweaks',
    'crispy_forms',
    'crispy_tailwind',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'django_celery_beat',
    'django_extensions',
    'viewflow',  # Workflow engine for appeals
    'strawberry.django',  # GraphQL API

    # Our apps
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'claims.apps.ClaimsConfig',
    'appeals.apps.AppealsConfig',
    'examprep.apps.ExamprepConfig',
    'agents.apps.AgentsConfig',
    'documentation.apps.DocumentationConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',  # HTMX support
    'allauth.account.middleware.AccountMiddleware',  # Django-allauth
    'core.middleware.AuditMiddleware',  # Audit logging for sensitive operations
    'core.middleware.SecurityHeadersMiddleware',  # Additional security headers
    'csp.middleware.CSPMiddleware',  # Content Security Policy
]

ROOT_URLCONF = 'benefits_navigator.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_settings',  # Site settings
                'core.context_processors.user_usage',  # User usage tracking
                'core.context_processors.tier_limits',  # Tier limit settings
                'core.context_processors.feature_flags',  # Feature flags for dual-path
            ],
        },
    },
]

WSGI_APPLICATION = 'benefits_navigator.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Password hashers - Argon2 for better security
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/New_York'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# CELERY CONFIGURATION
# ==============================================================================
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# Celery Beat Schedule for periodic tasks
from celery.schedules import crontab
CELERY_BEAT_SCHEDULE = {
    # Health monitoring
    'record-health-metrics': {
        'task': 'core.tasks.record_health_metrics',
        'schedule': 300,  # every 5 minutes
    },
    'check-processing-health': {
        'task': 'core.tasks.check_processing_health',
        'schedule': 900,  # every 15 minutes
    },
    'cleanup-old-health-metrics': {
        'task': 'core.tasks.cleanup_old_health_metrics',
        'schedule': crontab(hour=3, minute=0),  # daily at 3 AM
    },
    # Email reminders
    'send-daily-reminders': {
        'task': 'core.tasks.send_all_reminders',
        'schedule': crontab(hour=9, minute=0),  # daily at 9 AM
    },
    # Document cleanup
    'cleanup-old-documents': {
        'task': 'claims.tasks.cleanup_old_documents',
        'schedule': crontab(hour=2, minute=0),  # daily at 2 AM
    },
}

# ==============================================================================
# REDIS CONFIGURATION
# ==============================================================================
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')

# Use local memory cache in development/testing when Redis isn't available
# Set USE_REDIS_CACHE=false to force local memory cache
USE_REDIS_CACHE = env.bool('USE_REDIS_CACHE', default=not DEBUG)

if USE_REDIS_CACHE:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

# ==============================================================================
# SESSION CONFIGURATION
# ==============================================================================
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 1209600  # 2 weeks
SESSION_COOKIE_SECURE = not DEBUG  # True in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ==============================================================================
# CSRF CONFIGURATION
# ==============================================================================
CSRF_COOKIE_SECURE = not DEBUG  # True in production
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# ==============================================================================
# SECURITY SETTINGS
# ==============================================================================
# Always enabled
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME type sniffing
SECURE_BROWSER_XSS_FILTER = True  # Enable XSS filter
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Content Security Policy
# Restricts what resources can be loaded
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com")
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com", "https://unpkg.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_FORM_ACTION = ("'self'",)

# Production-only settings (skip SSL redirect in staging - DO handles SSL at edge)
if not DEBUG:
    # Only enable SSL redirect in production, not staging
    # DO App Platform handles SSL termination and uses HTTP for internal health checks
    STAGING = env.bool('STAGING', default=False)
    SECURE_SSL_REDIRECT = not STAGING
    SECURE_HSTS_SECONDS = 31536000 if not STAGING else 0  # 1 year in prod
    SECURE_HSTS_INCLUDE_SUBDOMAINS = not STAGING
    SECURE_HSTS_PRELOAD = not STAGING
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Stricter CSP in production
    CSP_SCRIPT_SRC = ("'self'", "https://cdn.tailwindcss.com", "https://unpkg.com")
    CSP_STYLE_SRC = ("'self'", "https://cdn.tailwindcss.com")

# ==============================================================================
# DJANGO-ALLAUTH CONFIGURATION
# ==============================================================================
SITE_ID = 1
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
# Email verification: 'mandatory' in production, 'optional' in development
ACCOUNT_EMAIL_VERIFICATION = 'optional' if DEBUG else 'mandatory'
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
ACCOUNT_LOGOUT_REDIRECT_URL = '/'
LOGIN_REDIRECT_URL = '/dashboard/'
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# ==============================================================================
# EMAIL CONFIGURATION
# ==============================================================================
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@benefitsnavigator.com')

# ==============================================================================
# CRISPY FORMS CONFIGURATION (Tailwind CSS)
# ==============================================================================
CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'

# ==============================================================================
# OPENAI CONFIGURATION
# ==============================================================================
OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
OPENAI_MODEL = env('OPENAI_MODEL', default='gpt-3.5-turbo')
OPENAI_MAX_TOKENS = env.int('OPENAI_MAX_TOKENS', default=4000)

# ==============================================================================
# STRIPE CONFIGURATION
# ==============================================================================
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')
STRIPE_PRICE_ID = env('STRIPE_PRICE_ID', default='')

# ==============================================================================
# AWS S3 CONFIGURATION (for production file storage)
# ==============================================================================
USE_S3 = env.bool('USE_S3', default=False)

if USE_S3:
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_DEFAULT_ACL = 'private'
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}

    # S3 static files settings
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

    # S3 media files settings
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# ==============================================================================
# FILE UPLOAD SETTINGS
# ==============================================================================
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB
ALLOWED_DOCUMENT_TYPES = [
    'application/pdf',
    'image/jpeg',
    'image/png',
    'image/tiff',
]
MAX_DOCUMENT_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_DOCUMENT_PAGES = 100

# ==============================================================================
# PROTECTED MEDIA SETTINGS
# ==============================================================================
# Media files are served through Django views that verify authentication
# and ownership. Do NOT serve media files directly via web server.
#
# In production with nginx, enable X-Accel-Redirect for performance:
#   USE_X_SENDFILE = True
#   SENDFILE_ROOT = '/protected-media'
#
# Then configure nginx:
#   location /protected-media/ {
#       internal;
#       alias /path/to/media/;
#   }
USE_X_SENDFILE = env.bool('USE_X_SENDFILE', default=False)
SENDFILE_ROOT = env('SENDFILE_ROOT', default='')

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
(BASE_DIR / 'logs').mkdir(exist_ok=True)

# ==============================================================================
# SENTRY CONFIGURATION (Error Tracking)
# ==============================================================================
SENTRY_DSN = env('SENTRY_DSN', default='')
if SENTRY_DSN and not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=False,  # Don't send user data
    )

# ==============================================================================
# RATE LIMITING
# ==============================================================================
# Disabled in DEBUG mode by default. Can be explicitly controlled via env var
# for testing scenarios (e.g., running browser tests against a live server)
RATELIMIT_ENABLE = env.bool('RATELIMIT_ENABLE', default=not DEBUG)
RATELIMIT_USE_CACHE = 'default'

# ==============================================================================
# FEATURE FLAGS
# ==============================================================================
# Controls progressive rollout of features for dual-path development
# Path A = Direct-to-Veteran (B2C), Path B = VSO Platform (B2B)

FEATURES = {
    # Path A - Direct-to-Veteran (stable, enabled)
    'freemium_limits': True,
    'stripe_individual': True,
    'usage_tracking': True,

    # Path B - VSO Platform (progressive rollout)
    'organizations': env.bool('FEATURE_ORGANIZATIONS', default=False),
    'org_roles': env.bool('FEATURE_ORG_ROLES', default=False),
    'org_invitations': env.bool('FEATURE_ORG_INVITATIONS', default=False),
    'caseworker_assignment': env.bool('FEATURE_CASEWORKER_ASSIGNMENT', default=False),
    'org_billing': env.bool('FEATURE_ORG_BILLING', default=False),
    'org_admin_dashboard': env.bool('FEATURE_ORG_ADMIN', default=False),
    'audit_export': env.bool('FEATURE_AUDIT_EXPORT', default=False),

    # Shared Features
    'doc_search': env.bool('FEATURE_DOC_SEARCH', default=True),  # Documentation search system

    # Future
    'sso_saml': env.bool('FEATURE_SSO_SAML', default=False),
    'mfa': env.bool('FEATURE_MFA', default=False),
}


def feature_enabled(feature_name: str) -> bool:
    """Check if a feature flag is enabled."""
    return FEATURES.get(feature_name, False)


# ==============================================================================
# APPLICATION-SPECIFIC SETTINGS
# ==============================================================================

# Free tier limits
FREE_TIER_DOCUMENTS_PER_MONTH = 3
FREE_TIER_MAX_STORAGE_MB = 100
FREE_TIER_DENIAL_DECODES_PER_MONTH = 2
FREE_TIER_AI_ANALYSES_PER_MONTH = 5

# Premium tier features
PREMIUM_UNLIMITED_DOCUMENTS = True
PREMIUM_UNLIMITED_DENIAL_DECODES = True
PREMIUM_UNLIMITED_AI_ANALYSES = True
PREMIUM_GPT4_ACCESS = False  # Enable for premium users later
PREMIUM_PRIORITY_SUPPORT = True
PREMIUM_SAVED_CALCULATIONS = True  # Save rating calculations
PREMIUM_EXPORT_DATA = True  # Export data to PDF/CSV

# OCR Settings
OCR_ENGINE = env('OCR_ENGINE', default='tesseract')  # 'tesseract' or 'textract'
TESSERACT_CMD = env('TESSERACT_CMD', default='/usr/bin/tesseract')

# Site settings
SITE_NAME = 'VA Benefits Navigator'
SITE_DESCRIPTION = 'AI-powered assistance for VA disability claims and appeals'
SUPPORT_EMAIL = 'support@benefitsnavigator.com'
