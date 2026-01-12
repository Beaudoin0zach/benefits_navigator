"""
Core views - Home page and shared views
"""

from datetime import date

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse

from .models import UserJourneyEvent, JourneyMilestone, Deadline
from .journey import TimelineBuilder


def home(request):
    """
    Home page view - landing page for the VA Benefits Navigator
    """
    context = {
        'page_title': 'Welcome to VA Benefits Navigator',
    }
    return render(request, 'core/home.html', context)


@login_required
def dashboard(request):
    """
    User dashboard - central hub showing all user activity
    """
    user = request.user

    # Get user's documents (most recent 5)
    documents = []
    if hasattr(user, 'documents'):
        documents = user.documents.filter(is_deleted=False).order_by('-created_at')[:5]

    # Get user's exam checklists
    checklists = []
    if hasattr(user, 'exam_checklists'):
        checklists = user.exam_checklists.all().order_by('-created_at')[:5]

    # Get user's appeals
    appeals = []
    if hasattr(user, 'appeals'):
        appeals = user.appeals.all().order_by('-created_at')[:5]

    # Calculate stats
    total_documents = user.documents.filter(is_deleted=False).count() if hasattr(user, 'documents') else 0
    total_checklists = user.exam_checklists.count() if hasattr(user, 'exam_checklists') else 0
    total_appeals = user.appeals.count() if hasattr(user, 'appeals') else 0

    # Get upcoming exams (checklists with exam dates in the future)
    from datetime import date
    upcoming_exams = []
    if hasattr(user, 'exam_checklists'):
        upcoming_exams = user.exam_checklists.filter(
            exam_date__gte=date.today(),
            exam_completed=False
        ).order_by('exam_date')[:3]

    # Get pending appeals
    pending_appeals = []
    if hasattr(user, 'appeals'):
        pending_appeals = user.appeals.exclude(
            status__in=['decided', 'closed']
        ).order_by('-created_at')[:3]

    context = {
        'page_title': 'My Dashboard',
        'documents': documents,
        'checklists': checklists,
        'appeals': appeals,
        'total_documents': total_documents,
        'total_checklists': total_checklists,
        'total_appeals': total_appeals,
        'upcoming_exams': upcoming_exams,
        'pending_appeals': pending_appeals,
    }
    return render(request, 'core/dashboard.html', context)


# =============================================================================
# JOURNEY DASHBOARD VIEWS
# =============================================================================

@login_required
def journey_dashboard(request):
    """
    Claims journey dashboard - visual timeline and progress tracking.
    """
    builder = TimelineBuilder(request.user)

    # Get timeline (limit to recent 20 events)
    timeline = builder.build_timeline(limit=20)

    # Get current stage
    current_stage = builder.get_current_stage()

    # Get upcoming deadlines (next 90 days)
    deadlines = builder.get_upcoming_deadlines(days=90)

    # Get stats
    stats = builder.get_stats()

    # Get milestones for display
    milestones = JourneyMilestone.objects.filter(
        user=request.user
    ).order_by('-date')[:5]

    context = {
        'page_title': 'My Claims Journey',
        'timeline': timeline,
        'current_stage': current_stage,
        'deadlines': deadlines,
        'stats': stats,
        'milestones': milestones,
    }
    return render(request, 'core/journey_dashboard.html', context)


@login_required
def journey_timeline_partial(request):
    """
    HTMX endpoint for refreshing the timeline.
    """
    builder = TimelineBuilder(request.user)
    timeline = builder.build_timeline(limit=20)

    return render(request, 'core/partials/journey_timeline.html', {
        'timeline': timeline,
    })


@login_required
def add_milestone(request):
    """
    Add a new journey milestone.
    """
    if request.method == 'POST':
        milestone_type = request.POST.get('milestone_type', 'custom')
        title = request.POST.get('title', '').strip()
        milestone_date = request.POST.get('date')
        notes = request.POST.get('notes', '').strip()

        if not title:
            messages.error(request, "Title is required.")
            return redirect('core:journey_dashboard')

        if not milestone_date:
            milestone_date = date.today()

        JourneyMilestone.objects.create(
            user=request.user,
            milestone_type=milestone_type,
            title=title,
            date=milestone_date,
            notes=notes,
        )

        messages.success(request, f"Milestone '{title}' added to your journey!")
        return redirect('core:journey_dashboard')

    # GET - show form
    context = {
        'milestone_types': JourneyMilestone.MILESTONE_TYPE_CHOICES,
    }
    return render(request, 'core/add_milestone.html', context)


@login_required
def add_deadline(request):
    """
    Add a new deadline.
    """
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        deadline_date = request.POST.get('deadline_date')
        priority = request.POST.get('priority', 'medium')
        description = request.POST.get('description', '').strip()

        if not title or not deadline_date:
            messages.error(request, "Title and date are required.")
            return redirect('core:journey_dashboard')

        Deadline.objects.create(
            user=request.user,
            title=title,
            deadline_date=deadline_date,
            priority=priority,
            description=description,
        )

        messages.success(request, f"Deadline '{title}' added!")
        return redirect('core:journey_dashboard')

    # GET - show form
    context = {
        'priority_choices': Deadline.PRIORITY_CHOICES,
    }
    return render(request, 'core/add_deadline.html', context)


