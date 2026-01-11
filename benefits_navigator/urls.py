"""
URL configuration for benefits_navigator project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from core import views
from accounts.views import (
    RateLimitedLoginView,
    RateLimitedSignupView,
    RateLimitedPasswordResetView,
    data_export,
    account_deletion,
    privacy_settings,
)

urlpatterns = [
    # Home page
    path('', views.home, name='home'),

    # User dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Admin
    path('admin/', admin.site.urls),

    # Rate-limited auth views (override allauth defaults)
    path('accounts/login/', RateLimitedLoginView.as_view(), name='account_login'),
    path('accounts/signup/', RateLimitedSignupView.as_view(), name='account_signup'),
    path('accounts/password/reset/', RateLimitedPasswordResetView.as_view(), name='account_reset_password'),

    # Privacy / Data management
    path('accounts/privacy/', privacy_settings, name='privacy_settings'),
    path('accounts/export/', data_export, name='data_export'),
    path('accounts/delete/', account_deletion, name='account_deletion'),

    # Authentication (django-allauth) - remaining URLs
    path('accounts/', include('allauth.urls')),

    # App URLs
    path('', include('core.urls')),
    path('claims/', include('claims.urls')),
    path('exam-prep/', include('examprep.urls')),
    path('appeals/', include('appeals.urls')),
    path('agents/', include('agents.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
