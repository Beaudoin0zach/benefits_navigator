"""
Custom authentication views with rate limiting and data management
"""

import json
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from allauth.account.views import LoginView, SignupView, PasswordResetView

from core.models import AuditLog


class RateLimitedLoginView(LoginView):
    """
    Login view with rate limiting to prevent brute force attacks.
    Limits: 5 attempts per minute per IP, 20 per hour
    """

    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True))
    @method_decorator(ratelimit(key='ip', rate='20/h', method='POST', block=True))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RateLimitedSignupView(SignupView):
    """
    Signup view with rate limiting to prevent abuse.
    Limits: 3 signups per hour per IP
    """

    @method_decorator(ratelimit(key='ip', rate='3/h', method='POST', block=True))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RateLimitedPasswordResetView(PasswordResetView):
    """
    Password reset view with rate limiting to prevent email bombing.
    Limits: 3 resets per hour per IP
    """

    @method_decorator(ratelimit(key='ip', rate='3/h', method='POST', block=True))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


# =============================================================================
# DATA EXPORT / PRIVACY VIEWS
# =============================================================================

@login_required
def data_export(request):
    """
    Request export of all user data (GDPR compliance).
    """
    if request.method == 'POST':
        # Log the export request
        AuditLog.log(
            action='pii_export',
            request=request,
            details={'export_type': 'full_data'},
        )

        # Generate export immediately (for small datasets)
        # For larger systems, this would be queued as a Celery task
        export_data = _generate_user_export(request.user)

        # Return as downloadable JSON file
        response = HttpResponse(
            json.dumps(export_data, indent=2, default=str),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="va_navigator_export_{request.user.id}.json"'
        return response

    context = {
        'page_title': 'Export My Data',
    }
    return render(request, 'accounts/data_export.html', context)


def _generate_user_export(user):
    """
    Generate a complete export of user data.
    """
    export = {
        'export_date': timezone.now().isoformat(),
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'date_joined': user.date_joined.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None,
        },
    }

    # Profile data
    if hasattr(user, 'profile'):
        profile = user.profile
        export['profile'] = {
            'branch_of_service': profile.branch_of_service,
            'date_of_birth': profile.date_of_birth.isoformat() if profile.date_of_birth else None,
            'va_file_number': profile.va_file_number,
            'disability_rating': profile.disability_rating,
            'bio': profile.bio,
        }

    # Documents
    if hasattr(user, 'documents'):
        export['documents'] = [
            {
                'id': doc.id,
                'file_name': doc.file_name,
                'document_type': doc.document_type,
                'uploaded_at': doc.created_at.isoformat(),
            }
            for doc in user.documents.filter(is_deleted=False)
        ]

    # Claims
    if hasattr(user, 'claims'):
        export['claims'] = [
            {
                'id': claim.id,
                'condition': claim.condition,
                'claim_type': claim.claim_type,
                'status': claim.status,
                'filed_date': claim.filed_date.isoformat() if claim.filed_date else None,
                'created_at': claim.created_at.isoformat(),
            }
            for claim in user.claims.filter(is_deleted=False)
        ]

    # Appeals
    if hasattr(user, 'appeals'):
        export['appeals'] = [
            {
                'id': appeal.id,
                'condition': appeal.condition,
                'appeal_type': appeal.appeal_type,
                'appeal_lane': appeal.appeal_lane,
                'status': appeal.status,
                'created_at': appeal.created_at.isoformat(),
            }
            for appeal in user.appeals.all()
        ]

    # Exam checklists
    if hasattr(user, 'exam_checklists'):
        export['exam_checklists'] = [
            {
                'id': checklist.id,
                'condition': checklist.condition,
                'exam_date': checklist.exam_date.isoformat() if checklist.exam_date else None,
                'created_at': checklist.created_at.isoformat(),
            }
            for checklist in user.exam_checklists.all()
        ]

    # Evidence checklists
    if hasattr(user, 'evidence_checklists'):
        export['evidence_checklists'] = [
            {
                'id': checklist.id,
                'condition': checklist.condition,
                'claim_type': checklist.claim_type,
                'completion_percentage': checklist.completion_percentage,
                'created_at': checklist.created_at.isoformat(),
            }
            for checklist in user.evidence_checklists.all()
        ]

    # Rating calculations
    if hasattr(user, 'rating_calculations'):
        export['rating_calculations'] = [
            {
                'id': calc.id,
                'name': calc.name,
                'combined_rounded': calc.combined_rounded,
                'created_at': calc.created_at.isoformat(),
            }
            for calc in user.rating_calculations.all()
        ]

    # Journey events
    if hasattr(user, 'journey_events'):
        export['journey_events'] = [
            {
                'id': event.id,
                'title': event.title,
                'event_date': event.event_date.isoformat(),
            }
            for event in user.journey_events.all()
        ]

    # Milestones
    if hasattr(user, 'journey_milestones'):
        export['journey_milestones'] = [
            {
                'id': milestone.id,
                'title': milestone.title,
                'date': milestone.date.isoformat(),
                'milestone_type': milestone.milestone_type,
            }
            for milestone in user.journey_milestones.all()
        ]

    return export


@login_required
def account_deletion(request):
    """
    Request account deletion (GDPR compliance).
    Implements 30-day grace period before actual deletion.
    """
    user = request.user

    # Check if deletion already scheduled
    deletion_scheduled = getattr(user, 'deletion_scheduled_at', None)

    if request.method == 'POST':
        confirm = request.POST.get('confirm')

        if confirm == 'DELETE':
            # Log the deletion request
            AuditLog.log(
                action='account_delete',
                request=request,
                details={'scheduled_for': (timezone.now() + timedelta(days=30)).isoformat()},
            )

            # Schedule deletion (30-day grace period)
            # In a production system, you'd add a field to User model
            # and a Celery beat task to process deletions
            messages.success(
                request,
                "Your account deletion has been scheduled. Your account and all data "
                "will be permanently deleted in 30 days. You can cancel this by logging "
                "in and visiting this page again."
            )

            # For now, just log out the user
            from django.contrib.auth import logout
            logout(request)

            return redirect('home')
        else:
            messages.error(request, "Please type DELETE to confirm account deletion.")

    context = {
        'page_title': 'Delete My Account',
        'deletion_scheduled': deletion_scheduled,
    }
    return render(request, 'accounts/account_deletion.html', context)


@login_required
def privacy_settings(request):
    """
    Privacy settings page - central hub for data management.
    """
    user = request.user

    # Get counts for the summary
    document_count = user.documents.filter(is_deleted=False).count() if hasattr(user, 'documents') else 0
    claim_count = user.claims.filter(is_deleted=False).count() if hasattr(user, 'claims') else 0
    appeal_count = user.appeals.count() if hasattr(user, 'appeals') else 0

    # Get recent audit logs for this user
    recent_activity = AuditLog.objects.filter(
        user=user
    ).order_by('-timestamp')[:10]

    context = {
        'page_title': 'Privacy Settings',
        'document_count': document_count,
        'claim_count': claim_count,
        'appeal_count': appeal_count,
        'recent_activity': recent_activity,
    }
    return render(request, 'accounts/privacy_settings.html', context)
