"""
Views for examprep app - C&P Exam preparation with accessibility
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q

from .models import ExamGuidance, GlossaryTerm, ExamChecklist
from .forms import ExamChecklistForm


def guide_list(request):
    """
    Display list of exam preparation guides by category
    Accessible to all users (authenticated and anonymous)
    """
    # Get all published guides, ordered by category and order
    guides = ExamGuidance.objects.filter(is_published=True).order_by('category', 'order')

    # Group guides by category for better display
    guides_by_category = {}
    for guide in guides:
        category = guide.get_category_display()
        if category not in guides_by_category:
            guides_by_category[category] = []
        guides_by_category[category].append(guide)

    context = {
        'guides_by_category': guides_by_category,
        'total_guides': guides.count(),
    }
    return render(request, 'examprep/guide_list.html', context)


def guide_detail(request, slug):
    """
    Display detailed exam preparation guide with all content sections
    Accessible to all users
    """
    guide = get_object_or_404(ExamGuidance, slug=slug, is_published=True)

    # Check if user has an existing checklist for this guide
    user_checklist = None
    if request.user.is_authenticated:
        user_checklist = ExamChecklist.objects.filter(
            user=request.user,
            guidance=guide
        ).first()

    context = {
        'guide': guide,
        'user_checklist': user_checklist,
    }
    return render(request, 'examprep/guide_detail.html', context)


def glossary_list(request):
    """
    Display VA terminology glossary with search
    Accessible to all users
    """
    query = request.GET.get('q', '').strip()

    if query:
        # Search in term, plain_language, and context fields
        terms = GlossaryTerm.objects.filter(
            Q(term__icontains=query) |
            Q(plain_language__icontains=query) |
            Q(context__icontains=query)
        ).order_by('term')
    else:
        # Show all terms
        terms = GlossaryTerm.objects.all().order_by('term')

    context = {
        'terms': terms,
        'query': query,
        'total_terms': terms.count(),
    }
    return render(request, 'examprep/glossary_list.html', context)


def glossary_detail(request, pk):
    """
    Display detailed glossary term with related terms
    Accessible to all users
    """
    term = get_object_or_404(GlossaryTerm, pk=pk)

    context = {
        'term': term,
        'related_terms': term.related_terms.all()
    }
    return render(request, 'examprep/glossary_detail.html', context)


@login_required
def checklist_list(request):
    """
    Display user's personal exam preparation checklists
    Shows upcoming exams and completion status
    """
    checklists = ExamChecklist.objects.filter(
        user=request.user
    ).select_related('guidance').order_by('-created_at')

    # Separate upcoming and past checklists
    upcoming = [c for c in checklists if c.is_upcoming and not c.exam_completed]
    past = [c for c in checklists if not c.is_upcoming or c.exam_completed]

    context = {
        'upcoming_checklists': upcoming,
        'past_checklists': past,
        'total_checklists': checklists.count(),
    }
    return render(request, 'examprep/checklist_list.html', context)


@login_required
def checklist_create(request):
    """
    Create a new exam preparation checklist
    Can be based on a guide or standalone
    """
    guide_slug = request.GET.get('guide')
    guide = None

    if guide_slug:
        guide = get_object_or_404(ExamGuidance, slug=guide_slug, is_published=True)

    if request.method == 'POST':
        form = ExamChecklistForm(request.POST, user=request.user)
        if form.is_valid():
            checklist = form.save(commit=False)
            checklist.user = request.user
            if guide:
                checklist.guidance = guide
            checklist.save()

            messages.success(
                request,
                f"Exam checklist for {checklist.condition} created successfully!"
            )
            return redirect('examprep:checklist_detail', pk=checklist.id)
    else:
        initial = {}
        if guide:
            initial['guidance'] = guide
        form = ExamChecklistForm(user=request.user, initial=initial)

    context = {
        'form': form,
        'guide': guide,
    }
    return render(request, 'examprep/checklist_create.html', context)


@login_required
def checklist_detail(request, pk):
    """
    Display detailed exam checklist with all preparation sections
    Shows progress, notes, and interactive checklist
    """
    checklist = get_object_or_404(
        ExamChecklist,
        pk=pk,
        user=request.user
    )

    context = {
        'checklist': checklist,
    }
    return render(request, 'examprep/checklist_detail.html', context)


@login_required
def checklist_update(request, pk):
    """
    Update exam checklist notes and information
    """
    checklist = get_object_or_404(
        ExamChecklist,
        pk=pk,
        user=request.user
    )

    if request.method == 'POST':
        form = ExamChecklistForm(request.POST, instance=checklist, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Checklist updated successfully!")
            return redirect('examprep:checklist_detail', pk=checklist.id)
    else:
        form = ExamChecklistForm(instance=checklist, user=request.user)

    context = {
        'form': form,
        'checklist': checklist,
    }
    return render(request, 'examprep/checklist_update.html', context)


@login_required
def checklist_delete(request, pk):
    """
    Delete exam checklist (confirmation required)
    """
    checklist = get_object_or_404(
        ExamChecklist,
        pk=pk,
        user=request.user
    )

    if request.method == 'POST':
        condition = checklist.condition
        checklist.delete()
        messages.success(request, f"Checklist for {condition} deleted.")
        return redirect('examprep:checklist_list')

    context = {
        'checklist': checklist,
    }
    return render(request, 'examprep/checklist_delete.html', context)


@login_required
def checklist_toggle_task(request, pk):
    """
    HTMX endpoint to toggle a checklist task completion
    Returns updated task HTML
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    checklist = get_object_or_404(
        ExamChecklist,
        pk=pk,
        user=request.user
    )

    task_id = request.POST.get('task_id')
    if not task_id:
        return HttpResponse("Missing task_id", status=400)

    # Toggle task in tasks_completed list
    tasks = checklist.tasks_completed or []
    if task_id in tasks:
        tasks.remove(task_id)
        completed = False
    else:
        tasks.append(task_id)
        completed = True

    checklist.tasks_completed = tasks
    checklist.save()

    # Get the task text from guidance checklist_items
    task_text = ""
    if checklist.guidance and checklist.guidance.checklist_items:
        try:
            # task_id format is "task_1", "task_2", etc. - extract index
            task_index = int(task_id.split('_')[1]) - 1
            if 0 <= task_index < len(checklist.guidance.checklist_items):
                task_text = checklist.guidance.checklist_items[task_index]
        except (ValueError, IndexError):
            pass

    # Return updated checkbox HTML for HTMX swap
    context = {
        'task_id': task_id,
        'completed': completed,
        'checklist': checklist,
        'task_text': task_text,
    }
    return render(request, 'examprep/partials/checklist_task.html', context)
