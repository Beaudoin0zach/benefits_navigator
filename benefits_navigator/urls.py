"""
URL configuration for benefits_navigator project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from django.http import JsonResponse
from strawberry.django.views import GraphQLView

from core import views


def health_check(request):
    """Health check endpoint for load balancers and monitoring."""
    from core.health import get_full_health_status

    # Quick check for load balancers - always returns 200 (liveness)
    if request.GET.get('quick') == '1':
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            db_status = "ok"
        except Exception as e:
            db_status = f"error: {str(e)[:50]}"
        # Always return 200 for liveness - app is running
        return JsonResponse({
            "status": "healthy" if db_status == "ok" else "degraded",
            "database": db_status,
        }, status=200)

    # Full health check (for monitoring)
    health = get_full_health_status()
    status_code = 200 if health['status'] == 'healthy' else 503
    return JsonResponse(health, status=status_code)
from accounts.views import (
    RateLimitedLoginView,
    RateLimitedSignupView,
    RateLimitedPasswordResetView,
)
from .schema import schema
from .sitemaps import sitemaps

urlpatterns = [
    # Health check for load balancers/monitoring
    path('health/', health_check, name='health_check'),

    # SEO files
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt',
        content_type='text/plain'
    ), name='robots_txt'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),

    # Home page
    path('', views.home, name='home'),

    # User dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # GraphQL API
    path('graphql/', GraphQLView.as_view(schema=schema), name='graphql'),

    # Admin
    path('admin/', admin.site.urls),

    # Rate-limited auth views (override allauth defaults)
    path('accounts/login/', RateLimitedLoginView.as_view(), name='account_login'),
    path('accounts/signup/', RateLimitedSignupView.as_view(), name='account_signup'),
    path('accounts/password/reset/', RateLimitedPasswordResetView.as_view(), name='account_reset_password'),

    # Accounts app URLs (privacy, export, deletion)
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # Authentication (django-allauth) - remaining URLs
    path('accounts/', include('allauth.urls')),

    # App URLs
    path('', include('core.urls')),
    path('claims/', include('claims.urls')),
    path('exam-prep/', include('examprep.urls')),
    path('appeals/', include('appeals.urls')),
    path('agents/', include('agents.urls')),
    path('docs/', include('documentation.urls', namespace='documentation')),
]

# Serve static files in development
# NOTE: Media files are NOT served directly for security reasons.
# All document access must go through protected views at /claims/document/<pk>/download/
# which verify authentication and ownership before serving files.
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    # DO NOT add: urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