@login_required
def toggle_deadline(request, pk):
    """
    HTMX endpoint to toggle deadline completion.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    deadline = get_object_or_404(Deadline, pk=pk, user=request.user)

    if deadline.is_completed:
        deadline.is_completed = False
        deadline.completed_at = None
        deadline.save(update_fields=['is_completed', 'completed_at', 'updated_at'])
    else:
        deadline.mark_complete()

    return render(request, 'core/partials/deadline_item.html', {
        'deadline': deadline,
    })


@login_required
def delete_deadline(request, pk):
    """
    Delete a deadline.
    """
    deadline = get_object_or_404(Deadline, pk=pk, user=request.user)

    if request.method == 'POST':
        title = deadline.title
        deadline.delete()
        messages.success(request, f"Deadline '{title}' deleted.")
        return redirect('core:journey_dashboard')

    return render(request, 'core/delete_deadline.html', {
        'deadline': deadline,
    })


@login_required
def delete_milestone(request, pk):
    """
    Delete a milestone.
    """
    milestone = get_object_or_404(JourneyMilestone, pk=pk, user=request.user)

    if request.method == 'POST':
        title = milestone.title
        milestone.delete()
        messages.success(request, f"Milestone '{title}' deleted.")
        return redirect('core:journey_dashboard')

    return render(request, 'core/delete_milestone.html', {
        'milestone': milestone,
    })


# =============================================================================
# FEEDBACK VIEWS
# =============================================================================

from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.mail import send_mail
from django.conf import settings as django_settings
from .models import Feedback, SupportRequest


def submit_feedback(request):
    """
    Submit feedback via HTMX.
    Accepts both authenticated and anonymous users.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    rating = request.POST.get('rating')
    if rating not in ['positive', 'negative', 'neutral']:
        return HttpResponse('Invalid rating', status=400)

    # Create feedback
    feedback = Feedback.objects.create(
        user=request.user if request.user.is_authenticated else None,
        page_url=request.POST.get('page_url', request.META.get('HTTP_REFERER', '')),
        page_title=request.POST.get('page_title', ''),
        rating=rating,
        category=request.POST.get('category', 'general'),
        comment=request.POST.get('comment', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        session_key=request.session.session_key or '',
    )

    return render(request, 'core/partials/feedback_thanks.html', {
        'feedback': feedback,
    })


def feedback_form(request):
    """
    Return the expanded feedback form for adding a comment.
    Used by HTMX when user clicks thumbs down or wants to add details.
    """
    return render(request, 'core/partials/feedback_form.html', {
        'page_url': request.GET.get('page_url', ''),
        'page_title': request.GET.get('page_title', ''),
        'initial_rating': request.GET.get('rating', ''),
    })


# =============================================================================
# SUPPORT / CONTACT VIEWS
# =============================================================================

def contact(request):
    """
    Contact/support form for users to submit questions or issues.
    """
    context = {
        'page_title': 'Contact Support',
        'categories': SupportRequest.CATEGORY_CHOICES,
    }

    # Pre-fill user info if authenticated
    if request.user.is_authenticated:
        context['user_email'] = request.user.email
        context['user_name'] = request.user.get_full_name() or request.user.email

    if request.method == 'POST':
        # Validate required fields
        email = request.POST.get('email', '').strip()
        name = request.POST.get('name', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        category = request.POST.get('category', 'general')

        errors = []
        if not email:
            errors.append('Email is required')
        if not name:
            errors.append('Name is required')
        if not subject:
            errors.append('Subject is required')
        if not message:
            errors.append('Message is required')

        if errors:
            context['errors'] = errors
            context['form_data'] = request.POST
            return render(request, 'core/contact.html', context)

        # Create support request
        support_request = SupportRequest.objects.create(
            user=request.user if request.user.is_authenticated else None,
            email=email,
            name=name,
            category=category,
            subject=subject,
            message=message,
            page_url=request.META.get('HTTP_REFERER', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )

        # Send notification email to support team (optional)
        try:
            send_mail(
                subject=f'[Support] {category}: {subject}',
                message=f'New support request from {name} ({email}):\n\n{message}',
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[django_settings.SUPPORT_EMAIL],
                fail_silently=True,
            )
        except Exception:
            pass  # Don't fail if email doesn't send

        messages.success(
            request,
            'Your message has been sent. We\'ll get back to you as soon as possible.'
        )
        return redirect('core:contact_success')

    return render(request, 'core/contact.html', context)


def contact_success(request):
    """Success page after submitting contact form."""
    return render(request, 'core/contact_success.html', {
        'page_title': 'Message Sent',
    })
