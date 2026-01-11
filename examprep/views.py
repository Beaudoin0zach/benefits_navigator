"""
Views for examprep app - C&P Exam preparation with accessibility
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q

from .models import ExamGuidance, GlossaryTerm, ExamChecklist, SavedRatingCalculation, EvidenceChecklist
from .forms import ExamChecklistForm
from .va_math import (
    DisabilityRating,
    calculate_combined_rating,
    estimate_monthly_compensation,
    VA_COMPENSATION_RATES_2024,
    format_currency,
)
import json


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


# =============================================================================
# RATING CALCULATOR VIEWS
# =============================================================================

def rating_calculator(request):
    """
    VA Disability Rating Calculator
    Accessible to all users - allows calculating combined ratings with VA Math
    """
    # Get user's saved calculations if logged in
    saved_calculations = None
    if request.user.is_authenticated:
        saved_calculations = SavedRatingCalculation.objects.filter(
            user=request.user
        ).order_by('-updated_at')[:5]

    context = {
        'compensation_rates': VA_COMPENSATION_RATES_2024,
        'saved_calculations': saved_calculations,
    }
    return render(request, 'examprep/rating_calculator.html', context)


def calculate_rating_htmx(request):
    """
    HTMX endpoint for real-time rating calculation
    Accepts POST with ratings data and returns calculated results
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        # Parse ratings from form data
        ratings_json = request.POST.get('ratings', '[]')
        ratings_data = json.loads(ratings_json)

        # Parse dependent info
        has_spouse = request.POST.get('has_spouse') == 'true'
        children = int(request.POST.get('children_under_18', 0))
        parents = int(request.POST.get('dependent_parents', 0))

        # Convert to DisabilityRating objects
        ratings = []
        for r in ratings_data:
            percentage = int(r.get('percentage', 0))
            if percentage > 0:
                ratings.append(DisabilityRating(
                    percentage=percentage,
                    description=r.get('description', ''),
                    is_bilateral=r.get('is_bilateral', False)
                ))

        if not ratings:
            context = {
                'combined_raw': 0,
                'combined_rounded': 0,
                'bilateral_factor': 0,
                'monthly_compensation': '$0.00',
                'annual_compensation': '$0.00',
                'step_by_step': [],
                'ratings': [],
                'has_ratings': False,
            }
            return render(request, 'examprep/partials/rating_result.html', context)

        # Calculate combined rating
        result = calculate_combined_rating(ratings)

        # Calculate compensation
        monthly = estimate_monthly_compensation(
            result.combined_rounded,
            spouse=has_spouse,
            children_under_18=children,
            dependent_parents=parents
        )

        context = {
            'combined_raw': round(result.combined_raw, 2),
            'combined_rounded': result.combined_rounded,
            'bilateral_factor': round(result.bilateral_factor_applied, 2),
            'monthly_compensation': format_currency(monthly),
            'annual_compensation': format_currency(monthly * 12),
            'step_by_step': result.step_by_step,
            'ratings': ratings_data,
            'has_ratings': True,
        }
        return render(request, 'examprep/partials/rating_result.html', context)

    except (json.JSONDecodeError, ValueError, TypeError) as e:
        return HttpResponse(f"Error: {str(e)}", status=400)


