"""
URL configuration for VSO app
"""

from django.urls import path
from . import views

app_name = 'vso'

urlpatterns = [
    # Organization selection (for multi-org users)
    path('select-org/', views.select_organization, name='select_organization'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Cases
    path('cases/', views.case_list, name='case_list'),
    path('cases/new/', views.case_create, name='case_create'),
    path('cases/<int:pk>/', views.case_detail, name='case_detail'),
    path('cases/<int:pk>/status/', views.case_update_status, name='case_update_status'),
    path('cases/<int:pk>/archive/', views.case_archive, name='case_archive'),
    path('cases/<int:pk>/notes/add/', views.add_case_note, name='add_case_note'),
    path('cases/<int:pk>/actions/<int:note_pk>/complete/',
         views.complete_action_item, name='complete_action_item'),

    # Shared document review
    path('cases/<int:pk>/documents/<int:doc_pk>/review/',
         views.shared_document_review, name='shared_document_review'),

    # HTMX partials
    path('cases/<int:pk>/notes/', views.case_notes_partial, name='case_notes_partial'),
    path('cases/<int:pk>/documents/', views.case_documents_partial, name='case_documents_partial'),

    # Veteran Invitations
    path('invitations/', views.invitations_list, name='invitations'),
    path('invitations/new/', views.invite_veteran, name='invite_veteran'),
    path('invitations/<str:token>/resend/', views.resend_invitation, name='resend_invitation'),
    path('invitations/<str:token>/cancel/', views.cancel_invitation, name='cancel_invitation'),
    path('invite/<str:token>/', views.accept_invitation, name='accept_invitation'),
]
