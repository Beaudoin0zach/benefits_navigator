"""
URL configuration for accounts app.
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('privacy/', views.privacy_settings, name='privacy_settings'),
    path('export/', views.data_export, name='data_export'),
    path('delete/', views.account_deletion, name='account_deletion'),
]
