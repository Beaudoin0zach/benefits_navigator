"""
Views for VSO app - Case management and dashboard for Veterans Service Organizations
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404, HttpResponseForbidden
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone

from accounts.models import Organization, OrganizationMembership
from core.models import AuditLog
from .models import (
    VeteranCase, CaseNote, SharedDocument,
    SharedAnalysis, CaseChecklist, ChecklistItem
)
from .permissions import (
    Roles, has_role, is_vso_staff as check_vso_staff,
    get_user_organization_membership, vso_staff_required
)


def is_vso_member(user, org_slug=None):
    """Check if user is a VSO staff member (admin or caseworker)."""
    if not user.is_authenticated:
        return False

    memberships = user.memberships.filter(
        role__in=['admin', 'caseworker'],
        is_active=True,
        organization__is_active=True
    )

    if org_slug:
        memberships = memberships.filter(organization__slug=org_slug)

    return memberships.exists()


def get_user_staff_memberships(user):
    """
    Get all VSO staff memberships for a user.

    Returns:
        QuerySet of OrganizationMembership objects where user is admin/caseworker
    """
    if not user.is_authenticated:
        return OrganizationMembership.objects.none()

    return user.memberships.filter(
        role__in=['admin', 'caseworker'],
        is_active=True,
        organization__is_active=True
    ).select_related('organization')


def get_user_organization(user, org_slug=None, request=None):
    """
    Get the user's active organization with explicit selection for multi-org users.

    Security: When user belongs to multiple organizations, require explicit selection
    via org_slug parameter or session to prevent ambiguous data access.

    Args:
        user: User instance
        org_slug: Optional explicit organization slug (from URL or parameter)
        request: Optional request object to check/store session selection

    Returns:
        Organization instance or None
    """
    memberships = get_user_staff_memberships(user)

    if not memberships.exists():
        return None

    # If org_slug provided, validate and use it
    if org_slug:
        membership = memberships.filter(organization__slug=org_slug).first()
        if membership:
            # Store selection in session for future requests
            if request:
                request.session['selected_org_slug'] = org_slug
            return membership.organization
        return None  # Invalid org_slug

    # Check session for previously selected org
    if request:
        session_org_slug = request.session.get('selected_org_slug')
        if session_org_slug:
            membership = memberships.filter(organization__slug=session_org_slug).first()
            if membership:
                return membership.organization
            # Session org no longer valid, clear it
            del request.session['selected_org_slug']

    # If only one organization, use it directly
    if memberships.count() == 1:
        org = memberships.first().organization
        if request:
            request.session['selected_org_slug'] = org.slug
        return org

    # Multiple organizations - require explicit selection
    # Return None to trigger org selection prompt
    return None


def requires_org_selection(user, request=None):
    """
    Check if user needs to select an organization.

    Returns:
        True if user has multiple orgs and none is selected
    """
    memberships = get_user_staff_memberships(user)

    if memberships.count() <= 1:
        return False

    # Check if valid org is already selected in session
    if request:
        session_org_slug = request.session.get('selected_org_slug')
        if session_org_slug and memberships.filter(organization__slug=session_org_slug).exists():
            return False

    return True


def vso_required(view_func):
    """Decorator to require VSO staff access."""
    return vso_staff_required(view_func)


@vso_required
def select_organization(request):
    """
    Organization selection page for multi-org users.

    Allows users belonging to multiple organizations to explicitly choose
    which organization they want to work with.
    """
    memberships = get_user_staff_memberships(request.user)

    if not memberships.exists():
        messages.error(request, "No organization membership found.")
        return redirect('claims:document_list')

    # If only one org, redirect directly
    if memberships.count() == 1:
        org = memberships.first().organization
        request.session['selected_org_slug'] = org.slug
        return redirect('vso:dashboard')

    if request.method == 'POST':
        org_slug = request.POST.get('organization')
        if org_slug:
            membership = memberships.filter(organization__slug=org_slug).first()
            if membership:
                request.session['selected_org_slug'] = org_slug
                messages.success(request, f"Now working with {membership.organization.name}")
                return redirect('vso:dashboard')

    context = {
        'memberships': memberships,
    }
    return render(request, 'vso/select_organization.html', context)


@vso_required
def dashboard(request):
    """
    VSO Dashboard - Overview of all cases and metrics
    """
    # Check if user needs to select an organization
    if requires_org_selection(request.user, request):
        return redirect('vso:select_organization')

    org = get_user_organization(request.user, request=request)
    if not org:
        messages.error(request, "Please select an organization to continue.")
        return redirect('vso:select_organization')

    # Get all cases for this organization
    cases = VeteranCase.objects.filter(organization=org)

    # Case counts by status
    status_counts = cases.values('status').annotate(count=Count('id'))
    status_dict = {item['status']: item['count'] for item in status_counts}

    # Priority cases (urgent or overdue)
    priority_cases = cases.filter(
        Q(priority='urgent') |
        Q(next_action_date__lt=timezone.now().date())
    ).filter(
        status__in=['intake', 'gathering_evidence', 'claim_filed',
                    'pending_decision', 'appeal_in_progress']
    ).order_by('next_action_date', '-priority')[:10]

    # Recent activity (notes and shared documents)
    recent_notes = CaseNote.objects.filter(
        case__organization=org
    ).select_related('case', 'author').order_by('-created_at')[:10]

    # Cases assigned to current user
    my_cases = cases.filter(
        assigned_to=request.user
    ).exclude(
        status__startswith='closed'
    ).order_by('next_action_date', '-priority')[:10]

    # Outcome metrics (closed cases)
    closed_cases = cases.filter(status__startswith='closed')
    won_cases = closed_cases.filter(status='closed_won').count()
    total_closed = closed_cases.count()
    win_rate = (won_cases / total_closed * 100) if total_closed > 0 else 0

    context = {
        'organization': org,
        'total_cases': cases.count(),
        'open_cases': cases.exclude(status__startswith='closed').count(),
        'status_counts': status_dict,
        'priority_cases': priority_cases,
        'recent_notes': recent_notes,
        'my_cases': my_cases,
        'win_rate': win_rate,
        'won_cases': won_cases,
        'total_closed': total_closed,
    }

    return render(request, 'vso/dashboard.html', context)


@vso_required
def case_list(request):
    """
    List all cases with filtering and search
    """
    org = get_user_organization(request.user, request=request)
    if not org:
        return redirect('vso:dashboard')

    cases = VeteranCase.objects.filter(
        organization=org
    ).select_related('veteran', 'assigned_to')

    # Filtering
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    assigned_filter = request.GET.get('assigned_to')
    search_query = request.GET.get('q')

    if status_filter:
        cases = cases.filter(status=status_filter)

    if priority_filter:
        cases = cases.filter(priority=priority_filter)

    if assigned_filter:
        if assigned_filter == 'me':
            cases = cases.filter(assigned_to=request.user)
        elif assigned_filter == 'unassigned':
            cases = cases.filter(assigned_to__isnull=True)
        else:
            cases = cases.filter(assigned_to_id=assigned_filter)

    if search_query:
        cases = cases.filter(
            Q(title__icontains=search_query) |
            Q(veteran__email__icontains=search_query) |
            Q(veteran__first_name__icontains=search_query) |
            Q(veteran__last_name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Ordering
    order_by = request.GET.get('order_by', '-created_at')
    cases = cases.order_by(order_by)

    # Pagination
    paginator = Paginator(cases, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get caseworkers for filter dropdown
    caseworkers = org.memberships.filter(
        role__in=['admin', 'caseworker'],
        is_active=True
    ).select_related('user')

    context = {
        'organization': org,
        'page_obj': page_obj,
        'cases': page_obj,
        'status_choices': VeteranCase.STATUS_CHOICES,
        'priority_choices': VeteranCase.PRIORITY_CHOICES,
        'caseworkers': caseworkers,
        'current_filters': {
            'status': status_filter,
            'priority': priority_filter,
            'assigned_to': assigned_filter,
            'q': search_query,
            'order_by': order_by,
        },
    }

    return render(request, 'vso/case_list.html', context)


@vso_required
def case_detail(request, pk):
    """
    Detailed view of a single case
    """
    org = get_user_organization(request.user, request=request)
    if not org:
        return redirect('vso:dashboard')

    case = get_object_or_404(
        VeteranCase.objects.select_related('veteran', 'assigned_to', 'organization'),
        pk=pk,
        organization=org
    )

    # Get related data
    notes = case.notes.select_related('author').order_by('-created_at')
    shared_docs = case.shared_documents.select_related('document', 'shared_by')
    shared_analyses = case.shared_analyses.select_related('shared_by')
    checklists = case.checklists.prefetch_related('items')

    # Action items (incomplete)
    action_items = case.notes.filter(
        is_action_item=True,
        action_completed=False
    ).order_by('action_due_date')

    context = {
        'organization': org,
        'case': case,
        'notes': notes,
        'shared_documents': shared_docs,
        'shared_analyses': shared_analyses,
        'checklists': checklists,
        'action_items': action_items,
        'status_choices': VeteranCase.STATUS_CHOICES,
        'priority_choices': VeteranCase.PRIORITY_CHOICES,
    }

    return render(request, 'vso/case_detail.html', context)


@vso_required
@require_POST
def case_update_status(request, pk):
    """
    HTMX endpoint to update case status
    """
    org = get_user_organization(request.user, request=request)
    case = get_object_or_404(VeteranCase, pk=pk, organization=org)

    new_status = request.POST.get('status')
    if new_status and new_status in dict(VeteranCase.STATUS_CHOICES):
        old_status = case.status
        case.status = new_status

        # Handle closure
        if new_status.startswith('closed') and not old_status.startswith('closed'):
            case.closed_at = timezone.now()
            case.closed_by = request.user

        case.save()

        # Create note about status change
        CaseNote.objects.create(
            case=case,
            author=request.user,
            note_type='milestone',
            subject=f'Status changed to {case.get_status_display()}',
            content=f'Case status updated from {dict(VeteranCase.STATUS_CHOICES).get(old_status)} to {case.get_status_display()}',
            visible_to_veteran=True
        )

        messages.success(request, f'Case status updated to {case.get_status_display()}')

    return redirect('vso:case_detail', pk=pk)


@vso_required
@require_POST
def add_case_note(request, pk):
    """
    Add a note to a case
    """
    org = get_user_organization(request.user, request=request)
    case = get_object_or_404(VeteranCase, pk=pk, organization=org)

    note_type = request.POST.get('note_type', 'general')
    subject = request.POST.get('subject', '').strip()
    content = request.POST.get('content', '').strip()
    is_action_item = request.POST.get('is_action_item') == 'on'
    action_due_date = request.POST.get('action_due_date') or None
    visible_to_veteran = request.POST.get('visible_to_veteran') == 'on'

    if subject and content:
        CaseNote.objects.create(
            case=case,
            author=request.user,
            note_type=note_type,
            subject=subject,
            content=content,
            is_action_item=is_action_item,
            action_due_date=action_due_date,
            visible_to_veteran=visible_to_veteran
        )
        messages.success(request, 'Note added successfully.')
    else:
        messages.error(request, 'Subject and content are required.')

    return redirect('vso:case_detail', pk=pk)


@vso_required
@require_POST
def complete_action_item(request, pk, note_pk):
    """
    Mark an action item as complete
    """
    org = get_user_organization(request.user, request=request)
    case = get_object_or_404(VeteranCase, pk=pk, organization=org)
    note = get_object_or_404(CaseNote, pk=note_pk, case=case, is_action_item=True)

    note.mark_complete(completed_by=request.user)
    messages.success(request, 'Action item marked as complete.')

    return redirect('vso:case_detail', pk=pk)


@vso_required
def case_create(request):
    """
    Create a new case (invite a veteran or create from existing user)
    """
    org = get_user_organization(request.user, request=request)
    if not org:
        return redirect('vso:dashboard')

    if request.method == 'POST':
        # Get form data
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        veteran_email = request.POST.get('veteran_email', '').strip()
        priority = request.POST.get('priority', 'normal')

        if not title or not veteran_email:
            messages.error(request, 'Title and veteran email are required.')
            return render(request, 'vso/case_create.html', {'organization': org})

        # Find or placeholder for veteran
        from django.contrib.auth import get_user_model
        User = get_user_model()

        veteran = User.objects.filter(email=veteran_email).first()

        if not veteran:
            # Create placeholder user (they'll need to accept invitation)
            # For now, require existing user
            messages.error(
                request,
                'Veteran not found. They must create an account first, '
                'or use the invitation system.'
            )
            return render(request, 'vso/case_create.html', {'organization': org})

        # Create the case
        case = VeteranCase.objects.create(
            organization=org,
            veteran=veteran,
            assigned_to=request.user,
            title=title,
            description=description,
            priority=priority,
            status='intake',
            intake_date=timezone.now().date()
        )

        # Create initial note
        CaseNote.objects.create(
            case=case,
            author=request.user,
            note_type='milestone',
            subject='Case created',
            content=f'New case created for {veteran.email}',
            visible_to_veteran=True
        )

        # Audit log: VSO case creation
        AuditLog.log(
            action='vso_case_create',
            request=request,
            resource_type='VeteranCase',
            resource_id=case.pk,
            details={
                'organization_id': org.pk,
                'organization_name': org.name,
                'veteran_id': veteran.pk,
            },
            success=True
        )

        messages.success(request, f'Case "{title}" created successfully.')
        return redirect('vso:case_detail', pk=case.pk)

    context = {
        'organization': org,
        'priority_choices': VeteranCase.PRIORITY_CHOICES,
    }
    return render(request, 'vso/case_create.html', context)


@vso_required
def shared_document_review(request, pk, doc_pk):
    """
    Review a shared document with comprehensive AI analysis for VSO prep.
    """
    org = get_user_organization(request.user, request=request)
    case = get_object_or_404(VeteranCase, pk=pk, organization=org)
    shared_doc = get_object_or_404(SharedDocument, pk=doc_pk, case=case)

    if request.method == 'POST':
        status = request.POST.get('status', 'reviewed')
        notes = request.POST.get('review_notes', '').strip()

        shared_doc.status = status
        shared_doc.review_notes = notes
        shared_doc.reviewed_by = request.user
        shared_doc.reviewed_at = timezone.now()
        shared_doc.save()

        # Create a note about the review
        CaseNote.objects.create(
            case=case,
            author=request.user,
            note_type='document_review',
            subject=f'Reviewed: {shared_doc.document.file_name}',
            content=notes if notes else 'Document reviewed.',
            visible_to_veteran=False
        )

        messages.success(request, 'Document review saved.')
        return redirect('vso:case_detail', pk=pk)

    # Get the document and all available analyses
    document = shared_doc.document
    analysis_data = {}

    if shared_doc.include_ai_analysis:
        from agents.models import RatingAnalysis, DecisionLetterAnalysis, DenialDecoding

        # Get rating analysis if available
        rating_analysis = RatingAnalysis.objects.filter(
            document=document
        ).first()
        if rating_analysis:
            analysis_data['rating'] = rating_analysis

        # Get decision letter analysis
        decision_analysis = DecisionLetterAnalysis.objects.filter(
            document=document
        ).first()
        if decision_analysis:
            analysis_data['decision'] = decision_analysis

        # Get denial decoding
        denial_decoding = DenialDecoding.objects.filter(
            decision_analysis__document=document
        ).first()
        if denial_decoding:
            analysis_data['denial'] = denial_decoding

    context = {
        'organization': org,
        'case': case,
        'shared_document': shared_doc,
        'document': document,
        'analysis_data': analysis_data,
        'status_choices': SharedDocument.SHARE_STATUS_CHOICES,
    }

    return render(request, 'vso/shared_document_review.html', context)


# HTMX partial views

@vso_required
def case_notes_partial(request, pk):
    """
    HTMX partial for case notes list
    """
    org = get_user_organization(request.user, request=request)
    case = get_object_or_404(VeteranCase, pk=pk, organization=org)
    notes = case.notes.select_related('author').order_by('-created_at')

    return render(request, 'vso/partials/case_notes.html', {
        'case': case,
        'notes': notes,
    })


@vso_required
def case_documents_partial(request, pk):
    """
    HTMX partial for shared documents list
    """
    org = get_user_organization(request.user, request=request)
    case = get_object_or_404(VeteranCase, pk=pk, organization=org)
    shared_docs = case.shared_documents.select_related('document', 'shared_by')

    return render(request, 'vso/partials/case_documents.html', {
        'case': case,
        'shared_documents': shared_docs,
    })


# ============================================================================
# Veteran Invitation System
# ============================================================================

@vso_required
def invite_veteran(request):
    """
    Invite a veteran to the organization's caseload.
    Creates an invitation and optionally a case.
    """
    from accounts.models import OrganizationInvitation

    org = get_user_organization(request.user, request=request)
    if not org:
        messages.error(request, "No active organization found.")
        return redirect('vso:dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        case_title = request.POST.get('case_title', '').strip()
        case_description = request.POST.get('case_description', '').strip()
        priority = request.POST.get('priority', 'normal')

        if not email:
            messages.error(request, 'Email address is required.')
            return render(request, 'vso/invite_veteran.html', {'organization': org})

        # Check if already invited (pending)
        existing_invite = OrganizationInvitation.objects.filter(
            organization=org,
            email=email,
            accepted_at__isnull=True,
            expires_at__gt=timezone.now()
        ).first()

        if existing_invite:
            messages.warning(
                request,
                f'An invitation is already pending for {email}. '
                f'It expires on {existing_invite.expires_at.strftime("%B %d, %Y")}.'
            )
            return redirect('vso:invitations')

        # Check if veteran already has a case with this org
        from django.contrib.auth import get_user_model
        User = get_user_model()
        existing_user = User.objects.filter(email=email).first()

        if existing_user:
            existing_case = VeteranCase.objects.filter(
                organization=org,
                veteran=existing_user
            ).exclude(status__startswith='closed').first()

            if existing_case:
                messages.warning(
                    request,
                    f'This veteran already has an active case: "{existing_case.title}". '
                    f'<a href="{existing_case.get_absolute_url()}" class="underline">View case</a>'
                )
                return redirect('vso:invitations')

        # Create the invitation
        invitation = OrganizationInvitation.objects.create(
            organization=org,
            email=email,
            role='veteran',
            invited_by=request.user
        )

        # Store case details in session for when invitation is accepted
        if case_title:
            request.session[f'pending_case_{invitation.token}'] = {
                'title': case_title,
                'description': case_description,
                'priority': priority,
                'invited_by_id': request.user.id,
            }

        # Send invitation email
        _send_veteran_invitation_email(invitation, case_title)

        messages.success(
            request,
            f'Invitation sent to {email}. They will receive an email with instructions.'
        )

        return redirect('vso:invitations')

    context = {
        'organization': org,
        'priority_choices': VeteranCase.PRIORITY_CHOICES,
    }
    return render(request, 'vso/invite_veteran.html', context)


def _send_veteran_invitation_email(invitation, case_title=None):
    """
    Send invitation email to veteran.
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings
    from django.urls import reverse

    accept_url = f"{settings.SITE_URL}{reverse('vso:accept_invitation', args=[invitation.token])}"

    subject = f"You've been invited to work with {invitation.organization.name}"

    context = {
        'invitation': invitation,
        'accept_url': accept_url,
        'case_title': case_title,
        'expires_days': 7,
    }

    html_message = render_to_string('vso/emails/veteran_invitation.html', context)
    plain_message = render_to_string('vso/emails/veteran_invitation.txt', context)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[invitation.email],
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as e:
        # Log but don't fail - invitation is still created
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send invitation email: {e}")