@login_required
def save_calculation(request):
    """
    Save a rating calculation for the logged-in user
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        name = request.POST.get('name', 'My Calculation')
        ratings_json = request.POST.get('ratings', '[]')
        ratings_data = json.loads(ratings_json)

        has_spouse = request.POST.get('has_spouse') == 'true'
        children = int(request.POST.get('children_under_18', 0))
        parents = int(request.POST.get('dependent_parents', 0))
        notes = request.POST.get('notes', '')

        # Create saved calculation
        calc = SavedRatingCalculation.objects.create(
            user=request.user,
            name=name,
            ratings=ratings_data,
            has_spouse=has_spouse,
            children_under_18=children,
            dependent_parents=parents,
            notes=notes
        )

        # Calculate and save results
        calc.recalculate()
        calc.save()

        if request.headers.get('HX-Request'):
            # Return HTMX response
            messages.success(request, f"Calculation '{name}' saved!")
            return render(request, 'examprep/partials/save_confirmation.html', {
                'calculation': calc
            })

        return redirect('examprep:saved_calculations')

    except (json.JSONDecodeError, ValueError) as e:
        if request.headers.get('HX-Request'):
            return HttpResponse(f"Error saving: {str(e)}", status=400)
        messages.error(request, f"Error saving calculation: {str(e)}")
        return redirect('examprep:rating_calculator')


@login_required
def saved_calculations(request):
    """
    List user's saved rating calculations
    """
    calculations = SavedRatingCalculation.objects.filter(
        user=request.user
    ).order_by('-updated_at')

    context = {
        'calculations': calculations,
    }
    return render(request, 'examprep/saved_calculations.html', context)


@login_required
def delete_calculation(request, pk):
    """
    Delete a saved calculation
    """
    calc = get_object_or_404(
        SavedRatingCalculation,
        pk=pk,
        user=request.user
    )

    if request.method == 'POST':
        name = calc.name
        calc.delete()

        if request.headers.get('HX-Request'):
            return HttpResponse('')  # Empty response for HTMX to remove element

        messages.success(request, f"Calculation '{name}' deleted.")
        return redirect('examprep:saved_calculations')

    context = {'calculation': calc}
    return render(request, 'examprep/calculation_delete.html', context)


@login_required
def load_calculation(request, pk):
    """
    HTMX endpoint to load a saved calculation into the calculator
    Returns JSON for JavaScript to populate the form
    """
    calc = get_object_or_404(
        SavedRatingCalculation,
        pk=pk,
        user=request.user
    )

    return JsonResponse({
        'ratings': calc.ratings,
        'has_spouse': calc.has_spouse,
        'children_under_18': calc.children_under_18,
        'dependent_parents': calc.dependent_parents,
        'name': calc.name,
        'notes': calc.notes,
    })


# =============================================================================
# EVIDENCE CHECKLIST VIEWS
# =============================================================================

@login_required
def evidence_checklist_list(request):
    """
    Display user's evidence checklists
    """
    checklists = EvidenceChecklist.objects.filter(
        user=request.user
    ).order_by('-updated_at')

    context = {
        'checklists': checklists,
    }
    return render(request, 'examprep/evidence_checklist_list.html', context)


@login_required
def evidence_checklist_create(request):
    """
    Create a new evidence checklist for a condition/claim type
    """
    from agents.services import EvidenceChecklistGenerator

    # Check if coming from a denial analysis
    from_denial_id = request.GET.get('from_denial')
    denial_analysis = None
    initial_condition = ''
    initial_claim_type = 'initial'

    if from_denial_id:
        from agents.models import DecisionLetterAnalysis
        try:
            denial_analysis = DecisionLetterAnalysis.objects.get(
                pk=from_denial_id,
                document__user=request.user
            )
            # Pre-populate from first denied condition if available
            if denial_analysis.conditions_denied:
                first_denial = denial_analysis.conditions_denied[0]
                initial_condition = first_denial.get('condition', '')
            initial_claim_type = 'appeal'
        except DecisionLetterAnalysis.DoesNotExist:
            pass

    if request.method == 'POST':
        condition = request.POST.get('condition', '').strip()
        claim_type = request.POST.get('claim_type', 'initial')
        primary_condition = request.POST.get('primary_condition', '').strip()

        if not condition:
            messages.error(request, "Please enter a condition.")
            return render(request, 'examprep/evidence_checklist_create.html', {
                'denial_analysis': denial_analysis,
                'initial_condition': condition,
                'initial_claim_type': claim_type,
            })

        # Generate checklist using AI service
        generator = EvidenceChecklistGenerator()

        # Build denial context if from denial analysis
        denial_context = None
        if denial_analysis and hasattr(denial_analysis, 'denial_decoding'):
            decoding = denial_analysis.denial_decoding
            # Find the specific denial for this condition
            for denial in decoding.denial_mappings:
                if denial.get('condition', '').lower() == condition.lower():
                    denial_context = {
                        'denial_reason': denial.get('denial_reason', ''),
                        'evidence_issue': denial.get('evidence_issue', ''),
                        'required_evidence': denial.get('required_evidence', []),
                    }
                    break

        checklist_items = generator.generate_checklist(
            condition=condition,
            claim_type=claim_type,
            primary_condition=primary_condition if claim_type == 'secondary' else None,
            denial_context=denial_context,
        )

        # Create EvidenceChecklist record
        checklist = EvidenceChecklist.objects.create(
            user=request.user,
            condition=condition,
            claim_type=claim_type,
            primary_condition=primary_condition if claim_type == 'secondary' else '',
            checklist_items=checklist_items,
            from_denial_analysis=denial_analysis,
        )
        checklist.update_completion()

        messages.success(request, f"Evidence checklist for {condition} created!")
        return redirect('examprep:evidence_checklist_detail', pk=checklist.pk)

    context = {
        'denial_analysis': denial_analysis,
        'initial_condition': initial_condition,
        'initial_claim_type': initial_claim_type,
        'claim_types': EvidenceChecklist.CLAIM_TYPE_CHOICES,
    }
    return render(request, 'examprep/evidence_checklist_create.html', context)


@login_required
def evidence_checklist_detail(request, pk):
    """
    Display evidence checklist with interactive toggles
    """
    checklist = get_object_or_404(
        EvidenceChecklist,
        pk=pk,
        user=request.user
    )

    # Group items by category
    items_by_category = checklist.get_items_by_category()

    context = {
        'checklist': checklist,
        'items_by_category': items_by_category,
    }
    return render(request, 'examprep/evidence_checklist_detail.html', context)


@login_required
def evidence_checklist_toggle(request, pk):
    """
    HTMX endpoint to toggle an evidence checklist item
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    checklist = get_object_or_404(
        EvidenceChecklist,
        pk=pk,
        user=request.user
    )

    item_id = request.POST.get('item_id')
    if not item_id:
        return HttpResponse("Missing item_id", status=400)

    # Toggle the item
    new_status = checklist.toggle_item(item_id)

    # Find the item for rendering
    item = None
    for i in checklist.checklist_items:
        if i.get('id') == item_id:
            item = i
            break

    context = {
        'item': item,
        'checklist': checklist,
    }
    return render(request, 'examprep/partials/evidence_checklist_item.html', context)


