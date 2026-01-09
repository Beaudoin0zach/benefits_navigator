"""
URL configuration for examprep app
"""

from django.urls import path
from . import views

app_name = 'examprep'

urlpatterns = [
    # Guide list and detail pages
    path('', views.guide_list, name='guide_list'),
    path('guide/<slug:slug>/', views.guide_detail, name='guide_detail'),

    # Glossary
    path('glossary/', views.glossary_list, name='glossary_list'),
    path('glossary/<int:pk>/', views.glossary_detail, name='glossary_detail'),

    # User's personal exam checklists
    path('my-checklists/', views.checklist_list, name='checklist_list'),
    path('my-checklists/create/', views.checklist_create, name='checklist_create'),
    path('my-checklists/<int:pk>/', views.checklist_detail, name='checklist_detail'),
    path('my-checklists/<int:pk>/update/', views.checklist_update, name='checklist_update'),
    path('my-checklists/<int:pk>/delete/', views.checklist_delete, name='checklist_delete'),

    # HTMX endpoints for interactive features
    path('my-checklists/<int:pk>/toggle-task/', views.checklist_toggle_task, name='checklist_toggle_task'),
]