@vso_required
def invitations_list(request):
    """
    List all pending and recent invitations for the organization.
    """
    from accounts.models import OrganizationInvitation

    org = get_user_organization(request.user, request=request)
    if not org:
        return redirect('vso:dashboard')

    # Get pending invitations
    pending = OrganizationInvitation.objects.filter(
        organization=org,
        accepted_at__isnull=True,
        expires_at__gt=timezone.now()
    ).order_by('-created_at')

    # Get recent (last 30 days) accepted/expired
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent = OrganizationInvitation.objects.filter(
        organization=org,
        created_at__gte=thirty_days_ago
    ).exclude(
        id__in=pending.values_list('id', flat=True)
    ).order_by('-created_at')

    context = {
        'organization': org,
        'pending_invitations': pending,
        'recent_invitations': recent,
    }

    return render(request, 'vso/invitations_list.html', context)


@vso_required
@require_POST
def resend_invitation(request, token):
    """
    Resend an invitation email.
    """
    from accounts.models import OrganizationInvitation

    org = get_user_organization(request.user, request=request)
    invitation = get_object_or_404(
        OrganizationInvitation,
        token=token,
        organization=org,
        accepted_at__isnull=True
    )

    if invitation.is_expired:
        # Extend expiration
        invitation.expires_at = timezone.now() + timezone.timedelta(days=7)
        invitation.save()

    # Get case title from session if exists
    case_info = request.session.get(f'pending_case_{token}', {})
    case_title = case_info.get('title')

    _send_veteran_invitation_email(invitation, case_title)

    messages.success(request, f'Invitation resent to {invitation.email}.')
    return redirect('vso:invitations')