@login_required
def evidence_checklist_delete(request, pk):
    """
    Delete an evidence checklist
    """
    checklist = get_object_or_404(
        EvidenceChecklist,
        pk=pk,
        user=request.user
    )

    if request.method == 'POST':
        condition = checklist.condition
        checklist.delete()
        messages.success(request, f"Evidence checklist for {condition} deleted.")
        return redirect('examprep:evidence_checklist_list')

    context = {
        'checklist': checklist,
    }
    return render(request, 'examprep/evidence_checklist_delete.html', context)


@login_required
def evidence_checklist_from_denial(request, analysis_id):
    """
    Generate evidence checklists from a denial decoder analysis
    Shows all denied conditions and lets user select which to create checklists for
    """
    from agents.models import DecisionLetterAnalysis

    analysis = get_object_or_404(
        DecisionLetterAnalysis,
        pk=analysis_id,
        document__user=request.user
    )

    if not analysis.conditions_denied:
        messages.warning(request, "No denied conditions found in this analysis.")
        return redirect('claims:denial_decoder_result', pk=analysis.document_id)

    # Check which conditions already have checklists
    existing_conditions = set(
        EvidenceChecklist.objects.filter(
            user=request.user,
            from_denial_analysis=analysis
        ).values_list('condition', flat=True)
    )

    denied_conditions = []
    for denial in analysis.conditions_denied:
        condition = denial.get('condition', 'Unknown')
        denied_conditions.append({
            'condition': condition,
            'reason': denial.get('reason', ''),
            'has_checklist': condition in existing_conditions,
        })

    context = {
        'analysis': analysis,
        'denied_conditions': denied_conditions,
    }
    return render(request, 'examprep/evidence_checklist_from_denial.html', context)
