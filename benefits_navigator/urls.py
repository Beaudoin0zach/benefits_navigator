"""
URL configuration for benefits_navigator project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from strawberry.django.views import GraphQLView

from core import views
from accounts.views import (
    RateLimitedLoginView,
    RateLimitedSignupView,
    RateLimitedPasswordResetView,
)
from .schema import schema

urlpatterns = [
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