@vso_required
@require_POST
def cancel_invitation(request, token):
    """
    Cancel a pending invitation.
    """
    from accounts.models import OrganizationInvitation

    org = get_user_organization(request.user, request=request)
    invitation = get_object_or_404(
        OrganizationInvitation,
        token=token,
        organization=org,
        accepted_at__isnull=True
    )

    # Clean up session data
    if f'pending_case_{token}' in request.session:
        del request.session[f'pending_case_{token}']

    invitation.delete()
    messages.success(request, f'Invitation to {invitation.email} has been cancelled.')
    return redirect('vso:invitations')


@login_required
def accept_invitation(request, token):
    """
    Accept a veteran invitation.
    This view is accessible to any logged-in user.
    """
    from accounts.models import OrganizationInvitation

    invitation = get_object_or_404(OrganizationInvitation, token=token)

    # Check if invitation is valid
    if invitation.accepted_at:
        messages.info(request, 'This invitation has already been accepted.')
        # Check if they have a case
        case = VeteranCase.objects.filter(
            organization=invitation.organization,
            veteran=request.user
        ).first()
        if case:
            return redirect('claims:document_list')
        return redirect('claims:document_list')

    if invitation.is_expired:
        messages.error(
            request,
            'This invitation has expired. Please contact the organization for a new invitation.'
        )
        return redirect('home')

    # Verify email matches (or allow any authenticated user)
    if invitation.email.lower() != request.user.email.lower():
        messages.warning(
            request,
            f'This invitation was sent to {invitation.email}. '
            f'You are logged in as {request.user.email}. '
            f'Please log in with the correct account or contact the organization.'
        )
        return redirect('account_login')

    if request.method == 'POST':
        try:
            # Accept the invitation
            invitation.accept(request.user)

            # Create case if details were stored
            case_info = request.session.get(f'pending_case_{token}', {})
            if case_info:
                from django.contrib.auth import get_user_model
                User = get_user_model()

                invited_by = User.objects.filter(id=case_info.get('invited_by_id')).first()

                case = VeteranCase.objects.create(
                    organization=invitation.organization,
                    veteran=request.user,
                    assigned_to=invited_by,
                    title=case_info.get('title', f'Case for {request.user.email}'),
                    description=case_info.get('description', ''),
                    priority=case_info.get('priority', 'normal'),
                    status='intake',
                    intake_date=timezone.now().date(),
                    veteran_consent_date=timezone.now()
                )

                # Create initial note
                CaseNote.objects.create(
                    case=case,
                    author=invited_by,
                    note_type='milestone',
                    subject='Veteran accepted invitation',
                    content=f'{request.user.email} accepted the invitation and joined the case.',
                    visible_to_veteran=True
                )

                # Clean up session
                del request.session[f'pending_case_{token}']

            messages.success(
                request,
                f'Welcome! You are now connected with {invitation.organization.name}. '
                f'You can now share documents with your caseworker.'
            )

            return redirect('claims:document_list')

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('home')

    context = {
        'invitation': invitation,
    }
    return render(request, 'vso/accept_invitation.html', context)
