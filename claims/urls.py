"""
URL routing for claims app
"""

from django.urls import path
from . import views

app_name = 'claims'

urlpatterns = [
    # Document upload and management
    path('', views.document_list, name='document_list'),
    path('upload/', views.document_upload, name='document_upload'),
    path('document/<int:pk>/', views.document_detail, name='document_detail'),
    path('document/<int:pk>/status/', views.document_status, name='document_status'),
    path('document/<int:pk>/delete/', views.document_delete, name='document_delete'),
]
